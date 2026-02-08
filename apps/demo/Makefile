# =============================================================================
# apps/demo/Makefile - Unified Demo Build
# =============================================================================

# Include shared configuration and functions
include ../../config.mk
include ../../build.mk

COMPONENT := demo
DOCKERFILE := Dockerfile
CONTEXT := .

# Source files that trigger rebuild when changed
CONTENT_SOURCES := frontend.py backend.py pyproject.toml Dockerfile

.PHONY: install
install: ## Install demo dependencies
	@echo "📦 Installing demo dependencies..."
	@uv sync --all-extras
	@echo "✅ Demo dependencies installed"

.PHONY: test
test: install ## Run demo tests
	@if [ -f "test_demo.py" ]; then \
		echo "🧪 Running demo tests..."; \
		uv run pytest test_demo.py -v || exit 1; \
		echo "✅ Demo tests passed"; \
	else \
		echo "⚠️  No tests found for demo (skipping)"; \
	fi

.PHONY: build
build: ensure-build-dirs ## Build demo image
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
push: ## Push demo image
	@VERSION=$$(cat $(VERSION_DIR)/$(COMPONENT) 2>/dev/null || echo "$(VERSION)"); \
	echo "📤 Pushing $(COMPONENT)..."; \
	$(CONTAINER_RUNTIME) push $(PUSH_FLAGS) \
		$(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/$(COMPONENT):$$VERSION; \
	echo "✅ $(COMPONENT) pushed"
