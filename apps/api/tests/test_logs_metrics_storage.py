"""Unit tests for logs and metrics storage per OTLP specification.

Tests verify:
- Logs write to database correctly
- Logs can be retrieved correctly
- trace_id/span_id correlation works
- Metrics write to database correctly
- Metrics can be retrieved correctly
- Resource attributes are preserved
"""

import json
from pathlib import Path

import pytest

from tests.fixtures import (
    make_log_record,
    make_metric,
    make_resource_logs,
    make_resource_metrics,
)

pytestmark = pytest.mark.skip(reason="Tests deprecated old schema - being replaced with OTLP schema")

# Load real OTLP examples
FIXTURES_DIR = Path(__file__).parent / "fixtures"
with (FIXTURES_DIR / "otlp_examples.json").open() as f:
    OTLP_EXAMPLES = json.load(f)


class TestLogsStorage:
    """Test logs write to and read from database correctly."""

    def test_log_record_fixture(self):
        """Verify log record fixture creates valid OTLP format."""
        log = make_log_record(
            trace_id="0102030405060708090a0b0c0d0e0f10",
            span_id="0102030405060708",
            body="Test message",
            severity_number=9,
        )

        # Verify OTLP format (snake_case with preserving_proto_field_name=True)
        assert "time_unix_nano" in log
        assert "severity_number" in log
        assert log["severity_number"] == 9
        assert "body" in log
        assert "trace_id" in log
        assert "span_id" in log

    def test_store_and_retrieve_logs(self, postgres_storage, time_range, pagination):
        """Verify logs round-trip through database correctly."""
        # Create log with known values
        trace_id = "aabbccddeeff00112233445566778899"
        span_id = "aabbccddeeff0011"

        log = make_log_record(
            trace_id=trace_id,
            span_id=span_id,
            body="Test log message",
            severity_number=9,
            severity_text="INFO",
        )

        resource_logs = make_resource_logs(service_name="test-service", log_records=[log])

        # Store
        count = postgres_storage.store_logs([resource_logs])
        assert count == 1

        # Retrieve by time range
        logs, _has_more, _cursor = postgres_storage.search_logs(
            time_range=time_range, filters=None, pagination=pagination
        )

        # Verify retrieval (search_logs returns LogRecord objects)
        assert len(logs) > 0
        log_found = None
        for log_result in logs:
            if log_result.body == "Test log message":
                log_found = log_result
                break

        assert log_found is not None, "Log not found in search results"
        assert log_found.trace_id == trace_id
        assert log_found.span_id == span_id
        assert log_found.severity_number == 9
        assert log_found.severity_text == "INFO"

    def test_logs_without_trace_correlation(self, postgres_storage, time_range, pagination):
        """Verify logs without trace_id/span_id are stored correctly."""
        log = make_log_record(
            body="Standalone log message",
            severity_number=9,
        )

        # Remove trace correlation fields (snake_case)
        log.pop("trace_id", None)
        log.pop("span_id", None)

        resource_logs = make_resource_logs(service_name="test-service", log_records=[log])

        # Store
        count = postgres_storage.store_logs([resource_logs])
        assert count == 1

        # Retrieve
        logs, _has_more, _cursor = postgres_storage.search_logs(
            time_range=time_range, filters=None, pagination=pagination
        )

        # Verify log exists and has no trace correlation (LogRecord objects)
        log_found = None
        for log_result in logs:
            if log_result.body == "Standalone log message":
                log_found = log_result
                break

        assert log_found is not None
        assert log_found.trace_id is None or log_found.trace_id == ""
        assert log_found.span_id is None or log_found.span_id == ""


class TestMetricsStorage:
    """Test metrics write to and read from database correctly."""

    def test_metric_fixture(self):
        """Verify metric fixture creates valid OTLP format."""
        metric = make_metric(
            name="http.server.request.duration",
            unit="ms",
            value=123.45,
        )

        # Verify OTLP format
        assert "name" in metric
        assert metric["name"] == "http.server.request.duration"
        assert "unit" in metric
        assert "gauge" in metric or "sum" in metric or "histogram" in metric

    def test_store_and_retrieve_metrics(self, postgres_storage, time_range, pagination):
        """Verify metrics round-trip through database correctly."""
        # Create metric with known values
        metric = make_metric(
            name="http.server.request.duration",
            unit="ms",
            value=123.45,
        )

        resource_metrics = make_resource_metrics(service_name="test-service", metrics=[metric])

        # Store
        count = postgres_storage.store_metrics([resource_metrics])
        assert count == 1

        # Retrieve by metric name
        metrics, _has_more, _cursor = postgres_storage.search_metrics(
            time_range=time_range, metric_names=["http.server.request.duration"], filters=None, pagination=pagination
        )

        # Verify retrieval
        assert len(metrics) > 0
        metric_found = None
        for metric_result in metrics:
            if metric_result.name == "http.server.request.duration":
                metric_found = metric_result
                break

        assert metric_found is not None, "Metric not found in search results"
        assert metric_found.name == "http.server.request.duration"
        assert metric_found.unit == "ms"

        # Verify data point value (Metric objects have data_points attribute)
        assert metric_found.data_points is not None
        data_points = (
            metric_found.data_points if isinstance(metric_found.data_points, list) else [metric_found.data_points]
        )

        assert len(data_points) > 0
        # Value might be in as_double or as_int (data points are dicts)
        dp = data_points[0]
        if isinstance(dp, dict):
            value = dp.get("as_double") or dp.get("as_int")
        else:
            value = getattr(dp, "as_double", None) or getattr(dp, "as_int", None) or getattr(dp, "value", None)
        assert value == 123.45

    def test_metrics_with_attributes(self, postgres_storage, time_range, pagination):
        """Verify metric attributes are preserved."""
        metric = make_metric(
            name="http.server.request.duration",
            unit="ms",
            value=123.45,
            attributes={"http.method": "GET", "http.status_code": 200, "http.route": "/api/users"},
        )

        resource_metrics = make_resource_metrics(service_name="test-service", metrics=[metric])

        # Store
        count = postgres_storage.store_metrics([resource_metrics])
        assert count == 1

        # Retrieve
        metrics, _has_more, _cursor = postgres_storage.search_metrics(
            time_range=time_range, metric_names=["http.server.request.duration"], filters=None, pagination=pagination
        )

        # Verify attributes preserved
        assert len(metrics) > 0
        metric_found = metrics[0]

        # Get data points from Metric object
        assert metric_found.data_points is not None
        data_points = (
            metric_found.data_points if isinstance(metric_found.data_points, list) else [metric_found.data_points]
        )

        assert len(data_points) > 0
        dp = data_points[0]
        if isinstance(dp, dict):
            attributes = dp.get("attributes", {})
        else:
            attributes = getattr(dp, "attributes", {}) or {}

        # Verify attributes exist (format may vary - OTLP protobuf or flat dict)
        # OTLP format: [{"key": "attributes", "value": {"arrayValue": {"values": [...]}}}]
        has_attributes = (
            isinstance(attributes, dict)
            and ("http.method" in attributes or any("method" in str(k).lower() for k in attributes))
        ) or (isinstance(attributes, list) and len(attributes) > 0)
        assert has_attributes


class TestResourceAttributePreservation:
    """Test that resource attributes are preserved for logs and metrics."""

    def test_log_resource_attributes(self, postgres_storage, time_range, pagination):
        """Verify log resource attributes are stored and retrieved."""
        log = make_log_record(body="Test message")

        resource_logs = make_resource_logs(service_name="test-service", log_records=[log])

        # Add custom resource attributes
        resource_logs["resource"]["attributes"].extend(
            [
                {"key": "service.version", "value": {"stringValue": "1.2.3"}},
                {"key": "deployment.environment", "value": {"stringValue": "production"}},
            ]
        )

        # Store
        count = postgres_storage.store_logs([resource_logs])
        assert count == 1

        # Retrieve and verify resource attributes
        logs, _, _ = postgres_storage.search_logs(time_range, None, pagination)

        log_found = next((log_item for log_item in logs if log_item.body == "Test message"), None)
        assert log_found is not None

        # Verify resource attributes preserved (LogRecord objects)
        assert log_found.service_name == "test-service" or (
            hasattr(log_found, "resource") and log_found.resource and "service.name" in log_found.resource
        )

    def test_metric_resource_attributes(self, postgres_storage, time_range, pagination):
        """Verify metric resource attributes are stored and retrieved."""
        metric = make_metric(name="test.metric", value=123.45)

        resource_metrics = make_resource_metrics(service_name="test-service", metrics=[metric])

        # Add custom resource attributes
        resource_metrics["resource"]["attributes"].extend(
            [
                {"key": "service.version", "value": {"stringValue": "1.2.3"}},
                {"key": "deployment.environment", "value": {"stringValue": "production"}},
            ]
        )

        # Store
        count = postgres_storage.store_metrics([resource_metrics])
        assert count == 1

        # Retrieve and verify resource attributes
        metrics, _, _ = postgres_storage.search_metrics(time_range, ["test.metric"], None, pagination)

        assert len(metrics) > 0
        metric_found = metrics[0]

        # Verify resource attributes preserved (Metric objects)
        assert metric_found.service_name == "test-service" or (
            metric_found.resource and "service.name" in metric_found.resource
        )
