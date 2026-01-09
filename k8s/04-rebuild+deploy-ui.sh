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

set +e

# This script rebuilds the UI image and restarts the K8s pod to pick up changes.

# Point to Minikube's Docker daemon
eval $(minikube docker-env)

echo "Rebuilding TinyOlly UI (Minikube)..."
echo "=================================================="

# Build image locally for minikube (only for UI)
# Using --no-cache to ensure latest changes are picked up
echo "Building tinyolly-ui:latest..."
docker build --no-cache -t tinyolly-ui:latest \
  -f ../docker/dockerfiles/Dockerfile.tinyolly-ui \
  --build-arg APP_DIR=tinyolly-ui \
  ../docker/

if [ $? -ne 0 ]; then
    echo "✗ Failed to build UI image"
    exit 1
fi

echo ""
echo "Restarting UI Pod..."
# Deleting the pod forces the Deployment to recreate it, picking up the new image (imagePullPolicy: Never uses local image)
kubectl delete pod -l app=tinyolly-ui

echo ""
echo "Waiting for new pod to be ready..."
kubectl wait --for=condition=ready pod -l app=tinyolly-ui --timeout=60s

echo ""
echo "✓ UI Rebuilt and Restarted!"
echo "URL: http://localhost:5002 (via minikube tunnel)"
