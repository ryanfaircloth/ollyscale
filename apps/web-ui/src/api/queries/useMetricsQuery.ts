import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import apiClient from '../client';
import type { MetricSearchRequest, MetricSearchResponse } from '../types/metric';

// Convert RFC3339 timestamp to nanoseconds since Unix epoch
function timestampToNanos(rfc3339: string): number {
  return new Date(rfc3339).getTime() * 1_000_000;
}

export function useMetricsQuery(
  request: MetricSearchRequest,
  options?: Omit<UseQueryOptions<MetricSearchResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['metrics', 'search', request],
    queryFn: async () => {
      // Convert request to v2 API format
      const params: Record<string, string | number> = {
        start_time: timestampToNanos(request.time_range.start_time),
        end_time: timestampToNanos(request.time_range.end_time),
        limit: request.pagination?.limit || 1000,
      };

      // Extract service_name from filters if present
      const serviceFilter = request.filters?.find(f => f.field === 'service.name' && f.operator === 'eq');
      if (serviceFilter && typeof serviceFilter.value === 'string') {
        params.service_name = serviceFilter.value;
      }

      // Call v2 API endpoint with GET and query parameters
      const response = await apiClient.get<MetricSearchResponse>('/api/v2/metrics/search', {
        params,
      });
      return response.data;
    },
    ...options,
  });
}
