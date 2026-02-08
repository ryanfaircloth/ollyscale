# =============================================================================
# charts/ollyscale-demos/Makefile - Demos Chart
# =============================================================================

# Include shared configuration and functions
include ../../config.mk
include ../../build.mk

CHART_NAME := ollyscale-demos
CHART_DIR := .

# Source files that trigger rebuild when changed
CONTENT_SOURCES := Chart.yaml values.yaml templates/ $(VERSION_DIR)/demo

# Prerequisites: Require demo image version file
$(VERSION_DIR)/demo:
	@echo "❌ Demo image not built yet"
	@exit 1

.PHONY: build
build: $(VERSION_DIR)/demo ensure-build-dirs ## Build demos chart
	@CHANGED=$(call sources-changed,chart-$(CHART_NAME),$(CONTENT_SOURCES)); \
	if [ "$$CHANGED" = "no" ]; then \
		CHART_VERSION=$(call read-version,chart-$(CHART_NAME)); \
		echo "⏭️  Skipping chart $(CHART_NAME): no changes detected (version $$CHART_VERSION)"; \
	else \
		VERSION_DEMO=$$(cat $(VERSION_DIR)/demo); \
		CHART_VERSION=$(VERSION); \
		echo "📦 Packaging chart $(CHART_NAME) version $$CHART_VERSION"; \
		helm package $(CHART_DIR) \
			--version $$CHART_VERSION \
			--app-version $$VERSION_DEMO \
			--destination $(PACKAGE_DIR); \
		echo "✅ Chart $(CHART_NAME) packaged"; \
		$(call write-version,chart-$(CHART_NAME),$$CHART_VERSION); \
	fi

.PHONY: push
push: ## Push demos chart
	@CHART_VERSION=$$(cat $(VERSION_DIR)/chart-$(CHART_NAME) 2>/dev/null || echo "$(VERSION)"); \
	echo "📤 Pushing $(CHART_NAME) to local registry..."; \
	helm push $(PACKAGE_DIR)/$(CHART_NAME)-$$CHART_VERSION.tgz \
		oci://$(EXTERNAL_CHART_REGISTRY) \
		--insecure-skip-tls-verify; \
	echo "✅ Chart pushed: $(CHART_NAME)-$$CHART_VERSION"
