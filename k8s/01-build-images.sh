#!/bin/bash

# Point to Minikube's Docker daemon
eval $(minikube docker-env)

# Build shared Python base image first
echo "Building shared Python base image..."
docker build --no-cache -t tinyolly-python-base:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-python-base \
  ../docker/

# Build images
# Build context must be ../docker/ so Dockerfile can access apps/, dockerfiles/, etc.
echo "Building tinyolly-ui..."
docker build --no-cache -t tinyolly-ui:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-ui \
  --build-arg APP_DIR=tinyolly-ui \
  ../docker/

echo "Building tinyolly-otlp-receiver..."
docker build --no-cache -t tinyolly-otlp-receiver:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-otlp-receiver \
  --build-arg APP_DIR=tinyolly-otlp-receiver \
  ../docker/

echo "Building tinyolly-opamp-server..."
docker build --no-cache -t tinyolly-opamp-server:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-opamp-server \
  ../docker/

echo "Building otel-supervisor..."
docker build --no-cache -t otel-supervisor:latest \
  -f ../docker/dockerfiles/Dockerfile.otel-supervisor \
  ../docker/

echo "Images built successfully in Minikube environment."
