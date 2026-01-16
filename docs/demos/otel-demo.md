# OpenTelemetry Demo

The OpenTelemetry Demo is the official demo application from the OpenTelemetry project, showcasing a realistic microservices-based e-commerce system.

## Overview

The OTel Demo (also known as "Astronomy Shop") is a complete distributed system featuring:

- **11+ microservices** in multiple languages (Go, Java, Node.js, Python, .NET, Rust, PHP)
- **Realistic workflows**: Product browsing, shopping cart, checkout, payments
- **Built-in load generator**: Automatic traffic simulation
- **Rich telemetry**: Traces, metrics, logs across all services

When deployed with ollyScale, all telemetry data is sent to ollyScale's collectors instead of bundled backends.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  frontend       │────→│ productcatalog  │     │  currencyservice│
│  (TypeScript)   │     │  (Go)           │     │  (.NET)         │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         │              ┌─────────────────┐     ┌─────────────────┐
         ├─────────────→│ cartservice     │────→│ redis           │
         │              │  (Go)           │     │  (cache)        │
         │              └─────────────────┘     └─────────────────┘
         │
         │              ┌─────────────────┐     ┌─────────────────┐
         └─────────────→│ checkoutservice │────→│ paymentservice  │
                        │  (Go)           │     │  (Node.js)      │
                        └────────┬────────┘     └─────────────────┘
                                 │
                                 │              ┌─────────────────┐
                                 ├─────────────→│ shippingservice │
                                 │              │  (Rust)         │
                                 │              └─────────────────┘
                                 │
                                 │              ┌─────────────────┐
                                 └─────────────→│ emailservice    │
                                                │  (Ruby)         │
                                                └─────────────────┘
                 │
                 ↓ OTLP
        gateway-collector → ollyScale UI
```

## Services

| Service                   | Language      | Purpose                               |
| ------------------------- | ------------- | ------------------------------------- |
| **frontend**              | TypeScript    | Web UI and BFF (Backend for Frontend) |
| **productcatalog**        | Go            | Product inventory and search          |
| **cartservice**           | Go            | Shopping cart management with Redis   |
| **checkoutservice**       | Go            | Order processing orchestration        |
| **paymentservice**        | Node.js       | Payment processing                    |
| **currencyservice**       | .NET          | Currency conversion                   |
| **shippingservice**       | Rust          | Shipping cost calculation             |
| **emailservice**          | Ruby          | Order confirmation emails             |
| **recommendationservice** | Python        | Product recommendations               |
| **adservice**             | Java          | Advertisement serving                 |
| **loadgenerator**         | Python/Locust | Traffic simulation                    |

## Features

### Multi-Language Instrumentation

The demo showcases OpenTelemetry instrumentation across:

- **Go**: Auto-instrumentation with `otelhttp`, `otelgrpc`
- **Java**: Auto-instrumentation via agent
- **Python**: Auto-instrumentation via `opentelemetry-instrument`
- **.NET**: Native OTel SDK
- **Node.js**: Auto-instrumentation via SDK
- **Rust**: Manual instrumentation
- **Ruby**: SDK instrumentation

### Realistic Scenarios

The load generator creates realistic user flows:

- Browse products
- Add items to cart
- View cart
- Checkout process
- Payment processing
- Shipping calculation

### Rich Telemetry

**Traces:**

- Multi-service distributed traces
- gRPC and HTTP spans
- Database queries (Redis)
- External service calls

**Metrics:**

- Request rates per service
- Error rates
- Latency histograms
- Custom business metrics

**Logs:**

- Structured logs with trace context
- Error logs
- Business event logs

## Deployment

### Helm Installation

```bash
# Install OTel Demo via ollyscale-demos chart
helm install ollyscale-demos charts/ollyscale-demos \
  --namespace ollyscale-demos \
  --create-namespace \
  --set customDemo.enabled=false \
  --set otelDemo.enabled=true
```

### ArgoCD Deployment (Recommended)

Enable via Terraform:

```bash
cd .kind
terraform apply -var="otel_demo_enabled=true" -var="custom_demo_enabled=false"
```

### Configuration

The demo is deployed as a subchart dependency with ollyScale configuration:

```yaml
otelDemo:
  enabled: true

  httpRoute:
    enabled: true
    hostname: otel-demo.ollyscale.test

opentelemetry-demo:
  # Disable bundled observability backends
  opentelemetry-collector:
    enabled: false
  jaeger:
    enabled: false
  grafana:
    enabled: false
  prometheus:
    enabled: false
  opensearch:
    enabled: false

  # Configure OTLP export to ollyScale
  default:
    env:
      - name: OTEL_EXPORTER_OTLP_ENDPOINT
        value: "http://gateway-collector.ollyscale.svc.cluster.local:4318"
      - name: OTEL_EXPORTER_OTLP_PROTOCOL
        value: "http/protobuf"
```

## Access

### Web UI

After deployment, access the frontend:

```bash
# Via HTTPRoute
curl https://otel-demo.ollyscale.test/

# Or browser
open https://otel-demo.ollyscale.test/
```

### Service Endpoints

The frontend provides:

- **Homepage**: Product catalog
- **Product details**: Individual product pages
- **Cart**: Shopping cart management
- **Checkout**: Order placement

## Viewing Telemetry

Open ollyScale UI at `https://ollyscale.ollyscale.test` to explore:

### Service Map

See all 11+ services and their relationships:

- Frontend calling multiple backend services
- Checkout orchestrating payment, shipping, email
- Product catalog serving frontend and recommendations

### Distributed Traces

Example trace flow for checkout:

1. `frontend` - User initiates checkout
2. `checkoutservice` - Orchestrates order processing
3. `cartservice` - Retrieves cart items from Redis
4. `productcatalog` - Gets product details
5. `currencyservice` - Converts prices
6. `paymentservice` - Processes payment
7. `shippingservice` - Calculates shipping
8. `emailservice` - Sends confirmation

Traces show:

- Total duration: ~500ms-2s
- Service-level timings
- gRPC/HTTP method details
- Error conditions

### Metrics

View RED metrics per service:

- **Rate**: Requests/second
- **Errors**: Error rate %
- **Duration**: p50, p95, p99 latencies

### Logs

Application logs with:

- Trace IDs for correlation
- Structured fields (service, level, message)
- Error stack traces

## Resource Requirements

The OTel Demo is more resource-intensive than the custom demo:

```yaml
# Recommended resources for local dev
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

**Note**: For local KIND clusters, ensure Docker/Podman has sufficient resources allocated (at least 4GB RAM).

## Load Generation

The demo includes an automatic load generator that:

- Simulates realistic user behavior
- Generates continuous traffic
- Creates diverse trace patterns
- Includes error scenarios

To adjust load intensity, modify the load generator settings in Helm values.

## Use Cases

### Multi-Language Observability

Perfect for testing ollyScale with polyglot microservices. See how different languages export telemetry.

### Complex Distributed Traces

Explore deeply nested traces with 5-10 spans across multiple services.

### Service Mesh Testing

If using Istio or Linkerd, see how mesh-generated spans integrate with application spans.

### Performance Analysis

Identify bottlenecks in the checkout flow by analyzing trace timings.

## Troubleshooting

### High Resource Usage

```bash
# Check pod resource usage
kubectl top pods -n ollyscale-demos

# Scale down load generator
kubectl scale deployment loadgenerator -n ollyscale-demos --replicas=0
```

### Services Not Starting

```bash
# Check pod status
kubectl get pods -n ollyscale-demos

# Describe failing pod
kubectl describe pod <pod-name> -n ollyscale-demos

# Check logs
kubectl logs <pod-name> -n ollyscale-demos
```

### No Telemetry

Verify OTLP endpoint configuration:

```bash
# Check environment variable
kubectl get deployment frontend -n ollyscale-demos -o yaml | grep OTEL_EXPORTER

# Test collector connectivity
kubectl exec -n ollyscale-demos deployment/frontend -- \
  curl -v gateway-collector.ollyscale.svc.cluster.local:4318
```

### HTTPRoute Not Working

```bash
# Check HTTPRoute
kubectl get httproute otel-demo-frontend -n ollyscale-demos -o yaml

# Verify backend service
kubectl get svc -n ollyscale-demos | grep frontendproxy
```

## Chart Version

The ollyscale-demos chart uses OpenTelemetry Demo Helm chart version:

```yaml
dependencies:
  - name: opentelemetry-demo
    version: "0.33.0"
    repository: https://open-telemetry.github.io/opentelemetry-helm-charts
```

To update to a newer version, modify `charts/ollyscale-demos/Chart.yaml` and run:

```bash
cd charts/ollyscale-demos
helm dependency update
```

## Comparison with Custom Demo

| Feature        | Custom Demo                | OTel Demo                                   |
| -------------- | -------------------------- | ------------------------------------------- |
| Services       | 2                          | 11+                                         |
| Languages      | Python                     | Go, Java, Python, .NET, Node.js, Rust, Ruby |
| Complexity     | Simple                     | Production-realistic                        |
| Resource Usage | Low (~256MB)               | High (~2-4GB)                               |
| Traces         | 3-5 spans                  | 10-20 spans                                 |
| Best For       | Quick testing, development | Comprehensive demos, training               |

## Migration from k8s-otel-demo

If you previously used `k8s-otel-demo/`, the new Helm chart provides:

- ✅ Same demo application, cleaner deployment
- ✅ HTTPRoute integration for ingress
- ✅ GitOps-ready via ArgoCD
- ✅ Managed as subchart dependency
- ✅ Automatic OTLP configuration

See [Migration Guide](../migration.md) for details.

## References

- [OpenTelemetry Demo Documentation](https://opentelemetry.io/docs/demo/)
- [Demo GitHub Repository](https://github.com/open-telemetry/opentelemetry-demo)
- [Demo Helm Chart](https://github.com/open-telemetry/opentelemetry-helm-charts/tree/main/charts/opentelemetry-demo)
