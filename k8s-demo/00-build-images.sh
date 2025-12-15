#!/bin/bash

# Build demo app images in Minikube's Docker environment
# Uses the docker-demo source (shared between docker and k8s deployments)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DEMO_DIR="$SCRIPT_DIR/../docker-demo"

echo "Building demo app images in Minikube..."
echo "(Using docker-demo source for feature parity)"
echo ""

# Point to Minikube's Docker daemon
eval $(minikube docker-env)

# Build frontend image from docker-demo
echo "Building demo-frontend..."
docker build -t demo-frontend:latest -f "$DOCKER_DEMO_DIR/Dockerfile" "$DOCKER_DEMO_DIR/"

echo ""
echo "Building demo-backend..."
docker build -t demo-backend:latest -f "$DOCKER_DEMO_DIR/Dockerfile.backend" "$DOCKER_DEMO_DIR/"

echo ""
echo "✓ Demo images built successfully in Minikube environment."
echo ""
echo "Images created:"
echo "  - demo-frontend:latest (from docker-demo)"
echo "  - demo-backend:latest (from docker-demo)"

