import type { TimeRange, Filter, PaginationRequest, PaginationResponse, Span, Trace } from './common';

// Trace Search
export interface TraceSearchRequest {
  time_range: TimeRange;
  filters?: Filter[];
  pagination?: PaginationRequest;
}

export interface TraceSearchResponse {
  traces: Trace[];
  pagination: PaginationResponse;
}

// Span Search
export interface SpanSearchRequest {
  time_range: TimeRange;
  filters?: Filter[];
  pagination?: PaginationRequest;
}

export interface SpanSearchResponse {
  spans: Span[];
  pagination: PaginationResponse;
}

// Trace Detail
export interface TraceDetailResponse {
  trace_id: string;
  spans: Span[];
  root_service_name?: string;
  start_time?: string;
  end_time?: string;
  duration_seconds?: number;
}

// New OTLP API types
export interface TraceSearchParams {
  start_time: number; // nanoseconds
  end_time: number; // nanoseconds
  service_name?: string;
  min_duration_ns?: number;
  limit?: number;
  offset?: number;
}

export interface OtlpTraceSearchResponse {
  traces: Trace[];
  count: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
