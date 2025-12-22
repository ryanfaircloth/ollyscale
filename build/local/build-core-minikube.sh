#!/bin/bash
set -e

# Build TinyOlly core images locally in Minikube's Docker environment
# Usage: ./build-core-minikube.sh
#
# NOTE: Uses --no-cache for fresh builds

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/../../docker"

echo "=========================================="
echo "TinyOlly Core - Local Minikube Build"
echo "=========================================="
echo ""

# Point to Minikube's Docker daemon
echo "Connecting to Minikube Docker environment..."
eval $(minikube docker-env)

# Build shared Python base image first
echo ""
echo "Building python-base..."
docker build --no-cache -t tinyolly/python-base:latest \
  -f "$DOCKER_DIR/dockerfiles/Dockerfile.tinyolly-python-base" \
  "$DOCKER_DIR/"

echo ""
echo "Building ui..."
docker build --no-cache -t tinyolly/ui:latest \
  -f "$DOCKER_DIR/dockerfiles/Dockerfile.tinyolly-ui" \
  --build-arg APP_DIR=tinyolly-ui \
  "$DOCKER_DIR/"

echo ""
echo "Building otlp-receiver..."
docker build --no-cache -t tinyolly/otlp-receiver:latest \
  -f "$DOCKER_DIR/dockerfiles/Dockerfile.tinyolly-otlp-receiver" \
  --build-arg APP_DIR=tinyolly-otlp-receiver \
  "$DOCKER_DIR/"

echo ""
echo "Building opamp-server..."
docker build --no-cache -t tinyolly/opamp-server:latest \
  -f "$DOCKER_DIR/dockerfiles/Dockerfile.tinyolly-opamp-server" \
  "$DOCKER_DIR/"

echo ""
echo "Building otel-supervisor..."
docker build --no-cache -t tinyolly/otel-supervisor:latest \
  -f "$DOCKER_DIR/dockerfiles/Dockerfile.otel-supervisor" \
  "$DOCKER_DIR/"

echo ""
echo "=========================================="
echo "✓ Core images built in Minikube"
echo "=========================================="
echo ""
echo "Images:"
echo "  - tinyolly/python-base:latest"
echo "  - tinyolly/ui:latest"
echo "  - tinyolly/otlp-receiver:latest"
echo "  - tinyolly/opamp-server:latest"
echo "  - tinyolly/otel-supervisor:latest"
echo ""
echo "Next: Deploy to Kubernetes"
echo "  cd k8s && ./02-deploy-tinyolly.sh"
echo ""
