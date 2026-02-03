import type { TimeRange, Filter, PaginationRequest, PaginationResponse } from './common';

export interface MetricDataPoint {
  timestamp: string;  // RFC3339
  value: number;
  attributes?: Record<string, string | number>;
}

export interface Metric {
  name: string;
  type: 'Gauge' | 'Counter' | 'Histogram' | 'Summary';
  unit?: string;
  description?: string;
  data_points: MetricDataPoint[];
  attributes?: Record<string, string>;
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
