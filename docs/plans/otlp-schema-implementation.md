# OTLP Schema Implementation Plan

**Status**: Phase 4 Complete - Metrics Tables Needed 
**Branch**: `improve-data-model`  
**Breaking Change**: Yes - Complete schema overhaul

## Overview

Complete OTLP-aligned schema implementation with attribute promotion, timestamp+nanos precision, and enriched views. Current migration (8316334b1935) has logs and spans working but is **MISSING** critical tables for metrics, reference data, span events/links, and resource/scope attributes.

## Implementation Status

### ✅ COMPLETED (Deployed & Working)

**Database Schema:**
- ✅ attribute_keys table (deduplication registry)
- ✅ otel_resources_dim table (with hash deduplication)
- ✅ otel_scopes_dim table (with hash deduplication)
- ✅ otel_logs_fact table (timestamp+nanos pattern)
- ✅ All 6 log attribute tables (string, int, double, bool, bytes, other)
- ✅ otel_spans_fact table (timestamp+nanos pattern, events/links as JSONB)
- ✅ All 6 span attribute tables
- ✅ v_otel_logs_enriched view (aggregates all attributes)
- ✅ v_otel_spans_enriched view (aggregates all attributes)

**Python Implementation:**
- ✅ AttributePromotionConfig class (48 tests passing)
- ✅ AttributeManager class (attribute routing & storage)
- ✅ ResourceManager class (hash-based deduplication)
- ✅ LogsStorage class (OTLP ingestion)
- ✅ TracesStorage class (OTLP ingestion)
- ✅ MetricsStorage class (OTLP ingestion)
- ✅ ORM models for all implemented tables
- ✅ /api/v2/logs endpoints (search, trace correlation)
- ✅ /api/v2/traces endpoints (search, span retrieval)
- ✅ /api/v2/metrics endpoints (search, aggregation)

**Configuration:**
- ✅ config/attribute-promotion.yaml (base semantic conventions)
- ✅ charts/ollyscale/templates/attribute-overrides-configmap.yaml
- ✅ Helm chart integration

### ❌ MISSING (Must Complete for Full OTLP Compliance)

**Reference/Lookup Tables (6 tables)** - CRITICAL for OTLP spec compliance:
- ❌ log_severity_numbers (severity levels 0-24)
- ❌ log_body_types (EMPTY, STRING, INT, DOUBLE, BOOL, BYTES, ARRAY, KVLIST)
- ❌ span_kinds (UNSPECIFIED, INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
- ❌ status_codes (UNSET, OK, ERROR)
- ❌ metric_types (GAUGE, SUM, HISTOGRAM, EXP_HISTOGRAM, SUMMARY)
- ❌ aggregation_temporalities (UNSPECIFIED, DELTA, CUMULATIVE)

**Resource Attribute Tables (6 tables)** - For promoted resource attributes:
- ❌ otel_resource_attrs_string, int, double, bool, bytes, other

**Scope Attribute Tables (6 tables)** - For promoted scope attributes:
- ❌ otel_scope_attrs_string, int, double, bool, bytes, other

**Span Events & Links (13 tables)** - Currently stored as JSONB, need proper tables:
- ❌ otel_span_events + 6 attribute tables (event_attrs_string, int, double, bool, bytes, other)
- ❌ otel_span_links + 6 attribute tables (link_attrs_string, int, double, bool, bytes, other)

**Metrics Tables (29 tables)** - Complete metrics support:
- ❌ otel_metrics_dim
- ❌ otel_metrics_data_points_number, histogram, exp_histogram, summary
- ❌ 24 metric data point attribute tables (4 DP types × 6 attr types)

**Table/Column COMMENT Statements** - Missing from many tables

**Total Missing: ~66 tables + COMMENT statements**

---

## IMMEDIATE ACTION required - Migration Update

**Task: Complete Migration 8316334b1935**

The migration is incomplete. Add to apps/api/alembic/versions/8316334b1935_create_otlp_schema.py:

1. **Reference tables** (after attribute_keys)
2. **Resource/scope attribute tables** (after otel_resources_dim/otel_scopes_dim)
3. **Update FK constraints** to reference the new reference tables
4. **Add missing COMMENT statements** on all tables/columns
5. **Span events/links tables** (if needed immediately, or defer to Phase 5)
6. **Metrics tables** (if needed immediately, or defer to Phase 5)

See "Task Details" section below for exact SQL.

---

## Task Breakdown for Completion

### PRIORITY 1: Fix Reference Tables (BLOCKING)

**Problem**: Migration creates FK references to tables that don't exist yet.

**Tasks**:
1. Add all 6 reference/lookup tables to migration 8316334b1935
2. Add seed data (INSERT statements) 
3. Update otel_logs_fact FK: severity_number → log_severity_numbers(severity_number)
4. Update otel_logs_fact FK: body_type_id → log_body_types(body_type_id)  
5. Update otel_spans_fact FK: kind → span_kinds(kind_id)
6. Update otel_spans_fact FK: status_code → status_codes(status_code_id)
7. Add COMMENT ON TABLE for each reference table

**SQL Location**: See "Reference Tables SQL" section below.

**Test**: `task deploy` succeeds, no FK constraint errors.

### PRIORITY 2: Add Resource/Scope Attribute Tables

**Problem**: ResourceManager has nowhere to store promoted resource/scope attributes.

**Tasks**:
1. Add 6 otel_resource_attrs_* tables (string, int, double, bool, bytes, other)
2. Add 6 otel_scope_attrs_* tables
3. Add indexes on (key_id, value)
4. Add COMMENT statements
5. Update ResourceManager to use these tables

**SQL Location**: See "Resource/Scope Attribute Tables SQL" section below.

**Test**: Verify resource attributes stored in typed columns, not just JSONB.

### PRIORITY 3: Add Missing COMMENT Statements

**Problem**: Schema undocumented, violates requirements.

**Tasks**:
1. Add COMMENT ON TABLE for all attribute tables
2. Add COMMENT ON COLUMN for time_nanos_fraction fields
3. Add COMMENT ON COLUMN for hash fields
4. Document promotion strategy in attribute table comments

**SQL Location**: See "COMMENT Statements SQL" section below.

**Test**: Run `\dt+ otel_*` in psql, verify all tables have comments.

### PRIORITY 4 (Optional): Span Events & Links Tables

**Current State**: Events/links stored as JSONB in spans_fact.

**Decision Needed**: Keep JSONB or create proper tables?

**If creating tables**:
1. Add otel_span_events table
2. Add 6 otel_span_event_attrs_* tables  
3. Add otel_span_links table
4. Add 6 otel_span_link_attrs_* tables
5. Update TracesStorage to use tables
6. Migrate existing JSONB data (if any)

**Trade-off**: JSONB simpler, proper tables enable attribute promotion and better queries.

### PRIORITY 5 (Deferred): Metrics Dimension Tables

**Current State**: Metrics stored somewhere (needs investigation).

**Required for full metrics support**:
1. otel_metrics_dim table
2. 4 data point tables (number, histogram, exp_histogram, summary)
3. 24 attribute tables (4 DP types × 6 attr types)
4. Update MetricsStorage class

**Test**: Full OTLP metrics ingestion working.

---

## SQL for Required Tasks

### Reference Tables SQL

Add this to `apps/api/alembic/versions/8316334b1935_create_otlp_schema.py` after attribute_keys table:

```python
    # Reference/Lookup Tables
    op.execute("""
        CREATE TABLE log_severity_numbers (
            severity_number SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        );
        COMMENT ON TABLE log_severity_numbers IS 'OTLP log severity levels (0-24) per OpenTelemetry specification';

        INSERT INTO log_severity_numbers (severity_number, name, description) VALUES
            (0, 'UNSPECIFIED', 'Unspecified severity'),
            (1, 'TRACE', 'Trace-level message (most verbose)'),
            (5, 'DEBUG', 'Debug-level message'),
            (9, 'INFO', 'Informational message'),
            (13, 'WARN', 'Warning message'),
            (17, 'ERROR', 'Error message'),
            (21, 'FATAL', 'Fatal error message (most severe)');

        CREATE TABLE log_body_types (
            body_type_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        );
        COMMENT ON TABLE log_body_types IS 'OTLP AnyValue types for log body field';

        INSERT INTO log_body_types (body_type_id, name, description) VALUES
            (0, 'EMPTY', 'Empty/null body'),
            (1, 'STRING', 'String body'),
            (2, 'INT', 'Integer body'),
            (3, 'DOUBLE', 'Double precision body'),
            (4, 'BOOL', 'Boolean body'),
            (5, 'BYTES', 'Bytes body'),
            (6, 'ARRAY', 'Array body'),
            (7, 'KVLIST', 'Key-value list body');

        CREATE TABLE span_kinds (
            kind_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        );
        COMMENT ON TABLE span_kinds IS 'OTLP span kinds per OpenTelemetry specification';

        INSERT INTO span_kinds (kind_id, name, description) VALUES
            (0, 'UNSPECIFIED', 'Unspecified span kind'),
            (1, 'INTERNAL', 'Internal operation within application'),
            (2, 'SERVER', 'Server-side handling of RPC or HTTP request'),
            (3, 'CLIENT', 'Client-side RPC or HTTP request'),
            (4, 'PRODUCER', 'Message producer (async operations)'),
            (5, 'CONSUMER', 'Message consumer (async operations)');

        CREATE TABLE status_codes (
            status_code_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        );
        COMMENT ON TABLE status_codes IS 'OTLP status codes per OpenTelemetry specification';

        INSERT INTO status_codes (status_code_id, name, description) VALUES
            (0, 'UNSET', 'Default status - operation not explicitly set'),
            (1, 'OK', 'Operation completed successfully'),
            (2, 'ERROR', 'Operation failed with error');

        CREATE TABLE metric_types (
            metric_type_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        );
        COMMENT ON TABLE metric_types IS 'OTLP metric data types';

        INSERT INTO metric_types (metric_type_id, name, description) VALUES
            (1, 'GAUGE', 'Point-in-time measurement (no aggregation)'),
            (2, 'SUM', 'Cumulative or delta sum aggregation'),
            (3, 'HISTOGRAM', 'Distribution with explicit bucket boundaries'),
            (4, 'EXP_HISTOGRAM', 'Distribution with exponential bucket boundaries'),
            (5, 'SUMMARY', 'Summary statistics with quantiles');

        CREATE TABLE aggregation_temporalities (
            temporality_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        );
        COMMENT ON TABLE aggregation_temporalities IS 'OTLP metric aggregation temporality';

        INSERT INTO aggregation_temporalities (temporality_id, name, description) VALUES
            (0, 'UNSPECIFIED', 'Unspecified temporality'),
            (1, 'DELTA', 'Change since last measurement interval'),
            (2, 'CUMULATIVE', 'Total accumulated since start');
    """)
```

### Resource/Scope Attribute Tables SQL

Add after otel_scopes_dim table:

```python
    # Resource Attribute Tables
    op.execute("""
        CREATE TABLE otel_resource_attrs_string (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        );
        CREATE INDEX idx_otel_resource_attrs_string_key_value ON otel_resource_attrs_string(key_id, value);
        COMMENT ON TABLE otel_resource_attrs_string IS 'Promoted string resource attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_resource_attrs_int (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        );
        CREATE INDEX idx_otel_resource_attrs_int_key_value ON otel_resource_attrs_int(key_id, value);
        COMMENT ON TABLE otel_resource_attrs_int IS 'Promoted integer resource attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_resource_attrs_double (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        );
        CREATE INDEX idx_otel_resource_attrs_double_key_value ON otel_resource_attrs_double(key_id, value);
        COMMENT ON TABLE otel_resource_attrs_double IS 'Promoted double resource attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_resource_attrs_bool (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        );
        CREATE INDEX idx_otel_resource_attrs_bool_key ON otel_resource_attrs_bool(key_id, value);
        COMMENT ON TABLE otel_resource_attrs_bool IS 'Promoted boolean resource attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_resource_attrs_bytes (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        );
        CREATE INDEX idx_otel_resource_attrs_bytes_key ON otel_resource_attrs_bytes(key_id);
        COMMENT ON TABLE otel_resource_attrs_bytes IS 'Promoted bytes resource attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_resource_attrs_other (
            resource_id BIGINT NOT NULL PRIMARY KEY REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            attributes JSONB NOT NULL
        );
        CREATE INDEX idx_otel_resource_attrs_other_gin ON otel_resource_attrs_other USING gin(attributes);
        COMMENT ON TABLE otel_resource_attrs_other IS 'JSONB catch-all for unpromoted resource attributes (complex types, unknown keys)';

        -- Scope Attribute Tables
        CREATE TABLE otel_scope_attrs_string (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        );
        CREATE INDEX idx_otel_scope_attrs_string_key_value ON otel_scope_attrs_string(key_id, value);
        COMMENT ON TABLE otel_scope_attrs_string IS 'Promoted string scope attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_scope_attrs_int (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        );
        CREATE INDEX idx_otel_scope_attrs_int_key_value ON otel_scope_attrs_int(key_id, value);
        COMMENT ON TABLE otel_scope_attrs_int IS 'Promoted integer scope attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_scope_attrs_double (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        );
        CREATE INDEX idx_otel_scope_attrs_double_key_value ON otel_scope_attrs_double(key_id, value);
        COMMENT ON TABLE otel_scope_attrs_double IS 'Promoted double scope attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_scope_attrs_bool (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        );
        CREATE INDEX idx_otel_scope_attrs_bool_key ON otel_scope_attrs_bool(key_id, value);
        COMMENT ON TABLE otel_scope_attrs_bool IS 'Promoted boolean scope attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_scope_attrs_bytes (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        );
        CREATE INDEX idx_otel_scope_attrs_bytes_key ON otel_scope_attrs_bytes(key_id);
        COMMENT ON TABLE otel_scope_attrs_bytes IS 'Promoted bytes scope attributes per attribute-promotion.yaml config';

        CREATE TABLE otel_scope_attrs_other (
            scope_id BIGINT NOT NULL PRIMARY KEY REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            attributes JSONB NOT NULL
        );
        CREATE INDEX idx_otel_scope_attrs_other_gin ON otel_scope_attrs_other USING gin(attributes);
        COMMENT ON TABLE otel_scope_attrs_other IS 'JSONB catch-all for unpromoted scope attributes (complex types, unknown keys)';
    """)
```

### Missing COMMENT Statements SQL

Add before views:

```python
    # Add missing COMMENT statements
    op.execute("""
        -- Log attribute table comments
        COMMENT ON TABLE otel_log_attrs_string IS 'Promoted string log attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_log_attrs_int IS 'Promoted integer log attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_log_attrs_double IS 'Promoted double log attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_log_attrs_bool IS 'Promoted boolean log attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_log_attrs_bytes IS 'Promoted bytes log attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_log_attrs_other IS 'JSONB catch-all for unpromoted log attributes (complex types)';

        -- Span attribute table comments
        COMMENT ON TABLE otel_span_attrs_string IS 'Promoted string span attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_span_attrs_int IS 'Promoted integer span attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_span_attrs_double IS 'Promoted double span attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_span_attrs_bool IS 'Promoted boolean span attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_span_attrs_bytes IS 'Promoted bytes span attributes per attribute-promotion.yaml';
        COMMENT ON TABLE otel_span_attrs_other IS 'JSONB catch-all for unpromoted span attributes (complex types)';

        -- Column comments for timestamp nanos_fraction fields
        COMMENT ON COLUMN otel_logs_fact.time_nanos_fraction IS 'Remaining nanoseconds (0-999) beyond microsecond precision in time field';
        COMMENT ON COLUMN otel_logs_fact.observed_time_nanos_fraction IS 'Remaining nanoseconds (0-999) beyond microsecond precision in observed_time field';
        COMMENT ON COLUMN otel_spans_fact.start_time_nanos_fraction IS 'Remaining nanoseconds (0-999) beyond microsecond precision in start_time field';
        COMMENT ON COLUMN otel_spans_fact.end_time_nanos_fraction IS 'Remaining nanoseconds (0-999) beyond microsecond precision in end_time field';

        -- Hash field comments
        COMMENT ON COLUMN otel_resources_dim.resource_hash IS 'SHA-256 hash of sorted resource attributes for deduplication';
        COMMENT ON COLUMN otel_scopes_dim.scope_hash IS 'SHA-256 hash of scope identity (name+version+schema_url) for deduplication';
    """)
```

---

## Architecture Principles

### 1. DRY (Don't Repeat Yourself)

**⚠️ CRITICAL**: Keep code DRY throughout implementation. Extract common patterns immediately.

**Shared Components**:
- **Resource/Scope Deduplication**: Single implementation for all signal types
- **Attribute Promotion**: Generic promotion engine with signal-specific configs
- **Attribute Key Registry**: Shared across all signals
- **Base Storage Classes**: Abstract storage operations common to all signals
- **View Query Builders**: Shared attribute aggregation logic
- **Hash Calculation**: Reusable hash functions for all dimensions

**Code Organization**:
```
app/storage/
  ├── base.py              # Abstract base classes
  ├── resource_manager.py  # Resource/scope dimension management
  ├── attribute_manager.py # Attribute promotion & storage
  ├── logs_storage.py      # Logs-specific storage
  ├── traces_storage.py    # Traces-specific storage
  └── metrics_storage.py   # Metrics-specific storage
```

**DRY Checklist** (review before each PR):
- [ ] No duplicate hash calculation logic
- [ ] No duplicate attribute promotion logic
- [ ] No duplicate view query patterns
- [ ] No duplicate test fixtures
- [ ] Shared utilities in common modules

### 2. Testing & Deployment

**⚠️ MANDATORY**: Test every change with full deployment cycle.

**Testing Requirements**:
- Unit tests for ALL new functions/classes
- Integration tests for storage operations
- API endpoint tests for new routes
- Test attribute promotion edge cases
- Test hash collision scenarios

**Deployment Validation**:
```bash
# After EVERY significant change:
task deploy

# Verify migration success:
kubectl -n ollyscale logs -l job-name=ollyscale-migration --tail=50

# Check receiver health (OTLP ingestion):
kubectl -n ollyscale logs -l app.kubernetes.io/component=ollyscale-receiver --tail=100

# Check API health:
kubectl -n ollyscale logs -l app.kubernetes.io/component=ollyscale-api --tail=100
```

**Test Checklist** (complete before marking task done):
- [ ] Unit tests added/updated
- [ ] Integration tests pass locally
- [ ] `task deploy` succeeds
- [ ] Migration logs show success
- [ ] Receiver logs show successful OTLP ingestion (no errors)
- [ ] API endpoints return expected data
- [ ] No regressions in existing tests

### 3. SQL Views for Abstraction

Views simplify queries by pre-joining attribute tables with fact tables, providing a denormalized view of the data.

### 4. API Structure

**New API Structure**:

**Traces**:
- `GET /api/traces` - List distinct traces (trace-level aggregation)
- `GET /api/traces/{trace_id}/spans` - Get all spans for a trace

**Logs**:
- `GET /api/logs` - Search logs with attribute filters
- `GET /api/logs/trace/{trace_id}` - Get all logs correlated to a trace (deprecated, use /spans)
- `GET /api/logs/trace/{trace_id}/spans` - Get logs grouped by span for entire trace
- `GET /api/logs/trace/{trace_id}/span/{span_id}` - Get logs for specific span

**Metrics**:
- `GET /api/metrics/series` - Query metric time series
- `GET /api/metrics/labels` - Get metric label values

---

## Schema Structure

See [Ollyscale Data Model](../otel-ollyscale-data-model.md) for complete schema documentation.

### Timestamp Storage Pattern

**CRITICAL REQUIREMENT**: All timestamps MUST use the following pattern for full nanosecond precision:

- `time` TIMESTAMP WITH TIME ZONE NOT NULL - Stores microsecond precision (PostgreSQL native)
- `time_nanos_fraction` SMALLINT NOT NULL DEFAULT 0 - Stores remaining 0-999 nanoseconds
- CHECK constraint: `time_nanos_fraction >= 0 AND time_nanos_fraction < 1000`

**Applies to:**
- Logs: `time`, `observed_time` (both with nanos_fraction)
- Spans: `start_time`, `end_time` (both with nanos_fraction)
- Span Events: `time` (with nanos_fraction)
- Metrics: `time`, `start_time` (both with nanos_fraction, start_time nullable for gauges)

**Conversion Logic:**
```python
# unix_nano → (timestamp, nanos_fraction)
unix_micros = unix_nano // 1000
nanos_fraction = unix_nano % 1000
timestamp = datetime.fromtimestamp(unix_micros / 1_000_000, tz=UTC)

# (timestamp, nanos_fraction) → unix_nano
unix_micros = int(timestamp.timestamp() * 1_000_000)
unix_nano = (unix_micros * 1000) + nanos_fraction
```

### Table Comments Requirement

**ALL tables and critical columns MUST have COMMENT statements** documenting:
- Purpose and relationship to OTLP specification
- Deduplication strategy (for dimension tables)
- Attribute promotion strategy (for attribute tables)
- Performance characteristics and index usage

### Dimension Tables (Shared)

#### `attribute_keys`
Central registry for all attribute key names across all signals. See data model doc for complete schema.

**Purpose**: Deduplicate attribute names, reduce storage, enable efficient joins.

#### `otel_resources_dim`
Resource identity with hash-based deduplication. See data model doc for schema.

**Key Design Decisions**:
- Hash includes ALL attributes for true deduplication (SHA-256)
- `service.name` and `service.namespace` extracted for fast service filtering
- `first_seen`/`last_seen` track resource lifecycle (both TIMESTAMPTZ)
- Requires unique index on `resource_hash` and composite index on service fields

#### `otel_scopes_dim`
Instrumentation library/scope identity. See data model doc for schema.

**Key Design Decisions**:
- Hash-based deduplication like resources
- Name and version tracked separately for filtering
- Requires unique index on `scope_hash` and regular index on `name`

### Resource Attribute Tables (6 tables)

**Required tables:**
- `otel_resource_attrs_string` - TEXT values with value index
- `otel_resource_attrs_int` - BIGINT values with value index  
- `otel_resource_attrs_double` - DOUBLE PRECISION values with value index
- `otel_resource_attrs_bool` - BOOLEAN values with value index
- `otel_resource_attrs_bytes` - BYTEA values (no value index - low cardinality expected)
- `otel_resource_attrs_other` - JSONB catch-all with GIN index

**All tables require:**
- Composite PK on (resource_id, key_id)
- FK to otel_resources_dim(resource_id) with ON DELETE CASCADE
- FK to attribute_keys(key_id)
- Index on (key_id, value) for typed tables (except bytes/other)
- COMMENT documenting promotion strategy

### Scope Attribute Tables (6 tables)

Identical structure to resource attributes:
- `otel_scope_attrs_string, int, double, bool, bytes, other`
- Same FK, PK, and index requirements as resource attrs
- Reference otel_scopes_dim instead of otel_resources_dim

---

## Signal-Specific Schemas

### 1. Logs

#### Fact Table: `otel_logs_fact`

**Requirements:**
- Primary key: log_id (BIGSERIAL)
- Foreign keys: resource_id (required), scope_id (optional)
- Timestamp fields: time + time_nanos_fraction, observed_time + observed_time_nanos_fraction
- Severity: severity_number (FK to reference table), severity_text
- Body: body_type_id (FK), body (JSONB)
- Trace correlation: trace_id, span_id_hex, trace_flags
- Metadata: dropped_attributes_count, flags
- Indexes: (time, time_nanos_fraction DESC), resource_id, severity_number, trace_id
- COMMENT: Document purpose and OTLP spec complianceReference/Lookup Tables (6 tables)

**Required tables with seed data:**
- `log_severity_numbers` - OTLP severity levels (0-24)
- `log_body_types` - OTLP body types (EMPTY, STRING, INT, DOUBLE, BOOL, BYTES, ARRAY, KVLIST)
- `span_kinds` - OTLP span kinds (UNSPECIFIED, INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
- `status_codes` - OTLP status codes (UNSET, OK, ERROR)
- `metric_types` - OTLP metric types (GAUGE, SUM, HISTOGRAM, EXP_HISTOGRAM, SUMMARY)
- `aggregation_temporalities` - OTLP temporalities (UNSPECIFIED, DELTA, CUMULATIVE)

**Requirements:**
- All tables must have name and description columns
- PK on numeric ID matching OTLP specification values
- Seed data inserted in migration (not separate data files)
- COMMENT on each table documenting OTLP specification compliance

### 1. Logs

#### Fact Table: `otel_logs_fact`

See data model doc for complete schema.
See data model doc for complete schema.

**Key Requirements**:
- Timestamp columns use timestamp+nanos pattern (4 columns total: start_time, start_time_nanos_fraction, end_time, end_time_nanos_fraction)
- FK to span_kinds and status_codes (both nullable)
- UNIQUE index on (trace_id, span_id_hex) - critical for OTLP compliance
- Indexes on: trace_id, resource_id, (start_time, start_time_nanos_fraction DESC)
- Partial index on parent_span_id_hex WHERE NOT NULL (for child span lookups)
- `attributes_other` JSONB column for unpromoted attributes with GIN index
- NO events/links as JSONB arrays - these go in separate tables per OTLP spec

#### Span Events Table (1 table + 6 attribute tables = 7 tables total)

**otel_span_events:**
- FK to spans with ON DELETE CASCADE
- Timestamp with nanos pattern (time, time_nanos_fraction)
- Event name and dropped count

**otel_span_event_attrs_{string,int,double,bool,bytes,other}:**
- FK to otel_span_events(event_id) with ON DELETE CASCADE
- Same structure as other attribute tables

#### Span Links Table (1 table + 6 attribute tables = 7 tables total)

**otel_span_links:**
- FK to spans with ON DELETE CASCADE  
- linked_trace_id and linked_span_id_hex for correlation
- trace_state for W3C trace context

**otel_span_link_attrs_{string,int,double,bool,bytes,other}:**
- FK to otel_span_links(link_id) with ON DELETE CASCADE
- Same structure as other attribute tables

#### Span Attribute Tables (6 tables)

**Required tables:**
- `otel_span_attrs_string, int, double, bool, bytes, other`
- FK to otel_spans_fact(span_id) with ON DELETE CASCADEemporalities(temporality_id),
    is_monotonic BOOLEAN,
    description TEXT,
    schema_url TEXT,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL
);

**Indexes:**
- UNIQUE index on metric_hash
- Index on metric_identity_hash (for grouping variants)
- Index on name (for lookups)

**Key Design:**
- Two hashes: one with description (full identity), one without (groups variants)
- Enables metric variants with different descriptions

#### Fact Tables: `otel_metrics_data_points_*`

Separate tables for each metric type for optimal storage:

**Number Data Points (Gauge & Sum)** - Table: `otel_metrics_data_points_number`
- Fields: data_point_id (PK), metric_id (FK), resource_id (FK), scope_id (FK)
- Timestamps: start_time + start_time_nanos_fraction (NULL for gauges), time + time_nanos_fraction
- Values: value_int (BIGINT), value_double (DOUBLE PRECISION) - exactly one must be non-NULL
- Additional: flags, exemplars (JSONB)
- Constraint: CHECK that exactly one of value_int or value_double is non-NULL

**Histogram Data Points** - Table: `otel_metrics_data_points_histogram`
- Fields: data_point_id (PK), metric_id (FK), resource_id (FK), scope_id (FK)
- Timestamps: start_time + start_time_nanos_fraction, time + time_nanos_fraction
- Statistics: count, sum, min, max
- Buckets: explicit_bounds (array), bucket_counts (array)
- Additional: flags, exemplars (JSONB)

**ExponentialHistogram Data Points** - Table: `otel_metrics_data_points_exp_histogram`
- Fields: data_point_id (PK), metric_id (FK), resource_id (FK), scope_id (FK)
- Timestamps: start_time + start_time_nanos_fraction, time + time_nanos_fraction
- Statistics: count, sum, min, max
- Exponential buckets: scale, zero_count, positive_offset, positive_bucket_counts, negative_offset, negative_bucket_counts
- Additional: flags, exemplars (JSONB)

**Summary Data Points** - Table: `otel_metrics_data_points_summary`
- Fields: data_point_id (PK), metric_id (FK), resource_id (FK), scope_id (FK)
- Timestamps: start_time + start_time_nanos_fraction, time + time_nanos_fraction
- Statistics: count, sum, quantile_values (JSONB array of {quantile, value})
- Additional: flags
```

---

## Attribute Promotion Configuration

See implementation plan for attribute promotion engine details.

**Requirements:**
- Base configuration promotes well-known OTLP semantic conventions
- Admin overrides allow deployment-specific customization
- Dropped attributes prevent storage (security/cardinality control)
- All configuration version-controlled (git/ConfigMap)
  string:
    - log.level
    - log.logger
    - log.file.name
    - log.file.path
    - error.type
    - exception.type
    - exception.message

  int:
    - log.line
    - error.code
    - http.status_code

spans:
  string:
    - http.method
    - http.route
    - http.url
    - http.target
    - http.host
    - http.scheme
    - db.system
    - db.name
    - db.operation
    - db.statement
    - messaging.system
    - messaging.destination
    - rpc.system
    - rpc.service
    - rpc.method
    - error.type
    - exception.type
    # AI/GenAI semantic conventions
    - gen_ai.system
    - gen_ai.request.model
    - gen_ai.response.model
    - llm.system
    - llm.request.type
    - http.status_code
    - rpc.grpc.status_code

  int:
    - gen_ai.usage.input_tokens
    - gen_ai.usage.output_tokens
    - gen_ai.usage.total_tokens
    - http.request.size
    - http.response.size

  double:
    - gen_ai.usage.cost

metrics:
  # For metric data points
  string:
    - endpoint
    - method
    - status_code
    - operation
    - job
    - instance
```

### Admin Override Configuration

Admins extend base configuration via ConfigMap mounted at `/config/attribute-overrides.yaml`.

**Kubernetes ConfigMap**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollyscale-attribute-overrides
  namespace: ollyscale
data:
  attribute-overrides.yaml: |
    # Admin overrides - merged with base config
    # These are deployment-specific customizations

    promote:
      # Add custom promoted attributes per signal type
      resource:
        string:
          - custom.datacenter
          - custom.region

      spans:
        string:
          - custom.request_id
          - custom.user_id
          - app.feature_flag
        int:
          - custom.retry_count

      logs:
        string:
          - app.version
          - app.component

    drop:
      # Drop sensitive or high-cardinality attributes
      logs:
        - sensitive.password
        - sensitive.api_key
        - internal.debug_data

      spans:
        - temp.cache_data
        - internal.testing_flag

      resource:
        - internal.build_hash  # High cardinality
```

**Deployment Configuration** (Helm values.yaml):
```yaml
receiver:
  attributeOverrides:
    enabled: true
    promote:
      spans:
        string:
          - custom.request_id
          - custom.user_id
    drop:
      logs:
        - sensitive.password
```

**File Mount** (in Deployment):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollyscale-receiver
spec:
  template:
    spec:
      containers:
      - name: receiver
        volumeMounts:
        - name: attribute-overrides
          mountPath: /config/attribute-overrides.yaml
          subPath: attribute-overrides.yaml
          readOnly: true
      volumes:
      - name: attribute-overrides
        configMap:
          name: ollyscale-attribute-overrides
          optional: true  # Optional - falls back to base config only
```

### Promotion Engine Implementation Requirements

**AttributePromotionConfig Class:**
- Load base configuration from YAML file (enforced semantic conventions)
- Load optional admin overrides from separate YAML file (deployment-specific)
- Merge base and override configs using set union operations
- Maintain separate promotion sets per signal type (resource, scope, logs, spans, metrics)
- Maintain separate drop lists per signal type (admin-only, not in base config)
- Build type-specific lookup sets for fast O(1) membership checks
- Provide `is_promoted(signal, key, value_type) -> bool` method
- Provide `should_drop(signal, key) -> bool` method

**AttributeManager Class:**
- Initialize with AttributePromotionConfig and database session
- Maintain in-memory cache of attribute key_id lookups
- Provide `get_or_create_key_id(key) -> int` with INSERT...ON CONFLICT logic
- Provide `store_attributes(signal, parent_id, parent_table, attributes)` method
- Route promoted attributes to typed columns in appropriate tables
- Route unpromoted attributes to JSONB catch-all column
- Extract OTLP AnyValue types (string_value, int_value, double_value, bool_value, bytes_value, array_value, kvlist_value)
- Handle complex types (arrays, kvlists) by storing in JSONB
        else:
            return ('other', value_obj)
```

---

## Resource/Scope Management

### Deduplication Strategy Requirements

**Hash Calculation Algorithm:**
- Use SHA-256 algorithm for resource/scope attribute hashing
- Sort attributes by key for stable hash calculation
- Use canonical JSON representation (sorted keys, consistent separators)
- Encoding: UTF-8 before hashing

**ResourceManager Class:**
- Initialize with db_session and attr_manager
- Maintain in-memory caches: resource_cache {hash: resource_id}, scope_cache {hash: scope_id}
- Method: `get_or_create_resource(resource: dict) -> int`
  - Calculate hash from attributes
  - Check cache first
  - SELECT by hash if not cached
  - INSERT if not exists (ON CONFLICT DO UPDATE pattern)
  - Extract service.name and service.namespace for denormalized columns
  - Store resource attributes using AttributeManager (signal='resource')
  - Return resource_id
- Method: `get_or_create_scope(scope: dict, resource_id: int) -> int`
  - Similar logic for scope dimensions
  - Store scope attributes using AttributeManager (signal='scope')
  - Return scope_id
        resource_hash = calculate_resource_hash(attributes)

        # Check cache
        if resource_hash in self.resource_cache:
            resource_id = self.resource_cache[resource_hash]
            # Update last_seen
            await self.db.execute(
                "UPDATE otel_resources_dim SET last_seen = NOW() WHERE resource_id = $1",
                resource_id
            )
            return resource_id

        # Extract promoted fields
        service_name = self._extract_attr(attributes, 'service.name')
        service_namespace = self._extract_attr(attributes, 'service.namespace')

        # Try SELECT first
        result = await self.db.execute(
            "SELECT resource_id FROM otel_resources_dim WHERE resource_hash = $1",
            resource_hash
        )

        if result:
            resource_id = result[0]['resource_id']
            await self.db.execute(
                "UPDATE otel_resources_dim SET last_seen = NOW() WHERE resource_id = $1",
                resource_id
            )
            self.resource_cache[resource_hash] = resource_id
            return resource_id

        # INSERT new resource
        resource_id = await self.db.execute(
            "INSERT INTO otel_resources_dim "
            "(resource_hash, service_name, service_namespace, schema_url, "
            "first_seen, last_seen, dropped_attributes_count) "
            "VALUES ($1, $2, $3, $4, NOW(), NOW(), $5) "
            "RETURNING resource_id",
            resource_hash, service_name, service_namespace, schema_url, dropped_count
        )

        # Store attributes
        await self.attr_manager.store_attributes(
            signal='resource',
            parent_id=resource_id,
            parent_table='otel_resource_attrs',
            attributes=attributes
        )

        self.resource_cache[resource_hash] = resource_id
        return resource_id

    async def get_or_create_scope(self, scope: dict | None) -> int | None:
        """Get or create scope, returns scope_id or None."""
        if not scope:
            return None

        # Similar implementation to resource
        # ...

    def _extract_attr(self, attributes: list[dict], key: str) -> str | None:
        """Extract attribute value by key."""
        for attr in attributes:
            if attr['key'] == key:
                value = attr.get('value', {})
                return value.get('string_value')
        return None
```

## SQL Views for Query Simplification Requirements

All views must join fact tables with typed attribute tables and JSONB catch-all columns to provide unified query interface.

### Logs View: `v_otel_logs_enriched`

**Requirements:**
- Select all log fact columns (log_id, timestamps, severity, body, trace correlation)
- Join resource dimension (service_name, service_namespace, resource_id)
- Join scope dimension (scope_id, name, version)
- Aggregate ALL attribute types into single JSONB column:
  - Union all typed attribute tables (string, int, double, bool, bytes)
  - JOIN attribute_keys to get key names
  - Use jsonb_object_agg to build {key: value} objects
  - Union with JSONB catch-all column (otel_log_attrs_other)
  - Return empty JSONB {} if no attributes
- Provide simplified query interface for application code

### Traces View: `v_otel_traces` (Trace-Level Aggregation)

**Requirements:**
- Group by trace_id
- Calculate trace-level metrics:
  - start_time_unix_nano (MIN of all span start times)
  - end_time_unix_nano (MAX of all span end times)
  - duration_nanos (end - start)
  - span_count (COUNT of spans)
  - error_count (COUNT WHERE status_code = ERROR)
- Extract root span information:
  - root_span_name (name of span with NULL parent)
  - service_name, service_namespace (from root span's resource)
- Enable efficient trace browsing without loading all span details

### Spans View: `v_otel_spans_enriched`

**Requirements:**
- Select all span fact columns (span_id, trace_id, name, timestamps, status)
- Calculate duration_nanos (end_time - start_time)
- Join span_kinds and status_codes reference tables for names
- Join resource dimension (service_name, service_namespace)
- Join scope dimension (scope_name, scope_version)
- Aggregate span attributes (all typed + JSONB catch-all)
- Aggregate span events as JSONB array:
  - Each event: {name, time_unix_nano, attributes{}}
  - Event attributes aggregated from all typed tables + JSONB
- Aggregate span links as JSONB array:
  - Each link: {trace_id, span_id, trace_state, attributes{}}
  - Link attributes aggregated from all typed tables + JSONB


**Benefits of Views**:
- Simplified application queries
- Backward compatibility layer
- Performance: PostgreSQL can optimize view queries
- Single source of truth for attribute aggregation logic

---

## REST API Refactoring

### Current Problems
- `GET /api/traces` returns all spans (inefficient, couples trace browsing with span details)
- No way to get just trace-level info without loading all spans
- Logs/metrics APIs lack attribute filtering

### New API Design

#### Traces

**List Traces** (trace-level aggregation):
```
GET /api/traces?start_time=<unix_nano>&end_time=<unix_nano>&service=<name>&min_duration=<nanos>

Query Parameters:
- start_time, end_time: Time range filter
- service: Filter by service name
- status: error, ok (filter by trace status)
- min_duration, max_duration: Duration filters
- limit, offset: Pagination

Response:
{
  "traces": [
    {
      "trace_id": "abc123...",
      "start_time_unix_nano": 1234567890,
      "end_time_unix_nano": 1234567900,
      "duration_nanos": 100000000,
      "span_count": 15,
      "error_count": 0,
      "root_span_name": "GET /api/users",
      "service_name": "api-server",
      "service_namespace": "production"
    }
  ],
  "total": 142,
  "has_more": true
}
```

**Get Trace Spans** (with semantic convention filters):
```
GET /api/traces/{trace_id}/spans?semantic_type=<type>

Path Parameters:
- trace_id: Trace ID

Query Parameters:
- semantic_type: Filter spans by semantic convention (optional)
  - ai_agent: Spans with gen_ai.* attributes (AI/LLM operations)
  - http: Spans with http.* attributes (HTTP requests)
  - db: Spans with db.* attributes (Database operations)
  - messaging: Spans with messaging.* attributes (Message queue operations)
  - rpc: Spans with rpc.* attributes (RPC/gRPC calls)
- attr.<key>: Filter by specific attribute (e.g., attr.gen_ai.system=openai)
- kind: Filter by span kind (server, client, internal, producer, consumer)

Response:
{
  "trace_id": "abc123...",
  "spans": [
    {
      "span_id": "def456",
      "parent_span_id": null,
      "name": "GET /api/users",
      "kind": "server",
      "start_time_unix_nano": 1234567890,
      "duration_nanos": 50000000,
      "status": "ok",
      "attributes": {
        "http.method": "GET",
        "http.status_code": 200
      },
      "semantic_type": "http"  // Added by server for UI hint
    },
    {
      "span_id": "ghi789",
      "parent_span_id": "def456",
      "name": "chat completion",
      "kind": "client",
      "start_time_unix_nano": 1234567895,
      "duration_nanos": 45000000,
      "status": "ok",
      "attributes": {
        "gen_ai.system": "openai",
        "gen_ai.request.model": "gpt-4",
        "gen_ai.usage.input_tokens": 150
      },
      "semantic_type": "ai_agent"  // UI uses this for specialized rendering
    }
  ]
}
```

**Design Rationale**:
- **Generic API**: No special endpoints for AI agents, DB calls, HTTP - one unified API
- **Semantic Type Detection**: Server detects semantic convention based on attribute prefixes
- **UI Presentation**: UI decides how to render based on `semantic_type` field
- **Extensibility**: Easy to add new semantic types (faas, k8s, aws, etc.) without API changes
- **Backward Compatible**: Existing AI agent UI code works with new generic API

#### Logs

**Search Logs** (with attribute filters):
```
GET /api/logs?start_time=<unix_nano>&end_time=<unix_nano>&severity=<num>&attr.key=value

Query Parameters:
- start_time, end_time: Time range
- severity: Minimum severity number
- service: Filter by service name
- trace_id: Filter by trace correlation (deprecated, use /api/logs/trace/{trace_id})
- attr.<key>: Filter by attribute (e.g., attr.http.status_code=500)
- limit, offset: Pagination

Response:
{
  "logs": [
    {
      "log_id": 123,
      "time_unix_nano": 1234567890,
      "severity_number": 17,
      "severity_text": "ERROR",
      "body": "Failed to connect to database",
      "service_name": "api-server",
      "attributes": {
        "error.type": "connection_error",
        "db.name": "users"
      },
      "trace_id": "abc123...",
      "span_id": "def456"
    }
  ],
  "total": 42,
  "has_more": false
}
```

**Get Logs for All Spans in Trace**:
```
GET /api/logs/trace/{trace_id}/spans?limit=1000

Path Parameters:
- trace_id: Trace ID to get logs for

Query Parameters:
- limit: Max logs to return (default 1000)

Response:
{
  "trace_id": "abc123...",
  "spans": [
    {
      "span_id": "def456",
      "span_name": "GET /api/users",
      "log_count": 5,
      "logs": [
        {
          "log_id": 123,
          "time_unix_nano": 1234567890,
          "severity_number": 17,
          "severity_text": "ERROR",
          "body": "Request failed",
          "service_name": "api-server",
          "attributes": {...}
        }
      ]
    },
    {
      "span_id": "ghi789",
      "span_name": "query database",
      "log_count": 2,
      "logs": [...]
    }
  ],
  "total_logs": 15,
  "total_spans_with_logs": 8
}
```

**Get Logs for Specific Span**:
```
GET /api/logs/trace/{trace_id}/span/{span_id}

Path Parameters:
- trace_id: Trace ID
- span_id: Span ID (hex format)

Response:
{
  "trace_id": "abc123...",
  "span_id": "def456",
  "logs": [
    {
      "log_id": 124,
      "time_unix_nano": 1234567891,
      "severity_number": 9,
      "severity_text": "INFO",
      "body": "Processing request",
      "service_name": "api-server",
      "attributes": {...}
    }
  ],
  "total": 3
}
```

**Use Cases**:
- APM workflows: `/api/logs/trace/{trace_id}/spans` - View all logs grouped by span in trace timeline
- Debug specific span: `/api/logs/trace/{trace_id}/span/{span_id}` - See logs emitted during span execution
- Root cause analysis: Trace errors across services via correlated logs

#### Metrics

**Query Metrics**:
```
GET /api/metrics/series?name=<metric_name>&start_time=<unix_nano>&end_time=<unix_nano>

Query Parameters:
- name: Metric name
- start_time, end_time: Time range
- service: Filter by service
- aggregation: avg, sum, min, max (server-side aggregation)
- group_by: Attribute key to group by
- attr.<key>: Filter by label

Response:
{
  "metric_name": "http.server.request.duration",
  "unit": "ms",
  "metric_type": "histogram",
  "series": [
    {
      "resource": {"service.name": "api"},
      "attributes": {"http.method": "GET", "http.route": "/api/users"},
      "data_points": [
        {
          "time_unix_nano": 1234567890,
          "count": 142,
          "sum": 5280.5,
          "buckets": [...]
        }
      ]
    }
  ]
}
```

**Get Metric Labels**:
```
GET /api/metrics/{metric_name}/labels?attribute=<key>

Response:
{
  "metric_name": "http.server.request.duration",
  "attribute": "http.method",
  "values": ["GET", "POST", "PUT", "DELETE"]
}
```

### API Router Organization

**Router Structure:**
- `app/routers/traces.py` - Trace-level operations + log correlation
- `app/routers/spans.py` - Span-level operations  
- `app/routers/logs.py` - Log search, retrieval, and trace/span correlation
- `app/routers/metrics.py` - Metric queries
- `app/routers/ingest.py` - OTLP ingestion (unchanged)

---

## Storage Layer Refactoring

### Base Classes Requirements

**SignalStorage Abstract Base Class:**
- Initialize with db_session, resource_mgr, attr_mgr, config
- Abstract method: `store(otlp_data: dict) -> int` - Store OTLP data, return count
- Abstract method: `search(filters: dict) -> list[dict]` - Search with filters
- Provides common initialization pattern for all signal-specific storage classes

**SemanticConventionDetector Class:**
- Shared utility for detecting semantic convention types from attributes
- Maintain dictionary of semantic type prefixes:
  - ai_agent: gen_ai., llm.
  - http: http., url.
  - db: db.
  - messaging: messaging.
  - rpc: rpc.
  - faas: faas.
  - aws: aws.
  - gcp: gcp.
  - azure: az.
- Class method: `detect_type(attributes: dict) -> str | None`
- Returns semantic type name or None if no match
- Used by API layer to add presentation hints for UI

### Implementation Structure Requirements

**LogsStorage Class (extends SignalStorage):**
- Implement `store(resource_logs: list[dict]) -> int` method
- For each resource_logs entry:
  - Get or create resource using ResourceManager
  - For each scope_logs entry:
    - Get or create scope using ResourceManager  
    - For each log_records entry:
      - Insert log fact row with all OTLP fields
      - Store attributes using AttributeManager (signal='logs', parent_table='otel_log_attrs')
      - Handle body type mapping
      - Handle trace/span correlation fields
- Implement `search(filters: dict) -> list[dict]` method
  - Query v_otel_logs_enriched view
  - Apply attribute filters using JSONB operators
  - Support time range, severity, service name filters

**TracesStorage Class (extends SignalStorage):**
- Implement `store(resource_spans: list[dict]) -> int` method
- For each resource_spans entry:
  - Get or create resource using ResourceManager
  - For each scope_spans entry:
    - Get or create scope using ResourceManager
    - For each spans entry:
      - Insert span fact row
      - Store span attributes using AttributeManager
      - Store span events (with event attributes)
      - Store span links (with link attributes)
- Implement `search(filters: dict) -> list[dict]` method
  - Query v_otel_spans_enriched view
  - Apply semantic_type filter if present (attribute prefix matching)
  - Enrich results with semantic_type hint using SemanticConventionDetector
  - Support time range, service name, trace_id filters

---

## Implementation Phases

### Phase 1: Foundation (Week 1) ✅ COMPLETE
**Commit Strategy**: Single squashed commit per phase for clean history

- [x] Create `config/attribute-promotion.yaml` (base configuration)
- [x] Create ConfigMap template for `attribute-overrides.yaml` in Helm chart
- [x] Implement `AttributePromotionConfig` class with file-based override merging
- [x] **Unit tests**: Config loading, YAML override merging, drop list, file not found handling (12 tests)
- [x] Implement `AttributeManager` class (DRY: shared across all signals)
- [x] **Unit tests**: Attribute promotion, drop filtering, key caching, type extraction (18 tests)
- [x] Implement `ResourceManager` class (DRY: shared hash/dedup logic)
- [x] **Unit tests**: Hash calculation consistency, deduplication, cache behavior (18 tests)
- [x] Update Helm chart values.yaml with attribute override examples
- [x] **Deploy**: task deploy - verified all pods running, migrations complete
- [x] **Testing**: 48 tests passing (12 config + 18 attribute + 18 resource manager)
- [x] **Commit**: Squashed commit with Phase 1 deliverables
- [x] **Deploy**: `task deploy` - verify no regressions (193 tests passing, all pods running)
- [x] **Code review**: DRY compliance verified

**Deliverables**: 48 new tests, 3 manager classes, 2 config files, comprehensive plan document
**Next**: Squash commits, then proceed to Phase 2

### Phase 2: Logs (Week 2) ✅ COMPLETE
**Commit Strategy**: Single commit for entire phase upon completion
- [x] Complete `LogsStorage` implementation
- [x] **Unit tests**: Log fact insertion, attribute storage (17 tests)
- [x] Create SQL views for logs (`v_otel_logs_enriched`)
- [x] **Test views**: Query correctness, attribute aggregation
- [x] Implement logs API: `/api/logs` with attribute filters
- [x] Add trace correlation APIs: `/api/logs/trace/{trace_id}/spans` and `/api/logs/trace/{trace_id}/span/{span_id}`
- [x] **Unit tests**: API endpoint responses, filter parsing, span grouping logic
- [x] **Integration tests**: End-to-end log ingestion → query
- [x] **Deploy**: `task deploy` - verify logs flow works
- [x] **Validation**: Check migration logs, test API endpoints

### Phase 3: Traces (Week 3) ✅ COMPLETE
**Commit Strategy**: Single commit for entire phase upon completion

- [x] Implement `TracesStorage` (DRY: reuse ResourceManager, AttributeManager)
- [x] **Unit tests**: Span fact insertion, event/link storage (18 tests)
- [x] Implement `SpansStorage` for span details
- [x] **Unit tests**: Span retrieval, parent-child relationships
- [x] Create views: `v_otel_traces`, `v_otel_spans_enriched`
- [x] **Test views**: Trace aggregation, span joins, event/link inclusion
- [x] Implement API: `/api/traces` (list) and `/api/traces/{trace_id}/spans` (details)
- [x] **Unit tests**: API responses, trace timeline ordering
- [x] **Integration tests**: Trace ingestion → query → span retrieval
- [x] **Deploy**: `task deploy` - verify traces work
- [x] **Validation**: Test trace queries, check span parent-child relationships

### Phase 4: Metrics (Week 4) ✅ COMPLETE
**Commit Strategy**: Single commit for entire phase upon completion

- [x] Implement `MetricsStorage` for all types (DRY: shared metric dimension logic)
- [x] **Unit tests**: Metric hash calculation, data point insertion per type (8 tests)
- [x] Create views: `v_otel_metrics_enriched` (unified view of all metric types)
- [x] **Test views**: Metric queries, label aggregation
- [x] Implement metrics API: `/api/metrics/search`, `/api/metrics/{name}/labels`
- [x] **Unit tests**: API responses, aggregation correctness
- [ ] **Integration tests**: Metric ingestion → query → label exploration (NEXT)
- [x] **Deploy**: `task deploy` - verify metrics work
- [x] **Validation**: Test all metric types (gauge, sum, histogram, exp_histogram, summary)

### Phase 5: Cleanup & Optimizations (Week 5) 🔄 IN PROGRESS
**Commit Strategy**: Single commit for entire phase upon completion
**NOTE**: Remove v1/v2 split and old code

**Step 1: Router Simplification** ✅ COMPLETE
- [x] Rename `logs_v2.py` → `logs.py`
- [x] Rename `traces_v2.py` → `traces.py`
- [x] Rename `metrics_v2.py` → `metrics.py`
- [x] Remove `/v2` prefix from router paths
- [x] Update `app/main.py` to use new router names
- [x] Remove old `query.py` router entirely
- [x] Remove old API tests (test_api_query.py, test_api_errors.py)
- [x] **Tests**: All 170 tests passing
- [x] **Deploy**: `task deploy` - API pods running

**Step 2: UI Updates** 🔄 IN PROGRESS (API breaking changes require UI updates)
- [ ] Update useLogsQuery: GET with nanosecond timestamps
- [ ] Update useTracesQuery: GET with nanosecond timestamps  
- [ ] Update useMetricsQuery: Fix path `/api/v2/metrics` → `/api/metrics`
- [ ] Update response type definitions (new pagination format)
- [ ] Add timestamp conversion helpers (RFC3339 → nanoseconds)
- [ ] **Test**: Verify all UI pages load data correctly

**Step 3: Old Schema Removal**
- [ ] Remove old schema models/tables
- [ ] **Tests**: Update remaining tests to use new schema only
- [ ] Update documentation (API docs, architecture docs)

**Step 4: Performance Optimization**
- [ ] Add database partitioning for fact tables
- [ ] **Tests**: Verify partition pruning works
- [ ] Query performance tuning (EXPLAIN ANALYZE on slow queries)
- [ ] **Benchmarks**: Measure query latency improvements

**Final Validation**:
- [ ] **Deploy**: `task deploy` - final production validation
- [ ] **Full smoke test**: Ingest & query all signal types
- [ ] Performance benchmarks (vs old schema)
- [ ] **Code review**: Final DRY compliance check

---

## Deployment Strategy

This is a **clean break** deployment:

1. **Empty database**: Deploy to fresh database (no data migration needed)
2. **New schema only**: Alembic migrations create new OTLP-aligned tables
3. **New APIs only**: All endpoints use new schema directly
4. **No versioning**: No v1/v2 API versions - just replace old implementation

**Rationale**: Simpler codebase, no legacy support burden, clean architecture.

---

## Performance Considerations

### Attribute Table Indexes Requirements

**Critical indexes for promoted attribute tables:**
- String attribute tables: Index on (key_id, value) for fast equality filtering
- Int attribute tables: Index on (key_id, value) for range queries
- Composite indexes: (parent_id, key_id, value) for multi-attribute filters
- Apply same pattern across all signal types (logs, spans, metrics)

### Query Pattern Guidelines

**Efficient Queries** - Filter on promoted attributes:
- Use JOIN to typed attribute tables
- Join through attribute_keys for key name lookup
- Index on (key_id, value) enables fast filtering
- Example pattern: JOIN fact table -> JOIN typed attr table ON parent_id WHERE key_id = X AND value = Y

**Less Efficient Queries** - Filter on unpromoted attributes:
- Query JSONB catch-all column using ? or @> operators
- Relies on GIN index on JSONB column
- Slower than typed column filtering but still functional
WHERE o.attributes @> '{"custom.field": "value"}';
```

**Recommendation**: Promote frequently-filtered attributes.

### Caching Strategy

- **Resource/Scope cache**: In-memory cache of hash → ID mappings
- **Attribute key cache**: Cache key → key_id mappings
- **View materialization**: Consider materialized views for trace aggregations

---

## Testing Strategy

### Unit Tests
- Attribute promotion config loading
- Hash calculation consistency
- Resource/scope deduplication logic
- Attribute type extraction

### Integration Tests
- End-to-end ingestion for each signal type
- Attribute filtering queries
- View query correctness
- API response format validation

### Performance Tests
- Ingestion throughput (spans/sec, logs/sec)
- Query latency with various attribute filters
- Cache hit rates
- Index usage verification

---

## Open Questions

1. **Attribute cardinality limits**: Should we enforce max cardinality per key to prevent explosion?
2. **Partitioning strategy**: Time-based partitioning for fact tables? Weekly? Monthly?
3. **Data retention**: TTL for old partitions?
4. **Exemplar storage**: How to efficiently query exemplars linked to metrics?
5. **Trace sampling**: Store sampling decisions in span attributes or separate column?
6. **Override validation**: Should we validate admin overrides on startup (error on invalid keys)?
7. **Config reload**: Hot reload on ConfigMap changes, or require pod restart?

---

## Success Metrics

- **Ingestion**: 10k+ spans/sec on modest hardware
- **Query latency**: p95 < 100ms for attribute-filtered queries
- **Storage efficiency**: 30-40% reduction vs JSONB-only approach
- **Code quality**: <1000 lines per signal storage class (DRY achieved)
- **API clarity**: Clean separation of concerns (traces vs spans)

---

## Kubernetes Label Reference

**IMPORTANT**: Use these exact labels for troubleshooting. The chart uses both `app.kubernetes.io/*` and legacy `app` labels.

### Pod Selection Labels

```bash
# API pods (Gunicorn workers serving /api/v2/* endpoints)
kubectl get pods -n ollyscale -l app.kubernetes.io/component=api
kubectl logs -n ollyscale -l app.kubernetes.io/component=api --tail=100

# OTLP Receiver pods (gRPC/HTTP ingestion on port 4317/4318)
kubectl get pods -n ollyscale -l app.kubernetes.io/component=otlp-receiver
kubectl logs -n ollyscale -l app.kubernetes.io/component=otlp-receiver --tail=100

# Web UI pods (React SPA served by nginx)
kubectl get pods -n ollyscale -l app.kubernetes.io/component=webui
kubectl logs -n ollyscale -l app.kubernetes.io/component=webui --tail=100

# OpAMP Server pods (agent configuration management)
kubectl get pods -n ollyscale -l app.kubernetes.io/component=opamp-server
kubectl logs -n ollyscale -l app.kubernetes.io/component=opamp-server --tail=100

# Migration job (Alembic database migrations)
kubectl get jobs -n ollyscale -l app.kubernetes.io/component=migration
kubectl logs -n ollyscale -l app.kubernetes.io/component=migration --tail=50

# Database pods (CloudNativePG cluster)
kubectl get pods -n ollyscale -l cnpg.io/cluster=ollyscale-db
kubectl get pods -n ollyscale -l cnpg.io/instanceRole=primary  # Primary only
kubectl get pods -n ollyscale -l cnpg.io/instanceRole=replica  # Replicas only
```

### Component Labels Summary

| Component | `app` label | `app.kubernetes.io/component` | Notes |
|-----------|-------------|------------------------------|-------|
| API | `ollyscale-api` | `api` | Gunicorn + FastAPI |
| OTLP Receiver | `ollyscale-otlp-receiver` | `otlp-receiver` | OTLP gRPC/HTTP |
| Web UI | `ollyscale-webui` | `webui` | React + nginx |
| OpAMP Server | `ollyscale-opamp-server` | `opamp-server` | Go service |
| Migration Job | N/A | `migration` | Alembic job |
| Database | `postgresql` | `database` | CloudNativePG |

### Common Troubleshooting Commands

```bash
# Check all ollyscale pods status
kubectl get pods -n ollyscale

# Check migration job completion
kubectl get jobs -n ollyscale -l app.kubernetes.io/component=migration

# View migration logs (full output)
kubectl logs -n ollyscale -l app.kubernetes.io/component=migration

# Exec into database primary
kubectl exec -it -n ollyscale ollyscale-db-1 -- psql -U postgres -d ollyscale

# Check which migrations are applied
kubectl exec -n ollyscale ollyscale-db-1 -- psql -U postgres -d ollyscale -c "SELECT version_num FROM alembic_version;"

# Check if enriched views exist
kubectl exec -n ollyscale ollyscale-db-1 -- psql -U postgres -d ollyscale -c "\dv"

# Port-forward to API for local testing
kubectl port-forward -n ollyscale svc/ollyscale-api 8000:8000

# Port-forward to database for local psql
kubectl port-forward -n ollyscale svc/ollyscale-db-rw 5432:5432
```

---

## Next Steps

### Immediate (Phase 4 Completion)
1. **Create `metrics_v2.py` router** - `/api/v2/metrics/*` endpoints
2. **Write MetricsStorage unit tests** - Expand beyond 8 basic tests
3. **Integration tests** - End-to-end metrics ingestion → query
4. **Deploy and validate** - Test all 5 metric types in production

### Future (Phase 5)
1. **Performance optimization** - Partitioning, query tuning
2. **Remove old schema** - Clean up deprecated tables
3. **Documentation** - Update API docs, architecture diagrams
4. **Benchmarks** - Document performance improvements

**Current Status**: Phase 4 storage layer complete, API endpoints remaining
**Est. Time to Phase 4 Complete**: 2-3 days (API + tests)
**Est. Time to Phase 5 Complete**: 1 week (optimization + cleanup)
