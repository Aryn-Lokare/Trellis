import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { IngestionStatus } from '../types';

export function useIngestionStatus(documentId: string | null) {
  return useQuery<IngestionStatus, Error>({
    queryKey: ['ingestion-status', documentId],
    queryFn: () => {
      if (!documentId) throw new Error('No document ID provided');
      return api.getIngestionStatus(documentId);
    },
    enabled: !!documentId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 2000;
    },
  });
}
