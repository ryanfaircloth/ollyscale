#!/bin/bash
set -e

# Push TinyOlly core images to Docker Hub
# Usage: ./push-core.sh [version]
# Example: ./push-core.sh v2.1.0
#
# NOTE: Run ./build-core.sh first, or use --build flag to build and push

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../../docker"

VERSION=${1:-"latest"}
DOCKER_HUB_ORG=${DOCKER_HUB_ORG:-"tinyolly"}

echo "=========================================="
echo "TinyOlly Core - Push to Docker Hub"
echo "=========================================="
echo "Organization: $DOCKER_HUB_ORG"
echo "Version: $VERSION"
echo ""

# Push all core images
IMAGES=(
  "python-base"
  "otlp-receiver"
  "ui"
  "opamp-server"
  "otel-supervisor"
)

for IMAGE in "${IMAGES[@]}"; do
  echo "Pushing $DOCKER_HUB_ORG/$IMAGE:$VERSION..."
  docker push $DOCKER_HUB_ORG/$IMAGE:$VERSION
  docker push $DOCKER_HUB_ORG/$IMAGE:latest
  echo "✓ Pushed $DOCKER_HUB_ORG/$IMAGE:$VERSION"
  echo ""
done

echo "=========================================="
echo "✓ All core images pushed to Docker Hub!"
echo "=========================================="
echo ""
echo "Published images:"
echo "  - $DOCKER_HUB_ORG/python-base:$VERSION"
echo "  - $DOCKER_HUB_ORG/otlp-receiver:$VERSION"
echo "  - $DOCKER_HUB_ORG/ui:$VERSION"
echo "  - $DOCKER_HUB_ORG/opamp-server:$VERSION"
echo "  - $DOCKER_HUB_ORG/otel-supervisor:$VERSION"
echo ""
echo "Verify: docker pull $DOCKER_HUB_ORG/ui:$VERSION"
echo ""
