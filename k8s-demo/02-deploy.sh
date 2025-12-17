#!/bin/bash

# Deploy TinyOlly Demo Apps to Kubernetes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TinyOlly Demo App Deployment${NC}"
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
    echo -e "  kubectl apply -f ."
    exit 1
fi
echo -e "${GREEN}✓ TinyOlly core services found${NC}"
echo ""

# Check if using Minikube
USE_MINIKUBE=false
if [ "$CONTEXT" = "minikube" ]; then
    USE_MINIKUBE=true
fi

# Build images if using Minikube
if [ "$USE_MINIKUBE" = true ]; then
    echo -e "${CYAN}Checking demo images...${NC}"
    
    # Check if images exist
    IMAGES_EXIST=false
    if minikube ssh "docker images" 2>/dev/null | grep -q "demo-frontend" && \
       minikube ssh "docker images" 2>/dev/null | grep -q "demo-backend"; then
        IMAGES_EXIST=true
    fi
    
    if [ "$IMAGES_EXIST" = true ]; then
        echo -e "${YELLOW}Demo images already exist. Rebuild? [y/N]:${NC} "
        read -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            bash "$SCRIPT_DIR/01-build-images.sh"
        else
            echo -e "${GREEN}✓ Using existing images${NC}"
        fi
    else
        echo -e "${YELLOW}Images not found. Building...${NC}"
        bash "$SCRIPT_DIR/01-build-images.sh"

        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ Failed to build images${NC}"
            exit 1
        fi
    fi
    echo ""
fi

# Deploy demo apps
echo -e "${CYAN}Deploying demo applications...${NC}"

kubectl apply -f "$SCRIPT_DIR/demo-backend.yaml"
kubectl apply -f "$SCRIPT_DIR/demo-frontend.yaml"

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

kubectl wait --for=condition=available --timeout=120s deployment/demo-backend 2>&1 || echo -e "${YELLOW}Backend not ready yet${NC}"
kubectl wait --for=condition=available --timeout=120s deployment/demo-frontend 2>&1 || echo -e "${YELLOW}Frontend not ready yet${NC}"

echo ""

# Check status
echo -e "${CYAN}Deployment status:${NC}"
kubectl get pods -l 'app in (demo-frontend,demo-backend)'
echo ""
kubectl get services -l 'app in (demo-frontend,demo-backend)'

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Demo Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$USE_MINIKUBE" = true ]; then
    echo -e "${CYAN}Access the demo:${NC}"
    echo -e "1. Make sure ${YELLOW}minikube tunnel${NC} is running"
    echo -e "2. TinyOlly UI: ${GREEN}http://localhost:5002${NC}"
    echo -e "3. Demo Frontend: ${GREEN}http://localhost:5001${NC}"
    echo ""
    echo -e "${CYAN}Auto-Traffic:${NC}"
    echo -e "The demo apps ${GREEN}automatically generate traffic${NC} every 3-8 seconds."
    echo -e "Watch traces, logs, and metrics appear in the TinyOlly UI!"
    echo ""
    echo -e "${CYAN}Optional - Generate additional traffic:${NC}"
    echo -e "  ${YELLOW}./generate-traffic.sh${NC}"
fi

