# =============================================================================
# apps/opamp-server/Makefile - OpAMP Server Build
# =============================================================================

# Include shared configuration and functions
include ../../config.mk
include ../../build.mk

COMPONENT := opamp-server
DOCKERFILE := Dockerfile
CONTEXT := .

# Source files that trigger rebuild when changed
CONTENT_SOURCES := *.go go.mod go.sum Dockerfile

.PHONY: install
install: ## Install OpAMP dependencies (Go modules)
	@echo "📦 Installing OpAMP dependencies..."
	@go mod download 2>/dev/null || echo "⚠️  Go modules not found or already cached"
	@echo "✅ OpAMP dependencies ready"

.PHONY: test
test: ## Run OpAMP tests
	@echo "⚠️  No tests configured for OpAMP server (skipping)"

.PHONY: build
build: ensure-build-dirs ## Build OpAMP server image
	@CHANGED=$(call sources-changed,opamp,$(CONTENT_SOURCES)); \
	if [ "$$CHANGED" = "no" ]; then \
		BUILD_VERSION=$(call read-version,opamp); \
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
		$(call write-version,opamp,$$BUILD_VERSION); \
	fi

.PHONY: push
push: ## Push OpAMP server image
	@VERSION=$$(cat $(VERSION_DIR)/opamp 2>/dev/null || echo "$(VERSION)"); \
	echo "📤 Pushing $(COMPONENT)..."; \
	$(CONTAINER_RUNTIME) push $(PUSH_FLAGS) \
		$(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/$(COMPONENT):$$VERSION; \
	echo "✅ $(COMPONENT) pushed"
