import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import apiClient from '../client';
import type { LogSearchRequest, LogSearchResponse } from '../types/log';

export function useLogsQuery(
  request: LogSearchRequest,
  options?: Omit<UseQueryOptions<LogSearchResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['logs', 'search', request],
    queryFn: async () => {
      const response = await apiClient.post<LogSearchResponse>('/api/logs/search', request);
      return response.data;
    },
    ...options,
  });
}
