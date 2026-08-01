import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { HealthResponse } from '../types';

export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 10000, // Poll every 10 seconds
    retry: 2,
    staleTime: 5000,
  });
}
