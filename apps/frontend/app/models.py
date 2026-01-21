from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message describing what went wrong")
    model_config = {"json_schema_extra": {"example": {"detail": "Trace not found"}}}


class HealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"]
    redis: Literal["connected", "disconnected"]
    model_config = {"json_schema_extra": {"example": {"status": "healthy", "redis": "connected"}}}


class IngestResponse(BaseModel):
    status: Literal["ok"]
    model_config = {"json_schema_extra": {"example": {"status": "ok"}}}


class TraceSpan(BaseModel):
    span_id: str | None = Field(None, description="Unique span identifier")
    trace_id: str | None = Field(None, description="Trace ID this span belongs to")
    parent_span_id: str | None = Field(None, description="Parent span ID for hierarchy")
    name: str | None = Field(None, description="Span operation name")
    kind: int | None = Field(None, description="Span kind (internal, server, client, etc.)")
    startTimeUnixNano: int | None = Field(None, description="Start time in nanoseconds")
    endTimeUnixNano: int | None = Field(None, description="End time in nanoseconds")
    attributes: dict[str, Any] | None = Field(None, description="Span attributes")
    status: dict[str, Any] | None = Field(None, description="Span status")
    model_config = {
        "json_schema_extra": {
            "example": {
                "span_id": "abc123",
                "trace_id": "trace-xyz",
                "name": "GET /api/users",
                "kind": 2,
                "startTimeUnixNano": 1638360000000000000,
                "endTimeUnixNano": 1638360001000000000,
                "attributes": {"http.method": "GET", "http.status_code": 200},
                "status": {"code": 0},
            }
        }
    }


class TraceDetail(BaseModel):
    trace_id: str = Field(..., description="Unique trace identifier")
    spans: list[dict[str, Any]] = Field(..., description="All spans in the trace")
    span_count: int = Field(..., description="Total number of spans")
    model_config = {
        "json_schema_extra": {
            "example": {
                "trace_id": "trace-xyz",
                "spans": [{"span_id": "abc123", "name": "GET /api/users"}],
                "span_count": 1,
            }
        }
    }


class LogEntry(BaseModel):
    log_id: str | None = Field(None, description="Unique log identifier")
    timestamp: float | None = Field(None, description="Log timestamp (Unix)")
    trace_id: str | None = Field(None, description="Associated trace ID for correlation")
    span_id: str | None = Field(None, description="Associated span ID for correlation")
    severity: str | None = Field(None, description="Log severity level")
    body: str | None = Field(None, description="Log message body")
    attributes: dict[str, Any] | None = Field(None, description="Additional log attributes")
    model_config = {
        "json_schema_extra": {
            "example": {
                "log_id": "log-123",
                "timestamp": 1638360000.0,
                "trace_id": "trace-xyz",
                "severity": "INFO",
                "body": "User request processed successfully",
                "attributes": {"user_id": "user-456"},
            }
        }
    }


class MetricMetadata(BaseModel):
    name: str = Field(..., description="Metric name")
    type: str = Field(..., description="Metric type (gauge, counter, histogram, etc.)")
    unit: str = Field(default="", description="Metric unit")
    description: str = Field(default="", description="Metric description")
    resource_count: int = Field(..., description="Number of unique resource combinations")
    attribute_combinations: int = Field(..., description="Number of unique attribute combinations")
    label_count: int = Field(..., description="Number of label dimension keys")
    services: list[str] = Field(default=[], description="List of service names emitting this metric")
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "http.server.duration",
                "type": "histogram",
                "unit": "ms",
                "description": "HTTP request duration",
                "resource_count": 3,
                "attribute_combinations": 10,
                "services": ["frontend", "backend"],
            }
        }
    }
