import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import apiClient from '../client';
import type { TraceSearchRequest, TraceSearchResponse, TraceDetailResponse } from '../types/trace';

// Search traces
export function useTracesQuery(
  request: TraceSearchRequest,
  options?: Omit<UseQueryOptions<TraceSearchResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['traces', 'search', request],
    queryFn: async () => {
      const response = await apiClient.post<TraceSearchResponse>('/api/traces/search', request);
      return response.data;
    },
    ...options,
  });
}

// Get trace detail by ID
export function useTraceDetailQuery(
  traceId: string,
  options?: Omit<UseQueryOptions<TraceDetailResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['traces', 'detail', traceId],
    queryFn: async () => {
      const response = await apiClient.get<TraceDetailResponse>(`/api/traces/${traceId}`);
      return response.data;
    },
    enabled: !!traceId,
    ...options,
  });
}
