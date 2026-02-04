import { type FieldSchema } from './QueryBuilder';

// Trace/Span field schema
export const TRACE_FIELD_SCHEMA: FieldSchema[] = [
  {
    field: 'service.name',
    label: 'Service Name',
    type: 'string',
    description: 'Name of the service',
  },
  {
    field: 'service.namespace',
    label: 'Service Namespace',
    type: 'string',
    description: 'Kubernetes namespace or similar grouping',
  },
  {
    field: 'http.method',
    label: 'HTTP Method',
    type: 'enum',
    enumValues: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'],
    description: 'HTTP request method',
  },
  {
    field: 'http.status_code',
    label: 'HTTP Status Code',
    type: 'number',
    description: 'HTTP response status code',
  },
  {
    field: 'http.route',
    label: 'HTTP Route',
    type: 'string',
    description: 'HTTP route pattern',
  },
  {
    field: 'span.kind',
    label: 'Span Kind',
    type: 'enum',
    enumValues: ['INTERNAL', 'SERVER', 'CLIENT', 'PRODUCER', 'CONSUMER'],
    description: 'Type of span',
  },
  {
    field: 'status.code',
    label: 'Status Code',
    type: 'enum',
    enumValues: ['UNSET', 'OK', 'ERROR'],
    description: 'Span status',
  },
  {
    field: 'duration_seconds',
    label: 'Duration (seconds)',
    type: 'number',
    description: 'Span duration in seconds',
  },
  {
    field: 'trace_id',
    label: 'Trace ID',
    type: 'string',
    description: 'Trace identifier',
  },
  {
    field: 'span_id',
    label: 'Span ID',
    type: 'string',
    description: 'Span identifier',
  },
];

// Log field schema
export const LOG_FIELD_SCHEMA: FieldSchema[] = [
  {
    field: 'severity_text',
    label: 'Severity',
    type: 'enum',
    enumValues: ['FATAL', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'],
    description: 'Log severity level',
  },
  {
    field: 'severity_number',
    label: 'Severity Number',
    type: 'number',
    description: 'Numeric severity (0-24)',
  },
  {
    field: 'body',
    label: 'Log Body',
    type: 'string',
    description: 'Log message content',
  },
  {
    field: 'trace_id',
    label: 'Trace ID',
    type: 'string',
    description: 'Associated trace ID',
  },
  {
    field: 'span_id',
    label: 'Span ID',
    type: 'string',
    description: 'Associated span ID',
  },
  {
    field: 'service.name',
    label: 'Service Name',
    type: 'string',
    description: 'Name of the service',
  },
  {
    field: 'service.namespace',
    label: 'Service Namespace',
    type: 'string',
    description: 'Kubernetes namespace or similar grouping',
  },
];

// Metric field schema
export const METRIC_FIELD_SCHEMA: FieldSchema[] = [
  {
    field: 'metric.name',
    label: 'Metric Name',
    type: 'string',
    description: 'Name of the metric',
  },
  {
    field: 'metric.type',
    label: 'Metric Type',
    type: 'enum',
    enumValues: ['Gauge', 'Counter', 'Histogram', 'Summary'],
    description: 'Type of metric',
  },
  {
    field: 'service.name',
    label: 'Service Name',
    type: 'string',
    description: 'Name of the service',
  },
  {
    field: 'service.namespace',
    label: 'Service Namespace',
    type: 'string',
    description: 'Kubernetes namespace or similar grouping',
  },
];

// Service field schema
export const SERVICE_FIELD_SCHEMA: FieldSchema[] = [
  {
    field: 'service.name',
    label: 'Service Name',
    type: 'string',
    description: 'Name of the service',
  },
  {
    field: 'service.namespace',
    label: 'Service Namespace',
    type: 'string',
    description: 'Kubernetes namespace or similar grouping',
  },
  {
    field: 'metrics.error_rate',
    label: 'Error Rate',
    type: 'number',
    description: 'Percentage of failed requests',
  },
  {
    field: 'metrics.request_count',
    label: 'Request Count',
    type: 'number',
    description: 'Total number of requests',
  },
];
