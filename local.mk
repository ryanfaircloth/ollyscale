# =============================================================================
# local.mk - Local Development Build Logic
# =============================================================================
# Included when CI is not set

# Chart packaging for local development
# Use helm flags to set version without modifying Chart.yaml
define helm-package-local
	@echo "📦 Packaging $(1) (local mode)..."
	@echo "Chart version: $(2)"
	helm package $(1) --destination $(PACKAGE_DIR) --version "$(2)" $(3)
	@echo "✅ Chart packaged: $(1)-$(2).tgz"
endef

# Helm push with insecure flag for local registry
define helm-push-local
	@echo "📤 Pushing $(1) to local registry..."
	helm push $(PACKAGE_DIR)/$(1)-$(2).tgz \
		oci://$(EXTERNAL_CHART_REGISTRY) \
		--insecure-skip-tls-verify
	@echo "✅ Chart pushed: $(1)-$(2)"
endef

# Container push flags for local registry
HELM_PUSH_CMD = $(call helm-push-local,$(1),$(2))

# Local registry is insecure
HELM_FLAGS = --insecure-skip-tls-verify

# Version generation for local builds
define generate-version
0.0.0-dev.$$(date +%s)
endef
