import pytest
from pydantic import ValidationError

from app.models import LogEntry, MetricMetadata, TraceSpan


def test_trace_span_valid():
    span = TraceSpan(
        span_id="abc123",
        trace_id="trace-xyz",
        name="GET /api/users",
        kind=2,
        startTimeUnixNano=1638360000000000000,
        endTimeUnixNano=1638360001000000000,
        attributes={"http.method": "GET", "http.status_code": 200},
        status={"code": 0},
    )
    assert span.span_id == "abc123"
    assert span.name == "GET /api/users"
    assert span.attributes["http.method"] == "GET"


def test_trace_span_invalid():
    with pytest.raises(ValidationError):
        TraceSpan(span_id=123)  # span_id must be str or None


def test_log_entry_valid():
    log = LogEntry(
        log_id="log-123",
        timestamp=1638360000.0,
        trace_id="trace-xyz",
        severity="INFO",
        body="User request processed successfully",
        attributes={"user_id": "user-456"},
    )
    assert log.log_id == "log-123"
    assert log.severity == "INFO"
    assert log.attributes["user_id"] == "user-456"


def test_log_entry_invalid():
    with pytest.raises(ValidationError):
        LogEntry(timestamp="not-a-float")


def test_metric_metadata_valid():
    metric = MetricMetadata(
        name="http.server.duration",
        type="histogram",
        unit="ms",
        description="HTTP request duration",
        resource_count=3,
        attribute_combinations=10,
        label_count=2,
        services=["frontend", "backend"],
    )
    assert metric.name == "http.server.duration"
    assert metric.type == "histogram"
    assert metric.services == ["frontend", "backend"]


def test_metric_metadata_invalid():
    with pytest.raises(ValidationError):
        MetricMetadata(
            name=123, type=None, resource_count="bad", attribute_combinations=None, label_count=None, services=None
        )
