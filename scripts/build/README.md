# ollyScale Build Scripts

Centralized build scripts for all ollyScale Docker images.

## Directory Structure

```
build/
├── README.md
└── dockerhub/                     # Build & push to GitHub Container Registry (GHCR)
    ├── 01-login.sh                # Step 1: Login (not needed for GHCR with GitHub Actions)
    ├── 02-build-all.sh            # Step 2: Build all images
    ├── 02-build-core.sh           # Step 2: Build core images
    ├── 02-build-ui.sh             # Step 2: Build UI only (quick iteration)
    ├── 02-build-demo.sh           # Step 2: Build demo images
    ├── 02-build-ebpf-demo.sh      # Step 2: Build eBPF demo images
    ├── 02-build-ai-demo.sh        # Step 2: Build AI demo image
    ├── 03-push-all.sh             # Step 3: Push all images
    ├── 03-push-core.sh            # Step 3: Push core images
    ├── 03-push-ui.sh              # Step 3: Push UI only
    ├── 03-push-demo.sh            # Step 3: Push demo images
    ├── 03-push-ebpf-demo.sh       # Step 3: Push eBPF demo images
    └── 03-push-ai-demo.sh         # Step 3: Push AI demo image
```

**Note**: For local Kubernetes development with KIND, use `charts/build-and-push-local.sh` instead. See [charts/README.md](../charts/README.md) for details.

## Quick Start - GitHub Container Registry (GHCR)

```bash
cd scripts/build

# Step 1: Login to GHCR (for manual builds)
# For CI/CD, authentication is automatic via GITHUB_TOKEN
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin

# Step 2: Build images locally
export CONTAINER_REGISTRY=ghcr.io/ryanfaircloth
./02-build-all.sh v2.1.0       # All images
# or
./02-build-core.sh v2.1.0      # Core only
# or
./02-build-ui.sh v2.1.0        # UI only (quick iteration)

# Step 3: Push to GHCR
export CONTAINER_REGISTRY=ghcr.io/ryanfaircloth
./03-push-all.sh v2.1.0        # All images
# or
./03-push-core.sh v2.1.0       # Core only
# or
./03-push-ui.sh v2.1.0         # UI only
```

## Quick Start - Local Kubernetes (KIND)

For local Kubernetes development, use the Helm-based workflow:

```bash
# Bootstrap KIND cluster with Terraform + ArgoCD
make up

# Build and push images + Helm chart to local registry
cd charts
./build-and-push-local.sh v2.1.x-feature

# Deploy to ArgoCD
cd ../.kind
terraform apply -replace='kubectl_manifest.observability_applications["observability/ollyscale.yaml"]' -auto-approve
```

See [charts/README.md](../charts/README.md) for complete documentation.

## Scripts Reference

### Step 1: Login

| Script | Description |
|--------|-------------|
| `01-login.sh` | Login to Docker Hub (legacy - use docker login for GHCR) |

### Step 2: Build

| Script | Description |
|--------|-------------|
| `02-build-all.sh` | Build all images locally |
| `02-build-core.sh` | Build core ollyScale images |
| `02-build-ui.sh` | Build UI image only (quick iteration) |
| `02-build-demo.sh` | Build demo app images |
| `02-build-ebpf-demo.sh` | Build eBPF demo images |
| `02-build-ai-demo.sh` | Build AI agent demo image |

### Step 3: Push

| Script | Description |
|--------|-------------|
| `03-push-all.sh` | Push all images to container registry |
| `03-push-core.sh` | Push core images |
| `03-push-ui.sh` | Push UI image only |
| `03-push-demo.sh` | Push demo images |
| `03-push-ebpf-demo.sh` | Push eBPF demo images |
| `03-push-ai-demo.sh` | Push AI demo image |

## Images Reference

### Core Images

| Image | Description |
|-------|-------------|
| `ghcr.io/ryanfaircloth/python-base` | Shared Python base image |
| `ghcr.io/ryanfaircloth/ui` | Web UI |
| `ghcr.io/ryanfaircloth/otlp-receiver` | OTLP receiver service |
| `ghcr.io/ryanfaircloth/opamp-server` | OpAMP configuration server |

### Demo Images

| Image | Description |
|-------|-------------|
| `ghcr.io/ryanfaircloth/demo-frontend` | Demo frontend app |
| `ghcr.io/ryanfaircloth/demo-backend` | Demo backend app |

### eBPF Demo Images

| Image | Description |
|-------|-------------|
| `ghcr.io/ryanfaircloth/ebpf-frontend` | eBPF demo frontend |
| `ghcr.io/ryanfaircloth/ebpf-backend` | eBPF demo backend |

### AI Demo Image

| Image | Description |
|-------|-------------|
| `ghcr.io/ryanfaircloth/ai-agent-demo` | AI agent demo app |

## Build Behavior

- **Build scripts**: Use `--no-cache` for fresh builds, `--load` to keep locally
- **Push scripts**: Push both `:version` and `:latest` tags
- **Multi-arch**: All images built for `linux/amd64` and `linux/arm64`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTAINER_REGISTRY` | `ollyscale` | Container registry path (use `ghcr.io/ryanfaircloth` for GHCR) |

## CI/CD Integration

### GitHub Actions

```yaml
name: Build and Push Images

on:
  release:
    types: [published]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build images
        run: ./scripts/build/02-build-all.sh ${{ github.ref_name }}
        env:
          CONTAINER_REGISTRY: ghcr.io/ryanfaircloth

      - name: Push images
        run: ./scripts/build/03-push-all.sh ${{ github.ref_name }}
        env:
          CONTAINER_REGISTRY: ghcr.io/ryanfaircloth
```

### Required Secrets

| Secret | Description |
|--------|-------------|
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions (no setup needed) |

### About GHCR Authentication

GitHub Container Registry authentication is automatic in GitHub Actions using the built-in `GITHUB_TOKEN`. No additional secrets are required.

For local manual pushes, create a Personal Access Token (PAT):

1. Go to <https://github.com/settings/tokens>
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes: `write:packages`, `read:packages`, `delete:packages`
4. Use the token for login:

   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
   ```

### Creating a Docker Hub Access Token (Legacy)

1. Go to <https://hub.docker.com/settings/security>
2. Click "New Access Token"
3. Name it `ollyscale-ci` with Read & Write permissions
4. Add as repository secret

## Manual Release Checklist

```bash
cd scripts/build

# Step 1: Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin

# Step 2: Set registry environment variable
export CONTAINER_REGISTRY=ghcr.io/ryanfaircloth

# Step 3: Build all images
./02-build-all.sh v2.1.0

# Step 4: Push to GHCR
./03-push-all.sh v2.1.0

# Step 5: Verify
docker pull ghcr.io/ryanfaircloth/ui:v2.1.0

# Step 5: Test Docker deployment
cd ../../docker
./01-start-core.sh

# Step 6: Test Kubernetes deployment
cd ../k8s
./02-deploy-ollyscale.sh
```
