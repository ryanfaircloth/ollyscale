# OTLP Schema Implementation - Fresh Start Plan

**Branch**: `otlp-schema-v2` (NEW - Clean Start)  
**Status**: NOT STARTED  
**Date**: February 5, 2026

---

## Executive Summary

Complete OTLP-aligned schema implementation in **5 strict phases** with **mandatory test-first approach**. Each phase must be 100% complete with full test coverage before moving to the next.

**Key Changes from Failed Branch:**
- ✅ Test-first development (write tests BEFORE code)
- ✅ Strict phase ordering (no jumping ahead)
- ✅ Complete migrations (all 66 tables, not just 20)
- ✅ Use existing PostgreSQL testcontainer infrastructure
- ✅ Deploy ONLY after all tests pass
- ✅ Verification after every phase

**Timeline**: 2-3 weeks (vs 1 week attempted, failed)

---

## Non-Negotiable Rules

### Rule 1: Test-First Development
```
ALWAYS:
1. Write failing test
2. Write minimal code to pass test
3. Write more tests (edge cases)
4. Refactor if needed
5. All tests pass
6. THEN deploy

NEVER:
- Write code without tests
- Deploy without tests passing
- Move to next phase with tests failing
```

### Rule 2: Phase Order Is Mandatory
```
Phase N complete means:
- ALL code implemented
- ALL tests passing (>90% coverage)
- task test:api passes
- task deploy succeeds
- Verification in K8s succeeds
- Documentation updated
- Git commit: "Phase N complete"

Only then: Begin Phase N+1
```

### Rule 3: Use Existing Infrastructure
```
✅ Use: PostgreSQL testcontainers (conftest.py)
✅ Use: Alembic migrations
✅ Use: SQLModel ORM
✅ Use: pytest fixtures

❌ Never: SQLite
❌ Never: Custom test infrastructure
❌ Never: Alternative database types
```

### Rule 4: DRY Code
```
Extract common patterns:
- Hash calculation (resources, scopes)
- Attribute promotion logic
- Cache management
- Session handling
- Test fixtures

Create shared utilities:
- app/storage/utils/hashing.py
- app/storage/utils/caching.py
- tests/helpers/fixtures.py
```

### Rule 5: Verify After Every Step
```
After each function/class:
1. Run its unit tests
2. Run full test suite
3. Check for regressions
4. Fix immediately

After each phase:
1. task deploy
2. Check migration logs
3. Check receiver logs
4. Run smoke test
5. Query database
```

---

## Phase 0: Complete Database Foundation

**Goal**: All 66 tables exist with proper migrations, ORM models, and COMMENT statements

### Tasks

#### Task 0.1: Complete Migration 8316334b1935

**File**: `apps/api/alembic/versions/8316334b1935_create_otlp_schema.py`

**Add:**

1. **Reference Tables (6 tables)**
   ```sql
   log_severity_numbers (25 rows of seed data)
   log_body_types (8 rows)
   span_kinds (6 rows)
   status_codes (3 rows)
   metric_types (5 rows)
   aggregation_temporalities (3 rows)
   ```

2. **Resource Attribute Tables (6 tables)**
   ```sql
   otel_resource_attrs_string
   otel_resource_attrs_int
   otel_resource_attrs_double
   otel_resource_attrs_bool
   otel_resource_attrs_bytes
   otel_resource_attrs_other
   ```

3. **Scope Attribute Tables (6 tables)**
   ```sql
   otel_scope_attrs_string
   otel_scope_attrs_int
   otel_scope_attrs_double
   otel_scope_attrs_bool
   otel_scope_attrs_bytes
   otel_scope_attrs_other
   ```

4. **COMMENT Statements**
   - All tables: Purpose and OTLP spec reference
   - All nanos_fraction columns: Precision explanation
   - All hash columns: Deduplication strategy
   - All attribute tables: Promotion strategy

**Test**:
```bash
# Run migration
task deploy

# Verify all tables exist
kubectl exec -n ollyscale ollyscale-db-1 -- sh -c \
  "PGPASSWORD=postgres psql -U postgres -d ollyscale -c '\dt otel_*'"

# Count tables (should be 32)
kubectl exec -n ollyscale ollyscale-db-1 -- sh -c \
  "PGPASSWORD=postgres psql -U postgres -d ollyscale -c \
  \"SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'otel_%'\""

# Verify reference tables have seed data
kubectl exec -n ollyscale ollyscale-db-1 -- sh -c \
  "PGPASSWORD=postgres psql -U postgres -d ollyscale -c 'SELECT COUNT(*) FROM log_severity_numbers'"

# Check COMMENT statements exist
kubectl exec -n ollyscale ollyscale-db-1 -- sh -c \
  "PGPASSWORD=postgres psql -U postgres -d ollyscale -c '\dt+ otel_resources_dim'" | grep COMMENT
```

#### Task 0.2: Complete ORM Models

**File**: `apps/api/app/models/otlp_schema.py`

**Add:** ORM models for:
- All 6 reference tables
- All 12 resource/scope attribute tables
- Proper FK relationships
- Proper indexes

**Test**:
```python
# tests/test_otlp_schema_models.py
def test_all_models_exist():
    """Verify all 32 OTLP tables have ORM models."""
    from app.models.otlp_schema import (
        AttributeKey,
        LogSeverityNumber,
        LogBodyType,
        SpanKind,
        StatusCode,
        MetricType,
        AggregationTemporality,
        OtelResourcesDim,
        OtelScopesDim,
        OtelLogsFact,
        OtelSpansFact,
        # ... all 32 models
    )
    assert all models can be instantiated

def test_reference_table_relationships():
    """Verify FK relationships to reference tables."""
    # Test OtelLogsFact.severity_number FK
    # Test OtelSpansFact.kind FK
    # etc.
```

#### Task 0.3: Create Test Fixtures

**File**: `tests/helpers/otlp_fixtures.py`

**Create** helper functions:
```python
def create_test_resource(session, **attributes):
    """Create test resource with attributes."""

def create_test_scope(session, **attributes):
    """Create test scope."""

def create_test_log(session, resource_id, **kwargs):
    """Create test log record."""

def create_test_span(session, resource_id, **kwargs):
    """Create test span."""
```

**Test fixtures:**
```bash
uv run pytest tests/test_otlp_fixtures.py -v
# Should have 10+ tests validating fixture helpers
```

#### Phase 0 Success Criteria

- [ ] Migration 8316334b1935 has all 66 tables
- [ ] Migration 8316334b1935 has all COMMENT statements
- [ ] ORM models exist for all 32 OTLP tables
- [ ] 6 reference tables have seed data
- [ ] Test fixture helpers created with 10+ tests
- [ ] `task deploy` succeeds with no errors
- [ ] Can query all tables via kubectl exec psql
- [ ] Git commit: "Phase 0 complete - Full OTLP schema foundation"

**Estimated Time**: 1-2 days

---

## Phase 1: Managers with Full Test Coverage

**Goal**: ResourceManager and AttributeManager with 50+ tests combined

### Task 1.1: AttributePromotionConfig (Already Complete)

✅ **Status**: 12 tests passing, no changes needed

### Task 1.2: ResourceManager - Test-First

**Approach**: Write ALL tests first, then implement

#### Step 1: Write Test Skeleton

**File**: `tests/test_resource_manager.py`

```python
"""Resource Manager Tests - PostgreSQL testcontainer"""

import pytest
from app.storage.resource_manager import ResourceManager

class TestResourceHashing:
    """Test hash calculation for resources and scopes."""

    def test_resource_hash_deterministic(self, postgres_session):
        """Same attributes produce same hash."""
        pass  # Write assertion first

    def test_resource_hash_order_independent(self, postgres_session):
        """Hash independent of attribute order."""
        pass

    def test_resource_hash_changes_with_values(self, postgres_session):
        """Different attributes produce different hash."""
        pass

    def test_scope_hash_deterministic(self, postgres_session):
        """Same scope produces same hash."""
        pass

class TestResourceDeduplication:
    """Test resource dimension deduplication."""

    def test_get_or_create_resource_creates_new(self, postgres_session):
        """First call creates new resource."""
        pass

    def test_get_or_create_resource_returns_existing(self, postgres_session):
        """Second call returns same resource_id."""
        pass

    def test_service_name_extracted(self, postgres_session):
        """service.name attribute extracted to service_name column."""
        pass

    def test_service_namespace_extracted(self, postgres_session):
        """service.namespace attribute extracted."""
        pass

class TestScopeDeduplication:
    """Test scope dimension deduplication."""

    def test_get_or_create_scope_creates_new(self, postgres_session):
        pass

    def test_get_or_create_scope_returns_existing(self, postgres_session):
        pass

    def test_scope_without_version(self, postgres_session):
        """Handle scope with no version."""
        pass

class TestResourceCaching:
    """Test resource caching behavior."""

    def test_cache_hit_avoids_query(self, postgres_session):
        pass

    def test_cache_miss_queries_db(self, postgres_session):
        pass

class TestAttributeStorage:
    """Test resource/scope attribute storage in typed tables."""

    def test_store_string_attribute(self, postgres_session):
        """String attributes go to otel_resource_attrs_string."""
        pass

    def test_store_int_attribute(self, postgres_session):
        pass

    def test_store_double_attribute(self, postgres_session):
        pass

    def test_store_bool_attribute(self, postgres_session):
        pass

    def test_store_bytes_attribute(self, postgres_session):
        pass

    def test_store_complex_attribute(self, postgres_session):
        """Complex types go to otel_resource_attrs_other (JSONB)."""
        pass
```

**Run tests (all should fail - no implementation yet):**
```bash
uv run pytest tests/test_resource_manager.py -v
# Expected: 25 failed tests
```

#### Step 2: Implement ResourceManager

**File**: `apps/api/app/storage/resource_manager.py`

**Implement to pass tests:**
- `calculate_resource_hash()` function
- `calculate_scope_hash()` function
- `get_or_create_resource()` method
- `get_or_create_scope()` method
- `_extract_service_name()` helper
- `_extract_service_namespace()` helper
- `_store_resource_attributes()` method
- `_store_scope_attributes()` method
- Resource cache (dict)
- Scope cache (dict)

**Run tests after each method:**
```bash
# After calculate_resource_hash
uv run pytest tests/test_resource_manager.py::TestResourceHashing -v

# After get_or_create_resource
uv run pytest tests/test_resource_manager.py::TestResourceDeduplication -v

# Continue until all pass
uv run pytest tests/test_resource_manager.py -v
# Expected: 25 passed
```

### Task 1.3: AttributeManager - Test-First

**File**: `tests/test_attribute_manager.py`

```python
"""Attribute Manager Tests"""

class TestKeyManagement:
    """Test attribute key registry."""

    def test_get_or_create_key_creates_new(self, postgres_session):
        pass

    def test_get_or_create_key_returns_existing(self, postgres_session):
        pass

    def test_keys_cached(self, postgres_session):
        pass

class TestTypeExtraction:
    """Test OTLP AnyValue type extraction."""

    def test_extract_string_value(self, postgres_session):
        """Extract from AnyValue.string_value."""
        pass

    def test_extract_int_value(self, postgres_session):
        pass

    def test_extract_double_value(self, postgres_session):
        pass

    def test_extract_bool_value(self, postgres_session):
        pass

    def test_extract_bytes_value(self, postgres_session):
        pass

    def test_extract_array_value(self, postgres_session):
        """Arrays go to JSONB."""
        pass

    def test_extract_kvlist_value(self, postgres_session):
        """KVList goes to JSONB."""
        pass

class TestPromotionLogic:
    """Test attribute promotion decisions."""

    def test_is_promoted_semantic_convention(self, postgres_session):
        """http.method is promoted for spans."""
        pass

    def test_is_not_promoted_unknown_key(self, postgres_session):
        """Unknown keys not promoted."""
        pass

    def test_is_not_promoted_wrong_signal(self, postgres_session):
        """log.level for spans not promoted (wrong signal)."""
        pass

class TestAttributeRouting:
    """Test routing to correct typed table."""

    def test_route_to_string_table(self, postgres_session):
        pass

    def test_route_to_int_table(self, postgres_session):
        pass

    def test_route_to_jsonb_table(self, postgres_session):
        """Unpromoted or complex go to _other table."""
        pass
```

**Run tests (should fail):**
```bash
uv run pytest tests/test_attribute_manager.py -v
# Expected: 20 failed tests
```

**Implement AttributeManager to pass tests**

**Run tests:**
```bash
uv run pytest tests/test_attribute_manager.py -v
# Expected: 20 passed
```

#### Phase 1 Success Criteria

- [ ] ResourceManager: 25+ tests passing
- [ ] AttributeManager: 20+ tests passing
- [ ] AttributePromotionConfig: 12 tests passing (existing)
- [ ] Total: 57+ tests passing
- [ ] `task test:api` passes with no regressions
- [ ] Code coverage >90% for both managers
- [ ] `task deploy` succeeds
- [ ] No errors in receiver logs
- [ ] Git commit: "Phase 1 complete - Managers with full test coverage"

**Estimated Time**: 2-3 days

---

## Phase 2: LogsStorage with Full Test Coverage

**Goal**: Complete logs ingestion and query with 30+ tests

### Task 2.1: LogsStorage - Test-First

**File**: `tests/test_logs_storage.py`

```python
"""Logs Storage Tests"""

class TestLogIngestion:
    """Test OTLP log ingestion."""

    def test_store_simple_log(self, postgres_session):
        """Store log with minimal fields."""
        pass

    def test_store_log_with_trace_correlation(self, postgres_session):
        """Store log with trace_id and span_id."""
        pass

    def test_store_log_with_attributes(self, postgres_session):
        """Promoted attributes go to typed tables."""
        pass

    def test_store_log_batch(self, postgres_session):
        """Store multiple logs efficiently."""
        pass

    def test_timestamp_nanos_precision(self, postgres_session):
        """Verify nanos_fraction stored correctly."""
        pass

class TestLogSearch:
    """Test log search queries."""

    def test_search_by_time_range(self, postgres_session):
        pass

    def test_search_by_severity(self, postgres_session):
        pass

    def test_search_by_service(self, postgres_session):
        pass

    def test_search_by_attribute(self, postgres_session):
        """Filter by promoted attribute."""
        pass

class TestTraceCorrelation:
    """Test log-trace correlation."""

    def test_get_logs_by_trace_id(self, postgres_session):
        pass

    def test_get_logs_by_span_id(self, postgres_session):
        pass

    def test_get_logs_grouped_by_span(self, postgres_session):
        pass

class TestResourceDeduplication:
    """Test resource reuse across logs."""

    def test_same_resource_reused(self, postgres_session):
        """Multiple logs with same resource share resource_id."""
        pass

    def test_different_resources_separate(self, postgres_session):
        pass
```

**Run tests (should fail):**
```bash
uv run pytest tests/test_logs_storage.py -v
# Expected: 30 failed tests
```

**Implement LogsStorage to pass tests**

**File**: `apps/api/app/storage/logs_storage.py`

**Implement:**
- `__init__()` with ResourceManager, AttributeManager
- `store_resource_logs()` method
- `_store_single_log()` helper
- `_store_log_attributes()` helper
- `search_logs()` method with filters
- `get_logs_by_trace()` method
- `get_logs_by_span()` method

**Run tests after each method:**
```bash
uv run pytest tests/test_logs_storage.py::TestLogIngestion -v
uv run pytest tests/test_logs_storage.py::TestLogSearch -v
uv run pytest tests/test_logs_storage.py -v
# Expected: 30 passed
```

### Task 2.2: Integration Test

**File**: `tests/test_logs_integration.py`

```python
def test_otlp_logs_end_to_end(postgres_session):
    """Full OTLP logs → storage → query cycle."""
    # 1. Create OTLP ResourceLogs proto
    # 2. Store via LogsStorage
    # 3. Query via search_logs()
    # 4. Verify attributes in typed tables
    # 5. Verify resource deduplication
    assert logs_retrieved
```

**Run:**
```bash
uv run pytest tests/test_logs_integration.py -v
# Expected: 1 passed
```

#### Phase 2 Success Criteria

- [ ] LogsStorage: 30+ tests passing
- [ ] Integration test passing
- [ ] `task test:api` passes (no regressions)
- [ ] Code coverage >90% for LogsStorage
- [ ] `task deploy` succeeds
- [ ] Can send OTLP logs via grpcurl
- [ ] Can query logs via API
- [ ] Verify in database: logs in otel_logs_fact
- [ ] Verify: attributes in typed tables
- [ ] Verify: resources deduplicated
- [ ] Git commit: "Phase 2 complete - LogsStorage with full test coverage"

**Estimated Time**: 3-4 days

---

## Phase 3: TracesStorage with Full Test Coverage

**Goal**: Complete spans ingestion with 30+ tests

### Task 3.1: TracesStorage - Test-First

**File**: `tests/test_traces_storage.py`

```python
"""Traces Storage Tests"""

class TestSpanIngestion:
    def test_store_simple_span(self, postgres_session):
        pass

    def test_store_span_with_parent(self, postgres_session):
        """Store span with parent_span_id."""
        pass

    def test_store_span_with_events(self, postgres_session):
        """Events stored as JSONB."""
        pass

    def test_store_span_with_links(self, postgres_session):
        """Links stored as JSONB."""
        pass

    def test_store_span_with_attributes(self, postgres_session):
        pass

    def test_timestamp_nanos_precision(self, postgres_session):
        """Both start and end times."""
        pass

class TestSpanSearch:
    def test_search_by_trace_id(self, postgres_session):
        pass

    def test_search_by_service(self, postgres_session):
        pass

    def test_search_by_time_range(self, postgres_session):
        pass

class TestTraceRetrieval:
    def test_get_trace_spans(self, postgres_session):
        """Get all spans for trace."""
        pass

    def test_get_root_span(self, postgres_session):
        """Identify root span (no parent)."""
        pass

    def test_get_child_spans(self, postgres_session):
        """Find children of span."""
        pass

class TestSpanRelationships:
    def test_parent_child_relationship(self, postgres_session):
        pass

    def test_trace_tree_structure(self, postgres_session):
        """Build full trace tree."""
        pass

class TestStatusHandling:
    def test_span_status_ok(self, postgres_session):
        pass

    def test_span_status_error(self, postgres_session):
        pass
```

**Run tests (should fail):**
```bash
uv run pytest tests/test_traces_storage.py -v
# Expected: 30 failed tests
```

**Implement TracesStorage to pass tests**

**Run tests:**
```bash
uv run pytest tests/test_traces_storage.py -v
# Expected: 30 passed
```

### Task 3.2: Integration Test

**File**: `tests/test_traces_integration.py`

```python
def test_otlp_traces_end_to_end(postgres_session):
    """Full OTLP traces → storage → query cycle."""
    # 1. Create OTLP ResourceSpans with multiple spans
    # 2. Store via TracesStorage
    # 3. Query by trace_id
    # 4. Verify parent-child relationships
    # 5. Verify attributes routed correctly
    assert trace_complete
```

**Run:**
```bash
uv run pytest tests/test_traces_integration.py -v
# Expected: 1 passed
```

#### Phase 3 Success Criteria

- [ ] TracesStorage: 30+ tests passing
- [ ] Integration test passing
- [ ] `task test:api` passes
- [ ] Code coverage >90%
- [ ] `task deploy` succeeds
- [ ] Can send OTLP traces via grpcurl
- [ ] Can query traces via API
- [ ] Verify spans in database with parent relationships
- [ ] Verify attributes in typed tables
- [ ] Git commit: "Phase 3 complete - TracesStorage with full test coverage"

**Estimated Time**: 3-4 days

---

## Phase 4: MetricsStorage with Full Test Coverage

**Goal**: All 5 metric types working with 25+ tests

### Task 4.1: Complete Metrics Tables (if not done in Phase 0)

**Migration**: Add if missing:
- `otel_metrics_dim`
- `otel_metrics_data_points_number`
- `otel_metrics_data_points_histogram`
- `otel_metrics_data_points_exp_histogram`
- `otel_metrics_data_points_summary`
- 24 metric data point attribute tables (4 DP types × 6 attr types)

### Task 4.2: MetricsStorage - Test-First

**File**: `tests/test_metrics_storage.py`

```python
"""Metrics Storage Tests"""

class TestGaugeMetrics:
    def test_store_gauge_int(self, postgres_session):
        pass

    def test_store_gauge_double(self, postgres_session):
        pass

    def test_gauge_no_start_time(self, postgres_session):
        """Gauges have NULL start_time."""
        pass

class TestSumMetrics:
    def test_store_sum_monotonic(self, postgres_session):
        pass

    def test_store_sum_non_monotonic(self, postgres_session):
        pass

    def test_sum_aggregation_temporality(self, postgres_session):
        pass

class TestHistogramMetrics:
    def test_store_histogram(self, postgres_session):
        pass

    def test_histogram_explicit_bounds(self, postgres_session):
        pass

    def test_histogram_bucket_counts(self, postgres_session):
        pass

class TestExpHistogramMetrics:
    def test_store_exp_histogram(self, postgres_session):
        pass

    def test_exp_histogram_scale(self, postgres_session):
        pass

class TestSummaryMetrics:
    def test_store_summary(self, postgres_session):
        pass

    def test_summary_quantiles(self, postgres_session):
        pass

class TestMetricSearch:
    def test_search_by_name(self, postgres_session):
        pass

    def test_search_by_time_range(self, postgres_session):
        pass

    def test_search_by_service(self, postgres_session):
        pass
```

**Run tests (should fail):**
```bash
uv run pytest tests/test_metrics_storage.py -v
# Expected: 25 failed tests
```

**Implement MetricsStorage to pass tests**

**Run tests:**
```bash
uv run pytest tests/test_metrics_storage.py -v
# Expected: 25 passed
```

### Task 4.3: Integration Test

**File**: `tests/test_metrics_integration.py`

```python
def test_otlp_metrics_all_types(postgres_session):
    """Test all 5 metric types end-to-end."""
    # Send gauge, sum, histogram, exp_histogram, summary
    # Query each type
    # Verify storage in correct DP table
    assert all_types_work
```

#### Phase 4 Success Criteria

- [ ] MetricsStorage: 25+ tests passing
- [ ] Integration test passing
- [ ] All 5 metric types work
- [ ] `task test:api` passes
- [ ] Code coverage >90%
- [ ] `task deploy` succeeds
- [ ] Can send all OTLP metric types
- [ ] Can query metrics via API
- [ ] Verify data in correct DP tables
- [ ] Git commit: "Phase 4 complete - MetricsStorage with full test coverage"

**Estimated Time**: 3-4 days

---

## Phase 5: OtlpStorage Wrapper & Receiver Integration

**Goal**: Complete end-to-end OTLP ingestion with 15+ tests

### Task 5.1: OtlpStorage - Test-First

**File**: `tests/test_otlp_storage.py`

```python
"""OTLP Storage Wrapper Tests"""

class TestStorageInitialization:
    def test_init_creates_managers(self):
        pass

    def test_init_loads_config(self):
        pass

    def test_connect_creates_engines(self):
        pass

class TestLogsIngestion:
    def test_store_resource_logs(self, postgres_session):
        pass

    def test_multiple_resource_logs(self, postgres_session):
        pass

class TestTracesIngestion:
    def test_store_resource_spans(self, postgres_session):
        pass

    def test_multiple_resource_spans(self, postgres_session):
        pass

class TestMetricsIngestion:
    def test_store_resource_metrics(self, postgres_session):
        pass

    def test_multiple_resource_metrics(self, postgres_session):
        pass

class TestTransactionHandling:
    def test_commit_after_all_resources(self, postgres_session):
        """Single commit after processing all resources."""
        pass

    def test_rollback_on_error(self, postgres_session):
        pass

class TestEndToEnd:
    def test_mixed_signals(self, postgres_session):
        """Process logs, traces, metrics in one session."""
        pass
```

**Run tests (should fail):**
```bash
uv run pytest tests/test_otlp_storage.py -v
# Expected: 15 failed tests
```

**Implement OtlpStorage to pass tests**

**Run tests:**
```bash
uv run pytest tests/test_otlp_storage.py -v
# Expected: 15 passed
```

### Task 5.2: Receiver Integration

**File**: `apps/api/receiver/server.py`

**Update** to use OtlpStorage:
- Initialize OtlpStorage in startup
- Use for Export() calls
- Handle errors properly

**Test**: Manual OTLP send
```bash
# Send test trace
grpcurl -d @ -plaintext localhost:4317 \
  opentelemetry.proto.collector.trace.v1.TraceService/Export < test_trace.json

# Check database
kubectl exec -n ollyscale ollyscale-db-1 -- sh -c \
  "PGPASSWORD=postgres psql -U postgres -d ollyscale -c \
  'SELECT COUNT(*) FROM otel_spans_fact'"
```

#### Phase 5 Success Criteria

- [ ] OtlpStorage: 15+ tests passing
- [ ] Receiver integration complete
- [ ] `task test:api` passes
- [ ] Code coverage >90%
- [ ] `task deploy` succeeds
- [ ] Can send OTLP data via grpcurl (all 3 signals)
- [ ] Data appears in database
- [ ] Attributes routed to typed tables
- [ ] Resources deduplicated
- [ ] No errors in receiver logs
- [ ] Git commit: "Phase 5 complete - Full OTLP ingestion working"

**Estimated Time**: 2-3 days

---

## Phase 6: API Endpoints & Web UI

**Goal**: Complete v2 API and update Web UI

### Task 6.1: API Endpoints

**Files to create:**
- `apps/api/app/routers/logs_v2.py`
- `apps/api/app/routers/traces_v2.py`
- `apps/api/app/routers/metrics_v2.py`

**Endpoints**:
```
GET /api/v2/logs/search
GET /api/v2/logs/trace/{trace_id}
GET /api/v2/logs/trace/{trace_id}/span/{span_id}

GET /api/v2/traces/search
GET /api/v2/traces/{trace_id}
GET /api/v2/traces/{trace_id}/spans

GET /api/v2/metrics/search
GET /api/v2/metrics/series
```

**Tests**: `tests/test_api_endpoints_v2.py` (30+ tests)

### Task 6.2: Web UI Updates

**Files**:
- Update React query hooks to use /v2 endpoints
- Update type definitions
- Test all pages work

### Task 6.3: Remove Legacy Code

**After v2 verified working:**
- Remove v1 endpoints
- Remove old postgres_orm_sync.py storage
- Remove old database tables
- Update documentation

#### Phase 6 Success Criteria

- [ ] All v2 API endpoints working (30+ tests)
- [ ] Web UI fully functional
- [ ] Legacy code removed
- [ ] `task test:api` passes
- [ ] `task deploy` succeeds
- [ ] Full end-to-end smoke test passes
- [ ] Documentation updated
- [ ] Git commit: "Phase 6 complete - API & UI migration"

**Estimated Time**: 3-4 days

---

## Testing Strategy Summary

### Unit Tests (Per Phase)
```
Phase 0: 10+ tests (fixtures, models)
Phase 1: 57+ tests (config, managers)
Phase 2: 31+ tests (logs storage + integration)
Phase 3: 31+ tests (traces storage + integration)
Phase 4: 26+ tests (metrics storage + integration)
Phase 5: 15+ tests (otlp wrapper)
Phase 6: 30+ tests (API endpoints)

Total: 200+ tests
```

### Test Infrastructure

**Use existing:**
- `tests/conftest.py` - PostgreSQL testcontainer
- `tests/fixtures.py` - OTLP data factories

**Add:**
- `tests/helpers/otlp_fixtures.py` - Resource/scope/log/span helpers
- `tests/helpers/assertions.py` - Custom assertions

### Coverage Requirements

**Per class:**
- Unit test coverage: >90%
- Integration test: At least 1 per storage class
- API test: At least 2 per endpoint (success + error)

**Tools:**
```bash
# Run tests with coverage
uv run pytest --cov=app/storage --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

---

## Deployment Strategy

### After Each Phase

```bash
# 1. All tests pass locally
task test:api

# 2. Deploy to K8s
task deploy

# 3. Check migration
kubectl logs -n ollyscale -l app.kubernetes.io/component=migration --tail=50

# 4. Check receiver
kubectl logs -n ollyscale -l app.kubernetes.io/component=otlp-receiver --tail=100

# 5. Check API
kubectl logs -n ollyscale -l app.kubernetes.io/component=api --tail=100

# 6. Send test data
grpcurl -d @ -plaintext localhost:4317 \
  opentelemetry.proto.collector.trace.v1.TraceService/Export < test.json

# 7. Query database
kubectl exec -n ollyscale ollyscale-db-1 -- sh -c \
  "PGPASSWORD=postgres psql -U postgres -d ollyscale -c 'SELECT COUNT(*) FROM otel_spans_fact'"

# 8. If ANY error: Fix immediately, redeploy, retest
```

### Smoke Test Script

**File**: `scripts/smoke-test.sh`

```bash
#!/bin/bash
# Send sample OTLP data for all 3 signals
# Query each signal via API
# Verify counts match
# Exit 0 if pass, 1 if fail
```

---

## Success Metrics

### Code Quality
- [ ] <1000 lines per storage class
- [ ] >90% test coverage across all storage classes
- [ ] Zero circular dependencies
- [ ] All DRY rules followed

### Performance
- [ ] 10k+ spans/sec ingestion
- [ ] p95 query latency <100ms
- [ ] Storage efficiency: 30-40% reduction vs JSONB-only

### Completeness
- [ ] All 66 OTLP tables created
- [ ] All 5 metric types working
- [ ] All semantic conventions supported
- [ ] Full trace correlation working

---

## Timeline

### Week 1
- Days 1-2: Phase 0 (foundation)
- Days 3-5: Phase 1 (managers)

### Week 2
- Days 1-3: Phase 2 (logs)
- Days 4-5: Phase 3 start (traces)

### Week 3
- Days 1-2: Phase 3 complete (traces)
- Days 3-5: Phase 4 (metrics)

### Week 4
- Days 1-3: Phase 5 (otlp wrapper)
- Days 4-5: Phase 6 start (APIs)

### Week 5 (if needed)
- Days 1-3: Phase 6 complete
- Days 4-5: Cleanup, docs, optimization

**Total: 2-3 weeks**

---

## Git Commit Strategy

### Phase Commits
```
Phase 0 complete - Full OTLP schema foundation
Phase 1 complete - Managers with full test coverage
Phase 2 complete - LogsStorage with full test coverage
Phase 3 complete - TracesStorage with full test coverage
Phase 4 complete - MetricsStorage with full test coverage
Phase 5 complete - Full OTLP ingestion working
Phase 6 complete - API & UI migration
```

### Checkpoint Commits (Within Phases)
```
test: add ResourceManager test skeleton (25 failing tests)
feat: implement ResourceManager hash calculation (5 tests passing)
feat: implement ResourceManager deduplication (15 tests passing)
feat: implement ResourceManager caching (25 tests passing)
```

---

## Lessons Applied

### From Failed Branch

1. ✅ **Test-first**: Write tests BEFORE code
2. ✅ **Strict phases**: Complete Phase N before N+1
3. ✅ **Use existing infra**: PostgreSQL testcontainers, not SQLite
4. ✅ **Deploy after tests**: Never deploy untested code
5. ✅ **Verify after deploy**: Check logs, query database
6. ✅ **DRY code**: Extract common patterns
7. ✅ **Complete migrations**: All 66 tables, not just 20

### New Protections

1. **Automated checks**:
   ```bash
   # Pre-deploy check script
   #!/bin/bash
   if pytest --co -q | grep -q "0 tests"; then
     echo "ERROR: No tests for new code"
     exit 1
   fi
   ```

2. **Phase gate review**:
   - Before marking phase complete: Review checklist
   - All items must be ✅ before git commit

3. **Coverage enforcement**:
   ```bash
   # Fail if coverage <90%
   pytest --cov=app/storage --cov-fail-under=90
   ```

---

## Final Checklist Before Starting

- [ ] Read entire plan
- [ ] Understand all 6 phases
- [ ] Understand test-first approach
- [ ] Reviewed conftest.py (PostgreSQL testcontainer)
- [ ] Reviewed existing test patterns
- [ ] Ready to commit to 2-3 week timeline
- [ ] Ready to follow phases strictly
- [ ] Ready to write tests BEFORE code
- [ ] Ready to deploy ONLY after tests pass

---

## Branch Creation

```bash
# Start clean
git checkout main
git pull

# Create new branch
git checkout -b otlp-schema-v2

# First commit
git commit --allow-empty -m "Start fresh OTLP schema implementation v2

Following strict test-first, phase-ordered approach.
See docs/plans/FRESH-START-PLAN.md for full plan."

# Push
git push -u origin otlp-schema-v2
```

---

**Status**: Ready to begin Phase 0  
**Next Action**: Task 0.1 - Complete Migration 8316334b1935
