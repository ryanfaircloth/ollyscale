# =============================================================================
# config.mk - Makefile Configuration Variables
# =============================================================================
# Lazy evaluation (=) allows variables to reference other variables and
# evaluate at use-time, fixing Taskfile's eager evaluation issues.

# Project configuration
PROJECT_SLUG = $(shell echo "$${PROJECT_SLUG:-ollyscale}")
GH_ORG = $(shell echo "$${GH_ORG:-ryanfaircloth}")

# Container runtime detection
CONTAINER_RUNTIME = $(shell \
	if command -v podman >/dev/null 2>&1; then \
		echo "podman"; \
	elif command -v docker >/dev/null 2>&1; then \
		echo "docker"; \
	else \
		echo "none"; \
	fi)

# Registry configuration
REGISTRY = ghcr.io
REGISTRY_ORG = $(GH_ORG)
IMAGE_PREFIX = $(REGISTRY)/$(REGISTRY_ORG)/$(PROJECT_SLUG)

# Local development registry (KIND cluster)
EXTERNAL_REGISTRY = registry.ollyscale.test:49443
INTERNAL_REGISTRY = docker-registry.registry.svc.cluster.local:5000
EXTERNAL_CHART_REGISTRY = $(EXTERNAL_REGISTRY)/$(PROJECT_SLUG)/charts
INTERNAL_CHART_REGISTRY = $(INTERNAL_REGISTRY)/$(PROJECT_SLUG)/charts

# Build configuration
# VERSION: Base version for builds
# - CI releases: Set via $VERSION environment variable (release-please)
# - Local dev: Generated with timestamp when content changes
# - Component Makefiles override this based on content hash checks
VERSION = $(shell echo "$${VERSION:-0.0.0-dev.$$(date +%s)}")

# Kubernetes
CLUSTER_NAME = $(PROJECT_SLUG)
NAMESPACE = ollyscale

# Build directory structure (absolute path from workspace root)
ROOT_DIR := $(shell pwd | sed 's|/apps/.*||; s|/charts/.*||')
BUILD_DIR = $(ROOT_DIR)/.build
VERSION_DIR = $(BUILD_DIR)/versions
PACKAGE_DIR = $(BUILD_DIR)/packages

# Container-specific flags
PODMAN_FLAGS = --tls-verify=false
DOCKER_FLAGS =

PUSH_FLAGS = $(shell \
	if [ "$(CONTAINER_RUNTIME)" = "podman" ]; then \
		echo "$(PODMAN_FLAGS)"; \
	else \
		echo "$(DOCKER_FLAGS)"; \
	fi)

# Build platform (local vs CI)
BUILD_PLATFORMS = $(shell \
	if [ "$${CI:-false}" = "true" ]; then \
		echo "linux/amd64,linux/arm64"; \
	else \
		uname -m | sed 's/x86_64/linux\/amd64/; s/arm64/linux\/arm64/; s/aarch64/linux\/arm64/'; \
	fi)

# Environment variables
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
