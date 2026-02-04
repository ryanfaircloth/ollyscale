import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import apiClient from './client';

interface HealthStatus {
  status: string;
  redis_connected?: boolean;
  redis_memory?: string;
  uptime?: string;
  version?: string;
}

/**
 * Test API connectivity by hitting health endpoint
 * Uses centralized apiClient for consistent URL handling
 */
export function useHealthCheck() {
  return useQuery<HealthStatus, Error>({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await apiClient.get<HealthStatus>('/health');
      return response.data;
    },
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
    staleTime: 10000,
  });
}

/**
 * Check if the API is reachable
 * Uses centralized apiClient for consistent URL handling
 */
export async function testApiConnection(): Promise<{ success: boolean; message: string; data?: unknown }> {
  try {
    const response = await apiClient.get<HealthStatus>('/health', { timeout: 5000 });
    return {
      success: true,
      message: 'API is reachable',
      data: response.data,
    };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
        return {
          success: false,
          message: 'Cannot connect to API. Is the backend running?',
        };
      }
      if (error.response) {
        return {
          success: false,
          message: `API returned error: ${error.response.status} ${error.response.statusText}`,
        };
      }
      return {
        success: false,
        message: `Network error: ${error.message}`,
      };
    }
    return {
      success: false,
      message: `Unknown error: ${String(error)}`,
    };
  }
}
