import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import apiClient from '../client';
import type { MetricSearchRequest, MetricSearchResponse } from '../types/metric';

export function useMetricsQuery(
  request: MetricSearchRequest,
  options?: Omit<UseQueryOptions<MetricSearchResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['metrics', 'search', request],
    queryFn: async () => {
      const response = await apiClient.post<MetricSearchResponse>('/api/metrics/search', request);
      return response.data;
    },
    ...options,
  });
}
