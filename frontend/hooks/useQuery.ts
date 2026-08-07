import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useComplianceStore } from '../store/useComplianceStore';
import { QueryResponse, ChatMessage } from '../types';

export function useQuerySubmission() {
  const queryClient = useQueryClient();
  const setActiveSubgraph = useComplianceStore((state) => state.setActiveSubgraph);

  return useMutation<QueryResponse, Error, { question: string; history?: ChatMessage[] }>({
    mutationFn: async ({ question, history }) => {
      return api.submitQuery(question, history);
    },
    onSuccess: (data) => {
      if (data.subgraph) {
        setActiveSubgraph(data.subgraph);
      }
      queryClient.invalidateQueries({ queryKey: ['graph'] });
    },
  });
}
