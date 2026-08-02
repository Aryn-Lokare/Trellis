import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Subgraph } from '../types';

export function useGraph() {
  return useQuery<Subgraph, Error>({
    queryKey: ['graph'],
    queryFn: () => api.getGraph(),
    staleTime: 10000,
    retry: 2,
  });
}
