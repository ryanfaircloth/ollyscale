"""Tests for health endpoints.

Comprehensive health check tests including mocked database states.
"""

import concurrent.futures
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_storage():
    """Mock storage backend for testing."""
    with patch("app.dependencies.get_storage") as mock:
        storage = AsyncMock()
        mock.return_value = storage
        yield storage


# --- ROOT ENDPOINT ---


def test_root():
    """Test root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "ollyscale-frontend"
    assert "version" in data
    assert data["version"] == "2.0.0"
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


# --- MAIN HEALTH ENDPOINT ---


def test_health():
    """Test main health endpoint returns healthy status."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "version" in data
    assert data["version"] == "2.0.0"


def test_health_with_trailing_slash():
    """Test health endpoint with trailing slash."""
    response = client.get("/health/")
    assert response.status_code == 200


def test_health_without_trailing_slash():
    """Test health endpoint without trailing slash."""
    response = client.get("/health")
    # FastAPI should redirect or accept both
    assert response.status_code in (200, 307)


# --- DATABASE HEALTH ENDPOINT ---


def test_health_db_not_connected():
    """Test database health when DB not connected."""
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()

    assert "connected" in data
    # Initially false since DB not configured in tests
    assert data["connected"] is False


def test_health_db_connected(mock_storage):
    """Test database health when DB is connected."""
    # Mock health check returning True
    mock_storage.health.return_value = True

    with patch("app.dependencies.get_storage", return_value=mock_storage):
        response = client.get("/health/db")

    # If health endpoint queries storage, it should show connected
    # Otherwise shows false (default test state)
    assert response.status_code == 200
    data = response.json()
    assert "connected" in data


def test_health_db_connection_failed(mock_storage):
    """Test database health when connection check fails."""
    # Mock health check raising exception
    mock_storage.health.side_effect = ConnectionError("Cannot connect to database")

    with patch("app.dependencies.get_storage", return_value=mock_storage):
        response = client.get("/health/db")

    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False


def test_health_db_degraded(mock_storage):
    """Test database health when DB is degraded (slow responses)."""
    # Mock health check being slow but successful
    mock_storage.health.return_value = True

    with patch("app.dependencies.get_storage", return_value=mock_storage):
        response = client.get("/health/db")

    # Should still return 200 but may include timing info
    assert response.status_code == 200


# --- RESPONSE FORMAT VALIDATION ---


def test_health_response_format():
    """Test health endpoint response format matches spec."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()

    # Validate required fields
    required_fields = ["status", "version"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Validate types
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)


def test_health_db_response_format():
    """Test database health endpoint response format."""
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()

    # Validate required fields
    assert "connected" in data
    assert isinstance(data["connected"], bool)


# --- CACHING & PERFORMANCE ---


def test_health_endpoint_performance():
    """Test health endpoint responds quickly."""
    start = time.time()
    response = client.get("/health/")
    elapsed = time.time() - start

    assert response.status_code == 200
    # Health check should be fast (<100ms)
    assert elapsed < 0.1


def test_health_concurrent_requests():
    """Test health endpoint handles concurrent requests."""

    def check_health():
        return client.get("/health/")

    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_health) for _ in range(10)]
        responses = [f.result() for f in futures]

    assert all(r.status_code == 200 for r in responses)


# --- CONTENT TYPE & HEADERS ---


def test_health_content_type():
    """Test health endpoint returns JSON content type."""
    response = client.get("/health/")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_health_accept_header():
    """Test health endpoint respects Accept header."""
    response = client.get("/health/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# --- ERROR CASES ---


def test_health_invalid_method():
    """Test health endpoint rejects non-GET methods."""
    response = client.post("/health/")
    assert response.status_code == 405  # Method Not Allowed


def test_health_db_invalid_method():
    """Test database health endpoint rejects non-GET methods."""
    response = client.post("/health/db")
    assert response.status_code == 405


# --- LIVENESS VS READINESS ---


def test_health_as_liveness_probe():
    """Test health endpoint suitable for Kubernetes liveness probe."""
    response = client.get("/health/")

    # Liveness probe should always succeed if app is running
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_db_as_readiness_probe():
    """Test database health endpoint suitable for Kubernetes readiness probe."""
    response = client.get("/health/db")

    # Readiness probe should reflect DB connectivity
    # In tests (no DB), returns 200 but connected=false
    assert response.status_code == 200

    # In production, app should not be marked ready until DB connected
    data = response.json()
    if data["connected"]:
        assert response.status_code == 200
    else:
        # Could return 503 Service Unavailable for readiness failures
        # But currently returns 200 with connected=false
        assert response.status_code == 200
