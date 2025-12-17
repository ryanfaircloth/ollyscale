# TinyOlly Docker Hub Deployment Guide

## Overview

TinyOlly images are now published to Docker Hub for easy deployment. This guide covers all deployment scenarios and options.

---

## Quick Start

### Docker Deployment (Recommended for Most Users)

```bash
git clone https://github.com/tinyolly/tinyolly
cd tinyolly/docker
./01-start-core.sh
```

That's it! Images pull from Docker Hub automatically. No build required.

**Access UI**: http://localhost:5005

---

## Available Images on Docker Hub

All images support **linux/amd64** and **linux/arm64** architectures.

| Image | Description | Docker Hub Link |
|-------|-------------|-----------------|
| `tinyolly/ui:latest` | Web UI and REST API | [hub.docker.com/r/tinyolly/ui](https://hub.docker.com/r/tinyolly/ui) |
| `tinyolly/otlp-receiver:latest` | OTLP gRPC receiver | [hub.docker.com/r/tinyolly/otlp-receiver](https://hub.docker.com/r/tinyolly/otlp-receiver) |
| `tinyolly/opamp-server:latest` | OpAMP configuration server | [hub.docker.com/r/tinyolly/opamp-server](https://hub.docker.com/r/tinyolly/opamp-server) |
| `tinyolly/otel-supervisor:latest` | OpenTelemetry Collector | [hub.docker.com/r/tinyolly/otel-supervisor](https://hub.docker.com/r/tinyolly/otel-supervisor) |
| `tinyolly/python-base:latest` | Shared Python base image | [hub.docker.com/r/tinyolly/python-base](https://hub.docker.com/r/tinyolly/python-base) |

### Version Tags

- `:latest` - Latest stable release
- `:v2.0.0` - Specific version (semantic versioning)

---

## Deployment Scenarios

### 1. Docker - Full Stack (Default)

Includes OTel Collector, TinyOlly receiver, Redis, and UI.

```bash
cd docker
./01-start-core.sh
```

**What it does:**
- Pulls latest images from Docker Hub
- Starts all services via docker-compose
- Exposes UI on port 5005
- OTLP endpoints on 4317 (gRPC) and 4318 (HTTP)

**Stop services:**
```bash
./02-stop-core.sh
```

---

### 2. Docker - Core Only (No Collector)

Use your own OpenTelemetry Collector (e.g., Elastic EDOT).

```bash
cd docker-core-only
./01-start-core.sh
```

**Services:**
- TinyOlly OTLP receiver: `localhost:4343` (gRPC only)
- OpAMP server: `ws://localhost:4320/v1/opamp`
- UI: `http://localhost:5005`

Point your external collector to `localhost:4343`.

---

### 3. Docker - Local Development Builds

Build images locally instead of using Docker Hub.

**Full Stack (with collector):**
```bash
cd docker
./01-start-core-local.sh
```

**Core Only (no collector):**
```bash
cd docker-core-only
./01-start-core-local.sh
```

These use `docker-compose-tinyolly-core-local.yml` which builds images from source.

**When to use:**
- Developing TinyOlly itself
- Testing unreleased changes
- Contributing to the project

---

### 4. Kubernetes - Minikube

Deploy to local Kubernetes cluster.

**Option A: Use Docker Hub images (default)**

```bash
minikube start
cd k8s
./02-deploy-tinyolly.sh  # Skip build step
minikube tunnel  # In separate terminal
```

UI available at: `http://localhost:5002`

**Option B: Build locally in Minikube**

```bash
minikube start
cd k8s
./01-build-images.sh  # Build images locally
./02-deploy-tinyolly.sh
minikube tunnel  # In separate terminal
```

**Cleanup:**
```bash
./03-cleanup.sh
```

---

### 5. Kubernetes - Core Only

Deploy without bundled OTel Collector.

```bash
cd k8s-core-only
./01-deploy.sh
```

Services exposed:
- OTLP receiver: `tinyolly-otlp-receiver:4343`
- OpAMP server: `tinyolly-opamp-server:4320`
- UI: `http://localhost:5002`

---

## Configuration Files

### Docker Compose Files

| File | Purpose | Image Source |
|------|---------|--------------|
| `docker/docker-compose-tinyolly-core.yml` | Production (default) | Docker Hub |
| `docker/docker-compose-tinyolly-core-local.yml` | Local builds | Built locally |
| `docker-core-only/docker-compose-tinyolly-core.yml` | Core-only production | Docker Hub |
| `docker-core-only/docker-compose-tinyolly-core-local.yml` | Core-only local | Built locally |

### Kubernetes Manifests

| File | Purpose | Image Reference |
|------|---------|-----------------|
| `k8s/tinyolly-ui.yaml` | UI deployment | `tinyolly/ui:latest` |
| `k8s/tinyolly-otlp-receiver.yaml` | Receiver deployment | `tinyolly/otlp-receiver:latest` |
| `k8s/tinyolly-opamp-server.yaml` | OpAMP server | `tinyolly/opamp-server:latest` |
| `k8s/otel-collector.yaml` | Collector deployment | `tinyolly/otel-supervisor:latest` |

All manifests use `imagePullPolicy: Always` to pull from Docker Hub.

---

## Using Specific Versions

### Pin to Specific Version

Edit docker-compose or Kubernetes manifests:

```yaml
services:
  tinyolly-ui:
    image: tinyolly/ui:v2.0.0  # Instead of :latest
```

### Pull Specific Version

```bash
docker pull tinyolly/ui:v2.0.0
docker pull tinyolly/otlp-receiver:v2.0.0
```

---

## Developer Workflows

### Building and Testing Locally

1. **Make changes to code**
2. **Test with local build:**
   ```bash
   cd docker
   ./01-start-core-local.sh
   ```
3. **Verify changes work**

### Publishing to Docker Hub (Maintainers Only)

1. **Login to Docker Hub:**
   ```bash
   cd docker
   ./docker-hub-login.sh
   ```

2. **Build and push new version:**
   ```bash
   ./build-and-push-images.sh v2.0.1
   ```

3. **Update latest tag:**
   ```bash
   ./build-and-push-images.sh latest
   ```

This builds multi-arch images (amd64 + arm64) and pushes to Docker Hub.

---

## Environment Variables

### Common Variables

All deployments support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `tinyolly-redis` | Redis server hostname |
| `REDIS_PORT` | `6579` | Redis server port |
| `OTEL_SERVICE_NAME` | Component name | Service name for telemetry |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Varies | OTLP endpoint URL |

### Docker-Specific

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOYMENT_ENV` | `docker` | Deployment environment identifier |

### Kubernetes-Specific

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOYMENT_ENV` | `kubernetes` | Deployment environment identifier |

---

## Troubleshooting

### Images Not Pulling

**Problem:** `docker pull tinyolly/ui:latest` fails

**Solution:**
1. Check internet connection
2. Verify Docker Hub is accessible
3. Try with explicit version: `docker pull tinyolly/ui:v2.0.0`

### Local Build Needed

**Problem:** Need to test unreleased changes

**Solution:** Use local build scripts:
```bash
# Docker
cd docker
./01-start-core-local.sh

# Kubernetes
cd k8s
./01-build-images.sh
./02-deploy-tinyolly.sh
```

### Wrong Architecture

**Problem:** Image doesn't work on Apple Silicon or Intel

**Solution:** All images are multi-arch. Docker automatically pulls the correct architecture. If issues persist:
```bash
docker pull --platform linux/arm64 tinyolly/ui:latest  # Apple Silicon
docker pull --platform linux/amd64 tinyolly/ui:latest  # Intel/AMD
```

### Image Already Exists Locally

**Problem:** Old local image conflicts with Docker Hub image

**Solution:** Force pull from Docker Hub:
```bash
docker pull tinyolly/ui:latest
docker-compose up -d --force-recreate
```

Or remove local images:
```bash
docker rmi tinyolly/ui:latest
docker rmi tinyolly-ui:latest  # Old naming
```

---

## File Reference

### Updated for Docker Hub

**Dockerfiles:**
- `docker/dockerfiles/Dockerfile.tinyolly-ui` - Uses `FROM tinyolly/python-base:latest`
- `docker/dockerfiles/Dockerfile.tinyolly-otlp-receiver` - Uses `FROM tinyolly/python-base:latest`

**Docker Compose:**
- `docker/docker-compose-tinyolly-core.yml` - Uses Docker Hub images
- `docker-core-only/docker-compose-tinyolly-core.yml` - Uses Docker Hub images

**Kubernetes:**
- All `k8s/*.yaml` files - Use `tinyolly/*:latest` images
- All `k8s-core-only/*.yaml` files - Use `tinyolly/*:latest` images

**Scripts:**
- `docker/01-start-core.sh` - Pulls from Docker Hub
- `docker-core-only/01-start-core.sh` - Pulls from Docker Hub
- `k8s/01-build-images.sh` - Optional local build (updated image names)

### New Files

**Build & Deploy:**
- `docker/build-and-push-images.sh` - Build and publish to Docker Hub
- `docker/docker-hub-login.sh` - Docker Hub authentication helper
- `docker/01-start-core-local.sh` - Local build deployment (full stack)
- `docker-core-only/01-start-core-local.sh` - Local build deployment (core-only)

**Compose Files:**
- `docker/docker-compose-tinyolly-core-local.yml` - Local build variant (full stack)
- `docker-core-only/docker-compose-tinyolly-core-local.yml` - Core-only local build

**Documentation:**
- `DOCKER_HUB_MIGRATION_PLAN.md` - Migration plan
- `DOCKER_HUB_MIGRATION_COMPLETE.md` - Migration completion report
- `DOCKER_HUB_DEPLOYMENT_GUIDE.md` - This file
- `DOCKER_HUB_MIGRATION_SUMMARY.md` - Quick reference summary

---

## Comparison: Before vs After

### Before (Local Builds)

```bash
cd docker
./01-start-core.sh
# Building shared Python base image...
# Building tinyolly-ui...
# Building tinyolly-otlp-receiver...
# ... 10-15 minutes of building ...
```

**Time:** 10-15 minutes
**Requires:** Docker build tools, Go compiler, etc.

### After (Docker Hub)

```bash
cd docker
./01-start-core.sh
# Pulling latest TinyOlly images from Docker Hub...
# ✓ Images pulled successfully
```

**Time:** 30-60 seconds
**Requires:** Only Docker runtime

---

## Best Practices

### Production Deployments

1. **Pin versions** - Use specific tags like `:v2.0.0` instead of `:latest`
2. **Test first** - Always test in non-production before upgrading
3. **Monitor logs** - Check `docker logs <container>` after deployment
4. **Backup Redis** - Redis data is ephemeral by default (30-minute TTL)

### Development

1. **Use local builds** - Test changes with local build scripts
2. **Don't push `:latest`** - Only maintainers should update `:latest` tag
3. **Version your changes** - Use semantic versioning for releases

### Kubernetes

1. **Resource limits** - All manifests include resource requests/limits
2. **Health checks** - Liveness and readiness probes configured
3. **minikube tunnel** - Required for LoadBalancer services

---

## FAQ

### Q: Do I need to build images myself?

**A:** No! Images are pre-built on Docker Hub. Just run `./01-start-core.sh`.

### Q: How do I update to a new version?

**A:** Pull the latest and recreate containers:
```bash
docker-compose pull
docker-compose up -d --force-recreate
```

### Q: Can I use this in production?

**A:** Yes, but:
- Pin specific versions (`:v2.0.0` not `:latest`)
- Review the BSD 3-Clause license for commercial use requirements
- Consider persistent storage for Redis if needed

### Q: Which architecture is supported?

**A:** Both linux/amd64 (Intel/AMD) and linux/arm64 (Apple Silicon, ARM servers).

### Q: How do I build images myself?

**A:** Use local build scripts:
- Docker (full stack): `./docker/01-start-core-local.sh`
- Docker (core-only): `./docker-core-only/01-start-core-local.sh`
- Kubernetes: `./k8s/01-build-images.sh`

### Q: Where are demo apps?

**A:** Demo apps (docker-demo, k8s-demo) still build locally as they're examples, not core TinyOlly components.

---

## Support

- **Documentation**: [tinyolly.github.io/tinyolly](https://tinyolly.github.io/tinyolly/)
- **GitHub**: [github.com/tinyolly/tinyolly](https://github.com/tinyolly/tinyolly)
- **Issues**: [github.com/tinyolly/tinyolly/issues](https://github.com/tinyolly/tinyolly/issues)
- **Docker Hub**: [hub.docker.com/u/tinyolly](https://hub.docker.com/u/tinyolly)

---

**Last Updated:** December 16, 2025
**TinyOlly Version:** v2.0.0+
