-- ollyScale v2 initial schema: traces, logs, metrics (star schema, OTEL-aligned)
-- This script is suitable for Alembic or direct execution in dev/test environments.

CREATE TABLE IF NOT EXISTS trace (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS log (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS metric (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for efficient querying (to be refined as schema evolves)
CREATE INDEX IF NOT EXISTS idx_trace_created_at ON trace (created_at);
CREATE INDEX IF NOT EXISTS idx_log_created_at ON log (created_at);
CREATE INDEX IF NOT EXISTS idx_metric_created_at ON metric (created_at);

-- Future: add partitioning, star schema dimensions, and more detailed OTEL fields
