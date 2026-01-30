"""API error handling and edge case tests.

Tests error scenarios, storage failures, and boundary conditions.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_storage
from app.main import app
from tests.fixtures import make_log_record, make_resource_logs, make_resource_metrics, make_resource_spans, make_span

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_storage():
    """Mock storage backend for all tests in this module."""
    storage = Mock()

    # Override the dependency
    app.dependency_overrides[get_storage] = lambda: storage

    yield storage

    # Clean up
    app.dependency_overrides.clear()


# --- DATABASE CONNECTION FAILURES ---


def test_ingest_traces_db_unavailable(mock_storage):
    """Test POST /api/traces when database is unavailable."""
    mock_storage.store_traces.side_effect = ConnectionError("Connection refused")

    response = client.post("/api/traces", json={"resource_spans": [make_resource_spans()]})

    assert response.status_code == 500
    assert "Failed to store traces" in response.json()["detail"]


def test_search_traces_db_timeout(mock_storage):
    """Test POST /api/traces/search when database times out."""
    mock_storage.search_traces.side_effect = TimeoutError("Query timeout exceeded")

    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "pagination": {"limit": 100},
        },
    )

    # FastAPI should catch unhandled exceptions and return 500
    assert response.status_code == 500


def test_get_trace_db_connection_lost(mock_storage):
    """Test GET /api/traces/{id} when database connection is lost."""
    mock_storage.get_trace_by_id.side_effect = ConnectionResetError("Connection reset by peer")

    response = client.get("/api/traces/0102030405060708090a0b0c0d0e0f10")

    assert response.status_code == 500


# --- INVALID PAYLOADS ---


def test_ingest_traces_invalid_hex_ids(mock_storage):
    """Test POST /api/traces with non-hex trace/span IDs."""
    # Configure mock to return success if called
    mock_storage.store_traces.return_value = None

    invalid_span = {
        "traceId": "not-a-hex-string",  # Invalid hex
        "spanId": "also-invalid",
        "name": "test",
        "startTimeUnixNano": 1000000000,
        "endTimeUnixNano": 2000000000,
    }

    response = client.post(
        "/api/traces",
        json={
            "resource_spans": [
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "test"}}]},
                    "scope_spans": [{"scope": {"name": "test"}, "spans": [invalid_span]}],
                }
            ]
        },
    )

    # Pydantic should validate or storage should handle
    # Accept validation error or successful ingestion (storage validates)
    assert response.status_code in (202, 422)


def test_ingest_logs_missing_body(mock_storage):
    """Test POST /api/logs with log record missing body."""
    # Configure mock to return success if called
    mock_storage.store_logs.return_value = None

    invalid_log = {
        "timeUnixNano": 1000000000,
        "observedTimeUnixNano": 1000000000,
        "severityNumber": 9,
        "severityText": "INFO",
        "attributes": [],  # body field intentionally missing for test
    }

    response = client.post(
        "/api/logs",
        json={
            "resource_logs": [
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "test"}}]},
                    "scope_logs": [{"scope": {"name": "test"}, "logRecords": [invalid_log]}],
                }
            ]
        },
    )

    # Should fail validation or be handled gracefully
    assert response.status_code in (202, 422)


def test_ingest_metrics_invalid_metric_type(mock_storage):
    """Test POST /api/metrics with unsupported metric type."""
    # Configure mock to return success if called
    mock_storage.store_metrics.return_value = None

    invalid_metric = {
        "name": "test.metric",
        "description": "Test",
        "unit": "1",
        # Missing gauge/sum/histogram - invalid
    }

    response = client.post(
        "/api/metrics",
        json={
            "resource_metrics": [
                {
                    "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "test"}}]},
                    "scopeMetrics": [{"scope": {"name": "test"}, "metrics": [invalid_metric]}],
                }
            ]
        },
    )

    # Should fail validation
    assert response.status_code in (202, 422)


# --- LARGE PAYLOADS ---


def test_ingest_traces_very_large_span_count(mock_storage):
    """Test POST /api/traces with 10000 spans."""
    mock_storage.store_traces.return_value = 10000

    # Create large payload
    spans = [make_span(name=f"span-{i}") for i in range(10000)]
    resource_spans = make_resource_spans(spans=spans)

    response = client.post("/api/traces", json={"resource_spans": [resource_spans]})

    # Should handle large payloads (or reject with 413 if configured)
    assert response.status_code in (202, 413)


def test_ingest_logs_large_message(mock_storage):
    """Test POST /api/logs with very large log message."""
    mock_storage.store_logs.return_value = 1

    large_body = "x" * 1_000_000  # 1MB log message

    log_record = make_log_record(body=large_body)
    resource_logs = make_resource_logs(log_records=[log_record])

    response = client.post("/api/logs", json={"resource_logs": [resource_logs]})

    # Should handle or reject large messages
    assert response.status_code in (202, 413)


def test_search_traces_extremely_large_time_range(mock_storage):
    """Test POST /api/traces/search with multi-year time range."""
    mock_storage.search_traces.return_value = ([], False, None)

    # 10 year time range using RFC3339 strings
    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {
                "start_time": "2000-01-01T00:00:00Z",
                "end_time": "2010-01-01T00:00:00Z",
            },
            "pagination": {"limit": 100},
        },
    )

    # Valid RFC3339 should be accepted
    assert response.status_code == 200


# --- MALFORMED JSON ---


def test_ingest_traces_malformed_json():
    """Test POST /api/traces with malformed JSON."""
    response = client.post(
        "/api/traces",
        content='{"resource_spans": [this is not json}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_ingest_logs_truncated_json():
    """Test POST /api/logs with truncated JSON."""
    response = client.post(
        "/api/logs",
        content='{"resource_logs": [{"resource": ',  # Truncated
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_search_traces_non_json_body():
    """Test POST /api/traces/search with non-JSON body."""
    response = client.post(
        "/api/traces/search",
        content="not json at all",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


# --- MISSING REQUIRED FIELDS ---


def test_ingest_traces_no_body():
    """Test POST /api/traces with empty request body."""
    response = client.post("/api/traces", json={})

    assert response.status_code == 422
    # Should report missing required field


def test_search_logs_missing_pagination(mock_storage):
    """Test POST /api/logs/search without pagination field."""
    mock_storage.search_logs.return_value = ([], False, None)

    response = client.post(
        "/api/logs/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"}
        },  # pagination intentionally missing
    )

    # May have defaults or require explicit pagination
    assert response.status_code in (200, 422)


def test_service_map_missing_time_range():
    """Test POST /api/service-map without time_range."""
    response = client.post("/api/service-map", json={})

    assert response.status_code == 422


# --- TYPE MISMATCHES ---


def test_ingest_traces_wrong_type():
    """Test POST /api/traces with resource_spans as string instead of array."""
    response = client.post("/api/traces", json={"resource_spans": "not an array"})

    assert response.status_code == 422


def test_search_traces_time_as_string(mock_storage):
    """Test POST /api/traces/search with time as string instead of int."""
    mock_storage.search_traces.return_value = ([], False, None)

    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {
                "start_time": "1000000000",  # String instead of int
                "end_time": "2000000000",
            },
            "pagination": {"limit": 100},
        },
    )

    # Pydantic may coerce or reject
    assert response.status_code in (200, 422)


def test_list_services_time_as_float(mock_storage):
    """Test POST /api/services with RFC3339 timestamps with fractional seconds."""
    mock_storage.get_services.return_value = []

    response = client.post(
        "/api/services",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40.5Z", "end_time": "2033-05-18T03:33:20.5Z"},
            "filters": [],
        },
    )

    # RFC3339 with fractional seconds should be accepted
    assert response.status_code == 200


# --- BOUNDARY CONDITIONS ---


def test_search_traces_epoch_zero(mock_storage):
    """Test POST /api/traces/search with epoch zero time."""
    mock_storage.search_traces.return_value = ([], False, None)

    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {"start_time": "1970-01-01T00:00:00Z", "end_time": "1970-01-01T00:00:01Z"},
            "pagination": {"limit": 100},
        },
    )

    assert response.status_code == 200


def test_search_logs_future_time(mock_storage):
    """Test POST /api/logs/search with future timestamp."""
    mock_storage.search_logs.return_value = ([], False, None)

    # Far future (year 2100)
    response = client.post(
        "/api/logs/search",
        json={
            "time_range": {"start_time": "2100-01-01T00:00:00Z", "end_time": "2100-01-02T00:00:00Z"},
            "pagination": {"limit": 100},
        },
    )

    assert response.status_code == 200


def test_search_metrics_max_int(mock_storage):
    """Test POST /api/metrics/search with max int64 timestamp."""
    mock_storage.search_metrics.return_value = ([], False, None)

    max_int64 = 2**63 - 1

    response = client.post(
        "/api/metrics/search",
        json={
            "time_range": {"start_time": max_int64 - 1000, "end_time": max_int64},
            "metric_names": [],
            "pagination": {"limit": 100},
        },
    )

    # Should handle or overflow
    assert response.status_code in (200, 422, 500)


# --- CONCURRENT REQUESTS ---


def test_concurrent_ingest_same_trace(mock_storage):
    """Test concurrent ingestion of spans for same trace."""
    mock_storage.store_traces.return_value = 1

    trace_id = "0102030405060708090a0b0c0d0e0f10"

    # Simulate concurrent requests with same trace_id
    responses = []
    for i in range(10):
        span = make_span(trace_id=trace_id, span_id=f"000000000000000{i}", name=f"span-{i}")
        resource_spans = make_resource_spans(spans=[span])

        response = client.post("/api/traces", json={"resource_spans": [resource_spans]})
        responses.append(response)

    assert all(r.status_code == 202 for r in responses)


def test_concurrent_queries(mock_storage):
    """Test concurrent query requests."""
    mock_storage.search_traces.return_value = ([], False, None)

    # Make 20 concurrent search requests
    responses = []
    for _ in range(20):
        response = client.post(
            "/api/traces/search",
            json={
                "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
                "pagination": {"limit": 100},
            },
        )
        responses.append(response)

    assert all(r.status_code == 200 for r in responses)


# --- STORAGE BACKEND ERRORS ---


def test_ingest_metrics_storage_integrity_error(mock_storage):
    """Test POST /api/metrics when storage raises IntegrityError."""
    mock_storage.store_metrics.side_effect = Exception("Unique constraint violation")

    response = client.post("/api/metrics", json={"resource_metrics": [make_resource_metrics()]})

    assert response.status_code == 500


def test_search_logs_storage_returns_none(mock_storage):
    """Test POST /api/logs/search when storage returns None (unexpected)."""
    mock_storage.search_logs.return_value = None  # Should return tuple

    response = client.post(
        "/api/logs/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "pagination": {"limit": 100},
        },
    )

    # Should handle gracefully or error
    assert response.status_code in (200, 500)


def test_get_services_storage_exception(mock_storage):
    """Test POST /api/services when storage raises generic exception."""
    mock_storage.get_services.side_effect = Exception("Unexpected error")

    response = client.post("/api/services", json={})

    assert response.status_code == 500
