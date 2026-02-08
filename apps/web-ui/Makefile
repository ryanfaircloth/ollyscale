# =============================================================================
# apps/web-ui/Makefile - Web UI Build
# =============================================================================

# Include shared configuration and functions
include ../../config.mk
include ../../build.mk

COMPONENT := web-ui
DOCKERFILE := Dockerfile
CONTEXT := .

# Source files that trigger rebuild when changed
CONTENT_SOURCES := src/ public/ index.html vite.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json package.json package-lock.json nginx/ Dockerfile

.PHONY: install
install: ## Install web UI dependencies
	@echo "📦 Installing web UI dependencies..."
	@npm install --silent 2>/dev/null || true
	@echo "✅ Web UI dependencies installed"

.PHONY: test
test: install ## Run web UI tests
	@if [ -f "package.json" ] && grep -q "vitest" package.json; then \
		echo "🧪 Running web UI tests..."; \
		npm test || exit 1; \
		echo "✅ Web UI tests passed"; \
	else \
		echo "⚠️  No tests configured for web-ui (skipping)"; \
	fi

.PHONY: build
build: ensure-build-dirs ## Build web UI image
	@CHANGED=$(call sources-changed,$(COMPONENT),$(CONTENT_SOURCES)); \
	if [ "$$CHANGED" = "no" ]; then \
		BUILD_VERSION=$(call read-version,$(COMPONENT)); \
		echo "⏭️  Skipping $(COMPONENT): no changes detected (version $$BUILD_VERSION)"; \
	else \
		BUILD_VERSION=$(VERSION); \
		echo "🔨 Building $(COMPONENT) version $$BUILD_VERSION"; \
		$(CONTAINER_RUNTIME) build \
			--layers \
			-f $(DOCKERFILE) \
			-t $(PROJECT_SLUG)/$(COMPONENT):$$BUILD_VERSION \
			-t $(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/$(COMPONENT):$$BUILD_VERSION \
			--platform $(BUILD_PLATFORMS) \
			$(CONTEXT); \
		echo "✅ $(COMPONENT) built"; \
		$(call write-version,$(COMPONENT),$$BUILD_VERSION); \
	fi

.PHONY: push
push: ## Push web UI image
	@VERSION=$$(cat $(VERSION_DIR)/$(COMPONENT) 2>/dev/null || echo "$(VERSION)"); \
	echo "📤 Pushing $(COMPONENT)..."; \
	$(CONTAINER_RUNTIME) push $(PUSH_FLAGS) \
		$(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/$(COMPONENT):$$VERSION; \
	echo "✅ $(COMPONENT) pushed"
