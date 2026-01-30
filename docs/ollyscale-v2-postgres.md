# ollyScale v2 - Postgres Backend Architecture

## Overview

ollyScale v2 introduces a PostgreSQL-backed storage layer to replace the Redis-based ephemeral storage,
providing persistent, queryable observability data with OTEL-aligned schema design.

## Architecture Principles

### Core Tenets

- **OTEL-Native**: Schema aligned with OpenTelemetry data model and semantic conventions
- **Postgres-First**: Leverage PostgreSQL features (JSONB, partitioning, indexes, pg_cron)
- **Separation of Concerns**: New `apps/frontend` app is independent from legacy `apps/ollyscale`
- **Clean Install**: No migration/ETL from Redis required
- **Kubernetes Native**: Managed via Zalando Postgres Operator

### Technology Stack

- **Database**: PostgreSQL 18+ via Zalando Postgres Operator
- **App Framework**: FastAPI with async SQLAlchemy
- **Migration Tool**: Alembic
- **Exposure**: Kubernetes Gateway API (HTTPRoutes)
- **Deployment**: Helm charts with K8s Jobs for migrations

## Data Model

### Signals

Three primary telemetry signals with OTEL alignment:

1. **Traces** (`spans_fact` table)
2. **Logs** (`logs_fact` table)
3. **Metrics** (`metrics_fact` table)

### Fact Tables

#### spans_fact

Stores distributed trace spans with OTEL span model:

```sql
CREATE TABLE spans_fact (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL DEFAULT 'default',
    connection_id VARCHAR(255),
    trace_id VARCHAR(32) NOT NULL,
    span_id VARCHAR(16) NOT NULL,
    parent_span_id VARCHAR(16),

    -- Core OTEL fields
    name VARCHAR(1024) NOT NULL,
    kind SMALLINT NOT NULL,  -- OTEL SpanKind enum
    status_code SMALLINT,     -- OTEL StatusCode enum
    status_message TEXT,

    -- Timing
    start_time_unix_nano BIGINT NOT NULL,
    end_time_unix_nano BIGINT NOT NULL,
    duration BIGINT GENERATED ALWAYS AS (end_time_unix_nano - start_time_unix_nano) STORED,

    -- References
    service_id INTEGER REFERENCES service_dim(id),
    operation_id INTEGER REFERENCES operation_dim(id),
    resource_id INTEGER REFERENCES resource_dim(id),

    -- OTEL structures as JSONB
    attributes JSONB,
    events JSONB,
    links JSONB,
    resource JSONB,
    scope JSONB,

    -- Flags
    flags INTEGER DEFAULT 0,
    dropped_attributes_count INTEGER DEFAULT 0,
    dropped_events_count INTEGER DEFAULT 0,
    dropped_links_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (start_time_unix_nano);

CREATE INDEX idx_spans_trace_id ON spans_fact(trace_id);
CREATE INDEX idx_spans_service ON spans_fact(service_id);
CREATE INDEX idx_spans_time ON spans_fact(start_time_unix_nano);
CREATE INDEX idx_spans_attributes ON spans_fact USING GIN (attributes);
```

#### logs_fact

Stores log entries with OTEL log data model:

```sql
CREATE TABLE logs_fact (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL DEFAULT 'default',
    connection_id VARCHAR(255),

    -- OTEL correlation
    trace_id VARCHAR(32),
    span_id VARCHAR(16),

    -- Timing
    time_unix_nano BIGINT NOT NULL,
    observed_time_unix_nano BIGINT,

    -- Severity
    severity_number SMALLINT,
    severity_text VARCHAR(64),

    -- Content
    body JSONB,

    -- OTEL structures
    attributes JSONB,
    resource JSONB,
    scope JSONB,

    -- Flags
    flags INTEGER DEFAULT 0,
    dropped_attributes_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (time_unix_nano);

CREATE INDEX idx_logs_trace_id ON logs_fact(trace_id);
CREATE INDEX idx_logs_time ON logs_fact(time_unix_nano);
CREATE INDEX idx_logs_severity ON logs_fact(severity_number);
CREATE INDEX idx_logs_attributes ON logs_fact USING GIN (attributes);
```

#### metrics_fact

Stores metrics with OTEL metrics data model:

```sql
CREATE TABLE metrics_fact (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL DEFAULT 'default',
    connection_id VARCHAR(255),

    -- Metric identity
    metric_name VARCHAR(1024) NOT NULL,
    metric_type VARCHAR(32) NOT NULL,  -- gauge, sum, histogram, summary, exponential_histogram
    unit VARCHAR(64),
    description TEXT,

    -- Timing
    time_unix_nano BIGINT NOT NULL,
    start_time_unix_nano BIGINT,

    -- OTEL structures
    resource JSONB,
    scope JSONB,
    attributes JSONB,
    data_points JSONB,  -- Array of data point objects

    -- Aggregation temporality (for sum/histogram)
    temporality VARCHAR(32),

    -- Monotonicity (for sum)
    is_monotonic BOOLEAN,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (time_unix_nano);

CREATE INDEX idx_metrics_name ON metrics_fact(metric_name);
CREATE INDEX idx_metrics_time ON metrics_fact(time_unix_nano);
CREATE INDEX idx_metrics_attributes ON metrics_fact USING GIN (attributes);
```

### Dimension Tables

#### service_dim

Service catalog:

```sql
CREATE TABLE service_dim (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL DEFAULT 'default',
    name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL DEFAULT '',
    version VARCHAR(255),
    attributes JSONB,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, name, namespace)
);
```

**Note on namespace**: Per OTEL spec, `service.namespace` is optional. We store empty string `''` when not provided (rather than NULL) so the UNIQUE constraint works correctly. OTEL spec states: "If service.namespace is not specified then service.name is expected to be unique for all services that have no explicit namespace defined (so the empty/unspecified namespace is simply one more valid namespace)."

#### operation_dim

Operation (span name) catalog:

```sql
CREATE TABLE operation_dim (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL DEFAULT 'default',
    service_id INTEGER REFERENCES service_dim(id),
    name VARCHAR(1024) NOT NULL,
    span_kind SMALLINT,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, service_id, name, span_kind)
);
```

#### resource_dim

Resource attributes catalog:

```sql
CREATE TABLE resource_dim (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL DEFAULT 'default',
    resource_hash VARCHAR(64) NOT NULL,
    attributes JSONB NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, resource_hash)
);

CREATE INDEX idx_resource_attributes ON resource_dim USING GIN (attributes);
```

## Retention & Partitioning

### Retention Policy Table

```sql
CREATE TABLE retention_policy (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL DEFAULT 'default',
    signal_type VARCHAR(32) NOT NULL,  -- 'traces', 'logs', 'metrics'
    retention_days INTEGER NOT NULL DEFAULT 7,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, signal_type)
);

-- Default retention policies
INSERT INTO retention_policy (tenant_id, signal_type, retention_days) VALUES
    ('default', 'traces', 7),
    ('default', 'logs', 3),
    ('default', 'metrics', 30);
```

### Partitioning Strategy

**Approach**: Native PostgreSQL table partitioning by time range

**Interval**: Daily partitions for spans_fact and logs_fact, weekly for metrics_fact

**Rationale**:

- Daily spans/logs for fine-grained retention control
- Weekly metrics for reduced partition overhead (metrics have higher cardinality)
- Partition pruning optimizes time-range queries
- Easy partition dropping for retention enforcement

**Partition Naming**:

- `spans_fact_YYYYMMDD` (e.g., `spans_fact_20260121`)
- `logs_fact_YYYYMMDD`
- `metrics_fact_YYYYWW` (e.g., `metrics_fact_202603` for week 3)

### Retention Enforcement

**Mechanism**: Kubernetes CronJob running daily at 02:00 UTC

**Process**:

1. Query `retention_policy` table for each signal type
2. Calculate partition names older than retention window
3. Drop expired partitions: `DROP TABLE IF EXISTS spans_fact_YYYYMMDD`
4. Log dropped partitions to stdout (captured by K8s logs)

**Job Specification**: See `charts/ollyscale/templates/cronjob-retention.yaml`

## API Design

### Endpoints

#### Ingest

- `POST /api/traces` - Ingest OTLP traces
- `POST /api/logs` - Ingest OTLP logs
- `POST /api/metrics` - Ingest OTLP metrics

#### Query

- `GET /api/traces/search` - Search traces with filters
- `GET /api/traces/{trace_id}` - Get trace by ID
- `GET /api/logs/search` - Search logs with filters
- `GET /api/metrics/search` - Query metrics
- `GET /api/service-map` - Get service dependency graph
- `GET /api/services` - List services with RED metrics

### Query Semantics

**Time Range (Required)**:

- All queries require `start_time` and `end_time` parameters (Unix nanoseconds)
- Leverages partition pruning for performance

**Filtering**:

- Structured filters: `{field: string, operator: string, value: any}[]`
- Supported operators: `eq`, `ne`, `gt`, `lt`, `gte`, `lte`, `contains`, `regex`
- Common fields: `service.name`, `http.method`, `status.code`, `severity`, `trace_id`

**Pagination**:

- Cursor-based pagination (opaque cursor encoding time + id)
- `limit` parameter (default: 100, max: 1000)
- Response includes `has_more` boolean and `next_cursor` string

**Limits**:

- Hard maximum of 1000 results per request (server-side enforcement)
- Query timeout: 30 seconds
- Large result warnings at 500+ rows

## Deployment

### Prerequisites

- Kubernetes cluster with Gateway API CRDs installed
- Zalando Postgres Operator deployed
- Sufficient storage for Postgres PVCs (default: 30GB)

### Components

1. **Postgres Cluster** (`apps/frontend/postgres-cluster`)
   - Zalando `postgresql` CRD resource
   - Single-node, no HA (upgradeable to Patroni later)
   - Operator-managed credentials in Secret

2. **Migration Job** (`charts/ollyscale/templates/job-migration.yaml`)
   - Runs Alembic `upgrade head` before app deployment
   - Uses init container pattern with shared volume
   - Fails deployment if migrations fail

3. **Frontend App** (`charts/ollyscale/templates/deployment-frontend.yaml`)
   - FastAPI app with async SQLAlchemy connection pool
   - Reads DB credentials from operator-managed Secret
   - Readiness probe checks DB connectivity + migration status

4. **Gateway API** (`charts/ollyscale/templates/httproute-frontend.yaml`)
   - HTTPRoute exposing `/api/*` paths
   - Matches Gateway in `ollyscale` namespace

### Helm Values

```yaml
postgres:
  enabled: true
  operator:
    namespace: postgres-operator
  cluster:
    name: ollyscale-db
    size: 30Gi
    storageClass: standard
  credentials:
    secretName: ollyscale-db-credentials

frontend:
  replicas: 2
  image:
    repository: ghcr.io/ryanfaircloth/ollyscale/frontend
    tag: "v2.0.0"
  resources:
    requests:
      memory: 512Mi
      cpu: 250m
    limits:
      memory: 1Gi
      cpu: 1000m
  database:
    poolSize: 20
    maxOverflow: 10
    queryTimeout: 30

migration:
  enabled: true
  backoffLimit: 3
  ttlSecondsAfterFinished: 86400
```

### Credentials Flow

1. **Zalando Operator** creates Secret: `<cluster-name>.<user>.<secret-suffix>`
   - Format: `ollyscale-db.frontend.credentials`
   - Keys: `username`, `password`, `hostname`, `port`, `database`

2. **Migration Job** mounts Secret as environment variables:

   ```yaml
   env:
     - name: DB_HOST
       valueFrom:
         secretKeyRef:
           name: ollyscale-db.frontend.credentials
           key: hostname
   ```

3. **Frontend App** constructs connection string:

   ```python
   DB_URL = f"postgresql+asyncpg://{username}:{password}@{hostname}:{port}/{database}"
   ```

## Migration Management

### Alembic Configuration

**Location**: `apps/frontend/migrations/`

**Key Files**:

- `alembic.ini` - Alembic configuration
- `env.py` - Environment setup with async support
- `versions/` - Migration scripts

**Connection String**:

```python
# env.py
config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/ollyscale")
)
```

### Creating Migrations

```bash
cd apps/frontend
poetry run alembic revision -m "add spans_fact partitioning"
# Edit generated file in migrations/versions/
poetry run alembic upgrade head  # Test locally
```

### Migration Job Flow

1. Init container runs `alembic upgrade head`
2. Logs migration output to stdout
3. Exits with code 0 on success, non-zero on failure
4. Main app container only starts if init container succeeds
5. Kubernetes backoff handles transient failures

### Rollback Strategy

**Automatic Rollback**: Not supported (forward-only migrations)

**Manual Rollback**:

```bash
kubectl exec -it <migration-job-pod> -- alembic downgrade -1
```

**Backup Strategy** (future):

- pg_dump before major schema changes
- Stored in S3-compatible object storage

## Health Endpoints

### `/health` (Overall Status)

Returns 200 if app is healthy, 503 if degraded:

```json
{
  "status": "healthy",
  "database": "connected",
  "migrations": "current",
  "version": "v2.0.0"
}
```

### `/health/db` (Database Status)

Returns DB connectivity and migration status:

```json
{
  "connected": true,
  "pool_size": 20,
  "pool_active": 5,
  "migrations_applied": 42,
  "latest_migration": "20260121_add_metrics_partitioning"
}
```

## Observability & Performance

### Instrumentation

**OTEL Tracing**:

- FastAPI automatic instrumentation via `opentelemetry-instrumentation-fastapi`
- SQLAlchemy query tracing via `opentelemetry-instrumentation-sqlalchemy`
- Sampling: 10% for normal requests, 100% for errors

**Metrics**:

- HTTP request duration (histogram)
- Database connection pool stats (gauge)
- Query execution time by endpoint (histogram)
- Ingest throughput (counter)

**Logging**:

- Structured JSON logs to stdout
- Correlation via `trace_id` and `span_id` fields
- Log levels: INFO (normal), DEBUG (query details), ERROR (failures)

### Performance Optimization

**Indexes**:

- B-tree on time columns (partition key)
- B-tree on trace_id, span_id (exact match queries)
- GIN on JSONB attributes (attribute filtering)
- Composite indexes on (service_id, time) for service-filtered queries

**Query Patterns**:

- Always include time range in WHERE clause (partition pruning)
- Use `attributes @> '{"key": "value"}'` for JSONB filtering
- Prefer `EXISTS` over `IN` for subqueries
- Use `EXPLAIN ANALYZE` for slow query debugging

**Connection Pooling**:

- SQLAlchemy async pool: 20 connections, max_overflow 10
- Connection timeout: 5 seconds
- Pool pre-ping enabled for stale connection detection

**Caching** (future):

- Service map cached for 30 seconds (Redis)
- Service catalog cached for 5 minutes
- Query result caching for identical time ranges (optional)

## Troubleshooting

### Migration Failures

**Symptom**: Migration Job fails, pods stuck in Init

**Diagnosis**:

```bash
kubectl logs -n ollyscale job/ollyscale-migration
```

**Common Causes**:

- DB credentials incorrect (check Secret)
- DB not reachable (check network policies)
- Syntax error in migration script
- Concurrent migration attempts (lock timeout)

**Resolution**:

- Fix underlying issue (credentials, network, SQL)
- Delete failed Job: `kubectl delete job -n ollyscale ollyscale-migration`
- Helm upgrade will recreate Job

### Slow Queries

**Symptom**: API timeouts, high DB load

**Diagnosis**:

```sql
-- Check slow queries
SELECT * FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
AND correlation < 0.5;
```

**Resolution**:

- Add missing indexes based on query patterns
- Reduce query time range
- Increase `limit` parameter instead of broad queries
- Consider query result caching

### High Cardinality

**Symptom**: Metrics table growing rapidly, slow queries

**Diagnosis**:

```sql
SELECT metric_name, COUNT(DISTINCT attributes) as cardinality
FROM metrics_fact
WHERE time_unix_nano > extract(epoch from now() - interval '1 hour') * 1000000000
GROUP BY metric_name
ORDER BY cardinality DESC
LIMIT 20;
```

**Resolution**:

- Identify high-cardinality metrics
- Drop unnecessary attributes at ingestion (OTEL Processor)
- Implement attribute allowlist/blocklist
- Consider aggregating high-cardinality metrics

### Partition Management

**Symptom**: Retention Job fails, old partitions not dropping

**Diagnosis**:

```bash
kubectl logs -n ollyscale cronjob/ollyscale-retention
```

**Resolution**:

- Check CronJob schedule and last run time
- Verify `retention_policy` table values
- Manually drop partitions if needed:

  ```sql
  DROP TABLE IF EXISTS spans_fact_20260101;
  ```

## Future Enhancements

**High Availability**:

- Enable Patroni for Postgres HA (Zalando Operator supports this)
- Multi-replica frontend app (already supported)
- Cross-AZ deployment

**Backups**:

- Automated pg_basebackup to S3
- Point-in-time recovery (PITR) via WAL archiving
- Backup retention policy (30 days)

**Multi-Tenancy**:

- Row-level security (RLS) for tenant isolation
- Separate schemas per tenant
- Tenant-specific retention policies

**Query Optimization**:

- Materialized views for service catalog
- Pre-aggregated RED metrics tables
- Query result caching (Redis)

**Advanced Features**:

- Trace exemplars linked to metrics
- Log pattern detection
- Anomaly detection on metrics
- Alerting on query results

## References

- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/)
- [Zalando Postgres Operator](https://github.com/zalando/postgres-operator)
- [PostgreSQL Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [FastAPI Async SQL](https://fastapi.tiangolo.com/advanced/async-sql-databases/)
