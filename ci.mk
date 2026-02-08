# =============================================================================
# ci.mk - CI Build Logic
# =============================================================================
# Included when CI is set

# Chart packaging for CI
# release-please has already updated Chart.yaml, just package it
define helm-package-ci
	@echo "📦 Packaging $(1) (CI mode)..."
	@helm package $(1) --destination $(PACKAGE_DIR)
	@CHART_VERSION=$$(yq eval '.version' $(1)/Chart.yaml) && \
	echo "Chart version: $$CHART_VERSION" && \
	echo "$$CHART_VERSION" > $(VERSION_DIR)/chart-$(1)
	@echo "✅ Chart packaged: $(1)"
endef

# Helm push for CI (includes GHCR)
define helm-push-ci
	@CHART_VERSION=$$(cat $(VERSION_DIR)/chart-$(1) 2>/dev/null || yq eval '.version' charts/$(1)/Chart.yaml) && \
	echo "📤 Pushing $(1)-$$CHART_VERSION to registries..." && \
	helm push $(PACKAGE_DIR)/$(1)-$$CHART_VERSION.tgz \
		oci://$(EXTERNAL_CHART_REGISTRY) \
		--insecure-skip-tls-verify && \
	echo "📤 Pushing to GitHub Container Registry..." && \
	helm push $(PACKAGE_DIR)/$(1)-$$CHART_VERSION.tgz \
		oci://$(REGISTRY)/$(REGISTRY_ORG)/$(PROJECT_SLUG)/charts && \
	echo "✅ Chart pushed to both registries: $(1)-$$CHART_VERSION"
endef

# Container push includes GHCR in CI
define container-push-ci
	@echo "📤 Pushing $(1) to registries..."
	$(CONTAINER_RUNTIME) push $(PUSH_FLAGS) \
		$(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/$(1):$(2)
	@echo "📤 Pushing to GitHub Container Registry..."
	docker tag $(PROJECT_SLUG)/$(1):$(2) $(IMAGE_PREFIX)/$(1):$(2)
	docker push $(IMAGE_PREFIX)/$(1):$(2)
	@echo "✅ $(1) pushed to both registries"
endef

HELM_PUSH_CMD = $(call helm-push-ci,$(1),$(2))

# CI uses secure connections
HELM_FLAGS =

# Version generation for CI (from environment)
define generate-version
$${VERSION}
endef

# Check if chart version already exists in GHCR
define check-chart-pushed
	@CHART_VERSION=$$(yq eval '.version' charts/$(1)/Chart.yaml) && \
	echo "Checking if $(1):$$CHART_VERSION exists in GHCR..." && \
	if helm pull oci://$(REGISTRY)/$(REGISTRY_ORG)/$(PROJECT_SLUG)/charts/$(1) \
		--version $$CHART_VERSION \
		--destination /tmp 2>&1 | grep -q "Error"; then \
		echo "Version $$CHART_VERSION not found - OK to push"; \
		exit 1; \
	else \
		echo "⚠️  Version $$CHART_VERSION already exists - skipping"; \
		rm -f /tmp/$(1)-$$CHART_VERSION.tgz; \
		exit 0; \
	fi
endef
