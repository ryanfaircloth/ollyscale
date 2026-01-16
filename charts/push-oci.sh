#!/usr/bin/env bash
# Push ollyScale Helm Chart to OCI Registry

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if registry URL is provided
if [ $# -eq 0 ]; then
    echo "❌ Error: Registry URL is required"
    echo ""
    echo "Usage: $0 <registry-url> [chart-version]"
    echo ""
    echo "Examples:"
    echo "  $0 ghcr.io/ryanfaircloth/ollyscale/charts"
    echo "  $0 ghcr.io/ryanfaircloth/ollyscale/charts 0.1.0"
    echo "  $0 registry.ollyscale.test:49443/ollyscale/charts"
    exit 1
fi

REGISTRY_URL="$1"
CHART_VERSION="${2:-}"

# Find the chart package
if [ -n "${CHART_VERSION}" ]; then
    CHART_PACKAGE="${SCRIPT_DIR}/ollyscale-${CHART_VERSION}.tgz"
else
    # Get the latest packaged chart
    CHART_PACKAGE=$(ls -t "${SCRIPT_DIR}"/ollyscale-*.tgz 2>/dev/null | head -1)
fi

if [ ! -f "${CHART_PACKAGE}" ]; then
    echo "❌ Error: Chart package not found!"
    echo ""
    echo "Please run './package.sh' first to create the chart package."
    exit 1
fi

PACKAGE_FILENAME="$(basename "${CHART_PACKAGE}")"
CHART_VERSION_DISPLAY="${PACKAGE_FILENAME#ollyscale-}"
CHART_VERSION_DISPLAY="${CHART_VERSION_DISPLAY%.tgz}"

echo "🚀 Pushing ollyScale Helm Chart to OCI Registry..."
echo "   Registry: ${REGISTRY_URL}"
echo "   Package:  ${PACKAGE_FILENAME}"
echo ""

# Check if already logged in
if ! helm registry login "${REGISTRY_URL%%/*}" --help &>/dev/null; then
    echo "⚠️  Warning: Unable to verify registry login"
    echo "   You may need to login first:"
    echo "   helm registry login ${REGISTRY_URL%%/*} -u <username>"
    echo ""
fi

# Push to OCI registry
echo "📤 Pushing chart..."
helm push "${CHART_PACKAGE}" "oci://${REGISTRY_URL}" --insecure-skip-tls-verify

echo ""
echo "✅ Chart pushed successfully!"
echo ""
cat <<EOF
To install from OCI registry, run:
    helm install ollyscale oci://${REGISTRY_URL}/ollyscale \\
        --version ${CHART_VERSION_DISPLAY} \\
        --namespace ollyscale \\
        --create-namespace
EOF
