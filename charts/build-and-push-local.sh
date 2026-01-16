#!/usr/bin/env bash
# Build and push containers + Helm chart for local development
# This script:
#   1. Builds container images (python-base, UI, OTLP receiver, OpAMP server)
#   2. Pushes them to local registry
#   3. Packages and pushes Helm chart to OCI registry
# Usage: ./build-and-push-local.sh [version-tag]
# Example: ./build-and-push-local.sh v2.1.8-test

set -euo pipefail

# Project configuration (can be overridden via environment)
PROJECT_NAME="${PROJECT_NAME:-ollyScale}"
PROJECT_SLUG="${PROJECT_SLUG:-ollyscale}"
GH_ORG="${GH_ORG:-ryanfaircloth}"
GH_REPO="${GH_REPO:-ollyscale}"

# Registry configuration
REGISTRY="${REGISTRY:-ghcr.io}"
REGISTRY_ORG="${REGISTRY_ORG:-$GH_ORG}"

# Legacy support for local KIND registry
EXTERNAL_REGISTRY="${EXTERNAL_REGISTRY:-registry.ollyscale.test:49443}"  # For desktop build/push
INTERNAL_REGISTRY="${INTERNAL_REGISTRY:-docker-registry.registry.svc.cluster.local:5000}"  # For cluster pulls
CHART_REGISTRY="${CHART_REGISTRY:-${EXTERNAL_REGISTRY}/ollyscale/charts}"

# Image naming (can be functional or branded)
IMAGE_ORG="${IMAGE_ORG:-$PROJECT_SLUG}"  # e.g. ollyscale or observability-platform

VERSION=${1:-"local-$(date +%s)"}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==============================================="
echo "Building $PROJECT_NAME: Containers + Helm Chart"
echo "==============================================="
echo "Project: $PROJECT_NAME ($PROJECT_SLUG)"
echo "Version tag: $VERSION"
echo "External registry (desktop): $EXTERNAL_REGISTRY"
echo "Internal registry (cluster): $INTERNAL_REGISTRY"
echo "Chart registry: oci://$CHART_REGISTRY"
echo "Image organization: $IMAGE_ORG"
echo ""

# Detect container runtime (podman or docker)
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    PUSH_FLAGS="--tls-verify=false"
    echo "Using: podman (TLS verify disabled for local registry)"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    PUSH_FLAGS=""
    echo "Using: docker"
    echo "Note: Ensure Docker daemon has $EXTERNAL_REGISTRY in insecure-registries"
else
    echo "❌ Error: Neither podman nor docker found"
    exit 1
fi
echo ""

# ==========================================
# PART 1: Build and Push Container Images
# ==========================================

echo "📦 PART 1: Building Container Images"
echo "=========================================="
echo ""

# Navigate to repo root
cd "$SCRIPT_DIR/.."

echo "Step 1/4: Building $IMAGE_ORG (API backend + OTLP receiver)"
echo "-----------------------------------------------------------"
$CONTAINER_CMD build \
  -f apps/ollyscale/Dockerfile \
  -t $IMAGE_ORG/ollyscale:latest \
  -t $IMAGE_ORG/ollyscale:$VERSION \
  -t $EXTERNAL_REGISTRY/$IMAGE_ORG/ollyscale:latest \
  -t $EXTERNAL_REGISTRY/$IMAGE_ORG/ollyscale:$VERSION \
  apps/ollyscale/
echo "✓ $PROJECT_NAME backend image built"
echo ""

echo "Step 2/4: Building $IMAGE_ORG-ui (static frontend)"
echo "-----------------------------------------------------------"
$CONTAINER_CMD build \
  -f apps/ollyscale-ui/Dockerfile \
  -t $IMAGE_ORG/ollyscale-ui:latest \
  -t $IMAGE_ORG/ollyscale-ui:$VERSION \
  -t $EXTERNAL_REGISTRY/$IMAGE_ORG/ollyscale-ui:latest \
  -t $EXTERNAL_REGISTRY/$IMAGE_ORG/ollyscale-ui:$VERSION \
  apps/ollyscale-ui/
echo "✓ $IMAGE_ORG-ui image built"
echo ""

echo "Step 3/4: Building OpAMP Server"
echo "-----------------------------------------------------------"
$CONTAINER_CMD build \
  -f apps/opamp-server/Dockerfile \
  -t $IMAGE_ORG/opamp-server:latest \
  -t $IMAGE_ORG/opamp-server:$VERSION \
  -t $EXTERNAL_REGISTRY/$IMAGE_ORG/opamp-server:latest \
  -t $EXTERNAL_REGISTRY/$IMAGE_ORG/opamp-server:$VERSION \
  apps/opamp-server/
echo "✓ OpAMP Server image built"
echo ""

echo "Step 4/4: Building Unified Demo Image"
echo "-----------------------------------------------------------"
$CONTAINER_CMD build \
  -f apps/demo/Dockerfile \
  -t $IMAGE_ORG/demo:latest \
  -t $IMAGE_ORG/demo:$VERSION \
  -t $EXTERNAL_REGISTRY/$IMAGE_ORG/demo:latest \
  -t $EXTERNAL_REGISTRY/$IMAGE_ORG/demo:$VERSION \
  apps/demo/
echo "✓ Unified Demo image built"
echo ""

echo "📤 Pushing Container Images to Registry"
echo "=========================================="
echo ""

echo "Pushing $PROJECT_NAME backend..."
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/$IMAGE_ORG/ollyscale:latest
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/$IMAGE_ORG/ollyscale:$VERSION
echo "✓ $PROJECT_NAME backend pushed"
echo ""

echo "Pushing $IMAGE_ORG-ui..."
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/$IMAGE_ORG/ollyscale-ui:latest
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/$IMAGE_ORG/ollyscale-ui:$VERSION
echo "✓ $IMAGE_ORG-ui pushed"
echo ""

echo "Pushing OpAMP Server..."
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/$IMAGE_ORG/opamp-server:latest
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/$IMAGE_ORG/opamp-server:$VERSION
echo "✓ OpAMP Server pushed"
echo ""

echo "Pushing Unified Demo..."
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/$IMAGE_ORG/demo:latest
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/$IMAGE_ORG/demo:$VERSION
echo "✓ Unified Demo pushed"
echo ""

# ==========================================
# PART 2: Package and Push Helm Chart
# ==========================================

echo "📦 PART 2: Packaging Helm Chart"
echo "=========================================="
echo ""

cd "$SCRIPT_DIR"

# Update Chart.yaml with the new version
CHART_DIR="$SCRIPT_DIR/ollyscale"
CHART_YAML="$CHART_DIR/Chart.yaml"

# Extract current chart version
CURRENT_CHART_VERSION=$(grep "^version:" "$CHART_YAML" | awk '{print $2}')
echo "Current chart version: $CURRENT_CHART_VERSION"

# Auto-increment chart version with timestamp for local builds
BASE_VERSION=$(echo "$CURRENT_CHART_VERSION" | cut -d'-' -f1)
NEW_CHART_VERSION="${BASE_VERSION}-${VERSION}"
echo "New chart version: $NEW_CHART_VERSION"
echo ""

# Update Chart.yaml with new version
echo "📝 Updating Chart.yaml version..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/^version: .*/version: $NEW_CHART_VERSION/" "$CHART_DIR/Chart.yaml"
else
    sed -i "s/^version: .*/version: $NEW_CHART_VERSION/" "$CHART_DIR/Chart.yaml"
fi
echo "✓ Updated Chart.yaml to version $NEW_CHART_VERSION"
echo ""

# Update values.yaml to use the new image tags
VALUES_YAML="$CHART_DIR/values.yaml"
echo "Updating image tags in values.yaml to: $VERSION"

# Create a temporary values file for local development
cat > "$SCRIPT_DIR/values-local-dev.yaml" <<EOF
# Auto-generated local development values
# Generated: $(date)
# Version: $VERSION
# Uses INTERNAL registry for cluster access

frontend:
  image:
    repository: $INTERNAL_REGISTRY/$IMAGE_ORG/ollyscale
    tag: $VERSION
  env:
    - name: MODE
      value: "ui"

webui:
  image:
    repository: $INTERNAL_REGISTRY/$IMAGE_ORG/ollyscale-ui
    tag: $VERSION

opampServer:
  image:
    repository: $INTERNAL_REGISTRY/$IMAGE_ORG/opamp-server
    tag: $VERSION

otlpReceiver:
  image:
    repository: $INTERNAL_REGISTRY/$IMAGE_ORG/ollyscale
    tag: $VERSION
  env:
    - name: MODE
      value: "receiver"

otelCollector:
  enabled: true

instrumentation:
  enabled: true
EOF

echo "✓ Created values-local-dev.yaml with updated image tags"
echo ""

# Lint the chart
echo "🔍 Linting Helm chart..."
helm lint "$CHART_DIR"
echo "✓ Chart linted successfully"
echo ""

# Package the chart
echo "📦 Packaging chart..."
helm package "$CHART_DIR" -d "$SCRIPT_DIR"
CHART_PACKAGE="$SCRIPT_DIR/ollyscale-${NEW_CHART_VERSION}.tgz"
echo "✓ Chart packaged: $(basename "$CHART_PACKAGE")"
echo ""

# Push to OCI registry
echo "📤 Pushing Helm chart to OCI registry..."
echo "   Registry: oci://$CHART_REGISTRY"
echo ""

if [[ "$CONTAINER_CMD" == "podman" ]]; then
    # Helm uses the container credential helper, so we need to login
    echo "🔐 Logging into registry (required for Helm with podman)..."
    # Check if already logged in
    if ! helm registry login "$EXTERNAL_REGISTRY" --help &>/dev/null 2>&1; then
        echo "⚠️  Note: You may need to run: helm registry login $EXTERNAL_REGISTRY"
    fi
fi

# Push the chart
echo "Pushing chart with: helm push $CHART_PACKAGE oci://$CHART_REGISTRY"
if helm push "$CHART_PACKAGE" "oci://$CHART_REGISTRY" --insecure-skip-tls-verify; then
    echo "✓ Chart pushed successfully"
else
    echo "❌ Error: Chart push failed"
    echo "   Please check helm registry login and credentials"
    exit 1
fi
echo ""

# ==========================================
# Summary
# ==========================================

echo "✅ BUILD COMPLETE"
echo "=========================================="
echo ""
echo "Container Images:"
echo "  • Built/pushed to: $EXTERNAL_REGISTRY/$IMAGE_ORG/*:$VERSION"
echo "  • Cluster pulls from: $INTERNAL_REGISTRY/$IMAGE_ORG/*:$VERSION"
echo ""
echo "Helm Chart:"
echo "  • Package: $(basename "$CHART_PACKAGE")"
echo "  • Version: $NEW_CHART_VERSION"
echo ""
echo "📋 Next Steps:"
echo ""
echo "  Install with Helm (using local values):"
echo "    cd helm"
echo "    helm install ollyscale ./ollyscale \\"
echo "      --namespace ollyscale \\"
echo "      --create-namespace \\"
echo "      --values values-local-dev.yaml"
echo ""
echo "  Or upgrade existing installation:"
echo "    helm upgrade ollyscale ./ollyscale \\"
echo "      --namespace ollyscale \\"
echo "      --values values-local-dev.yaml"
echo ""
echo "  Deploy to ArgoCD (recommended):"
echo "    ./deploy-to-argocd.sh"
echo ""
echo "  Deploy specific image version with kubectl:"
echo "    kubectl set image deployment/$PROJECT_SLUG-ui \\"
echo "      $PROJECT_SLUG-ui=$EXTERNAL_REGISTRY/$IMAGE_ORG/ui:$VERSION -n ollyscale"
echo ""

# Auto-deploy to ArgoCD with new chart version and image version
echo "🚀 Deploying to ArgoCD with chart version $NEW_CHART_VERSION and image version $VERSION..."
echo ""
"$SCRIPT_DIR/deploy-to-argocd.sh" "$NEW_CHART_VERSION" "$VERSION"
