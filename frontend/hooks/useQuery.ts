import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useComplianceStore } from '../store/useComplianceStore';
import { QueryResponse } from '../types';

export function useQuerySubmission() {
  const queryClient = useQueryClient();
  const setActiveSubgraph = useComplianceStore((state) => state.setActiveSubgraph);

  return useMutation<QueryResponse, Error, string>({
    mutationFn: async (question: string) => {
      return api.submitQuery(question);
    },
    onSuccess: (data) => {
      if (data.subgraph) {
        setActiveSubgraph(data.subgraph);
      }
      queryClient.invalidateQueries({ queryKey: ['graph'] });
    },
  });
}
