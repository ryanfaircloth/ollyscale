# TinyOlly Demo Apps - Docker Hub Publishing Guide

## Overview

This guide explains how to optionally publish and use demo application images from Docker Hub.

**Note:** Demo apps are **examples** and most users build them locally. Publishing to Docker Hub is optional and primarily for maintainers to speed up demo deployments.

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

## Using Pre-Built Demo Images

### Option 1: Use Docker Hub Images (Faster)

**Docker Demo:**
```bash
cd docker-demo
docker-compose -f docker-compose-demo-dockerhub.yml up -d
```

**AI Agent Demo:**
```bash
cd docker-ai-agent-demo
docker-compose -f docker-compose-dockerhub.yml up -d
```

**Benefits:**
- Instant deployment (no build time)
- Consistent across environments
- Smaller download (optimized layers)

### Option 2: Build Locally (Default)

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
- Can modify demo code
- No Docker Hub dependency
- Useful for development

---

## File Reference

### Build Scripts (New)

**Docker Demo:**
- `/docker-demo/build-and-push-demo-images.sh` - Build and push to Docker Hub

**AI Agent Demo:**
- `/docker-ai-agent-demo/build-and-push-ai-demo-image.sh` - Build and push to Docker Hub

### Compose Files

**Docker Demo:**
- `docker-compose-demo.yml` - Local builds (default)
- `docker-compose-demo-dockerhub.yml` - Uses Docker Hub images

**AI Agent Demo:**
- `docker-compose.yml` - Local build (default)
- `docker-compose-dockerhub.yml` - Uses Docker Hub images

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

3. **Update docker-compose-dockerhub.yml** (if using specific version)
   ```yaml
   services:
     demo-frontend:
       image: tinyolly/demo-frontend:v2.1.0  # Pin to version
   ```

4. **Test deployment**
   ```bash
   docker-compose -f docker-compose-demo-dockerhub.yml up -d
   ```

---

## Docker Hub Images

When published, these images will be available at:

- https://hub.docker.com/r/tinyolly/demo-frontend
- https://hub.docker.com/r/tinyolly/demo-backend
- https://hub.docker.com/r/tinyolly/ai-agent-demo

**Architectures:** linux/amd64, linux/arm64

---

## Why Demos Build Locally by Default

1. **Examples** - Users often modify demo code to learn
2. **Small apps** - Build time is minimal (<1 minute)
3. **No dependency** - Works without Docker Hub access
4. **Educational** - Shows how to containerize apps

---

## Decision Matrix

| Scenario | Use Local Build | Use Docker Hub |
|----------|----------------|----------------|
| First time user | ✅ Default | ⚠️ Optional |
| Workshop/demo | ⚠️ Slower | ✅ Faster setup |
| Modifying demo code | ✅ Required | ❌ Can't modify |
| Production use | ❌ Not for production | ❌ Not for production |
| Testing TinyOlly | ✅ Recommended | ⚠️ Optional |

**Note:** Demo apps are **never** for production use. They're examples only.

---

## FAQ

### Q: Should I publish demo apps to Docker Hub?

**A:** Only if you're a TinyOlly maintainer. Regular users should build locally.

### Q: Why aren't demos on Docker Hub by default?

**A:** They're examples meant to be modified and learned from. Building locally is educational.

### Q: What if I want faster demo deployment?

**A:** You can publish your own fork to your Docker Hub account:
```bash
export DOCKER_HUB_ORG=myusername
cd docker-demo
./build-and-push-demo-images.sh
```

### Q: Can I use demo images in production?

**A:** No! Demo apps are simple examples, not production-ready applications. Build your own apps following the patterns shown in the demos.

---

## Summary

- ✅ Build scripts created for demo apps
- ✅ Docker Hub compose variants created
- ⚠️ Publishing is optional (local builds recommended)
- ✅ Useful for maintainers and workshop scenarios
- ❌ Not required for regular users

**Default behavior:** Demos build locally (unchanged)
**Optional behavior:** Use pre-built images for faster deployment
