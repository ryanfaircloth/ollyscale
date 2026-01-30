"""Tests for API models."""

import pytest
from pydantic import ValidationError

from app.models.api import (
    Filter,
    LogRecord,
    Metric,
    MetricDataPoint,
    PaginationRequest,
    Span,
    SpanAttribute,
    SpanStatus,
    TimeRange,
    TraceIngestRequest,
)


def test_time_range_valid():
    """Test valid TimeRange."""
    tr = TimeRange(start_time="2001-09-09T01:46:40Z", end_time="2033-05-18T03:33:20Z")
    assert tr.start_time == "2001-09-09T01:46:40Z"
    assert tr.end_time == "2033-05-18T03:33:20Z"


def test_filter_valid():
    """Test valid Filter."""
    f = Filter(field="service.name", operator="eq", value="my-service")
    assert f.field == "service.name"
    assert f.operator == "eq"
    assert f.value == "my-service"


def test_pagination_request_defaults():
    """Test PaginationRequest defaults."""
    pr = PaginationRequest()
    assert pr.limit == 100
    assert pr.cursor is None


def test_pagination_request_limit_validation():
    """Test PaginationRequest limit validation."""
    # Valid limits
    pr1 = PaginationRequest(limit=1)
    assert pr1.limit == 1

    pr2 = PaginationRequest(limit=1000)
    assert pr2.limit == 1000

    # Invalid limits should raise ValidationError
    with pytest.raises(ValidationError):
        PaginationRequest(limit=0)

    with pytest.raises(ValidationError):
        PaginationRequest(limit=1001)


def test_span_valid():
    """Test valid Span."""
    span = Span(
        trace_id="0" * 32,
        span_id="0" * 16,
        name="test-span",
        kind=1,
        start_time="2001-09-09T01:46:40Z",
        end_time="2001-09-09T01:46:41Z",
        duration_seconds=1.0,
    )
    assert span.trace_id == "0" * 32
    assert span.span_id == "0" * 16
    assert span.name == "test-span"
    assert span.kind == 1


def test_span_invalid_trace_id():
    """Test Span with invalid trace_id."""
    with pytest.raises(ValidationError):
        Span(
            trace_id="short",  # Too short
            span_id="0" * 16,
            name="test-span",
            kind=1,
            start_time="2001-09-09T01:46:40Z",
            end_time="2001-09-09T01:46:41Z",
            duration_seconds=1.0,
        )


def test_span_status():
    """Test SpanStatus."""
    status = SpanStatus(code=2, message="Error occurred")
    assert status.code == 2
    assert status.message == "Error occurred"


def test_span_attribute():
    """Test SpanAttribute."""
    attr = SpanAttribute(key="http.method", value="GET")
    assert attr.key == "http.method"
    assert attr.value == "GET"


def test_log_record_valid():
    """Test valid LogRecord."""
    log = LogRecord(
        timestamp="2001-09-09T01:46:40Z",
        severity_number=9,
        severity_text="INFO",
        body="Test log message",
    )
    assert log.timestamp == "2001-09-09T01:46:40Z"
    assert log.severity_number == 9
    assert log.body == "Test log message"


def test_log_record_with_trace_correlation():
    """Test LogRecord with trace correlation."""
    log = LogRecord(
        timestamp="2001-09-09T01:46:40Z",
        body="Correlated log",
        trace_id="0" * 32,
        span_id="0" * 16,
    )
    assert log.trace_id == "0" * 32
    assert log.span_id == "0" * 16


def test_metric_data_point():
    """Test MetricDataPoint."""
    dp = MetricDataPoint(
        time_unix_nano=1000000000000000000,
        value=42.5,
        attributes=[SpanAttribute(key="host", value="server1")],
    )
    assert dp.time_unix_nano == 1000000000000000000
    assert dp.value == 42.5
    assert len(dp.attributes) == 1


def test_metric_valid():
    """Test valid Metric."""
    metric = Metric(
        name="http.server.request.duration",
        metric_type="histogram",
        unit="ms",
        data_points=[MetricDataPoint(time_unix_nano=1000000000000000000, value={"buckets": [10, 50, 100]})],
    )
    assert metric.name == "http.server.request.duration"
    assert metric.metric_type == "histogram"
    assert metric.unit == "ms"
    assert len(metric.data_points) == 1


def test_trace_ingest_request():
    """Test TraceIngestRequest."""
    request = TraceIngestRequest(
        resource_spans=[
            {
                "resource": {"attributes": [{"key": "service.name", "value": "test"}]},
                "scope_spans": [
                    {
                        "scope": {"name": "test-tracer"},
                        "spans": [
                            {
                                "trace_id": "0" * 32,
                                "span_id": "0" * 16,
                                "name": "test",
                                "kind": 1,
                                "start_time_unix_nano": 1000000000000000000,
                                "end_time_unix_nano": 2000000000000000000,
                            }
                        ],
                    }
                ],
            }
        ]
    )
    assert len(request.resource_spans) == 1
    assert len(request.resource_spans[0]["scope_spans"]) == 1
