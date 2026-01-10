# TinyOlly AI Agent Instructions

## Project Overview

**TinyOlly** is a lightweight, desktop-first OpenTelemetry observability platform for local development. It ingests traces, logs, and metrics via OTLP, stores them in Redis with 30-minute TTL, and provides real-time visualization through a web UI.

**Core Philosophy**: Ephemeral observability for development. Data is compressed (ZSTD + msgpack), TTL'd, and never persisted. Think of it as "observability workbench" not production monitoring.

## Architecture

### Core Services

- **tinyolly-ui** (FastAPI): Web UI + REST API + OTLP ingestion (port 5002)
- **tinyolly-otlp-receiver** (FastAPI): Dedicated OTLP receiver (port 4343)
- **tinyolly-opamp-server** (Go): OpAMP server for OTel Collector remote config (ports 4320/4321)
- **Redis**: Storage backend (port 6579)
- **OTel Collector**: Bundled collector for demo environments (ports 4317/4318)

### Data Flow

```
OTel SDK → Collector (4317/4318) → OTLP Receiver (4343) → Redis (6579) ← UI (5002)
                                                                          ↑
                                                         OpAMP Server (4320/4321)
```

### Shared Code: `tinyolly-common`

The `docker/apps/tinyolly-common` package contains shared utilities:

- **storage.py**: Redis operations with ZSTD compression, msgpack serialization
- **otlp_utils.py**: Centralized OTLP attribute parsing (use `get_attr_value()`, `parse_attributes()`)

**Critical**: Changes to `tinyolly-common` require rebuilding the **python-base** image first, then dependent services. See [Build Workflow](#build-workflow).

## Key Conventions

### OTLP Handling

- **IDs**: Convert base64 trace/span IDs to hex using `base64.b64decode(id_b64).hex()`
- **Attributes**: Use `otlp_utils.get_attr_value(span, ['http.method', 'http.request.method'])` for semantic convention compatibility
- **Resources**: Extract with `extract_resource_attributes(resource)` from `otlp_utils`
- **Span kinds**: Use integer values (0=UNSPECIFIED, 1=INTERNAL, 2=SERVER, 3=CLIENT, 4=PRODUCER, 5=CONSUMER)

### Service Graph Edge Direction

**Critical pattern**: When building service graphs from spans:

- **PRODUCER spans** (kind=4): Edge direction is `source → target` (normal)
- **CONSUMER spans** (kind=5): Edge direction is **reversed** `target ← source` for messaging systems
- See [storage.py](docker/apps/tinyolly-common/tinyolly_common/storage.py) `build_service_graph()` for implementation

### Code Organization (tinyolly-ui)

- **Routers**: `app/routers/` (ingest, query, services, admin, system, opamp)
- **Models**: `models.py` (Pydantic schemas)
- **Static assets**: `static/*.js` (modular JS with ES6 imports)
- **Templates**: `templates/` (Jinja2 with partials)
- **Dependencies**: Use FastAPI dependency injection via `app/dependencies.py`

### Async Patterns

- All Redis operations are **async** (`async def`, `await storage.store_spans()`)
- Use `uvloop` for event loop (already configured in `app/main.py`)
- Batch operations with Redis pipelines for performance

## Build Workflow

### Docker Builds (Pre-built Images)

```bash
cd docker
./01-start-core.sh              # Pull & run from GHCR
./02-stop-core.sh               # Stop all services
./04-rebuild-ui.sh              # Rebuild UI only (local changes)
```

### Kubernetes Builds (Minikube/Kind)

```bash
cd k8s
./02-deploy-tinyolly.sh         # Deploy to cluster
./04-rebuild+deploy-ui.sh       # Rebuild UI, restart pod
./05-rebuild-local-changes.sh <version>  # Rebuild base + UI for tinyolly-common changes
./06-rebuild-all-local.sh <version>      # Rebuild ALL images (base, UI, OTLP receiver, OpAMP server)
./07-deploy-local-images.sh <version>    # Deploy specific version to cluster
```

**Critical Build & Registry Pattern**:

**REGISTRY ENDPOINTS** (same physical registry, different access points):

- **External (desktop → registry)**: `registry.tinyolly.test:49443` - Use for `podman push --tls-verify=false`
- **NodePort (desktop → cluster)**: `localhost:30500` - Use for `podman push --tls-verify=false`
- **Internal (cluster → registry)**: `docker-registry.registry.svc.cluster.local:5000` - Use in Kubernetes deployments

**BUILD & DEPLOY WORKFLOW**:

1. Build images using `06-rebuild-all-local.sh <version>` - builds and pushes to `registry.tinyolly.test:49443`
2. Images are automatically available at NodePort `localhost:30500` (same registry)
3. Deploy using `07-deploy-local-images.sh <version>` - sets deployment to use `docker-registry.registry.svc.cluster.local:5000/<image>:<version>`
4. Kubernetes pulls images from internal service DNS

**DO NOT**:

- Mix registry endpoints in same command
- Push to `registry.tinyolly.test:49443` and deploy with same address (cluster can't resolve it)
- Manually tag/push to multiple endpoints (build scripts handle this)

**CORRECT PATTERN**:

```bash
cd k8s
./06-rebuild-all-local.sh v2.1.9-perms     # Builds + pushes to registry.tinyolly.test:49443
./07-deploy-local-images.sh v2.1.9-perms   # Deploys using docker-registry.registry.svc.cluster.local:5000
```

**MANUAL PATTERN** (if scripts fail):

```bash
# Build and push to external endpoint
podman build -t registry.tinyolly.test:49443/tinyolly/ui:v2.1.9 .
podman push --tls-verify=false registry.tinyolly.test:49443/tinyolly/ui:v2.1.9

# OR push to NodePort
podman tag registry.tinyolly.test:49443/tinyolly/ui:v2.1.9 localhost:30500/tinyolly/ui:v2.1.9
podman push --tls-verify=false localhost:30500/tinyolly/ui:v2.1.9

# Deploy using INTERNAL endpoint
kubectl set image deployment/tinyolly-ui \
  tinyolly-ui=docker-registry.registry.svc.cluster.local:5000/tinyolly/ui:v2.1.9 -n tinyolly
```

### Testing Changes

- **Clear cache after deployment**: `kubectl exec -n tinyolly deployment/tinyolly-redis -- redis-cli -p 6579 FLUSHDB`
- **Check logs**: `kubectl logs -n tinyolly deployment/tinyolly-ui -f`
- **Verify image**: `podman images | grep registry.tinyolly.test:49443/tinyolly/ui`
- **Check ArgoCD sync**: `kubectl -n argocd get application docker-registry -o yaml`

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

### Frontend JavaScript

- **Modular ES6**: `api.js`, `render.js`, `filter.js`, `serviceMap.js`
- **Cytoscape.js**: For service map visualization
- **Chart.js**: For metrics charts
- **Filter pattern**: `filterTinyOllyData()` to exclude internal services from UI

### Testing

- Located in `docker/apps/tinyolly-ui/tests/`
- Use pytest with async support: `pytest-asyncio`
- Test Redis operations with real Redis instance (not mocked)

## Deployment Environments

### Local Development (`docker-compose-*-local.yml`)

- Builds images from local source
- Mounts no volumes (stateless)
- Fast iteration with `./04-rebuild-ui.sh`

### Docker Hub (`docker-compose-*.yml`)

- Pulls pre-built images from GHCR (`ghcr.io/ryanfaircloth/*`)
- Production-like setup
- Used for demos and releases

### Kubernetes

- **Deployment**: ArgoCD manages infrastructure and applications
- **Local registry**: `registry.tinyolly.test:49443` (TLS, skip verify) for dev builds
- **Namespace**: `tinyolly`
- **Services**: Exposed via Envoy Gateway with HTTPRoutes

### ArgoCD GitOps

- **Infrastructure apps**: `.kind/modules/main/argocd-applications/infrastructure/`
- **Application pattern**: Separate Applications for Helm charts and HTTPRoutes
- **Example**: `docker-registry.yaml` (Helm) + `docker-registry-route.yaml` (raw HTTPRoute)
- **No Flux**: All deployments use ArgoCD native Helm support, not Flux HelmRelease CRDs

## Common Tasks

### Debugging OTLP Issues

1. Check span attributes: `kubectl logs -n tinyolly deployment/tinyolly-ui | grep "kind"`
2. Verify storage format: `kubectl exec -n tinyolly deployment/tinyolly-redis -- redis-cli -p 6579 KEYS "span:*" | head -5`
3. Test attribute parsing: Use `get_attr_value()` from `otlp_utils` with multiple semantic convention keys

### Clearing Data

```bash
# Docker
docker exec tinyolly-redis redis-cli -p 6579 FLUSHDB

# Kubernetes
kubectl exec -n tinyolly deployment/tinyolly-redis -- redis-cli -p 6579 FLUSHDB
```

### Adding Metrics to Service Catalog

1. Compute RED metrics (Rate, Error, Duration) from spans in `storage.get_service_catalog()`
2. Cache results with short TTL to balance freshness and performance
3. Return service-level aggregates, not raw datapoints

## OpAMP Integration

TinyOlly uses **OpAMP** (OpenTelemetry Agent Management Protocol) for remote OTel Collector configuration:

- Server: Go implementation at `docker/apps/tinyolly-opamp-server/main.go`
- Validation: Uses `otelcol-contrib validate` binary in UI container
- Templates: YAML configs in `otelcol-configs/` and `otelcol-templates/`
- REST API: `/opamp/*` endpoints in `app/routers/opamp.py`

## Critical Performance Patterns

1. **Batch Redis operations**: Use pipelines, never loop with individual `await` calls
2. **Compression threshold**: Only compress data >512 bytes (see `COMPRESSION_THRESHOLD`)
3. **TTL everything**: All Redis keys must have TTL to prevent memory leaks
4. **Cache service graphs**: Don't rebuild on every API call (use `SERVICE_GRAPH_CACHE_TTL`)
5. **Index by timestamp**: Use sorted sets for time-based queries

## Current Work Context

Working on branch `fix/issue-7-apm-kafka-consumer-direction` to fix service graph edge direction for Kafka consumers (CONSUMER spans should reverse edge direction).
