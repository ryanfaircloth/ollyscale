-- ollyScale v2 initial schema: traces, logs, metrics (star schema, OTEL-aligned)
-- This script is suitable for Alembic or direct execution in dev/test environments.


-- Dimension tables
CREATE TABLE IF NOT EXISTS service_dim (
    service_id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS operation_dim (
    operation_id SERIAL PRIMARY KEY,
    operation_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS resource_dim (
    resource_id SERIAL PRIMARY KEY,
    resource_jsonb JSONB NOT NULL
);

-- Fact table: spans (traces)
CREATE TABLE IF NOT EXISTS spans_fact (
    span_id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL,
    parent_span_id VARCHAR(32),
    service_id INTEGER REFERENCES service_dim(service_id),
    operation_id INTEGER REFERENCES operation_dim(operation_id),
    resource_id INTEGER REFERENCES resource_dim(resource_id),
    start_time_unix_nano BIGINT NOT NULL,
    end_time_unix_nano BIGINT NOT NULL,
    duration BIGINT GENERATED ALWAYS AS (end_time_unix_nano - start_time_unix_nano) STORED,
    status_code INTEGER,
    kind INTEGER,
    tenant_id TEXT,
    connection_id TEXT,
    attributes JSONB,
    events JSONB,
    links JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    partition_key DATE GENERATED ALWAYS AS (to_timestamp(start_time_unix_nano / 1e9)::date) STORED
)
PARTITION BY RANGE (partition_key);

-- Example partition for current month (adjust as needed)
CREATE TABLE IF NOT EXISTS spans_fact_p202601 PARTITION OF spans_fact
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Fact table: logs
CREATE TABLE IF NOT EXISTS logs_fact (
    log_id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(32),
    span_id VARCHAR(32),
    service_id INTEGER REFERENCES service_dim(service_id),
    resource_id INTEGER REFERENCES resource_dim(resource_id),
    time_unix_nano BIGINT NOT NULL,
    severity_text TEXT,
    body TEXT,
    tenant_id TEXT,
    connection_id TEXT,
    attributes JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    partition_key DATE GENERATED ALWAYS AS (to_timestamp(time_unix_nano / 1e9)::date) STORED
)
PARTITION BY RANGE (partition_key);

CREATE TABLE IF NOT EXISTS logs_fact_p202601 PARTITION OF logs_fact
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Fact table: metrics
CREATE TABLE IF NOT EXISTS metrics_fact (
    metric_id BIGSERIAL PRIMARY KEY,
    service_id INTEGER REFERENCES service_dim(service_id),
    resource_id INTEGER REFERENCES resource_dim(resource_id),
    name TEXT NOT NULL,
    time_unix_nano BIGINT NOT NULL,
    value DOUBLE PRECISION,
    tenant_id TEXT,
    connection_id TEXT,
    attributes JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    partition_key DATE GENERATED ALWAYS AS (to_timestamp(time_unix_nano / 1e9)::date) STORED
)
PARTITION BY RANGE (partition_key);

CREATE TABLE IF NOT EXISTS metrics_fact_p202601 PARTITION OF metrics_fact
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_spans_fact_trace_id ON spans_fact (trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_fact_service_id ON spans_fact (service_id);
CREATE INDEX IF NOT EXISTS idx_spans_fact_start_time ON spans_fact (start_time_unix_nano);
CREATE INDEX IF NOT EXISTS idx_logs_fact_trace_id ON logs_fact (trace_id);
CREATE INDEX IF NOT EXISTS idx_logs_fact_service_id ON logs_fact (service_id);
CREATE INDEX IF NOT EXISTS idx_logs_fact_time ON logs_fact (time_unix_nano);
CREATE INDEX IF NOT EXISTS idx_metrics_fact_service_id ON metrics_fact (service_id);
CREATE INDEX IF NOT EXISTS idx_metrics_fact_time ON metrics_fact (time_unix_nano);

-- Note: Add/rotate partitions as needed for production
