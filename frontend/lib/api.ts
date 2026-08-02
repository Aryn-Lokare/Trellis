import axios from 'axios';
import {
  Document,
  DocumentDetail,
  HealthResponse,
  IngestionStatus,
  QueryResponse,
  Subgraph,
} from '../types';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const api = {
  /**
   * Health check endpoint
   * GET /health
   */
  async getHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/backend/health');
    return response.data;
  },

  /**
   * Upload a document (PDF, audio, CSV/table, image/schematic)
   * POST /upload
   */
  async uploadDocument(
    file: File,
    documentType?: string
  ): Promise<{ id: string; filename: string; type: string; status: string }> {
    const formData = new FormData();
    formData.append('file', file);
    if (documentType) {
      formData.append('type', documentType);
    }

    const response = await apiClient.post('/backend/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Submit a natural-language compliance question
   * POST /query
   */
  async submitQuery(question: string): Promise<QueryResponse> {
    const response = await apiClient.post<QueryResponse>('/backend/query', {
      question,
    });
    return response.data;
  },

  /**
   * Fetch current full/partial knowledge graph for visualization
   * GET /graph
   */
  async getGraph(): Promise<Subgraph> {
    const response = await apiClient.get<Subgraph>('/backend/graph');
    return response.data;
  },

  /**
   * Fetch document metadata, extracted content & span data
   * GET /document/{id}
   */
  async getDocument(id: string): Promise<DocumentDetail> {
    const response = await apiClient.get<DocumentDetail>(`/backend/document/${id}`);
    return response.data;
  },

  /**
   * Fetch list of all ingested documents
   * GET /documents
   */
  async getDocuments(): Promise<Document[]> {
    try {
      const response = await apiClient.get<Document[]>('/backend/documents');
      return response.data;
    } catch {
      // Fallback if backend does not expose list route separately
      const graph = await api.getGraph();
      const docIds = new Set<string>();
      graph.nodes?.forEach((n) => n.source_doc_id && docIds.add(n.source_doc_id));
      graph.edges?.forEach((e) => e.source_doc_id && docIds.add(e.source_doc_id));
      
      const docs: Document[] = Array.from(docIds).map((id) => ({
        id,
        filename: `Document-${id.substring(0, 8)}`,
        type: 'pdf',
        created_at: new Date().toISOString(),
        status: 'completed',
      }));
      return docs;
    }
  },

  /**
   * Ingestion status check for a document
   * GET /document/{id}/status (or polling /document/{id})
   */
  async getIngestionStatus(id: string): Promise<IngestionStatus> {
    try {
      const response = await apiClient.get<IngestionStatus>(`/backend/document/${id}/status`);
      return response.data;
    } catch {
      const doc = await api.getDocument(id);
      return {
        document_id: doc.id,
        filename: doc.filename,
        type: doc.type,
        status: doc.status || 'completed',
        progress_percent: doc.status === 'completed' ? 100 : 50,
      };
    }
  },
};
