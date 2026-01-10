#!/bin/bash
# Deploy/Update ArgoCD in TinyOlly Kind cluster
# This script applies Terraform changes to deploy ArgoCD

set -e

cd "$(dirname "$0")"

echo "🚀 Deploying ArgoCD to TinyOlly cluster..."
echo ""

# Navigate to Terraform directory
cd .kind

# Initialize if needed
if [ ! -d ".terraform" ]; then
    echo "Initializing Terraform..."
    terraform init
fi

# Plan changes
echo ""
echo "📋 Planning ArgoCD deployment..."
terraform plan -out=tfplan

# Apply changes
echo ""
read -p "Apply changes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    terraform apply tfplan
    rm -f tfplan
    
    echo ""
    echo "✅ ArgoCD deployment complete!"
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. Wait for ArgoCD pods to be ready:"
    echo "   kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s"
    echo ""
    echo "2. Get admin password:"
    echo "   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d && echo"
    echo ""
    echo "3. Access ArgoCD UI:"
    echo "   kubectl port-forward svc/argocd-server -n argocd 8080:443"
    echo "   Open: https://localhost:8080"
    echo "   Username: admin"
    echo "   Password: (from step 2)"
    echo ""
    echo "4. Install ArgoCD CLI (optional):"
    echo "   brew install argocd  # macOS"
    echo ""
    echo "For more info, see: .kind/modules/main/ARGOCD.md"
else
    echo "Deployment cancelled"
    rm -f tfplan
    exit 1
fi
