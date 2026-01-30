"""Test fixtures for OTLP data structures.

Provides reusable fixtures for traces, logs, and metrics testing.
"""

import time
from typing import Any


def make_attribute(key: str, value: Any) -> dict:
    """Create OTLP attribute with proper type detection.

    Args:
        key: Attribute key
        value: Attribute value (str, int, float, bool, list)

    Returns:
        OTLP attribute dict with typed value
    """
    if isinstance(value, str):
        return {"key": key, "value": {"stringValue": value}}
    if isinstance(value, bool):  # Must check bool before int
        return {"key": key, "value": {"boolValue": value}}
    if isinstance(value, int):
        return {"key": key, "value": {"intValue": value}}
    if isinstance(value, float):
        return {"key": key, "value": {"doubleValue": value}}
    if isinstance(value, list):
        return {"key": key, "value": {"arrayValue": {"values": [{"stringValue": str(v)} for v in value]}}}
    return {"key": key, "value": {"stringValue": str(value)}}


def make_resource(service_name: str = "test-service", **attrs: Any) -> dict:
    """Create OTLP Resource.

    Args:
        service_name: Service name (required by OTEL)
        **attrs: Additional resource attributes

    Returns:
        OTLP Resource dict
    """
    attributes = [make_attribute("service.name", service_name)]
    attributes.extend([make_attribute(k, v) for k, v in attrs.items()])

    return {"attributes": attributes}


def make_span(
    trace_id: str = "0102030405060708090a0b0c0d0e0f10",
    span_id: str = "0102030405060708",
    parent_span_id: str = "",
    name: str = "test-span",
    kind: int = 1,  # INTERNAL
    start_time_unix_nano: int | None = None,
    end_time_unix_nano: int | None = None,
    **attrs: Any,
) -> dict:
    """Create OTLP Span.

    Args:
        trace_id: Trace ID (32 hex chars)
        span_id: Span ID (16 hex chars)
        parent_span_id: Parent span ID (empty for root)
        name: Span name
        kind: Span kind (1=INTERNAL, 2=SERVER, 3=CLIENT, 4=PRODUCER, 5=CONSUMER)
        start_time_unix_nano: Start time in nanoseconds (defaults to now)
        end_time_unix_nano: End time in nanoseconds (defaults to now + 100ms)
        **attrs: Span attributes

    Returns:
        OTLP Span dict
    """
    if start_time_unix_nano is None:
        start_time_unix_nano = int(time.time() * 1e9)
    if end_time_unix_nano is None:
        end_time_unix_nano = start_time_unix_nano + int(100e6)  # +100ms

    span = {
        "trace_id": trace_id,
        "span_id": span_id,
        "name": name,
        "kind": kind,
        "start_time_unix_nano": start_time_unix_nano,
        "end_time_unix_nano": end_time_unix_nano,
        "attributes": [make_attribute(k, v) for k, v in attrs.items()],
    }

    if parent_span_id:
        span["parent_span_id"] = parent_span_id

    return span


def make_resource_spans(service_name: str = "test-service", spans: list[dict] | None = None) -> dict:
    """Create OTLP ResourceSpans.

    Args:
        service_name: Service name
        spans: List of spans (creates one default span if None)

    Returns:
        OTLP ResourceSpans dict
    """
    if spans is None:
        spans = [make_span()]

    return {
        "resource": make_resource(service_name),
        "scope_spans": [{"scope": {"name": "test-scope", "version": "1.0.0"}, "spans": spans}],
    }


def make_log_record(
    time_unix_nano: int | None = None,
    observed_time_unix_nano: int | None = None,
    severity_number: int = 9,  # INFO
    severity_text: str = "INFO",
    body: str = "Test log message",
    trace_id: str = "",
    span_id: str = "",
    **attrs: Any,
) -> dict:
    """Create OTLP LogRecord.

    Args:
        time_unix_nano: Log timestamp (defaults to now)
        observed_time_unix_nano: Observed timestamp (defaults to time_unix_nano)
        severity_number: Severity number (9=INFO, 17=ERROR)
        severity_text: Severity text
        body: Log message
        trace_id: Trace ID for correlation (empty if not correlated)
        span_id: Span ID for correlation (empty if not correlated)
        **attrs: Log attributes

    Returns:
        OTLP LogRecord dict
    """
    if time_unix_nano is None:
        time_unix_nano = int(time.time() * 1e9)
    if observed_time_unix_nano is None:
        observed_time_unix_nano = time_unix_nano

    log_record = {
        "time_unix_nano": time_unix_nano,
        "observed_time_unix_nano": observed_time_unix_nano,
        "severity_number": severity_number,
        "severity_text": severity_text,
        "body": {"stringValue": body},
        "attributes": [make_attribute(k, v) for k, v in attrs.items()],
    }

    if trace_id:
        log_record["trace_id"] = trace_id
    if span_id:
        log_record["span_id"] = span_id

    return log_record


def make_resource_logs(service_name: str = "test-service", log_records: list[dict] | None = None) -> dict:
    """Create OTLP ResourceLogs.

    Args:
        service_name: Service name
        log_records: List of log records (creates one default if None)

    Returns:
        OTLP ResourceLogs dict
    """
    if log_records is None:
        log_records = [make_log_record()]

    return {
        "resource": make_resource(service_name),
        "scope_logs": [{"scope": {"name": "test-scope", "version": "1.0.0"}, "log_records": log_records}],
    }


def make_gauge_datapoint(
    time_unix_nano: int | None = None,
    value: int | float = 42,
    **attrs: Any,
) -> dict:
    """Create OTLP Gauge DataPoint.

    Args:
        time_unix_nano: Timestamp (defaults to now)
        value: Gauge value
        **attrs: DataPoint attributes

    Returns:
        OTLP NumberDataPoint dict
    """
    if time_unix_nano is None:
        time_unix_nano = int(time.time() * 1e9)

    datapoint = {"time_unix_nano": time_unix_nano, "attributes": [make_attribute(k, v) for k, v in attrs.items()]}

    if isinstance(value, int):
        datapoint["as_int"] = value
    else:
        datapoint["as_double"] = value

    return datapoint


def make_gauge_metric(name: str = "test.gauge", datapoints: list[dict] | None = None) -> dict:
    """Create OTLP Gauge Metric.

    Args:
        name: Metric name
        datapoints: List of datapoints (creates one default if None)

    Returns:
        OTLP Metric dict with gauge
    """
    if datapoints is None:
        datapoints = [make_gauge_datapoint()]

    return {
        "name": name,
        "description": f"Test gauge metric {name}",
        "unit": "1",
        "gauge": {"data_points": datapoints},
    }


def make_metric(
    name: str = "test.metric",
    unit: str = "1",
    value: float | int = 100.0,
    attributes: dict[str, Any] | None = None,
    timestamp_ns: int | None = None,
) -> dict:
    """Create OTLP Metric (gauge type) with flexible parameters.

    Args:
        name: Metric name
        unit: Unit of measurement
        value: Metric value
        attributes: Metric attributes (labels)
        timestamp_ns: Timestamp in nanoseconds (defaults to current time)

    Returns:
        OTLP Metric dict with gauge
    """
    if timestamp_ns is None:
        timestamp_ns = int(time.time() * 1e9)

    attrs = []
    if attributes:
        attrs = [make_attribute(k, v) for k, v in attributes.items()]

    datapoint = make_gauge_datapoint(
        value=value,
        attributes=attrs,
        time_unix_nano=timestamp_ns,
    )

    return {
        "name": name,
        "description": f"Test metric {name}",
        "unit": unit,
        "gauge": {"data_points": [datapoint]},
    }


def make_resource_metrics(service_name: str = "test-service", metrics: list[dict] | None = None) -> dict:
    """Create OTLP ResourceMetrics.

    Args:
        service_name: Service name
        metrics: List of metrics (creates one default gauge if None)

    Returns:
        OTLP ResourceMetrics dict
    """
    if metrics is None:
        metrics = [make_gauge_metric()]

    return {
        "resource": make_resource(service_name),
        "scope_metrics": [{"scope": {"name": "test-scope", "version": "1.0.0"}, "metrics": metrics}],
    }


# --- INVALID/EDGE CASE FIXTURES ---


def make_invalid_span_missing_required() -> dict:
    """Create invalid span missing required fields."""
    return {
        "name": "incomplete-span",
        # Missing: traceId, spanId, startTimeUnixNano, endTimeUnixNano
    }


def make_invalid_span_malformed_ids() -> dict:
    """Create span with malformed hex IDs."""
    return make_span(
        trace_id="not-hex-invalid",  # Invalid hex
        span_id="short",  # Too short
    )


def make_empty_resource_spans() -> dict:
    """Create ResourceSpans with no spans."""
    return {
        "resource": make_resource("empty-service"),
        "scope_spans": [{"scope": {"name": "test-scope"}, "spans": []}],
    }


def make_correlated_trace_and_logs(
    trace_id: str = "0102030405060708090a0b0c0d0e0f10", service_name: str = "test-service"
) -> tuple[dict, dict]:
    """Create correlated trace and logs for testing trace-log linking.

    Args:
        trace_id: Shared trace ID
        service_name: Service name

    Returns:
        Tuple of (ResourceSpans, ResourceLogs) with matching trace_id
    """
    span_id = "0102030405060708"

    spans = [make_span(trace_id=trace_id, span_id=span_id, name="test-operation")]

    logs = [
        make_log_record(
            body="Log entry correlated with trace",
            trace_id=trace_id,
            span_id=span_id,
            level="info",
        )
    ]

    return (make_resource_spans(service_name, spans), make_resource_logs(service_name, logs))
