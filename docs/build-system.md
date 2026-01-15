# TinyOlly Build System - Deliverables & Dependencies

**Document Version**: 2.1  
**Last Updated**: January 15, 2026  
**Status**: Active

## Overview

This document maps TinyOlly's **deliverable artifacts** and traces their build dependencies. We work backwards from what we ship to understand what needs to be built and in what order.

**Purpose**:

- Identify what artifacts we publish to registries
- Understand rebuild requirements when source changes
- Optimize build order and minimize rebuilds
- Document the delivery pipeline

---

## Our Deliverables

TinyOlly produces **two types of artifacts** that are published to OCI registries:

### 1. OCI Container Images (4 images)

### 2. Helm Charts (2 charts)

All other scripts, configurations, and source code exist solely to produce these deliverables.

---

## Deliverable #1: OCI Container Images

We publish **4 container images** to OCI-compatible registries:

```
DELIVERABLE: OCI Container Images
├─ tinyolly/tinyolly          (Python backend - FastAPI + OTLP receiver)
├─ tinyolly/webui             (Static frontend - nginx + TypeScript/Vite)
├─ tinyolly/opamp-server      (OpAMP configuration server)
└─ tinyolly/demo              (Demo application)
```

### Image: `tinyolly/tinyolly`

**What it is**: Python backend application that runs as either API server or OTLP receiver

**Published to**:

- Production: `ghcr.io/ryanfaircloth/tinyolly/tinyolly:VERSION`
- Local dev: `registry.tinyolly.test:49443/tinyolly/tinyolly:VERSION`

**Run modes** (controlled by `MODE` env var):

- `MODE=ui` → FastAPI REST API server on port 5002
- `MODE=receiver` → gRPC OTLP receiver on port 4343

**Built from**:

- **Dockerfile**: `apps/tinyolly/Dockerfile`
- **Base image**: `python:3.14-slim`
- **Source files** (all from `apps/tinyolly/`):
  - `main.py` - Entry point that selects mode
  - `models.py` - Pydantic data models
  - `requirements.txt` - Python dependencies
  - `app/` - FastAPI routers and API endpoints
  - `receiver/` - gRPC receiver for receiver mode
  - `common/` - Shared utilities (storage, OTLP parsing)
docker buildx build --platform linux/amd64,linux/arm64 \
  -f apps/tinyolly/Dockerfile \
  -t ghcr.io/ryanfaircloth/tinyolly/tinyolly:v2.1.8 \
  --push apps/tinyolly/

# Local dev (single-arch)
podman build -f apps/tinyolly/Dockerfile \
  -t registry.tinyolly.test:49443/tinyolly/tinyolly:v2.1.x-feature \
  apps/tinyolly/
```

**Rebuild triggers**:

- Change to any file in `apps/tinyolly/`
- Change to `requirements.txt`
- Change to Dockerfile

---

### Image: `tinyolly/webui`

**What it is**: Static web frontend served by nginx

**Published to**:

- Production: `ghcr.io/ryanfaircloth/tinyolly/webui:VERSION`
- Local dev: `registry.tinyolly.test:49443/tinyolly/webui:VERSION`

**Functionality**:

- TypeScript/Vite SPA with modern build tooling
- Served by nginx on port 80
- Connects to backend API at `/api/*`

**Built from**:

- **Dockerfile**: `apps/tinyolly-ui/Dockerfile`
- **Base image**: `node:20-alpine` (build), `nginx:alpine` (runtime)
- **Source files** (from `apps/tinyolly-ui/`):
  - `src/` - TypeScript modules and main entry point
  - `src/modules/` - API client, traces, serviceMap, metrics, etc.
  - `index.html` - HTML template
  - `vite.config.js` - Vite build configuration
  - `package.json` - NPM dependencies
  - `nginx/` - nginx configuration

**Build command**:

```bash
# Production (multi-arch)
docker buildx build --platform linux/amd64,linux/arm64 \
  -f apps/tinyolly-ui/Dockerfile \
  -t ghcr.io/ryanfaircloth/tinyolly/webui:v2.1.8 \
  --push apps/tinyolly-ui/

# Local dev (single-arch)
podman build -f apps/tinyolly-ui/Dockerfile \
  -t registry.tinyolly.test:49443/tinyolly/webui:v2.1.x-feature \
  apps/tinyolly-ui/
```

**Rebuild triggers**:

- Change to any file in `apps/tinyolly-ui/src/`
- Change to `package.json`
- Change to Dockerfile
- Change to nginx configuration

---

### Image: `tinyolly/opamp-server`

**What it is**: OpAMP server for remote OpenTelemetry Collector configuration

**Published to**:

- Production: `ghcr.io/ryanfaircloth/tinyolly/opamp-server:VERSION`
- Local dev: `registry.tinyolly.test:49443/tinyolly/opamp-server:VERSION`

**Functionality**:

- OpAMP protocol endpoint on port 4320
- REST API for config management on port 4321

**Built from**:

- **Dockerfile**: `apps/opamp-server/Dockerfile`
- **Base image**: `golang:1.25-alpine` (build), `scratch` (runtime)
- **Source files** (from `apps/opamp-server/`):
  - `main.go` - OpAMP server implementation
  - `go.mod` - Go module definition

**Build command**:

```bash
# Production (multi-arch)
docker buildx build --platform linux/amd64,linux/arm64 \
  -f apps/opamp-server/Dockerfile \
  -t ghcr.io/ryanfaircloth/tinyolly/opamp-server:v2.1.8 \
  --push apps/opamp-server/

# Local dev (single-arch)
podman build -f apps/opamp-server/Dockerfile \
  -t registry.tinyolly.test:49443/tinyolly/opamp-server:v2.1.x-feature \
  apps/opamp-server/
```

**Rebuild triggers**:

- Change to `main.go`
- Change to `go.mod`
- Change to Dockerfile

---

### Image: `tinyolly/demo`

**What it is**: Unified demo application with frontend and backend

**Published to**:

- Production: `ghcr.io/ryanfaircloth/tinyolly/demo:VERSION`
- Local dev: `registry.tinyolly.test:49443/tinyolly/demo:VERSION`

**Functionality**:

- Generates sample traces, logs, and metrics
- Can run as frontend or backend via `MODE` env var

**Built from**:

- **Dockerfile**: `apps/demo/Dockerfile`
- **Base image**: `python:3.12-slim`
- **Source files** (from `apps/demo/`):
  - `frontend.py` - Demo frontend service
  - `backend.py` - Demo backend service
  - `requirements.txt` - Python dependencies

**Build command**:

```bash
# Production (multi-arch)
docker buildx build --platform linux/amd64,linux/arm64 \
  -f apps/demo/Dockerfile \
  -t ghcr.io/ryanfaircloth/tinyolly/demo:v2.1.8 \
  --push apps/demo/

# Local dev (single-arch)
podman build -f apps/demo/Dockerfile \
  -t registry.tinyolly.test:49443/tinyolly/demo:v2.1.x-feature \
  apps/demo/
```

**Rebuild triggers**:

- Change to `frontend.py` or `backend.py`
- Change to `requirements.txt`
- Change to Dockerfile

---

## Deliverable #2: Helm Charts

We publish **2 Helm charts** to OCI registries:

```
DELIVERABLE: Helm Charts (OCI format)
├─ tinyolly              (Main platform chart)
└─ tinyolly-demos        (Demo applications chart)
```

### Chart: `tinyolly`

**What it is**: Complete TinyOlly platform deployment

**Published to**:

- Production: `oci://ghcr.io/ryanfaircloth/tinyolly/charts/tinyolly:VERSION`
- Local dev: `oci://registry.tinyolly.test:49443/tinyolly/charts/tinyolly:VERSION`

**Contains**:

- Backend API deployment (uses `tinyolly/tinyolly:VERSION` with `MODE=ui`)
- Frontend webui deployment (uses `tinyolly/webui:VERSION`)
- OTLP receiver deployment (uses `tinyolly/tinyolly:VERSION` with `MODE=receiver`)
- OpAMP server deployment (uses `tinyolly/opamp-server:VERSION`)
- Redis StatefulSet
- OTel Collector DaemonSet (optional)
- OpenTelemetry Instrumentation CRs (optional)
- Services, ConfigMaps, Secrets

**Built from**:

- **Chart location**: `charts/tinyolly/`
- **Chart.yaml**: Metadata and version
- **values.yaml**: Default configuration
- **templates/**: Kubernetes manifests
  - `webui-deployment.yaml`
  - `frontend-deployment.yaml`
  - `otlp-receiver-deployment.yaml`
  - `opamp-server-deployment.yaml`
  - `redis-statefulset.yaml`
  - `otelcol-daemonset.yaml`
  - `instrumentation.yaml`
  - `service-*.yaml`
  - `configmap-*.yaml`

**Dependencies**:

- Requires container images to exist:
  - `tinyolly/webui:VERSION`
  - `tinyolly/tinyolly:VERSION`
  - `tinyolly/opamp-server:VERSION`
- May reference external charts (Redis Operator, OTel Operator)

**Build command**:

```bash
# Package chart
helm package charts/tinyolly/ -d charts/

# Push to OCI registry
helm push charts/tinyolly-0.1.1-v2.1.x-feature.tgz \
  oci://registry.tinyolly.test:49443/tinyolly/charts
```

**Version format**:

- Production: `0.1.1` (semantic version)
- Local dev: `0.1.1-v2.1.x-description`

**Rebuild triggers**:

- Change to any file in `charts/tinyolly/templates/`
- Change to `values.yaml`
- Change to `Chart.yaml`
- New container image version (update `appVersion`)

---

### Chart: `tinyolly-demos`

**What it is**: Demo applications for TinyOlly

**Published to**:

- Production: `oci://ghcr.io/ryanfaircloth/tinyolly/charts/tinyolly-demos:VERSION`
- Local dev: `oci://registry.tinyolly.test:49443/tinyolly/charts/tinyolly-demos:VERSION`

**Contains**:

- Demo frontend deployment (uses `tinyolly/demo:VERSION` with `MODE=frontend`)
- Demo backend deployment (uses `tinyolly/demo:VERSION` with `MODE=backend`)
- Traffic generator (optional)
- Services to wire frontend → backend

**Built from**:

- **Chart location**: `charts/tinyolly-demos/`
- **Chart.yaml**: Metadata and version
- **values.yaml**: Demo configuration
- **templates/**: Kubernetes manifests
  - `deployment-frontend.yaml`
  - `deployment-backend.yaml`
  - `job-traffic-generator.yaml`
  - `service-*.yaml`

**Dependencies**:

- Requires container image: `tinyolly/demo:VERSION`
- Expects `tinyolly` chart to be deployed (for OTLP endpoint)

**Build command**:

```bash
# Package chart
helm package charts/tinyolly-demos/ -d charts/

# Push to OCI registry
helm push charts/tinyolly-demos-0.1.5.tgz \
  oci://registry.tinyolly.test:49443/tinyolly/charts
```

**Rebuild triggers**:

- Change to any file in `charts/tinyolly-demos/templates/`
- Change to `values.yaml`
- Change to `Chart.yaml`
- New demo image version

---

## Dependency Graph (Backwards from Deliverables)

```
┌────────────────────────────────────────────────────────────────┐
│                    DELIVERABLE ARTIFACTS                        │
│                  (What we publish to registries)                │
└────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
     ┌───────────────────┐           ┌───────────────────┐
     │  OCI IMAGES (3)   │           │  HELM CHARTS (2)  │
     ├───────────────────┤           ├───────────────────┤
     │ 1. tinyolly       │           │ 1. tinyolly       │
     │ 2. opamp-server   │           │ 2. tinyolly-demos │
     │ 3. demo           │           └─────────┬─────────┘
     └─────────┬─────────┘                     │
               │                               │
               │          ┌────────────────────┘
               │          │
               ▼          ▼
     ┌─────────────────────────────────────────────────────┐
     │              BUILD INPUTS                           │
     │          (Dockerfiles + Source Code)                │
     └─────────────────────────────────────────────────────┘
               │
               ├─────────────────────────────────────┐
               │                                     │
               ▼                                     ▼
     ┌─────────────────────┐            ┌─────────────────────┐
     │  apps/tinyolly/     │            │ Chart.yaml          │
     │  Dockerfile         │            │ values.yaml         │
     │       +             │            │ templates/*.yaml    │
     │  ├─ main.py         │            └─────────────────────┘
     │  ├─ models.py       │                     ▲
     │  ├─ requirements.txt│                     │
     │  ├─ app/            │                     │
     │  ├─ receiver/       │            (Helm charts reference)
     │  ├─ common/         │            (image tags from above)
     │  ├─ static/         │
     │  └─ templates/      │
     └─────────────────────┘


```

**Key relationships**:

1. **Helm charts depend on container images** - Charts reference image tags
2. **Container images depend on source code** - Dockerfiles copy source into images
3. **Charts must be rebuilt** when image versions change (update `appVersion`)

---

## Build Scripts by Target

### Production Builds → GHCR (Multi-platform)

**Location**: `scripts/build/`  
**Registry**: `ghcr.io/ryanfaircloth/tinyolly/*`  
**Platforms**: `linux/amd64`, `linux/arm64`

| Script                     | Builds                                                 | Command                              |
| -------------------------- | ------------------------------------------------------ | ------------------------------------ |
| `02-build-core.sh VERSION` | tinyolly:VERSION<br>webui:VERSION<br>opamp-server:VERSION | Uses Docker Buildx<br>Multi-platform |
| `02-build-demo.sh VERSION` | demo:VERSION                                           | Uses Docker Buildx<br>Multi-platform |
| `02-build-all.sh VERSION`  | All images above                                       | Calls other scripts                  |
| `03-push-core.sh VERSION`  | N/A - pushes only                                      | Pushes to GHCR                       |
| `03-push-demo.sh VERSION`  | N/A - pushes only                                      | Pushes to GHCR                       |
| `03-push-all.sh VERSION`   | N/A - pushes only                                      | Pushes all to GHCR                   |

**Typical workflow**:

```bash
cd scripts/build
./02-build-all.sh v2.1.8    # Build all images (multi-arch)
./03-push-all.sh v2.1.8     # Push to ghcr.io
```

**Chart publishing** (separate process):

```bash
cd charts
./package.sh                # Package charts
./push-oci.sh               # Push to public registry
```

---

### Local Development Builds → Local Registry (Single-platform)

**Location**: `charts/`  
**Registry**: `registry.tinyolly.test:49443/tinyolly/*`  
**Platforms**: Native only (faster builds)

| Script                            | Builds                                                              | Description                                                                                                                           |
| --------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `build-and-push-local.sh VERSION` | 1. All 4 container images<br>2. tinyolly Helm chart | **Complete pipeline**:<br>- Build images<br>- Push to local registry<br>- Update Chart.yaml<br>- Package chart<br>- Push chart to OCI |

**What it does**:

```bash
# Example: ./build-and-push-local.sh v2.1.x-tail-sampling

# Step 1: Build images
podman build -f apps/tinyolly/Dockerfile \
  -t registry.tinyolly.test:49443/tinyolly/tinyolly:v2.1.x-tail-sampling \
  apps/tinyolly/

podman build -f apps/tinyolly-ui/Dockerfile \
  -t registry.tinyolly.test:49443/tinyolly/webui:v2.1.x-tail-sampling \
  apps/tinyolly-ui/

podman build -f apps/opamp-server/Dockerfile \
  -t registry.tinyolly.test:49443/tinyolly/opamp-server:v2.1.x-tail-sampling \
  apps/opamp-server/

podman build -f apps/demo/Dockerfile \
  -t registry.tinyolly.test:49443/tinyolly/demo:v2.1.x-tail-sampling \
  apps/demo/

# Step 2: Push images to local registry (external endpoint)
podman push --tls-verify=false registry.tinyolly.test:49443/tinyolly/tinyolly:v2.1.x-tail-sampling
# ... (webui, opamp-server, demo)

# Step 3: Update Chart.yaml version
sed -i '' "s/^version: .*/version: 0.1.1-v2.1.x-tail-sampling/" charts/tinyolly/Chart.yaml

# Step 4: Generate values-local-dev.yaml with INTERNAL registry
cat > values-local-dev.yaml <<EOF
ui:
  image:
    repository: docker-registry.registry.svc.cluster.local:5000/tinyolly/tinyolly
    tag: v2.1.x-tail-sampling
webui:
  image:
    repository: docker-registry.registry.svc.cluster.local:5000/tinyolly/webui
    tag: v2.1.x-tail-sampling
# ... etc
EOF

# Step 5: Package chart
helm package charts/tinyolly/ -d charts/

# Step 6: Push chart to OCI registry
helm push charts/tinyolly-0.1.1-v2.1.x-tail-sampling.tgz \
  oci://registry.tinyolly.test:49443/tinyolly/charts
```

**Deploy to cluster**:

```bash
# Update ArgoCD Application to use new chart version
cd .kind
terraform apply -replace='kubectl_manifest.observability_applications["observability/tinyolly.yaml"]' -auto-approve
```

---

### Deprecated Scripts (Do Not Use)

These scripts are no longer maintained and should not be used:

| Status        | Replacement                      | Notes                          |
| ------------- | -------------------------------- | ------------------------------ |
| 🗑️ Removed    | `charts/build-and-push-local.sh` | Old k8s/ scripts deleted       |
| 🗑️ Removed    | ArgoCD + Terraform pattern       | GitOps deployment recommended  |

---

## Registry Endpoints (Critical!)

TinyOlly uses **different registry endpoints** for build/push vs runtime deployment. This is a common source of confusion.

### The Same Physical Registry, Different Access Points

```
┌─────────────────────────────────────────────────────────────┐
│          LOCAL KUBERNETES CLUSTER REGISTRY                   │
│                  (One registry pod)                          │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  EXTERNAL    │  │   NODEPORT   │  │   INTERNAL   │
│  (Build)     │  │  (Alt Build) │  │  (Runtime)   │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ registry.    │  │ localhost:   │  │ docker-      │
│ tinyolly.    │  │ 30500        │  │ registry.    │
│ test:49443   │  │              │  │ registry.svc │
│              │  │              │  │ .cluster.    │
│              │  │              │  │ local:5000   │
│              │  │              │  │              │
│ Use: podman  │  │ Use: podman  │  │ Use: K8s pod │
│ push from    │  │ push from    │  │ image pull   │
│ desktop      │  │ desktop      │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Rules**:

1. **Build scripts** push to `registry.tinyolly.test:49443` (external endpoint)
2. **Helm values** reference `docker-registry.registry.svc.cluster.local:5000` (internal endpoint)
3. **Never** use `registry.tinyolly.test:49443` in pod image specs - cluster can't resolve it!

**Example** (`values-local-dev.yaml`):

```yaml
# ✅ CORRECT - internal endpoint for cluster
ui:
  image:
    repository: docker-registry.registry.svc.cluster.local:5000/tinyolly/tinyolly
    tag: v2.1.x-feature

# ❌ WRONG - external endpoint, pods can't pull
ui:
  image:
    repository: registry.tinyolly.test:49443/tinyolly/tinyolly
    tag: v2.1.x-feature
```

### Production Registry (GHCR)

**Endpoint**: `ghcr.io/ryanfaircloth/tinyolly/*`  
**Access**: Public (read), authenticated (write)  
**Usage**: Production releases only

---

## Complete Dependency Matrix

### What Triggers What?

| Change Type                               | Requires Rebuild             | Deployment Action                           |
| ----------------------------------------- | ---------------------------- | ------------------------------------------- |
| **Source Code**                           |                              |                                             |
| `apps/tinyolly/app/`                      | `tinyolly:VERSION` image     | Rebuild image → Update chart → Deploy       |
| `apps/tinyolly/receiver/`                 | `tinyolly:VERSION` image     | Rebuild image → Update chart → Deploy       |
| `apps/tinyolly/requirements.txt`          | `tinyolly:VERSION` image     | Rebuild image → Update chart → Deploy       |
| `apps/tinyolly-ui/src/`                   | `webui:VERSION` image        | Rebuild image → Update chart → Deploy       |
| `apps/tinyolly-ui/package.json`           | `webui:VERSION` image        | Rebuild image → Update chart → Deploy       |
| `apps/opamp-server/`                      | `opamp-server:VERSION` image | Rebuild image → Update chart → Deploy       |
| `apps/demo/frontend.py`                   | `demo:VERSION` image         | Rebuild image → Update demos chart → Deploy |
| `apps/demo/backend.py`                    | `demo:VERSION` image         | Rebuild image → Update demos chart → Deploy |
| **Dockerfiles**                           |                              |                                             |
| `apps/tinyolly/Dockerfile`                | `tinyolly:VERSION` image     | Rebuild image → Update chart → Deploy       |
| `apps/tinyolly-ui/Dockerfile`             | `webui:VERSION` image        | Rebuild image → Update chart → Deploy       |
| `apps/opamp-server/Dockerfile`            | `opamp-server:VERSION` image | Rebuild image → Update chart → Deploy       |
| `apps/demo/Dockerfile`                    | `demo:VERSION` image         | Rebuild image → Update demos chart → Deploy |
| **Helm Charts**                           |                              |                                             |
| `charts/tinyolly/templates/`              | `tinyolly` chart             | Package chart → Deploy                      |
| `charts/tinyolly/values.yaml`             | `tinyolly` chart             | Package chart → Deploy                      |
| `charts/tinyolly/Chart.yaml`              | `tinyolly` chart             | Package chart → Deploy                      |
| `charts/tinyolly-demos/templates/`        | `tinyolly-demos` chart       | Package chart → Deploy                      |
| **Deployment**                            |                              |                                             |
| `.kind/modules/main/argocd-applications/` | None (config only)           | `terraform apply`                           |

---

## Build Optimization Opportunities

### Current Issues

1. **No shared base image**: `tinyolly` image rebuilds all Python deps on every build
2. **No build caching**: Production builds use `--no-cache` flag
3. **Dockerfile redundancy**: Demo images duplicate patterns from main image
4. **Version coordination**: Chart version and image tags updated manually

### Improvement Proposals

#### 1. Create Python Base Image

```dockerfile
# NEW: Dockerfile.tinyolly-python-base
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Tag: tinyolly/python-base:v2.1
```

Then update `Dockerfile.tinyolly`:

```dockerfile
FROM tinyolly/python-base:v2.1  # ← Use base
# Only copy app code, deps already installed
```

**Benefit**: Faster builds when only code changes (not deps)

#### 2. Enable Build Caching for Local Builds

```bash
# Remove --no-cache flag from build scripts
docker buildx build ... # (no --no-cache)
```

**Benefit**: 5-10x faster iteration on small changes

#### 3. Single Multi-stage Dockerfile

Combine all demo variants into one Dockerfile:

```dockerfile
# Dockerfile.demo - unified
FROM python:3.12-slim AS base
# ... shared setup ...

FROM base AS frontend
COPY frontend.py .
CMD ["python", "frontend.py"]

FROM base AS backend
COPY backend.py .
CMD ["python", "backend.py"]
```

**Benefit**: DRY, easier to maintain

#### 4. Automated Version Management

```bash
# Extract version from git tag or commit
VERSION=$(git describe --tags --always)
# Auto-update Chart.yaml appVersion
yq eval ".appVersion = \"$VERSION\"" -i Chart.yaml
```

**Benefit**: Eliminate manual version sync errors

---

## Quick Reference: Build Commands

### Local Development (Common Case)

```bash
# From repo root
cd charts
./build-and-push-local.sh v2.1.x-description

# Deploy to cluster
cd ../.kind
terraform apply -replace='kubectl_manifest.observability_applications["observability/tinyolly.yaml"]' -auto-approve

# Verify deployment
kubectl get pods -n tinyolly
kubectl logs -n tinyolly deployment/tinyolly-ui -f

# Clear cache if needed
kubectl exec -n tinyolly tinyolly-redis-0 -- redis-cli FLUSHDB
```

### Production Release

```bash
# Build and push images
cd scripts/build
./02-build-all.sh v2.1.8
./03-push-all.sh v2.1.8

# Package and publish charts
cd ../../helm
./package.sh
./push-oci.sh

# Tag release
git tag -a v2.1.8 -m "Release v2.1.8"
git push origin v2.1.8
```

### Quick Image-Only Rebuild (Local)

```bash
# When you ONLY changed tinyolly source code
cd /repo/root/docker
podman build -f dockerfiles/Dockerfile.tinyolly \
  -t registry.tinyolly.test:49443/tinyolly/tinyolly:v2.1.x-hotfix .
podman push --tls-verify=false \
  registry.tinyolly.test:49443/tinyolly/tinyolly:v2.1.x-hotfix

# Update just the image tag in ArgoCD
kubectl -n argocd patch application tinyolly --type merge \
  -p '{"spec":{"source":{"helm":{"valuesObject":{"ui":{"image":{"tag":"v2.1.x-hotfix"}}}}}}}'
```

---

## Summary: The Build System in One Diagram

```
SOURCE CODE                    BUILD ARTIFACTS                 REGISTRIES
─────────────                  ─────────────────              ──────────────

docker/apps/
tinyolly/          ────────▶   tinyolly/tinyolly    ────────▶ ghcr.io/...
  (Python)                     (OCI image)                    (production)

docker/apps/                                                  registry.
tinyolly-opamp-    ────────▶   tinyolly/opamp-      ────────▶ tinyolly.test
server/ (Go)                   server (OCI image)             (local dev)

apps/demo/       ────────▶   tinyolly/demo        ────────▶
  (Python)                     (OCI image)
                                      │
                                      │ (referenced by)
                                      ▼
charts/tinyolly/     ────────▶   tinyolly             ────────▶ OCI registry
  (K8s manifests)              (Helm chart .tgz)              /charts

charts/tinyolly-     ────────▶   tinyolly-demos       ────────▶ OCI registry
demos/                         (Helm chart .tgz)              /charts


TOOLS USED:
- podman/docker buildx  →  Build OCI images
- helm package          →  Package charts
- helm push            →  Publish to OCI registry
- ArgoCD + Terraform   →  Deploy to Kubernetes
```

**Key Insight**: We ship **5 artifacts** total:

- 3 container images (tinyolly, opamp-server, demo)
- 2 Helm charts (tinyolly, tinyolly-demos)

---

## Document Maintenance

This document should be updated when:

- New container images are added
- New Helm charts are created
- Build scripts are added/removed/renamed
- Deployment workflow changes
- Registry endpoints change
- New dependencies are introduced

**Owner**: Infrastructure Team  
**Review Frequency**: On major releases or build system changes
