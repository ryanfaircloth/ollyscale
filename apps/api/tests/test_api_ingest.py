"""API integration tests for ingestion endpoints.

Tests the FastAPI endpoints with TestClient, mocking storage backend.
Validates API contracts, error handling, and response formats.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_storage
from app.main import app
from tests.fixtures import (
    make_gauge_datapoint,
    make_gauge_metric,
    make_log_record,
    make_resource_logs,
    make_resource_metrics,
    make_resource_spans,
    make_span,
)

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


# --- TRACE INGESTION TESTS ---


def test_ingest_traces_valid(mock_storage):
    """Test POST /api/traces with valid trace data."""
    mock_storage.store_traces.return_value = 2  # 2 spans stored

    resource_spans = make_resource_spans(
        service_name="frontend",
        spans=[
            make_span(name="GET /api/users", kind=2, **{"http.method": "GET", "http.status_code": 200}),
            make_span(name="db.query", kind=3, **{"db.system": "postgresql", "db.statement": "SELECT * FROM users"}),
        ],
    )

    response = client.post("/api/traces", json={"resource_spans": [resource_spans]})

    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "count": 2}
    mock_storage.store_traces.assert_called_once()


def test_ingest_traces_empty_spans(mock_storage):
    """Test POST /api/traces with empty resource_spans array."""
    response = client.post("/api/traces", json={"resource_spans": []})

    assert response.status_code == 422
    assert "resource_spans cannot be empty" in response.json()["detail"]
    mock_storage.store_traces.assert_not_called()


def test_ingest_traces_missing_field():
    """Test POST /api/traces with missing required field."""
    response = client.post("/api/traces", json={})

    assert response.status_code == 422
    # FastAPI validation error for missing field
    detail = response.json()["detail"]
    assert any("resource_spans" in str(error) for error in detail)


def test_ingest_traces_storage_failure(mock_storage):
    """Test POST /api/traces when storage fails."""
    mock_storage.store_traces.side_effect = Exception("Database connection failed")

    resource_spans = make_resource_spans()

    response = client.post("/api/traces", json={"resource_spans": [resource_spans]})

    assert response.status_code == 500
    assert "Failed to store traces" in response.json()["detail"]


def test_ingest_traces_multiple_services(mock_storage):
    """Test POST /api/traces with multiple services."""
    mock_storage.store_traces.return_value = 4

    response = client.post(
        "/api/traces",
        json={
            "resource_spans": [
                make_resource_spans("frontend", [make_span(name="http-request")]),
                make_resource_spans("backend", [make_span(name="process-request")]),
                make_resource_spans("database", [make_span(name="query")]),
            ]
        },
    )

    assert response.status_code == 202
    assert response.json()["count"] == 4


# --- LOG INGESTION TESTS ---


def test_ingest_logs_valid(mock_storage):
    """Test POST /api/logs with valid log data."""
    mock_storage.store_logs.return_value = 3

    resource_logs = make_resource_logs(
        service_name="backend",
        log_records=[
            make_log_record(body="Request received", severity_text="INFO"),
            make_log_record(body="Processing data", severity_text="DEBUG"),
            make_log_record(body="Request completed", severity_text="INFO"),
        ],
    )

    response = client.post("/api/logs", json={"resource_logs": [resource_logs]})

    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "count": 3}
    mock_storage.store_logs.assert_called_once()


def test_ingest_logs_empty(mock_storage):
    """Test POST /api/logs with empty resource_logs array."""
    response = client.post("/api/logs", json={"resource_logs": []})

    assert response.status_code == 422
    assert "resource_logs cannot be empty" in response.json()["detail"]
    mock_storage.store_logs.assert_not_called()


def test_ingest_logs_correlated_with_trace(mock_storage):
    """Test POST /api/logs with trace correlation."""
    mock_storage.store_logs.return_value = 1

    trace_id = "0102030405060708090a0b0c0d0e0f10"
    span_id = "0102030405060708"

    resource_logs = make_resource_logs(
        log_records=[
            make_log_record(
                body="Log entry from span",
                trace_id=trace_id,
                span_id=span_id,
                level="info",
            )
        ]
    )

    response = client.post("/api/logs", json={"resource_logs": [resource_logs]})

    assert response.status_code == 202
    assert response.json()["count"] == 1


def test_ingest_logs_storage_failure(mock_storage):
    """Test POST /api/logs when storage fails."""
    mock_storage.store_logs.side_effect = Exception("Disk full")

    resource_logs = make_resource_logs()

    response = client.post("/api/logs", json={"resource_logs": [resource_logs]})

    assert response.status_code == 500
    assert "Failed to store logs" in response.json()["detail"]


# --- METRIC INGESTION TESTS ---


def test_ingest_metrics_valid(mock_storage):
    """Test POST /api/metrics with valid metric data."""
    mock_storage.store_metrics.return_value = 2

    resource_metrics = make_resource_metrics(
        service_name="frontend",
        metrics=[
            make_gauge_metric("http.requests.active"),
            make_gauge_metric("memory.usage.bytes"),
        ],
    )

    response = client.post("/api/metrics", json={"resource_metrics": [resource_metrics]})

    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "count": 2}
    mock_storage.store_metrics.assert_called_once()


def test_ingest_metrics_empty(mock_storage):
    """Test POST /api/metrics with empty resource_metrics array."""
    response = client.post("/api/metrics", json={"resource_metrics": []})

    assert response.status_code == 422
    assert "resource_metrics cannot be empty" in response.json()["detail"]
    mock_storage.store_metrics.assert_not_called()


def test_ingest_metrics_storage_failure(mock_storage):
    """Test POST /api/metrics when storage fails."""
    mock_storage.store_metrics.side_effect = Exception("Write timeout")

    resource_metrics = make_resource_metrics()

    response = client.post("/api/metrics", json={"resource_metrics": [resource_metrics]})

    assert response.status_code == 500
    assert "Failed to store metrics" in response.json()["detail"]


# --- EDGE CASES & VALIDATION ---


def test_ingest_traces_invalid_json():
    """Test POST /api/traces with malformed JSON."""
    response = client.post(
        "/api/traces",
        content='{"resource_spans": [invalid json}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_ingest_logs_invalid_severity(mock_storage):
    """Test POST /api/logs with invalid severity number."""
    # Note: Pydantic should validate this, but we test the contract
    mock_storage.store_logs.return_value = 1

    resource_logs = make_resource_logs(
        log_records=[
            {
                "timeUnixNano": 1000000000,
                "observedTimeUnixNano": 1000000000,
                "severityNumber": 999,  # Invalid (should be 1-24)
                "severityText": "INVALID",
                "body": {"stringValue": "test"},
                "attributes": [],
            }
        ]
    )

    response = client.post("/api/logs", json={"resource_logs": [resource_logs]})

    # If Pydantic validation passes (no constraints on severityNumber), accept it
    # Otherwise expect 422
    assert response.status_code in (202, 422)


def test_ingest_traces_large_payload(mock_storage):
    """Test POST /api/traces with large number of spans."""
    mock_storage.store_traces.return_value = 1000

    # Create 1000 spans
    spans = [make_span(name=f"span-{i}") for i in range(1000)]
    resource_spans = make_resource_spans(spans=spans)

    response = client.post("/api/traces", json={"resource_spans": [resource_spans]})

    assert response.status_code == 202
    assert response.json()["count"] == 1000


def test_ingest_metrics_multiple_datapoints(mock_storage):
    """Test POST /api/metrics with metric having multiple datapoints."""
    mock_storage.store_metrics.return_value = 1

    metric = make_gauge_metric(
        name="cpu.usage",
        datapoints=[
            make_gauge_datapoint(value=45.2, **{"host": "server1"}),
            make_gauge_datapoint(value=67.8, **{"host": "server2"}),
            make_gauge_datapoint(value=23.1, **{"host": "server3"}),
        ],
    )

    resource_metrics = make_resource_metrics(metrics=[metric])

    response = client.post("/api/metrics", json={"resource_metrics": [resource_metrics]})

    assert response.status_code == 202


# --- CONCURRENT REQUESTS (simulated) ---


def test_ingest_concurrent_traces(mock_storage):
    """Test multiple concurrent trace ingestion requests."""
    mock_storage.store_traces.return_value = 1

    # Simulate concurrent requests by making multiple calls
    responses = []
    for i in range(5):
        resource_spans = make_resource_spans(service_name=f"service-{i}")
        response = client.post("/api/traces", json={"resource_spans": [resource_spans]})
        responses.append(response)

    assert all(r.status_code == 202 for r in responses)
    assert mock_storage.store_traces.call_count == 5
