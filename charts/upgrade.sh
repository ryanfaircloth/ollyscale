#!/usr/bin/env bash
# Upgrade ollyScale Helm Chart

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHART_DIR="${SCRIPT_DIR}/ollyscale"

# Default values
NAMESPACE="${NAMESPACE:-ollyscale}"
RELEASE_NAME="${RELEASE_NAME:-ollyscale}"
VALUES_FILE="${VALUES_FILE:-}"

echo "⬆️  Upgrading ollyScale Helm Chart..."
echo "   Release:   ${RELEASE_NAME}"
echo "   Namespace: ${NAMESPACE}"
if [ -n "${VALUES_FILE}" ]; then
    echo "   Values:    ${VALUES_FILE}"
fi
echo ""

# Build the helm command
HELM_CMD=(helm upgrade "${RELEASE_NAME}" "${CHART_DIR}" \
    --namespace "${NAMESPACE}" \
    --install)

# Add values file if specified
if [ -n "${VALUES_FILE}" ]; then
    HELM_CMD+=(--values "${VALUES_FILE}")
fi

# Add any additional arguments passed to the script
HELM_CMD+=("$@")

# Execute the command
echo "Executing: ${HELM_CMD[*]}"
echo ""
"${HELM_CMD[@]}"

echo ""
echo "✅ Upgrade complete!"
echo ""
echo "To check the status:"
echo "  helm status ${RELEASE_NAME} -n ${NAMESPACE}"
echo ""
echo "To view the pods:"
echo "  kubectl get pods -n ${NAMESPACE}"
