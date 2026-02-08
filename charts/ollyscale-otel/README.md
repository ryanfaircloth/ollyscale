# ollyscale-otel

OpenTelemetry collector infrastructure for OllyScale.

## Overview

This chart deploys the OpenTelemetry collector infrastructure required by OllyScale, including:

- **Agent Collector**: DaemonSet mode collector that runs on each node to collect telemetry from workloads
- **Gateway Collector**: Stateless gateway that aggregates, processes, and forwards telemetry to the OllyScale API
- **Browser Collector**: Dedicated collector for browser-based telemetry (RUM)
- **Instrumentation CR**: Enables automatic instrumentation of workloads across namespaces
- **eBPF Agent**: Optional eBPF-based network instrumentation (disabled by default)

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- OpenTelemetry Operator installed in the cluster
- OllyScale main application (must be deployed **after** this chart)

## Namespace Requirements

**IMPORTANT**: This chart must be deployed to the `otel-system` namespace:

```bash
kubectl create namespace otel-system
helm install ollyscale-otel ./charts/ollyscale-otel --namespace otel-system
```

## Deployment Order

This chart must be deployed **before** the main `ollyscale` chart to ensure
instrumentation infrastructure is available when application components start:

1. `ollyscale-postgres` (database)
2. **`ollyscale-otel`** (telemetry infrastructure) ← This chart
3. `ollyscale` (main application)
4. `ollyscale-demos` (optional demos)
5. `ollyscale-otel-agent` (optional AI agent)

## Cross-Namespace Usage

### Instrumentation Annotation

To enable automatic instrumentation for pods in other namespaces (including
the `ollyscale` namespace), use the following annotation:

```yaml
instrumentation.opentelemetry.io/inject-python: \
  "otel-system/ollyscale-instrumentation"
```

The format is `<namespace>/<instrumentation-cr-name>`.

### OTLP Endpoints

Applications can send telemetry directly to the collectors using these endpoints:

- **Gateway Collector (recommended)**: `gateway-collector.otel-system.svc.cluster.local:4317` (gRPC) or `:4318` (HTTP)
- **Agent Collector (node-local)**: `agent-collector.otel-system.svc.cluster.local:4318` (HTTP)
- **Browser Collector (RUM)**: `ollyscale-browser-collector.otel-system.svc.cluster.local:4318` (HTTP)

## Configuration

### Key Values

| Parameter | Description | Default |
| --------- | ----------- | ------- |
| `agentCollector.enabled` | Enable agent collector DaemonSet | `true` |
| `gatewayCollector.enabled` | Enable gateway collector | `true` |
| `gatewayCollector.replicas` | Number of gateway replicas | `1` |
| `browserCollector.enabled` | Enable browser collector | `true` |
| `instrumentation.enabled` | Deploy Instrumentation CR | `true` |
| `ebpfAgent.enabled` | Enable eBPF agent DaemonSet | `false` |

### Gateway Collector

The gateway collector performs:

- Tail-based sampling (keeps errors, samples successes)
- Batching for efficiency
- Load balanced forwarding to OllyScale OTLP receiver

Default sampling policies:

- Keep all errors (HTTP 4xx/5xx, spans with ERROR status)
- Keep all demo application traces
- Keep all non-ollyscale service traces
- Sample 5% of successful ollyscale service traces

### Agent Collector

Runs as a DaemonSet on each node, receiving telemetry from:

- Auto-instrumented applications
- Manual OTLP exporters
- Forwards to gateway collector with load balancing

### Browser Collector

Dedicated HTTP-only collector for Real User Monitoring (RUM) data from
web browsers. Exposed via HTTPRoute in the main ollyscale chart.

## Example

```yaml
# values.yaml
gatewayCollector:
  replicas: 3
  resources:
    limits:
      memory: 2Gi
    requests:
      memory: 1Gi

instrumentation:
  python:
    image:
      tag: 0.60b1
```

Deploy:

```bash
helm install ollyscale-otel ./charts/ollyscale-otel \
  --namespace otel-system \
  --create-namespace \
  -f values.yaml
```

## Integration with OllyScale

The gateway collector forwards all telemetry to the OllyScale OTLP receiver at:
`ollyscale-otlp-receiver.ollyscale.svc.cluster.local:4343`

This cross-namespace communication requires the full FQDN as the receiver remains in the `ollyscale` namespace.

## Troubleshooting

### Collectors not starting

Check if the OpenTelemetry Operator is running:

```bash
kubectl get pods -n opentelemetry-operator-system
```

### Instrumentation not injecting

Verify the Instrumentation CR exists:

```bash
kubectl get instrumentation -n otel-system
```

Check pod annotations match the namespace:

```bash
kubectl get pod <pod-name> -n <namespace> -o yaml | grep instrumentation
```

### Telemetry not flowing

Check collector logs:

```bash
kubectl logs -n otel-system -l app.kubernetes.io/component=opentelemetry-collector
```

## License

AGPL-3.0 - See LICENSE file for details.
