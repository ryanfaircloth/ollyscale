# Custom Demo Applications

The custom demo applications provide a simple but realistic microservice architecture for demonstrating ollyScale's observability capabilities.

## Overview

The demo consists of two Python Flask applications that automatically generate OpenTelemetry traces, logs, and Prometheus metrics:

- **demo-frontend**: User-facing service with multiple endpoints
- **demo-backend**: Backend service for data processing

Both applications feature **automatic traffic generation** - they create distributed traces every 3-8 seconds without external input.

## Architecture

```
┌─────────────────┐
│  demo-frontend  │  Port 5000 (HTTP)
│   (Flask)       │  Port 8000 (Prometheus metrics)
└────────┬────────┘
         │ HTTP
         │ OTLP gRPC → gateway-collector:4317
         │ Prom → gateway-collector:19291
         ↓
┌─────────────────┐
│  demo-backend   │  Port 5000 (HTTP)
│   (Flask)       │
└────────┬────────┘
         │ OTLP gRPC → gateway-collector:4317
         ↓
    ollyScale UI
```

## Frontend Endpoints

### `/` - Home

Returns service information and available endpoints.

**Example:**

```bash
curl https://demo-frontend.ollyscale.test:49443/
```

### `/hello` - Simple Request

Basic endpoint that returns a greeting. Generates simple traces.

**Example:**

```bash
curl https://demo-frontend.ollyscale.test:49443/hello
```

### `/calculate` - Backend Interaction

Calls the backend to perform a calculation. Demonstrates service-to-service tracing.

**Example:**

```bash
curl https://demo-frontend.ollyscale.test:49443/calculate
```

**Response:**

```json
{
  "operation": "add",
  "a": 42,
  "b": 17,
  "result": 59
}
```

### `/error` - Error Scenario

Intentionally triggers an exception to demonstrate error tracking.

**Example:**

```bash
curl https://demo-frontend.ollyscale.test:49443/error
```

### `/process-order` - Complex Distributed Trace

Creates a multi-span distributed trace across frontend and backend:

1. Frontend receives order request
2. Backend validates order
3. Backend processes payment
4. Backend checks inventory
5. Order completion

**Example:**

```bash
curl https://demo-frontend.ollyscale.test:49443/process-order
```

**Response:**

```json
{
  "status": "success",
  "order_id": 7342,
  "details": {
    "status": "success",
    "order_id": 7342,
    "processing_time_ms": 287
  }
}
```

## Backend Endpoints

### `/health` - Health Check

Kubernetes liveness/readiness probe endpoint.

### `/calculate` - Math Operations

Performs simple calculations with span attributes showing operands and results.

### `/process` - Order Processing

Handles order processing with multiple sub-operations (validation, payment, inventory).

## Observability Features

### OpenTelemetry Traces

Both services are instrumented with OpenTelemetry auto-instrumentation:

- **Flask instrumentation**: Automatic HTTP server spans
- **Requests instrumentation**: Automatic HTTP client spans
- **Custom spans**: Business logic operations with attributes

**Span attributes include:**

- `http.method`, `http.route`, `http.status_code`
- `calculation.operand_a`, `calculation.operand_b`, `calculation.result`
- `order.id`, `order.status`
- `payment.amount`, `payment.method`

### Prometheus Metrics

Frontend exports custom metrics:

- `demo_frontend_requests_total{endpoint, status}`: Request counter
- `demo_frontend_request_duration_seconds{endpoint}`: Request histogram

Metrics are scraped from port 8000 and pushed to the OTel Collector via remote write.

### Automatic Traffic Generation

The frontend includes a background thread that continuously generates requests:

- **50%**: Process orders (complex traces)
- **20%**: Calculate (service-to-service)
- **20%**: Hello (simple requests)
- **10%**: Errors (failure scenarios)

Requests occur every 3-8 seconds with random intervals.

## Deployment

### Helm Installation

```bash
# Install demos chart
helm install ollyscale-demos charts/ollyscale-demos \
  --namespace ollyscale-demos \
  --create-namespace \
  --values charts/ollyscale-demos/values-local-dev.yaml
```

### ArgoCD Deployment (Recommended)

The demos are managed by ArgoCD via Terraform:

```bash
# Enable custom demo in Terraform
cd .kind
terraform apply -var="custom_demo_enabled=true"
```

### Configuration Options

**Enable/disable via Helm values:**

```yaml
customDemo:
  enabled: true # Set to false to disable

  frontend:
    image:
      repository: ghcr.io/ryanfaircloth/demo-frontend
      tag: latest

    env:
      otelExporterOtlpEndpoint: "http://gateway-collector.ollyscale.svc.cluster.local:4317"
      otelServiceName: "demo-frontend"

  backend:
    image:
      repository: ghcr.io/ryanfaircloth/demo-backend
      tag: latest
```

## Access

After deployment, access the frontend via HTTPRoute:

```bash
# Check deployment status
kubectl get pods -n ollyscale-demos

# Access frontend
curl https://demo-frontend.ollyscale.test:49443/

# Or use port-forward
kubectl port-forward -n ollyscale-demos svc/demo-frontend 5000:5000
curl http://localhost:5000/
```

## Viewing Telemetry

Open ollyScale UI at `https://ollyscale.ollyscale.test` to see:

1. **Service Map**: Visual graph showing frontend → backend relationships
2. **Traces**: Distributed traces with detailed timing and attributes
3. **Logs**: Application logs with trace context
4. **Metrics**: RED metrics (Rate, Errors, Duration) per service

## Development

### Building Local Images

```bash
# Build and push to local registry
cd charts
./build-and-push-local.sh v2.1.x-custom-demo

# Images will be built and pushed:
# - registry.ollyscale.test:49443/ollyscale/demo-frontend:v2.1.x-custom-demo
# - registry.ollyscale.test:49443/ollyscale/demo-backend:v2.1.x-custom-demo
```

### Source Code

Demo source code is located in:

- `apps/demo/frontend.py` - Frontend Flask application
- `apps/demo/backend.py` - Backend Flask application
- `apps/demo/requirements.txt` - Python dependencies

Dockerfiles:

- `docker/dockerfiles/Dockerfile.demo-frontend`
- `docker/dockerfiles/Dockerfile.demo-backend`

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod -n ollyscale-demos -l app.kubernetes.io/name=demo-frontend

# Check logs
kubectl logs -n ollyscale-demos -l app.kubernetes.io/name=demo-frontend
```

### No telemetry in ollyScale

1. Verify OTel Collector is running:

   ```bash
   kubectl get pods -n ollyscale -l app.kubernetes.io/name=opentelemetry-collector
   ```

2. Check demo environment variables:

   ```bash
   kubectl get deployment demo-frontend -n ollyscale-demos -o yaml | grep OTEL_
   ```

3. Test collector connectivity:

   ```bash
   kubectl exec -n ollyscale-demos deployment/demo-frontend -- \
     curl -v gateway-collector.ollyscale.svc.cluster.local:4317
   ```

### HTTPRoute not working

```bash
# Check HTTPRoute status
kubectl get httproute -n ollyscale-demos demo-frontend -o yaml

# Verify Gateway
kubectl get gateway -n envoy-gateway-system cluster-gateway
```

## Traffic Generation

A traffic generation script is provided to continuously send requests to the custom demo and create realistic observability data.

### Usage

```bash
# From the charts/ollyscale-demos directory
cd charts/ollyscale-demos
./generate-custom-demo-traffic.sh
```

The script:

- Sends requests to `https://demo-frontend.ollyscale.test:49443` (no port-forward needed)
- Generates realistic traffic patterns:
  - **50%**: `/process-order` - Complex distributed traces
  - **20%**: `/calculate` - Service-to-service calls
  - **20%**: `/hello` - Simple requests
  - **10%**: `/error` - Error scenarios
- Displays real-time request status with color-coded output
- Uses random delays (0.5-2 seconds) between requests

### Requirements

- Custom demo deployed via Helm/ArgoCD
- HTTPRoute configured and working
- Envoy Gateway running

Press `Ctrl+C` to stop the traffic generator.

## Example Use Cases

### Testing Service Dependencies

Use the `/process-order` endpoint to generate complex traces showing multiple service interactions.

### Error Tracking

The `/error` endpoint creates error traces with exception details for testing error monitoring.

### Load Testing

Run the traffic generation script or adjust its timing for sustained load testing.

### Metrics Analysis

Export Prometheus metrics to analyze request rates, error rates, and latency distributions.

## Migration from k8s-demo

If you previously used `k8s-demo/`, the new Helm chart provides:

- ✅ Same functionality with cleaner deployment
- ✅ HTTPRoute integration (no LoadBalancer needed)
- ✅ GitOps-ready via ArgoCD
- ✅ Easy enable/disable via values
- ✅ Local registry support for development

See [Migration Guide](../migration.md) for details.
