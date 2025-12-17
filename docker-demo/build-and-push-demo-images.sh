#!/bin/bash
set -e

# Build and push TinyOlly demo app images to Docker Hub
# Usage: ./build-and-push-demo-images.sh [version]
# Example: ./build-and-push-demo-images.sh v2.0.0

VERSION=${1:-"latest"}
DOCKER_HUB_ORG=${DOCKER_HUB_ORG:-"tinyolly"}
PLATFORMS="linux/amd64,linux/arm64"

echo "=========================================="
echo "TinyOlly Demo Apps - Build & Push"
echo "=========================================="
echo "Organization: $DOCKER_HUB_ORG"
echo "Version: $VERSION"
echo "Platforms: $PLATFORMS"
echo ""
echo "NOTE: These are demo/example applications."
echo "      Most users build these locally."
echo "      Only push if you're a maintainer."
echo ""

# Ensure buildx builder exists
echo "Setting up Docker Buildx..."
docker buildx create --name tinyolly-builder --use 2>/dev/null || docker buildx use tinyolly-builder
docker buildx inspect --bootstrap
echo ""

# Build demo-frontend
echo "----------------------------------------"
echo "Building demo-frontend..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  -f Dockerfile \
  -t $DOCKER_HUB_ORG/demo-frontend:latest \
  -t $DOCKER_HUB_ORG/demo-frontend:$VERSION \
  --push .
echo "✓ Pushed $DOCKER_HUB_ORG/demo-frontend:$VERSION"
echo ""

# Build demo-backend
echo "----------------------------------------"
echo "Building demo-backend..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  -f Dockerfile.backend \
  -t $DOCKER_HUB_ORG/demo-backend:latest \
  -t $DOCKER_HUB_ORG/demo-backend:$VERSION \
  --push .
echo "✓ Pushed $DOCKER_HUB_ORG/demo-backend:$VERSION"
echo ""

echo "=========================================="
echo "✓ Demo images built and pushed!"
echo "=========================================="
echo ""
echo "Published images:"
echo "  - $DOCKER_HUB_ORG/demo-frontend:$VERSION"
echo "  - $DOCKER_HUB_ORG/demo-backend:$VERSION"
echo ""
echo "To use pre-built images:"
echo "  Edit docker-compose-demo.yml and replace 'build:' with 'image: $DOCKER_HUB_ORG/demo-frontend:latest'"
echo ""
