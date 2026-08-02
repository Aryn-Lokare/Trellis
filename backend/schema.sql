-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create documents table (if not exists)
CREATE TABLE IF NOT EXISTS documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filename text,
  doc_type text,           -- 'pdf' | 'audio' | 'table'
  storage_path text,
  raw_text text,
  extraction_metadata jsonb,
  status text DEFAULT 'pending',
  error_message text,
  created_at timestamp DEFAULT now()
);

-- Create entities table
CREATE TABLE IF NOT EXISTS entities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  type text NOT NULL,      -- 'person' | 'organization' | 'regulation' | 'system' | 'financial_instrument' | 'date_or_deadline' | 'location'
  source_doc_id uuid REFERENCES documents(id) ON DELETE CASCADE,
  source_span text,
  source_location text,
  embedding vector(1536),  -- Left NULL during scaffolding
  
  -- Validation constraint for allowed entity types
  CONSTRAINT chk_entity_type CHECK (type IN (
    'person', 
    'organization', 
    'regulation', 
    'system', 
    'financial_instrument', 
    'date_or_deadline', 
    'location'
  ))
);

-- Create relationships table
CREATE TABLE IF NOT EXISTS relationships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_entity_id uuid REFERENCES entities(id) ON DELETE CASCADE,
  target_entity_id uuid REFERENCES entities(id) ON DELETE CASCADE,
  relation_type text NOT NULL, -- 'employs' | 'supplies_to' | 'regulated_by' | 'violates' | 'flagged_for' | 'located_at' | 'reports_to' | 'party_to' | 'occurred_on'
  source_doc_id uuid REFERENCES documents(id) ON DELETE CASCADE,
  source_span text,
  source_location text,
  
  -- Validation constraint for allowed relationship types
  CONSTRAINT chk_relation_type CHECK (relation_type IN (
    'employs', 
    'supplies_to', 
    'regulated_by', 
    'violates', 
    'flagged_for', 
    'located_at', 
    'reports_to', 
    'party_to', 
    'occurred_on'
  ))
);

-- Indexing for performance and query lookup
CREATE INDEX IF NOT EXISTS idx_entities_source_doc_id ON entities(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_entities_name_type ON entities(name, type);
CREATE INDEX IF NOT EXISTS idx_relationships_source_doc_id ON relationships(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_relationships_source_entity ON relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target_entity ON relationships(target_entity_id);

-- Migration steps for existing databases
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status text DEFAULT 'pending';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS error_message text;

-- Cross-document entity provenance tracking
CREATE TABLE IF NOT EXISTS entity_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id uuid REFERENCES entities(id) ON DELETE CASCADE,
  source_doc_id uuid REFERENCES documents(id) ON DELETE CASCADE,
  source_span text,
  source_location text
);
CREATE INDEX IF NOT EXISTS idx_entity_sources_entity ON entity_sources(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_sources_doc ON entity_sources(source_doc_id);

-- ============================================================================
-- GraphRAG Query Layer Migrations
-- ============================================================================

-- Fix embedding dimension: Gemini text-embedding-004 outputs 768 dims
ALTER TABLE entities ALTER COLUMN embedding TYPE vector(768);

-- RPC: Vector similarity search for seed entities
CREATE OR REPLACE FUNCTION match_entities(
  query_embedding vector(768),
  match_threshold float DEFAULT 0.3,
  match_count int DEFAULT 8
)
RETURNS TABLE (
  id uuid,
  name text,
  type text,
  source_doc_id uuid,
  source_span text,
  source_location text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    e.id, e.name, e.type, e.source_doc_id,
    e.source_span, e.source_location,
    1 - (e.embedding <=> query_embedding) AS similarity
  FROM entities e
  WHERE e.embedding IS NOT NULL
    AND 1 - (e.embedding <=> query_embedding) > match_threshold
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- RPC: Graph traversal via recursive CTE
CREATE OR REPLACE FUNCTION traverse_graph(
  seed_ids uuid[],
  max_hops int DEFAULT 2,
  max_entities int DEFAULT 50
)
RETURNS TABLE (
  entity_id uuid,
  entity_name text,
  entity_type text,
  entity_source_doc_id uuid,
  entity_source_span text,
  entity_source_location text,
  hop_distance int
)
LANGUAGE sql STABLE
AS $$
  WITH RECURSIVE traversal AS (
    -- Base case: seed entities at hop 0
    SELECT e.id AS entity_id, e.name AS entity_name, e.type AS entity_type,
           e.source_doc_id AS entity_source_doc_id,
           e.source_span AS entity_source_span,
           e.source_location AS entity_source_location,
           0 AS hop_distance
    FROM entities e
    WHERE e.id = ANY(seed_ids)

    UNION

    -- Recursive step: follow relationships outward
    SELECT e2.id, e2.name, e2.type,
           e2.source_doc_id, e2.source_span, e2.source_location,
           t.hop_distance + 1
    FROM traversal t
    JOIN relationships r ON (r.source_entity_id = t.entity_id OR r.target_entity_id = t.entity_id)
    JOIN entities e2 ON (
      e2.id = CASE
        WHEN r.source_entity_id = t.entity_id THEN r.target_entity_id
        ELSE r.source_entity_id
      END
    )
    WHERE t.hop_distance < max_hops
  )
  SELECT entity_id, entity_name, entity_type,
         entity_source_doc_id, entity_source_span, entity_source_location,
         hop_distance
  FROM (
    SELECT DISTINCT ON (t.entity_id)
      t.entity_id, t.entity_name, t.entity_type,
      t.entity_source_doc_id, t.entity_source_span, t.entity_source_location,
      t.hop_distance
    FROM traversal t
    ORDER BY t.entity_id, t.hop_distance ASC
  ) sub
  ORDER BY hop_distance ASC
  LIMIT max_entities;
$$;

-- RPC: Fetch relationships connecting a set of entity IDs
CREATE OR REPLACE FUNCTION get_relationships_for_entities(
  entity_ids uuid[]
)
RETURNS TABLE (
  id uuid,
  source_entity_id uuid,
  target_entity_id uuid,
  relation_type text,
  source_doc_id uuid,
  source_span text,
  source_location text
)
LANGUAGE sql STABLE
AS $$
  SELECT r.id, r.source_entity_id, r.target_entity_id,
         r.relation_type, r.source_doc_id,
         r.source_span, r.source_location
  FROM relationships r
  WHERE r.source_entity_id = ANY(entity_ids)
    AND r.target_entity_id = ANY(entity_ids);
$$;

