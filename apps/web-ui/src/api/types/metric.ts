import type { TimeRange, Filter, PaginationRequest, PaginationResponse } from './common';

export interface MetricDataPoint {
  timestamp: string;  // RFC3339
  value: number;
  attributes?: Record<string, string | number>;
}

export interface Metric {
  metric_id?: string;
  name: string;
  metric_type: string;  // 'gauge', 'sum', 'histogram', 'summary', etc.
  unit?: string;
  description?: string;
  aggregation_temporality?: string | number;
  timestamp_ns?: number;
  value?: any;
  data_points: MetricDataPoint[] | any[];  // Support both typed and raw dict
  attributes?: Record<string, any>;
  service_name?: string;
  service_namespace?: string | null;
  resource?: Record<string, any>;
  exemplars?: any[];
  // Aggregated stats for catalog view
  resource_count?: number;
  label_count?: number;
  attribute_combinations?: number;
  scope?: Record<string, any>;
}

export interface MetricSearchRequest {
  time_range: TimeRange;
  filters?: Filter[];
  pagination?: PaginationRequest;
}

export interface MetricSearchResponse {
  metrics: Metric[];
  pagination: PaginationResponse;
}

export interface MetricCardinality {
  metric_name: string;
  series_count: number;
  label_values: Record<string, string[]>;
}
