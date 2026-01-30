# Partition Management

## Overview

The ollyScale v2 backend uses PostgreSQL native table partitioning to efficiently manage
time-series observability data. This document describes the automated partition
management system.

## Why Partitioning?

Time-series data (traces, logs, metrics) accumulates rapidly and has a natural
time-based access pattern:

- **Recent data is hot** - Most queries target last few hours/days
- **Old data is cold** - Rarely accessed after retention period
- **Predictable lifecycle** - Data expires based on retention policy

Partitioning provides:

- **Query performance** - Partition pruning skips irrelevant data
- **Efficient deletion** - Drop entire partitions instead of DELETE (much faster)
- **Storage optimization** - Old partitions can be compressed or moved to cold storage
- **Maintenance windows** - Operations on individual partitions don't lock entire table

## Partitioning Strategy

### Tables

All fact tables use range partitioning on their timestamp column:

| Table         | Partition Key    | Retention (default) |
|---------------|------------------|---------------------|
| `spans_fact`  | `start_time_ns`  | 7 days              |
| `logs_fact`   | `timestamp_ns`   | 3 days              |
| `metrics_fact`| `timestamp_ns`   | 30 days             |

### Partition Naming Convention

Partitions are named: `{table_name}_y{YYYY}_m{MM}_d{DD}`

Examples:

- `spans_fact_y2026_m01_d21` - Spans for January 21, 2026
- `logs_fact_y2026_m01_d20` - Logs for January 20, 2026
- `metrics_fact_y2026_m02_d05` - Metrics for February 5, 2026

### Partition Granularity

- **Daily partitions** (24-hour intervals)
- Aligned to UTC day boundaries
- One partition per table per day

## Automated Management

### CronJob

The `partition-maintenance` CronJob runs daily at 2 AM UTC:

```yaml
partitionMaintenance:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  daysAhead: 7            # Create partitions 7 days ahead
```

**Actions performed:**

1. **Create future partitions** - Ensures partitions exist for upcoming data
2. **Drop old partitions** - Removes partitions older than retention policy

### Functions

#### `create_partitions_for_range()`

Creates partitions for a time range.

**Signature:**

```sql
create_partitions_for_range(
    table_name TEXT,
    start_time BIGINT,
    end_time BIGINT,
    interval_hours INTEGER DEFAULT 24
) RETURNS INTEGER
```

**Parameters:**

- `table_name` - Target fact table (`spans_fact`, `logs_fact`, `metrics_fact`)
- `start_time` - Start time in nanoseconds (Unix epoch)
- `end_time` - End time in nanoseconds
- `interval_hours` - Partition size in hours (default: 24)

**Returns:** Number of partitions created

**Example:**

```sql
-- Create daily partitions for spans_fact for next 7 days
SELECT create_partitions_for_range(
    'spans_fact',
    EXTRACT(EPOCH FROM NOW())::BIGINT * 1000000000,
    EXTRACT(EPOCH FROM NOW() + INTERVAL '7 days')::BIGINT * 1000000000,
    24
);
```

#### `drop_old_partitions()`

Drops partitions older than retention policy.

**Signature:**

```sql
drop_old_partitions(
    table_name TEXT,
    signal_type TEXT,
    tenant_id_param TEXT DEFAULT 'default'
) RETURNS INTEGER
```

**Parameters:**

- `table_name` - Target fact table
- `signal_type` - Signal type (`traces`, `logs`, `metrics`)
- `tenant_id_param` - Tenant ID (default: `'default'`)

**Returns:** Number of partitions dropped

**Example:**

```sql
-- Drop old trace partitions
SELECT drop_old_partitions('spans_fact', 'traces', 'default');
```

#### `maintenance_create_partitions()`

Wrapper that creates future partitions for all fact tables.

**Signature:**

```sql
maintenance_create_partitions(
    days_ahead INTEGER DEFAULT 7
) RETURNS TABLE(table_name TEXT, partitions_created INTEGER)
```

**Parameters:**

- `days_ahead` - Number of days ahead to create partitions (default: 7)

**Returns:** Table with results per fact table

**Example:**

```sql
-- Create partitions 14 days ahead
SELECT * FROM maintenance_create_partitions(14);
```

Output:

```text
  table_name   | partitions_created
---------------+-------------------
 spans_fact    |                 7
 logs_fact     |                 7
 metrics_fact  |                 7
```

#### `maintenance_drop_partitions()`

Wrapper that drops old partitions for all fact tables.

**Signature:**

```sql
maintenance_drop_partitions()
RETURNS TABLE(table_name TEXT, signal_type TEXT, partitions_dropped INTEGER)
```

**Returns:** Table with results per fact table

**Example:**

```sql
SELECT * FROM maintenance_drop_partitions();
```

Output:

```text
  table_name   | signal_type | partitions_dropped
---------------+-------------+-------------------
 spans_fact    | traces      |                 2
 logs_fact     | logs        |                 5
 metrics_fact  | metrics     |                 0
```

## Monitoring

### View All Partitions

```sql
SELECT
    parent.relname AS table_name,
    child.relname AS partition_name,
    pg_size_pretty(pg_total_relation_size(child.oid)) AS partition_size,
    pg_get_expr(child.relpartbound, child.oid) AS partition_range
FROM pg_class parent
JOIN pg_inherits i ON i.inhparent = parent.oid
JOIN pg_class child ON child.oid = i.inhrelid
WHERE parent.relname IN ('spans_fact', 'logs_fact', 'metrics_fact')
ORDER BY parent.relname, child.relname;
```

### Check Partition Coverage

```sql
-- Check if partitions exist for today and tomorrow
WITH dates AS (
    SELECT
        t.table_name,
        CURRENT_DATE + i AS check_date
    FROM generate_series(0, 1) AS i
    CROSS JOIN (VALUES ('spans_fact'), ('logs_fact'), ('metrics_fact')) AS t(table_name)
)
SELECT
    d.table_name,
    d.check_date,
    CASE
        WHEN c.relname IS NOT NULL THEN 'EXISTS'
        ELSE 'MISSING'
    END AS status
FROM dates d
LEFT JOIN pg_class c ON c.relname = d.table_name || '_y' ||
    TO_CHAR(d.check_date, 'YYYY') || '_m' ||
    TO_CHAR(d.check_date, 'MM') || '_d' ||
    TO_CHAR(d.check_date, 'DD')
ORDER BY d.table_name, d.check_date;
```

### Partition Sizes

```sql
SELECT
    parent.relname AS table_name,
    COUNT(*) AS partition_count,
    pg_size_pretty(SUM(pg_total_relation_size(child.oid))) AS total_size,
    pg_size_pretty(AVG(pg_total_relation_size(child.oid))::BIGINT) AS avg_partition_size
FROM pg_class parent
JOIN pg_inherits i ON i.inhparent = parent.oid
JOIN pg_class child ON child.oid = i.inhrelid
WHERE parent.relname IN ('spans_fact', 'logs_fact', 'metrics_fact')
GROUP BY parent.relname
ORDER BY parent.relname;
```

## Troubleshooting

### Missing Partitions

**Symptom:** Ingestion fails with "no partition of relation found for row"

**Diagnosis:**

```sql
-- Check if partition exists for specific timestamp
SELECT
    table_name || '_y' ||
    TO_CHAR(TO_TIMESTAMP(timestamp_ns / 1000000000.0), 'YYYY') || '_m' ||
    TO_CHAR(TO_TIMESTAMP(timestamp_ns / 1000000000.0), 'MM') || '_d' ||
    TO_CHAR(TO_TIMESTAMP(timestamp_ns / 1000000000.0), 'DD') AS expected_partition,
    EXISTS (
        SELECT 1 FROM pg_class
        WHERE relname = table_name || '_y' ||
            TO_CHAR(TO_TIMESTAMP(timestamp_ns / 1000000000.0), 'YYYY') || '_m' ||
            TO_CHAR(TO_TIMESTAMP(timestamp_ns / 1000000000.0), 'MM') || '_d' ||
            TO_CHAR(TO_TIMESTAMP(timestamp_ns / 1000000000.0), 'DD')
    ) AS partition_exists
FROM (
    SELECT 'spans_fact' AS table_name, 1737478800000000000::BIGINT AS timestamp_ns
) AS test;
```

**Fix:** Create missing partition manually

```sql
-- Create partition for specific date
SELECT create_partitions_for_range(
    'spans_fact',
    EXTRACT(EPOCH FROM '2026-01-21'::TIMESTAMP)::BIGINT * 1000000000,
    EXTRACT(EPOCH FROM '2026-01-22'::TIMESTAMP)::BIGINT * 1000000000,
    24
);
```

### CronJob Not Running

**Diagnosis:**

```bash
# Check CronJob status
kubectl get cronjob -n ollyscale partition-maintenance

# Check recent jobs
kubectl get jobs -n ollyscale -l app.kubernetes.io/component=partition-maintenance

# Check logs
kubectl logs -n ollyscale -l app.kubernetes.io/component=partition-maintenance
```

**Fix:** Trigger manual job

```bash
kubectl create job -n ollyscale \
    partition-maintenance-manual \
    --from=cronjob/ollyscale-partition-maintenance
```

### Partition Cleanup Not Working

**Symptom:** Old partitions not being dropped

**Diagnosis:**

```sql
-- Check retention policy
SELECT * FROM retention_policy;

-- Manually test drop function
SELECT * FROM drop_old_partitions('spans_fact', 'traces', 'default');
```

**Fix:** Verify retention policy is correct

```sql
-- Update retention policy if needed
UPDATE retention_policy
SET retention_days_value = 7
WHERE signal_type_value = 'traces' AND tenant_id = 'default';
```

## Manual Operations

### Create Partitions for Specific Date Range

```sql
-- Create partitions for January 2026
SELECT create_partitions_for_range(
    'spans_fact',
    EXTRACT(EPOCH FROM '2026-01-01'::TIMESTAMP)::BIGINT * 1000000000,
    EXTRACT(EPOCH FROM '2026-02-01'::TIMESTAMP)::BIGINT * 1000000000,
    24
);
```

### Drop Specific Partition

```sql
-- Drop partition for specific date
DROP TABLE IF EXISTS spans_fact_y2026_m01_d15;
```

### Disable Automatic Maintenance

```bash
# Edit values.yaml
helm upgrade ollyscale ./charts/ollyscale \
    --namespace ollyscale \
    --set partitionMaintenance.enabled=false
```

## Best Practices

1. **Monitor partition coverage** - Ensure partitions exist for current + N days ahead
2. **Check CronJob logs** - Review daily maintenance logs for errors
3. **Set appropriate retention** - Balance storage costs vs. query needs
4. **Test manually first** - Run maintenance functions manually before relying on CronJob
5. **Plan for time zones** - Partitions use UTC, coordinate with query patterns
6. **Pre-create partitions** - Always maintain buffer of future partitions (7+ days)

## Integration with Other Components

### Migration Job

The [migration job](postgres-infrastructure.md#database-migrations) creates partition management functions during deployment:

- Runs `alembic upgrade head` as Helm pre-upgrade/pre-install hook
- Creates functions: `create_partitions_for_range()`, `drop_old_partitions()`, etc.
- Creates initial 7 days of partitions

### Ingestion Pipeline

The OTLP receiver and frontend API insert data into fact tables:

- PostgreSQL automatically routes rows to correct partition based on timestamp
- If no partition exists, insert fails with error
- Maintenance CronJob ensures partitions always exist

### Retention Policy

Partition cleanup respects the `retention_policy` table:

| tenant_id | signal_type_value | retention_days_value |
|-----------|-------------------|----------------------|
| default   | traces            | 7                    |
| default   | logs              | 3                    |
| default   | metrics           | 30                   |

See [ollyscale-v2-postgres.md](ollyscale-v2-postgres.md#retention-policy) for details.

## References

- [PostgreSQL Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [ollyscale v2 Architecture](ollyscale-v2-postgres.md)
- [Postgres Infrastructure](postgres-infrastructure.md)
- [Migration Strategy](postgres-infrastructure.md#database-migrations)
