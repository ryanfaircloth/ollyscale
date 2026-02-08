"""Database session management for async SQLAlchemy."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Database connection manager."""

    def __init__(self):
        """Initialize database connection manager."""
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Create database engine and session factory."""
        if self.engine is not None:
            return

        # Read connection URI from CNPG secret
        db_secret_path = Path("/secrets/db")
        uri_file = db_secret_path / "uri"

        if not uri_file.exists():
            msg = f"Database secret not found at {uri_file}"
            raise ValueError(msg)

        uri = uri_file.read_text().strip()

        # Convert postgresql:// to postgresql+asyncpg://
        if uri.startswith("postgresql://"):
            url = uri.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif uri.startswith("postgresql+psycopg2://"):
            url = uri.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        else:
            url = uri

        # Create async engine with connection pooling
        self.engine = create_async_engine(
            url,
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
        )

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """
        Get database session context manager.

        Usage:
            async with db.session() as session:
                result = await session.execute(query)
        """
        if self.session_factory is None:
            await self.connect()

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Global database instance
db = Database()
