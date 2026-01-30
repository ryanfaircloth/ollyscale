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
- Poetry
- PostgreSQL 15+ (for local development)

### Setup

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Start development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running with Database

```bash
# Set database URL
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/ollyscale"

# Run migrations
poetry run alembic upgrade head

# Start server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
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
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_models.py -v
```

## Code Quality

```bash
# Lint and format
poetry run ruff check .
poetry run ruff format .

# Fix auto-fixable issues
poetry run ruff check --fix .
```

## Database Migrations

```bash
# Create new migration
poetry run alembic revision -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Show current migration
poetry run alembic current

# Show migration history
poetry run alembic history --verbose
```

## Deployment

See Helm chart documentation in `charts/ollyscale/`.

## License

AGPL-3.0 - See [LICENSE](../../LICENSE)
