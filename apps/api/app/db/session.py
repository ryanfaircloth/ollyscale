"""Database session management for async SQLAlchemy."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


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

        # Build connection URL from environment variables
        host = os.getenv("DATABASE_HOST", "localhost")
        port = os.getenv("DATABASE_PORT", "5432")
        user = os.getenv("DATABASE_USER", "postgres")
        password = os.getenv("DATABASE_PASSWORD")
        if not password:
            raise ValueError("DATABASE_PASSWORD environment variable is required")
        db_name = os.getenv("DATABASE_NAME", "ollyscale")

        # Use asyncpg driver for PostgreSQL
        url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"

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
