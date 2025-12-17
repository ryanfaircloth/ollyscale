# TinyOlly Demo Apps - Docker Hub Deployment Guide

## Overview

This guide explains how to use pre-built demo application images from Docker Hub and how to build them locally for development.

**Note:** Demo apps use Docker Hub by default for faster deployment. Local builds are available for development and customization.

---

## Demo Applications

### 1. Docker Demo Apps
Location: `/docker-demo/`

**Apps:**
- `demo-frontend` - Flask frontend with auto-generated traffic
- `demo-backend` - Flask backend service

**Purpose:** Demonstrate distributed tracing, logs, and metrics with TinyOlly

### 2. AI Agent Demo
Location: `/docker-ai-agent-demo/`

**Apps:**
- `ai-agent-demo` - Python agent with OpenTelemetry auto-instrumentation for Ollama
- Uses `ollama/ollama:latest` (already on Docker Hub)

**Purpose:** Demonstrate GenAI observability with zero-code instrumentation

---

## Building and Publishing (Maintainers Only)

### Prerequisites

1. Docker Hub account with access to `tinyolly` organization
2. Docker Buildx configured
3. Logged in to Docker Hub

```bash
docker login
```

### Build and Push Docker Demo Apps

```bash
cd docker-demo
./build-and-push-demo-images.sh v2.0.0
```

This publishes:
- `tinyolly/demo-frontend:latest` and `:v2.0.0`
- `tinyolly/demo-backend:latest` and `:v2.0.0`

### Build and Push AI Agent Demo

```bash
cd docker-ai-agent-demo
./build-and-push-ai-demo-image.sh v2.0.0
```

This publishes:
- `tinyolly/ai-agent-demo:latest` and `:v2.0.0`

---

## Using Demo Applications

### Option 1: Use Docker Hub Images (Default - Recommended)

**Docker Demo:**
```bash
cd docker-demo
./01-deploy-demo.sh
```

**AI Agent Demo:**
```bash
cd docker-ai-agent-demo
./01-deploy-ai-demo.sh
```

**Benefits:**
- Instant deployment (~30 seconds vs 5-10 minutes)
- Consistent across environments
- Multi-architecture support (amd64, arm64)
- No build time or dependencies

### Option 2: Build Locally (For Development)

**Docker Demo:**
```bash
cd docker-demo
./01-deploy-demo-local.sh
```

**AI Agent Demo:**
```bash
cd docker-ai-agent-demo
./01-deploy-ai-demo-local.sh
```

**Benefits:**
- Can modify demo code for testing
- No Docker Hub dependency
- Useful for demo app development

---

## File Reference

### Build Scripts (New)

**Docker Demo:**
- `/docker-demo/build-and-push-demo-images.sh` - Build and push to Docker Hub

**AI Agent Demo:**
- `/docker-ai-agent-demo/build-and-push-ai-demo-image.sh` - Build and push to Docker Hub

### Compose Files

**Docker Demo:**
- `docker-compose-demo.yml` - Uses Docker Hub images (default)
- `docker-compose-demo-local.yml` - Local builds (development)

**AI Agent Demo:**
- `docker-compose.yml` - Uses Docker Hub images (default)
- `docker-compose-local.yml` - Local builds (development)

---

## Publishing Workflow (Maintainers)

When releasing a new TinyOlly version:

1. **Update demo apps** (if needed)
   ```bash
   cd docker-demo
   # Make changes to app.py, backend-service.py, etc.
   ```

2. **Build and push with version tag**
   ```bash
   ./build-and-push-demo-images.sh v2.1.0

   cd ../docker-ai-agent-demo
   ./build-and-push-ai-demo-image.sh v2.1.0
   ```

3. **Update docker-compose-demo.yml** (if pinning to specific version)
   ```yaml
   services:
     demo-frontend:
       image: tinyolly/demo-frontend:v2.1.0  # Pin to version
   ```

4. **Test deployment**
   ```bash
   cd docker-demo
   ./01-deploy-demo.sh
   ```

---

## Docker Hub Images

When published, these images will be available at:

- https://hub.docker.com/r/tinyolly/demo-frontend
- https://hub.docker.com/r/tinyolly/demo-backend
- https://hub.docker.com/r/tinyolly/ai-agent-demo

**Architectures:** linux/amd64, linux/arm64

---

## Why Demos Use Docker Hub by Default

1. **Speed** - Deployment in ~30 seconds vs 5-10 minutes
2. **Consistency** - Same images across all environments
3. **Multi-arch** - Works on both Intel and ARM (Apple Silicon)
4. **Simplicity** - No build tools required

Local builds are still available for users who want to modify demo code.

---

## Decision Matrix

| Scenario | Use Docker Hub | Use Local Build |
|----------|----------------|-----------------|
| First time user | ✅ Default (faster) | ⚠️ Optional |
| Workshop/demo | ✅ Faster setup | ⚠️ Slower |
| Modifying demo code | ❌ Can't modify | ✅ Required |
| Production use | ❌ Not for production | ❌ Not for production |
| Testing TinyOlly | ✅ Recommended (faster) | ⚠️ Optional |

**Note:** Demo apps are **never** for production use. They're examples only.

---

## FAQ

### Q: Should I publish demo apps to Docker Hub?

**A:** Only if you're a TinyOlly maintainer. Regular users use pre-built images from `tinyolly` organization.

### Q: Can I modify the demo apps?

**A:** Yes! Use the local build scripts (`01-deploy-demo-local.sh`) to build your modified versions.

### Q: What if I want to publish my own modified demos?

**A:** You can publish to your own Docker Hub account:
```bash
export DOCKER_HUB_ORG=myusername
cd docker-demo
./build-and-push-demo-images.sh
# Then update compose files to use your org name
```

### Q: Can I use demo images in production?

**A:** No! Demo apps are simple examples, not production-ready applications. Build your own apps following the patterns shown in the demos.

---

## Summary

- ✅ Build scripts created for demo apps
- ✅ Images published to Docker Hub (`tinyolly` organization)
- ✅ Docker Hub deployment is default (faster)
- ✅ Local build scripts available for development
- ✅ Multi-architecture support (amd64, arm64)

**Default behavior:** Deploy from Docker Hub (~30 seconds)
**Optional behavior:** Build locally for development/customization
