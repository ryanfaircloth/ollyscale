# ollyScale v2 Frontend

Postgres-backed observability platform with OTEL-aligned APIs.

## Overview

This is the v2 frontend application for ollyScale, providing:

- OTLP-compatible ingestion endpoints for traces, logs, and metrics
- Query APIs with time-based filtering, pagination, and cursor support
- Service catalog with RED metrics
- Service dependency map generation
- PostgreSQL storage with Alembic migrations

## Architecture

See [docs/ollyscale-v2-postgres.md](../../docs/ollyscale-v2-postgres.md) for full architecture documentation.

## Development

### Prerequisites

- Python 3.11+
- uv (modern Python package manager)
- PostgreSQL 15+ (for local development)

### Setup

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Start development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running with Database

```bash
# Set database URL
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/ollyscale"

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health

- `GET /health` - Overall health status
- `GET /health/db` - Database health and migration status

### Ingest (OTLP)

- `POST /api/traces` - Ingest traces
- `POST /api/logs` - Ingest logs
- `POST /api/metrics` - Ingest metrics

### Query

- `POST /api/traces/search` - Search traces
- `GET /api/traces/{trace_id}` - Get trace by ID
- `POST /api/logs/search` - Search logs
- `POST /api/metrics/search` - Search metrics
- `GET /api/services` - List services with RED metrics
- `POST /api/service-map` - Get service dependency map

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_models.py -v
```

## Code Quality

```bash
# Lint and format
uv run ruff check .
uv run ruff format .

# Fix auto-fixable issues
uv run ruff check --fix .
```

## Database Migrations

```bash
# Create new migration
uv run alembic revision -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Show current migration
uv run alembic current

# Show migration history
uv run alembic history --verbose
```

## Deployment

See Helm chart documentation in `charts/ollyscale/`.

## License

AGPL-3.0 - See [LICENSE](../../LICENSE)
