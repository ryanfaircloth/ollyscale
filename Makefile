# Makefile for TinyOlly KIND cluster management
#
# Targets:
#   up           : Create KIND cluster with local registry
#   down         : Destroy KIND cluster and registry
#   clean        : Remove terraform state files

# Cluster configuration
CLUSTER_NAME := tinyolly

.PHONY: up down clean

## Create KIND cluster with local registry
up:
	@if [ ! -f .kind/terraform.tfstate ]; then \
		pushd .kind && terraform init && popd; \
	fi
	@# Check if cluster exists to determine bootstrap mode
	@if ! kind get clusters 2>/dev/null | grep -q "^$(CLUSTER_NAME)$$"; then \
		echo "🚀 Bootstrap mode: Creating new cluster..."; \
		export TF_VAR_bootstrap=true && pushd .kind && terraform apply -auto-approve && popd; \
		echo ""; \
		echo "⏳ Waiting for ArgoCD to sync infrastructure apps..."; \
		sleep 30; \
		echo "⏳ Waiting for Gateway API CRDs to be installed..."; \
		for i in 1 2 3 4 5 6 7 8 9 10; do \
			if kubectl get crd gateways.gateway.networking.k8s.io httproutes.gateway.networking.k8s.io 2>/dev/null; then \
				echo "✅ Gateway API CRDs are ready!"; \
				kubectl wait --for condition=established --timeout=60s crd/gateways.gateway.networking.k8s.io crd/httproutes.gateway.networking.k8s.io; \
				break; \
			fi; \
			echo "  Attempt $$i/10: CRDs not found yet, waiting 30s..."; \
			sleep 30; \
		done; \
		echo ""; \
		echo "🔄 Running second pass to enable HTTPRoutes..."; \
		export TF_VAR_bootstrap=false && pushd .kind && terraform apply -auto-approve && popd; \
	else \
		echo "♻️  Updating existing cluster..."; \
		export TF_VAR_bootstrap=false && pushd .kind && terraform apply -auto-approve && popd; \
	fi
	@echo ""
	@echo "🎉 TinyOlly cluster deployment complete!"
	@echo ""
	@echo "📋 Next Steps:"
	@echo "  1. Access ArgoCD UI: https://argocd.tinyolly.test:49443"
	@echo "  2. Get ArgoCD admin password:"
	@echo "     cd .kind && terraform output -raw argocd_admin_password"
	@echo "  3. Deploy applications via ArgoCD"
	@echo ""

## Destroy KIND cluster and registry
down:
	@echo "Deleting KIND cluster..."
	-kind delete cluster --name $(CLUSTER_NAME)
	@echo "Cleaning up terraform state and config files..."
	-rm -f .kind/terraform.tfstate .kind/terraform.tfstate.backup
	-rm -f .kind/$(CLUSTER_NAME)-config
	@echo "Cleanup complete!"

## Remove terraform state files
clean:
	rm -f .kind/terraform.tfstate .kind/terraform.tfstate.backup
	rm -f .kind/$(CLUSTER_NAME)-config