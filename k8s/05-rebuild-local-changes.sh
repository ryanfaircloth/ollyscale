#!/bin/bash
set -e

# Rebuild base image + UI image for local testing of tinyolly-common changes
# Builds and pushes to local registry - does NOT deploy (use your own deployment tool)
# Usage: ./05-rebuild-local-changes.sh [version-tag]
# Example: ./05-rebuild-local-changes.sh v2.1.8-test

VERSION=${1:-"local-$(date +%s)"}
REGISTRY="localhost:5050"

echo "==============================================="
echo "Rebuilding TinyOlly for Local Testing"
echo "==============================================="
echo "Version tag: $VERSION"
echo "Registry: $REGISTRY"
echo ""

# Detect container runtime (podman or docker)
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    echo "Using: podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    echo "Using: docker"
else
    echo "Error: Neither podman nor docker found"
    exit 1
fi
echo ""

# Navigate to docker directory (build context)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../docker"

echo "Step 1/5: Building python-base (includes tinyolly-common)"
echo "---------------------------------------------------"
$CONTAINER_CMD build \
  -f dockerfiles/Dockerfile.tinyolly-python-base \
  -t tinyolly/python-base:latest \
  -t tinyolly/python-base:$VERSION \
  .
echo "✓ Base image built with local storage.py changes"
echo ""

echo "Step 2/5: Building UI (uses local python-base)"
echo "---------------------------------------------------"
$CONTAINER_CMD build \
  -f dockerfiles/Dockerfile.tinyolly-ui \
  --build-arg APP_DIR=tinyolly-ui \
  -t $REGISTRY/tinyolly/ui:$VERSION \
  -t $REGISTRY/tinyolly/ui:latest \
  .
echo "✓ UI image built using local base image"
echo ""

echo "Step 3/5: Pushing to local registry ($REGISTRY)"
echo "---------------------------------------------------"
# Quick check that registry is accessible
if ! curl -sf http://localhost:5050/v2/_catalog > /dev/null 2>&1; then
    echo "⚠ Warning: Registry at localhost:5050 may not be accessible"
    echo "Attempting to push anyway..."
    echo ""
fi

if $CONTAINER_CMD push --tls-verify=false $REGISTRY/tinyolly/ui:$VERSION; then
    echo "✓ Pushed $REGISTRY/tinyolly/ui:$VERSION"
else
    echo "✗ Failed to push image"
    echo ""
    echo "Troubleshooting:"
    echo "1. Verify registry is running and accessible:"
    echo "   curl http://localhost:5050/v2/_catalog"
    echo ""
    echo "2. Check registry logs/status"
    exit 1
fi
echo ""

echo "==============================================="
echo "✓ Build & Push Complete!"
echo "==============================================="
echo "Image: $REGISTRY/tinyolly/ui:$VERSION"
echo "Base: ghcr.io/ryanfaircloth/python-base:$VERSION"
echo ""
echo "Ready to deploy with your deployment tool"
echo ""
echo "Manual deployment commands (if needed):"
echo "  kubectl set image deployment/tinyolly-ui tinyolly-ui=$REGISTRY/tinyolly/ui:$VERSION -n tinyolly"
echo "  kubectl rollout status deployment/tinyolly-ui -n tinyolly"
echo ""
echo "Clear Redis cache after deployment:"
echo "  kubectl exec -n tinyolly deployment/tinyolly-redis -- redis-cli -p 6579 FLUSHDB"
