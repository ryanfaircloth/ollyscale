import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import apiClient from '../client';
import type { ServiceSearchRequest, ServiceListResponse, ServiceMapResponse } from '../types/service';
import type { TimeRange } from '../types/common';

export function useServicesQuery(
  request: ServiceSearchRequest,
  options?: Omit<UseQueryOptions<ServiceListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['services', 'list', request],
    queryFn: async () => {
      const response = await apiClient.post<ServiceListResponse>('/api/services', request);
      return response.data;
    },
    ...options,
  });
}

export function useServiceMapQuery(
  timeRange: TimeRange,
  options?: Omit<UseQueryOptions<ServiceMapResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: ['services', 'map', timeRange],
    queryFn: async () => {
      const response = await apiClient.post<ServiceMapResponse>('/api/service-map', { time_range: timeRange });
      return response.data;
    },
    ...options,
  });
}
