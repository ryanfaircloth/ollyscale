#!/bin/bash

# Point to Minikube's Docker daemon
eval $(minikube docker-env)

# Build images
# Build context must be ../docker/apps/ (parent directory) so Dockerfile can access both tinyolly-common and app directories
echo "Building tinyolly-ui..."
docker build --no-cache -t tinyolly-ui:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-ui \
  --build-arg APP_DIR=tinyolly-ui \
  ../docker/apps/

echo "Building tinyolly-otlp-receiver..."
docker build --no-cache -t tinyolly-otlp-receiver:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-otlp-receiver \
  --build-arg APP_DIR=tinyolly-otlp-receiver \
  ../docker/apps/

echo "Images built successfully in Minikube environment."
