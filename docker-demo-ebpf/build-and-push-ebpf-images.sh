#!/bin/bash
set -e

# Build and push TinyOlly eBPF demo app images to Docker Hub
# Usage: ./build-and-push-ebpf-images.sh [version]
# Example: ./build-and-push-ebpf-images.sh v2.0.0

VERSION=${1:-"latest"}
DOCKER_HUB_ORG=${DOCKER_HUB_ORG:-"tinyolly"}
PLATFORMS="linux/amd64,linux/arm64"

echo "=========================================="
echo "TinyOlly eBPF Demo Apps - Build & Push"
echo "=========================================="
echo "Organization: $DOCKER_HUB_ORG"
echo "Version: $VERSION"
echo "Platforms: $PLATFORMS"
echo ""
echo "NOTE: These are eBPF demo applications."
echo "      Most users build these locally."
echo "      Only push if you're a maintainer."
echo ""

# Ensure buildx builder exists
echo "Setting up Docker Buildx..."
docker buildx create --name tinyolly-builder --use 2>/dev/null || docker buildx use tinyolly-builder
docker buildx inspect --bootstrap
echo ""

# Build ebpf-frontend
echo "----------------------------------------"
echo "Building ebpf-frontend..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  -f Dockerfile \
  -t $DOCKER_HUB_ORG/ebpf-frontend:latest \
  -t $DOCKER_HUB_ORG/ebpf-frontend:$VERSION \
  --push .
echo "✓ Pushed $DOCKER_HUB_ORG/ebpf-frontend:$VERSION"
echo ""

# Build ebpf-backend
echo "----------------------------------------"
echo "Building ebpf-backend..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  -f Dockerfile.backend \
  -t $DOCKER_HUB_ORG/ebpf-backend:latest \
  -t $DOCKER_HUB_ORG/ebpf-backend:$VERSION \
  --push .
echo "✓ Pushed $DOCKER_HUB_ORG/ebpf-backend:$VERSION"
echo ""

echo "=========================================="
echo "✓ eBPF demo images built and pushed!"
echo "=========================================="
echo ""
echo "Published images:"
echo "  - $DOCKER_HUB_ORG/ebpf-frontend:$VERSION"
echo "  - $DOCKER_HUB_ORG/ebpf-backend:$VERSION"
echo ""
