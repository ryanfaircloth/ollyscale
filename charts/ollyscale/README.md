# ollyScale Helm Chart

A lightweight, desktop-first OpenTelemetry observability platform for local development.

## Features

- **OTLP Ingestion**: Receive traces, logs, and metrics via OTLP protocol
- **OpAMP Server**: Remote OpenTelemetry Collector configuration management
- **Web UI**: Real-time visualization and service map
- **Auto-Instrumentation**: Supports Python and Go via ollyscale-otel chart

**Note:** OpenTelemetry collectors and instrumentation are now in a separate
`ollyscale-otel` chart which must be deployed first.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- **External PostgreSQL database** - Deploy `ollyscale-postgres` chart
  separately or provide external connection
- **OpenTelemetry Infrastructure** - Deploy `ollyscale-otel` chart to `otel-system` namespace before this chart
- OpenTelemetry Operator (for auto-instrumentation and collectors)

## Important: Deployment Dependencies

This chart has two required dependencies that must be deployed first:

### 1. Database (ollyscale-postgres)

**Breaking Change:** PostgreSQL is no longer included in this chart.

You must deploy the database separately using one of these options:

#### Option 1: ollyscale-postgres Chart (Recommended)

```bash
helm install ollyscale-postgres oci://ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale-postgres \
  --namespace ollyscale-postgres \
  --create-namespace
```

Then configure this chart to use it:

```yaml
api:
  databaseSecretName: ollyscale-postgres-app
otlpReceiver:
  databaseSecretName: ollyscale-postgres-app
```

#### Option 2: External PostgreSQL

Provide a Kubernetes secret with a `uri` key containing the connection string:

```bash
kubectl create secret generic my-postgres-secret \
  --from-literal=uri="postgresql://user:pass@host:5432/dbname"
```

### 2. OpenTelemetry Infrastructure (ollyscale-otel)

**Required:** Deploy the `ollyscale-otel` chart to the `otel-system` namespace before deploying this chart.

The ollyscale-otel chart provides:

- Agent Collector (DaemonSet for node-level collection)
- Gateway Collector (centralized processing with tail sampling)
- Browser Collector (for RUM data)
- Instrumentation CR (for auto-instrumentation)
- Optional eBPF agent

```bash
helm install ollyscale-otel ./charts/ollyscale-otel \
  --namespace otel-system \
  --create-namespace
```

Pods in the `ollyscale` namespace use auto-instrumentation from `otel-system`:

```yaml
annotations:
  instrumentation.opentelemetry.io/inject-python: "otel-system/ollyscale-instrumentation"
```

Then reference the database secret:

```yaml
api:
  databaseSecretName: my-postgres-secret
otlpReceiver:
  databaseSecretName: my-postgres-secret
```

## Installation

```bash
# Add ollyScale Helm repository (if published)
helm repo add ollyscale https://charts.ollyscale.io
helm repo update

# Install ollyScale
helm install ollyscale ollyscale/ollyscale \
  --namespace ollyscale \
  --create-namespace
```

## Configuration

### Core Configuration

```yaml
# values.yaml

# Gateway Collector - main processing pipeline
gatewayCollector:
  enabled: true
  replicas: 1
  resources:
    requests:
      cpu: 200m
      memory: 512Mi

# Agent Collector - DaemonSet for log collection
agentCollector:
  enabled: true
```

### eBPF Zero-Code Instrumentation

**⚠️ Platform Requirements:**

The eBPF agent requires a **real Linux kernel** with eBPF support (kernel 5.11+).
It will **NOT work** on:

- ❌ KIND clusters on macOS/Windows
- ❌ Docker Desktop on macOS/Windows
- ❌ Podman on macOS
- ❌ Any Docker-in-Docker or VM-based Kubernetes

**For local development** on macOS/Windows, use the
[OpenTelemetry Operator auto-instrumentation](#auto-instrumentation) feature instead.

**Supported platforms:**

- ✅ Native Linux Kubernetes clusters (GKE, EKS, AKS, bare-metal)
- ✅ Real hardware or KVM-based VMs with Linux kernel 5.11+

Enable the eBPF agent for automatic kernel-level tracing without code changes:

```yaml
# values.yaml

ebpfAgent:
  enabled: true
  config:
    # Ports to instrument (comma-separated)
    openPorts: "5000,8080"
    # Service name prefix
    serviceName: "my-app"
    # Collector endpoint
    otlpEndpoint: "http://gateway-collector.ollyscale.svc.cluster.local:4317"
```

**eBPF Features:**

- **Zero code changes**: Works with any language (Python, Go, Java, Node.js, etc.)
- **Automatic HTTP/gRPC tracing**: Captures network calls at kernel level
- **DaemonSet deployment**: Instruments all pods on each node
- **Requires privileged mode**: Needs access to kernel debug filesystem

**Use cases:**

- Legacy applications without OTel SDK
- Quick tracing during development
- Multi-language microservices (no per-language SDK needed)

**Example deployment:**

```bash
# Install with eBPF agent enabled
helm install ollyscale ollyscale/ollyscale \
  --namespace ollyscale \
  --create-namespace \
  --set ebpfAgent.enabled=true \
  --set ebpfAgent.config.openPorts="5000,8080,3000"
```

**Note**: eBPF instrumentation provides network-level spans (connection details,
HTTP status codes) but lacks application-level context (route names, user IDs) compared
to SDK instrumentation.

### Auto-Instrumentation

Enable automatic instrumentation for Python and Go applications:

```yaml
# values.yaml

instrumentation:
  enabled: true
  selfObservability: true # Instrument ollyScale itself

  python:
    image:
      tag: 0.60b0
    env:
      - name: OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED
        value: "true"

  go:
    image:
      tag: v0.15.0-alpha
```

**To instrument your application pods**, add this annotation:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        instrumentation.opentelemetry.io/inject-python: "ollyscale/ollyscale-instrumentation"
        # or for Go:
        # instrumentation.opentelemetry.io/inject-go: "ollyscale/ollyscale-instrumentation"
```

### Tail Sampling Configuration

The gateway collector uses tail sampling to keep all errors while sampling successful traces:

```yaml
gatewayCollector:
  config:
    processors:
      tail_sampling:
        policies:
          # Keep ALL errors
          - name: errors
            type: status_code
            status_code:
              status_codes: [ERROR]
          # Keep ALL HTTP 4xx/5xx
          - name: http-errors
            type: string_attribute
            string_attribute:
              key: http.status_code
              values: ["4[0-9]{2}", "5[0-9]{2}"]
              enabled_regex_matching: true
          # Sample success traces at 5%
          - name: sample-success
            type: probabilistic
            probabilistic:
              sampling_percentage: 5.0
```

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                        ollyScale Platform                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐      ┌──────────────┐      ┌──────────────┐   │
│  │ OTel SDK    │─────▶│  Agent       │─────▶│   Gateway    │   │
│  │ (Your Apps) │ OTLP │  Collector   │ OTLP │  Collector   │   │
│  └─────────────┘      │  (DaemonSet) │      │ (Deployment) │   │
│                        └──────────────┘      └──────┬───────┘   │
│  ┌─────────────┐                                    │           │
│  │ eBPF Agent  │────────────────────────────────────┘           │
│  │ (Optional)  │ Kernel-level HTTP/gRPC tracing                 │
│  └─────────────┘                                                 │
│                                    │                             │
│                                    ▼                             │
│                        ┌──────────────────┐                      │
│                        │ OTLP Receiver    │                      │
│                        │ (Ingestion API)  │                      │
│                        └────────┬─────────┘                      │
│                                 │                                │
│                                 ▼                                │
│                        ┌──────────────────┐                      │
│                        │     Redis        │                      │
│                        │ (30min TTL)      │                      │
│                        └────────┬─────────┘                      │
│                                 │                                │
│                                 ▼                                │
│                        ┌──────────────────┐                      │
│                        │    ollyScale UI   │                      │
│                        │  (Web Interface) │                      │
│                        └──────────────────┘                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Values Reference

See [values.yaml](./values.yaml) for full configuration options.

### Key Configuration Sections

| Section            | Description                                    |
| ------------------ | ---------------------------------------------- |
| `gatewayCollector` | Central processing pipeline with tail sampling |
| `agentCollector`   | Node-level DaemonSet for log collection        |
| `ebpfAgent`        | Zero-code eBPF instrumentation (optional)      |
| `instrumentation`  | Python/Go auto-instrumentation                 |
| `ui`               | Web interface deployment                       |
| `otlpReceiver`     | OTLP ingestion endpoint                        |
| `opampServer`      | Remote collector configuration                 |
| `redis`            | Storage backend settings                       |

## Upgrading

```bash
# Upgrade ollyScale
helm upgrade ollyscale ollyscale/ollyscale \
  --namespace ollyscale \
  --reuse-values \
  --set gatewayCollector.replicas=2
```

## Uninstallation

```bash
helm uninstall ollyscale --namespace ollyscale
```

## License

Apache-2.0

## Links

- [Documentation](https://ollyscale.io/docs)
- [GitHub Repository](https://github.com/ollyscale/ollyscale)
- [eBPF Instrumentation Guide](https://ollyscale.io/docs/ebpf)
