# ollyScale AI Agent Instructions

## Documentation and Resources

- **Official Documentation**: [https://ryanfaircloth.github.io/ollyscale/](https://ryanfaircloth.github.io/ollyscale/)
- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **README**: [README.md](../README.md)
- **Pre-commit Documentation**: [docs/precommit.md](../docs/precommit.md)

## CRITICAL RULES

### Code Quality and Safety

**Pre-commit hooks are MANDATORY:**

- All commits must pass pre-commit checks before being committed
- Setup hooks: `make precommit-setup` or `./setup-precommit.sh`
- Run manually: `make lint` or `pre-commit run --all-files`
- Auto-fix: `make lint-fix`

**Checks include**: ruff (Python), yamlfmt, prettier (JSON), shellcheck, hadolint (Docker), helm lint, golangci-lint (Go), markdownlint, terraform fmt/validate

**NEVER bypass pre-commit hooks or git checks without explicit permission:**

- Do NOT use `git commit --no-verify` or `--no-verify` flag
- Do NOT use `git push --force` or `--force-with-lease` without explicit permission
- If pre-commit checks fail, fix the issues properly or ask for permission to bypass
- Even when authorized to "run all commands", safety checks must be respected unless specifically instructed otherwise

### Repository Identity

**This is a FORK:**

- **Repository**: `ryanfaircloth/ollyscale` (forked from `ollyscale/ollyscale`)
- **Original Project**: ollyScale by Infrastructure Architects, LLC (BSD-3-Clause)
- **Fork Enhancements**: AGPL-3.0 licensed
- **Container Registry**: `ghcr.io/ryanfaircloth/ollyscale` - ALWAYS use this registry
- **Helm Chart Registry**: `ghcr.io/ryanfaircloth/ollyscale/charts` - ALWAYS use this registry

## Project Overview

**ollyScale** is a lightweight, desktop-first OpenTelemetry observability platform for local development, evolved from ollyScale. It ingests traces, logs, and metrics via OTLP, stores them in Redis with 30-minute TTL, and provides real-time visualization through a web UI.

**Core Philosophy**: Ephemeral observability for development. Data is compressed (ZSTD + msgpack), TTL'd, and never persisted. Think of it as "observability workbench" not production monitoring.

## Architecture

### Core Services

- **ollyscale-ui** (FastAPI): Web UI + REST API + OTLP ingestion (port 5002)
- **ollyscale-otlp-receiver** (FastAPI): Dedicated OTLP receiver (port 4343)
- **ollyscale-opamp-server** (Go): OpAMP server for OTel Collector remote config (ports 4320/4321)
- **Redis**: Storage backend (port 6379)
- **OTel Collector**: Bundled collector for demo environments (ports 4317/4318)

### Data Flow

```
OTel SDK → Collector (4317/4318) → OTLP Receiver (4343) → Redis (6379) ← UI (5002)
                                                                          ↑
                                                         OpAMP Server (4320/4321)
```

### Shared Code

Shared utilities are in `apps/ollyscale/common/`:

- **storage.py**: Redis operations with ZSTD compression, msgpack serialization
- **otlp_utils.py**: Centralized OTLP attribute parsing (use `get_attr_value()`, `parse_attributes()`)

## Key Conventions

### Python Code Style

- **Formatter**: ruff with 120 char line length
- **Linting**: Comprehensive ruff rules (see `pyproject.toml`)
- **Imports**: Sorted by ruff (isort rules), known first-party: `tinyolly`, `app`, `common`, `receiver`
- **Type hints**: Encouraged but not required
- **Async**: All Redis operations must be async
- **Config**: [`pyproject.toml`](../pyproject.toml)

### OTLP Handling

- **IDs**: Convert base64 trace/span IDs to hex using `base64.b64decode(id_b64).hex()`
- **Attributes**: Use `otlp_utils.get_attr_value(span, ['http.method', 'http.request.method'])` for semantic convention compatibility
- **Resources**: Extract with `extract_resource_attributes(resource)` from `otlp_utils`
- **Span kinds**: Use integer values (0=UNSPECIFIED, 1=INTERNAL, 2=SERVER, 3=CLIENT, 4=PRODUCER, 5=CONSUMER)

### Service Graph Edge Direction

**Critical pattern**: When building service graphs from spans:

- **PRODUCER spans** (kind=4): Edge direction is `source → target` (normal)
- **CONSUMER spans** (kind=5): Edge direction is **reversed** `target ← source` for messaging systems
- See [storage.py](apps/ollyscale/common/storage.py) `build_service_graph()` for implementation

### Code Organization

**Backend (`apps/ollyscale/`)**:

- **Routers**: `app/routers/` (ingest, query, services, admin, system, opamp)
- **Models**: `models.py` (Pydantic schemas)
- **Dependencies**: Use FastAPI dependency injection via `app/dependencies.py`

**Frontend (`apps/ollyscale-ui/`)**:

- **TypeScript/Vite**: Modern build tooling with ES modules
- **Modules**: `src/modules/` (api, traces, serviceMap, metrics, etc.)
- **Assets**: Compiled to `dist/` and served by nginx

### Async Patterns

- All Redis operations are **async** (`async def`, `await storage.store_spans()`)
- Use `uvloop` for event loop (already configured in `app/main.py`)
- Batch operations with Redis pipelines for performance

## Build Workflow

### Kubernetes Builds (KIND Cluster with Terraform)

**Primary workflow** for local Kubernetes development:

```bash
# Create/update cluster infrastructure (from repo root)
make up                         # Bootstrap KIND cluster + ArgoCD via Terraform

# Build and deploy ollyScale (from repo root or charts/)
cd charts
./build-and-push-local.sh v2.1.x-description  # Build images + Helm chart, push to local registry
```

**How `build-and-push-local.sh` works**:

1. Builds all 4 container images (python-base, UI, OTLP receiver, OpAMP server)
2. Pushes images to `registry.ollyscale.test:49443` (external registry endpoint)
3. Updates `Chart.yaml` version to `0.1.1-<your-version-tag>`
4. Packages and pushes Helm chart to OCI registry
5. Creates `values-local-dev.yaml` with image references using **internal registry** (`docker-registry.registry.svc.cluster.local:5000`)

**ArgoCD deployment**:

- ArgoCD Application defined in `.kind/modules/main/argocd-applications/observability/ollyscale.yaml`
- Automatically syncs Helm chart from local OCI registry
- Must update `targetRevision` in ArgoCD Application to deploy new chart version:

```bash
# Option 1: Update via terraform (preferred)
cd .kind
terraform apply -replace='kubectl_manifest.observability_applications["observability/ollyscale.yaml"]' -auto-approve

# Option 2: Patch directly
kubectl -n argocd patch application ollyscale --type merge \
  -p '{"spec":{"source":{"targetRevision":"0.1.1-v2.1.x-description"}}}'
```

**Critical Build & Registry Pattern**:

**REGISTRY ENDPOINTS** (same physical registry, different access points):

- **External (desktop → registry)**: `registry.ollyscale.test:49443` - Use for `podman push --tls-verify=false`
- **NodePort (desktop → cluster)**: `localhost:30500` - Alternative push endpoint (same registry)
- **Internal (cluster → registry)**: `docker-registry.registry.svc.cluster.local:5000` - Use in Kubernetes deployments

**BUILD & DEPLOY WORKFLOW** (automated by `build-and-push-local.sh`):

1. Script builds images and pushes to **external endpoint** (`registry.ollyscale.test:49443`)
2. Images automatically available via NodePort (`localhost:30500`)
3. Script generates Helm `values-local-dev.yaml` using **internal endpoint** for image pulls
4. Helm chart packaged and pushed to OCI registry at `registry.ollyscale.test:49443/ollyscale/charts`
5. ArgoCD pulls chart from registry, deploys to cluster using internal DNS for image pulls

**DO NOT**:

- Mix registry endpoints in same command
- Push to `registry.ollyscale.test:49443` and deploy with same address (cluster can't resolve it)
- Manually tag/push to multiple endpoints (build scripts handle this)
- **DEPRECATED**: Old `k8s/` scripts (`05-rebuild-local-changes.sh`, `06-rebuild-all-local.sh`, `07-deploy-local-images.sh`) are obsolete - use `charts/build-and-push-local.sh` instead

**CORRECT PATTERN**:

```bash
# From repo root
make up                         # Create/update cluster

# Build and deploy
cd charts
./build-and-push-local.sh v2.1.x-fix  # Builds, pushes, packages chart

# Update ArgoCD to use new chart version
cd ../.kind
terraform apply -replace='kubectl_manifest.observability_applications["observability/ollyscale.yaml"]' -auto-approve
```

**MANUAL PATTERN** (if scripts fail):

```bash
# Build and push to external endpoint (from docker/apps)
cd docker/apps
podman build -f ../dockerfiles/Dockerfile.ollyscale-ui -t registry.ollyscale.test:49443/ollyscale/ui:v2.1.9 .
podman push --tls-verify=false registry.ollyscale.test:49443/ollyscale/ui:v2.1.9

# Update ArgoCD Application spec with new image tag
kubectl -n argocd patch application ollyscale --type merge \
  -p '{"spec":{"source":{"helm":{"valuesObject":{"ui":{"image":{"tag":"v2.1.9"}}}}}}}'
```

### Testing Changes

- **Clear cache after deployment**: `kubectl exec -n ollyscale ollyscale-redis-0 -- redis-cli -p 6379 FLUSHDB`
- **Check logs**: `kubectl logs -n ollyscale deployment/ollyscale-ui -f`
- **Verify image**: `podman images | grep registry.ollyscale.test:49443/ollyscale/ui`
- **Check ArgoCD sync**: `kubectl -n argocd get application ollyscale -o jsonpath='{.status.sync.status}'`
- **Force ArgoCD refresh**: `kubectl -n argocd patch application ollyscale -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' --type merge`
- **Wait for pods to restart**: `sleep 20 && kubectl get po -n ollyscale`

### Terraform Bootstrap Pattern

The cluster uses a **two-phase bootstrap** to handle CRD dependencies:

**Phase 1 (Bootstrap mode)**: `TF_VAR_bootstrap=true`

- Creates KIND cluster with local registry
- Installs ArgoCD via Helm
- Deploys infrastructure apps (Envoy Gateway, OTel Operator, Redis Operator, etc.)
- **Skips HTTPRoutes** - Gateway API CRDs not yet installed

**Phase 2 (Normal mode)**: `TF_VAR_bootstrap=false`

- Waits for Gateway API CRDs to be established
- Deploys HTTPRoutes for ingress
- Re-runs terraform to apply full configuration

**Automation**: `make up` handles this automatically by checking if cluster exists:

- New cluster: runs both phases
- Existing cluster: runs normal mode only

**Manual bootstrap** (if `make up` fails):

```bash
cd .kind
export TF_VAR_bootstrap=true && terraform apply -auto-approve
sleep 30  # Wait for CRDs
export TF_VAR_bootstrap=false && terraform apply -auto-approve
```

## Development Patterns

### Adding OTLP Endpoints

1. Define Pydantic model in `models.py` (e.g., `OTLPTraceRequest`)
2. Add router handler in `app/routers/ingest.py`
3. Parse OTLP with `storage.parse_otlp_traces(data)` or similar
4. Store with batch operation: `await storage.store_spans(spans)`

### Service Map Generation

- Built from spans in Redis using `storage.build_service_graph()`
- Cached for `SERVICE_GRAPH_CACHE_TTL` (default 5s)
- Edge direction depends on span kind (see above)
- Node types inferred from span attributes (db, messaging, external)

### Frontend (TypeScript/Vite)

- **Location**: `apps/ollyscale-ui/src/modules/`
- **TypeScript modules**: `api.ts`, `traces.ts`, `serviceMap.ts`, `metrics.ts`, etc.
- **Cytoscape.js**: For service map visualization
- **Chart.js**: For metrics charts
- **Build**: Vite bundles to `dist/`, served by nginx

### Testing

- **Backend tests**: `apps/ollyscale/tests/`
- Use pytest with async support: `pytest-asyncio`
- Test Redis operations with real Redis instance (not mocked)
- Use fixtures from `conftest.py` for Redis setup
- Follow existing test structure for consistency

**Available test files**:

- `test_spans.py`: Span storage and retrieval
- `test_traces.py`: Trace operations
- `test_logs.py`: Log ingestion and correlation
- `test_metrics.py`: Metrics handling
- `test_compression.py`: ZSTD compression
- `test_services.py`: Service catalog
- `test_alerts.py`: Alert generation
- `test_edge_cases.py`: Edge cases and error handling
- `test_ttl_cleanup.py`: TTL expiration

### Go Tests (OpAMP Server)

```bash
cd docker/apps/tinyolly-opamp-server
go test -v ./...
```

## Deployment Environments

### Kubernetes

- **Deployment**: ArgoCD manages infrastructure and applications
- **Local registry**: `registry.ollyscale.test:49443` (TLS, skip verify) for dev builds
- **Namespace**: `ollyscale`
- **Services**: Exposed via Envoy Gateway with HTTPRoutes

### ArgoCD GitOps

- **Infrastructure apps**: `.kind/modules/main/argocd-applications/infrastructure/`
- **Observability apps**: `.kind/modules/main/argocd-applications/observability/`
- **Application pattern**: Separate Applications for Helm charts and HTTPRoutes
- **Example**: `docker-registry.yaml` (Helm) + `docker-registry-route.yaml` (raw HTTPRoute)
- **No Flux**: All deployments use ArgoCD native Helm support, not Flux HelmRelease CRDs
- **Sync waves**: Applications use `argocd.argoproj.io/sync-wave` annotation for ordered deployment
- **ollyScale chart source**: `docker-registry.registry.svc.cluster.local:5000/ollyscale/charts` (OCI registry)
- **Update pattern**: Change `targetRevision` in Application manifest, then `terraform apply -replace`

## Common Tasks

### Debugging OTLP Issues

1. Check span attributes: `kubectl logs -n ollyscale deployment/ollyscale-ui | grep "kind"`
2. Verify storage format: `kubectl exec -n ollyscale deployment/ollyscale-redis -- redis-cli -p 6379 KEYS "span:*" | head -5`
3. Test attribute parsing: Use `get_attr_value()` from `otlp_utils` with multiple semantic convention keys

### Clearing Data

```bash
# Docker
docker exec ollyscale-redis redis-cli -p 6379 FLUSHDB

# Kubernetes
kubectl exec -n ollyscale deployment/ollyscale-redis -- redis-cli -p 6379 FLUSHDB
```

### Adding Metrics to Service Catalog

1. Compute RED metrics (Rate, Error, Duration) from spans in `storage.get_service_catalog()`
2. Cache results with short TTL to balance freshness and performance
3. Return service-level aggregates, not raw datapoints

## OpAMP Integration

ollyScale uses **OpAMP** (OpenTelemetry Agent Management Protocol) for remote OTel Collector configuration:

- Server: Go implementation at `docker/apps/ollyscale-opamp-server/main.go`
- Validation: Uses `otelcol-contrib validate` binary in UI container
- Templates: YAML configs in `otelcol-configs/` and `otelcol-templates/`
- REST API: `/opamp/*` endpoints in `app/routers/opamp.py`

## Critical Performance Patterns

1. **Batch Redis operations**: Use pipelines, never loop with individual `await` calls
2. **Compression threshold**: Only compress data >512 bytes (see `COMPRESSION_THRESHOLD`)
3. **TTL everything**: All Redis keys must have TTL to prevent memory leaks
4. **Cache service graphs**: Don't rebuild on every API call (use `SERVICE_GRAPH_CACHE_TTL`)
5. **Index by timestamp**: Use sorted sets for time-based queries
