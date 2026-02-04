import type { TimeRange, Filter, PaginationRequest, PaginationResponse } from './common';

export interface ServiceMetrics {
  request_count: number;
  error_count: number;
  error_rate: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  span_count?: number; // Total spans for service
  rate?: number; // Requests per second
}

export interface Service {
  name: string;
  namespace?: string;
  metrics: ServiceMetrics;
  last_seen?: string;
}

export interface ServiceSearchRequest {
  time_range: TimeRange;
  filters?: Filter[];
  pagination?: PaginationRequest;
}

export interface ServiceListResponse {
  services: Service[];
  pagination: PaginationResponse;
}

// Service Map
export interface ServiceMapNode {
  id: string;
  name: string;
  namespace?: string;
  type: 'client' | 'server' | 'database' | 'messaging' | 'external';
  metrics?: ServiceMetrics;
  // OTEL semantic convention attributes for icon detection
  db_system?: string;  // e.g., 'postgresql', 'mysql', 'redis', 'mongodb'
  messaging_system?: string;  // e.g., 'rabbitmq', 'kafka'
}

export interface ServiceMapEdge {
  source: string;
  target: string;
  call_count: number;
  error_count?: number;
  avg_latency_ms?: number;
}

export interface ServiceMapResponse {
  nodes: ServiceMapNode[];
  edges: ServiceMapEdge[];
  time_range: TimeRange;
}
