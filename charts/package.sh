#!/usr/bin/env bash
# Package ollyScale Helm Chart

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHART_DIR="${SCRIPT_DIR}/ollyscale"

echo "📦 Packaging ollyScale Helm Chart..."

# Lint the chart first
echo "🔍 Linting chart..."
helm lint "${CHART_DIR}"

# Update dependencies if any
if [ -f "${CHART_DIR}/Chart.lock" ]; then
    echo "📥 Updating dependencies..."
    helm dependency update "${CHART_DIR}"
fi

# Package the chart
echo "📦 Creating chart package..."
helm package "${CHART_DIR}" -d "${SCRIPT_DIR}"

echo "✅ Chart packaged successfully!"
echo ""
echo "Generated files:"
ls -lh "${SCRIPT_DIR}"/*.tgz 2>/dev/null || echo "No .tgz files found"

echo ""
echo "To push to OCI registry, run:"
echo "  ./push-oci.sh <registry-url>"
echo ""
echo "Example:"
echo "  ./push-oci.sh ghcr.io/ryanfaircloth/ollyscale/charts"
