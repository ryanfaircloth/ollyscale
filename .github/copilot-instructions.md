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
./01-start-core.sh              # Pull & run from Docker Hub
./02-stop-core.sh               # Stop all services
./04-rebuild-ui.sh              # Rebuild UI only (local changes)
```

### Kubernetes Builds (Minikube/Kind)

```bash
cd k8s
./02-deploy-tinyolly.sh         # Deploy to cluster
./04-rebuild+deploy-ui.sh       # Rebuild UI, restart pod
./05-rebuild-local-changes.sh <version>  # Rebuild base + UI for tinyolly-common changes
```

**Critical Build Pattern**: When modifying `tinyolly-common/storage.py`:

1. Rebuild `python-base` image (contains tinyolly-common)
2. Rebuild dependent images (UI, OTLP receiver)
3. Push to registry (localhost:5050 for local k8s)
4. Deploy updated images

Example from terminal history:

```bash
cd docker && podman build -f dockerfiles/Dockerfile.tinyolly-python-base -t tinyolly/python-base:latest .
podman build -f dockerfiles/Dockerfile.tinyolly-ui --build-arg APP_DIR=tinyolly-ui -t localhost:5050/tinyolly/ui:v2.1.7-debug .
podman push --tls-verify=false localhost:5050/tinyolly/ui:v2.1.7-debug
kubectl set image deployment/tinyolly-ui tinyolly-ui=localhost:5050/tinyolly/ui:v2.1.7-debug -n tinyolly
```

### Testing Changes

- **Clear cache after deployment**: `kubectl exec -n tinyolly deployment/tinyolly-redis -- redis-cli -p 6579 FLUSHDB`
- **Check logs**: `kubectl logs -n tinyolly deployment/tinyolly-ui -f`
- **Verify image**: `podman images | grep localhost:5050/tinyolly/ui`

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

- Pulls pre-built images from `tinyolly/*`
- Production-like setup
- Used for demos and releases

### Kubernetes

- Uses local registry `localhost:5050` for dev builds
- Namespace: `tinyolly`
- Services exposed via LoadBalancer (Minikube tunnel required)

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
