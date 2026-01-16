# Technical Details

## Architecture

<div align="center">
  <img src="../images/architecture.png" alt="ollyScale Architecture" width="700">
</div>

---

## Data Storage

- **Format**: Full OpenTelemetry (OTEL) format for traces, logs, and metrics
- **Redis**: All telemetry stored with 30-minute TTL (compressed with ZSTD + msgpack)
- **Sorted Sets**: Time-series data indexed by timestamp
- **Correlation**: Native trace-metric-log correlation via trace/span IDs
- **Cardinality Protection**: Prevents metric explosion
- **No Persistence**: Data vanishes after TTL (ephemeral dev tool)

---

## OTLP Compatibility

ollyScale is **fully OpenTelemetry-native**:

- **Ingestion**: Accepts OTLP/gRPC (primary) and OTLP/HTTP
- **Storage**: Stores traces, logs, and metrics in full OTEL format with resources, scopes, and attributes
- **Correlation**: Native support for trace/span ID correlation across all telemetry types
- **REST API**: Exposes OTEL-formatted JSON for programmatic access
- **Control Plane**: OpenTelemetry Collector OpAmp for dynamic configuration
