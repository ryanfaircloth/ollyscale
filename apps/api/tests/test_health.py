"""Tests for health endpoints.

Comprehensive health check tests including mocked database states.
"""

import concurrent.futures
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_storage_ready():
    """Mock storage backend that is ready."""
    storage = MagicMock()
    storage.is_ready = True
    storage.get_readiness_status.return_value = {
        "ready": True,
        "message": "Database ready",
        "schema_version": "abc123",
        "last_check": time.time(),
    }
    storage.get_connection_pool_stats.return_value = {
        "pool_size": 10,
        "checked_out": 2,
        "checked_in": 8,
        "overflow": 0,
        "overflow_in_use": 0,
    }
    storage.engine = MagicMock()
    return storage


@pytest.fixture
def mock_storage_not_ready():
    """Mock storage backend that is not ready."""
    storage = MagicMock()
    storage.is_ready = False
    storage.get_readiness_status.return_value = {
        "ready": False,
        "message": "Database initializing",
        "schema_version": None,
        "last_check": time.time(),
    }
    storage.engine = None
    return storage


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
    """Test main health endpoint returns 503 when storage not ready."""
    # Storage not initialized in test environment
    response = client.get("/health/")
    assert response.status_code == 503
    data = response.json()
    assert "status" in data
    assert data["status"] == "not_ready"


def test_health_ready():
    """Test main health endpoint returns 200 when storage ready."""
    with patch("app.dependencies._storage") as mock_storage:
        mock_storage.is_ready = True
        mock_storage.get_readiness_status.return_value = {
            "ready": True,
            "message": "Database ready",
            "schema_version": "abc123",
        }

        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "schema_version" in data


def test_health_with_trailing_slash():
    """Test health endpoint with trailing slash."""
    # Returns 503 when not ready
    response = client.get("/health/")
    assert response.status_code == 503


def test_health_without_trailing_slash():
    """Test health endpoint without trailing slash."""
    response = client.get("/health")
    # FastAPI redirects or returns 503
    assert response.status_code in (503, 307)


# --- LIVENESS ENDPOINT ---


def test_health_live():
    """Test liveness endpoint always returns 200."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert data["version"] == "2.0.0"


def test_health_live_always_succeeds():
    """Test liveness probe never fails (for K8s liveness)."""
    # Even if storage not ready, liveness should pass
    response = client.get("/health/live")
    assert response.status_code == 200


# --- READINESS ENDPOINT ---


def test_health_ready_endpoint_not_ready():
    """Test readiness endpoint returns 503 when not ready."""
    response = client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"


def test_health_ready_endpoint_ready():
    """Test readiness endpoint returns 200 when ready."""
    with patch("app.dependencies._storage") as mock_storage:
        mock_storage.is_ready = True
        mock_storage.get_readiness_status.return_value = {
            "ready": True,
            "message": "Database ready",
            "schema_version": "abc123",
        }

        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


# --- DATABASE HEALTH ENDPOINT ---


def test_health_db_not_connected():
    """Test database health when storage not initialized."""
    response = client.get("/health/db")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_initialized"
    assert data["connected"] is False


def test_health_db_connected():
    """Test database health when DB is connected and ready."""
    with patch("app.dependencies._storage") as mock_storage:
        mock_storage.is_ready = True
        mock_storage.engine = MagicMock()
        mock_storage.get_readiness_status.return_value = {
            "ready": True,
            "message": "Database ready",
            "schema_version": "abc123",
        }
        mock_storage.get_connection_pool_stats.return_value = {"pool_size": 10, "checked_out": 2, "checked_in": 8}

        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["connected"] is True


def test_health_db_connection_failed():
    """Test database health when connection check fails."""
    with patch("app.dependencies._storage") as mock_storage:
        mock_storage.is_ready = False
        mock_storage.get_readiness_status.return_value = {"ready": False, "message": "Connection failed"}

        response = client.get("/health/db")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"


def test_health_db_degraded():
    """Test database health when DB is ready (no degraded state currently)."""
    with patch("app.dependencies._storage") as mock_storage:
        mock_storage.is_ready = True
        mock_storage.engine = MagicMock()
        mock_storage.get_readiness_status.return_value = {"ready": True, "message": "Database ready"}
        mock_storage.get_connection_pool_stats.return_value = {"pool_size": 10, "checked_out": 2}

        response = client.get("/health/db")
        assert response.status_code == 200


# --- RESPONSE FORMAT VALIDATION ---


def test_health_response_format():
    """Test health endpoint response format when ready."""
    with patch("app.dependencies._storage") as mock_storage:
        mock_storage.is_ready = True
        mock_storage.get_readiness_status.return_value = {
            "ready": True,
            "message": "Database ready",
            "schema_version": "abc123",
        }

        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()

        # Validate required fields
        assert "status" in data
        assert "version" in data
        assert data["status"] == "ready"
        assert data["version"] == "2.0.0"


def test_health_db_response_format():
    """Test database health endpoint response format when ready."""
    with patch("app.dependencies._storage") as mock_storage:
        mock_storage.is_ready = True
        mock_storage.engine = MagicMock()
        mock_storage.get_readiness_status.return_value = {"ready": True, "message": "Database ready"}
        mock_storage.get_connection_pool_stats.return_value = {"pool_size": 10}

        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()

        # Validate required fields
        assert "connected" in data
        assert isinstance(data["connected"], bool)
        assert data["connected"] is True


# --- CACHING & PERFORMANCE ---


def test_health_endpoint_performance():
    """Test health/live endpoint responds quickly (no DB check)."""
    start = time.time()
    response = client.get("/health/live")
    elapsed = time.time() - start

    assert response.status_code == 200
    # Liveness check should be extremely fast (<100ms)
    assert elapsed < 0.1


def test_health_concurrent_requests():
    """Test health/live endpoint handles concurrent requests."""

    def check_health():
        return client.get("/health/live")

    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_health) for _ in range(10)]
        responses = [f.result() for f in futures]

    assert all(r.status_code == 200 for r in responses)


# --- CONTENT TYPE & HEADERS ---


def test_health_content_type():
    """Test health endpoint returns JSON content type."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_health_accept_header():
    """Test health endpoint respects Accept header."""
    response = client.get("/health/live", headers={"Accept": "application/json"})
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
    """Test /health/live endpoint suitable for Kubernetes liveness probe."""
    # Liveness should always succeed if app is running
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_health_db_as_readiness_probe():
    """Test /health/ready endpoint suitable for Kubernetes readiness probe."""
    # Readiness should reflect DB connectivity
    # When not ready, returns 503
    response = client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"

    # When ready, returns 200
    with patch("app.dependencies._storage") as mock_storage:
        mock_storage.is_ready = True
        mock_storage.get_readiness_status.return_value = {
            "ready": True,
            "message": "Database ready",
            "schema_version": "abc123",
        }

        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
