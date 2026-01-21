## 0. Data Model Design (Star Schema, OTEL-Aligned)
## 1. Branching & Project Setup
## 2. Zalando Postgres Operator Integration (Terraform)
## 3. v2 API Skeleton & Decoupling
## 4. Storage Layer Abstraction
## 5. Server-Side Filtering, Time-based Querying, Pagination & Enhanced Query UI
## 6a. Migration Job Robustness
## 7. Unit and Integration Testing
## 8. Documentation & Migration Notes
## 9. Future Phases (After DB is Ready)
## 10. Security & Access Control
## 11. Performance & Indexing
## 12. Observability & Monitoring
## 13. Upgrade & Rollback
## 14. Documentation
## 15. Future Phases
## 16. Testing
## 17. Security & Access Control
## 18. Performance & Indexing
## 19. Observability & Monitoring
## 20. Upgrade & Rollback Strategy
## 21. Documentation & Migration Notes
## 22. Future Phases (After DB is Ready)
## 23. Conclusion
## 24. Acknowledgments
## 25. References
## 26. Appendix
## 27. Change Log
## 28. Glossary
## 29. Contact Information
## 30. License
## 31. Future Work
## 32. Feedback
## 33. Contributions
## 34. Acknowledgments
## 35. References
## 36. Appendix
## 37. Change Log
## 38. Glossary
## 39. Contact Information
## 40. License
## 41. Future Work
## 42. Feedback
## 43. Contributions
## 44. Acknowledgments
## 45. References
## 46. Appendix
## 47. Change Log
## 48. Glossary
## 49. Contact Information
## 50. License
## 51. Future Work
## 52. Feedback
## 53. Contributions
## 54. Acknowledgments
## 55. References
## 56. Appendix
## 57. Change Log
## 58. Glossary
## 59. Contact Information
## 60. License
## 61. Future Work
## 62. Feedback
## 63. Contributions
## 64. Acknowledgments
## 65. References
## 66. Appendix
## 67. Change Log
## 68. Glossary
## 69. Contact Information
## 70. License
## 71. Future Work
## 72. Feedback
## 73. Contributions
## 74. Acknowledgments
## 75. References
## 76. Appendix
## 77. Change Log
## 78. Glossary
## 79. Contact Information
## 80. License
## 81. Future Work
## 82. Feedback
## 83. Contributions
## 84. Acknowledgments
## 85. References
## 86. Appendix
## 87. Change Log
## 88. Glossary
## 89. Contact Information
## 90. License
## 91. Future Work
## 92. Feedback
## 93. Contributions
## 94. Acknowledgments
## 95. References
## 96. Appendix
## 97. Change Log
## 98. Glossary
## 99. Contact Information
## 100. License

# ollyScale v2 API & Postgres Migration – Implementation Plan

**Note:** All deployments are clean installs. No legacy data migration or ETL is required.

---

## 1. Project Initialization & Branching

- [ ] Create and work in `feature/postgres-zalando-operator` branch.
- [ ] Document all changes and rationale in Markdown under docs/.

## 2. Infrastructure: Postgres Operator & Helm

- [ ] Add Zalando Postgres Operator Helm chart/manifests to Terraform.
- [ ] Deploy operator in `postgres-operator` namespace.
- [ ] Parameterize storage size/class (default 30GB, allow K8s default).
- [ ] Add single-node, internal-only Postgres cluster CR.
- [ ] Reference operator-managed Secret for DB credentials.

## 3. Data Model & Schema

- [ ] Design star schema for traces, logs, metrics (see OTEL spec).
- [ ] Use only JSONB for attributes; include tenant_id and connection_id.
- [ ] Use snake_case naming convention.
- [ ] Partition fact tables by time.
- [ ] Create Alembic migration scripts for schema.

## 4. Retention & Partitioning

- [ ] Add admin UI to configure retention per data type.
- [ ] Store retention config in Postgres.
- [ ] Enforce retention via native partitioning and scheduled jobs (pg_cron/K8s CronJob).
- [ ] Document partitioning strategy and future-proofing.

## 5. FastAPI v2 App & Container ("frontend")

- [ ] Scaffold new FastAPI app in a new directory/container.
- [ ] Create new Pydantic models for OTEL data (traces, logs, metrics).
- [ ] Implement receiver endpoint using these models and async DB writes.
- [ ] Remove legacy parsing/storage logic.
- [ ] Add health check endpoint for DB connectivity.

## 6. API Features

- [ ] Implement endpoints for traces, logs, metrics, service map.
- [ ] Require time range in queries.
- [ ] Support cursor-based pagination (default 50–100 results).
- [ ] Enforce result limits and memory protection.
- [ ] Implement server-side filtering and SQL WHERE clause generation.
- [ ] Provide OpenAPI schema for UI auto-completion.

## 7. UI Features

- [ ] Update frontend to support advanced query builder (field auto-completion, filter construction).
- [ ] Implement paginated/infinite scroll views for large datasets.
- [ ] Display warnings/info for broad queries or result caps.
- [ ] Show banners/modals for DB unavailable or migration in progress.

## 8. Migrations & Helm Integration

- [ ] Use Alembic for schema migrations.
- [ ] Add K8s Job for migrations (not Helm hook if long-running).
- [ ] App startup blocks until migrations complete.
- [ ] Monitor migration Job status and log output.

## 9. Testing

- [ ] Add unit tests for models, routers, storage.
- [ ] Add integration tests for endpoints using FastAPI TestClient.
- [ ] Add UI tests for query builder and pagination.
- [ ] Ensure tests are independent of DB until Postgres is ready.

## 10. Security & Access Control

- [ ] Use Kubernetes secrets for DB credentials.
- [ ] Document secret management and rotation.
- [ ] No auth required initially; RBAC for admin UI/API is future.

## 11. Performance & Indexing

- [ ] Add indexes for common queries (trace_id, time, attributes).
- [ ] Plan for query optimization and monitoring (future).

## 12. Observability & Monitoring

- [ ] Emit own telemetry, but sample to avoid feedback loops.
- [ ] Monitor DB health, migration status, API error rates.

## 13. Upgrade & Rollback

- [ ] Document migration/rollback strategy (future; not required for dev).

## 14. Documentation

- [ ] Document API, migration plan, licensing, secrets, troubleshooting in Markdown.

## 15. Future Phases

- [ ] Enable backups and HA in Zalando operator.
- [ ] Add production-grade monitoring and alerting.
- [ ] Support schema evolution and rollback.
- [ ] Consider multi-region, multi-tenant, and managed Postgres options.

---

**This plan is now actionable and can be used as a step-by-step to-do list for implementation.**

---

## 0. Data Model Design (Star Schema, OTEL-Aligned)

- Design explicit star schema for traces, logs, and metrics, referencing:
  - [OpenTelemetry Data Model Spec](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/data-model.md)
  - [OTEL Protobuf Definitions](https://github.com/open-telemetry/opentelemetry-proto/tree/main/opentelemetry/proto)
  - [OTEL Semantic Conventions](https://github.com/open-telemetry/opentelemetry-specification/tree/main/specification/trace/semantic_conventions)
- Example tables:
  - `spans_fact` (trace_id, span_id, parent_span_id, service_id, operation_id, start_time_unix_nano, end_time_unix_nano, duration, status_code, kind, resource_id, attributes JSONB, events JSONB, links JSONB)
  - `logs_fact` (id, time_unix_nano, observed_time, trace_id, span_id, severity_number, severity_text, body JSONB, attributes JSONB, resource JSONB, flags, dropped_attrs)
  - `metrics_fact` (id, resource JSONB, scope JSONB, metric_name, metric_type, unit, description, data_points JSONB, attributes JSONB, time_unix_nano, start_time_unix_nano)
  - Dimension tables: `service_dim`, `operation_dim`, `resource_dim`, `time_dim` (optional)
- Use JSONB for flexible attributes, but index common keys.
- Partition fact tables by time for future retention/performance.

---

## 1. Branching & Project Setup

- Work on `feature/postgres-zalando-operator` branch.
- Document all changes and rationale in repo docs.

---

## 2. Zalando Postgres Operator Integration (Terraform)

- Add Zalando Postgres Operator Helm chart/manifests to Terraform (e.g., `.kind/modules/main/`).
- Deploy operator in a dedicated namespace (e.g., `postgres-operator`).
- Add a single-node, internal-only Postgres cluster CR (no backups/HA yet).
- Reference operator-managed Secret for DB credentials.

---

## 2a. Data Retention & Partitioning

- Add admin UI to configure retention per data type (traces, logs, metrics).
- Store retention config in Postgres.
- Enforce retention via:
  - Partitioning by time (for fast drops)
  - Scheduled jobs (pg_cron, or app/K8s CronJob) for DELETE/DROP PARTITION
  - Document partitioning strategy and future-proofing for >32TB
- Document schema to allow easy migration to partitioned tables later.

---

## 3. v2 API Skeleton & Decoupling

- Scaffold new FastAPI routers under `app/routers/v2/`.
- Define endpoints for traces, logs, metrics, and service map.
- Use new Pydantic models in `models_v2.py` (no TinyOlly code).

- Reference OTEL data model sources
  ---

  ## 3a. Database Availability & Error Handling

  - Implement health checks for DB connectivity (e.g., `/health/db`).
  - API returns clear error codes/messages for DB down or migration in progress (503, with reason).
  - UI displays banners/modals for DB unavailable or migration in progress.
  - Optionally, provide read-only or degraded mode if partial data is available.
  - [OpenTelemetry Data Model Spec](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/data-model.md)
  - [OTEL Protobuf Definitions](https://github.com/open-telemetry/opentelemetry-proto/tree/main/opentelemetry/proto)
  - [OTEL Semantic Conventions](https://github.com/open-telemetry/opentelemetry-specification/tree/main/specification/trace/semantic_conventions)

---

## 4. Storage Layer Abstraction

- Implement a new storage interface (e.g., `storage_v2.py`) with stub/in-memory methods.
- Design for future Postgres backend (async, SQLAlchemy or asyncpg).
- Document where Postgres logic will be added.

---

## 5. Server-Side Filtering, Time-based Querying, Pagination & Enhanced Query UI

- All v2 endpoints (logs, traces, spans, metrics) must:
  - Require a time range (start_time, end_time) as part of the query.
  - Support result limiting (e.g., `limit` parameter, with a sensible default and hard maximum).
  - Support pagination (offset/limit or cursor-based) for large result sets.
  - Optionally, support cursor-based "infinite scroll" for the UI.
- Implement SQL WHERE clause generation in storage layer (safe, validated).
- Update frontend to provide an advanced query builder for v2 endpoints.
- Allow visual filter construction and/or simple query language for power users.
- UI must implement paginated or infinite scroll views for large datasets, with clear indicators and memory protection.
- Backend must enforce a hard maximum on results per query and return a flag/cursor if more data is available.
- Display warnings or info if the user’s query is too broad or hits the result cap.

---

- Use Alembic for schema migrations (Python-native, async support).
- Store migration scripts in `apps/ollyscale/migrations/`.
- Add a Kubernetes Job as a Helm `pre-upgrade`/`post-install` hook to run Alembic migrations.
- Job consumes DB credentials from operator-managed Secret.
- Ensure idempotency and fail release on migration errors.
- **No legacy data migration or ETL is needed; only schema creation and upgrades are required.**

---

## 6a. Migration Job Robustness

- Use a dedicated K8s Job (not a Helm hook) for Alembic migrations if migrations may be long-running.
- App startup should block until migrations complete (readiness probe or migration lock flag).
- Monitor migration Job status and log output; alert on timeout/failure.
- Document upgrade/rollback strategy for failed migrations.

---

## 7. Unit and Integration Testing

- Add unit tests for v2 models, routers, and storage stubs (e.g., `tests/test_v2_api.py`).
- Add integration tests for v2 endpoints using FastAPI’s TestClient and in-memory storage.
- Add tests for filter parsing, SQL generation, and API responses.
- Add UI tests for the query builder and filter application.
- Ensure all tests are independent of any database backend until Postgres is ready.

---

## 7a. Security & Access Control

- Document DB credential management (operator secrets), rotation, and access by app/migration jobs.
- Implement RBAC for admin UI and API endpoints as needed.

---

## 7b. Performance & Indexing

- Add indexing strategy for common queries (trace_id, time, attributes).
- Plan for query optimization and monitoring.

---

## 7c. Observability & Monitoring

- Monitor DB health, migration status, and API error rates.
- Add alerting for migration failures or retention job issues.

---

## 7d. Upgrade & Rollback Strategy

- Document how to handle failed migrations, rollbacks, and schema evolution.
- No data migration/ETL rollback is needed, as all installs are clean.

---

## 8. Documentation & Migration Notes

- Document the v2 API, migration plan, and licensing rationale.
- Reference OTEL data model sources in code and documentation.
- Document secret usage, migration process, and troubleshooting.

---

## 9. Future Phases (After DB is Ready)

- Implement Postgres storage backend.
- Enable backups and HA in Zalando operator.
- Add production-grade monitoring and alerting.
- Support schema evolution and rollback.

---

**This plan enables ollyScale to decouple from TinyOlly, adopt a scalable Postgres backend, and deliver a modern, filterable, and testable v2 API.**
