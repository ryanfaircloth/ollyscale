import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import apiClient from '../client';
import type { SpanSearchRequest, SpanSearchResponse } from '../types/trace';

export function useSpansQuery(
  request: SpanSearchRequest,
  options?: Omit<UseQueryOptions<SpanSearchResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['spans', 'search', request],
    queryFn: async () => {
      const response = await apiClient.post<SpanSearchResponse>('/api/spans/search', request);
      return response.data;
    },
    ...options,
  });
}
