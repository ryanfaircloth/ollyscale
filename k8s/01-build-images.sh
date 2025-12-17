#!/bin/bash

# Build images locally in Minikube for development
# NOTE: By default, TinyOlly uses pre-built images from Docker Hub.
#       Only use this script for local development builds.

echo "=========================================="
echo "TinyOlly Kubernetes - LOCAL BUILD MODE"
echo "=========================================="
echo ""
echo "This script builds images locally in Minikube instead of using Docker Hub."
echo "For production deployments, skip this step and use images from Docker Hub."
echo ""
echo "To use Docker Hub images instead:"
echo "  1. Skip running this script"
echo "  2. Update k8s manifests to use imagePullPolicy: Always"
echo "  3. Run: ./02-deploy-tinyolly.sh"
echo ""

# Point to Minikube's Docker daemon
eval $(minikube docker-env)

# Build shared Python base image first
echo "Building shared Python base image..."
docker build --no-cache -t tinyolly/python-base:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-python-base \
  ../docker/

# Build images
# Build context must be ../docker/ so Dockerfile can access apps/, dockerfiles/, etc.
echo "Building tinyolly-ui..."
docker build --no-cache -t tinyolly/ui:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-ui \
  --build-arg APP_DIR=tinyolly-ui \
  ../docker/

echo "Building tinyolly-otlp-receiver..."
docker build --no-cache -t tinyolly/otlp-receiver:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-otlp-receiver \
  --build-arg APP_DIR=tinyolly-otlp-receiver \
  ../docker/

echo "Building tinyolly-opamp-server..."
docker build --no-cache -t tinyolly/opamp-server:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-opamp-server \
  ../docker/

echo "Building otel-supervisor..."
docker build --no-cache -t tinyolly/otel-supervisor:latest \
  -f ../docker/dockerfiles/Dockerfile.otel-supervisor \
  ../docker/

echo ""
echo "=========================================="
echo "✓ Images built successfully in Minikube environment"
echo "=========================================="
echo ""
echo "Next step: Deploy to Kubernetes"
echo "  cd .. && k8s/02-deploy-tinyolly.sh"
echo ""
