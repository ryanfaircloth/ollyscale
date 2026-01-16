# ollyScale Helm Chart

A Helm chart for deploying ollyScale, a lightweight OpenTelemetry observability platform for local development.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.8+
- Redis Operator (for managed Redis cluster)
- OpenTelemetry Collector (pre-configured)

## Features

- ✅ Supports all three ollyScale components (UI, OpAMP Server, OTLP Receiver)
- ✅ Service accounts for each component with RBAC support
- ✅ Configurable resource limits and requests
- ✅ Health checks (liveness and readiness probes)
- ✅ Flexible service types (LoadBalancer, ClusterIP, NodePort)
- ✅ OCI registry support for chart distribution
- ✅ Production-ready defaults with easy customization

## Installation

### Install from OCI Registry

```bash
# Add the ollyScale OCI registry (example)
helm install ollyscale oci://ghcr.io/ollyscale/charts/ollyscale \
  --version 0.1.0 \
  --namespace ollyscale \
  --create-namespace
```

### Install from Local Chart

```bash
# From the helm directory
helm install ollyscale ./ollyscale \
  --namespace ollyscale \
  --create-namespace
```

### Install with Custom Values

```bash
helm install ollyscale ./ollyscale \
  --namespace ollyscale \
  --create-namespace \
  --values custom-values.yaml
```

## Configuration

### Key Configuration Options

|Parameter|Description|Default|
|---------|-----------|-------|
|`replicaCount`|Number of replicas for each component|`1`|
|`redis.host`|Redis hostname|`ollyscale-redis`|
|`redis.port`|Redis port|`6379`|
|`ui.enabled`|Enable UI component|`true`|
|`ui.service.type`|UI service type|`LoadBalancer`|
|`ui.service.port`|UI service port|`5002`|
|`ui.image.repository`|UI image repository|`ghcr.io/ryanfaircloth/ui`|
|`ui.image.tag`|UI image tag|`latest`|
|`opampServer.enabled`|Enable OpAMP Server|`true`|
|`opampServer.service.type`|OpAMP service type|`ClusterIP`|
|`opampServer.service.websocketPort`|OpAMP WebSocket port|`4320`|
|`opampServer.service.httpPort`|OpAMP HTTP port|`4321`|
|`otlpReceiver.enabled`|Enable OTLP Receiver|`true`|
|`otlpReceiver.service.type`|OTLP service type|`ClusterIP`|
|`otlpReceiver.service.port`|OTLP service port|`4343`|
|`otelCollector.endpoint`|OTel Collector endpoint|`http://otel-collector:4318`|

### Example Custom Values

```yaml
# custom-values.yaml
ui:
  replicaCount: 2
  service:
    type: ClusterIP
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 256Mi

opampServer:
  replicaCount: 2
  resources:
    limits:
      cpu: 500m
      memory: 512Mi

redis:
  host: my-redis-cluster
  port: 6379

otelCollector:
  endpoint: http://my-otel-collector:4318
```

## Building and Publishing

### Package the Chart

```bash
cd charts
./package.sh
```

This will:

1. Lint the chart
2. Package it into a `.tgz` file
3. Prepare it for OCI registry push

### Push to OCI Registry

```bash
# Login to your OCI registry
helm registry login ghcr.io -u <username>

# Push the chart
./push-oci.sh ghcr.io/ollyscale/charts
```

Or manually:

```bash
helm push ollyscale-0.1.0.tgz oci://ghcr.io/ollyscale/charts
```

### Development Workflow

```bash
# Lint the chart
helm lint ./ollyscale

# Dry-run installation
helm install ollyscale ./ollyscale \
  --namespace ollyscale \
  --dry-run \
  --debug

# Template rendering (see generated manifests)
helm template ollyscale ./ollyscale \
  --namespace ollyscale \
  --values custom-values.yaml
```

## Upgrading

```bash
# Upgrade from OCI registry
helm upgrade ollyscale oci://ghcr.io/ollyscale/charts/ollyscale \
  --version 0.2.0 \
  --namespace ollyscale

# Upgrade from local chart
helm upgrade ollyscale ./ollyscale \
  --namespace ollyscale \
  --values custom-values.yaml
```

## Uninstalling

```bash
helm uninstall ollyscale --namespace ollyscale
```

## Architecture

The chart deploys three main components:

1. **ollyScale UI** - Web interface and REST API
   - Exposes port 5002
   - Service account with minimal permissions
   - Health checks on `/health` endpoint

2. **ollyScale OpAMP Server** - OpenTelemetry Agent Management Protocol server
   - WebSocket port 4320
   - HTTP port 4321
   - Service account with minimal permissions

3. **ollyScale OTLP Receiver** - Dedicated OTLP ingestion endpoint
   - gRPC port 4343
   - Service account with minimal permissions

## Dependencies

The chart assumes the following external dependencies are available:

- **Redis**: Deployed via redis-operator
- **OTel Collector**: Pre-configured collector for telemetry export
- **ConfigMaps**: `otel-collector-config` and `otelcol-templates` for OTel configuration

## Best Practices

This chart follows Helm and Kubernetes best practices:

- ✅ Uses semantic versioning
- ✅ Includes health checks for all components
- ✅ Configurable resource limits
- ✅ Service accounts per component
- ✅ Flexible service types
- ✅ OCI registry support
- ✅ Comprehensive values documentation
- ✅ Template helpers for DRY principles
- ✅ NOTES.txt for post-install guidance

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n ollyscale
```

### View Logs

```bash
# UI logs
kubectl logs -n ollyscale -l app.kubernetes.io/component=ui -f

# OpAMP Server logs
kubectl logs -n ollyscale -l app.kubernetes.io/component=opamp-server -f

# OTLP Receiver logs
kubectl logs -n ollyscale -l app.kubernetes.io/component=otlp-receiver -f
```

### Validate Configuration

```bash
helm get values ollyscale -n ollyscale
```

### Debug Template Rendering

```bash
helm template ollyscale ./ollyscale --debug
```

## Contributing

Contributions are welcome! Please ensure:

1. Chart version is bumped following semver
2. `values.yaml` is documented with comments
3. Templates follow Helm best practices
4. All changes are tested with `helm lint` and `helm template`

## License

Apache 2.0 - See LICENSE file for details

## Support

- Documentation: <https://ollyscale.io/docs>
- GitHub Issues: <https://github.com/ollyscale/ollyscale/issues>
- Discussions: <https://github.com/ollyscale/ollyscale/discussions>
