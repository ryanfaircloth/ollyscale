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
