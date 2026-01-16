<div align="center">
  <img src="images/ollyscaletitle.svg" alt="ollyScale" width="500"><br>
  <b>Desktop-First Observability Platform for Local Development</b>
</div>

---

## Introducing ollyScale

ollyScale is an OpenTelemetry-native observability platform evolved from the excellent TinyOlly project.

**Repository:** [https://github.com/ryanfaircloth/ollyscale](https://github.com/ryanfaircloth/ollyscale)

```bash
git clone https://github.com/ryanfaircloth/ollyscale
```

### Why ollyScale?

Why send telemetry to a cloud observability platform while coding? Why not have one on your desktop?

ollyScale is a **lightweight OpenTelemetry-native observability platform** built to visualize and correlate logs, metrics, and traces. No 3rd party observability tools - just Python (FastAPI), Redis, OpenAPI, and JavaScript.

### Key Features

- **Development-focused** - Perfect your app's telemetry locally before production
- **Full OpenTelemetry support** - Native OTLP ingestion (gRPC & HTTP)
- **Pre-built Docker images** - Deploy in ~30 seconds from Docker Hub
- **Multi-architecture** - Supports linux/amd64 and linux/arm64 (Apple Silicon)
- **Trace correlation** - Link logs, metrics, and traces automatically
- **Metrics Explorer** - Analyze cardinality, labels, and raw series data
- **Service catalog** - RED metrics (Rate, Errors, Duration) for all services
- **Interactive service map** - Visualize dependencies and call graphs
- **OpenTelemetry Collector management** - Remote configuration management via OpAMP protocol
- **REST API** - Programmatic access with OpenAPI documentation
- **Zero vendor lock-in** - Works with any OTel Collector distribution

!!! note "Local Development Only"
ollyScale is _not_ designed to compete with production observability platforms! It's for local development only and is not focused on infrastructure monitoring at this time.

### Platform Support

Tested on:

- Docker Desktop (macOS Apple Silicon)
- Minikube Kubernetes (macOS Apple Silicon)
- May work on other platforms

### Quick Start

Ready to try ollyScale? Check out the [Quick Start Guide](quickstart.md) to get running in under 5 minutes!

---

## Screenshots

<div align="center">
  <table>
    <tr>
      <td align="center" width="33%">
        <img src="images/traces.png" width="300"><br>
        <em>Trace Waterfall with Correlated Logs</em>
      </td>
      <td align="center" width="33%">
        <img src="images/logs1.png" width="300"><br>
        <em>Real-time Logs with Filtering</em>
      </td>
      <td align="center" width="33%">
        <img src="images/metrics.png" width="300"><br>
        <em>Metrics with Chart Visualization</em>
      </td>
    </tr>
    <tr>
      <td align="center" width="33%">
        <img src="images/servicecatalog.png" width="300"><br>
        <em>Service Catalog with RED Metrics</em>
      </td>
      <td align="center" width="33%">
        <img src="images/servicemap.png" width="300"><br>
        <em>Interactive Service Dependency Map</em>
      </td>
      <td align="center" width="33%">
        <img src="images/collector.png" width="300"><br>
        <em>OTel Collector Configuration (OpAMP)</em>
      </td>
    </tr>
  </table>
</div>

---

<div align="center">
  <p>Built for the OpenTelemetry community</p>
  <p>
    <a href="https://github.com/ryanfaircloth/ollyscale">GitHub</a> •
    <a href="https://github.com/ryanfaircloth/ollyscale/issues">Issues</a>
  </p>
</div>
