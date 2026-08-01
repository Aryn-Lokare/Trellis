import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useUpload() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ file, documentType }: { file: File; documentType?: string }) => {
      return api.uploadDocument(file, documentType);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['graph'] });
    },
  });
}
