# =============================================================================
# Makefile - OllyScale Build System
# =============================================================================
# Unified build configuration for local (Podman) and CI (Docker buildx)
# Replaces Taskfile with proper lazy evaluation and centralized build artifacts

.PHONY: help
.DEFAULT_GOAL := help

# Include configuration
include config.mk
include build.mk

# Include environment-specific logic (local or CI)
ifdef CI
include ci.mk
else
include local.mk
endif

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "OllyScale Build System"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup & Validation:"
	@echo "  check          - Check prerequisites and configuration"
	@echo "  install        - Install dependencies for all projects"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all unit tests"
	@echo "  test-api       - Run API tests"
	@echo "  test-demo      - Run demo tests"
	@echo "  test-demo-agent - Run demo agent tests"
	@echo "  test-web-ui    - Run web UI tests"
	@echo ""
	@echo "Linting:"
	@echo "  lint           - Run pre-commit checks"
	@echo "  lint-fix       - Run pre-commit with auto-fix"
	@echo ""
	@echo "Building:"
	@echo "  build          - Build all images and charts"
	@echo "  build-images   - Build all container images"
	@echo "  build-charts   - Build all Helm charts"
	@echo ""
	@echo "Pushing:"
	@echo "  push           - Push all images and charts"
	@echo "  push-images    - Push all container images"
	@echo "  push-charts    - Push all Helm charts"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy         - Build, push, and deploy to KIND cluster"
	@echo "  up             - Create KIND cluster"
	@echo "  down           - Destroy KIND cluster"
	@echo ""
	@echo "Debugging:"
	@echo "  show-versions  - Display all component versions"
	@echo "  show-status    - Show which components need rebuilding"
	@echo "  clean-metadata - Clear version metadata (forces full rebuild)"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean          - Remove build artifacts (.build/ directory)"
	@echo "  clean-cache    - Clean container build cache"

# =============================================================================
# Setup & Validation
# =============================================================================

.PHONY: check
check: check-prerequisites ## Check prerequisites and configuration

.PHONY: install
install: ## Install dependencies for all projects
	@$(MAKE) -C apps/api install
	@$(MAKE) -C apps/demo install
	@$(MAKE) -C apps/demo-otel-agent install
	@$(MAKE) -C apps/web-ui install
	@echo "✅ All dependencies installed"

# =============================================================================
# Testing
# =============================================================================

.PHONY: test
test: test-api test-demo test-demo-agent test-web-ui ## Run all tests
	@echo "✅ All tests passed"

.PHONY: test-api
test-api: ## Run API tests
	@$(MAKE) -C apps/api test

.PHONY: test-demo
test-demo: ## Run demo tests
	@$(MAKE) -C apps/demo test

.PHONY: test-demo-agent
test-demo-agent: ## Run demo agent tests
	@$(MAKE) -C apps/demo-otel-agent test

.PHONY: test-web-ui
test-web-ui: ## Run web UI tests
	@$(MAKE) -C apps/web-ui test

# =============================================================================
# Linting
# =============================================================================

.PHONY: lint
lint: ## Run pre-commit checks
	@echo "Running pre-commit checks..."
	@pre-commit run --all-files
	@echo "✅ Lint checks passed"

.PHONY: lint-fix
lint-fix: ## Run pre-commit with auto-fix
	@echo "🔧 Running pre-commit with auto-fix..."
	@pre-commit run --all-files || true
	@echo "🔧 Auto-fixes applied. Review changes before committing."

# =============================================================================
# Building - Images
# =============================================================================

.PHONY: build-images
build-images: ensure-build-dirs ## Build all container images
	@$(MAKE) -C apps/api build
	@$(MAKE) -C apps/web-ui build
	@$(MAKE) -C apps/opamp-server build
	@$(MAKE) -C apps/demo build
	@$(MAKE) -C apps/demo-otel-agent build
	@echo "✅ All images built"

# =============================================================================
# Building - Charts
# =============================================================================

.PHONY: build-charts
build-charts: build-images ensure-build-dirs ## Build all Helm charts
	@$(MAKE) -C charts/ollyscale build
	@$(MAKE) -C charts/ollyscale-postgres build
	@$(MAKE) -C charts/ollyscale-otel build
	@$(MAKE) -C charts/ollyscale-demos build
	@$(MAKE) -C charts/ollyscale-otel-agent build
	@echo "✅ All charts built"

.PHONY: build
build: build-images build-charts ## Build all images and charts

# =============================================================================
# Pushing - Images
# =============================================================================

.PHONY: push-images
push-images: ## Push all container images
	@$(MAKE) -C apps/api push
	@$(MAKE) -C apps/web-ui push
	@$(MAKE) -C apps/opamp-server push
	@$(MAKE) -C apps/demo push
	@$(MAKE) -C apps/demo-otel-agent push
	@echo "✅ All images pushed"

# =============================================================================
# Pushing - Charts
# =============================================================================

.PHONY: push-charts
push-charts: ## Push all Helm charts
	@$(MAKE) -C charts/ollyscale push
	@$(MAKE) -C charts/ollyscale-postgres push
	@$(MAKE) -C charts/ollyscale-otel push
	@$(MAKE) -C charts/ollyscale-demos push
	@$(MAKE) -C charts/ollyscale-otel-agent push
	@echo "✅ All charts pushed"

.PHONY: push
push: push-images push-charts ## Push all images and charts

# =============================================================================
# Deployment
# =============================================================================

.PHONY: deploy
deploy: build push ## Build, push, and deploy to local KIND cluster
	@echo "🔄 Updating terraform auto vars..."
	@mkdir -p .kind
	@VER_API=$$(cat $(VERSION_DIR)/api 2>/dev/null || echo "missing"); \
	VER_WEBUI=$$(cat $(VERSION_DIR)/web-ui 2>/dev/null || echo "missing"); \
	VER_OPAMP=$$(cat $(VERSION_DIR)/opamp 2>/dev/null || echo "missing"); \
	VER_DEMO_AGENT=$$(cat $(VERSION_DIR)/demo-otel-agent 2>/dev/null || echo "missing"); \
	VER_CHART_OLLYSCALE=$$(cat $(VERSION_DIR)/chart-ollyscale 2>/dev/null || echo "missing"); \
	VER_CHART_POSTGRES=$$(cat $(VERSION_DIR)/chart-ollyscale-postgres 2>/dev/null || yq eval '.version' charts/ollyscale-postgres/Chart.yaml); \
	VER_CHART_OTEL=$$(cat $(VERSION_DIR)/chart-ollyscale-otel 2>/dev/null || yq eval '.version' charts/ollyscale-otel/Chart.yaml); \
	VER_CHART_OTEL_AGENT=$$(cat $(VERSION_DIR)/chart-ollyscale-otel-agent 2>/dev/null || echo "missing"); \
	echo "ollyscale_tag = \"$$VER_API\"" > .kind/api.auto.tfvars; \
	echo "webui_tag = \"$$VER_WEBUI\"" > .kind/webui.auto.tfvars; \
	echo "opamp_tag = \"$$VER_OPAMP\"" > .kind/opamp.auto.tfvars; \
	echo "ai_agent_tag = \"$$VER_DEMO_AGENT\"" > .kind/demo-otel-agent.auto.tfvars; \
	echo "ai_agent_image = \"$(INTERNAL_REGISTRY)/$(PROJECT_SLUG)/demo-otel-agent\"" >> .kind/demo-otel-agent.auto.tfvars; \
	echo "ollyscale_chart_tag = \"$$VER_CHART_OLLYSCALE\"" > .kind/chart-ollyscale.auto.tfvars; \
	echo "postgres_chart_tag = \"$$VER_CHART_POSTGRES\"" > .kind/chart-postgres.auto.tfvars; \
	echo "ollyscale_otel_chart_tag = \"$$VER_CHART_OTEL\"" > .kind/chart-otel.auto.tfvars; \
	echo "ai_agent_chart_tag = \"$$VER_CHART_OTEL_AGENT\"" > .kind/chart-otel-agent.auto.tfvars
	@echo "🔄 Applying terraform configuration..."
	@cd .kind && terraform apply -auto-approve
	@echo "✅ Deployment complete!"

.PHONY: up
up: ## Create KIND cluster
	@cd .kind && \
	if [ ! -f terraform.tfstate ]; then terraform init; fi && \
	if ! kind get clusters 2>/dev/null | grep -q "^$(CLUSTER_NAME)$$"; then \
		echo "🚀 Creating new cluster..."; \
		export TF_VAR_bootstrap=true && terraform apply -auto-approve; \
		echo "⏳ Waiting for Gateway API CRDs..."; \
		sleep 30; \
		for i in 1 2 3 4 5 6 7 8 9 10; do \
			if kubectl get crd gateways.gateway.networking.k8s.io httproutes.gateway.networking.k8s.io 2>/dev/null; then \
				echo "✅ Gateway API CRDs ready!"; \
				kubectl wait --for condition=established --timeout=60s crd/gateways.gateway.networking.k8s.io crd/httproutes.gateway.networking.k8s.io; \
				break; \
			fi; \
			echo "  Attempt $$i/10: CRDs not found, waiting..."; \
			sleep 30; \
		done; \
		echo "🔄 Second pass to enable HTTPRoutes..."; \
		export TF_VAR_bootstrap=false && terraform apply -auto-approve; \
	else \
		echo "♻️  Updating existing cluster..."; \
		export TF_VAR_bootstrap=false && terraform apply -auto-approve; \
	fi
	@echo "✅ KIND cluster ready!"

.PHONY: down
down: ## Destroy KIND cluster
	@echo "Deleting KIND cluster..."
	@kind delete cluster --name $(CLUSTER_NAME) || true
	@rm -f .kind/terraform.tfstate .kind/terraform.tfstate.backup
	@echo "✅ Cleanup complete!"

# =============================================================================
# Debugging
# =============================================================================

.PHONY: show-versions
show-versions: ## Display all component versions
	@echo "📋 Component Versions:"
	@echo ""
	@echo "Images:"
	@printf "  %-20s %s\n" "api:" "$$(cat $(VERSION_DIR)/api 2>/dev/null || echo 'not built')"
	@printf "  %-20s %s\n" "web-ui:" "$$(cat $(VERSION_DIR)/web-ui 2>/dev/null || echo 'not built')"
	@printf "  %-20s %s\n" "opamp-server:" "$$(cat $(VERSION_DIR)/opamp 2>/dev/null || echo 'not built')"
	@printf "  %-20s %s\n" "demo:" "$$(cat $(VERSION_DIR)/demo 2>/dev/null || echo 'not built')"
	@printf "  %-20s %s\n" "demo-otel-agent:" "$$(cat $(VERSION_DIR)/demo-otel-agent 2>/dev/null || echo 'not built')"
	@echo ""
	@echo "Charts:"
	@printf "  %-20s %s\n" "ollyscale:" "$$(cat $(VERSION_DIR)/chart-ollyscale 2>/dev/null || echo 'not built')"
	@printf "  %-20s %s\n" "ollyscale-postgres:" "$$(cat $(VERSION_DIR)/chart-ollyscale-postgres 2>/dev/null || echo 'not built')"
	@printf "  %-20s %s\n" "ollyscale-otel:" "$$(cat $(VERSION_DIR)/chart-ollyscale-otel 2>/dev/null || echo 'not built')"
	@printf "  %-20s %s\n" "ollyscale-demos:" "$$(cat $(VERSION_DIR)/chart-ollyscale-demos 2>/dev/null || echo 'not built')"
	@printf "  %-20s %s\n" "ollyscale-otel-agent:" "$$(cat $(VERSION_DIR)/chart-ollyscale-otel-agent 2>/dev/null || echo 'not built')"

.PHONY: show-status
show-status: ensure-build-dirs ## Show which components need rebuilding
	@echo "🔍 Build Status (checking timestamps):"
	@echo ""
	@echo "Images:"
	@if [ ! -f "$(VERSION_DIR)/api" ]; then \
		echo "  🔨 api: not built yet"; \
	elif [ -f "apps/api/app" -a "apps/api/app" -nt "$(VERSION_DIR)/api" ] || \
	     [ -f "apps/api/main.py" -a "apps/api/main.py" -nt "$(VERSION_DIR)/api" ] || \
	     [ -f "apps/api/Dockerfile" -a "apps/api/Dockerfile" -nt "$(VERSION_DIR)/api" ] || \
	     [ -f "apps/api/pyproject.toml" -a "apps/api/pyproject.toml" -nt "$(VERSION_DIR)/api" ]; then \
		echo "  🔨 api: needs rebuild (sources changed)"; \
	else \
		echo "  ⏭️  api: up-to-date"; \
	fi
	@if [ ! -f "$(VERSION_DIR)/web-ui" ]; then \
		echo "  🔨 web-ui: not built yet"; \
	elif [ -f "apps/web-ui/src" -a "apps/web-ui/src" -nt "$(VERSION_DIR)/web-ui" ] || \
	     [ -f "apps/web-ui/package.json" -a "apps/web-ui/package.json" -nt "$(VERSION_DIR)/web-ui" ] || \
	     [ -f "apps/web-ui/Dockerfile" -a "apps/web-ui/Dockerfile" -nt "$(VERSION_DIR)/web-ui" ]; then \
		echo "  🔨 web-ui: needs rebuild (sources changed)"; \
	else \
		echo "  ⏭️  web-ui: up-to-date"; \
	fi
	@if [ ! -f "$(VERSION_DIR)/opamp" ]; then \
		echo "  🔨 opamp-server: not built yet"; \
	elif [ -f "apps/opamp-server/main.go" -a "apps/opamp-server/main.go" -nt "$(VERSION_DIR)/opamp" ] || \
	     [ -f "apps/opamp-server/go.mod" -a "apps/opamp-server/go.mod" -nt "$(VERSION_DIR)/opamp" ] || \
	     [ -f "apps/opamp-server/Dockerfile" -a "apps/opamp-server/Dockerfile" -nt "$(VERSION_DIR)/opamp" ]; then \
		echo "  🔨 opamp-server: needs rebuild (sources changed)"; \
	else \
		echo "  ⏭️  opamp-server: up-to-date"; \
	fi
	@if [ ! -f "$(VERSION_DIR)/demo" ]; then \
		echo "  🔨 demo: not built yet"; \
	elif [ -f "apps/demo/frontend.py" -a "apps/demo/frontend.py" -nt "$(VERSION_DIR)/demo" ] || \
	     [ -f "apps/demo/Dockerfile" -a "apps/demo/Dockerfile" -nt "$(VERSION_DIR)/demo" ]; then \
		echo "  🔨 demo: needs rebuild (sources changed)"; \
	else \
		echo "  ⏭️  demo: up-to-date"; \
	fi
	@if [ ! -f "$(VERSION_DIR)/demo-otel-agent" ]; then \
		echo "  🔨 demo-otel-agent: not built yet"; \
	elif [ -f "apps/demo-otel-agent/agent.py" -a "apps/demo-otel-agent/agent.py" -nt "$(VERSION_DIR)/demo-otel-agent" ] || \
	     [ -f "apps/demo-otel-agent/Dockerfile" -a "apps/demo-otel-agent/Dockerfile" -nt "$(VERSION_DIR)/demo-otel-agent" ]; then \
		echo "  🔨 demo-otel-agent: needs rebuild (sources changed)"; \
	else \
		echo "  ⏭️  demo-otel-agent: up-to-date"; \
	fi
	@echo ""
	@echo "Tip: Run 'make build-images' to build only changed components"
	@echo "Tip: Run 'make FORCE_REBUILD=1 build-images' to force rebuild all"

.PHONY: clean-metadata
clean-metadata: ## Clear version metadata (forces full rebuild)
	@echo "🗑️  Clearing build metadata..."
	@rm -rf $(VERSION_DIR)
	@echo "✅ Metadata cleared - next build will rebuild everything"

# =============================================================================
# Cleanup
# =============================================================================

.PHONY: clean
clean: ## Remove build artifacts
	@echo "🗑️  Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@rm -f .kind/*.auto.tfvars
	@echo "✅ Build artifacts cleaned"

.PHONY: clean-cache
clean-cache: ## Clean container build cache
	@echo "🗑️  Cleaning container build cache..."
	@if [ "$(CONTAINER_RUNTIME)" = "podman" ]; then \
		podman system prune -f; \
		echo "✅ Podman build cache cleaned"; \
	else \
		docker builder prune -f; \
		echo "✅ Docker build cache cleaned"; \
	fi
