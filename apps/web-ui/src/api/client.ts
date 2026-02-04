import axios, { type AxiosInstance, type AxiosError } from 'axios';

// Use relative URL (empty string) to use same origin
// For local dev with 'npm run dev', vite.config.ts proxy handles /api routing
// For production, requests go to same origin where HTTPRoute handles routing
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Enhanced error type with user-friendly messages
 */
export interface APIError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
}

/**
 * Transform Axios errors into user-friendly error messages
 */
function transformError(error: AxiosError): APIError {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data as Record<string, unknown>;

    // Extract error message from response
    const serverMessage = (data?.message as string) || (data?.error as string) || (data?.detail as string);

    switch (status) {
      case 400:
        return {
          message: serverMessage || 'Invalid request. Please check your query parameters.',
          status,
          code: 'BAD_REQUEST',
          details: data,
        };
      case 401:
        return {
          message: 'Unauthorized. Please check your authentication.',
          status,
          code: 'UNAUTHORIZED',
        };
      case 403:
        return {
          message: 'Access forbidden. You do not have permission for this action.',
          status,
          code: 'FORBIDDEN',
        };
      case 404:
        return {
          message: serverMessage || 'Resource not found.',
          status,
          code: 'NOT_FOUND',
        };
      case 422:
        return {
          message: serverMessage || 'Validation error. Please check your input.',
          status,
          code: 'VALIDATION_ERROR',
          details: data,
        };
      case 429:
        return {
          message: 'Too many requests. Please slow down.',
          status,
          code: 'RATE_LIMITED',
        };
      case 500:
        return {
          message: 'Internal server error. Please try again later.',
          status,
          code: 'SERVER_ERROR',
          details: data,
        };
      case 503:
        return {
          message: 'Service temporarily unavailable. Please try again later.',
          status,
          code: 'SERVICE_UNAVAILABLE',
        };
      default:
        return {
          message: serverMessage || `Request failed with status ${status}`,
          status,
          code: 'UNKNOWN_ERROR',
          details: data,
        };
    }
  } else if (error.request) {
    // Request made but no response (network error)
    return {
      message: 'Network error. Please check your connection and try again.',
      code: 'NETWORK_ERROR',
    };
  } else if (error.code === 'ECONNABORTED') {
    // Request timeout
    return {
      message: 'Request timeout. The server took too long to respond.',
      code: 'TIMEOUT',
    };
  } else {
    // Something else happened
    return {
      message: error.message || 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR',
    };
  }
}

// Create axios instance with retry configuration
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth tokens or headers here if needed
    // Example: config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => {
    return Promise.reject(transformError(error));
  }
);

// Response interceptor with enhanced error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    const apiError = transformError(error);

    // Log error for debugging (only in development)
    if (import.meta.env.DEV) {
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: apiError.status,
        message: apiError.message,
        details: apiError.details,
      });
    }

    // Reject with our enhanced error
    return Promise.reject(apiError);
  }
);

export default apiClient;
