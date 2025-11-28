# TinyOlly Core v1.0.0

First release of TinyOlly - a lightweight OpenTelemetry-native observability platform for local development.

## What's Included

- **Core Application**: Complete TinyOlly observability platform
  - OTLP Receiver (FastAPI)
  - Web UI with real-time visualization
  - Redis storage backend
  - Docker and Kubernetes deployment configurations

## Quick Start

```bash
git clone https://github.com/tinyolly/tinyolly
cd tinyolly
git checkout v1.0.0

# Docker deployment
cd docker
./01-start-core.sh
to stop  
./02-stop-core.sh  

# Or Kubernetes deployment
cd k8s
./01-build-images.sh
kubectl apply -f .
to stop
./02-cleanup.sh  
```

## Features

- Real-time visualization of traces, logs, and metrics
- Service catalog with RED metrics
- Interactive service map
- Full OpenTelemetry format support
- REST API with OpenAPI documentation
- Cardinality protection

See [README.md](README.md) for full documentation.

