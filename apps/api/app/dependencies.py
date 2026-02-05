"""Dependency injection for FastAPI routes."""

import os
from collections.abc import Generator

from sqlalchemy.orm import Session

from app.storage.interface import StorageBackend
from app.storage.otlp_storage import OtlpStorage
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


def get_db_session() -> Generator[Session]:
    """
    Get database session for v2 routers.

    Yields a SQLAlchemy session from the global storage engine.
    Session is automatically committed on success or rolled back on error.

    Yields:
        Session: Active database session

    Raises:
        RuntimeError: If storage is not initialized
    """
    storage = get_storage()
    if not hasattr(storage, "engine") or storage.engine is None:
        msg = "Storage engine not initialized. Call storage.connect() first."
        raise RuntimeError(msg)

    with Session(storage.engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def get_storage_sync() -> OtlpStorage:
    """
    Get OTLP storage backend instance synchronously (for gRPC receiver).

    This is used by the receiver module which manages its own connection lifecycle.

    Requires DATABASE_HOST environment variable to be set.

    Raises:
        RuntimeError: If DATABASE_HOST is not configured
    """
    # Require DATABASE_HOST to be set
    if not os.getenv("DATABASE_HOST"):
        msg = "DATABASE_HOST environment variable must be set. OtlpStorage is required."
        raise RuntimeError(msg)

    # Build connection string from environment variables
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = os.getenv("DATABASE_PORT", "5432")
    db_name = os.getenv("DATABASE_NAME", "ollyscale")
    db_user = os.getenv("DATABASE_USER", "postgres")
    db_password = os.getenv("DATABASE_PASSWORD", "postgres")
    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Path to attribute promotion config (ConfigMap mount or default)
    config_path = os.getenv("ATTRIBUTE_PROMOTION_CONFIG", "/config/attribute-promotion.yaml")

    return OtlpStorage(connection_string, config_path)
