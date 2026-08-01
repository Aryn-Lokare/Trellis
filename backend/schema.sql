-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create documents table (if not exists)
CREATE TABLE IF NOT EXISTS documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filename text,
  doc_type text,           -- 'pdf' | 'audio' | 'table' | 'schematic'
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
