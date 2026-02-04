"""Pydantic models for ollyScale v2 API."""

from typing import Any

from pydantic import BaseModel, Field

# ==================== Common Models ====================


class TimeRange(BaseModel):
    """Time range for queries."""

    start_time: str = Field(..., description="Start time in RFC3339 format (e.g., '2026-01-26T00:00:00Z')")
    end_time: str = Field(..., description="End time in RFC3339 format (e.g., '2026-01-26T23:59:59Z')")


class Filter(BaseModel):
    """Query filter."""

    field: str = Field(..., description="Field to filter on (e.g., 'service.name', 'http.method')")
    operator: str = Field(..., description="Operator: eq, ne, gt, lt, gte, lte, contains, regex")
    value: Any = Field(..., description="Filter value")


class PaginationRequest(BaseModel):
    """Pagination parameters for queries."""

    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    cursor: str | None = Field(None, description="Opaque cursor for pagination")


# Alias for backward compatibility with tests
Pagination = PaginationRequest


class PaginationResponse(BaseModel):
    """Pagination metadata in responses."""

    has_more: bool = Field(..., description="Whether more results are available")
    next_cursor: str | None = Field(None, description="Cursor for next page")
    total_count: int | None = Field(None, description="Total count (if available)")


# ==================== Trace Models ====================


class SpanAttribute(BaseModel):
    """OTEL span attribute."""

    key: str
    value: Any


class SpanEvent(BaseModel):
    """OTEL span event with RFC3339 timestamp."""

    name: str
    timestamp: str = Field(..., description="RFC3339 timestamp, e.g. '2026-01-25T17:30:45.123456789Z'")
    attributes: list[SpanAttribute] | None = None


class SpanLink(BaseModel):
    """OTEL span link."""

    trace_id: str
    span_id: str
    attributes: list[SpanAttribute] | None = None


class SpanStatus(BaseModel):
    """OTEL span status."""

    code: int = Field(..., description="Status code: 0=UNSET, 1=OK, 2=ERROR")
    message: str | None = None


class Span(BaseModel):
    """OTEL span representation with RFC3339 timestamps."""

    trace_id: str = Field(..., min_length=32, max_length=32)
    span_id: str = Field(..., min_length=16, max_length=16)
    parent_span_id: str | None = Field(None, min_length=16, max_length=16)
    name: str
    kind: int = Field(
        ..., description="SpanKind: 0=UNSPECIFIED, 1=INTERNAL, 2=SERVER, 3=CLIENT, 4=PRODUCER, 5=CONSUMER"
    )
    start_time: str = Field(..., description="RFC3339 timestamp, e.g. '2026-01-25T17:30:45.123456789Z'")
    end_time: str = Field(..., description="RFC3339 timestamp, e.g. '2026-01-25T17:30:45.123456789Z'")
    duration_seconds: float = Field(..., description="Duration in seconds with fractional precision")
    attributes: list[SpanAttribute] | None = None
    events: list[SpanEvent] | None = None
    links: list[SpanLink] | None = None
    status: SpanStatus | None = None
    resource: dict[str, Any] | None = None
    scope: dict[str, Any] | None = None
    service_name: str | None = Field(None, description="Service name from service dimension")
    service_namespace: str | None = Field(None, description="Service namespace from namespace dimension")


class TraceIngestRequest(BaseModel):
    """Request body for trace ingestion."""

    resource_spans: list[dict[str, Any]] = Field(..., description="OTLP ResourceSpans array")


class TraceSearchRequest(BaseModel):
    """Request body for trace search."""

    time_range: TimeRange
    filters: list[Filter] | None = None
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)


class TraceSearchResponse(BaseModel):
    """Response for trace search."""

    traces: list[dict[str, Any]] = Field(..., description="Array of traces with spans")
    pagination: PaginationResponse


class SpanSearchRequest(BaseModel):
    """Request body for span search."""

    time_range: TimeRange
    filters: list[Filter] | None = None
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)


class SpanSearchResponse(BaseModel):
    """Response for span search."""

    spans: list[Span] = Field(..., description="Array of spans")
    pagination: PaginationResponse


# ==================== Log Models ====================


class LogRecord(BaseModel):
    """OTEL log record with RFC3339 timestamps."""

    log_id: str | None = Field(None, description="Unique log ID")
    timestamp: str = Field(..., description="RFC3339 timestamp, e.g. '2026-01-25T17:30:45.123456789Z'")
    observed_timestamp: str | None = Field(None, description="RFC3339 observed timestamp")
    severity_number: int | None = Field(None, ge=0, le=24)
    severity_text: str | None = None
    body: Any = Field(..., description="Log body (string or structured)")
    attributes: list[SpanAttribute] | None = None
    trace_id: str | None = Field(None, min_length=32, max_length=32)
    span_id: str | None = Field(None, min_length=16, max_length=16)
    flags: int | None = None
    service_name: str | None = None
    service_namespace: str | None = None
    resource: dict[str, Any] | None = None
    scope: dict[str, Any] | None = None


class LogIngestRequest(BaseModel):
    """Request body for log ingestion."""

    resource_logs: list[dict[str, Any]] = Field(..., description="OTLP ResourceLogs array")


class LogSearchRequest(BaseModel):
    """Request body for log search."""

    time_range: TimeRange
    filters: list[Filter] | None = None
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)


class LogSearchResponse(BaseModel):
    """Response for log search."""

    logs: list[LogRecord]
    pagination: PaginationResponse


# ==================== Metric Models ====================


class MetricDataPoint(BaseModel):
    """OTEL metric data point."""

    attributes: list[SpanAttribute] | None = None
    time_unix_nano: int
    value: Any = Field(..., description="Metric value (number, histogram, etc.)")


class Metric(BaseModel):
    """OTEL metric."""

    metric_id: str | None = Field(None, description="Unique metric ID")
    name: str
    description: str | None = None
    unit: str | None = None
    metric_type: str = Field(..., description="gauge, sum, histogram, summary, exponential_histogram")
    aggregation_temporality: int | str | None = None  # Accept both int (OTLP) and string (database storage)
    timestamp_ns: int | None = None
    value: Any | None = None
    attributes: dict[str, Any] | None = None
    exemplars: list[dict[str, Any]] | None = None
    service_name: str | None = None
    service_namespace: str | None = None
    data_points: list[MetricDataPoint] | list[dict] | None = None  # Accept both typed and raw dict
    resource: dict[str, Any] | None = None
    # Aggregated stats for catalog view
    resource_count: int | None = None
    label_count: int | None = None
    attribute_combinations: int | None = None
    scope: dict[str, Any] | None = None


class MetricIngestRequest(BaseModel):
    """Request body for metric ingestion."""

    resource_metrics: list[dict[str, Any]] = Field(..., description="OTLP ResourceMetrics array")


class MetricSearchRequest(BaseModel):
    """Request body for metric search."""

    time_range: TimeRange
    metric_names: list[str] | None = None
    filters: list[Filter] | None = None
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)
    include_attributes: bool = Field(
        default=False, description="Include unique attribute combinations for cardinality analysis"
    )


class MetricSearchResponse(BaseModel):
    """Response for metric search."""

    metrics: list[Metric]
    pagination: PaginationResponse


# ==================== Service Models ====================


class Service(BaseModel):
    """Service catalog entry with RED metrics."""

    name: str = Field(..., description="Service name")
    request_count: int = Field(0, description="Total request count in time range")
    error_count: int = Field(0, description="Total error count in time range")
    error_rate: float = Field(0.0, description="Error rate percentage")
    p50_latency_ms: float = Field(0.0, description="P50 latency in milliseconds")
    p95_latency_ms: float = Field(0.0, description="P95 latency in milliseconds")
    first_seen: int = Field(..., description="First seen timestamp (nanoseconds)")
    last_seen: int = Field(..., description="Last seen timestamp (nanoseconds)")
    # Optional attributes for extensibility
    namespace: str | None = None
    version: str | None = None
    attributes: dict[str, Any] | None = None


class ServiceSearchRequest(BaseModel):
    """Request body for service search."""

    time_range: TimeRange | None = None
    filters: list[Filter] | None = None


class ServiceListResponse(BaseModel):
    """Response for service list."""

    services: list[Service]
    total_count: int


class ServiceMapNode(BaseModel):
    """Node in service dependency map."""

    id: str = Field(..., description="Service ID or name")
    name: str
    type: str = Field(..., description="service, database, external, messaging")
    attributes: dict[str, Any] | None = None
    # OTEL semantic convention attributes for accurate type detection
    db_system: str | None = Field(
        None, description="Database system from db.system attribute (postgresql, mysql, redis, mongodb, etc.)"
    )
    messaging_system: str | None = Field(
        None, description="Messaging system from messaging.system attribute (rabbitmq, kafka, etc.)"
    )


class ServiceMapEdge(BaseModel):
    """Edge in service dependency map."""

    source: str = Field(..., description="Source service ID")
    target: str = Field(..., description="Target service ID")
    call_count: int = Field(..., description="Number of calls in time range")
    error_count: int = Field(0, description="Number of errors")
    avg_duration_ms: float | None = None


class ServiceMapResponse(BaseModel):
    """Response for service map."""

    nodes: list[ServiceMapNode]
    edges: list[ServiceMapEdge]
    time_range: TimeRange
