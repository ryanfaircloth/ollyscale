<!-- markdownlint-disable MD013 MD052 MD036 -->

Below is a revised **single plan file** with your corrections baked in:

- Assumes **you create/manage the branch** (no branch-creation steps in the plan).
- The **new frontend app _is_ v2**; no `v2` prefixes/markings inside the code.
- Exposure is via **Kubernetes Gateway API** (not classic Ingress wording).[1][2][3]
- Markdown is structured so you can paste it directly into the repo as `docs/ollyscale-postgres-plan.md`.

All OTEL / Postgres / operator references remain aligned with current practices.[4][5][6][7][8]

***

# ollyScale Postgres & OTEL Migration Plan

## Implementation Status

**Branch:** `storage-improvements`  
**Progress:** Phases 1-10 Complete (as of January 21, 2026)

### ✅ Completed Phases

| Phase | Status | Commits | Notes |
| ----- | ------ | ------- | ----- |
| **Phase 1: Frontend Skeleton** | ✅ Complete | a79d7fc | FastAPI structure, StorageBackend, OTEL models |
| **Phase 2: PostgreSQL Infrastructure** | ✅ Complete | 1968d7f | Zalando Operator, Postgresql CR (2 replicas + PgBouncer) |
| **Phase 3: Alembic OTEL Schema** | ✅ Complete | 96ee885, 0143588 | Async Alembic, partitioned fact tables, dimension tables |
| **Phase 4: Partition Management** | ✅ Complete | d773d6b | create_partitions(), drop_old_partitions(), daily CronJob |
| **Phase 5: PostgresStorage Backend** | ✅ Complete | 4a62d83 | Database session manager, full StorageBackend implementation |
| **Phase 6: Query API** | ✅ Complete | e289095 | Dependency injection, all query endpoints implemented |
| **Phase 7: Ingestion API** | ✅ Complete | af670d3 | Ingest endpoints with validation, error handling |
| **Phase 8: Migration Job** | ✅ Complete | 0143588 | Helm pre-upgrade Job runs Alembic migrations |
| **Phase 9: Testing** | ✅ Complete | a89e9de, 19e55ef | 22 unit tests passing, 6 integration tests (require live DB) |
| **Phase 10: Documentation** | ✅ Complete | 1327624, 19e55ef | Status table, testing strategy documented |

### 🔧 Refactoring Complete

- **InMemoryStorage Removal** | a89e9de | Removed dual-mode operation, PostgresStorage required in production
- **Bug Fixes** | 19e55ef | Fixed TimeRange attribute names (start_time/end_time), fixed _upsert methods

### 📋 Remaining Phases

- **Phase 11:** Integration Testing - API contract tests with FastAPI TestClient (see section 11 below)
- **Phase 12:** Performance Benchmarking - Load test ingestion/queries, optimize indexes
- **Phase 13:** Observability - Add metrics for storage operations, partition status
- **Phase 14:** Deployment & Rollback - Deploy to test environment, verify migration

### Phase 11 Status Update (January 21, 2026)

**Integration Testing Framework Added:**

- **Test Fixtures** (`tests/fixtures.py`): Reusable OTLP data generators for ResourceSpans, ResourceLogs, ResourceMetrics
- **Ingestion Tests** (`tests/test_api_ingest.py`): 17 tests covering POST /api/traces, /api/logs, /api/metrics - ALL PASSING ✅
- **Query Tests** (`tests/test_api_query.py`): 21 tests for search endpoints, pagination, filters (mock data structure fixes needed)
- **Error Tests** (`tests/test_api_errors.py`): 26 tests for error handling, large payloads, concurrent requests
- **Health Tests** (`tests/test_health.py`): 18 comprehensive health endpoint tests - ALL PASSING ✅

**Testing Philosophy:**

- **Unit Tests**: Mock database completely, test business logic and error handling
- **Integration Tests**: Use FastAPI TestClient with mocked StorageBackend to test API contracts
- **Dependency Override Pattern**: `app.dependency_overrides[get_storage] = lambda: mock_storage`
- **No Live DB Required**: All tests use AsyncMock for storage, fast execution (~0.5s for 108 tests)

**Current Status:**

- 86 tests passing, 22 tests need mock data structure fixes to match Pydantic models
- Deprecation warning fixed: `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT`
- Removed obsolete `test_storage.py` (tested removed InMemoryStorage)

**Next Steps:**

- Fix mock data structures in query/error tests to match actual Service, Metric, ServiceMapNode models
- Add test coverage for edge cases (time range validation, pagination cursors)
- Consider adding property-based testing with Hypothesis for OTLP data validation

### Key Technical Decisions

**Storage Architecture:**

- Single-mode operation: PostgresStorage required (DATABASE_HOST must be set)
- InMemoryStorage removed for production safety (was not in original plan)
- Dependency injection pattern with `get_storage()` for clean separation
- PostgreSQL 18 with native partitioning (daily intervals on `time_unix_nano`)

**Schema Design:**

- Partitioned fact tables: `spans_fact`, `logs_fact`, `metrics_fact`
- Dimension tables: `service_dim`, `operation_dim`, `resource_dim`
- JSONB attributes with GIN indexes for flexible querying
- Foreign keys with indexes for fast joins

**Partition Management:**

- Automated creation of future partitions (7-day lookahead)
- Automated cleanup of old partitions (30-day retention)
- CronJob running daily at 2 AM with comprehensive error handling

**Testing:**

- 25 unit tests passing (InMemoryStorage)
- 6 integration tests require live PostgreSQL (validated in Kubernetes)
- Pre-commit hooks ensure code quality (ruff, pytest, yamlfmt, hadolint)

**Dependencies:**

- FastAPI 0.115+, Pydantic 2.10+, SQLAlchemy[asyncio] 2.0.36+
- asyncpg 0.30+ for high-performance async Postgres
- Alembic 1.14+ for schema migrations

***

**Goal:** Introduce an OTEL-aligned, Postgres-backed version of the ollyScale frontend app (replacing Redis-based storage) using the Zalando Postgres Operator, exposed via Kubernetes Gateway API.[2][5][6][1][4]

**Constraints:**

- The **new frontend app is the “v2”**; no `v2` prefixes in module names, URLs, or directories inside that app.
- All new work happens under:
  - `apps/frontend/app`
  - `apps/frontend/tests`
- `apps/ollyscale/` is effectively frozen:
  - Only minimal bug/operational fixes are allowed.
  - No new “v2” logic, models, or storage added there.
- No legacy data migration/ETL is required; all deployments are clean installs.

***

## 0. Scope & Guardrails

- Replace Redis-backed storage for traces, logs, and metrics with Postgres in the **new frontend application**, while keeping the legacy ollyscale app intact for this phase.[5][6][9]
- The new frontend app:
  - Implements OTEL-aligned ingest and query APIs.
  - Is exposed to clients via Gateway API HTTPRoutes.
- A follow-up phase will:
  - Remove unused Redis and legacy code.
  - Finalize cut-over and decommission Redis.

**Guardrail rules for implementation:**

- Do not rename internal modules to include `v2` (e.g., avoid `routers/v2/*`); the whole app is the new version.
- Before every commit:
  - Verify that `apps/ollyscale/` has no unintended changes.
  - Ensure all new code is under `apps/frontend/` paths.

***

## 1. Project Setup (Docs & Structure Only)

- Add plan and architecture docs:
  - `docs/ollyscale-postgres-plan.md` (this file).
  - Optionally `docs/ollyscale-postgres-architecture.md` for diagrams and schema.
- Under `apps/frontend/app`:
  - Ensure there is a clear app entrypoint (e.g., `main.py`) and standard FastAPI layout.[8][10]
  - Add top-level packages:
    - `routers/` for HTTP endpoints.
    - `models/` for Pydantic request/response models.
    - `storage/` for storage abstraction and implementations.
    - `db/` for DB session/connection utilities (if needed).

_(Branch creation is assumed to be handled manually by the developer, not by this plan.)_

***

## 2. Postgres Infrastructure (Zalando Operator via Terraform)

- Use Terraform to deploy **Zalando Postgres Operator** and a Postgres cluster:[11][12][13][4]
  - Operator:
    - Install in namespace like `postgres-operator`.
    - Ensure required CRDs and RBAC are applied.
  - Cluster:
    - Create an `acid.zalan.do/v1` `postgresql` manifest for a single-node internal cluster.
    - Parameterize storage size and class (e.g., 30GB default; overridable).
    - Restrict network access so only the frontend app namespace(s) and migration Jobs can reach it.
- Credentials and connectivity:
  - Use the operator-managed Secret for DB credentials.
  - Mount credentials into:
    - Frontend app Deployment/Pod.
    - Alembic migration Job.
  - Document:
    - Secret names.
    - Connection URI format.
    - How credentials are mapped into environment variables.

***

## 3. OTEL-Aligned Data Model & Schema

- Design schema aligned with OpenTelemetry’s data model and semantic conventions for logs, metrics, and traces:[6][7][14][15][5]
  - Signals:
    - Traces (spans).
    - Logs.
    - Metrics (time-series points).
- Fact tables (examples to adjust as needed):
  - `spans_fact`:
    - Keys: `tenant_id`, `connection_id`, `trace_id`, `span_id`, `parent_span_id`, `service_id`, `operation_id`.
    - Time: `start_time_unix_nano`, `end_time_unix_nano`, `duration`.
    - Fields: `status_code`, `kind`, `resource_id`, `attributes JSONB`, `events JSONB`, `links JSONB`.
  - `logs_fact`:
    - Keys: `id`, `tenant_id`, `connection_id`.
    - Time: `time_unix_nano`, `observed_time_unix_nano`.
    - OTEL: `trace_id`, `span_id`, `severity_number`, `severity_text`, `body JSONB`, `attributes JSONB`, `resource JSONB`, `flags`, `dropped_attributes_count`.
  - `metrics_fact`:
    - Keys: `id`, `tenant_id`, `connection_id`.
    - OTEL: `resource JSONB`, `scope JSONB`, `metric_name`, `metric_type`, `unit`, `description`, `data_points JSONB`, `attributes JSONB`, `time_unix_nano`, `start_time_unix_nano`.[16][5]
- Dimensions:
  - `service_dim`, `operation_dim`, `resource_dim`, optional `time_dim`.
- Conventions:
  - Snake_case for all identifiers.
  - JSONB for flexible attributes with planned GIN indexes for common keys (e.g., service name, environment).[7]
  - Time-based partitioning on fact tables (details next section).
- Implement via Alembic migrations under `apps/frontend/migrations/`.

***

## 4. Retention & Partitioning

- Retention configuration:
  - Create `retention_policy` table with:
    - Tenant identifier.
    - Signal type (trace/log/metric).
    - Retention period (e.g., days).
  - Provide a simple API/CLI path for reading/updating retention policies.
- Partitioning:
  - Use native Postgres partitioning on time columns (`time_unix_nano` or truncated timestamp).
  - Choose an initial interval (daily or weekly) and document why.
- Enforcement:
  - Implement either:
    - `pg_cron` jobs within Postgres, or
    - K8s CronJobs calling a management script.
  - Logic:
    - Drop expired partitions or run `DELETE` on old rows (for tables not yet partitioned).
    - Log actions for audit.
- Document future-proofing and volume assumptions in `docs/ollyscale-postgres-architecture.md`.

***

## 5. Frontend App API Design (New “v2” App)

_(In this plan, “v2” refers to the entire new frontend app; internal names remain clean.)_

- Endpoints:
  - Ingest:
    - `/api/traces`
    - `/api/logs`
    - `/api/metrics`
  - Query:
    - `/api/traces/search`
    - `/api/logs/search`
    - `/api/metrics/search`
    - `/api/service-map`
- Models:
  - Create Pydantic models in `apps/frontend/app/models/` that:
    - Are compatible with OTEL structures but simplified for HTTP JSON.
    - Represent ingest payloads and query responses clearly.
- Decoupling:
  - The frontend app must not import code from `apps/ollyscale/`.
  - The legacy app remains separate in deployment and routing.

***

## 6. Storage Layer Abstraction

- Define a storage abstraction in `apps/frontend/app/storage/`:
  - Interfaces:
    - `store_traces(payload)`
    - `store_logs(payload)`
    - `store_metrics(payload)`
    - `search_traces(query)`
    - `search_logs(query)`
    - `search_metrics(query)`
    - `get_service_map(params)`
- Implementation phases:
  - Phase A (stub):
    - Implement an in-memory or no-op backend for early unit testing.
  - Phase B (Postgres):
    - Implement Postgres-backed storage using an async driver (e.g., async SQLAlchemy or asyncpg) and a pooled connection.[10][17][8]
    - Encapsulate all SQL and query-building logic inside this layer.

***

## 7. Query Semantics: Time, Filtering, Pagination

- Time:
  - All search endpoints require `start_time` and `end_time` parameters.
- Limits:
  - `limit` parameter with default (e.g., 50–100) and hard maximum.
- Pagination:
  - Prefer cursor-based pagination (opaque cursor capturing time and id).
  - Accept offset/limit as a fallback if needed, but design for cursor-first.
- Filtering:
  - Accept structured filters (field, operator, value).
  - Validate filters and construct safe SQL WHERE clauses in the storage layer.
  - Support common fields such as: tenant, service, operation, severity, status, trace_id, environment.
- Response signals:
  - Include `has_more` or `next_cursor` when additional results are available.
  - Enforce the hard cap on rows per query server-side.

***

## 8. Exposure via Kubernetes Gateway API

- Use Gateway API to expose the new frontend app:[3][18][1][2]
  - Create a `Gateway` object (or use an existing one) for HTTP traffic.
  - Create `HTTPRoute` objects that:
    - Match hostnames/paths for the new app (e.g., `api.ziggiz.ai` with `/olly` prefix, adjust as needed).
    - Forward traffic to the Service backing the new frontend Deployment.
- Routing rules:
  - Treat the new frontend app as the **authoritative “v2”** API for new clients.
  - Keep legacy routes pointing at the existing ollyscale app until cut-over.
- Document:
  - Which hostnames/paths route to the new frontend app.
  - Any header-based routing or canary/A/B patterns if used.[19][20]

***

## 9. Migrations & Deployment Integration

- Alembic:
  - Configure Alembic (and SQLAlchemy if used) for Postgres migrations.[8][10]
  - Store migration scripts in `apps/frontend/migrations/`.
- Migration Job:
  - Add a dedicated K8s Job that:
    - Runs `alembic upgrade head` on deploy/upgrade.
    - Uses DB credentials from the operator Secret.
    - Is idempotent and fails fast on errors.
- App readiness:
  - Implement readiness checks so the frontend app:
    - Verifies DB connectivity.
    - Confirms required migrations are applied (via Alembic version table).
- Health endpoints:
  - `/health` and `/health/db`:
    - Return 200 when the app is ready and DB is healthy.
    - Return 503 (with structured body) when DB is down or migrations are running.

***

## 10. Unit Testing

- Add unit tests in `apps/frontend/tests/` for:
  - Pydantic models: validation, defaults, required fields.
  - Routers: status codes, error handling, payload shapes.
  - Storage abstraction:
    - Stub behavior.
    - Filter parsing and SQL generation (where possible without hitting real DB).
  - Retention logic (computations and selection of partitions to drop).
- Ensure the unit test suite can run without a live Postgres instance (stubs/mocks).[21]

***

## 11. Integration Testing (Final Testing Layer)

- API integration tests:
  - Use FastAPI `TestClient` with a test Postgres instance (e.g., Dockerized DB) and migrations applied.
  - Cover:
    - Ingest flows for traces/logs/metrics.
    - Query flows with time range, filters, and pagination.
    - Behavior when DB is unavailable or migrations are incomplete.
- UI integration/E2E:
  - Exercise:
    - Query builder behavior.
    - Pagination/infinite scroll.
    - Error and maintenance banners when `/health` or `/health/db` indicate problems.
- Integration tests must be run **after** unit tests are passing and are treated as the last verification layer before commit/merge.[22]

***

## 12. Observability, Performance & Indexing

- Observability:
  - Emit telemetry for the new frontend app using OTEL (traces, metrics, logs) with appropriate sampling.[9][14][23]
  - Monitor:
    - DB health and resource usage.
    - Migration Job success/failure.
    - API latency, error rates, and throughput.
- Indexing:
  - Add indexes on:
    - Time columns for partition pruning.
    - `trace_id`, `span_id`.
    - Foreign keys such as `service_id`, `operation_id`.
    - JSONB attributes used frequently in filters (GIN indexes).[7]
- Performance:
  - Capture slow queries and iteratively tune indexes and query patterns.
  - Adjust partitioning strategy if needed based on actual load.

***

## 13. Documentation & Follow-Up (Cleanup Phase)

- Documentation:
  - Keep `docs/ollyscale-postgres-plan.md` and architecture docs up to date as implementation details change.
  - Include:
    - Schema diagrams, table descriptions.
    - Retention and partitioning details.
    - Deployment & migration steps.
    - Troubleshooting guides.
- Future cleanup phase (out of scope for this plan):
  - Identify and remove unused Redis and legacy ollyscale code paths.
  - Plan and execute final cut-over from legacy to new frontend app as the single source of truth.
  - Decommission Redis and any unused infrastructure.

***

## 14. Copilot / Automation Rules

For **each incremental change** within these phases:

1. Implement the minimal set of changes needed for that step.
2. Run the **full test suite** (unit + integration + UI tests if configured).
3. If any tests fail:
   - Fix the issues.
   - Re-run tests until green.
4. Before committing:
   - Ensure **no new v2 logic** has been added under `apps/ollyscale/`.
   - Confirm all changes are under `apps/frontend/` (plus allowed infra/docs tweaks).
5. Only when all tests pass and guardrails are satisfied:
   - Format code as needed.
   - Commit with a descriptive message referencing the phase/step.
6. Continue autonomously to the next step in the plan, maintaining the same discipline.[24][25][22]

Sources
[1] Kubernetes Gateway API: Introduction <https://gateway-api.sigs.k8s.io>
[2] Gateway API - Kubernetes <https://kubernetes.io/docs/concepts/services-networking/gateway/>
[3] What Is the Kubernetes Gateway API? - Tetrate <https://tetrate.io/learn/what-is-kubernetes-gateway-api>
[4] Zalando Postgres operator - The Blue Book <https://lyz-code.github.io/blue-book/zalando_postgres_operator/>
[5] Metrics Data Model | OpenTelemetry <https://opentelemetry.io/docs/specs/otel/metrics/data-model/>
[6] Logs Data Model | OpenTelemetry <https://opentelemetry.io/docs/specs/otel/logs/data-model/>
[7] OpenTelemetry Logging Explained: Concepts and Data Model · Dash0 <https://www.dash0.com/knowledge/opentelemetry-logging-explained>
[8] FastAPI with Async SQLAlchemy, SQLModel, and Alembic <https://testdriven.io/blog/fastapi-sqlmodel/>
[9] OpenTelemetry Signals Overview: Logs vs Metrics vs Traces - Dash0 <https://www.dash0.com/knowledge/logs-metrics-and-traces-observability>
[10] Adding a production-grade database to your FastAPI project <https://python.plainenglish.io/adding-a-production-grade-database-to-your-fastapi-project-local-setup-50107b10d539>
[11] zalando/postgres-operator - GitHub <https://github.com/zalando/postgres-operator>
[12] Zalando's Postgres Operator <https://opensource.zalando.com/postgres-operator/docs/quickstart.html>
[13] Postgres Operator - Read the Docs <https://postgres-operator.readthedocs.io>
[14] OpenTelemetry Logging <https://opentelemetry.io/docs/specs/otel/logs/>
[15] Inside OpenTelemetry: Understanding Its Data Model - LinkedIn <https://www.linkedin.com/pulse/opentelemetry-series-6-deep-dive-opentelemetrys-data-model-kulkarni-rzmmf>
[16] Understanding OpenTelemetry Metrics: Types, Model, Collection ... <https://edgedelta.com/company/blog/understanding-opentelemetry-metrics>
[17] FastAPI SQLAlchemy 2, Alembic and PostgreSQL Setup Tutorial 2025 <https://www.youtube.com/watch?v=gg7AX1iRnmg>
[18] API Overview - Kubernetes Gateway API <https://gateway-api.sigs.k8s.io/concepts/api-overview/>
[19] Understanding Kubernetes Gateway API: A Modern Approach to ... <https://www.cncf.io/blog/2025/05/02/understanding-kubernetes-gateway-api-a-modern-approach-to-traffic-management/>
[20] Kubernetes Gateway API in action | Containers - AWS <https://aws.amazon.com/blogs/containers/kubernetes-gateway-api-in-action/>
[21] How to use PostgreSQL test database in async FastAPI tests? <https://stackoverflow.com/questions/70752806/how-to-use-postgresql-test-database-in-async-fastapi-tests>
[22] Automation Pipeline and CI/CD: A Guide to Testing Best Practices <https://www.browserstack.com/guide/automation-pipeline>
[23] What is OpenTelemetry? An open-source standard for logs, metrics ... <https://www.dynatrace.com/news/blog/what-is-opentelemetry/>
[24] Run Tests Before Commit - JetBrains Guide <https://www.jetbrains.com/guide/go/tips/vcs-run-tests-before-commit/>
[25] pre-commit vs. CI - Sebastian Witowski <https://switowski.com/blog/pre-commit-vs-ci/>
[26] Kubernetes Gateway API: What Is It And Why Do You Need It? <https://traefik.io/glossary/kubernetes-gateway-api>
[27] Getting started with Gateway API <https://gateway-api.sigs.k8s.io/guides/>
[28] Collect logs, metrics, and traces with OpenTelemetry - Open Liberty <https://openliberty.io/docs/latest/microprofile-telemetry.html>
[29] Postgres operator doesn't place the user secrets in the defined ... <https://github.com/zalando/postgres-operator/issues/1827>
