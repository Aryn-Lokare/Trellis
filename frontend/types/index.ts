export type DocumentType = 'pdf' | 'audio' | 'table' | 'schematic';

export type IngestionStepStatus = 'queued' | 'parsing' | 'extracting' | 'completed' | 'failed';

export interface Document {
  id: string;
  filename: string;
  type: DocumentType;
  storage_path?: string;
  created_at: string;
  status?: IngestionStepStatus;
  page_count?: number;
  duration_seconds?: number;
  content_summary?: string;
}

export interface Entity {
  id: string;
  name: string;
  type: string; // person, company, regulation, system, vendor, policy, etc.
  source_doc_id: string;
  source_span: string; // e.g. "Page 3" or "02:15"
  embedding?: number[];
  properties?: Record<string, unknown>;
}

export interface Relationship {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  source_doc_id: string;
  source_span: string; // e.g. "Page 3" or "02:15"
  description?: string;
}

export interface Citation {
  id: string;
  citation_index: number;
  source_doc_id: string;
  source_span: string; // Page number or audio timestamp
  snippet: string;
  document_filename?: string;
  document_type?: DocumentType;
  verified?: boolean;
}

export interface Subgraph {
  nodes: Entity[];
  edges: Relationship[];
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  subgraph: Subgraph;
  f1_score: number;
}

export interface IngestionStatus {
  document_id: string;
  filename: string;
  type: DocumentType;
  status: IngestionStepStatus;
  progress_percent?: number;
  current_step?: string;
  error?: string;
  extracted_entities_count?: number;
  extracted_relationships_count?: number;
}

export interface DocumentDetail extends Document {
  extracted_entities?: Entity[];
  extracted_relationships?: Relationship[];
  content_text?: string;
  spans?: Array<{
    span_id: string;
    label: string; // e.g. "Page 1, Para 2" or "00:45 - 01:15"
    text: string;
  }>;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unreachable' | string;
  timestamp?: string;
  services?: Record<string, string>;
}