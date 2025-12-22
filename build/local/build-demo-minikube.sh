#!/bin/bash
set -e

# Build TinyOlly demo images locally in Minikube's Docker environment
# Usage: ./build-demo-minikube.sh
#
# NOTE: Uses --no-cache for fresh builds

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$SCRIPT_DIR/../../docker-demo"

echo "=========================================="
echo "TinyOlly Demo - Local Minikube Build"
echo "=========================================="
echo ""

# Point to Minikube's Docker daemon
echo "Connecting to Minikube Docker environment..."
eval $(minikube docker-env)

echo ""
echo "Building demo-frontend..."
docker build --no-cache -t demo-frontend:latest -f "$DEMO_DIR/Dockerfile" "$DEMO_DIR/"

echo ""
echo "Building demo-backend..."
docker build --no-cache -t demo-backend:latest -f "$DEMO_DIR/Dockerfile.backend" "$DEMO_DIR/"

echo ""
echo "=========================================="
echo "✓ Demo images built in Minikube"
echo "=========================================="
echo ""
echo "Images:"
echo "  - demo-frontend:latest"
echo "  - demo-backend:latest"
echo ""
echo "Next: Deploy to Kubernetes"
echo "  cd k8s-demo && ./02-deploy.sh"
echo ""
