# =============================================================================
# apps/api/Makefile - API Backend Build
# =============================================================================

# Include shared configuration and functions
include ../../config.mk
include ../../build.mk

COMPONENT := api
DOCKERFILE := Dockerfile
CONTEXT := .

# Source files that trigger rebuild when changed
CONTENT_SOURCES := app/ common/ receiver/ alembic/ main.py alembic.ini pyproject.toml Dockerfile

.PHONY: install
install: ## Install API dependencies
	@echo "📦 Installing API dependencies..."
	@uv sync --all-extras
	@echo "✅ API dependencies installed"

.PHONY: test
test: install ## Run API tests
	@if [ -f "pyproject.toml" ] && grep -q "pytest" pyproject.toml; then \
		echo "🧪 Running API tests..."; \
		uv run pytest tests/ -v || exit 1; \
		echo "✅ API tests passed"; \
	else \
		echo "⚠️  No tests configured for API (skipping)"; \
	fi

.PHONY: build
build: ensure-build-dirs ## Build API image
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
push: ## Push API image
	@VERSION=$$(cat $(VERSION_DIR)/$(COMPONENT) 2>/dev/null || echo "$(VERSION)"); \
	echo "📤 Pushing $(COMPONENT)..."; \
	$(CONTAINER_RUNTIME) push $(PUSH_FLAGS) \
		$(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/$(COMPONENT):$$VERSION; \
	echo "✅ $(COMPONENT) pushed"
