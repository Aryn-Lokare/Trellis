import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { DocumentDetail } from '../types';

export function useDocument(documentId: string | null) {
  return useQuery<DocumentDetail, Error>({
    queryKey: ['document', documentId],
    queryFn: () => {
      if (!documentId) throw new Error('No document ID provided');
      return api.getDocument(documentId);
    },
    enabled: !!documentId,
    staleTime: 30000,
  });
}

export function useDocumentList() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: () => api.getDocuments(),
    staleTime: 10000,
  });
}
