#!/bin/bash
set -e

# Build TinyOlly eBPF demo images locally in Minikube's Docker environment
# Usage: ./build-ebpf-demo-minikube.sh
#
# NOTE: Uses --no-cache for fresh builds

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$SCRIPT_DIR/../../docker-demo-ebpf"

echo "=========================================="
echo "TinyOlly eBPF Demo - Local Minikube Build"
echo "=========================================="
echo ""

# Point to Minikube's Docker daemon
echo "Connecting to Minikube Docker environment..."
eval $(minikube docker-env)

echo ""
echo "Building ebpf-frontend..."
docker build --no-cache -t ebpf-frontend:latest -f "$DEMO_DIR/Dockerfile" "$DEMO_DIR/"

echo ""
echo "Building ebpf-backend..."
docker build --no-cache -t ebpf-backend:latest -f "$DEMO_DIR/Dockerfile.backend" "$DEMO_DIR/"

echo ""
echo "=========================================="
echo "✓ eBPF demo images built in Minikube"
echo "=========================================="
echo ""
echo "Images:"
echo "  - ebpf-frontend:latest"
echo "  - ebpf-backend:latest"
echo ""
echo "Next: Deploy to Kubernetes"
echo "  cd k8s-demo-ebpf && ./02-deploy.sh"
echo ""
