"""Dependency injection for FastAPI routes."""

import os

from app.storage.interface import StorageBackend
from app.storage.postgres_orm_sync import PostgresStorage

# Global storage instance
_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """
    Get storage backend instance.

    Requires DATABASE_HOST environment variable to be set.

    Raises:
        RuntimeError: If DATABASE_HOST is not configured
    """
    global _storage

    if _storage is None:
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

        # Connect to storage
        _storage.connect()

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
