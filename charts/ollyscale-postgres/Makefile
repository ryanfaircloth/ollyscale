# =============================================================================
# charts/ollyscale-postgres/Makefile - PostgreSQL Chart
# =============================================================================

# Include shared configuration and functions
include ../../config.mk
include ../../build.mk

CHART_NAME := ollyscale-postgres
CHART_DIR := .

# Source files that trigger rebuild when changed
CONTENT_SOURCES := Chart.yaml values.yaml templates/ ct.yaml

.PHONY: test
test: ## Test postgres chart with helm lint
	@echo "🧪 Testing postgres chart with helm lint..."
	@helm lint .
	@if command -v ct >/dev/null 2>&1 && command -v yamllint >/dev/null 2>&1; then \
		echo "🧪 Running chart-testing lint..."; \
		cd .. && ct lint --config $(CHART_NAME)/ct.yaml --charts $(CHART_NAME); \
	elif command -v ct >/dev/null 2>&1; then \
		echo "⚠️  yamllint not found - skipping chart-testing"; \
		echo "   Install with: brew install yamllint (macOS) or pip install yamllint"; \
	else \
		echo "ℹ️  chart-testing (ct) not found - helm lint only"; \
		echo "   Install with: brew install chart-testing (optional)"; \
	fi
	@echo "✅ Postgres chart tests passed"

.PHONY: build
build: test ensure-build-dirs ## Build postgres chart
	@CHANGED=$(call sources-changed,chart-$(CHART_NAME),$(CONTENT_SOURCES)); \
	if [ "$$CHANGED" = "no" ]; then \
		CHART_VERSION=$(call read-version,chart-$(CHART_NAME)); \
		echo "⏭️  Skipping chart $(CHART_NAME): no changes detected (version $$CHART_VERSION)"; \
	else \
		CHART_VERSION=$(VERSION); \
		echo "📦 Packaging chart $(CHART_NAME) version $$CHART_VERSION"; \
		helm package $(CHART_DIR) \
			--version $$CHART_VERSION \
			--destination $(PACKAGE_DIR); \
		echo "✅ Chart $(CHART_NAME) packaged"; \
		$(call write-version,chart-$(CHART_NAME),$$CHART_VERSION); \
	fi

.PHONY: push
push: ## Push postgres chart
	@CHART_VERSION=$$(cat $(VERSION_DIR)/chart-$(CHART_NAME) 2>/dev/null || echo "$(VERSION)"); \
	echo "📤 Pushing $(CHART_NAME) to local registry..."; \
	helm push $(PACKAGE_DIR)/$(CHART_NAME)-$$CHART_VERSION.tgz \
		oci://$(EXTERNAL_CHART_REGISTRY) \
		--insecure-skip-tls-verify; \
	echo "✅ Chart pushed: $(CHART_NAME)-$$CHART_VERSION"; \
	echo "📝 Updating .kind/postgres.auto.tfvars..."; \
	printf 'postgres_chart_tag = "%s"\n' "$$CHART_VERSION" > ../../.kind/postgres.auto.tfvars; \
	echo "✅ Auto vars updated"
