"""Dependency injection for FastAPI routes."""

import os

from fastapi import HTTPException

from app.storage.interface import StorageBackend
from app.storage.postgres_orm_sync import PostgresStorage

# Global storage instance
_storage: StorageBackend | None = None


def initialize_storage() -> None:
    """
    Initialize storage backend (called once at startup).

    Creates storage instance and starts background readiness checker.
    Does NOT check if ready - that happens in get_storage().
    """
    global _storage

    if _storage is not None:
        return  # Already initialized

    # Require DATABASE_HOST to be set
    if not os.getenv("DATABASE_HOST"):
        msg = "DATABASE_HOST environment variable must be set. PostgresStorage is required."
        raise RuntimeError(msg)

    # Build connection string from environment variables
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = os.getenv("DATABASE_PORT", "5432")
    db_name = os.getenv("DATABASE_NAME", "ollyscale")
    db_user = os.getenv("DATABASE_USER", "postgres")
    db_password = os.getenv("DATABASE_PASSWORD", "postgres")
    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    _storage = PostgresStorage(connection_string)

    # Start background readiness checker (non-blocking)
    # This will check DB readiness every 1s and call connect() when ready
    _storage.start_readiness_checker()


def get_storage() -> StorageBackend:
    """
    Get storage backend instance.

    Requires storage to be initialized and ready.

    Raises:
        RuntimeError: If storage not initialized
        HTTPException(503): If database is not ready yet
    """
    if _storage is None:
        raise RuntimeError("Storage not initialized - call initialize_storage() first")

    # Check if database is ready before allowing operations
    if not _storage.is_ready:
        status = _storage.get_readiness_status()
        raise HTTPException(status_code=503, detail=f"Database initializing: {status['message']}")

    return _storage


def close_storage():
    """Close storage backend connection."""
    global _storage
    if _storage is not None:
        _storage.close()
        _storage = None


def get_storage_sync() -> StorageBackend:
    """
    Get storage backend instance synchronously (for gRPC receiver).

    This is used by the receiver module which manages its own connection lifecycle.

    Requires DATABASE_HOST environment variable to be set.

    Raises:
        RuntimeError: If DATABASE_HOST is not configured
    """
    # Require DATABASE_HOST to be set
    if not os.getenv("DATABASE_HOST"):
        msg = "DATABASE_HOST environment variable must be set. PostgresStorage is required."
        raise RuntimeError(msg)

    # Build connection string from environment variables
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = os.getenv("DATABASE_PORT", "5432")
    db_name = os.getenv("DATABASE_NAME", "ollyscale")
    db_user = os.getenv("DATABASE_USER", "postgres")
    db_password = os.getenv("DATABASE_PASSWORD", "postgres")
    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    return PostgresStorage(connection_string)
