# Makefile for ollyScale KIND cluster management
#
# Project configuration
PROJECT_NAME ?= ollyScale
PROJECT_SLUG ?= ollyscale
GH_ORG ?= ryanfaircloth
GH_REPO ?= ollyscale

# Container configuration
REGISTRY ?= ghcr.io
REGISTRY_ORG ?= $(GH_ORG)
IMAGE_PREFIX ?= $(REGISTRY)/$(REGISTRY_ORG)

# Kubernetes configuration
CLUSTER_NAME ?= $(PROJECT_SLUG)
NAMESPACE ?= observability

# Legacy cluster name support (can be overridden)
LEGACY_CLUSTER_NAME := ollyscale

# Use legacy name if it exists, otherwise use new name
ACTIVE_CLUSTER_NAME := $(shell if kind get clusters 2>/dev/null | grep -q "^$(LEGACY_CLUSTER_NAME)$$"; then echo "$(LEGACY_CLUSTER_NAME)"; else echo "$(CLUSTER_NAME)"; fi)

#
# Targets:
#   up           : Create KIND cluster with local registry (infrastructure only)
#   deploy       : Build local images and deploy to cluster
#   down         : Destroy KIND cluster and registry
#   clean        : Remove terraform state files
#   demos        : Deploy custom demo applications
#   demos-otel   : Deploy OpenTelemetry Demo
#   demos-all    : Deploy both custom and OTel demos
#   demos-off    : Disable all demos
#   precommit-setup : Install and configure pre-commit hooks
#   lint         : Run pre-commit checks on all files
#   lint-fix     : Run pre-commit with auto-fix on all files

.PHONY: up deploy down clean demos demos-otel demos-all demos-off precommit-setup lint lint-fix

## Create KIND cluster with local registry (infrastructure only, no $(PROJECT_NAME) apps)
up:
	@if [ ! -f .kind/terraform.tfstate ]; then \
		cd $(CURDIR)/.kind && terraform init; \
	fi
	@if ! kind get clusters 2>/dev/null | grep -q "^$(ACTIVE_CLUSTER_NAME)$$"; then \
		echo "🚀 Bootstrap mode: Creating new cluster..."; \
		cd $(CURDIR)/.kind && export TF_VAR_bootstrap=true && terraform apply -auto-approve; \
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
		cd $(CURDIR)/.kind && export TF_VAR_bootstrap=false && terraform apply -auto-approve; \
	else \
		echo "♻️  Updating existing cluster..."; \
		cd $(CURDIR)/.kind && export TF_VAR_bootstrap=false && terraform apply -auto-approve; \
	fi
	@echo ""
	@echo "🎉 KIND cluster ready!"
	@echo ""
	@echo "📋 Next Steps:"
	@echo "  1. Build and deploy: make deploy"
	@echo "  2. Access ArgoCD UI: https://argocd.ollyscale.test:49443"
	@echo "  3. Get ArgoCD admin password:"
	@echo "     cd .kind && terraform output -raw argocd_admin_password"
	@echo ""

## Build local images and deploy to cluster
deploy:
	@set -e; \
	if ! kind get clusters 2>/dev/null | grep -q "^$(ACTIVE_CLUSTER_NAME)$$"; then \
		echo "❌ Cluster not found. Run 'make up' first!"; \
		exit 1; \
	fi; \
	echo "🔨 Building local images..."; \
	VERSION="0.0.$$(date +%s)"; \
	cd $(CURDIR)/charts && ./build-and-push-local.sh "$$VERSION"; \
	echo ""; \
	echo "✅ Images built and pushed: version $$VERSION"; \
	echo ""; \
	echo "🔄 Creating terraform auto vars file..."; \
	BASE_CHART_VERSION=$$(grep "^version:" $(CURDIR)/charts/ollyscale/Chart.yaml | awk '{print $$2}' | cut -d'-' -f1); \
	AGENT_BASE_CHART_VERSION=$$(grep "^version:" $(CURDIR)/charts/ollyscale-otel-agent/Chart.yaml | awk '{print $$2}' | cut -d'-' -f1); \
	echo "ollyscale_chart_tag = \"$$BASE_CHART_VERSION-$$VERSION\"" > $(CURDIR)/.kind/terraform.auto.tfvars; \
	echo "ollyscale_tag = \"$$VERSION\"" >> $(CURDIR)/.kind/terraform.auto.tfvars; \
	echo "opamp_tag = \"$$VERSION\"" >> $(CURDIR)/.kind/terraform.auto.tfvars; \
	echo "ai_agent_chart_tag = \"$$AGENT_BASE_CHART_VERSION-$$VERSION\"" >> $(CURDIR)/.kind/terraform.auto.tfvars; \
	echo "ai_agent_image = \"docker-registry.registry.svc.cluster.local:5000/ollyscale/demo-otel-agent\"" >> $(CURDIR)/.kind/terraform.auto.tfvars; \
	echo "ai_agent_tag = \"$$VERSION\"" >> $(CURDIR)/.kind/terraform.auto.tfvars; \
	echo "🔄 Updating ArgoCD application..."; \
	cd $(CURDIR)/.kind; \
	terraform apply -auto-approve; \
	echo ""; \
	echo "⏳ Waiting for ollyscale to sync..."; \
	echo "   This may take a few minutes on first deployment or major upgrades."; \
	for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do \
		SYNC_STATUS=$$(kubectl get application ollyscale -n argocd -o jsonpath='{.status.sync.status}' 2>/dev/null || echo "NotFound"); \
		HEALTH_STATUS=$$(kubectl get application ollyscale -n argocd -o jsonpath='{.status.health.status}' 2>/dev/null || echo "Unknown"); \
		if [ "$$SYNC_STATUS" = "Synced" ] && [ "$$HEALTH_STATUS" = "Healthy" ]; then \
			echo "✅ ollyscale is synced and healthy!"; \
			break; \
		fi; \
		echo "   Status: Sync=$$SYNC_STATUS, Health=$$HEALTH_STATUS (attempt $$i/12)"; \
		if [ $$i -eq 12 ]; then \
			echo "⚠️  Timeout waiting for ollyscale to sync. Check status with:"; \
			echo "     kubectl get application ollyscale -n argocd"; \
			break; \
		fi; \
		sleep 15; \
	done; \
	echo ""; \
	echo "✅ Deployment complete!"; \
	echo ""; \
	echo "📋 Access $(PROJECT_NAME):"; \
	echo "  UI: https://ollyscale.ollyscale.test:49443"; \
	echo ""

## Destroy KIND cluster and registry
down:
	@echo "Deleting KIND cluster..."
	-kind delete cluster --name $(ACTIVE_CLUSTER_NAME)
	@echo "Cleaning up terraform state and config files..."
	-rm -f .kind/terraform.tfstate .kind/terraform.tfstate.backup
	-rm -f .kind/$(ACTIVE_CLUSTER_NAME)-config
	@echo "Cleanup complete!"

## Remove terraform state files
clean:
	rm -f .kind/terraform.tfstate .kind/terraform.tfstate.backup
	rm -f .kind/$(ACTIVE_CLUSTER_NAME)-config

## Deploy custom demo applications (demo-frontend + demo-backend)
demos:
	@echo "🚀 Deploying custom demo applications..."
	@cd $(CURDIR)/.kind && \
		export TF_VAR_bootstrap=false && \
		export TF_VAR_custom_demo_enabled=true && \
		export TF_VAR_otel_demo_enabled=false && \
		terraform apply -auto-approve
	@echo ""
	@echo "✅ Custom demos deployed!"
	@echo "   Access: https://demo-frontend.ollyscale.test:49443"
	@echo ""

## Deploy OpenTelemetry Demo (astronomy shop)
demos-otel:
	@echo "🚀 Deploying OpenTelemetry Demo..."
	@cd $(CURDIR)/.kind && \
		export TF_VAR_bootstrap=false && \
		export TF_VAR_custom_demo_enabled=false && \
		export TF_VAR_otel_demo_enabled=true && \
		terraform apply -auto-approve
	@echo ""
	@echo "✅ OTel Demo deployed!"
	@echo "   Access: https://otel-demo.ollyscale.test:49443"
	@echo ""

## Deploy both custom and OpenTelemetry demos
demos-all:
	@echo "🚀 Deploying all demo applications..."
	@cd $(CURDIR)/.kind && \
		export TF_VAR_bootstrap=false && \
		export TF_VAR_custom_demo_enabled=true && \
		export TF_VAR_otel_demo_enabled=true && \
		terraform apply -auto-approve
	@echo ""
	@echo "✅ All demos deployed!"
	@echo "   Custom Demo: https://demo-frontend.ollyscale.test:49443"
	@echo "   OTel Demo:   https://otel-demo.ollyscale.test:49443"
	@echo ""

## Disable all demo applications
demos-off:
	@echo "⏹️  Disabling demo applications..."
	@export TF_VAR_bootstrap=false && \
		export TF_VAR_custom_demo_enabled=false && \
		export TF_VAR_otel_demo_enabled=false && \
		pushd .kind && terraform apply -auto-approve && popd
	@echo ""
	@echo "✅ Demos disabled!"
	@echo ""

## Install and configure pre-commit hooks
precommit-setup:
	@./setup-precommit.sh

## Run pre-commit checks on all files
lint:
	@pre-commit run --all-files

## Run pre-commit with auto-fix on all files
lint-fix:
	@pre-commit run --all-files || true
	@echo "🔧 Auto-fixes applied where possible. Review changes before committing."
