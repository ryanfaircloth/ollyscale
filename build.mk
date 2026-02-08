# =============================================================================
# build.mk - Shared Build Functions
# =============================================================================
# Helper functions used across all Makefiles
#
# Timestamp-Based Build System:
# - Uses Make's built-in file timestamp comparison
# - Version files in .build/versions/<component> act as sentinels
# - Components declare CONTENT_SOURCES as prerequisites
# - Rebuilds only when sources are newer than version file (or version missing)
# - Set FORCE_REBUILD=1 to force rebuild regardless of timestamps

# Ensure build directories exist
.PHONY: ensure-build-dirs
ensure-build-dirs:
	@mkdir -p $(VERSION_DIR) $(PACKAGE_DIR)

# Function: write version to file
# Usage: call directly in recipe: @$(call write-version,component-name,version-string)
# Note: This must be a single-line command for make to execute properly
define write-version
mkdir -p $(VERSION_DIR) && echo "$(2)" > $(VERSION_DIR)/$(1) && echo "📝 Version file written: $(VERSION_DIR)/$(1) = $(2)"
endef

# Function: read version from file
# Usage: VERSION_API = $(call read-version,api)
define read-version
$(shell cat $(VERSION_DIR)/$(1) 2>/dev/null || echo "missing")
endef

# Function: check if version file exists
# Usage: $(call version-exists,component-name)
# Returns: "yes" if exists, "no" if missing
define version-exists
$(shell test -f $(VERSION_DIR)/$(1) && echo "yes" || echo "no")
endef

# Function: check if any source files are newer than version file
# Usage: $(call sources-changed,component-name,source-file-list)
# Returns: "yes" if any source is newer or version missing, "no" if version is up-to-date
define sources-changed
$(shell \
	if [ "$(FORCE_REBUILD)" = "1" ]; then \
		echo "yes"; \
	elif [ ! -f "$(VERSION_DIR)/$(1)" ]; then \
		echo "yes"; \
	else \
		VERSION_FILE="$(VERSION_DIR)/$(1)"; \
		for src in $(2); do \
			if [ -e "$$src" ] && [ "$$src" -nt "$$VERSION_FILE" ]; then \
				echo "yes"; \
				exit 0; \
			fi; \
		done; \
		echo "no"; \
	fi)
endef

# Function: get package path
# Usage: PACKAGE_PATH = $(call package-path,chart-name,version)
define package-path
$(PACKAGE_DIR)/$(1)-$(2).tgz
endef

# Function: check required command
# Usage: $(call check-command,command-name,install-hint)
define check-command
	@if ! command -v $(1) >/dev/null 2>&1; then \
		echo "❌ $(1) not found"; \
		echo "   Install: $(2)"; \
		exit 1; \
	fi
endef

# Function: container build
# Usage: $(call container-build,dockerfile-path,image-name,version,context-path)
define container-build
	@echo "🔨 Building $(2)..."
	@date +"Build started at %Y-%m-%d %H:%M:%S"
	$(CONTAINER_RUNTIME) build \
		--layers \
		-f $(1) \
		-t $(PROJECT_SLUG)/$(2):$(3) \
		-t $(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/$(2):$(3) \
		--platform $(BUILD_PLATFORMS) \
		$(4)
	@date +"Build completed at %Y-%m-%d %H:%M:%S"
	@echo "✅ $(2) built"
endef

# Function: container push
# Usage: $(call container-push,image-name,version)
define container-push
	@echo "📤 Pushing $(1)..."
	$(CONTAINER_RUNTIME) push $(PUSH_FLAGS) \
		$(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/$(1):$(2)
	@echo "✅ $(1) pushed"
endef

# Check prerequisites
.PHONY: check-prerequisites
check-prerequisites:
	@echo "Checking build environment..."
	$(call check-command,uv,curl -LsSf https://astral.sh/uv/install.sh | sh)
	$(call check-command,helm,brew install helm)
	$(call check-command,yq,brew install yq)
	$(call check-command,kubectl,brew install kubectl)
	$(call check-command,kind,brew install kind)
	$(call check-command,terraform,brew install terraform)
	@if [ "$(CONTAINER_RUNTIME)" = "none" ]; then \
		echo "❌ Neither podman nor docker found"; \
		echo "   Install: brew install podman"; \
		exit 1; \
	fi
	@echo "✓ All required commands available"
	@echo "Container runtime: $(CONTAINER_RUNTIME)"
	@echo "Build version: $(VERSION)"
	@echo "Build platforms: $(BUILD_PLATFORMS)"
	@echo "Registry: $(EXTERNAL_REGISTRY)"
	@echo "✅ Environment ready"
