#!/usr/bin/env bash
# Build and push containers + Helm chart for local development
# This script:
#   1. Builds container images (python-base, UI, OTLP receiver, OpAMP server)
#   2. Pushes them to local registry
#   3. Packages and pushes Helm chart to OCI registry
# Usage: ./build-and-push-local.sh [version-tag]
# Example: ./build-and-push-local.sh v2.1.8-test

set -euo pipefail

VERSION=${1:-"local-$(date +%s)"}
EXTERNAL_REGISTRY="registry.tinyolly.test:49443"  # For desktop build/push
INTERNAL_REGISTRY="docker-registry.registry.svc.cluster.local:5000"  # For cluster pulls
CHART_REGISTRY="${EXTERNAL_REGISTRY}/tinyolly/charts"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==============================================="
echo "Building TinyOlly: Containers + Helm Chart"
echo "==============================================="
echo "Version tag: $VERSION"
echo "External registry (desktop): $EXTERNAL_REGISTRY"
echo "Internal registry (cluster): $INTERNAL_REGISTRY"
echo "Chart registry: oci://$CHART_REGISTRY"
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

echo "Step 1/3: Building tinyolly (unified UI + OTLP receiver)"
echo "-----------------------------------------------------------"
$CONTAINER_CMD build \
  -f apps/tinyolly/Dockerfile \
  -t tinyolly/tinyolly:latest \
  -t tinyolly/tinyolly:$VERSION \
  -t $EXTERNAL_REGISTRY/tinyolly/tinyolly:latest \
  -t $EXTERNAL_REGISTRY/tinyolly/tinyolly:$VERSION \
  apps/tinyolly/
echo "✓ TinyOlly image built"
echo ""

echo "Step 2/3: Building OpAMP Server"
echo "-----------------------------------------------------------"
$CONTAINER_CMD build \
  -f apps/opamp-server/Dockerfile \
  -t tinyolly/opamp-server:latest \
  -t tinyolly/opamp-server:$VERSION \
  -t $EXTERNAL_REGISTRY/tinyolly/opamp-server:latest \
  -t $EXTERNAL_REGISTRY/tinyolly/opamp-server:$VERSION \
  apps/opamp-server/
echo "✓ OpAMP Server image built"
echo ""

echo "Step 3/3: Building Unified Demo Image"
echo "-----------------------------------------------------------"
$CONTAINER_CMD build \
  -f apps/demo/Dockerfile \
  -t tinyolly/demo:latest \
  -t tinyolly/demo:$VERSION \
  -t $EXTERNAL_REGISTRY/tinyolly/demo:latest \
  -t $EXTERNAL_REGISTRY/tinyolly/demo:$VERSION \
  apps/demo/
echo "✓ Unified Demo image built"
echo ""

echo "📤 Pushing Container Images to Registry"
echo "=========================================="
echo ""

echo "Pushing TinyOlly (unified)..."
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/tinyolly/tinyolly:latest
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/tinyolly/tinyolly:$VERSION
echo "✓ TinyOlly pushed"
echo ""

echo "Pushing OpAMP Server..."
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/tinyolly/opamp-server:latest
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/tinyolly/opamp-server:$VERSION
echo "✓ OpAMP Server pushed"
echo ""

echo "Pushing Unified Demo..."
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/tinyolly/demo:latest
$CONTAINER_CMD push $PUSH_FLAGS $EXTERNAL_REGISTRY/tinyolly/demo:$VERSION
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
CHART_DIR="$SCRIPT_DIR/tinyolly"
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

ui:
  image:
    repository: $INTERNAL_REGISTRY/tinyolly/tinyolly
    tag: $VERSION
  env:
    - name: MODE
      value: "ui"

opampServer:
  image:
    repository: $INTERNAL_REGISTRY/tinyolly/opamp-server
    tag: $VERSION

otlpReceiver:
  image:
    repository: $INTERNAL_REGISTRY/tinyolly/tinyolly
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
CHART_PACKAGE="$SCRIPT_DIR/tinyolly-${NEW_CHART_VERSION}.tgz"
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
echo "  • Built/pushed to: $EXTERNAL_REGISTRY/tinyolly/*:$VERSION"
echo "  • Cluster pulls from: $INTERNAL_REGISTRY/tinyolly/*:$VERSION"
echo ""
echo "Helm Chart:"
echo "  • Package: $(basename "$CHART_PACKAGE")"
echo "  • Version: $NEW_CHART_VERSION"
echo ""
echo "📋 Next Steps:"
echo ""
echo "  Install with Helm (using local values):"
echo "    cd helm"
echo "    helm install tinyolly ./tinyolly \\"
echo "      --namespace tinyolly \\"
echo "      --create-namespace \\"
echo "      --values values-local-dev.yaml"
echo ""
echo "  Or upgrade existing installation:"
echo "    helm upgrade tinyolly ./tinyolly \\"
echo "      --namespace tinyolly \\"
echo "      --values values-local-dev.yaml"
echo ""
echo "  Deploy to ArgoCD (recommended):"
echo "    ./deploy-to-argocd.sh"
echo ""
echo "  Deploy specific image version with kubectl:"
echo "    kubectl set image deployment/tinyolly-ui \\"
echo "      tinyolly-ui=$EXTERNAL_REGISTRY/tinyolly/ui:$VERSION -n tinyolly"
echo ""

# Auto-deploy to ArgoCD with new chart version and image version
echo "🚀 Deploying to ArgoCD with chart version $NEW_CHART_VERSION and image version $VERSION..."
echo ""
"$SCRIPT_DIR/deploy-to-argocd.sh" "$NEW_CHART_VERSION" "$VERSION"
