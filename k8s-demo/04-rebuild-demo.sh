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

# This script rebuilds the demo-frontend image and restarts the K8s pod.

# Point to Minikube's Docker daemon
eval $(minikube docker-env)

# Ensure we are in the script directory so relative paths work
cd "$(dirname "$0")"

echo "Rebuilding Demo Frontend (Minikube)..."
echo "=================================================="

# Build image
echo "Building demo-frontend:latest..."
docker build --no-cache -t demo-frontend:latest \
  -f ../docker-demo/Dockerfile \
  ../docker-demo/

if [ $? -ne 0 ]; then
    echo "✗ Failed to build demo-frontend image"
    exit 1
fi

echo ""
echo "Restarting Demo Frontend Pod..."
kubectl delete pod -l app=demo-frontend

echo ""
echo "Waiting for new pod to be ready..."
kubectl wait --for=condition=ready pod -l app=demo-frontend --timeout=60s

echo ""
echo "✓ Demo Frontend Rebuilt and Restarted!"
