import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import apiClient from '../client';
import type { TraceSearchRequest, TraceSearchResponse, TraceDetailResponse, OtlpTraceSearchResponse } from '../types/trace';
import { rfc3339ToNanoseconds } from '../utils/timestamp';

// Search traces
export function useTracesQuery(
  request: TraceSearchRequest,
  options?: Omit<UseQueryOptions<TraceSearchResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['traces', 'search', request],
    queryFn: async () => {
      // Convert to new OTLP API format
      const params = {
        start_time: rfc3339ToNanoseconds(request.time_range.start_time),
        end_time: rfc3339ToNanoseconds(request.time_range.end_time),
        limit: request.pagination?.limit || 100,
        offset: request.pagination?.limit ? (request.pagination.limit * ((request.pagination?.cursor as unknown as number) || 0)) : 0,
      };

      // Add filters as query params
      const serviceFilter = request.filters?.find(f => f.field === 'service.name' || f.field === 'service_name');
      if (serviceFilter) {
        Object.assign(params, { service_name: serviceFilter.value });
      }

      const durationFilter = request.filters?.find(f => f.field === 'duration' || f.field === 'duration_ns');
      if (durationFilter) {
        Object.assign(params, { min_duration_ns: durationFilter.value });
      }

      const response = await apiClient.get<OtlpTraceSearchResponse>('/api/traces/search', { params });

      // Convert to old response format for compatibility
      return {
        traces: response.data.traces,
        pagination: {
          has_more: response.data.has_more,
          total_count: response.data.count,
          next_cursor: response.data.has_more ? String(response.data.offset + response.data.limit) : undefined,
        }
      };
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
