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


# Deploy eBPF Zero-Code Tracing Demo to Kubernetes

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TinyOlly eBPF Demo Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗ kubectl is not installed${NC}"
    exit 1
fi

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}✗ Not connected to a Kubernetes cluster${NC}"
    exit 1
fi

CONTEXT=$(kubectl config current-context)
echo -e "${CYAN}Cluster context: ${CONTEXT}${NC}"
echo ""

# Check if TinyOlly core is deployed
echo -e "${CYAN}Checking TinyOlly core services...${NC}"
if ! kubectl get service otel-collector &> /dev/null; then
    echo -e "${RED}✗ OTel Collector service not found${NC}"
    echo -e "${YELLOW}Please deploy TinyOlly core first:${NC}"
    echo -e "  cd ../k8s"
    echo -e "  ./02-deploy-tinyolly.sh"
    exit 1
fi
echo -e "${GREEN}✓ TinyOlly core services found${NC}"
echo ""

# Note: Images are pulled from GHCR (ghcr.io/ryanfaircloth/ebpf-frontend, ghcr.io/ryanfaircloth/ebpf-backend)
# For local development, use ./build/local/build-ebpf-demo-minikube.sh to build locally

# Deploy eBPF agent first
echo -e "${CYAN}Deploying eBPF agent (DaemonSet)...${NC}"
kubectl apply -f "$SCRIPT_DIR/ebpf-agent.yaml"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to deploy eBPF agent${NC}"
    exit 1
fi
echo -e "${GREEN}✓ eBPF agent deployed${NC}"
echo ""

# Deploy demo apps
echo -e "${CYAN}Deploying eBPF demo applications...${NC}"
kubectl apply -f "$SCRIPT_DIR/ebpf-backend.yaml"
kubectl apply -f "$SCRIPT_DIR/ebpf-frontend.yaml"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to apply manifests${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Manifests applied${NC}"
echo ""

# Wait for deployments
echo -e "${CYAN}Waiting for deployments to be ready...${NC}"
echo -e "${YELLOW}This may take a minute...${NC}"
echo ""

kubectl wait --for=condition=available --timeout=120s deployment/ebpf-backend 2>&1 || echo -e "${YELLOW}Backend not ready yet${NC}"
kubectl wait --for=condition=available --timeout=120s deployment/ebpf-frontend 2>&1 || echo -e "${YELLOW}Frontend not ready yet${NC}"

echo ""

# Check status
echo -e "${CYAN}Deployment status:${NC}"
kubectl get pods -l 'app in (ebpf-frontend,ebpf-backend,otel-ebpf-agent)'
echo ""
kubectl get services -l 'app in (ebpf-frontend,ebpf-backend)'
echo ""
kubectl get daemonset otel-ebpf-agent

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}eBPF Demo Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${CYAN}Access the demo:${NC}"
echo -e "1. Make sure ${YELLOW}minikube tunnel${NC} is running"
echo -e "2. TinyOlly UI: ${GREEN}http://localhost:5002${NC}"
echo -e "3. eBPF Demo Frontend: ${GREEN}http://localhost:5001${NC}"
echo ""
echo -e "${CYAN}What's different:${NC}"
echo -e "- Traces come from eBPF agent (kernel level), not SDK"
echo -e "- Span names will be generic (e.g., 'in queue', 'CONNECT')"
echo -e "- Logs will have empty trace_id/span_id (no SDK injection)"
echo -e "- Metrics work normally via OTel SDK"
echo ""
echo -e "${CYAN}To stop:${NC}"
echo -e "  ${YELLOW}./03-cleanup.sh${NC}"
echo ""
