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
