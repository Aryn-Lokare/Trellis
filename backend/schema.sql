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

-- Supabase Auth keeps passwords and session credentials in auth.users. This table
-- contains only application profile information that the authenticated user may read.
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text NOT NULL,
  full_name text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own profile" ON public.profiles;
CREATE POLICY "Users can view their own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;
CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data ->> 'full_name')
  ON CONFLICT (id) DO UPDATE
    SET email = EXCLUDED.email,
        full_name = COALESCE(EXCLUDED.full_name, public.profiles.full_name),
        updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT OR UPDATE ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_auth_user();
