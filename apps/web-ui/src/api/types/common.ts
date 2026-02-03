// Common types matching backend API models

export interface TimeRange {
  start_time: string; // RFC3339 format
  end_time: string;   // RFC3339 format
}

export interface Filter {
  field: string;      // e.g., 'service.name', 'http.method'
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains' | 'regex';
  value: string | number | boolean;
}

export interface PaginationRequest {
  limit?: number;     // Default 100, max 1000
  cursor?: string;    // Opaque cursor for pagination
}

export interface PaginationResponse {
  has_more: boolean;
  next_cursor?: string;
  total_count?: number;
}

export interface SpanAttribute {
  key: string;
  value: string | number | boolean | null;
}

export interface SpanEvent {
  name: string;
  timestamp: string;  // RFC3339
  attributes?: SpanAttribute[];
}

export interface SpanLink {
  trace_id: string;
  span_id: string;
  attributes?: SpanAttribute[];
}

export interface SpanStatus {
  code: 0 | 1 | 2;    // 0=UNSET, 1=OK, 2=ERROR
  message?: string;
}

export interface Span {
  trace_id: string;
  span_id: string;
  parent_span_id?: string;
  name: string;
  kind: 0 | 1 | 2 | 3 | 4 | 5;  // 0=UNSPECIFIED, 1=INTERNAL, 2=SERVER, 3=CLIENT, 4=PRODUCER, 5=CONSUMER
  start_time: string;   // RFC3339
  end_time: string;     // RFC3339
  duration_seconds: number;
  attributes?: SpanAttribute[];
  events?: SpanEvent[];
  links?: SpanLink[];
  status?: SpanStatus;
  resource?: Record<string, unknown>;
  scope?: Record<string, unknown>;
  service_name?: string;
  service_namespace?: string;
}

export interface MetricDataPoint {
  timestamp: string;  // ISO 8601 timestamp
  value: number | string;  // Metric value
  attributes?: Record<string, unknown>;
}

export interface Trace {
  trace_id: string;
  spans: Span[];
  root_service_name?: string;
  start_time?: string;
  end_time?: string;
  duration_seconds?: number;
  root_span_name?: string;
  root_span_method?: string;         // http.method or http.request.method
  root_span_route?: string;          // http.route
  root_span_url?: string;            // http.url or url.full
  root_span_target?: string;         // Computed: url > route > http.target
  root_span_status_code?: number;    // http.status_code or http.response.status_code
  root_span_host?: string;           // http.host or net.host.name
  root_span_scheme?: string;         // http.scheme or url.scheme
}
