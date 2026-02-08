"""Dependency injection for FastAPI routes."""

from pathlib import Path

from app.storage.interface import StorageBackend
from app.storage.postgres_orm_sync import PostgresStorage

# Global storage instance
_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """
    Get storage backend instance.

    Reads database connection from /secrets/db/uri.

    Raises:
        RuntimeError: If secret file is not found
    """
    global _storage

    if _storage is None:
        # Read connection URI from CNPG secret
        db_secret_path = Path("/secrets/db")
        uri_file = db_secret_path / "uri"

        if not uri_file.exists():
            msg = f"Database secret not found at {uri_file}"
            raise RuntimeError(msg)

        uri = uri_file.read_text().strip()

        # Convert to postgresql+psycopg2://
        if uri.startswith("postgresql://"):
            connection_string = uri.replace("postgresql://", "postgresql+psycopg2://", 1)
        elif uri.startswith("postgresql+asyncpg://"):
            connection_string = uri.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        else:
            connection_string = uri

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

    This is used by the receiver module which manages its own connection
    lifecycle.

    Reads database connection from /secrets/db/uri.

    Raises:
        RuntimeError: If secret file is not found
    """
    # Read connection URI from CNPG secret
    db_secret_path = Path("/secrets/db")
    uri_file = db_secret_path / "uri"

    if not uri_file.exists():
        msg = f"Database secret not found at {uri_file}"
        raise RuntimeError(msg)

    uri = uri_file.read_text().strip()

    # Convert to postgresql+psycopg2://
    if uri.startswith("postgresql://"):
        connection_string = uri.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif uri.startswith("postgresql+asyncpg://"):
        connection_string = uri.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    else:
        connection_string = uri

    return PostgresStorage(connection_string)
