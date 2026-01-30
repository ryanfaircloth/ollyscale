import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get database URL from environment
database_url = os.getenv(
    "DATABASE_URL",
    (
        f"postgresql+asyncpg://{os.getenv('DATABASE_USER', 'ollyscale')}:"
        f"{os.getenv('DATABASE_PASSWORD', '')}@"
        f"{os.getenv('DATABASE_HOST', 'localhost')}:"
        f"{os.getenv('DATABASE_PORT', '5432')}/"
        f"{os.getenv('DATABASE_NAME', 'ollyscale')}"
    ),
)
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# TODO: Import application models here for autogenerate support
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with given connection."""
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)

    with context.begin_transaction():
        context.run_migrations()


def run_sync_migrations() -> None:
    """Run migrations in sync mode (for testing with psycopg2)."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


async def run_async_migrations() -> None:
    """Run async migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async support."""
    url = config.get_main_option("sqlalchemy.url")
    if url and ("psycopg2" in url or "sqlite" in url):
        # Sync mode for testing
        run_sync_migrations()
    else:
        # Async mode for production
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
