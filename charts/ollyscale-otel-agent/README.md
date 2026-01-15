# TinyOlly AI Agent Demo Helm Chart

This Helm chart deploys the TinyOlly AI Agent demo with Ollama LLM server.

## Overview

The AI agent demo showcases:

- **Zero-code OpenTelemetry instrumentation** using the OTel operator
- **GenAI observability** with automatic span generation for LLM calls
- **Ollama LLM** running tinyllama model locally

## Components

1. **Ollama**: LLM server running tinyllama model with persistent storage
2. **AI Agent**: Python agent making LLM calls with auto-instrumentation

## Installation

### Prerequisites

- Kubernetes cluster with OTel operator installed
- Python Instrumentation resource in `tinyolly` namespace
- TinyOlly platform deployed

### Install the chart

```bash
helm install tinyolly-ai-agent ./charts/tinyolly-ai-agent
```

### Install with custom values

```bash
helm install tinyolly-ai-agent ./charts/tinyolly-ai-agent \
  --set ollama.model=llama2 \
  --set agent.httpRoute.enabled=true
```

## Configuration

See [values.yaml](values.yaml) for all configuration options.

### Key Configuration

| Parameter                        | Description               | Default             |
| -------------------------------- | ------------------------- | ------------------- |
| `global.namespace`               | Namespace for deployment  | `tinyolly-ai-agent` |
| `ollama.model`                   | LLM model to download     | `tinyllama`         |
| `ollama.persistence.enabled`     | Enable persistent storage | `true`              |
| `ollama.persistence.size`        | Storage size              | `10Gi`              |
| `ollama.resources.limits.memory` | Memory limit for Ollama   | `4Gi`               |
| `agent.httpRoute.enabled`        | Enable HTTPRoute          | `false`             |

## How It Works

### OTel Auto-Instrumentation

The agent deployment has this annotation:

```yaml
instrumentation.opentelemetry.io/inject-python: "tinyolly/python-instrumentation"
```

This tells the OTel operator to:

1. Inject an init container with OpenTelemetry Python packages
2. Configure OTLP exporter to send to the gateway collector
3. Auto-instrument the Ollama client library

### GenAI Spans

When the agent calls Ollama, the instrumentation automatically creates spans with:

- `gen_ai.system`: "ollama"
- `gen_ai.request.model`: Model name (e.g., "tinyllama")
- `gen_ai.prompt`: User prompt text
- `gen_ai.completion`: LLM response text

## Monitoring

View traces in the TinyOlly UI:

```bash
# Port-forward to TinyOlly UI
kubectl port-forward -n tinyolly svc/tinyolly-ui 5002:5002

# Open browser
open http://localhost:5002
```

Filter for service: `ai-agent-demo`

## Troubleshooting

### Ollama not ready

Check if the model is downloaded:

```bash
kubectl exec -n tinyolly-ai-agent deployment/ollama -- ollama list
```

### Agent not sending traces

Check if instrumentation is injected:

```bash
kubectl get pod -n tinyolly-ai-agent -o yaml | grep -A 10 "instrumentation"
```

Check OTel operator logs:

```bash
kubectl logs -n opentelemetry-operator-system deployment/opentelemetry-operator
```

## Uninstall

```bash
helm uninstall tinyolly-ai-agent
kubectl delete namespace tinyolly-ai-agent
```
