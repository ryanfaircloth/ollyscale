# Schema Implementation Plan: New Data Model

## Overview

This document describes the implementation of the new OTEL Arrow-inspired data model with hybrid attribute storage for **new Ollyscale deployments**. Since we're starting fresh with no existing data to preserve, we can implement the complete new schema directly.

## Implementation Strategy Summary

### Key Features

1. **No Multi-Tenancy**: Single-tenant deployment model per instance
2. **Hybrid Attribute Storage**: Typed tables (string, int, double, bool) + JSONB catch-all
3. **OTLP Enum Dimensions**: Seeded dimension tables for span_kinds, status_codes, severity levels, etc.
4. **Metric Dimension Table**: Deduplication with description variant support
5. **Trace Correlation**: NOT VALID foreign keys for query hints without enforcement
6. **Resource/Scope Deduplication**: Hash-based with first_seen/last_seen tracking
7. **Normalized Data Points**: Separate tables for events, links, exemplars, quantiles

### Implementation Phases

**Phase 1: Foundation Tables (This PR)**

- Create OTLP enum dimension tables (span_kinds, status_codes, etc.)
- Create attribute_keys registry
- Create typed attribute tables pattern (*_attrs_string, *_attrs_int, etc.)
- Seed enum tables with OTLP specification values

**Phase 2: Dimension Tables**

- Create metrics_dim with two-hash strategy
- Create resources_dim and scopes_dim
- Create operation_dim for span name caching

**Phase 3: Fact Tables**

- Create spans_fact with normalized events/links
- Create logs_fact with body type support
- Create metrics_fact with normalized data points (number, histogram, summary, exponential histogram)
- Add NOT VALID foreign keys for trace correlation

**Phase 4: Indexes and Constraints**

- Add performance indexes
- Add trace_id/span_id indexes for correlation
- Create views for attribute unified access

**Phase 5: Receiver Implementation**

- Update receiver to write to new schema
- Implement attribute promotion logic
- Implement metric dimension deduplication
- Add trace correlation support

## Implementation Steps

### Step 1: OTLP Enum Dimension Tables

Create seeded dimension tables for all OTLP enums to provide self-documenting schema and enable readable queries.

**Files to Create:**
- `alembic/versions/XXXXX_create_otlp_enum_dimensions.py`

**Tables:**
- `span_kinds` (6 values)
- `status_codes` (3 values)
- `log_severity_numbers` (25 values)
- `log_body_types` (8 values)
- `metric_types` (5 values)
- `aggregation_temporalities` (3 values)

### Step 2: Attribute Storage Foundation

Create the attribute_keys registry and type-specific attribute tables for all contexts.

**Files to Create:**
- `alembic/versions/XXXXX_create_attribute_keys.py`
- `alembic/versions/XXXXX_create_resource_attrs.py`
- `alembic/versions/XXXXX_create_scope_attrs.py`
- `alembic/versions/XXXXX_create_span_attrs.py`
- `alembic/versions/XXXXX_create_log_attrs.py`
- `alembic/versions/XXXXX_create_metric_attrs.py`

**Pattern per context:** `*_attrs_string`, `*_attrs_int`, `*_attrs_double`, `*_attrs_bool`, `*_attrs_bytes`, `*_attrs_other`

### Step 3: Metric Dimension Table

Create metrics_dim with two-hash strategy for description variant handling.

**Files to Create:**
- `alembic/versions/XXXXX_create_metrics_dim.py`

### Step 4: Resource and Scope Dimensions

Create dimension tables for resource and scope deduplication.

**Files to Create:**
- `alembic/versions/XXXXX_create_resources_dim.py`
- `alembic/versions/XXXXX_create_scopes_dim.py`

### Step 5: Fact Tables

Create fact tables for spans, logs, and metrics with normalized child entities.

**Files to Create:**
- `alembic/versions/XXXXX_create_spans_fact.py` (includes span_events, span_links, event/link attrs)
- `alembic/versions/XXXXX_create_logs_fact.py`
- `alembic/versions/XXXXX_create_metrics_fact.py` (includes data point tables for all metric types)

### Step 6: Indexes and FKs

Add performance indexes and NOT VALID foreign keys for trace correlation.

**Files to Create:**
- `alembic/versions/XXXXX_create_indexes.py`
- `alembic/versions/XXXXX_create_trace_correlation_fks.py`

### Step 7: Views and Utility Tables

Create unified views for attribute access and utility tables for operations.

**Files to Create:**
- `alembic/versions/XXXXX_create_attribute_views.py`
- `alembic/versions/XXXXX_create_operation_dim.py`

## Current Schema Summary

### Dimension Tables (To Be Replaced)

- **tenant_dim** - Multi-tenancy support (id, name) → **ELIMINATED**
- **connection_dim** - Data source tracking (id, tenant_id, name) → **ELIMINATED**
- **namespace_dim** - Namespace tracking → **MERGED INTO resources_dim.service_namespace**
- **service_dim** - Service tracking (id, tenant_id, name, namespace_id, version, attributes, first_seen, last_seen) → **MERGED INTO resources_dim**
- **operation_dim** - Operation/span name tracking → **KEPT for query performance (without tenant_id)**
- **resource_dim** - Resource tracking with JSONB → **REPLACED BY resources_dim + typed attribute tables**

### Fact Tables (To Be Updated)

- **spans_fact** - Trace spans with tenant_id, connection_id, JSONB attributes/events/links
- **logs_fact** - Log records with tenant_id, connection_id, JSONB attributes
- **metrics_fact** - Metrics with tenant_id, connection_id, JSONB attributes/data_points

## New Model: Hybrid Attribute Storage

### Core Concept

The new model replaces single JSONB columns with a **three-tier attribute storage strategy**:

1. **Promoted Attributes** → Type-specific tables (`*_attrs_string`, `*_attrs_int`, `*_attrs_double`, `*_attrs_bool`)
   - High-frequency, heavily-queried keys
   - Native PostgreSQL types with B-tree indexes
   - Example: `service.name`, `http.method`, `http.status_code`

2. **Dropped Attributes** → Not stored at all
   - Configured via ConfigMap
   - High-cardinality ephemeral data with no query value
   - Example: `k8s.pod.uid`, `k8s.replicaset.uid`, sensitive PII

3. **Catch-All Attributes** → JSONB in `*_attrs_other` tables
   - Rare, low-frequency keys
   - Custom attributes not yet promoted
   - Complex types (arrays, objects)
   - GIN indexed for flexible queries

### ConfigMap-Driven Promotion

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollyscale-receiver-config
data:
  promoted-keys.yaml: |
    resource:
      service.name: string
      service.namespace: string
      service.version: string
      telemetry.sdk.name: string
      k8s.deployment.name: string
      deployment.environment: string
    span:
      http.method: string
      http.status_code: int
      db.system: string
      error: bool

  dropped-keys.yaml: |
    resource:
      - k8s.pod.uid
      - k8s.pod.name
      - k8s.replicaset.uid
    span:
      - guid:x-request-id
```

### Attribute Key Registry

Central registry tracks all promoted keys:

```sql
CREATE TABLE attribute_keys (
  key_id SERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  description TEXT,
  value_type TEXT NOT NULL,  -- 'string', 'int', 'double', 'bool'
  is_indexed BOOLEAN DEFAULT false,
  is_searchable BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Type-Specific Tables Pattern

Each context (resource, scope, span, log, metric, event, link) has its own set:

```sql
-- String attributes (most common)
CREATE TABLE resource_attrs_string (
  resource_id BIGINT NOT NULL,
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value TEXT NOT NULL,
  PRIMARY KEY (resource_id, key_id)
);
CREATE INDEX idx_resource_attrs_string_value ON resource_attrs_string(key_id, value);

-- Integer attributes
CREATE TABLE resource_attrs_int (
  resource_id BIGINT NOT NULL,
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value BIGINT NOT NULL,
  PRIMARY KEY (resource_id, key_id)
);

-- Double precision attributes
CREATE TABLE resource_attrs_double (
  resource_id BIGINT NOT NULL,
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value DOUBLE PRECISION NOT NULL,
  PRIMARY KEY (resource_id, key_id)
);

-- Boolean attributes
CREATE TABLE resource_attrs_bool (
  resource_id BIGINT NOT NULL,
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value BOOLEAN NOT NULL,
  PRIMARY KEY (resource_id, key_id)
);

-- JSONB catch-all for unpromoted/complex attributes
CREATE TABLE resource_attrs_other (
  resource_id BIGINT PRIMARY KEY,
  attributes JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_resource_attrs_other_gin ON resource_attrs_other USING GIN(attributes);
```

### Resource Dimension with first_seen/last_seen

The new resources_dim maintains temporal tracking for deduplication:

```sql
CREATE TABLE resources_dim (
  resource_id BIGSERIAL PRIMARY KEY,
  resource_hash VARCHAR(64) NOT NULL UNIQUE,

  -- Extracted well-known fields for fast access
  service_name TEXT,
  service_namespace TEXT,

  -- Temporal tracking - CRITICAL FOR MIGRATION
  first_seen TIMESTAMPTZ DEFAULT NOW(),  -- Never updated, preserves original appearance
  last_seen TIMESTAMPTZ DEFAULT NOW(),   -- Updated on each upsert

  -- Schema versioning
  schema_url TEXT,

  -- Dropped counts
  dropped_attributes_count INTEGER DEFAULT 0
);

-- Upsert pattern preserves first_seen
INSERT INTO resources_dim (resource_hash, service_name, service_namespace, first_seen, last_seen)
VALUES ($1, $2, $3, NOW(), NOW())
ON CONFLICT (resource_hash) DO UPDATE SET
    last_seen = NOW(),  -- Only update last_seen
    service_name = EXCLUDED.service_name,
    service_namespace = EXCLUDED.service_namespace
RETURNING resource_id;
```

### Migration: JSONB → Typed Tables

Old schema example:

```sql
-- resource_dim (current)
resource_id: 42
attributes: {
  "service.name": {"string_value": "my-service"},
  "service.namespace": {"string_value": "prod"},
  "deployment.environment": {"string_value": "production"},
  "k8s.pod.uid": {"string_value": "abc-123"},  -- Will be dropped
  "custom.tag": {"string_value": "value"}      -- Will go to catch-all
}
```

New schema after migration:

```sql
-- resources_dim
resource_id: 42
resource_hash: "sha256..."
service_name: "my-service"
service_namespace: "prod"
first_seen: 2026-01-15 10:00:00
last_seen: 2026-02-04 14:30:00

-- resource_attrs_string (promoted keys)
resource_id | key_id | value
42         | 1      | "my-service"           -- service.name
42         | 2      | "prod"                  -- service.namespace
42         | 5      | "production"            -- deployment.environment

-- resource_attrs_other (catch-all JSONB)
resource_id | attributes
42         | {"custom.tag": {"string_value": "value"}}

-- k8s.pod.uid was dropped (not stored anywhere)
```

## Field-by-Field Mapping Analysis

### ✅ Direct Mappings (No Issues)

| Current Field | New Model Equivalent | Notes |
|--------------|---------------------|-------|
| trace_id | trace_id | Direct mapping |
| span_id | span_id | Direct mapping |
| parent_span_id | parent_span_id | Direct mapping |
| name | name | Direct mapping |
| kind | kind | Direct mapping |
| status_code | status_code | Direct mapping |
| status_message | status_status_message | Direct mapping |
| severity_number | severity_number | Direct mapping |
| severity_text | severity_text | Direct mapping |
| flags | flags | Direct mapping |
| dropped_attributes_count | dropped_attributes_count | Direct mapping |
| dropped_events_count | dropped_events_count | Direct mapping |
| dropped_links_count | dropped_links_count | Direct mapping |

### ⚠️ Fields Requiring Special Handling

#### 1. **Timestamp Nanosecond Precision**

**Current Schema:**

```sql
start_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
start_nanos_fraction SMALLINT NOT NULL DEFAULT 0,  -- 0-999999999
end_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
end_nanos_fraction SMALLINT NOT NULL DEFAULT 0,
timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
nanos_fraction SMALLINT NOT NULL DEFAULT 0,
observed_timestamp TIMESTAMP WITH TIME ZONE,
observed_nanos_fraction SMALLINT NOT NULL DEFAULT 0
```

**New Model:**

```
start_time_unix_nano timestamp
time_unix_nano timestamp
observed_time_unix_nano timestamp
```

**Issue:** Current model splits timestamps into TIMESTAMPTZ + nanos_fraction (0-999999999). New model shows "timestamp" type but OTEL requires full nanosecond precision (Unix epoch nanos).

**Solution Options:**

1. Store as BIGINT (unix_nano) - full precision, harder to query
2. Keep current TIMESTAMPTZ + nanos_fraction approach
3. Use PostgreSQL NUMERIC for full precision

**Recommendation:** Keep current approach (TIMESTAMPTZ + nanos_fraction) as it provides:

- Easy human-readable queries on timestamp
- Exact nanosecond precision in fraction field
- Good index performance on timestamp column

#### 2. **Service Dimension (Namespace + Version)**

**Current Schema:**

```sql
-- service_dim
name VARCHAR(255) NOT NULL
namespace_id INTEGER REFERENCES namespace_dim(id)
version VARCHAR(255)
attributes JSONB

-- In fact tables:
service_id INTEGER REFERENCES service_dim(id)
```

**New Model:**

```
-- No explicit service dimension
-- Only scope_name and scope_version in METRICS/LOGS/SPANS tables
scope_name string "optional"
scope_version string "optional"
```

**Issue:** Current model has a normalized service dimension with namespace relationships. New model doesn't explicitly show service as a dimension, only scope.

**Considerations:**

- Service identity is critical for queries ("show me all spans for service X")
- Namespace provides logical grouping (k8s namespace)
- Version tracking enables deployment correlation
- Current service_dim enables efficient joins and aggregations

**Solution:** Create a hybrid approach:

```sql
-- Keep service dimension but align with OTEL semantics
CREATE TABLE service_dim (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,           -- service.name from resource attrs
  namespace VARCHAR(255),                 -- service.namespace from resource attrs
  version VARCHAR(255),                   -- service.version from resource attrs
  resource_id BIGINT REFERENCES resources(id),  -- Link to full resource
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(name, namespace, version)
);
```

#### 3. **Operation Dimension**

**Current Schema:**

```sql
CREATE TABLE operation_dim (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  service_id INTEGER REFERENCES service_dim(id),
  name VARCHAR(1024) NOT NULL,
  span_kind SMALLINT,
  UNIQUE(tenant_id, service_id, name, span_kind)
)
```

**New Model:**

- No operation dimension
- Operations are just the span `name` field

**Issue:** Current model pre-computes operation dimension for efficient aggregation queries like "top operations by latency for service X".

**Considerations:**

- Operations are heavily queried for APM use cases
- Operation cardinality can be high but is bounded per service
- Pre-computing this dimension significantly improves query performance

**Solution:** Keep operation dimension but remove tenant_id:

```sql
CREATE TABLE operation_dim (
  id SERIAL PRIMARY KEY,
  service_id INTEGER REFERENCES service_dim(id),
  name VARCHAR(1024) NOT NULL,
  span_kind SMALLINT,
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(service_id, name, span_kind)
);
```

#### 4. **Resource Hash-Based Deduplication**

**Current Schema:**

```sql
CREATE TABLE resource_dim (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  resource_hash VARCHAR(64) NOT NULL,
  attributes JSONB NOT NULL,
  UNIQUE(tenant_id, resource_hash)
)
```

**New Model:**

```
METRICS/LOGS/SPANS {
  resource_id u16 "optional"
}
```

**Issue:** Current model uses hash-based deduplication to avoid storing duplicate resource attribute sets. New model shows resource_id but doesn't detail the resource table structure or hash mechanism.

**Solution:** Enhance resource dimension with hash and type-specific attributes:

```sql
CREATE TABLE resources (
  id BIGSERIAL PRIMARY KEY,
  resource_hash VARCHAR(64) NOT NULL UNIQUE,
  schema_url TEXT,
  dropped_attributes_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Then type-specific attribute tables reference this
CREATE TABLE resource_attrs_string (
  resource_id BIGINT NOT NULL REFERENCES resources(id),
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value TEXT NOT NULL,
  PRIMARY KEY (resource_id, key_id)
);
```

#### 5. **Denormalized Resource and Scope JSONB**

**Current Schema:**

```sql
-- In spans_fact, logs_fact, metrics_fact:
resource JSONB
scope JSONB
```

**New Model:**

- Separate dimension tables for resource and scope attributes
- No denormalized JSONB in fact tables

**Issue:** Current model stores full resource and scope objects in each row for:

1. Query flexibility (can filter on any attribute without joins)
2. Complete data recovery
3. Schema flexibility

**Trade-offs:**

- **Storage:** Denormalized = more space, Normalized = less space
- **Query Performance:** Denormalized = faster for attribute filters, Normalized = requires joins
- **Write Performance:** Denormalized = simpler writes, Normalized = requires multiple table inserts
- **Data Integrity:** Denormalized = can drift, Normalized = guaranteed consistency

**Solution:** Hybrid approach during migration:

1. **Phase 1:** Keep denormalized JSONB for backward compatibility
2. **Phase 2:** Populate normalized attribute tables alongside JSONB
3. **Phase 3:** Switch queries to normalized tables
4. **Phase 4:** Remove denormalized JSONB columns

Alternatively, keep a slim version:

```sql
-- Keep resource_id and scope_id only, no JSONB
resource_id BIGINT REFERENCES resources(id)
scope_id BIGINT REFERENCES scopes(id)
```

#### 6. **Events and Links Storage**

**Current Schema:**

```sql
-- In spans_fact:
events JSONB    -- Array of event objects
links JSONB     -- Array of link objects
```

**New Model:**

```sql
SPAN_EVENTS {
  id u32 "optional"
  parent_id u16
  time_unix_nano timestamp "optional"
  name string
}

SPAN_LINKS {
  id u32 "optional"
  parent_id u16
  trace_id bytes[16] "optional"
  span_id bytes[8] "optional"
}
```

**Issue:** Current model stores events and links as JSONB arrays. New model has dedicated tables.

**Solution:** Create separate tables during migration:

```sql
CREATE TABLE span_events (
  id BIGSERIAL PRIMARY KEY,
  span_id BIGINT NOT NULL REFERENCES spans_fact(id),
  time_timestamp TIMESTAMPTZ,
  time_nanos_fraction SMALLINT,
  name VARCHAR(1024),
  dropped_attributes_count INTEGER DEFAULT 0
);

CREATE TABLE span_links (
  id BIGSERIAL PRIMARY KEY,
  span_id BIGINT NOT NULL REFERENCES spans_fact(id),
  linked_trace_id VARCHAR(32),
  linked_span_id VARCHAR(16),
  trace_state TEXT,
  dropped_attributes_count INTEGER DEFAULT 0
);
```

#### 7. **Metrics Data Points**

**Current Schema:**

```sql
-- In metrics_fact:
data_points JSONB    -- Array of data point objects
metric_type VARCHAR(32)
```

**New Model:**

- Separate tables for each metric type:
  - NUMBER_DATA_POINTS
  - HISTOGRAM_DATA_POINTS
  - EXP_HISTOGRAM_DATA_POINTS
  - SUMMARY_DATA_POINTS

**Issue:** Current model stores all data points as JSONB array in single row per metric. New model requires separate tables per metric type.

**Solution:** Create metric-type-specific fact tables:

```sql
CREATE TABLE number_data_points (
  id BIGSERIAL PRIMARY KEY,
  metric_id VARCHAR(255) NOT NULL,  -- Or reference to metrics dimension
  resource_id BIGINT REFERENCES resources(id),
  scope_id BIGINT REFERENCES scopes(id),
  timestamp TIMESTAMPTZ NOT NULL,
  nanos_fraction SMALLINT DEFAULT 0,
  start_timestamp TIMESTAMPTZ,
  start_nanos_fraction SMALLINT DEFAULT 0,
  int_value BIGINT,
  double_value DOUBLE PRECISION,
  flags INTEGER DEFAULT 0
);

CREATE TABLE histogram_data_points (
  id BIGSERIAL PRIMARY KEY,
  metric_id VARCHAR(255) NOT NULL,
  resource_id BIGINT REFERENCES resources(id),
  scope_id BIGINT REFERENCES scopes(id),
  timestamp TIMESTAMPTZ NOT NULL,
  nanos_fraction SMALLINT DEFAULT 0,
  start_timestamp TIMESTAMPTZ,
  start_nanos_fraction SMALLINT DEFAULT 0,
  count BIGINT,
  sum DOUBLE PRECISION,
  min DOUBLE PRECISION,
  max DOUBLE PRECISION,
  bucket_counts BIGINT[],
  explicit_bounds DOUBLE PRECISION[],
  flags INTEGER DEFAULT 0
);
```

### ❌ Fields Being Eliminated

| Current Field | Reason for Elimination |
|--------------|----------------------|
| tenant_id | Multi-tenancy being eliminated |
| connection_id | Data source tracking being eliminated |
| created_at | Not in OTEL spec, can be recomputed from timestamps |

### 🔧 New Fields to Add

| New Field | Purpose | Notes |
|-----------|---------|-------|
| duration_time_unix_nano | Span duration | Can be computed from end - start but storing improves query performance |
| trace_state | W3C Trace Context | Currently not stored, needed for distributed tracing |
| schema_url | Schema version | OTEL protocol field for versioning |
| resource_schema_url | Resource schema version | OTEL protocol field |
| aggregation_temporality | Metrics aggregation | Delta vs Cumulative |
| is_monotonic | Metrics behavior | Counter vs Gauge |

## Detailed Migration Strategy

### Phase 1: Schema Extension (Backward Compatible)

**Goal:** Add new normalized structures alongside existing tables without breaking current system.

**Database Changes:**

```sql
-- 1. Create attribute_keys registry
CREATE TABLE attribute_keys (
  key_id SERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  description TEXT,
  value_type TEXT NOT NULL,
  is_indexed BOOLEAN DEFAULT false,
  is_searchable BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create resources_dim with first_seen/last_seen tracking
CREATE TABLE resources_dim (
  resource_id BIGSERIAL PRIMARY KEY,
  resource_hash VARCHAR(64) NOT NULL UNIQUE,
  service_name TEXT,
  service_namespace TEXT,
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  schema_url TEXT,
  dropped_attributes_count INTEGER DEFAULT 0
);

-- 3. Create type-specific attribute tables
CREATE TABLE resource_attrs_string (
  resource_id BIGINT NOT NULL REFERENCES resources_dim(resource_id),
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value TEXT NOT NULL,
  PRIMARY KEY (resource_id, key_id)
);
CREATE INDEX idx_resource_attrs_string_value ON resource_attrs_string(key_id, value);

-- Similar for resource_attrs_int, resource_attrs_double, resource_attrs_bool

-- 4. Create catch-all JSONB table
CREATE TABLE resource_attrs_other (
  resource_id BIGINT PRIMARY KEY REFERENCES resources_dim(resource_id),
  attributes JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_resource_attrs_other_gin ON resource_attrs_other USING GIN(attributes);

-- 5. Create scopes_dim with similar structure
CREATE TABLE scopes_dim (
  scope_id BIGSERIAL PRIMARY KEY,
  scope_hash VARCHAR(64) NOT NULL UNIQUE,
  name TEXT,
  version TEXT,
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  schema_url TEXT,
  dropped_attributes_count INTEGER DEFAULT 0
);

-- 6. Create span_events and span_links tables
CREATE TABLE span_events (
  event_id BIGSERIAL PRIMARY KEY,
  span_id BIGINT NOT NULL,  -- Will reference new spans table
  time_timestamp TIMESTAMPTZ NOT NULL,
  time_nanos_fraction SMALLINT DEFAULT 0,
  name VARCHAR(1024) NOT NULL,
  dropped_attributes_count INTEGER DEFAULT 0
);

CREATE TABLE span_links (
  link_id BIGSERIAL PRIMARY KEY,
  span_id BIGINT NOT NULL,  -- Will reference new spans table
  linked_trace_id VARCHAR(32) NOT NULL,
  linked_span_id VARCHAR(16) NOT NULL,
  trace_state TEXT,
  dropped_attributes_count INTEGER DEFAULT 0
);

-- 7. Create metric-type-specific tables
CREATE TABLE number_data_points (
  data_point_id BIGSERIAL PRIMARY KEY,
  metric_id VARCHAR(255) NOT NULL,
  resource_id BIGINT REFERENCES resources_dim(resource_id),
  scope_id BIGINT REFERENCES scopes_dim(scope_id),
  time_timestamp TIMESTAMPTZ NOT NULL,
  time_nanos_fraction SMALLINT DEFAULT 0,
  start_timestamp TIMESTAMPTZ,
  start_nanos_fraction SMALLINT DEFAULT 0,
  int_value BIGINT,
  double_value DOUBLE PRECISION,
  aggregation_temporality INTEGER,
  is_monotonic BOOLEAN,
  flags INTEGER DEFAULT 0,
  dropped_attributes_count INTEGER DEFAULT 0
);

-- Similar for histogram_data_points, exp_histogram_data_points, summary_data_points
```

**ConfigMap Deployment:**

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollyscale-receiver-config
  namespace: ollyscale
data:
  promoted-keys.yaml: |
    resource:
      service.name: string
      service.namespace: string
      service.version: string
      telemetry.sdk.name: string
      telemetry.sdk.language: string
      telemetry.sdk.version: string
      k8s.namespace.name: string
      k8s.deployment.name: string
      k8s.container.name: string
      k8s.node.name: string
      deployment.environment: string
    scope:
      otel.library.name: string
      otel.library.version: string
    span:
      http.method: string
      http.status_code: int
      http.url: string
      db.system: string
      db.name: string
      db.statement: string
      error: bool

  dropped-keys.yaml: |
    resource:
      - k8s.pod.uid
      - k8s.pod.name
      - k8s.replicaset.uid
      - service.instance.id
    span:
      - guid:x-request-id
      - internal.debug.id
EOF
```

**Application Changes:**

- No changes to existing ingestion code yet
- Deploy ConfigMap for future use

**Timeline:** 1-2 weeks for schema creation and testing

### Phase 2: Dual-Write Implementation

**Goal:** Update receiver to write to both old and new structures while preserving first_seen/last_seen.

**Receiver Changes:**

1. **Load ConfigMaps on startup:**

```python
# Load promoted/dropped keys
promoted_keys = load_promoted_keys_config()
dropped_keys = load_dropped_keys_config()
```

1. **Extract OTLP AnyValue attributes:**

```python
def extract_typed_value(anyvalue: dict) -> tuple[str, any]:
    """Extract type and value from OTLP AnyValue format."""
    if 'string_value' in anyvalue:
        return 'string', anyvalue['string_value']
    elif 'int_value' in anyvalue:
        return 'int', int(anyvalue['int_value'])
    elif 'double_value' in anyvalue:
        return 'double', float(anyvalue['double_value'])
    elif 'bool_value' in anyvalue:
        return 'bool', anyvalue['bool_value']
    elif 'bytes_value' in anyvalue:
        return 'bytes', anyvalue['bytes_value']
    else:
        return 'other', anyvalue
```

1. **Process resource attributes with first_seen/last_seen upsert:**

```python
def ingest_resource(resource_attrs: dict) -> int:
    # Compute hash of all attributes (before dropping)
    resource_hash = compute_hash(resource_attrs)

    # Split attributes: promoted, dropped, other
    promoted_attrs = {}
    other_attrs = {}
    dropped_count = 0

    for key, anyvalue in resource_attrs.items():
        if key in dropped_keys['resource']:
            dropped_count += 1
            continue

        value_type, value = extract_typed_value(anyvalue)

        if key in promoted_keys['resource']:
            promoted_attrs[key] = (value_type, value)
        else:
            other_attrs[key] = anyvalue  # Keep in OTLP format

    # Upsert resources_dim (CRITICAL: preserves first_seen)
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO resources_dim (
                resource_hash,
                service_name,
                service_namespace,
                first_seen,
                last_seen,
                dropped_attributes_count
            )
            VALUES (%s, %s, %s, NOW(), NOW(), %s)
            ON CONFLICT (resource_hash) DO UPDATE SET
                last_seen = NOW(),  -- Only update last_seen
                service_name = EXCLUDED.service_name,
                service_namespace = EXCLUDED.service_namespace,
                dropped_attributes_count = EXCLUDED.dropped_attributes_count
            RETURNING resource_id, first_seen
        """, (
            resource_hash,
            promoted_attrs.get('service.name', [None, None])[1],
            promoted_attrs.get('service.namespace', [None, None])[1],
            dropped_count
        ))
        resource_id, first_seen = cur.fetchone()

    # Insert promoted attributes (upsert to handle duplicates)
    for key, (value_type, value) in promoted_attrs.items():
        key_id = get_or_create_attribute_key(key, value_type)
        table_name = f"resource_attrs_{value_type}"

        cur.execute(f"""
            INSERT INTO {table_name} (resource_id, key_id, value)
            VALUES (%s, %s, %s)
            ON CONFLICT (resource_id, key_id) DO UPDATE SET
                value = EXCLUDED.value
        """, (resource_id, key_id, value))

    # Insert catch-all attributes
    if other_attrs:
        cur.execute("""
            INSERT INTO resource_attrs_other (resource_id, attributes)
            VALUES (%s, %s)
            ON CONFLICT (resource_id) DO UPDATE SET
                attributes = EXCLUDED.attributes
        """, (resource_id, json.dumps(other_attrs)))

    # ALSO write to old schema for backward compatibility
    cur.execute("""
        INSERT INTO resource_dim (resource_hash, attributes)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (resource_hash, json.dumps(resource_attrs)))

    return resource_id
```

1. **Similar dual-write for spans, logs, metrics**

**Validation:**

- Compare row counts between old and new tables
- Validate first_seen values are never updated
- Validate last_seen values are updated on each appearance
- Check dropped_attributes_count matches actual dropped keys

**Timeline:** 3-4 weeks for implementation and testing

### Phase 3: Backfill & Validation

**Goal:** Migrate historical data from old schema to new schema while preserving first_seen timestamps.

**Backfill Process:**

```sql
-- Migrate resource_dim to resources_dim + typed tables
INSERT INTO resources_dim (
    resource_hash,
    service_name,
    service_namespace,
    first_seen,
    last_seen,
    dropped_attributes_count
)
SELECT
    resource_hash,
    attributes->'service.name'->>'string_value',
    attributes->'service.namespace'->>'string_value',
    first_seen,  -- CRITICAL: preserve original first_seen
    last_seen,   -- CRITICAL: preserve last last_seen
    0  -- We didn't track dropped count before
FROM resource_dim
ON CONFLICT (resource_hash) DO NOTHING;  -- Don't overwrite dual-written data

-- Migrate promoted string attributes
WITH promoted_resource_attrs AS (
    SELECT
        rd.id as old_resource_id,
        rdnew.resource_id as new_resource_id,
        jsonb_each(rd.attributes) as attr
    FROM resource_dim rd
    JOIN resources_dim rdnew ON rd.resource_hash = rdnew.resource_hash
    WHERE jsonb_typeof(rd.attributes) = 'object'
)
INSERT INTO resource_attrs_string (resource_id, key_id, value)
SELECT
    new_resource_id,
    ak.key_id,
    (attr).value->>'string_value'
FROM promoted_resource_attrs
CROSS JOIN attribute_keys ak
WHERE (attr).key = ak.key
    AND ak.value_type = 'string'
    AND (attr).value ? 'string_value'
ON CONFLICT (resource_id, key_id) DO NOTHING;

-- Similar backfill for int, double, bool attributes...

-- Migrate catch-all attributes (everything not promoted)
INSERT INTO resource_attrs_other (resource_id, attributes)
SELECT
    rdnew.resource_id,
    jsonb_object_agg(
        (attr).key,
        (attr).value
    )
FROM resource_dim rd
JOIN resources_dim rdnew ON rd.resource_hash = rdnew.resource_hash
CROSS JOIN jsonb_each(rd.attributes) as attr
LEFT JOIN attribute_keys ak ON (attr).key = ak.key
WHERE ak.key_id IS NULL  -- Not promoted
GROUP BY rdnew.resource_id
ON CONFLICT (resource_id) DO NOTHING;
```

**Validation Queries:**

```sql
-- Verify row counts match
SELECT
    (SELECT COUNT(*) FROM resource_dim) as old_count,
    (SELECT COUNT(*) FROM resources_dim) as new_count;

-- Verify first_seen preserved
SELECT
    rd.first_seen as old_first_seen,
    rdnew.first_seen as new_first_seen,
    rd.first_seen = rdnew.first_seen as matches
FROM resource_dim rd
JOIN resources_dim rdnew ON rd.resource_hash = rdnew.resource_hash
WHERE rd.first_seen != rdnew.first_seen;  -- Should return 0 rows

-- Verify all promoted attrs migrated
SELECT COUNT(*)
FROM resources_dim rd
LEFT JOIN resource_attrs_string ras ON rd.resource_id = ras.resource_id
WHERE ras.resource_id IS NULL;  -- Should match resources with no string attrs
```

**Timeline:** 2-3 weeks for backfill and validation

### Phase 4: Query Migration

**Goal:** Update all queries to use new normalized structure.

**Create Compatibility Views:**

```sql
-- View that emulates old resource_dim.attributes JSONB structure
CREATE VIEW resource_dim_compat AS
SELECT
    rd.resource_id as id,
    rd.resource_hash,
    rd.first_seen,
    rd.last_seen,
    -- Reconstruct JSONB from typed tables
    (
        SELECT jsonb_object_agg(
            ak.key,
            jsonb_build_object('string_value', ras.value)
        )
        FROM resource_attrs_string ras
        JOIN attribute_keys ak ON ras.key_id = ak.key_id
        WHERE ras.resource_id = rd.resource_id
    ) || COALESCE(
        (
            SELECT jsonb_object_agg(
                ak.key,
                jsonb_build_object('int_value', rai.value::text)
            )
            FROM resource_attrs_int rai
            JOIN attribute_keys ak ON rai.key_id = ak.key_id
            WHERE rai.resource_id = rd.resource_id
        ), '{}'::jsonb
    ) || COALESCE(rao.attributes, '{}'::jsonb) as attributes
FROM resources_dim rd
LEFT JOIN resource_attrs_other rao ON rd.resource_id = rao.resource_id;
```

**Update Application Queries:**

```python
# Old query
SELECT * FROM spans_fact
WHERE resource->>'service.name' = 'my-service';

# New query (using denormalized service_name)
SELECT * FROM spans_fact sf
JOIN resources_dim rd ON sf.resource_id = rd.resource_id
WHERE rd.service_name = 'my-service';

# Or using typed attribute table
SELECT * FROM spans_fact sf
JOIN resource_attrs_string ras ON sf.resource_id = ras.resource_id
JOIN attribute_keys ak ON ras.key_id = ak.key_id
WHERE ak.key = 'service.name' AND ras.value = 'my-service';
```

**Timeline:** 4-6 weeks for query migration and testing

### Phase 5: Cleanup & Optimization

**Goal:** Remove legacy structures and optimize new schema.

**Cleanup Steps:**

```sql
-- 1. Drop old columns
ALTER TABLE spans_fact DROP COLUMN tenant_id;
ALTER TABLE spans_fact DROP COLUMN connection_id;
ALTER TABLE logs_fact DROP COLUMN tenant_id;
ALTER TABLE logs_fact DROP COLUMN connection_id;
ALTER TABLE metrics_fact DROP COLUMN tenant_id;
ALTER TABLE metrics_fact DROP COLUMN connection_id;

-- 2. Drop old dimension tables
DROP TABLE tenant_dim CASCADE;
DROP TABLE connection_dim CASCADE;
DROP TABLE resource_dim CASCADE;  -- After all references updated

-- 3. Drop denormalized JSONB (optional, keep for audit)
-- ALTER TABLE spans_fact DROP COLUMN resource;
-- ALTER TABLE spans_fact DROP COLUMN scope;
```

**Optimization:**

```sql
-- 1. Add partitioning on fact tables
CREATE TABLE spans_fact_partitioned (
    LIKE spans_fact
) PARTITION BY RANGE (start_timestamp);

-- Create monthly partitions
CREATE TABLE spans_fact_202601 PARTITION OF spans_fact_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- 2. Create materialized views for common queries
CREATE MATERIALIZED VIEW mv_top_operations_by_service AS
SELECT
    rd.service_name,
    sf.name as operation_name,
    COUNT(*) as span_count,
    AVG(sf.duration_time_unix_nano) as avg_duration
FROM spans_fact sf
JOIN resources_dim rd ON sf.resource_id = rd.resource_id
GROUP BY rd.service_name, sf.name;

CREATE UNIQUE INDEX ON mv_top_operations_by_service(service_name, operation_name);

-- Refresh hourly
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_operations_by_service;

-- 3. Optimize indexes based on query patterns
CREATE INDEX idx_spans_resource_time ON spans_fact(resource_id, start_timestamp DESC);
CREATE INDEX idx_resource_attrs_string_composite ON resource_attrs_string(key_id, value, resource_id);
```

**Timeline:** 2-3 weeks for cleanup and optimization

## Critical Success Factors

1. **Nanosecond Precision:** Maintain current TIMESTAMPTZ + nanos_fraction approach for full nanosecond precision
2. **Service/Operation Dimensions:** Keep these for query performance (remove tenant_id, add first_seen/last_seen)
3. **Resource Deduplication:** Maintain hash-based approach with **first_seen/last_seen temporal tracking**
4. **ConfigMap-Driven:** Use Kubernetes ConfigMaps for promoted_keys and dropped_keys (no code changes)
5. **Gradual Migration:** Dual-write approach with compatibility views during transition
6. **Query Performance:** Validate normalized structure maintains or improves performance
7. **Backward Compatibility:** Maintain views that emulate old structure during transition
8. **first_seen Preservation:** CRITICAL - never update first_seen, only last_seen on upsert

## Decisions Made (Answers to Previous Questions)

### 1. ✅ Keep service_dim and operation_dim?

**Decision:** YES, keep both dimensions but remove tenant_id and add first_seen/last_seen.

**Rationale:**

- Service dimension enables efficient "show all spans for service X" queries
- Operation dimension pre-computes (service, operation_name, span_kind) for APM aggregations
- Both provide significant query performance benefits
- Adding first_seen/last_seen enables temporal analysis and data lifecycle management

```sql
CREATE TABLE service_dim (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  namespace VARCHAR(255),
  version VARCHAR(255),
  resource_id BIGINT REFERENCES resources_dim(resource_id),
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(name, namespace, version)
);

CREATE TABLE operation_dim (
  id SERIAL PRIMARY KEY,
  service_id INTEGER REFERENCES service_dim(id),
  name VARCHAR(1024) NOT NULL,
  span_kind SMALLINT,
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(service_id, name, span_kind)
);
```

### 2. ✅ Transition period strategy?

**Decision:** Use **dual-write with compatibility views** during 3-6 month transition.

**Implementation:**

- Phase 2: Receiver writes to both old and new structures
- Phase 3: Create views that emulate old JSONB structure from normalized tables
- Phase 4: Gradually migrate queries to use new structures
- Phase 5: Drop old structures once all queries migrated

**Benefits:**

- Zero downtime migration
- Gradual query migration reduces risk
- Easy rollback if issues detected
- Compatibility views enable some queries to auto-benefit from new indexes

### 3. ✅ Backfill strategy for historical data?

**Decision:** **SQL-based backfill with first_seen/last_seen preservation.**

**Process:**

1. Run backfill SQL during low-traffic period
2. Use `ON CONFLICT DO NOTHING` to avoid overwriting dual-written data
3. **CRITICAL: Copy first_seen/last_seen from old schema** - never recalculate as NOW()
4. Backfill in batches (e.g., 100K rows at a time) to avoid long transactions
5. Validate row counts and sample data after each batch

**SQL Pattern:**

```sql
INSERT INTO resources_dim (resource_hash, service_name, first_seen, last_seen, ...)
SELECT
    resource_hash,
    attributes->'service.name'->>'string_value',
    first_seen,  -- PRESERVE original first_seen
    last_seen,   -- PRESERVE original last_seen
    ...
FROM resource_dim
ON CONFLICT (resource_hash) DO NOTHING;
```

### 4. ✅ Maintain tenant/connection concepts?

**Decision:** **NO - eliminate completely from storage.**

**Rationale:**

- Ollyscale moving to simplified deployment model
- tenant_id and connection_id add complexity without current use case
- Can be re-added as JSONB attributes if needed in future
- Simplifies queries and reduces index overhead

**Migration:**

- Phase 5: `ALTER TABLE ... DROP COLUMN tenant_id, connection_id`
- Document that multi-tenancy can be achieved via:
  - Separate PostgreSQL databases per tenant
  - Filtering by resource attributes (e.g., `tenant` custom attribute)
  - Network-level isolation (separate receiver endpoints)

### 5. ✅ Keep denormalized JSONB for flexibility?

**Decision:** **Hybrid approach - keep resource/scope JSONB in fact tables during transition, optionally drop later.**

**During Migration (Phases 1-4):**

```sql
-- Fact tables have both
spans_fact:
  resource_id BIGINT REFERENCES resources_dim(resource_id)
  resource JSONB  -- Keep for backward compatibility
  scope_id BIGINT REFERENCES scopes_dim(scope_id)
  scope JSONB     -- Keep for backward compatibility
```

**Post-Migration (Phase 5 - Optional):**

```sql
-- Option A: Drop JSONB completely
ALTER TABLE spans_fact DROP COLUMN resource;
ALTER TABLE spans_fact DROP COLUMN scope;

-- Option B: Keep slim JSONB with non-promoted attributes
-- (Same as *_attrs_other content)

-- Option C: Keep full JSONB for audit/disaster recovery
-- (Accept ~30-40% storage overhead for safety)
```

**Recommendation:** Keep resource/scope JSONB for 6-12 months post-migration, then evaluate:

- If no queries use it → drop it
- If used for debugging → move to separate audit table
- If frequently queried → keep it but add GIN indexes

### 6. ✅ Partitioning strategy for normalized tables?

**Decision:** **Time-based partitioning on fact tables, list/hash partitioning on dimension tables if needed.**

**Fact Tables (spans, logs, data_points):**

```sql
-- Monthly partitions
CREATE TABLE spans_fact (
    ...
    start_timestamp TIMESTAMPTZ NOT NULL,
    ...
) PARTITION BY RANGE (start_timestamp);

CREATE TABLE spans_fact_202601 PARTITION OF spans_fact
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

**Dimension Tables:**

- Usually too small to need partitioning
- If resources_dim grows beyond 10M rows, consider hash partitioning on resource_hash
- If attribute tables grow large, consider list partitioning on key_id (one partition per promoted key)

**Typed Attribute Tables:**

- Consider partitioning by key_id if single table grows beyond 100M rows

```sql
CREATE TABLE resource_attrs_string_service_name PARTITION OF resource_attrs_string
    FOR VALUES IN (1);  -- key_id for 'service.name'
```

### 7. ✅ ConfigMap update strategy?

**Decision:** **Support dynamic reload with graceful fallback.**

**Implementation:**

```python
class ConfigMapWatcher:
    def __init__(self):
        self.promoted_keys = self.load_config()
        self.dropped_keys = self.load_dropped_config()
        self.last_reload = datetime.now()

    def reload_if_changed(self):
        """Check for ConfigMap changes every minute."""
        if (datetime.now() - self.last_reload).seconds > 60:
            try:
                new_promoted = self.load_config()
                new_dropped = self.load_dropped_config()

                # Atomic swap
                self.promoted_keys = new_promoted
                self.dropped_keys = new_dropped
                self.last_reload = datetime.now()

                logger.info("Reloaded promoted/dropped keys from ConfigMap")
            except Exception as e:
                logger.error(f"Failed to reload ConfigMap: {e}")
                # Keep using existing config
```

**Benefits:**

- No receiver restart needed to add/remove promoted keys
- Ops team can tune performance by promoting high-cardinality keys
- Easy A/B testing of different promotion strategies

## Open Questions (Remaining)

1. **Backfill performance:** Can we achieve <1 hour downtime for backfill, or do we need online backfill?
2. **Query performance comparison:** Need benchmarks comparing old JSONB queries vs new normalized queries
3. **Storage savings:** What's the expected storage reduction from typed tables vs JSONB?
4. **Index strategy:** Which composite indexes provide best performance for common query patterns?
5. **Retention policy:** Should we leverage partitioning for automated data retention (e.g., drop partitions older than 90 days)?
6. **Disaster recovery:** Do we need point-in-time recovery during migration, or is backup/restore sufficient?
