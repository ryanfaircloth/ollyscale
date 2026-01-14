# TinyOlly AI Agent Demo - Deployment Guide

## Overview

The TinyOlly AI Agent demo has been refactored to use Helm charts with OTel operator
auto-instrumentation. This provides a cleaner, more maintainable deployment approach
compared to the previous manual Kubernetes manifests.

## What Changed

### Before (Old Approach)

- Manual Kubernetes YAML files in `scripts/k8s/ai-agent-demo/`
- Manual OTLP configuration via environment variables
- Separate deployment and cleanup scripts
- No GitOps integration

### After (New Approach)

- Helm chart in `charts/tinyolly-ai-agent/`
- OTel operator auto-instrumentation (zero-code)
- ArgoCD GitOps deployment
- Integrated with local registry and build scripts

## Architecture

```text
┌─────────────────────────────────────────────┐
│           tinyolly-ai-agent                 │
│                                             │
│  ┌──────────────┐      ┌────────────────┐  │
│  │  AI Agent    │─────▶│    Ollama      │  │
│  │              │      │   (tinyllama)  │  │
│  │ OTel Auto-   │      │                │  │
│  │ Instrumented │      │  Persistent    │  │
│  └──────┬───────┘      │  Storage       │  │
│         │              └────────────────┘  │
│         │                                   │
│         │ OTLP (auto-configured)            │
│         ▼                                   │
│  ┌──────────────────┐                      │
│  │ Agent Collector  │                      │
│  │   (in tinyolly)  │                      │
│  └──────────────────┘                      │
└─────────────────────────────────────────────┘
```

## Deployment

### Automated (Recommended)

The AI agent demo is automatically deployed via ArgoCD when you run:

```bash
make up
```

This will:

1. Create the KIND cluster
2. Install ArgoCD
3. Deploy infrastructure (including OTel operator)
4. Deploy TinyOlly platform
5. Deploy AI agent demo

### Manual Build and Deploy

If you make changes to the AI agent code:

```bash
# Build all images including AI agent
cd charts
./build-and-push-local.sh v2.2.0-my-changes

# ArgoCD will automatically sync the new version
# Or force sync:
cd ../.kind
terraform apply -auto-approve
```

### Chart-only Update

If you only changed the Helm chart (no code changes):

```bash
cd charts
helm package tinyolly-ai-agent
helm push tinyolly-ai-agent-0.1.0.tgz oci://registry.tinyolly.test:49443/tinyolly/charts --insecure-skip-tls-verify

# Update ArgoCD
cd ../.kind
terraform apply -auto-approve
```

## Configuration

### Default Values

See [`charts/tinyolly-ai-agent/values.yaml`](../charts/tinyolly-ai-agent/values.yaml) for all configuration options.

Key defaults:

- **Namespace**: `tinyolly-ai-agent`
- **Ollama model**: `tinyllama`
- **Ollama storage**: 10Gi persistent volume
- **Ollama resources**: 2 CPU / 4Gi RAM (limit)
- **Agent resources**: 500m CPU / 512Mi RAM (limit)
- **HTTPRoute**: Disabled (no external access by default)

### Customization

To override values, edit `.kind/modules/tinyolly/argocd-applications/observability/tinyolly-ai-agent.yaml`:

```yaml
spec:
  source:
    helm:
      valuesObject:
        ollama:
          model: llama2 # Use different model
          resources:
            limits:
              cpu: "4000m"
              memory: "8Gi"

        agent:
          httpRoute:
            enabled: true # Enable external access
```

## Verification

### Check Deployment Status

```bash
# Check ArgoCD application
kubectl get application -n argocd tinyolly-ai-agent

# Check pods
kubectl get pods -n tinyolly-ai-agent

# Check services
kubectl get svc -n tinyolly-ai-agent
```

### View Logs

```bash
# Agent logs (should show successful LLM calls)
kubectl logs -n tinyolly-ai-agent deployment/ai-agent -f

# Ollama logs (should show model downloads)
kubectl logs -n tinyolly-ai-agent deployment/ollama -f
```

### Verify Auto-Instrumentation

```bash
# Check if init container was injected
kubectl get pod -n tinyolly-ai-agent -l app=ai-agent \
  -o jsonpath='{.items[0].spec.initContainers[*].name}'
# Should output: opentelemetry-auto-instrumentation-python

# Check OTLP endpoint configuration
kubectl get pod -n tinyolly-ai-agent -l app=ai-agent \
  -o jsonpath='{.items[0].spec.containers[0].env[?(@.name=="OTEL_EXPORTER_OTLP_ENDPOINT")].value}'
# Should output: http://agent-collector.tinyolly.svc.cluster.local:4318
```

### Check Traces in TinyOlly UI

1. Port-forward to TinyOlly UI:

   ```bash
   kubectl port-forward -n tinyolly svc/tinyolly-ui 5002:5002
   ```

2. Open browser: <http://localhost:5002>

3. Filter for service: `ai-agent`

4. Look for GenAI spans with attributes:
   - `gen_ai.system`: "ollama"
   - `gen_ai.request.model`: "tinyllama"
   - `gen_ai.prompt`: User prompt text
   - `gen_ai.completion`: LLM response

## Troubleshooting

### Ollama Not Ready

If Ollama pod stays in "NotReady":

```bash
# Check if model is downloading
kubectl logs -n tinyolly-ai-agent deployment/ollama

# Verify model is pulled
kubectl exec -n tinyolly-ai-agent deployment/ollama -- ollama list
```

Model download can take several minutes depending on network speed.

### Agent Can't Connect to Ollama

If agent logs show connection errors:

```bash
# Verify Ollama service
kubectl get svc -n tinyolly-ai-agent ollama

# Check Ollama pod is ready
kubectl get pods -n tinyolly-ai-agent -l app=ollama
```

### No Traces Appearing

If traces aren't showing in TinyOlly:

```bash
# Verify instrumentation annotation
kubectl get deployment -n tinyolly-ai-agent ai-agent -o yaml | grep instrumentation

# Check OTel operator logs
kubectl logs -n opentelemetry-operator-system deployment/opentelemetry-operator

# Verify Python instrumentation resource exists
kubectl get instrumentation -n tinyolly python-instrumentation
```

## Cleanup

### Remove AI Agent Demo

```bash
# Delete via ArgoCD
kubectl delete application -n argocd tinyolly-ai-agent

# Or delete namespace directly
kubectl delete namespace tinyolly-ai-agent
```

### Full Cluster Teardown

```bash
make down
```

## Migration Notes

If you were using the old K8s deployment method:

1. The old files in `scripts/k8s/ai-agent-demo/` have been removed
2. Old deployment scripts no longer work
3. Use `make up` to deploy the new Helm-based version
4. Configuration is now in the Helm chart values
5. Deployment is managed by ArgoCD

## Files Reference

- **Helm Chart**: `charts/tinyolly-ai-agent/`
- **ArgoCD App**: `.kind/modules/tinyolly/argocd-applications/observability/tinyolly-ai-agent.yaml`
- **Terraform Config**: `.kind/modules/tinyolly/variables.tf` (ai_agent_image, ai_agent_tag)
- **Build Script**: `charts/build-and-push-local.sh`
- **Application Code**: `apps/ai-agent-demo/`
