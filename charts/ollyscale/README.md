# TinyOlly Helm Chart

A lightweight, desktop-first OpenTelemetry observability platform for local development.

## Features

- **OTLP Ingestion**: Receive traces, logs, and metrics via OTLP protocol
- **Gateway Collector**: Centralized processing with tail sampling and service name extraction
- **Agent Collector**: DaemonSet for node-level log collection
- **eBPF Agent** (Optional): Zero-code instrumentation using OpenTelemetry eBPF Instrumentation
- **Auto-Instrumentation**: Python and Go auto-instrumentation support
- **OpAMP Server**: Remote OpenTelemetry Collector configuration management
- **Web UI**: Real-time visualization and service map

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- OpenTelemetry Operator (for auto-instrumentation and collectors)
- Redis Operator (for data storage)

## Installation

```bash
# Add TinyOlly Helm repository (if published)
helm repo add tinyolly https://charts.tinyolly.io
helm repo update

# Install TinyOlly
helm install tinyolly tinyolly/tinyolly \
  --namespace tinyolly \
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
    otlpEndpoint: "http://gateway-collector.tinyolly.svc.cluster.local:4317"
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
helm install tinyolly tinyolly/tinyolly \
  --namespace tinyolly \
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
  selfObservability: true # Instrument TinyOlly itself

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
        instrumentation.opentelemetry.io/inject-python: "tinyolly/python-instrumentation"
        # or for Go:
        # instrumentation.opentelemetry.io/inject-go: "tinyolly/python-instrumentation"
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
│                        TinyOlly Platform                         │
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
│                        │    TinyOlly UI   │                      │
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
# Upgrade TinyOlly
helm upgrade tinyolly tinyolly/tinyolly \
  --namespace tinyolly \
  --reuse-values \
  --set gatewayCollector.replicas=2
```

## Uninstallation

```bash
helm uninstall tinyolly --namespace tinyolly
```

## License

Apache-2.0

## Links

- [Documentation](https://tinyolly.io/docs)
- [GitHub Repository](https://github.com/tinyolly/tinyolly)
- [eBPF Instrumentation Guide](https://tinyolly.io/docs/ebpf)
