"""Tests for demo applications."""

import sys
from pathlib import Path

from flask import Flask

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

import backend
import frontend


def test_demo_imports():
    """Test that demo modules can be imported."""
    # Check that Flask apps are defined
    assert hasattr(backend, "app")
    assert hasattr(frontend, "app")

    # Check that apps are Flask instances
    assert isinstance(backend.app, Flask)
    assert isinstance(frontend.app, Flask)


def test_backend_health_endpoint():
    """Test backend health endpoint."""
    with backend.app.test_client() as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"


def test_frontend_health_endpoint():
    """Test frontend root endpoint."""
    with frontend.app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
