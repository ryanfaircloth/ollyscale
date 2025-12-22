#!/bin/bash

# Build eBPF demo images for Kubernetes (Minikube)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$SCRIPT_DIR/../docker-demo-ebpf"

echo "========================================================"
echo "  Building eBPF Demo Images for Kubernetes"
echo "========================================================"
echo ""

# Check if using Minikube
if [ "$(kubectl config current-context)" = "minikube" ]; then
    echo "Detected Minikube - using minikube docker-env"
    eval $(minikube docker-env)
fi

# Build frontend image
echo "Building ebpf-frontend image..."
docker build -t ebpf-frontend:latest -f "$DEMO_DIR/Dockerfile" "$DEMO_DIR"

if [ $? -ne 0 ]; then
    echo "✗ Failed to build ebpf-frontend"
    exit 1
fi
echo "✓ ebpf-frontend built"

# Build backend image
echo "Building ebpf-backend image..."
docker build -t ebpf-backend:latest -f "$DEMO_DIR/Dockerfile.backend" "$DEMO_DIR"

if [ $? -ne 0 ]; then
    echo "✗ Failed to build ebpf-backend"
    exit 1
fi
echo "✓ ebpf-backend built"

echo ""
echo "========================================================"
echo "  Images Built Successfully"
echo "========================================================"
echo ""
echo "Images:"
echo "  - ebpf-frontend:latest"
echo "  - ebpf-backend:latest"
echo ""
