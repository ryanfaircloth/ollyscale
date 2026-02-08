"""Pytest configuration for integration tests with real PostgreSQL database.

This module provides fixtures for connecting to test PostgreSQL.
Uses testcontainers for local testing or Kubernetes cluster for CI.

NOTE: Tests now use SYNC storage (not async) for simpler I/O-bound operations.
"""

import base64
import os
import subprocess
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer

from app.models.api import Pagination, TimeRange
from app.storage.postgres_orm_sync import PostgresStorage
from tests.fixtures import make_log_record


@pytest.fixture(scope="session", autouse=True)
def mock_db_secret(postgres_connection_string):
    """Mock /secrets/db/uri file reading for all tests.

    This allows the code to read from /secrets/db/uri without actually
    creating files on the filesystem.
    """

    def mock_exists(path):
        if str(path) == "/secrets/db/uri":
            return True
        # For other paths, use real os.path.exists
        return os.path.exists.__wrapped__(path) if hasattr(os.path.exists, "__wrapped__") else Path(path).exists()

    def mock_file_open(path, *args, **kwargs):
        if str(path) == "/secrets/db/uri":
            return mock_open(read_data=postgres_connection_string)()
        # For other paths, use real open
        return (
            open.__wrapped__(path, *args, **kwargs)
            if hasattr(open, "__wrapped__")
            else Path(path).open(*args, **kwargs)
        )

    with patch("os.path.exists", side_effect=mock_exists), patch("builtins.open", side_effect=mock_file_open):
        yield


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for local testing.

    Uses testcontainers with podman backend.
    Set PYTEST_SKIP_TESTCONTAINERS=1 to use K8s cluster instead.
    """
    if os.getenv("PYTEST_SKIP_TESTCONTAINERS") == "1":
        yield None
        return

    # Configure testcontainers to use podman (macOS)
    # Disable Ryuk on macOS/podman - it doesn't work with podman socket mounting
    os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"

    # Try to get podman socket from machine inspect (works on macOS with Apple HyperVisor)
    try:
        result = subprocess.run(
            ["podman", "machine", "inspect", "--format", "{{.ConnectionInfo.PodmanSocket.Path}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        socket_path = Path(result.stdout.strip())
        if socket_path.exists():
            os.environ["DOCKER_HOST"] = f"unix://{socket_path}"
        else:
            raise FileNotFoundError(f"Podman socket not found at {socket_path}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to trying common socket locations
        socket_paths = [
            Path(f"/run/user/{os.getuid()}/podman/podman.sock"),  # Runtime socket
            Path.home() / ".local/share/containers/podman/machine/qemu/podman.sock",  # QEMU machine
            Path("/var/run/docker.sock"),  # Docker fallback
        ]
        found = False
        for sock_path in socket_paths:
            if sock_path.exists():
                os.environ["DOCKER_HOST"] = f"unix://{sock_path}"
                found = True
                break

        if not found:
            pytest.skip("No podman/docker socket found. Install podman or set PYTEST_SKIP_TESTCONTAINERS=1")

    container = PostgresContainer(
        image="postgres:16-alpine",
        username="ollyscale",
        password="test_password",
        dbname="ollyscale",
    )

    with container:
        yield container


@pytest.fixture(scope="session")
def postgres_connection_string(postgres_container):
    """Get PostgreSQL connection string from testcontainer or K8s cluster.

    Priority:
    1. testcontainer (local development)
    2. POSTGRES_PASSWORD env var (CI/CD)
    3. Kubernetes secret (cluster testing)
    """
    # Use testcontainer if available
    if postgres_container:
        return postgres_container.get_connection_url()

    # Fall back to K8s cluster connection
    # Use external gateway endpoint (kafka-listener port 9094)
    host = os.getenv("POSTGRES_HOST", "ollyscale-db.ollyscale.test")
    port = os.getenv("POSTGRES_PORT", "9094")
    user = os.getenv("POSTGRES_USER", "ollyscale")
    database = os.getenv("POSTGRES_DB", "ollyscale")

    # Get password from environment or Kubernetes secret
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        try:
            result = subprocess.run(
                ["kubectl", "get", "secret", "ollyscale-db-app", "-n", "ollyscale", "-o", "jsonpath={.data.password}"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            password = base64.b64decode(result.stdout).decode("utf-8")
        except Exception as e:
            pytest.skip(f"Cluster not available and POSTGRES_PASSWORD not set: {e}")

    # SSL mode for TLS connection through gateway
    sslmode = os.getenv("POSTGRES_SSLMODE", "require")

    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}"


@pytest.fixture
def postgres_engine(postgres_connection_string):
    """Create sync SQLAlchemy engine for tests.

    For testcontainers, also runs alembic migrations to create schema.
    """
    engine = create_engine(
        postgres_connection_string,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    # Create schema if using fresh testcontainer (no existing tables)
    inspector = inspect(engine)
    if not inspector.get_table_names():
        # Fresh database - run alembic migrations
        # Pass database URL via -x flag to avoid needing secret file
        result = subprocess.run(
            ["alembic", "-x", f"dburl={postgres_connection_string}", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            check=False,
        )
        if result.returncode != 0:
            pytest.fail(f"Alembic migration failed: {result.stderr}")

    yield engine

    engine.dispose()


@pytest.fixture
def postgres_session(postgres_engine):
    """Create sync database session for tests."""
    with Session(postgres_engine) as session:
        yield session


@pytest.fixture
def postgres_storage(postgres_connection_string, postgres_engine):  # noqa: ARG001
    """Create PostgresStorage instance connected to test database.

    Depends on postgres_engine to ensure migrations run before storage is used.
    postgres_engine is used implicitly to trigger migration fixture.
    """
    storage = PostgresStorage(postgres_connection_string)
    storage.connect()

    yield storage

    storage.close()


@pytest.fixture
def clean_database(postgres_session):
    """Clean test data from database before/after tests.

    With star schema pattern, dimension upserts commit immediately,
    so we must truncate dimensions AND facts for test isolation.
    CASCADE handles foreign key constraints.
    """
    # Clean before test - truncate facts first, then dimensions
    postgres_session.execute(
        text(
            "TRUNCATE TABLE spans_fact, logs_fact, metrics_fact, "
            "namespace_dim, service_dim, operation_dim, resource_dim "
            "CASCADE"
        )
    )
    postgres_session.commit()

    yield

    # Clean after test
    postgres_session.execute(
        text(
            "TRUNCATE TABLE spans_fact, logs_fact, metrics_fact, "
            "namespace_dim, service_dim, operation_dim, resource_dim "
            "CASCADE"
        )
    )
    postgres_session.commit()


@pytest.fixture
def time_range():
    """Standard time range for tests (RFC3339 format)."""
    return TimeRange(
        start_time="2001-09-09T01:46:40Z",  # 1000000000 as RFC3339
        end_time="2033-05-18T03:33:20Z",  # 2000000000 as RFC3339
    )


@pytest.fixture
def pagination():
    """Standard pagination for tests."""
    return Pagination(offset=0, limit=100)


@pytest.fixture
def make_log():
    """Factory fixture for creating OTLP log records."""
    return make_log_record
