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


echo "========================================"
echo "TinyOlly Core Kubernetes Cleanup"
echo "========================================"

echo ""
echo "Checking for TinyOlly resources..."
echo "The following resources will be deleted:"
echo ""
kubectl get deployments,services,configmaps 2>/dev/null | grep -E "(tinyolly-redis|tinyolly|otel-collector)" || echo "  (checking resources...)"
echo ""

read -p "Do you want to proceed with cleanup? [y/N]:" confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Deleting TinyOlly resources..."

echo ""
echo "→ Deleting resources..."
kubectl delete -f tinyolly-ui.yaml --ignore-not-found
kubectl delete -f tinyolly-opamp-server.yaml --ignore-not-found
kubectl delete -f tinyolly-otlp-receiver.yaml --ignore-not-found
kubectl delete -f redis.yaml --ignore-not-found

echo ""
echo "→ Ensuring all configmaps are deleted..."
kubectl delete configmap otel-collector-config --ignore-not-found=true 2>/dev/null || true
kubectl delete configmap otelcol-templates --ignore-not-found=true 2>/dev/null || true

echo ""
echo "Waiting for pods to terminate..."
kubectl wait --for=delete pod -l app=tinyolly-redis --timeout=60s 2>/dev/null || true
kubectl wait --for=delete pod -l app=tinyolly-otlp-receiver --timeout=60s 2>/dev/null || true
kubectl wait --for=delete pod -l app=tinyolly-opamp-server --timeout=60s 2>/dev/null || true
kubectl wait --for=delete pod -l app=tinyolly-ui --timeout=60s 2>/dev/null || true

echo ""
echo "Verifying cleanup..."
if [ -z "$(kubectl get pods -l app=tinyolly-ui -o name 2>/dev/null)" ]; then
    echo "✓ All TinyOlly resources have been deleted"
else
    echo "⚠ Some resources might still be terminating"
fi

echo ""
echo "========================================"
echo "Cleanup complete!"
echo "========================================"
