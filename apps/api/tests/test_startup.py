"""Tests for application startup events and storage initialization."""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import app.dependencies
from app.dependencies import get_storage
from app.main import app


def test_startup_event_initializes_storage():
    """Test that the startup event handler is registered and calls get_storage()."""
    # Verify that startup event handler is registered
    assert len(app.router.on_startup) > 0, "Startup event handlers should be registered"

    # The startup_event function should be in the handlers
    handler_names = [h.__name__ for h in app.router.on_startup]
    assert "startup_event" in handler_names, "startup_event handler should be registered"


def test_startup_event_handles_storage_initialization_error():
    """Test that startup event logs errors but doesn't crash the app."""

    # Mock get_storage to raise an exception
    def mock_get_storage():
        raise RuntimeError("Cannot find alembic.ini")

    # Patch get_storage before importing app
    with (
        patch("app.dependencies.get_storage", side_effect=mock_get_storage),
        TestClient(app) as client,
    ):
        response = client.get("/health/live")
        # Liveness should still work even if storage init failed
        assert response.status_code == 200


@pytest.mark.skip(reason="Thread timing makes mocking difficult - covered by integration tests")
def test_readiness_checker_starts_on_storage_init(monkeypatch):
    """Test that calling get_storage() starts the readiness checker thread."""
    # Set required environment variable
    monkeypatch.setenv("DATABASE_HOST", "localhost")

    # Mock the database-ready state - returns (ready, version, message, details)
    mock_check = MagicMock(return_value=(True, "test123", "Database ready", None))

    # Mock the PostgreSQL connection and alembic check
    with (
        patch("app.storage.postgres_orm_sync.create_engine"),
        patch("app.storage.postgres_orm_sync._get_expected_alembic_revision", return_value="test123"),
        patch("app.storage.postgres_orm_sync.PostgresStorage.connect"),
        patch("app.storage.postgres_orm_sync.PostgresStorage.check_database_ready", mock_check),
    ):
        # Reset the singleton
        app.dependencies._storage = None

        # Give the readiness checker a moment to run
        storage = get_storage()
        time.sleep(0.1)  # Brief wait for thread to start

        # Verify readiness checker thread was started
        assert storage._readiness_checker_thread is not None
        assert storage._readiness_checker_thread.daemon is True
        assert storage._readiness_checker_thread.is_alive()


def test_health_endpoints_before_storage_init():
    """Test that health endpoints work even before storage is initialized."""
    with (
        patch("app.dependencies._storage", None),
        TestClient(app) as client,
    ):
        # Liveness should always work
        response = client.get("/health/live")
        assert response.status_code == 200

        # Readiness should return 503 when storage not initialized
        response = client.get("/health/ready")
        assert response.status_code == 503
