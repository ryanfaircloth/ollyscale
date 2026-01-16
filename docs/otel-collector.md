# OpenTelemetry Collector

<div align="center">
  <img src="../images/collector.png" alt="OpenTelemetry Collector Configuration" width="700">
  <p><em>OpenTelemetry Collector configuration management via OpAMP</em></p>
</div>

---

ollyScale uses the [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) as the telemetry ingestion and shipping layer. The collector receives telemetry from your applications and forwards it to ollyScale's OTLP receiver.

## OpenTelemetry Collector + OpAMP Config Page

ollyScale includes a web interface for managing OpenTelemetry Collector configurations via the OpAMP (Open Agent Management Protocol). Access this page through the **"OpenTelemetry Collector + OpAMP Config"** tab in the ollyScale UI.

**Features:**

- View current configuration from connected collectors
- Apply configuration changes with real-time validation
- Browse configuration templates for common use cases
- Monitor OpAMP server status and connected agents
- Preview configuration diffs before applying

**Requirements:**

- Your collector must be configured with the OpAMP extension (see [OpAMP Configuration](#opamp-configuration-optional) below)
- Collector must be connected to the OpAMP server

## Configuration

ollyScale includes a sample collector configuration that you can customize for your needs. The configuration files are located at:

- **Docker**: `docker/otelcol-configs/config.yaml`
- **Kubernetes (Helm)**: Configured via Helm values - see `charts/ollyscale/values.yaml` for OTel Collector settings

## Default Configuration

The default configuration includes:

- **OTLP Receivers**: Accepts telemetry on ports 4317 (gRPC) and 4318 (HTTP)
- **OpAMP Extension**: Enables remote configuration management via ollyScale UI
- **Span Metrics Connector**: Automatically generates RED metrics from traces
- **Batch Processor**: Batches telemetry for efficient processing
- **OTLP Exporter**: Forwards all telemetry to ollyScale's OTLP receiver

## Customization Examples

You can extend the collector configuration to add additional capabilities. The collector uses the `otel/opentelemetry-collector-contrib` image which includes:

- **Receivers**: OTLP, Prometheus, Jaeger, Zipkin, and many more
- **Processors**: Batch, Memory Limiter, Resource Detection, Tail Sampling, Filtering
- **Connectors**: Span Metrics, Service Graph
- **Exporters**: OTLP, Prometheus, Logging, and many more

For a complete list of available components, see the [OpenTelemetry Collector Contrib documentation](https://github.com/open-telemetry/opentelemetry-collector-contrib).

## Applying Changes

### Docker

After modifying `docker/otelcol-configs/config.yaml` rebuild/restart using:

```bash
cd docker
./01-start-core.sh
```

### Kubernetes

When deployed via Helm, the OTel Collector is managed by the OpenTelemetry Operator. To customize the configuration:

1. Edit `charts/ollyscale/values.yaml` under the `otelCollector` section
2. Apply changes:

   ```bash
   cd charts
   helm upgrade ollyscale ./ollyscale -n ollyscale
   ```

Alternatively, patch the OpenTelemetryCollector custom resource directly:

```bash
kubectl edit opentelemetrycollector ollyscale-otel-collector -n ollyscale
```

## Using Your Own Collector

You can use your own OpenTelemetry Collector instance instead of the one bundled with ollyScale. This is useful if you have an existing collector setup or want to test specific collector configurations.

To do this, deploy the **Core-Only** version of ollyScale (see [Docker Deployment](docker.md#5-ollyscale-core-only-deployment-use-your-own-docker-opentelemetry-collector) or [Kubernetes Deployment](kubernetes.md#4-ollyscale-core-only-deployment-use-your-own-kubernetes-opentelemetry-collector)).

Then, configure your collector's OTLP exporter to send data to the ollyScale Receiver:

- **Endpoint**: `ollyscale-otlp-receiver:4343` (or `localhost:4343` from host)
- **Protocol**: gRPC
- **TLS**: Insecure (or configured as needed)

Example Exporter Configuration:

```yaml
exporters:
  otlp:
    endpoint: "ollyscale-otlp-receiver:4343"
    tls:
      insecure: true
```

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

The default configuration template (located at `docker/otelcol-configs/config.yaml`) shows a complete example with OTLP receivers, OpAMP extension, batch processing, and spanmetrics connector. Your collector will connect to the OpAMP server and receive configuration updates through the ollyScale UI.
