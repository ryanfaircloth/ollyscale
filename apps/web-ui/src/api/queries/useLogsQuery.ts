import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import apiClient from '../client';
import type { LogSearchRequest, LogSearchResponse, OtlpLogSearchResponse } from '../types/log';
import { rfc3339ToNanoseconds } from '../utils/timestamp';

export function useLogsQuery(
  request: LogSearchRequest,
  options?: Omit<UseQueryOptions<LogSearchResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['logs', 'search', request],
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

      const traceFilter = request.filters?.find(f => f.field === 'trace_id');
      if (traceFilter) {
        Object.assign(params, { trace_id: traceFilter.value });
      }

      const severityFilter = request.filters?.find(f => f.field === 'severity' || f.field === 'severity_number');
      if (severityFilter) {
        Object.assign(params, { severity_min: severityFilter.value });
      }

      const response = await apiClient.get<OtlpLogSearchResponse>('/api/logs/search', { params });

      // Convert to old response format for compatibility
      return {
        logs: response.data.logs,
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
