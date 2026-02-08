# =============================================================================
# apps/demo-otel-agent/Makefile - AI Agent Demo Build
# =============================================================================

# Include shared configuration and functions
include ../../config.mk
include ../../build.mk

COMPONENT := demo-otel-agent
DOCKERFILE := Dockerfile
CONTEXT := .

# Source files that trigger rebuild when changed
CONTENT_SOURCES := agent.py test_agent.py pyproject.toml Dockerfile

.PHONY: install
install: ## Install demo agent dependencies
	@echo "📦 Installing demo agent dependencies..."
	@uv sync --all-extras
	@echo "✅ Demo agent dependencies installed"

.PHONY: test
test: install ## Run demo agent tests
	@if [ -f "test_agent.py" ]; then \
		echo "🧪 Running demo agent tests..."; \
		uv run pytest test_agent.py -v || exit 1; \
		echo "✅ Demo agent tests passed"; \
	else \
		echo "⚠️  No tests found for demo-agent (skipping)"; \
	fi

.PHONY: build
build: ensure-build-dirs ## Build demo agent image
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
push: ## Push demo agent image
	@VERSION=$$(cat $(VERSION_DIR)/$(COMPONENT) 2>/dev/null || echo "$(VERSION)"); \
	echo "📤 Pushing $(COMPONENT)..."; \
	$(CONTAINER_RUNTIME) push $(PUSH_FLAGS) \
		$(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/$(COMPONENT):$$VERSION; \
	echo "✅ $(COMPONENT) pushed"
