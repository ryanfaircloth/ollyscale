#!/bin/bash
set -e

# Build and push TinyOlly AI Agent demo image to Docker Hub
# Usage: ./build-and-push-ai-demo-image.sh [version]
# Example: ./build-and-push-ai-demo-image.sh v2.0.0

VERSION=${1:-"latest"}
DOCKER_HUB_ORG=${DOCKER_HUB_ORG:-"tinyolly"}
PLATFORMS="linux/amd64,linux/arm64"

echo "=========================================="
echo "TinyOlly AI Agent Demo - Build & Push"
echo "=========================================="
echo "Organization: $DOCKER_HUB_ORG"
echo "Version: $VERSION"
echo "Platforms: $PLATFORMS"
echo ""
echo "NOTE: This is a demo/example application."
echo "      Most users build this locally."
echo "      Only push if you're a maintainer."
echo ""

# Ensure buildx builder exists
echo "Setting up Docker Buildx..."
docker buildx create --name tinyolly-builder --use 2>/dev/null || docker buildx use tinyolly-builder
docker buildx inspect --bootstrap
echo ""

# Build ai-agent
echo "----------------------------------------"
echo "Building ai-agent-demo..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  -f Dockerfile \
  -t $DOCKER_HUB_ORG/ai-agent-demo:latest \
  -t $DOCKER_HUB_ORG/ai-agent-demo:$VERSION \
  --push .
echo "✓ Pushed $DOCKER_HUB_ORG/ai-agent-demo:$VERSION"
echo ""

echo "=========================================="
echo "✓ AI Agent demo image built and pushed!"
echo "=========================================="
echo ""
echo "Published image:"
echo "  - $DOCKER_HUB_ORG/ai-agent-demo:$VERSION"
echo ""
echo "To use pre-built image:"
echo "  Edit docker-compose.yml and replace 'build: .' with 'image: $DOCKER_HUB_ORG/ai-agent-demo:latest'"
echo ""
echo "Note: Ollama image (ollama/ollama:latest) is already from Docker Hub."
echo ""
