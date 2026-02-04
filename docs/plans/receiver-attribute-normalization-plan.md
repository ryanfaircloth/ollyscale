# Receiver Attribute Normalization Plan

This document describes how the OTLP receiver will normalize OTLP attributes into the typed attribute table structure.

## Overview

The receiver will:

1. Extract attributes from OTLP KeyValue pairs
2. Normalize promoted keys into type-specific tables
3. Store unpromoted keys in JSONB catch-all
4. Maintain first_seen/last_seen timestamps for dimension tables
5. Support configurable key promotion and dropping

## Default Promoted Resource Keys (String Type)

Based on analysis of production data, these resource attribute keys will be promoted to `resource_attrs_string` by default:

| Key | Cardinality | Justification |
|-----|-------------|---------------|
| `service.name` | Low (~4) | Core service identity, heavily queried |
| `service.namespace` | Low (~2) | Service grouping, heavily queried |
| `service.version` | Low-Medium (~3) | Version filtering, indexable |
| `telemetry.sdk.name` | Very Low (~2) | SDK identification |
| `telemetry.sdk.language` | Very Low (~2) | Language filtering |
| `telemetry.sdk.version` | Low (~2) | SDK version tracking |
| `telemetry.auto.version` | Very Low (~1) | Auto-instrumentation version |
| `k8s.namespace.name` | Low (~2) | Kubernetes namespace filtering |
| `k8s.deployment.name` | Low (~3) | Deployment identification |
| `k8s.container.name` | Low (~3) | Container identification |
| `k8s.node.name` | Low (~3) | Node placement queries |

### High-Cardinality Keys - JSONB Catch-All

These keys have high cardinality and should remain in JSONB:

| Key | Cardinality | Why JSONB |
|-----|-------------|-----------|
| `service.instance.id` | High (~8 unique per 8 samples) | Unique per instance, rarely queried |
| `k8s.pod.name` | Very High (1:1 with pods) | Ephemeral, unique per pod |
| `k8s.pod.uid` | Very High (1:1 with pods) | UUID, unique per pod |
| `k8s.replicaset.name` | High | Generated names, ephemeral |
| `k8s.replicaset.uid` | Very High | UUID, unique per replicaset |
| `k8s.deployment.uid` | High | UUID, stable but not queried by value |

## Configuration via ConfigMap

### Promoted Keys ConfigMap

Allow operators to extend the default promotion list:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollyscale-receiver-config
  namespace: ollyscale
data:
  promoted-resource-keys.yaml: |
    # Additional resource attribute keys to normalize into typed tables
    # Format: key: type
    # Supported types: string, int, double, bool
    resource:
      # OTEL semantic conventions
      host.name: string
      host.arch: string
      process.pid: int
      deployment.environment: string

      # Custom application attributes
      app.team: string
      app.cost_center: string

    # Scope attributes (if any need normalization)
    scope: {}

    # Span attributes
    span:
      http.method: string
      http.status_code: int
      db.system: string
      db.name: string

    # Log attributes
    log:
      log.level: string

    # Metric attributes
    metric: {}
```

### Dropped Keys ConfigMap

Allow operators to drop noisy or sensitive attributes at ingestion:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollyscale-receiver-config
  namespace: ollyscale
data:
  dropped-resource-keys.yaml: |
    # Resource attribute keys to drop at receiver (not stored)
    # Use for:
    # - Sensitive data (PII, secrets)
    # - Noisy attributes with no query value
    # - Compliance requirements
    resource:
      - k8s.pod.uid           # Ephemeral, rarely useful
      - k8s.replicaset.uid    # Ephemeral, rarely useful
      - process.parent_pid    # Internal detail, not needed
      - host.id               # May contain sensitive info

    scope:
      - telemetry.sdk.commit_hash  # Not useful for queries

    span: []
    log: []
    metric: []
```

## Dimension Tables with First/Last Seen Tracking

### Resource Dimension Table

```sql
CREATE TABLE resources_dim (
  resource_id BIGSERIAL PRIMARY KEY,
  resource_hash VARCHAR(64) NOT NULL UNIQUE,

  -- Directly extracted well-known fields (not in attrs tables)
  service_name TEXT,
  service_namespace TEXT,

  -- Temporal tracking
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),

  -- Schema versioning
  schema_url TEXT
);

-- Type-specific resource attributes
CREATE TABLE resource_attrs_string (
  resource_id BIGINT NOT NULL REFERENCES resources_dim(resource_id),
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value TEXT NOT NULL,
  PRIMARY KEY (resource_id, key_id)
);

CREATE INDEX idx_resource_attrs_string_lookup ON resource_attrs_string(key_id, value);

-- Catch-all for unpromoted attributes
CREATE TABLE resource_attrs_other (
  resource_id BIGINT PRIMARY KEY REFERENCES resources_dim(resource_id),
  attributes JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_resource_attrs_other_gin ON resource_attrs_other USING GIN(attributes);
```

### Scope Dimension Table

```sql
CREATE TABLE scopes_dim (
  scope_id BIGSERIAL PRIMARY KEY,
  scope_hash VARCHAR(64) NOT NULL UNIQUE,

  -- Directly extracted fields
  scope_name TEXT,
  scope_version TEXT,

  -- Temporal tracking
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_seen TIMESTAMPTZ DEFAULT NOW(),

  -- Schema versioning
  schema_url TEXT
);

-- Type-specific scope attributes
CREATE TABLE scope_attrs_string (
  scope_id BIGINT NOT NULL REFERENCES scopes_dim(scope_id),
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value TEXT NOT NULL,
  PRIMARY KEY (scope_id, key_id)
);

-- Catch-all
CREATE TABLE scope_attrs_other (
  scope_id BIGINT PRIMARY KEY REFERENCES scopes_dim(scope_id),
  attributes JSONB NOT NULL DEFAULT '{}'
);
```

## Receiver Ingestion Logic

### Resource Processing Flow

```python
async def process_resource(otlp_resource: Resource) -> int:
    """
    Process OTLP resource and return resource_id.
    Maintains first_seen/last_seen timestamps.
    """
    # 1. Load promoted keys config
    promoted_keys = load_promoted_keys_config()
    dropped_keys = load_dropped_keys_config()

    # 2. Extract attributes as dict
    attrs = {}
    for kv in otlp_resource.attributes:
        key = kv.key

        # Drop if configured
        if key in dropped_keys.get('resource', []):
            continue

        # Extract typed value from AnyValue
        if kv.value.HasField('string_value'):
            value = kv.value.string_value
            value_type = 'string'
        elif kv.value.HasField('int_value'):
            value = kv.value.int_value
            value_type = 'int'
        elif kv.value.HasField('double_value'):
            value = kv.value.double_value
            value_type = 'double'
        elif kv.value.HasField('bool_value'):
            value = kv.value.bool_value
            value_type = 'bool'
        else:
            # Complex types (array, kvlist) -> keep as JSONB
            value = anyvalue_to_json(kv.value)
            value_type = 'object'

        attrs[key] = {'value': value, 'type': value_type}

    # 3. Compute resource hash (for deduplication)
    # Hash includes all attributes except dropped ones
    resource_hash = compute_hash(attrs)

    # 4. Extract well-known fields
    service_name = attrs.get('service.name', {}).get('value')
    service_namespace = attrs.get('service.namespace', {}).get('value')
    schema_url = otlp_resource.schema_url

    # 5. Upsert resource dimension
    # Use ON CONFLICT to update last_seen
    query = """
        INSERT INTO resources_dim (resource_hash, service_name, service_namespace, schema_url, first_seen, last_seen)
        VALUES ($1, $2, $3, $4, NOW(), NOW())
        ON CONFLICT (resource_hash) DO UPDATE SET
            last_seen = NOW(),
            service_name = EXCLUDED.service_name,
            service_namespace = EXCLUDED.service_namespace
        RETURNING resource_id
    """
    resource_id = await db.fetchval(query, resource_hash, service_name, service_namespace, schema_url)

    # 6. Split attributes into promoted vs catch-all
    promoted_attrs = {}
    catchall_attrs = {}

    for key, item in attrs.items():
        value = item['value']
        value_type = item['type']

        # Check if key is promoted
        config_type = promoted_keys.get('resource', {}).get(key)

        if config_type and value_type == config_type:
            # Promoted to typed table
            promoted_attrs.setdefault(value_type, []).append({
                'key': key,
                'value': value
            })
        else:
            # Catch-all JSONB
            # Store in OTLP AnyValue format for consistency
            catchall_attrs[key] = anyvalue_to_json_format(value, value_type)

    # 7. Insert/update promoted attributes
    for value_type, items in promoted_attrs.items():
        table = f'resource_attrs_{value_type}'

        for item in items:
            # Get or create key_id
            key_id = await get_or_create_attribute_key(item['key'], value_type)

            # Upsert attribute
            query = f"""
                INSERT INTO {table} (resource_id, key_id, value)
                VALUES ($1, $2, $3)
                ON CONFLICT (resource_id, key_id) DO UPDATE SET
                    value = EXCLUDED.value
            """
            await db.execute(query, resource_id, key_id, item['value'])

    # 8. Insert/update catch-all JSONB
    if catchall_attrs:
        query = """
            INSERT INTO resource_attrs_other (resource_id, attributes)
            VALUES ($1, $2)
            ON CONFLICT (resource_id) DO UPDATE SET
                attributes = EXCLUDED.attributes
        """
        await db.execute(query, resource_id, json.dumps(catchall_attrs))

    return resource_id
```

### Attribute Key Registry Management

```python
async def get_or_create_attribute_key(key: str, value_type: str) -> int:
    """
    Get key_id from attribute_keys table, creating if needed.
    Uses cache to minimize DB lookups.
    """
    # Check cache first
    cache_key = f'{key}:{value_type}'
    if cache_key in attribute_key_cache:
        return attribute_key_cache[cache_key]

    # Determine indexing strategy based on key
    is_indexed = should_index_key(key, value_type)
    is_searchable = should_make_searchable(key)

    # Upsert key
    query = """
        INSERT INTO attribute_keys (key, value_type, is_indexed, is_searchable)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (key) DO UPDATE SET
            value_type = EXCLUDED.value_type,
            is_indexed = EXCLUDED.is_indexed OR attribute_keys.is_indexed,
            is_searchable = EXCLUDED.is_searchable OR attribute_keys.is_searchable
        RETURNING key_id
    """
    key_id = await db.fetchval(query, key, value_type, is_indexed, is_searchable)

    # Cache result
    attribute_key_cache[cache_key] = key_id

    return key_id


def should_index_key(key: str, value_type: str) -> bool:
    """
    Determine if attribute should be indexed based on:
    - Expected cardinality
    - Query patterns
    - OTEL semantic conventions
    """
    # High-priority indexed keys
    indexed_keys = {
        'service.name',
        'service.namespace',
        'deployment.environment',
        'http.method',
        'http.status_code',
        'db.system',
        'db.name',
    }

    return key in indexed_keys


def should_make_searchable(key: str) -> bool:
    """
    Determine if attribute should be searchable (available in WHERE clauses).
    """
    # Everything promoted is searchable by default
    return True
```

## Span Fact Table with Resource/Scope References

```sql
CREATE TABLE spans_fact (
  span_id BIGSERIAL PRIMARY KEY,

  -- Dimension references
  resource_id BIGINT NOT NULL REFERENCES resources_dim(resource_id),
  scope_id BIGINT NOT NULL REFERENCES scopes_dim(scope_id),

  -- Core span fields
  trace_id BYTEA NOT NULL,  -- 16 bytes
  span_id_hex BYTEA NOT NULL,  -- 8 bytes
  parent_span_id BYTEA,

  -- Timing
  start_timestamp TIMESTAMPTZ NOT NULL,
  start_nanos_fraction SMALLINT NOT NULL DEFAULT 0,
  duration_nanos BIGINT NOT NULL,

  -- Span metadata
  name TEXT NOT NULL,
  kind SMALLINT,
  status_code SMALLINT,
  status_message TEXT,
  trace_state TEXT,

  -- Flags and counts
  flags INTEGER DEFAULT 0,
  dropped_attributes_count INTEGER DEFAULT 0,
  dropped_events_count INTEGER DEFAULT 0,
  dropped_links_count INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partitioning by time
CREATE INDEX idx_spans_time ON spans_fact(start_timestamp, span_id);
CREATE INDEX idx_spans_trace ON spans_fact(trace_id);
CREATE INDEX idx_spans_resource ON spans_fact(resource_id);

-- Span attributes (typed)
CREATE TABLE span_attrs_string (
  span_id BIGINT NOT NULL REFERENCES spans_fact(span_id),
  key_id INT NOT NULL REFERENCES attribute_keys(key_id),
  value TEXT NOT NULL,
  PRIMARY KEY (span_id, key_id)
);

CREATE INDEX idx_span_attrs_string_lookup ON span_attrs_string(key_id, value);

-- Span attributes (catch-all)
CREATE TABLE span_attrs_other (
  span_id BIGINT PRIMARY KEY REFERENCES spans_fact(span_id),
  attributes JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_span_attrs_other_gin ON span_attrs_other USING GIN(attributes);
```

## Default Promoted Span Keys

Based on query analysis, promote these high-frequency span attribute keys:

### String Type

- `http.method` - Very low cardinality (~5), frequently queried
- `http.url` - High cardinality, but important for filtering
- `http.target` - High cardinality, but important for filtering
- `db.system` - Very low cardinality (~1-5), frequently queried
- `db.name` - Low cardinality, frequently queried
- `messaging.system` - Low cardinality
- `component` - Very low cardinality
- `peer.address` - Medium cardinality

### Integer Type

- `http.status_code` - Low cardinality (~100), heavily queried
- `response_size` - High cardinality, but useful for aggregations
- `request_size` - High cardinality, but useful for aggregations

### Boolean Type

- `error` - Boolean flag, frequently queried

### Keep in JSONB

- `db.statement` - Very high cardinality, text-search needed
- `user_agent` - High cardinality
- `guid:x-request-id` - Unique per request
- `upstream_cluster` - Medium cardinality, not frequently queried alone

## Configuration File Format

### Complete Example

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollyscale-receiver-config
data:
  attribute-config.yaml: |
    # Attribute normalization configuration
    # Keys listed here will be extracted from JSONB and stored in typed tables

    promoted_keys:
      resource:
        # OTEL Semantic Conventions - Service
        service.name: string
        service.namespace: string
        service.version: string
        service.instance.id: string  # Note: High cardinality, consider dropping instead

        # OTEL Semantic Conventions - Telemetry SDK
        telemetry.sdk.name: string
        telemetry.sdk.language: string
        telemetry.sdk.version: string
        telemetry.auto.version: string

        # OTEL Semantic Conventions - Kubernetes
        k8s.namespace.name: string
        k8s.deployment.name: string
        k8s.container.name: string
        k8s.node.name: string

        # OTEL Semantic Conventions - Host
        host.name: string
        host.arch: string

        # OTEL Semantic Conventions - Process
        process.pid: int

        # OTEL Semantic Conventions - Deployment
        deployment.environment: string

      span:
        # HTTP
        http.method: string
        http.status_code: int
        http.url: string
        http.target: string

        # Database
        db.system: string
        db.name: string
        db.user: string

        # Messaging
        messaging.system: string
        messaging.destination: string

        # Error tracking
        error: bool

        # Network
        net.peer.port: int

      log:
        log.level: string

      metric: {}

    dropped_keys:
      resource:
        # Drop ephemeral/high-cardinality Kubernetes IDs
        - k8s.pod.uid
        - k8s.pod.name
        - k8s.replicaset.uid
        - k8s.replicaset.name
        - k8s.deployment.uid

      span:
        # Drop very high cardinality request IDs
        - guid:x-request-id

      log: []
      metric: []

    # Advanced: Attribute transformations
    transformations:
      # Rename keys during ingestion
      renames:
        http.status: http.status_code

      # Default values
      defaults:
        deployment.environment: "unknown"
```

## Migration from Current Schema

### Phase 1: Preserve Old Behavior

1. Keep old `resource_dim` table with JSONB
2. Add new `resources_dim` + typed tables alongside
3. Dual-write to both schemas

### Phase 2: Migrate Queries

1. Update application to query new schema
2. Create views that union old and new schemas
3. Verify query performance

### Phase 3: Data Migration

1. Backfill `resources_dim` from `resource_dim`
2. Extract promoted keys into typed tables
3. Verify first_seen/last_seen preservation

### Phase 4: Cleanup

1. Drop old tables
2. Remove dual-write logic

## Performance Considerations

### Resource Deduplication with first_seen/last_seen

The upsert pattern maintains temporal information efficiently:

```sql
-- Example: 100k spans all reference same 10 resources
-- Old schema: 100k rows × ~500 bytes = 50MB of duplicated resource data
-- New schema:
--   - 10 resources_dim rows × ~100 bytes = 1KB
--   - ~50 resource_attrs_string rows × ~50 bytes = 2.5KB
--   - 100k span rows with resource_id reference × 8 bytes = 800KB
-- Total: ~803KB (94% reduction)
```

### Index Strategy

```sql
-- Frequently queried keys get direct indexes
CREATE INDEX idx_resource_attrs_service_name
  ON resource_attrs_string(value)
  WHERE key_id = (SELECT key_id FROM attribute_keys WHERE key = 'service.name');

-- Generic index for all promoted keys
CREATE INDEX idx_resource_attrs_string_lookup
  ON resource_attrs_string(key_id, value);

-- Rare keys stay in JSONB with GIN index
CREATE INDEX idx_resource_attrs_other_gin
  ON resource_attrs_other USING GIN(attributes);
```

## Testing Plan

1. **Unit Tests**: Attribute extraction, type detection, hash computation
2. **Integration Tests**: Full OTLP message processing with DB
3. **Performance Tests**: Benchmark ingestion rate, query performance
4. **Config Tests**: Validate ConfigMap parsing, dynamic key promotion
5. **Migration Tests**: Verify first_seen/last_seen preservation

## Rollout Plan

1. **Development**: Implement in feature branch, test with synthetic data
2. **Staging**: Deploy to staging cluster, monitor with OTEL Demo
3. **Canary**: Roll out to 10% of production traffic
4. **Production**: Full rollout with monitoring
5. **Optimization**: Tune indexes, adjust promoted keys based on usage
