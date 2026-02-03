import type { TimeRange, Filter, PaginationRequest, PaginationResponse, SpanAttribute } from './common';

export interface LogRecord {
  log_id?: string;
  timestamp: string;  // RFC3339
  observed_timestamp?: string;
  severity_number?: number; // 0-24
  severity_text?: string;  // DEBUG, INFO, WARN, ERROR, FATAL
  body: string | Record<string, unknown>;
  attributes?: SpanAttribute[];
  trace_id?: string;
  span_id?: string;
  resource?: Record<string, unknown>;
  scope?: Record<string, unknown>;
  service_name?: string;
  service_namespace?: string;
}

export interface LogSearchRequest {
  time_range: TimeRange;
  filters?: Filter[];
  pagination?: PaginationRequest;
}

export interface LogSearchResponse {
  logs: LogRecord[];
  pagination: PaginationResponse;
}
