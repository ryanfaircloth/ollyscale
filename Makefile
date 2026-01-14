# Makefile for TinyOlly KIND cluster management
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

# Cluster configuration
CLUSTER_NAME := tinyolly

.PHONY: up deploy down clean demos demos-otel demos-all demos-off precommit-setup lint lint-fix

## Create KIND cluster with local registry (infrastructure only, no TinyOlly apps)
up:
	@if [ ! -f .kind/terraform.tfstate ]; then \
		cd $(CURDIR)/.kind && terraform init; \
	fi
	@if ! kind get clusters 2>/dev/null | grep -q "^$(CLUSTER_NAME)$$"; then \
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
	@echo "  2. Access ArgoCD UI: https://argocd.tinyolly.test:49443"
	@echo "  3. Get ArgoCD admin password:"
	@echo "     cd .kind && terraform output -raw argocd_admin_password"
	@echo ""

## Build local images and deploy to cluster
deploy:
	@if ! kind get clusters 2>/dev/null | grep -q "^$(CLUSTER_NAME)$$"; then \
		echo "❌ Cluster not found. Run 'make up' first!"; \
		exit 1; \
	fi
	@echo "🔨 Building local images..."
	@VERSION="0.0.$$(date +%s)"; \
	cd $(CURDIR)/charts && ./build-and-push-local.sh "$$VERSION"; \
	echo "" && \
	echo "✅ Images built and pushed: version $$VERSION" && \
	echo "" && \
	echo "🔄 Creating terraform auto vars file..." && \
	echo "tinyolly_chart_tag = \"0.3.0-$$VERSION\"" > $(CURDIR)/.kind/terraform.auto.tfvars && \
	echo "tinyolly_tag = \"$$VERSION\"" >> $(CURDIR)/.kind/terraform.auto.tfvars && \
	echo "opamp_tag = \"$$VERSION\"" >> $(CURDIR)/.kind/terraform.auto.tfvars && \
	echo "🔄 Updating ArgoCD application..." && \
	cd $(CURDIR)/.kind && \
	terraform apply -auto-approve && \
	echo "" && \
	echo "✅ Deployment complete!" && \
	echo "" && \
	echo "📋 Access TinyOlly:" && \
	echo "  UI: https://tinyolly.tinyolly.test:49443" && \
	echo ""

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
	@echo "   Access: https://demo-frontend.tinyolly.test:49443"
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
	@echo "   Access: https://otel-demo.tinyolly.test:49443"
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
	@echo "   Custom Demo: https://demo-frontend.tinyolly.test:49443"
	@echo "   OTel Demo:   https://otel-demo.tinyolly.test:49443"
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
