#!/bin/bash
set -e

# Push ALL TinyOlly images to Docker Hub
# Usage: ./push-all.sh [version]
# Example: ./push-all.sh v2.1.0
#
# This pushes: core, demo, ebpf-demo, and ai-demo images
# Run ./build-all.sh first to build the images

VERSION=${1:-"latest"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "TinyOlly - Push ALL Images to Docker Hub"
echo "=========================================="
echo "Version: $VERSION"
echo ""

# Push core images
echo ""
echo ">>> Pushing Core Images..."
echo ""
"$SCRIPT_DIR/push-core.sh" "$VERSION"

# Push demo images
echo ""
echo ">>> Pushing Demo Images..."
echo ""
"$SCRIPT_DIR/push-demo.sh" "$VERSION"

# Push eBPF demo images
echo ""
echo ">>> Pushing eBPF Demo Images..."
echo ""
"$SCRIPT_DIR/push-ebpf-demo.sh" "$VERSION"

# Push AI demo image
echo ""
echo ">>> Pushing AI Demo Image..."
echo ""
"$SCRIPT_DIR/push-ai-demo.sh" "$VERSION"

echo ""
echo "=========================================="
echo "✓ ALL images pushed to Docker Hub!"
echo "=========================================="
echo ""
echo "Published images:"
echo "  - tinyolly/python-base:$VERSION"
echo "  - tinyolly/otlp-receiver:$VERSION"
echo "  - tinyolly/ui:$VERSION"
echo "  - tinyolly/opamp-server:$VERSION"
echo "  - tinyolly/otel-supervisor:$VERSION"
echo "  - tinyolly/demo-frontend:$VERSION"
echo "  - tinyolly/demo-backend:$VERSION"
echo "  - tinyolly/ebpf-frontend:$VERSION"
echo "  - tinyolly/ebpf-backend:$VERSION"
echo "  - tinyolly/ai-agent-demo:$VERSION"
echo ""
