#!/bin/bash

# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
