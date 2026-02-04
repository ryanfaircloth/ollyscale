# Attribute Key Analysis and Migration Plan

This directory contains tools to analyze existing JSONB attribute data and plan the migration to typed attribute tables.

## Overview

The hybrid attribute storage model requires understanding which keys exist in your data, their types, frequency, and cardinality. This helps decide:

1. **Which keys to promote** to typed tables (high frequency keys)
2. **Which indexing strategy** to use (based on cardinality)
3. **Proper type mapping** for each key

## Files

- **attribute-key-analysis.sql** - SQL script to analyze current JSONB columns
- **generate-attribute-schema.py** - Python script to generate typed table schemas
- **otel-ollyscale-data-model.md** - Target data model documentation

## Step 1: Analyze Current Data

Run the analysis SQL script against your current database:

```bash
psql -h your-host -U your-user -d your-database -f attribute-key-analysis.sql > analysis_results.txt
```

This will output several result sets:

### Resource Attributes Analysis

Shows all resource attribute keys found in:

- `resource_dim.attributes`
- `spans_fact.resource`
- `logs_fact.resource`
- `metrics_fact.resource`

### Scope Attributes Analysis

Shows all scope attribute keys from spans, logs, and metrics.

### Signal-Specific Attributes

Shows attributes from:

- `spans_fact.attributes`
- `logs_fact.attributes`
- `metrics_fact.attributes`

### Summary Report

The most important output showing:

- **Key name**
- **Detected type** (string, number, boolean, array, object)
- **Total occurrences** - how many times this key appears
- **Max distinct values** - cardinality estimate
- **Contexts** - where the key is used (resource, scope, span, log, metric)
- **Recommendation** - whether to promote to typed table
- **Index recommendation** - indexing strategy based on cardinality

### Type Consistency Check

Identifies keys that have inconsistent types (e.g., stored as string in one place, number in another).

## Step 2: Review Results

Look at the summary report and identify:

### High-Priority Keys (> 10,000 occurrences)

These should definitely be promoted to typed tables:

- `service.name`
- `service.instance.id`
- `deployment.environment`
- `http.method`
- `http.status_code`

### Medium-Priority Keys (1,000 - 10,000 occurrences)

Consider promoting based on query patterns:

- `host.name`
- `db.system`
- `http.target`

### Low-Priority Keys (< 1,000 occurrences)

Keep in JSONB catch-all table.

### Cardinality Considerations

**Low cardinality (< 100 distinct values)**

- Good for B-tree indexes
- Examples: `deployment.environment`, `http.method`

**Medium cardinality (100 - 10,000 distinct values)**

- B-tree indexes still effective
- Examples: `service.name`, `db.name`

**High cardinality (> 10,000 distinct values)**

- Indexes may be expensive
- Consider partial indexes or no index
- Examples: `http.url`, `db.statement`, `service.instance.id`

## Step 3: Generate Schema

Use the Python script to generate the actual table definitions:

```bash
# Generate with default threshold (1,000 occurrences)
python generate-attribute-schema.py --output generated-schema.sql

# Or customize threshold
python generate-attribute-schema.py --occurrence-threshold 5000 --output generated-schema.sql
```

This generates:

1. **attribute_keys table** - Registry of all promoted keys
2. **Type-specific tables** - e.g., `resource_attrs_string`, `span_attrs_int`
3. **Catch-all tables** - e.g., `resource_attrs_other` (JSONB)
4. **Migration scripts** - SQL to move data from old to new schema

## Step 4: Customize Schema

Review `generated-schema.sql` and adjust:

### Add Custom Keys

Based on your domain-specific attributes:

```sql
INSERT INTO attribute_keys (key, value_type, is_indexed, is_searchable) VALUES
  ('my.custom.attribute', 'string', true, true);
```

### Create Integer-Specific Tables

If you have many integer attributes, split from double:

```sql
CREATE TABLE resource_attrs_int (
  resource_id BIGINT NOT NULL,
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value BIGINT NOT NULL,
  PRIMARY KEY (resource_id, key_id)
);
```

### Adjust Indexing Strategy

```sql
-- Remove index from high-cardinality columns
DROP INDEX idx_span_attrs_string_value;

-- Create partial index for specific keys
CREATE INDEX idx_span_attrs_http_method
  ON span_attrs_string(value)
  WHERE key_id = (SELECT key_id FROM attribute_keys WHERE key = 'http.method');
```

## Step 5: Test Migration

Run in a development environment:

```bash
# Create new schema
psql -f generated-schema.sql

# Verify data
psql -c "SELECT COUNT(*) FROM resource_attrs_string;"
psql -c "SELECT COUNT(*) FROM resource_attrs_other;"

# Check for data consistency
psql -c "
  SELECT
    COUNT(*) as old_count
  FROM resource_dim,
    LATERAL jsonb_object_keys(attributes) as key
  WHERE attributes != '{}'::jsonb;

  SELECT
    (SELECT COUNT(*) FROM resource_attrs_string) +
    (SELECT COUNT(*) FROM resource_attrs_int) +
    (SELECT COUNT(*) FROM resource_attrs_double) +
    (SELECT COUNT(*) FROM resource_attrs_bool) as new_count;
"
```

## Step 6: Query Migration

Update application queries to use new schema:

### Old Query (JSONB)

```sql
SELECT * FROM spans_fact
WHERE attributes->>'http.method' = 'POST'
  AND (attributes->>'http.status_code')::int >= 500;
```

### New Query (Typed Tables)

```sql
SELECT s.* FROM spans_fact s
JOIN span_attrs_string sas1
  ON s.id = sas1.span_id
  AND sas1.key_id = (SELECT key_id FROM attribute_keys WHERE key = 'http.method')
  AND sas1.value = 'POST'
JOIN span_attrs_int sai1
  ON s.id = sai1.span_id
  AND sai1.key_id = (SELECT key_id FROM attribute_keys WHERE key = 'http.status_code')
  AND sai1.value >= 500;
```

### Or Use Unified View

```sql
CREATE VIEW span_attrs_unified AS
SELECT span_id, ak.key, 'string' as type, sas.value::text as value
FROM span_attrs_string sas
JOIN attribute_keys ak USING (key_id)
UNION ALL
SELECT span_id, ak.key, 'int' as type, sai.value::text as value
FROM span_attrs_int sai
JOIN attribute_keys ak USING (key_id);

-- Query using view
SELECT s.* FROM spans_fact s
JOIN span_attrs_unified sau1 ON s.id = sau1.span_id
  AND sau1.key = 'http.method' AND sau1.value = 'POST'
JOIN span_attrs_unified sau2 ON s.id = sau2.span_id
  AND sau2.key = 'http.status_code' AND sau2.value::int >= 500;
```

## Step 7: Create Alembic Migration

Create production migration:

```bash
cd apps/api
alembic revision -m "add_typed_attribute_tables"
```

Edit the migration file to include:

1. Forward migration from `generated-schema.sql`
2. Backward migration (drop tables, restore JSONB)
3. Data migration logic

## Performance Expectations

### Query Performance

- **JSONB searches**: 10-100ms for GIN index lookups
- **Typed table joins**: 1-10ms for B-tree index lookups (10-100x faster)

### Storage Efficiency

- **JSONB with duplicates**: ~500 bytes per span with 20 attributes
- **Typed tables with key_id**: ~200 bytes per span (60% reduction)

### Ingestion Performance

- **JSONB insert**: Single row insert
- **Typed tables**: Multiple inserts (1 per promoted attribute) but better normalization

## Common OTEL Semantic Convention Keys

Pre-populate these high-frequency keys:

### Resource (service identity)

- `service.name` - Service identifier (string)
- `service.namespace` - Service grouping (string)
- `service.version` - Service version (string)
- `service.instance.id` - Unique instance ID (string)
- `deployment.environment` - Deployment stage (string)

### Resource (host info)

- `host.name` - Hostname (string)
- `host.arch` - Architecture (string)
- `process.pid` - Process ID (number)

### Resource (telemetry SDK)

- `telemetry.sdk.name` - SDK name (string)
- `telemetry.sdk.language` - Language (string)
- `telemetry.sdk.version` - SDK version (string)

### Span (HTTP)

- `http.method` - HTTP method (string)
- `http.status_code` - Status code (number)
- `http.url` - Full URL (string, high cardinality)
- `http.target` - Target path (string, high cardinality)

### Span (Database)

- `db.system` - Database type (string)
- `db.name` - Database name (string)
- `db.statement` - SQL/query (string, high cardinality)

### Span (Messaging)

- `messaging.system` - Message system (string)
- `messaging.destination` - Queue/topic (string)

## References

- [OTEL Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [otel-ollyscale-data-model.md](otel-ollyscale-data-model.md)
- [schema-migration-analysis.md](schema-migration-analysis.md)
