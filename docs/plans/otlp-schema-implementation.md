# OTLP Schema Implementation Plan

**Status**: Design Phase  
**Branch**: `improve-data-model`  
**Breaking Change**: Yes - Complete schema and API overhaul

## Overview

This document outlines the complete implementation of the new OTLP-aligned schema with denormalized attribute tables for logs, traces, and metrics. This is a **major breaking change** that replaces the old schema entirely.

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
kubectl -n ollyscale logs -l app=ollyscale-receiver --tail=100

# Check API health:
kubectl -n ollyscale logs -l app=ollyscale-api --tail=100
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

Views provide backward compatibility layer and simplify queries by pre-joining attribute tables.

### 4. API Refactoring

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

### Dimension Tables (Shared)

#### `attribute_keys`
Central registry for all attribute key names across all signals.

```sql
CREATE TABLE attribute_keys (
    key_id BIGSERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE
);
CREATE UNIQUE INDEX idx_attribute_keys_key ON attribute_keys(key);
```

**Purpose**: Deduplicate attribute names, reduce storage, enable efficient joins.

#### `otel_resources_dim`
Resource identity with hash-based deduplication.

```sql
CREATE TABLE otel_resources_dim (
    resource_id BIGSERIAL PRIMARY KEY,
    resource_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 of all attributes
    service_name VARCHAR(255),                   -- Extracted for fast filtering
    service_namespace VARCHAR(255),              -- Extracted for fast filtering
    schema_url TEXT,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    dropped_attributes_count INTEGER NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX idx_otel_resources_hash ON otel_resources_dim(resource_hash);
CREATE INDEX idx_otel_resources_service ON otel_resources_dim(service_name, service_namespace);
```

**Key Design Decisions**:
- Hash includes ALL attributes for true deduplication
- `service.name` and `service.namespace` extracted for fast service filtering
- `first_seen`/`last_seen` track resource lifecycle

#### `otel_scopes_dim`
Instrumentation library/scope identity.

```sql
CREATE TABLE otel_scopes_dim (
    scope_id BIGSERIAL PRIMARY KEY,
    scope_hash VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(255),
    schema_url TEXT,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    dropped_attributes_count INTEGER NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX idx_otel_scopes_hash ON otel_scopes_dim(scope_hash);
CREATE INDEX idx_otel_scopes_name ON otel_scopes_dim(name);
```

### Resource Attribute Tables

Each type gets its own table for optimal storage and indexing:

```sql
-- otel_resource_attrs_string
CREATE TABLE otel_resource_attrs_string (
    resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id),
    key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
    value TEXT NOT NULL,
    PRIMARY KEY (resource_id, key_id)
);
CREATE INDEX idx_otel_resource_attrs_string_value ON otel_resource_attrs_string(key_id, value);

-- otel_resource_attrs_int (similar structure)
-- otel_resource_attrs_double (similar structure)
-- otel_resource_attrs_bool (similar structure)
-- otel_resource_attrs_bytes (similar structure)

-- otel_resource_attrs_other (JSONB catch-all)
CREATE TABLE otel_resource_attrs_other (
    resource_id BIGINT PRIMARY KEY REFERENCES otel_resources_dim(resource_id),
    attributes JSONB NOT NULL
);
CREATE INDEX idx_otel_resource_attrs_other_gin ON otel_resource_attrs_other USING GIN(attributes);
```

### Scope Attribute Tables

Identical structure to resource attributes but for scopes:
- `otel_scope_attrs_string`
- `otel_scope_attrs_int`
- `otel_scope_attrs_double`
- `otel_scope_attrs_bool`
- `otel_scope_attrs_bytes`
- `otel_scope_attrs_other`

---

## Signal-Specific Schemas

### 1. Logs

#### Fact Table: `otel_logs_fact`

```sql
CREATE TABLE otel_logs_fact (
    log_id BIGSERIAL PRIMARY KEY,

    -- Dimensions
    resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id),
    scope_id BIGINT REFERENCES otel_scopes_dim(scope_id),

    -- Timing
    time_unix_nano BIGINT NOT NULL,
    observed_time_unix_nano BIGINT NOT NULL,

    -- Severity
    severity_number SMALLINT REFERENCES log_severity_numbers(severity_number),
    severity_text TEXT,

    -- Body
    body_type_id SMALLINT REFERENCES log_body_types(body_type_id),
    body JSONB,

    -- Trace correlation
    trace_id VARCHAR(32),
    span_id_hex VARCHAR(16),
    trace_flags INTEGER,

    -- Metadata
    dropped_attributes_count INTEGER DEFAULT 0,
    flags INTEGER DEFAULT 0
);

CREATE INDEX idx_otel_logs_time ON otel_logs_fact(time_unix_nano DESC);
CREATE INDEX idx_otel_logs_resource ON otel_logs_fact(resource_id);
CREATE INDEX idx_otel_logs_severity ON otel_logs_fact(severity_number);
CREATE INDEX idx_otel_logs_trace ON otel_logs_fact(trace_id, span_id_hex);
```

#### Log Attribute Tables

```sql
-- otel_log_attrs_string, int, double, bool, bytes, other
-- Same pattern as resource attributes but FK to log_id
```

**Key Design**:
- No tenant/connection - those are resource attributes
- `body` stays JSONB (can be complex object)
- Trace correlation fields for APM workflows

### 2. Traces

#### Fact Table: `otel_spans_fact`

```sql
CREATE TABLE otel_spans_fact (
    span_id BIGSERIAL PRIMARY KEY,

    -- Dimensions
    resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id),
    scope_id BIGINT REFERENCES otel_scopes_dim(scope_id),

    -- Trace identity
    trace_id VARCHAR(32) NOT NULL,
    span_id_hex VARCHAR(16) NOT NULL,
    parent_span_id_hex VARCHAR(16),
    trace_state TEXT,

    -- Span identity
    name TEXT NOT NULL,
    kind_id SMALLINT REFERENCES span_kinds(kind_id),

    -- Timing
    start_time_unix_nano BIGINT NOT NULL,
    end_time_unix_nano BIGINT NOT NULL,

    -- Status
    status_code_id SMALLINT REFERENCES status_codes(status_code_id),
    status_message TEXT,

    -- Metadata
    dropped_attributes_count INTEGER DEFAULT 0,
    dropped_events_count INTEGER DEFAULT 0,
    dropped_links_count INTEGER DEFAULT 0,
    flags INTEGER DEFAULT 0
);

CREATE UNIQUE INDEX idx_otel_spans_trace_span ON otel_spans_fact(trace_id, span_id_hex);
CREATE INDEX idx_otel_spans_trace ON otel_spans_fact(trace_id);
CREATE INDEX idx_otel_spans_resource ON otel_spans_fact(resource_id);
CREATE INDEX idx_otel_spans_time ON otel_spans_fact(start_time_unix_nano DESC);
CREATE INDEX idx_otel_spans_parent ON otel_spans_fact(parent_span_id_hex) WHERE parent_span_id_hex IS NOT NULL;
```

#### Span Events & Links

```sql
CREATE TABLE otel_span_events (
    event_id BIGSERIAL PRIMARY KEY,
    span_id BIGINT NOT NULL REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    time_unix_nano BIGINT NOT NULL,
    dropped_attributes_count INTEGER DEFAULT 0
);

CREATE TABLE otel_span_links (
    link_id BIGSERIAL PRIMARY KEY,
    span_id BIGINT NOT NULL REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,
    linked_trace_id VARCHAR(32) NOT NULL,
    linked_span_id_hex VARCHAR(16) NOT NULL,
    trace_state TEXT,
    dropped_attributes_count INTEGER DEFAULT 0
);
```

#### Span Attribute Tables

Same pattern as logs:
- `otel_span_attrs_string, int, double, bool, bytes, other`
- `otel_span_event_attrs_string, int, double, bool, bytes, other`
- `otel_span_link_attrs_string, int, double, bool, bytes, other`

### 3. Metrics

#### Metric Dimension: `otel_metrics_dim`

Metrics need a dimension table because same metric can have different descriptions/metadata.

```sql
CREATE TABLE otel_metrics_dim (
    metric_id BIGSERIAL PRIMARY KEY,
    metric_hash VARCHAR(64) NOT NULL UNIQUE,           -- Hash with description
    metric_identity_hash VARCHAR(64) NOT NULL,         -- Hash without description
    name VARCHAR(1024) NOT NULL,
    metric_type_id SMALLINT NOT NULL REFERENCES metric_types(metric_type_id),
    unit VARCHAR(64),
    aggregation_temporality_id SMALLINT REFERENCES aggregation_temporalities(temporality_id),
    is_monotonic BOOLEAN,
    description TEXT,
    schema_url TEXT,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX idx_otel_metrics_hash ON otel_metrics_dim(metric_hash);
CREATE INDEX idx_otel_metrics_identity ON otel_metrics_dim(metric_identity_hash);
CREATE INDEX idx_otel_metrics_name ON otel_metrics_dim(name);
```

**Key Design**:
- Two hashes: one with description (full identity), one without (groups variants)
- Enables metric variants with different descriptions

#### Fact Tables: `otel_metrics_data_points_*`

Separate tables for each metric type for optimal storage:

```sql
-- Gauge & Sum (number values)
CREATE TABLE otel_metrics_data_points_number (
    data_point_id BIGSERIAL PRIMARY KEY,
    metric_id BIGINT NOT NULL REFERENCES otel_metrics_dim(metric_id),
    resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id),
    scope_id BIGINT REFERENCES otel_scopes_dim(scope_id),
    start_time_unix_nano BIGINT,  -- NULL for gauges
    time_unix_nano BIGINT NOT NULL,
    value_int BIGINT,
    value_double DOUBLE PRECISION,
    flags INTEGER DEFAULT 0,
    exemplars JSONB,  -- Array of exemplars
    CONSTRAINT chk_value_one_of CHECK ((value_int IS NOT NULL) <> (value_double IS NOT NULL))
);

-- Histogram
CREATE TABLE otel_metrics_data_points_histogram (
    data_point_id BIGSERIAL PRIMARY KEY,
    metric_id BIGINT NOT NULL REFERENCES otel_metrics_dim(metric_id),
    resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id),
    scope_id BIGINT REFERENCES otel_scopes_dim(scope_id),
    start_time_unix_nano BIGINT NOT NULL,
    time_unix_nano BIGINT NOT NULL,
    count BIGINT NOT NULL,
    sum DOUBLE PRECISION,
    min DOUBLE PRECISION,
    max DOUBLE PRECISION,
    explicit_bounds DOUBLE PRECISION[] NOT NULL,
    bucket_counts BIGINT[] NOT NULL,
    flags INTEGER DEFAULT 0,
    exemplars JSONB
);

-- ExponentialHistogram
CREATE TABLE otel_metrics_data_points_exp_histogram (
    data_point_id BIGSERIAL PRIMARY KEY,
    metric_id BIGINT NOT NULL REFERENCES otel_metrics_dim(metric_id),
    resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id),
    scope_id BIGINT REFERENCES otel_scopes_dim(scope_id),
    start_time_unix_nano BIGINT NOT NULL,
    time_unix_nano BIGINT NOT NULL,
    count BIGINT NOT NULL,
    sum DOUBLE PRECISION,
    min DOUBLE PRECISION,
    max DOUBLE PRECISION,
    scale INTEGER NOT NULL,
    zero_count BIGINT NOT NULL,
    positive_offset INTEGER,
    positive_bucket_counts BIGINT[],
    negative_offset INTEGER,
    negative_bucket_counts BIGINT[],
    flags INTEGER DEFAULT 0,
    exemplars JSONB
);

-- Summary
CREATE TABLE otel_metrics_data_points_summary (
    data_point_id BIGSERIAL PRIMARY KEY,
    metric_id BIGINT NOT NULL REFERENCES otel_metrics_dim(metric_id),
    resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id),
    scope_id BIGINT REFERENCES otel_scopes_dim(scope_id),
    start_time_unix_nano BIGINT NOT NULL,
    time_unix_nano BIGINT NOT NULL,
    count BIGINT NOT NULL,
    sum DOUBLE PRECISION NOT NULL,
    quantile_values JSONB NOT NULL,  -- Array of {quantile, value}
    flags INTEGER DEFAULT 0
);
```

#### Metric Data Point Attribute Tables

Pattern for each metric type:
- `otel_metric_number_attrs_string, int, double, bool, bytes, other`
- `otel_metric_histogram_attrs_string, int, double, bool, bytes, other`
- `otel_metric_exp_histogram_attrs_string, int, double, bool, bytes, other`
- `otel_metric_summary_attrs_string, int, double, bool, bytes, other`

---

## Attribute Promotion Configuration

### Strategy

**Promoted Attributes** = Stored in typed tables for fast filtering/aggregation  
**Unpromoted Attributes** = Stored in JSONB catch-all table  
**Dropped Attributes** = Not stored at all (filtered out during ingestion)

### Configuration Architecture

**Two-Tier Configuration**:
1. **Base Configuration** (`config/attribute-promotion.yaml`) - Enforced, shipped with application, version controlled
2. **Admin Overrides** (ConfigMap → `/config/attribute-overrides.yaml`) - Deployment-specific customizations

**Merge Strategy**:
- Base promoted attributes are **always** promoted (cannot be removed)
- Admin can add additional promoted attributes (merged with base)
- Admin can drop specific attributes (takes precedence, attribute not stored)
- All configuration is version controlled and reviewed via git/ConfigMap changes

### Base Configuration File

`config/attribute-promotion.yaml` (enforced, shipped with application):

```yaml
# Attribute promotion configuration for OTLP schema
# Promoted attributes are stored in typed tables for fast queries

resource:
  string:
    - service.name
    - service.namespace
    - service.instance.id
    - deployment.environment
    - cloud.provider
    - cloud.region
    - cloud.availability_zone
    - k8s.cluster.name
    - k8s.namespace.name
    - k8s.pod.name
    - k8s.deployment.name
    - host.name
    - host.type
    - container.name
    - container.id

  int:
    - service.port

  # Other types: double, bool, bytes

scope:
  string:
    - otel.library.name
    - otel.library.version

logs:
  # Log-specific promoted attributes
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

  int:
    - http.status_code
    - rpc.grpc.status_code
    - gen_ai.usage.input_tokens
    - gen_ai.usage.output_tokens
    - gen_ai.usage.total_tokens

  double:
    - http.request.size
    - http.response.size
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

### Promotion Engine Implementation

```python
class AttributePromotionConfig:
    """Load and merge base config with admin overrides from files."""

    def __init__(
        self,
        base_config_path: Path,
        override_config_path: Path | None = None
    ):
        # Load base (enforced) configuration
        with base_config_path.open() as f:
            base_config = yaml.safe_load(f)

        # Load admin overrides (optional)
        admin_overrides = {}
        if override_config_path and override_config_path.exists():
            with override_config_path.open() as f:
                admin_overrides = yaml.safe_load(f) or {}

        # Build base promotion sets (enforced)
        self.base_resource = self._build_type_sets(base_config['resource'])
        self.base_scope = self._build_type_sets(base_config['scope'])
        self.base_logs = self._build_type_sets(base_config['logs'])
        self.base_spans = self._build_type_sets(base_config['spans'])
        self.base_metrics = self._build_type_sets(base_config['metrics'])

        # Merge with admin overrides
        promote_overrides = admin_overrides.get('promote', {})
        self.resource_promoted = self._merge_sets(
            self.base_resource,
            self._build_type_sets(promote_overrides.get('resource', {}))
        )
        self.scope_promoted = self._merge_sets(
            self.base_scope,
            self._build_type_sets(promote_overrides.get('scope', {}))
        )
        self.logs_promoted = self._merge_sets(
            self.base_logs,
            self._build_type_sets(promote_overrides.get('logs', {}))
        )
        self.spans_promoted = self._merge_sets(
            self.base_spans,
            self._build_type_sets(promote_overrides.get('spans', {}))
        )
        self.metrics_promoted = self._merge_sets(
            self.base_metrics,
            self._build_type_sets(promote_overrides.get('metrics', {}))
        )

        # Load drop lists (admin only, not in base config)
        drop_overrides = admin_overrides.get('drop', {})
        self.resource_dropped = set(drop_overrides.get('resource', []))
        self.scope_dropped = set(drop_overrides.get('scope', []))
        self.logs_dropped = set(drop_overrides.get('logs', []))
        self.spans_dropped = set(drop_overrides.get('spans', []))
        self.metrics_dropped = set(drop_overrides.get('metrics', []))

    def _build_type_sets(self, config: dict) -> dict[str, set[str]]:
        """Build {type: set(keys)} for fast lookups."""
        return {
            'string': set(config.get('string', [])),
            'int': set(config.get('int', [])),
            'double': set(config.get('double', [])),
            'bool': set(config.get('bool', [])),
            'bytes': set(config.get('bytes', [])),
        }

    def _merge_sets(
        self,
        base: dict[str, set[str]],
        overrides: dict[str, set[str]]
    ) -> dict[str, set[str]]:
        """Merge base and override sets (union)."""
        merged = {}
        for value_type in ['string', 'int', 'double', 'bool', 'bytes']:
            merged[value_type] = base.get(value_type, set()) | overrides.get(value_type, set())
        return merged

    def should_drop(self, signal: str, key: str) -> bool:
        """Check if attribute should be dropped (not stored at all)."""
        dropped = getattr(self, f"{signal}_dropped")
        return key in dropped

    def is_promoted(self, signal: str, key: str, value_type: str) -> bool:
        """Check if attribute key should be promoted (includes base + admin)."""
        if self.should_drop(signal, key):
            return False  # Dropped attributes are never promoted

        promoted = getattr(self, f"{signal}_promoted")
        return key in promoted.get(value_type, set())


class AttributeManager:
    """Manage attribute storage and promotion."""

    def __init__(self, config: AttributePromotionConfig, db_session):
        self.config = config
        self.db = db_session
        self.key_cache = {}  # {key_name: key_id}

    async def get_or_create_key_id(self, key: str) -> int:
        """Get or create attribute key, with caching."""
        if key in self.key_cache:
            return self.key_cache[key]

        # Try SELECT first
        result = await self.db.execute(
            "SELECT key_id FROM attribute_keys WHERE key = $1",
            key
        )
        if result:
            key_id = result[0]['key_id']
            self.key_cache[key] = key_id
            return key_id

        # INSERT if not exists
        key_id = await self.db.execute(
            "INSERT INTO attribute_keys (key) VALUES ($1) "
            "ON CONFLICT (key) DO UPDATE SET key = EXCLUDED.key "
            "RETURNING key_id",
            key
        )
        self.key_cache[key] = key_id
        return key_id

    async def store_attributes(
        self,
        signal: str,
        parent_id: int,
        parent_table: str,
        attributes: list[dict],
    ) -> None:
        """Store attributes in appropriate tables based on promotion config.

        Args:
            signal: 'resource', 'scope', 'logs', 'spans', 'metrics'
            parent_id: resource_id, scope_id, log_id, span_id, etc.
            parent_table: Table prefix (e.g., 'otel_log_attrs')
            attributes: OTLP attributes array [{key, value: {stringValue, ...}}]
        """
        promoted = {
            'string': [],
            'int': [],
            'double': [],
            'bool': [],
            'bytes': [],
        }
        unpromoted = {}

        for attr in attributes:
            key = attr['key']
            value_obj = attr['value']

            # Determine type and extract value
            value_type, value = self._extract_value(value_obj)

            # Check if promoted
            if self.config.is_promoted(signal, key, value_type):
                promoted[value_type].append({'key': key, 'value': value})
            else:
                # Store in JSONB catch-all
                unpromoted[key] = value_obj  # Keep OTLP AnyValue format

        # Insert promoted attributes
        for value_type, items in promoted.items():
            if not items:
                continue

            table = f"{parent_table}_{value_type}"

            for item in items:
                key_id = await self.get_or_create_key_id(item['key'])

                await self.db.execute(
                    f"INSERT INTO {table} (parent_id, key_id, value) "
                    f"VALUES ($1, $2, $3) "
                    f"ON CONFLICT (parent_id, key_id) DO UPDATE SET value = EXCLUDED.value",
                    parent_id, key_id, item['value']
                )

        # Insert unpromoted attributes
        if unpromoted:
            await self.db.execute(
                f"INSERT INTO {parent_table}_other (parent_id, attributes) "
                f"VALUES ($1, $2) "
                f"ON CONFLICT (parent_id) DO UPDATE SET attributes = EXCLUDED.attributes",
                parent_id, unpromoted
            )

    def _extract_value(self, value_obj: dict) -> tuple[str, Any]:
        """Extract (type, value) from OTLP AnyValue."""
        if 'string_value' in value_obj:
            return ('string', value_obj['string_value'])
        elif 'int_value' in value_obj:
            return ('int', value_obj['int_value'])
        elif 'double_value' in value_obj:
            return ('double', value_obj['double_value'])
        elif 'bool_value' in value_obj:
            return ('bool', value_obj['bool_value'])
        elif 'bytes_value' in value_obj:
            return ('bytes', value_obj['bytes_value'])
        elif 'array_value' in value_obj or 'kvlist_value' in value_obj:
            return ('other', value_obj)  # Complex types go to JSONB
        else:
            return ('other', value_obj)
```

---

## Resource/Scope Management

### Deduplication Strategy

**Hash Calculation**:
```python
import hashlib
import json

def calculate_resource_hash(attributes: list[dict]) -> str:
    """Calculate SHA-256 hash of resource attributes for deduplication.

    Hash must be stable:
    - Sort attributes by key
    - Use canonical JSON representation
    """
    # Sort by key for stable hash
    sorted_attrs = sorted(attributes, key=lambda a: a['key'])

    # Create canonical representation
    canonical = json.dumps(sorted_attrs, sort_keys=True, separators=(',', ':'))

    return hashlib.sha256(canonical.encode()).hexdigest()
```

### ResourceManager Implementation

```python
class ResourceManager:
    """Manage resource and scope dimensions with deduplication."""

    def __init__(self, db_session, attr_manager: AttributeManager):
        self.db = db_session
        self.attr_manager = attr_manager
        self.resource_cache = {}  # {hash: resource_id}
        self.scope_cache = {}  # {hash: scope_id}

    async def get_or_create_resource(self, resource: dict) -> int:
        """Get or create resource, returns resource_id."""
        attributes = resource.get('attributes', [])
        schema_url = resource.get('schema_url')
        dropped_count = resource.get('dropped_attributes_count', 0)

        # Calculate hash
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

---

## SQL Views for Query Simplification

Views join fact tables with attribute tables to provide a simpler query interface.

### Logs View

```sql
CREATE VIEW v_otel_logs_enriched AS
SELECT
    l.log_id,
    l.time_unix_nano,
    l.observed_time_unix_nano,
    l.severity_number,
    l.severity_text,
    l.body,
    l.trace_id,
    l.span_id_hex,

    -- Resource info
    r.resource_id,
    r.service_name,
    r.service_namespace,

    -- Scope info
    s.scope_id,
    s.name as scope_name,
    s.version as scope_version,

    -- Aggregated attributes (all promoted + unpromoted)
    COALESCE(
        (
            SELECT jsonb_object_agg(ak.key, a.value)
            FROM otel_log_attrs_string a
            JOIN attribute_keys ak ON a.key_id = ak.key_id
            WHERE a.log_id = l.log_id
        ) ||
        (SELECT jsonb_object_agg(ak.key, a.value::text)
         FROM otel_log_attrs_int a
         JOIN attribute_keys ak ON a.key_id = ak.key_id
         WHERE a.log_id = l.log_id
        ) ||
        -- ... other types ...
        (SELECT attributes FROM otel_log_attrs_other WHERE log_id = l.log_id),
        '{}'::jsonb
    ) as attributes

FROM otel_logs_fact l
JOIN otel_resources_dim r ON l.resource_id = r.resource_id
LEFT JOIN otel_scopes_dim s ON l.scope_id = s.scope_id;
```

### Traces View (Trace-Level Aggregation)

```sql
CREATE VIEW v_otel_traces AS
SELECT
    s.trace_id,
    MIN(s.start_time_unix_nano) as start_time_unix_nano,
    MAX(s.end_time_unix_nano) as end_time_unix_nano,
    MAX(s.end_time_unix_nano) - MIN(s.start_time_unix_nano) as duration_nanos,
    COUNT(*) as span_count,
    COUNT(*) FILTER (WHERE s.status_code_id = 2) as error_count,  -- ERROR status

    -- Root span info
    FIRST_VALUE(s.name) FILTER (WHERE s.parent_span_id_hex IS NULL)
        OVER (PARTITION BY s.trace_id ORDER BY s.start_time_unix_nano) as root_span_name,

    -- Resource/service info (from root span)
    FIRST_VALUE(r.service_name) FILTER (WHERE s.parent_span_id_hex IS NULL)
        OVER (PARTITION BY s.trace_id ORDER BY s.start_time_unix_nano) as service_name,
    FIRST_VALUE(r.service_namespace) FILTER (WHERE s.parent_span_id_hex IS NULL)
        OVER (PARTITION BY s.trace_id ORDER BY s.start_time_unix_nano) as service_namespace

FROM otel_spans_fact s
JOIN otel_resources_dim r ON s.resource_id = r.resource_id
GROUP BY s.trace_id;
```

### Spans View

```sql
CREATE VIEW v_otel_spans_enriched AS
SELECT
    s.span_id,
    s.trace_id,
    s.span_id_hex,
    s.parent_span_id_hex,
    s.name,
    s.kind_id,
    sk.name as kind_name,
    s.start_time_unix_nano,
    s.end_time_unix_nano,
    s.end_time_unix_nano - s.start_time_unix_nano as duration_nanos,
    s.status_code_id,
    sc.name as status_name,
    s.status_message,

    -- Resource
    r.resource_id,
    r.service_name,
    r.service_namespace,

    -- Scope
    scope.scope_id,
    scope.name as scope_name,

    -- Aggregated attributes
    COALESCE(
        (SELECT jsonb_object_agg(ak.key, a.value)
         FROM otel_span_attrs_string a
         JOIN attribute_keys ak ON a.key_id = ak.key_id
         WHERE a.span_id = s.span_id)
        || -- ... other types ...
        (SELECT attributes FROM otel_span_attrs_other WHERE span_id = s.span_id),
        '{}'::jsonb
    ) as attributes,

    -- Events (aggregated)
    (SELECT jsonb_agg(jsonb_build_object(
        'name', e.name,
        'time_unix_nano', e.time_unix_nano,
        'attributes', COALESCE(
            (SELECT jsonb_object_agg(ak.key, a.value)
             FROM otel_span_event_attrs_string a
             JOIN attribute_keys ak ON a.key_id = ak.key_id
             WHERE a.event_id = e.event_id),
            '{}'::jsonb
        )
    ))
     FROM otel_span_events e
     WHERE e.span_id = s.span_id
    ) as events,

    -- Links (aggregated)
    (SELECT jsonb_agg(jsonb_build_object(
        'trace_id', l.linked_trace_id,
        'span_id', l.linked_span_id_hex,
        'trace_state', l.trace_state,
        'attributes', COALESCE(
            (SELECT jsonb_object_agg(ak.key, a.value)
             FROM otel_span_link_attrs_string a
             JOIN attribute_keys ak ON a.key_id = ak.key_id
             WHERE a.link_id = l.link_id),
            '{}'::jsonb
        )
    ))
     FROM otel_span_links l
     WHERE l.span_id = s.span_id
    ) as links

FROM otel_spans_fact s
JOIN otel_resources_dim r ON s.resource_id = r.resource_id
LEFT JOIN otel_scopes_dim scope ON s.scope_id = scope.scope_id
LEFT JOIN span_kinds sk ON s.kind_id = sk.kind_id
LEFT JOIN status_codes sc ON s.status_code_id = sc.status_code_id;
```

### Metrics View

```sql
CREATE VIEW v_otel_metrics_number AS
SELECT
    dp.data_point_id,
    m.metric_id,
    m.name as metric_name,
    m.unit,
    mt.name as metric_type,
    dp.time_unix_nano,
    dp.start_time_unix_nano,
    COALESCE(dp.value_int, dp.value_double) as value,

    -- Resource
    r.service_name,
    r.service_namespace,

    -- Aggregated attributes
    COALESCE(
        (SELECT jsonb_object_agg(ak.key, a.value)
         FROM otel_metric_number_attrs_string a
         JOIN attribute_keys ak ON a.key_id = ak.key_id
         WHERE a.data_point_id = dp.data_point_id)
        || -- ... other types ...
        (SELECT attributes FROM otel_metric_number_attrs_other
         WHERE data_point_id = dp.data_point_id),
        '{}'::jsonb
    ) as attributes

FROM otel_metrics_data_points_number dp
JOIN otel_metrics_dim m ON dp.metric_id = m.metric_id
JOIN metric_types mt ON m.metric_type_id = mt.metric_type_id
JOIN otel_resources_dim r ON dp.resource_id = r.resource_id;
```

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

```
app/routers/
  ├── traces.py      # Trace-level operations + log correlation
  ├── spans.py       # Span-level operations
  ├── logs.py        # Log search, retrieval, and trace/span correlation
  ├── metrics.py     # Metric queries
  └── ingest.py      # OTLP ingestion (unchanged)
```

---

## Storage Layer Refactoring

### Base Classes

```python
# app/storage/base.py

from abc import ABC, abstractmethod

class SignalStorage(ABC):
    """Base class for signal-specific storage implementations."""

    def __init__(self, db_session, resource_mgr, attr_mgr, config):
        self.db = db_session
        self.resource_mgr = resource_mgr
        self.attr_mgr = attr_mgr
        self.config = config

    @abstractmethod
    async def store(self, otlp_data: dict) -> int:
        """Store OTLP data, return count of stored items."""
        pass

    @abstractmethod
    async def search(self, filters: dict) -> list[dict]:
        """Search with filters, return results."""
        pass


class SemanticConventionDetector:
    """Detect semantic convention type from span attributes (DRY: shared logic)."""

    SEMANTIC_PREFIXES = {
        'ai_agent': ['gen_ai.', 'llm.'],
        'http': ['http.', 'url.'],
        'db': ['db.'],
        'messaging': ['messaging.'],
        'rpc': ['rpc.'],
        'faas': ['faas.'],
        'aws': ['aws.'],
        'gcp': ['gcp.'],
        'azure': ['az.'],
    }

    @classmethod
    def detect_type(cls, attributes: dict) -> str | None:
        """Detect semantic convention type from attributes.

        Returns semantic type name or None if no match.
        Used by API layer to add hints for UI presentation.
        """
        for semantic_type, prefixes in cls.SEMANTIC_PREFIXES.items():
            for attr_key in attributes.keys():
                if any(attr_key.startswith(prefix) for prefix in prefixes):
                    return semantic_type
        return None
```

### Implementation Structure

```python
# app/storage/logs_storage.py

class LogsStorage(SignalStorage):
    """Logs-specific storage implementation."""

    async def store(self, resource_logs: list[dict]) -> int:
        """Store OTLP logs in new schema."""
        count = 0

        for rl in resource_logs:
            # 1. Get or create resource
            resource_id = await self.resource_mgr.get_or_create_resource(
                rl['resource']
            )

            # 2. Process each scope_logs
            for sl in rl.get('scope_logs', []):
      **Unit tests**: Config loading, validation, type inference
- [ ] Implement `AttributeManager` class (DRY: shared across all signals)
- [ ] **Unit tests**: Attribute promotion, key caching, type extraction
- [ ] Implement `ResourceManager` class (DRY: shared hash/dedup logic)
- [ ] **Unit tests**: Hash calculation consistency, deduplication, cache behavior
- [ ] **Deploy**: `task deploy` - verify no regressions
- [ ] **Code review**: Check DRY compliance before proceeding
                )

                # 3. Process log records
                for log in sl['log_records']:
                    # Insert log fact
                    log_id = await self._insert_log_fact(
                        log, resource_id, scope_id
                    )

                    # Store attributes
                    if 'attributes' in log:
                        await self.attr_mgr.store_attributes(
                            signal='logs',
                            parent_id=log_id,
                            parent_table='otel_log_attrs',
                            attributes=log['attributes']
                        )

                    count += 1

        return count

    async def _insert_log_fact(self, log: dict, resource_id: int, scope_id: int) -> int:
        """Insert log fact row, return log_id."""
        return await self.db.execute(
            """
            INSERT INTO otel_logs_fact (
                resource_id, scope_id,
                time_unix_nano, observed_time_unix_nano,
                severity_number, severity_text,
                body_type_id, body,
                trace_id, span_id_hex, trace_flags,
                dropped_attributes_count, flags
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING log_id
            """,
            resource_id, scope_id,
            log['time_unix_nano'], log['observed_time_unix_nano'],
            log.get('severity_number'), log.get('severity_text'),
            self._get_body_type_id(log.get('body')), log.get('body'),
            log.get('trace_id'), log.get('span_id'), log.get('flags'),
            log.get('dropped_attributes_count', 0), log.get('flags', 0)
        )

    async def search(self, filters: dict) -> list[dict]:
        """Search logs using view with attribute filters."""
        # Build query using v_otel_logs_enriched view
        # Apply attribute filters using JSONB operators
        # ...


# app/storage/traces_storage.py

class TracesStorage(SignalStorage):
    """Traces-specific storage implementation."""

    async def search(self, filters: dict) -> list[dict]:
        """Search spans with semantic convention filtering."""
        # Build query using v_otel_spans_enriched view
        # If semantic_type filter present, add WHERE clause for attribute prefixes
        # Example: semantic_type=ai_agent -> WHERE attributes ? 'gen_ai.system'
        results = await self._execute_query(filters)

        # Enrich results with semantic_type hint for UI
        for span in results:
            span['semantic_type'] = SemanticConventionDetector.detect_type(
                span.get('attributes', {})
            )

        return results
```

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
- [x] Update logs API: `/api/logs` with attribute filters
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
- [x] Update API: `/api/traces` (list) and `/api/traces/{trace_id}/spans` (details)
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
- [ ] Update metrics API: `/api/metrics/series`, `/api/metrics/{name}/labels` (NEXT)
- [ ] **Unit tests**: API responses, aggregation correctness (NEXT)
- [ ] **Integration tests**: Metric ingestion → query → label exploration (NEXT)
- [x] **Deploy**: `task deploy` - verify metrics work
- [x] **Validation**: Test all metric types (gauge, sum, histogram, exp_histogram, summary)

### Phase 5: Optimizations & Cleanup (Week 5)
**Commit Strategy**: Single commit for entire phase upon completion
**NOTE**: This is the first phase that modifies existing code (removes old schema)

- [ ] Add database partitioning for fact tables
- [ ] **Tests**: Verify partition pruning works
- [ ] Query performance tuning (EXPLAIN ANALYZE on slow queries)
- [ ] **Benchmarks**: Measure query latency improvements
- [ ] Remove old schema models/tables
- [ ] **Tests**: Update remaining tests to use new schema
- [ ] Update documentation (API docs, architecture docs)
- [ ] **Deploy**: `task deploy` - final production validation
- [ ] **Final validation**: Full end-to-end smoke test of all signals
- [ ] Performance benchmarks (document improvements vs old schema)
- [ ] **Code review**: Final DRY compliance check, remove any duplication

---

## Migration from Old Schema

Since this is a **breaking change**, migration is simple:

1. **Deploy new code**: Schema already exists (migrations ran successfully)
2. **Start fresh**: No data migration - new data goes to new schema
3. **Old data**: Can remain in old tables or be dropped
4. **Cutover**: Simply deploy new API version

**No dual-write complexity** - clean break from old schema.

---

## Performance Considerations

### Attribute Table Indexes

Critical indexes for promoted attributes:
```sql
-- String attributes (for filtering)
CREATE INDEX idx_log_attrs_string_key_value ON otel_log_attrs_string(key_id, value);

-- Int attributes (for range queries)
CREATE INDEX idx_span_attrs_int_key_value ON otel_span_attrs_int(key_id, value);

-- Composite for multi-attribute filters
CREATE INDEX idx_log_attrs_string_multi ON otel_log_attrs_string(log_id, key_id, value);
```

### Query Patterns

**Efficient**: Filter on promoted attributes
```sql
-- Fast: Uses index on key_id + value
SELECT l.* FROM otel_logs_fact l
JOIN otel_log_attrs_string a ON l.log_id = a.log_id
JOIN attribute_keys ak ON a.key_id = ak.key_id
WHERE ak.key = 'http.status_code' AND a.value = '500';
```

**Less Efficient**: Filter on unpromoted attributes
```sql
-- Slower: JSONB GIN index scan
SELECT * FROM otel_logs_fact l
JOIN otel_log_attrs_other o ON l.log_id = o.log_id
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
kubectl get pods -n ollyscale -l app=ollyscale-api
kubectl logs -n ollyscale -l app=ollyscale-api --tail=100

# OTLP Receiver pods (gRPC/HTTP ingestion on port 4317/4318)
kubectl get pods -n ollyscale -l app=ollyscale-otlp-receiver
kubectl logs -n ollyscale -l app=ollyscale-otlp-receiver --tail=100

# Web UI pods (React SPA served by nginx)
kubectl get pods -n ollyscale -l app=ollyscale-webui
kubectl logs -n ollyscale -l app=ollyscale-webui --tail=100

# OpAMP Server pods (agent configuration management)
kubectl get pods -n ollyscale -l app=ollyscale-opamp-server
kubectl logs -n ollyscale -l app=ollyscale-opamp-server --tail=100

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
