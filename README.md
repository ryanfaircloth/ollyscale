<div align="center">
  <img src="docs/images/ollyscaletitle.png" alt="ollyScale" width="500">

**Desktop-First Observability Platform for Local Development**

</div>

---

## Origins

**ollyScale** is based on the excellent [TinyOlly](https://github.com/tinyolly/tinyolly) project by Infrastructure Architects, LLC.

TinyOlly pioneered the concept of "desktop observability" - bringing enterprise-grade observability tools to local development environments. ollyScale continues this vision while adding enhancements and maintaining compatibility with the OpenTelemetry ecosystem.

**Key Attribution:**
- Original concept and core architecture: TinyOlly (BSD-3-Clause)
- ollyScale enhancements and modifications: AGPL-3.0
- See [NOTICE](./NOTICE) for complete licensing information

---

## Documentation

Docs are here: [https://ryanfaircloth.github.io/ollyscale/](https://ryanfaircloth.github.io/ollyscale/)

## What is ollyScale?

Why send telemetry to a cloud observability platform while coding? Why not have one on your desktop?

ollyScale is a **lightweight OpenTelemetry-native observability platform** for local development, evolved from TinyOlly.  
Visualize and correlate logs, metrics, and traces without sending data to the cloud.

**Key Features:**

- Full OpenTelemetry Protocol (OTLP) support with gRPC and HTTP ingestion
- REST API with OpenAPI documentation
- Service catalog, dependency maps, and distributed tracing
- Works with any OTel Collector distro
- Built with Python (FastAPI), Redis, and JavaScript
- Pre-built Docker images available on Docker Hub

**Platform Support:** Tested on Docker Desktop and KIND Kubernetes (Apple Silicon Mac)
**Architectures:** linux/amd64, linux/arm64 (Apple Silicon)

## Screenshots

<div align="center">
  <table>
    <tr>
      <td align="center" width="50%">
        <img src="docs/images/traces.png" width="400"><br>
        <em>Trace waterfall with correlated logs</em>
      </td>
      <td align="center" width="50%">
        <img src="docs/images/logs1.png" width="400"><br>
        <em>Real-time logs with trace/span linking</em>
      </td>
    </tr>
    <tr>
      <td align="center" width="50%">
        <img src="docs/images/metrics.png" width="400"><br>
        <em>Metrics with chart visualizations</em>
      </td>
      <td align="center" width="50%">
        <img src="docs/images/servicecatalog.png" width="400"><br>
        <em>Service catalog with RED metrics</em>
      </td>
    </tr>
    <tr>
      <td align="center" width="50%">
        <img src="docs/images/servicemap.png" width="400"><br>
        <em>Interactive service dependency map</em>
      </td>
      <td align="center" width="50%">
        <img src="docs/images/collector.png" width="400"><br>
        <em>OpenTelemetry Collector configuration via OpAMP</em>
      </td>
    </tr>
  </table>
</div>

---

## Quick Start

All examples are launched from the repo- clone it first:

```bash
git clone https://github.com/ryanfaircloth/ollyscale
```

## Docker Deployment

### 1. Deploy ollyScale Core (Required)

Start the observability backend (pulls pre-built images from Docker Hub):

```bash
cd docker
./01-start-core.sh
```

**Deployment time:** ~30 seconds (pulls images from Docker Hub)

**Services:**

- **OTLP Receiver**: `localhost:4343` (gRPC)
- **OpAMP Server**: `ws://localhost:4320/v1/opamp` (WebSocket), `localhost:4321` (HTTP REST API)
- **UI**: `http://localhost:5005`
- **Redis**: `localhost:6379`
- **OTel Collector**: `localhost:4317` (gRPC), `localhost:4318` (HTTP)

**Stop:** `./02-stop-core.sh`

---

### 2. Deploy Demo Apps (Optional)

```bash
cd docker-demo
./01-deploy-demo.sh
```

Two Flask microservices with automatic traffic generation (pulls from Docker Hub). Wait 30 seconds for telemetry to appear.

**For local development:** Use `./01-deploy-demo-local.sh` to build images locally
**Stop:** `./02-cleanup-demo.sh`

---

### 3. eBPF Zero-Code Tracing Demo (Optional)

Deploy a demo showing OpenTelemetry eBPF Instrumentation (OBI) - traces captured at the kernel level with zero code changes:

```bash
cd docker-demo-ebpf
./01-deploy-ebpf-demo.sh
```

**Deployment time:** ~30 seconds (pulls pre-built images from Docker Hub)

This demonstrates:

- **eBPF Agent** captures HTTP traces automatically at kernel level
- **No tracing SDK** in application code - traces come from eBPF
- **Logs & Metrics** still use OTel SDK (shows hybrid approach)

See [eBPF Demo Documentation](docs/ebpf.md) for details on how traces differ from SDK-instrumented apps.

**Stop:** `./02-cleanup.sh`

---

### 5. AI Agent Demo with Ollama (Optional)

Deploy an AI agent demo with zero-code OpenTelemetry auto-instrumentation:

```bash
cd docker-ai-agent-demo
./01-deploy-ai-demo.sh
```

This starts:

- **Ollama** with TinyLlama model for local LLM inference
- **AI Agent** with automatic GenAI span instrumentation via `opentelemetry-instrumentation-ollama`

View AI traces in the **AI Agents** tab - see prompts, responses, token usage (in/out), and latency for each LLM call.

**For local development:** Use `./01-deploy-ai-demo-local.sh` to build locally
**Stop:** `./02-stop-ai-demo.sh`
**Cleanup (remove volumes):** `./03-cleanup-ai-demo.sh`

---

### 6. OpenTelemetry Demo (~20 Services - Optional)

Clone and configure the [OpenTelemetry Demo](https://github.com/open-telemetry/opentelemetry-demo) to route telemetry to ollyScale. Edit `src/otel-collector/otelcol-config-extras.yml` to add ollyScale as an exporter, then deploy with built-in observability tools disabled.

---

### 7. Use ollyScale with Your Own Apps

Point your OpenTelemetry exporter to:

- **gRPC**: `http://otel-collector:4317`
- **HTTP**: `http://otel-collector:4318`

### 8. Core-Only Deployment (Use Your Own OTel Collector)

```bash
cd docker-core-only
./01-start-core.sh
```

Deploys ollyScale without the bundled OTel Collector. Includes:

- **OTLP Receiver**: `localhost:4343` (gRPC only)
- **OpAMP Server**: `ws://localhost:4320/v1/opamp` (WebSocket), `localhost:4321` (HTTP REST API)
- **UI**: `http://localhost:5005`
- **Redis**: `localhost:6379`

Point your external collector to `localhost:4343` for telemetry ingestion.

## OpAMP Configuration (Optional)

The **OpenTelemetry Collector + OpAMP Config** page in the ollyScale UI allows you to view and manage collector configurations remotely. To enable this feature, add the OpAMP extension to your collector config:

```yaml
extensions:
  opamp:
    server:
      ws:
        endpoint: ws://localhost:4320/v1/opamp

service:
  extensions: [opamp]
```

The default configuration template (located at `config/otelcol/config.yaml`) shows a complete example with OTLP receivers, OpAMP extension, batch processing, and spanmetrics connector. Your collector will connect to the OpAMP server and receive configuration updates through the ollyScale UI.

**Stop:** `./02-stop-core.sh`

## Kubernetes Deployment

### 1. Deploy ollyScale Core

```bash
cd charts
./install.sh  # Installs to Kubernetes using Helm
```

**Access UI:**

```bash
# UI exposed via Envoy Gateway on localhost
```

UI available at: `http://ollyscale.test`

**Enable eBPF agent for zero-code instrumentation:**

```bash
helm install ollyscale ./charts/ollyscale \
  --namespace ollyscale \
  --create-namespace \
  --set ebpfAgent.enabled=true \
  --set ebpfAgent.config.openPorts="5000,8080,3000"
```

The eBPF agent runs as a DaemonSet and automatically captures HTTP/gRPC traces from applications on specified ports without any code changes. See the [Helm Chart README](charts/ollyscale/README.md#ebpf-zero-code-instrumentation) for full configuration options.

**Cleanup:**

```bash
helm uninstall ollyscale -n ollyscale
kubectl delete namespace ollyscale
```

---

### 2. Demo Applications (Optional)

```bash
cd k8s-demo
./02-deploy.sh  # Automatically builds images if needed
```

**Manual image build (optional):** `cd charts && ./build-and-push-local.sh v2.1.x-demo`
**Cleanup:** `./03-cleanup.sh`

### 3. eBPF Zero-Code Tracing Demo (Optional)

```bash
cd k8s-demo-ebpf
./02-deploy.sh
```

Deploys the eBPF demo with traces captured at the kernel level. Images are pulled from Docker Hub (`ryanfaircloth/ollyscale-ebpf-frontend`, `ryanfaircloth/ollyscale-ebpf-backend`).

See [eBPF Demo Documentation](docs/ebpf.md) for details.

**Cleanup:** `./03-cleanup.sh`

### 4. Core-Only Deployment (Use Your Own OTel Collector)

```bash
cd k8s-core-only
./01-deploy.sh
```

**Cleanup:** `./02-cleanup.sh`

---

## Building Images

For building and publishing Docker images, see [build/README.md](build/README.md).

---

## Features

### UI

- Auto-refresh every 5 seconds (pausable)
- Export JSON with one click
- Service catalog with RED metrics
- Interactive service dependency map
- Distributed trace waterfall with correlated logs
- Metric cardinality protection with visual warnings
- OpAMP-based OpenTelemetry Collector configuration management
- AI Agents tab for GenAI observability

### AI Agents

- View LLM calls with prompts, responses, and token usage
- Zero-code auto-instrumentation via OpenTelemetry GenAI semantic conventions
- Token tracking (input/output) with visual indicators
- Latency monitoring per LLM call
- Click-to-expand JSON span details
- Supports any OpenTelemetry-instrumented LLM (Ollama, OpenAI, etc.)

### Metrics

- Dense, aligned table layout with "Chart" buttons
- Inline "Cardinality" column showing label dimensions and series count
- **Cardinality Explorer**:
  - Deep-dive into metric attributes
  - **Label Analysis**: View high-cardinality labels and their top values (expandable)
  - **Raw Series**: Scrollable view of all active series in PromQL-like syntax
  - **Export**: Copy PromQL or Download JSON for offline analysis

### Service Catalog

- RED metrics (Rate, Errors, Duration) with P50/P95 latencies
- Inline metric visualization
- Sortable columns with persistent filters
- Color-coded error rates

### Service Map

- Auto-detected node types (Client, Server, Database, Messaging)
- Interactive graph with zoom/pan
- Call counts between services
- Real-time topology updates

### Cardinality Protection

- Hard limit of 1000 unique metric names (configurable via `MAX_METRIC_CARDINALITY`)
- Visual warnings at 70% and 90%
- Drops metrics exceeding limit with tracking

### OpenTelemetry Collector + OpAMP Config

- View and manage OpenTelemetry Collector configuration via the OpAMP protocol
- Real-time validation of collector configurations before applying
- Configuration templates for common use cases (default, prometheus-remote-write, etc.)
- View OpAMP server status and connected collector agents
- Apply configuration changes with diff preview
- Requires collector to be connected to the OpAMP server (configured in collector config)

---

## REST API & OpenAPI

Full REST API with OpenAPI 3.0 documentation:

- **Swagger UI**: `http://localhost:5005/docs`
- **ReDoc**: `http://localhost:5005/redoc`
- **OpenAPI Spec**: `http://localhost:5005/openapi.json`

Generate clients in any language:

```bash
curl http://localhost:5005/openapi.json > openapi.json
openapi-generator-cli generate -i openapi.json -g python -o ./ollyscale-client
```

All responses return OpenTelemetry-native JSON with full trace/span context.

## Technical Details

### Stack

- **Backend**: FastAPI (async), Redis with ZSTD compression + msgpack
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Ingestion**: OTLP/gRPC and OTLP/HTTP
- **Storage**: 30-minute TTL, sorted sets indexed by timestamp
- **Correlation**: Native trace/span/log linking

### OTLP Support

- Full OpenTelemetry Protocol compliance
- ResourceSpans, ResourceLogs, ResourceMetrics
- Spanmetrics integration for RED metrics
- OpAMP protocol support for remote collector configuration management
- No vendor lock-in

---

### Development

#### Pre-commit Hooks

ollyScale uses [pre-commit](https://pre-commit.com/) to maintain code quality:

```bash
# Setup (first time)
make precommit-setup

# Run checks manually
make lint

# Run with auto-fix
make lint-fix
```

**Checks include:**

- Python: ruff (lint + format)
- YAML/JSON: validation + formatting
- Shell: shellcheck
- Docker: hadolint
- Helm: helm lint
- Go: golangci-lint
- Markdown: markdownlint

See [docs/precommit.md](docs/precommit.md) for details.

### Admin Endpoints

- `GET /admin/stats` - Redis memory, cardinality, uptime
- `GET/POST/DELETE /admin/alerts` - Alert management
- `GET /health` - Connectivity status

## Licensing

**Dual Licensing:**

- **Original TinyOlly Code**: BSD-3-Clause (see [LICENSE-BSD3-ORIGINAL](./LICENSE-BSD3-ORIGINAL))
- **ollyScale Modifications/Enhancements**: AGPL-3.0 (see [LICENSE](./LICENSE))

See [NOTICE](./NOTICE) for complete attribution and licensing information.

---

<div align="center">
  <p>Built for the OpenTelemetry community</p>
  <p>
    <a href="https://github.com/ryanfaircloth/ollyscale">GitHub</a> •
    <a href="https://github.com/ryanfaircloth/ollyscale/issues">Issues</a>
  </p>
</div>
