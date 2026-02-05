import type { TimeRange, Filter, PaginationRequest, PaginationResponse } from './common';

export interface MetricDataPoint {
  time: number;  // nanoseconds since Unix epoch
  start_time?: number;  // nanoseconds since Unix epoch
  flags?: number;
  attributes?: Record<string, unknown>;
  // Type-specific fields (only present for relevant metric types)
  value?: number;  // Gauge/Sum
  count?: number;  // Histogram/ExponentialHistogram/Summary
  sum?: number;
  min?: number;
  max?: number;
  explicit_bounds?: number[];
  bucket_counts?: number[];
  scale?: number;
  zero_count?: number;
  positive_offset?: number;
  positive_bucket_counts?: number[];
  negative_offset?: number;
  negative_bucket_counts?: number[];
  quantile_values?: Array<{ quantile: number; value: number }>;
  exemplars?: unknown[];
  // Legacy timestamp field for compatibility
  timestamp?: string;  // RFC3339
}

export interface Metric {
  name: string;
  type: 'Gauge' | 'Sum' | 'Histogram' | 'ExponentialHistogram' | 'Summary';
  unit?: string;
  aggregation_temporality?: string;
  resource?: {
    service_name?: string;
    service_namespace?: string;
  };
  scope?: {
    name?: string;
    version?: string;
  };
  data_points: MetricDataPoint[];
  // Legacy fields for compatibility
  description?: string;
  attributes?: Record<string, string>;
}

export interface MetricSearchRequest {
  time_range: TimeRange;
  filters?: Filter[];
  pagination?: PaginationRequest;
}

export interface MetricSearchResponse {
  metrics: Metric[];
  count: number;
  total_data_points: number;
  limit: number;
  has_more: boolean;
  // Legacy pagination for compatibility
  pagination?: PaginationResponse;
}

export interface MetricCardinality {
  metric_name: string;
  series_count: number;
  label_values: Record<string, string[]>;
}
