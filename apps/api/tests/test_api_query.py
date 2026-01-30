"""API integration tests for query endpoints.

Tests search endpoints with various filters, pagination, and time ranges.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_storage
from app.main import app

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


# --- TRACE QUERY TESTS ---


def test_search_traces_valid(mock_storage):
    """Test POST /api/traces/search with valid request."""
    # Mock search results
    mock_storage.search_traces.return_value = (
        [
            {
                "trace_id": "0102030405060708090a0b0c0d0e0f10",
                "root_span_name": "GET /api/users",
                "service_name": "frontend",
                "start_time": "2001-09-09T01:46:40Z",
                "duration_ms": 125.5,
                "span_count": 3,
            }
        ],
        False,  # has_more
        None,  # next_cursor
    )

    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "filters": [],
            "pagination": {"limit": 100},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["traces"]) == 1
    assert data["traces"][0]["trace_id"] == "0102030405060708090a0b0c0d0e0f10"
    assert data["pagination"]["has_more"] is False
    assert data["pagination"]["total_count"] == 1


def test_search_traces_with_filters(mock_storage):
    """Test POST /api/traces/search with service filter."""
    mock_storage.search_traces.return_value = ([], False, None)

    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "filters": [{"field": "service.name", "operator": "eq", "value": "backend"}],
            "pagination": {"limit": 50},
        },
    )

    assert response.status_code == 200
    assert response.json()["traces"] == []

    # Verify filters passed to storage
    call_args = mock_storage.search_traces.call_args
    assert len(call_args.kwargs["filters"]) == 1
    assert call_args.kwargs["filters"][0].field == "service.name"
    assert call_args.kwargs["filters"][0].value == "backend"


def test_search_traces_with_pagination(mock_storage):
    """Test POST /api/traces/search with pagination."""
    mock_storage.search_traces.return_value = (
        [{"trace_id": f"trace-{i}"} for i in range(50)],
        True,  # has_more
        "cursor-abc123",  # next_cursor
    )

    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "pagination": {"limit": 50, "cursor": None},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["traces"]) == 50
    assert data["pagination"]["has_more"] is True
    assert data["pagination"]["next_cursor"] == "cursor-abc123"


def test_search_traces_next_page(mock_storage):
    """Test POST /api/traces/search with cursor for next page."""
    mock_storage.search_traces.return_value = (
        [{"trace_id": f"trace-{i}"} for i in range(50, 75)],
        False,
        None,
    )

    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "pagination": {"limit": 50, "cursor": "cursor-abc123"},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["traces"]) == 25
    assert data["pagination"]["has_more"] is False


def test_get_trace_by_id_found(mock_storage):
    """Test GET /api/traces/{trace_id} when trace exists."""
    mock_storage.get_trace_by_id.return_value = {
        "trace_id": "0102030405060708090a0b0c0d0e0f10",
        "spans": [
            {"span_id": "01", "name": "root"},
            {"span_id": "02", "name": "child"},
        ],
    }

    response = client.get("/api/traces/0102030405060708090a0b0c0d0e0f10")

    assert response.status_code == 200
    data = response.json()

    assert data["trace_id"] == "0102030405060708090a0b0c0d0e0f10"
    assert len(data["spans"]) == 2


def test_get_trace_by_id_not_found(mock_storage):
    """Test GET /api/traces/{trace_id} when trace doesn't exist."""
    mock_storage.get_trace_by_id.return_value = None

    response = client.get("/api/traces/nonexistent-trace-id")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# --- LOG QUERY TESTS ---


def test_search_logs_valid(mock_storage):
    """Test POST /api/logs/search with valid request."""
    mock_storage.search_logs.return_value = (
        [
            {
                "timestamp": "2001-09-09T01:46:40Z",
                "observed_timestamp": None,
                "severity_number": 9,
                "severity_text": "INFO",
                "body": "Request received",
                "attributes": [],
                "trace_id": None,
                "span_id": None,
                "service_name": "test-service",
                "service_namespace": None,
                "resource": {},
            }
        ],
        False,
        None,
    )

    response = client.post(
        "/api/logs/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "filters": [],
            "pagination": {"limit": 100},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["logs"]) == 1
    assert data["logs"][0]["body"] == "Request received"


def test_search_logs_with_trace_correlation(mock_storage):
    """Test POST /api/logs/search filtered by trace_id."""
    mock_storage.search_logs.return_value = (
        [
            {
                "timestamp": "2001-09-09T01:46:40Z",
                "observed_timestamp": None,
                "severity_number": None,
                "severity_text": None,
                "body": "Log from trace",
                "attributes": [],
                "trace_id": "0102030405060708090a0b0c0d0e0f10",
                "span_id": "0102030405060708",
                "service_name": None,
                "service_namespace": None,
                "resource": {},
            }
        ],
        False,
        None,
    )

    response = client.post(
        "/api/logs/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "filters": [{"field": "trace_id", "operator": "eq", "value": "0102030405060708090a0b0c0d0e0f10"}],
            "pagination": {"limit": 100},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["logs"]) == 1
    assert data["logs"][0]["trace_id"] == "0102030405060708090a0b0c0d0e0f10"


def test_search_logs_with_severity_filter(mock_storage):
    """Test POST /api/logs/search filtered by severity."""
    mock_storage.search_logs.return_value = ([], False, None)

    response = client.post(
        "/api/logs/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "filters": [{"field": "severity", "operator": "eq", "value": "ERROR"}],
            "pagination": {"limit": 100},
        },
    )

    assert response.status_code == 200

    # Verify filter passed correctly
    call_args = mock_storage.search_logs.call_args
    assert len(call_args.kwargs["filters"]) == 1
    assert call_args.kwargs["filters"][0].field == "severity"
    assert call_args.kwargs["filters"][0].value == "ERROR"


# --- METRIC QUERY TESTS ---


def test_search_metrics_valid(mock_storage):
    """Test POST /api/metrics/search with valid request."""
    mock_storage.search_metrics.return_value = (
        [
            {
                "name": "http.requests.active",
                "metric_type": "gauge",
                "data_points": [{"time_unix_nano": 1000000000, "value": 42}],
            }
        ],
        False,
        None,
    )

    response = client.post(
        "/api/metrics/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "metric_names": ["http.requests.active"],
            "filters": [],
            "pagination": {"limit": 100},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["metrics"]) == 1
    assert data["metrics"][0]["name"] == "http.requests.active"
    assert data["metrics"][0]["metric_type"] == "gauge"
    assert data["metrics"][0]["data_points"][0]["value"] == 42


def test_search_metrics_multiple_names(mock_storage):
    """Test POST /api/metrics/search with multiple metric names."""
    mock_storage.search_metrics.return_value = (
        [
            {
                "name": "cpu.usage",
                "metric_type": "gauge",
                "data_points": [{"time_unix_nano": 1000000000, "value": 45.2}],
            },
            {
                "name": "memory.usage",
                "metric_type": "gauge",
                "data_points": [{"time_unix_nano": 1000000000, "value": 1024}],
            },
        ],
        False,
        None,
    )

    response = client.post(
        "/api/metrics/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "metric_names": ["cpu.usage", "memory.usage"],
            "pagination": {"limit": 100},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["metrics"]) == 2


def test_search_metrics_with_label_filter(mock_storage):
    """Test POST /api/metrics/search with label filter."""
    mock_storage.search_metrics.return_value = ([], False, None)

    response = client.post(
        "/api/metrics/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "metric_names": ["http.requests"],
            "filters": [{"field": "host", "operator": "eq", "value": "server1"}],
            "pagination": {"limit": 100},
        },
    )

    assert response.status_code == 200

    # Verify filters passed
    call_args = mock_storage.search_metrics.call_args
    assert len(call_args.kwargs["filters"]) == 1
    assert call_args.kwargs["filters"][0].field == "host"
    assert call_args.kwargs["filters"][0].value == "server1"


# --- SERVICE CATALOG TESTS ---


def test_list_services_no_time_range(mock_storage):
    """Test GET /api/services without time range."""
    mock_storage.get_services.return_value = [
        {
            "name": "frontend",
            "request_count": 12550,
            "error_count": 251,
            "error_rate": 0.02,
            "p50_latency_ms": 45.2,
            "p95_latency_ms": 120.8,
            "first_seen": 1000000000,
            "last_seen": 2000000000,
        },
        {
            "name": "backend",
            "request_count": 9830,
            "error_count": 98,
            "error_rate": 0.01,
            "p50_latency_ms": 32.1,
            "p95_latency_ms": 85.4,
            "first_seen": 1000000000,
            "last_seen": 2000000000,
        },
    ]

    response = client.post("/api/services", json={})

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 2
    assert len(data["services"]) == 2
    assert data["services"][0]["name"] == "frontend"


def test_list_services_with_time_range(mock_storage):
    """Test GET /api/services with time range query params."""
    mock_storage.get_services.return_value = [
        {
            "name": "frontend",
            "request_count": 10000,
            "error_count": 0,
            "error_rate": 0.0,
            "p50_latency_ms": 50.0,
            "p95_latency_ms": 100.0,
            "first_seen": 1000000000,
            "last_seen": 2000000000,
        }
    ]

    response = client.post(
        "/api/services",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "filters": [],
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 1

    # Verify time_range passed to storage
    call_args = mock_storage.get_services.call_args
    assert call_args.kwargs["time_range"] is not None
    assert call_args.kwargs["time_range"].start_time == "2001-09-09T01:46:40Z"


def test_list_services_empty(mock_storage):
    """Test POST /api/services when no services exist."""
    mock_storage.get_services.return_value = []

    response = client.post("/api/services", json={})

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 0
    assert data["services"] == []


# --- SERVICE MAP TESTS ---


def test_get_service_map_valid(mock_storage):
    """Test POST /api/service-map with valid time range."""
    mock_storage.get_service_map.return_value = (
        [
            {"id": "frontend", "name": "frontend", "type": "service", "attributes": {}},
            {"id": "backend", "name": "backend", "type": "service", "attributes": {}},
        ],
        [{"source": "frontend", "target": "backend", "call_count": 1250}],
    )

    response = client.post(
        "/api/service-map",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "filters": [],
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["edges"][0]["call_count"] == 1250
    assert data["time_range"]["start_time"] == "2001-09-09T01:46:40Z"


def test_get_service_map_complex_topology(mock_storage):
    """Test POST /api/service-map with complex service topology."""
    mock_storage.get_service_map.return_value = (
        [
            {"id": "frontend", "name": "frontend", "type": "service"},
            {"id": "backend", "name": "backend", "type": "service"},
            {"id": "database", "name": "database", "type": "database"},
            {"id": "cache", "name": "cache", "type": "database"},
        ],
        [
            {"source": "frontend", "target": "backend", "call_count": 500},
            {"source": "backend", "target": "database", "call_count": 450},
            {"source": "backend", "target": "cache", "call_count": 300},
        ],
    )

    response = client.post(
        "/api/service-map",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "filters": [],
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["nodes"]) == 4
    assert len(data["edges"]) == 3

    # Verify database nodes identified
    db_nodes = [n for n in data["nodes"] if n["type"] == "database"]
    assert len(db_nodes) == 2


# --- EDGE CASES & ERROR HANDLING ---


def test_search_traces_invalid_time_range(mock_storage):
    """Test POST /api/traces/search with invalid time range."""
    mock_storage.search_traces.return_value = ([], False, None)

    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {"start_time": "2033-05-18T03:33:20Z", "end_time": "2001-09-09T01:46:40Z"},  # Reversed
            "pagination": {"limit": 100},
        },
    )

    # Pydantic should validate or storage should handle
    # Accept either 422 (validation error) or 200 (storage handles gracefully)
    assert response.status_code in (200, 422)


def test_search_logs_missing_time_range():
    """Test POST /api/logs/search without time_range."""
    response = client.post(
        "/api/logs/search",
        json={"pagination": {"limit": 100}},
    )

    # Should fail validation for missing required field
    assert response.status_code == 422


def test_search_metrics_empty_metric_names(mock_storage):
    """Test POST /api/metrics/search with empty metric_names array."""
    mock_storage.search_metrics.return_value = ([], False, None)

    response = client.post(
        "/api/metrics/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "metric_names": [],  # Empty array
            "pagination": {"limit": 100},
        },
    )

    # Should be valid - means "return all metrics"
    assert response.status_code == 200


def test_search_traces_zero_limit(mock_storage):
    """Test POST /api/traces/search with limit=0."""
    mock_storage.search_traces.return_value = ([], False, None)

    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "pagination": {"limit": 0},  # Edge case
        },
    )

    # Should either return empty results or validation error
    assert response.status_code in (200, 422)


def test_search_traces_negative_limit():
    """Test POST /api/traces/search with negative limit."""
    response = client.post(
        "/api/traces/search",
        json={
            "time_range": {"start_time": "2001-09-09T01:46:40Z", "end_time": "2033-05-18T03:33:20Z"},
            "pagination": {"limit": -10},
        },
    )

    # Should fail validation
    assert response.status_code == 422
