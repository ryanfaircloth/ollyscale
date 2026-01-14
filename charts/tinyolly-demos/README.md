# TinyOlly Demos Helm Chart

Unified Helm chart for deploying demo applications to showcase TinyOlly's observability capabilities.

## Features

- **Custom Demo**: Simple Python Flask microservices (demo-frontend + demo-backend)
- **OpenTelemetry Demo**: Official OTel Demo application (11+ microservices)
- **HTTPRoute Integration**: Ingress via Envoy Gateway
- **Local Registry Support**: For KIND cluster development
- **ArgoCD Ready**: GitOps deployment patterns

## Quick Start

### Install Custom Demo

```bash
# Install with default settings (custom demo enabled)
helm install tinyolly-demos . \
  --namespace tinyolly-demos \
  --create-namespace
```

### Install OpenTelemetry Demo

```bash
# Install OTel Demo (disable custom demo)
helm install tinyolly-demos . \
  --namespace tinyolly-demos \
  --create-namespace \
  --set customDemo.enabled=false \
  --set otelDemo.enabled=true
```

### Install Both

```bash
# Install both demos
helm install tinyolly-demos . \
  --namespace tinyolly-demos \
  --create-namespace \
  --set customDemo.enabled=true \
  --set otelDemo.enabled=true
```

## Local Development

### Build and Deploy

```bash
# From repo root
cd charts
./build-and-push-local.sh v2.1.x-demo-test

# Install with local images
helm install tinyolly-demos ./tinyolly-demos \
  --namespace tinyolly-demos \
  --create-namespace \
  --values ./tinyolly-demos/values-local-dev.yaml
```

### Upgrade

```bash
helm upgrade tinyolly-demos ./tinyolly-demos \
  --namespace tinyolly-demos \
  --values ./tinyolly-demos/values-local-dev.yaml
```

## Configuration

### Custom Demo

```yaml
customDemo:
  enabled: true

  frontend:
    image:
      repository: ghcr.io/ryanfaircloth/demo-frontend
      tag: latest
    httpRoute:
      enabled: true
      hostname: demo-frontend.tinyolly.test

  backend:
    image:
      repository: ghcr.io/ryanfaircloth/demo-backend
      tag: latest
```

### OpenTelemetry Demo

```yaml
otelDemo:
  enabled: true
  httpRoute:
    enabled: true
    hostname: otel-demo.tinyolly.test

opentelemetry-demo:
  default:
    env:
      - name: OTEL_EXPORTER_OTLP_ENDPOINT
        value: "http://gateway-collector.tinyolly.svc.cluster.local:4318"
```

## Access

After deployment:

- **Custom Demo**: <https://demo-frontend.tinyolly.test:49443>
- **OTel Demo**: <https://otel-demo.tinyolly.test:49443>
- **TinyOlly UI**: <https://tinyolly.tinyolly.test:49443>

## Traffic Generation

For the custom demo, a traffic generation script is included to create realistic observability data:

```bash
# Run from charts/tinyolly-demos directory
./generate-custom-demo-traffic.sh
```

The script sends continuous requests to the demo-frontend using the FQDN (no port-forwarding required), generating:

- 50% complex distributed traces (`/process-order`)
- 20% service-to-service calls (`/calculate`)
- 20% simple requests (`/hello`)
- 10% error scenarios (`/error`)

Press `Ctrl+C` to stop. See [Custom Demo Documentation](../../docs/demos/custom-demo.md#traffic-generation) for details.

## Dependencies

The chart includes the OpenTelemetry Demo as a subchart dependency:

```bash
# Update dependencies
helm dependency update
```

## ArgoCD Deployment

Deploy via ArgoCD using Terraform:

```bash
cd .kind
terraform apply \
  -var="custom_demo_enabled=true" \
  -var="otel_demo_enabled=false"
```

## Uninstall

```bash
helm uninstall tinyolly-demos --namespace tinyolly-demos
kubectl delete namespace tinyolly-demos
```

## Documentation

- [Custom Demo Documentation](../../docs/demos/custom-demo.md)
- [OpenTelemetry Demo Documentation](../../docs/demos/otel-demo.md)
- [Demos Overview](../../docs/demos/index.md)

## Troubleshooting

### Check deployment status

```bash
kubectl get pods -n tinyolly-demos
kubectl get httproute -n tinyolly-demos
```

### View logs

```bash
kubectl logs -n tinyolly-demos -l app.kubernetes.io/name=demo-frontend
```

### Test connectivity to OTel Collector

```bash
kubectl exec -n tinyolly-demos deployment/demo-frontend -- \
  curl -v gateway-collector.tinyolly.svc.cluster.local:4317
```
