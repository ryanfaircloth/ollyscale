# Database Connection Pooling and Star Schema ETL Pattern

## Overview

ollyScale uses SQLAlchemy with asyncpg for high-performance async PostgreSQL access with a
**star schema** dimensional model. This document covers connection pooling, transaction
management, and the ETL pattern used to avoid deadlocks in multi-process environments.

## Star Schema Architecture

ollyScale implements a dimensional model with:

- **Dimension tables**: `namespace_dim`, `service_dim`, `operation_dim`, `resource_dim`
- **Fact tables**: `spans_fact`, `logs_fact`, `metrics_fact`

### Multi-Process Transaction Strategy

In multi-process/multi-threaded environments, traditional single-transaction upserts cause
**deadlocks** when multiple processes try to insert the same dimensions simultaneously.

**Solution - Two-Phase ETL Pattern**:

**Phase 1 - Dimension Upserts** (Independent, Auto-Commit):

- Each dimension upsert commits immediately after INSERT
- Idempotent operations (`INSERT ON CONFLICT DO UPDATE`)
- No locks held between dimension operations
- If batch fails and retries, dimensions already exist (safe)
- Works from outer edge inward: namespace → service → operation

**Phase 2 - Fact Inserts** (Single Transaction):

- After ALL dimensions committed, insert facts in one transaction
- Facts reference dimensions via foreign keys
- Dimensions guaranteed to exist from Phase 1

**Benefits**:

- No deadlocks from concurrent dimension upserts
- Idempotent retries (dimensions survive batch failures)
- Better concurrency (no long-held locks)
- Connection pool efficiency maintained

### Testing Implications

**Important**: Dimension auto-commits affect test isolation.

**Problem**: Standard test patterns using transaction rollback don't work:

- Dimensions commit immediately (not rolled back)
- Test data leaks between tests
- Non-deterministic dimension IDs

**Solution**: `clean_database` fixture must truncate dimensions AND facts:

```python
@pytest_asyncio.fixture
async def clean_database(postgres_session):
    """Clean dimensions AND facts for test isolation."""
    await postgres_session.execute(
        "TRUNCATE TABLE spans_fact, logs_fact, metrics_fact, "
        "namespace_dim, service_dim, operation_dim, resource_dim "
        "CASCADE"
    )
    await postgres_session.commit()
```

See `tests/conftest.py` for complete fixture implementation.

## Connection Pool Configuration

Connection pool settings in `app/db/session.py`:

```python
self.engine = create_async_engine(
    url,
    pool_size=10,              # Base pool size (concurrent connections)
    max_overflow=20,           # Additional connections beyond pool_size
    pool_pre_ping=True,        # Verify connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
)
```

**Environment variables**:

- `DATABASE_POOL_SIZE` - Base pool size (default: 10)
- `DATABASE_MAX_OVERFLOW` - Additional overflow connections (default: 20)

## Session Management Pattern

### ✅ CORRECT: Star Schema Two-Phase Pattern

```python
async def store_traces(self, resource_spans: list[dict]) -> int:
    """Store OTLP traces - star schema ETL pattern."""
    async with AsyncSession(self.engine) as session:
        # Phase 1: Dimension upserts (each commits immediately)
        namespace_id = await self._upsert_namespace(session, namespace)  # COMMITS
        service_id = await self._upsert_service(session, name, namespace_id)  # COMMITS
        operation_id = await self._upsert_operation(session, service_id, op_name, kind)  # COMMITS

        # Phase 2: Fact inserts (single transaction after dimensions exist)
        session.add_all(spans_to_insert)
        await session.commit()  # Final commit for facts
```

**Benefits**:

- ✅ No deadlocks in multi-process environments
- ✅ Idempotent dimension upserts survive retries
- ✅ Clean traces with minimal transaction control spans
- ✅ Better performance (fewer round-trips)

### ❌ INCORRECT: Multiple Commits Per Request

```python
async def _upsert_service(self, session: AsyncSession, name: str) -> int:
    """BAD: Committing inside helper method."""
    stmt = insert(ServiceDim).values(name=name)
    await session.execute(stmt)
    await session.commit()  # ❌ WRONG - breaks connection reuse
    return service_id
```

**Problems**:

- ❌ Connection returned to pool after each commit
- ❌ Next operation may get different connection
- ❌ Multiple BEGIN/COMMIT/ROLLBACK cycles
- ❌ Auto-instrumentation creates span for each transaction control
- ❌ Trace noise: 20+ BEGIN/COMMIT/ROLLBACK spans instead of 1-2

## Trace Impact

### Before Fix (Multiple Commits)

```text
gRPC Export (215ms)
├─ connect #1 (5ms)
│  ├─ BEGIN
│  ├─ SELECT tenant_dim
│  └─ COMMIT
├─ connect #2 (5ms)
│  ├─ BEGIN
│  ├─ INSERT namespace_dim
│  ├─ COMMIT
│  ├─ BEGIN
│  ├─ SELECT namespace_dim
│  └─ ROLLBACK
├─ connect #3 (5ms)
│  ├─ BEGIN
│  ├─ INSERT service_dim
│  ├─ COMMIT
│  ├─ BEGIN
│  └─ ROLLBACK
... (8 total connections) ...
└─ connect #8 (5ms)
   ├─ BEGIN
   ├─ INSERT logs_fact (24 records)
   └─ COMMIT
```

**Issues**:

- 8 separate connections in single request
- 20+ transaction control spans (BEGIN, COMMIT, ROLLBACK)
- Connection pool thrashing
- Excessive trace noise

### After Fix (Single Transaction)

```text
gRPC Export (180ms) - 35ms faster!
└─ connect (5ms)
   ├─ BEGIN
   ├─ SELECT tenant_dim
   ├─ INSERT namespace_dim
   ├─ SELECT namespace_dim
   ├─ INSERT service_dim
   ├─ SELECT service_dim
   ├─ INSERT operation_dim
   ├─ SELECT operation_dim
   ├─ INSERT logs_fact (24 records)
   └─ COMMIT
```

**Benefits**:

- ✅ 1 connection per request
- ✅ 2 transaction control spans (BEGIN, COMMIT)
- ✅ Clean, readable trace
- ✅ 17% performance improvement

## OpenTelemetry Auto-Instrumentation

### SQLAlchemy Instrumentation Configuration

In `charts/ollyscale/values.yaml`:

```yaml
instrumentation:
  python:
    env:
      # Disable SQL comment injection (reduces overhead)
      - name: OTEL_INSTRUMENTATION_SQLALCHEMY_ENABLE_COMMENTER
        value: 'false'

      # Instrument all engines automatically
      - name: OTEL_PYTHON_SQLALCHEMY_INSTRUMENT_ALL_ENGINES
        value: 'true'
```

### Trace Span Reduction Strategies

1. **Remove intermediate commits** - Covered above ✅
2. **Use batch inserts** - `session.add_all()` instead of loops
3. **Disable SQL commenter** - Reduces per-query overhead
4. **Connection pooling** - Reuse connections across requests

## Troubleshooting

### Symptom: Many "connect" spans per request

**Diagnosis**: Check for intermediate `session.commit()` calls in helper methods.

**Fix**: Remove commits from `_upsert_*` methods, let caller handle single commit.

### Symptom: BEGIN/COMMIT/ROLLBACK span noise

**Diagnosis**: Multiple transactions per request due to intermediate commits.

**Fix**: Same as above - one transaction per request.

### Symptom: "connection already being used" errors

**Diagnosis**: Session being used from multiple coroutines (not thread-safe).

**Fix**: Each async task needs its own session. Don't share sessions across `asyncio.create_task()` calls.

### Symptom: "connection pool exhausted" warnings

**Diagnosis**: Connection leaks or insufficient pool size.

**Fix**:

1. Verify all sessions use `async with` context manager
2. Increase `DATABASE_POOL_SIZE` or `DATABASE_MAX_OVERFLOW`
3. Check for long-running transactions blocking pool

## References

- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [asyncpg Pool Configuration](https://magicstack.github.io/asyncpg/current/api/index.html#connection-pools)
- [OpenTelemetry SQLAlchemy Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/sqlalchemy/sqlalchemy.html)

## Related

- [Technical Architecture](technical.md)
- [PostgreSQL Infrastructure](postgres-infrastructure.md)
- [Pre-commit Configuration](precommit.md)
