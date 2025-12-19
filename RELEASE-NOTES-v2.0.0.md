# TinyOlly v2.0.0

**Release Date:** December 2024

Major release with Docker Hub deployment, comprehensive OpenAPI documentation, modular architecture refactoring, OpAMP server for collector management, and AI agent observability.

---

## Highlights

- **Docker Hub Images** - Pre-built multi-arch images for 30-second deployments
- **Modular Architecture** - Complete refactoring into FastAPI best practices
- **OpenAPI 3.0** - Full API documentation with 13 Pydantic models
- **OpAMP Server** - Remote OpenTelemetry Collector configuration management
- **AI Agent Observability** - New tab for GenAI/LLM tracing with Ollama integration
- **Core-Only Mode** - Deploy TinyOlly without bundled collector

---

## What's New

### Docker Hub Deployment

TinyOlly images are now published to Docker Hub for instant deployment:

**Published Images:**
- `tinyolly/python-base` - Shared Python base image
- `tinyolly/ui` - TinyOlly web UI
- `tinyolly/otlp-receiver` - OTLP data receiver
- `tinyolly/opamp-server` - OpAMP configuration server
- `tinyolly/otel-supervisor` - OpenTelemetry Collector with OpAMP
- `tinyolly/demo-frontend` - Demo frontend application
- `tinyolly/demo-backend` - Demo backend service
- `tinyolly/ai-agent-demo` - AI agent with GenAI instrumentation

**Benefits:**
- Multi-architecture: linux/amd64, linux/arm64 (Apple Silicon)
- ~30 second deployment vs 5-10 minutes building locally
- Version tags: `:latest` and semantic versions (`:v2.0.0`)
- Local build scripts available with `-local` suffix

### Modular Architecture Refactoring

The monolithic application has been refactored into a clean, modular FastAPI structure:

```
tinyolly-ui/
├── app/
│   ├── main.py           # App factory
│   ├── config.py         # Centralized settings
│   ├── models.py         # Pydantic models
│   ├── core/
│   │   ├── logging.py    # Logging setup
│   │   ├── middleware.py # HTTP middleware
│   │   └── telemetry.py  # OpenTelemetry instrumentation
│   ├── managers/
│   │   ├── websocket.py  # WebSocket connections
│   │   └── alerts.py     # Alert management
│   ├── routers/
│   │   ├── ingest.py     # OTLP ingestion
│   │   ├── query.py      # Data queries
│   │   ├── services.py   # Service catalog/map
│   │   ├── admin.py      # Admin operations
│   │   ├── system.py     # Health & WebSocket
│   │   └── opamp.py      # OpAMP protocol
│   └── services/
│       └── validation.py # Config validation
```

**Improvements:**
- Clear separation of concerns
- Dependency injection pattern
- Uvloop for faster async event loop
- ORJSONResponse for faster JSON serialization
- Comprehensive OpenTelemetry instrumentation

### OpenAPI & REST API Enhancements

**13 Pydantic Models:**
- `ErrorResponse`, `HealthResponse`, `IngestResponse`
- `TraceDetail`, `TraceSummary`, `SpanDetail`
- `LogEntry`, `MetricMetadata`, `MetricDetail`, `MetricQueryResult`
- `ServiceMap`, `ServiceCatalogEntry`, `StatsResponse`

**8 API Tags:**
- Ingestion, Traces, Spans, Logs, Metrics, Services, System, OpAMP

**Documentation:**
- 20+ endpoints fully documented
- Request/response schemas with examples
- Parameter limits and defaults
- HTTP status codes documented
- Operation IDs for SDK generation

**Access Points:**
- Swagger UI: `http://localhost:5005/docs`
- ReDoc: `http://localhost:5005/redoc`
- OpenAPI JSON: `http://localhost:5005/openapi.json`

### OpAMP Server

New Go-based OpAMP server for remote OpenTelemetry Collector management:

**Features:**
- Real-time collector configuration viewing and editing
- Configuration validation before applying
- Template support for common configurations
- Live status of connected collectors
- Configuration diff preview

**Ports:**
- 4320 - OpAMP WebSocket
- 4321 - OpAMP HTTP REST API

**New UI Tab:** Collector configuration management with visual editor

### AI Agent Observability

New tab for observing Generative AI / LLM applications:

**Features:**
- Zero-code auto-instrumentation via `opentelemetry-instrumentation-ollama`
- GenAI semantic conventions support
- LLM call prompts and responses
- Token usage tracking (input/output)
- Latency per LLM call
- Model information

**Demo Application:**
- Ollama integration for local LLM inference
- Sample AI agent in `docker-ai-agent-demo/`

### Core-Only Deployment

New deployment option without bundled OpenTelemetry Collector:

```bash
# Docker
cd docker-core-only
./01-start-core.sh

# Kubernetes
cd k8s-core-only
./01-deploy.sh
```

Use your own external collector pointing to TinyOlly's OTLP receiver.

### Shared Common Package

New `tinyolly-common` Python package for shared utilities:

- Redis storage layer with ZSTD compression + msgpack
- OTLP format utilities
- TTL-based automatic cleanup (30-minute default)
- Async/await interface with connection pooling

---

## New Deployment Scripts

**Docker:**
- `01-start-core.sh` - Start with Docker Hub images
- `01-start-core-local.sh` - Start with local builds
- `build-and-push-images.sh` - Publish to Docker Hub
- `04-rebuild-ui.sh` - Rebuild UI only

**Kubernetes:**
- `02-deploy-tinyolly.sh` - Deploy from Docker Hub
- `01-build-images.sh` - Build locally for K8s

**Demo Applications:**
- `docker-demo/01-deploy-demo.sh` - Standard demo
- `docker-ai-agent-demo/01-deploy-ai-demo.sh` - AI agent demo

---

## Enhanced Features

### Metrics Cardinality

- Inline cardinality indicators per metric
- Label analysis with high-cardinality detection
- Top values for each label (expandable)
- Raw series view in PromQL-like syntax
- Copy PromQL queries
- JSON export
- Protection limits with visual warnings

### Frontend Enhancements

- `aiAgents.js` - AI agent session visualization
- `collector.js` - OpAMP collector configuration UI
- `filter.js` - Filtering utilities
- Enhanced metrics cardinality explorer
- New tabs for AI Agents and Collector management

---

## Bug Fixes

- Fixed missing `StreamingResponse` import in log streaming endpoint
- Added proper type hints throughout codebase
- Standardized error response format
- Added `status` module import for HTTP status constants

---

## Upgrade Instructions

### From v1.0.0

TinyOlly v2.0.0 is **100% backward compatible**. No breaking changes to:
- API endpoints (all URLs remain the same)
- Data formats
- OTLP ingestion

**Upgrade Steps:**
```bash
# Pull latest changes
git pull origin main

# Docker - now pulls from Docker Hub (~30 seconds)
cd docker
./02-stop-core.sh
./01-start-core.sh

# Or Kubernetes
cd k8s
./03-cleanup.sh
./02-deploy-tinyolly.sh
```

**For local development:** Use `-local` script variants to build images locally.

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/tinyolly/tinyolly
cd tinyolly
git checkout v2.0.0

# Start with Docker (pulls from Docker Hub)
cd docker
./01-start-core.sh

# Deploy demo apps (optional)
cd ../docker-demo
./01-deploy-demo.sh

# Access the application
# Web UI: http://localhost:5005
# Swagger UI: http://localhost:5005/docs
# ReDoc: http://localhost:5005/redoc
```

---

## Statistics

- **108 commits** since v1.0.0
- **13 Pydantic models** for type safety
- **20+ API endpoints** fully documented
- **8 Docker images** on Docker Hub
- **2 architectures** supported (amd64, arm64)
- **~30 second** deployment time
- **100% backward compatible**

---

## Additional Resources

- [Documentation](https://tinyolly.github.io/tinyolly/)
- [GitHub Repository](https://github.com/tinyolly/tinyolly)
- [Docker Deployment Guide](docs/docker.md)
- [Kubernetes Deployment Guide](docs/kubernetes.md)
- [API Reference](docs/api.md)

---

**Built for the OpenTelemetry community**
