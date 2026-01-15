#!/usr/bin/env bash
# Deploy TinyOlly Helm chart to ArgoCD after local build
# This script updates the ArgoCD Application with the correct chart version
# and image tags, then triggers a sync
#
# Usage: ./deploy-to-argocd.sh [chart-version] [image-version]
# Example: ./deploy-to-argocd.sh 0.1.0 v2.1.9-perms

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHART_DIR="$SCRIPT_DIR/tinyolly"
ARGOCD_APP_FILE="${ARGOCD_APP_FILE:-$SCRIPT_DIR/../.kind/modules/main/argocd-applications/observability/tinyolly.yaml}"
INTERNAL_REGISTRY="docker-registry.registry.svc.cluster.local:5000"

# Get chart version from Chart.yaml or use provided version
if [ $# -ge 1 ]; then
    CHART_VERSION="$1"
    echo "Using provided chart version: $CHART_VERSION"
else
    CHART_VERSION=$(grep "^version:" "$CHART_DIR/Chart.yaml" | awk '{print $2}')
    echo "Using chart version from Chart.yaml: $CHART_VERSION"
fi

# Get image version (defaults to chart version if not provided)
if [ $# -ge 2 ]; then
    IMAGE_VERSION="$2"
    echo "Using provided image version: $IMAGE_VERSION"
else
    IMAGE_VERSION="$CHART_VERSION"
    echo "Using image version same as chart: $IMAGE_VERSION"
fi

echo ""
echo "📋 Deploying TinyOlly to ArgoCD"
echo "========================================"
echo "Chart version:  $CHART_VERSION"
echo "Image version:  $IMAGE_VERSION"
echo "Image registry: $INTERNAL_REGISTRY"
echo "ArgoCD App:     $ARGOCD_APP_FILE"
echo ""

# Check if ArgoCD Application exists
if ! kubectl get application tinyolly -n argocd &>/dev/null; then
    echo "⚠️  ArgoCD Application 'tinyolly' does not exist yet"
    echo "   It will be created by ArgoCD when it syncs the Applications"
    echo ""
fi

# Update the targetRevision in the ArgoCD Application
if [ -f "$ARGOCD_APP_FILE" ]; then
    echo "📝 Verifying targetRevision uses terraform variable..."

    # Check if targetRevision uses the variable
    # shellcheck disable=SC2016
    if grep -q 'targetRevision: \${tinyolly_chart_tag}' "$ARGOCD_APP_FILE"; then
        echo "✓ targetRevision correctly uses \${tinyolly_chart_tag} variable"
    else
        echo "⚠️  WARNING: targetRevision should use \${tinyolly_chart_tag} variable"
        echo "   Current value:"
        grep "targetRevision:" "$ARGOCD_APP_FILE"
    fi
    echo ""
fi

# Check if the Application is managed by ArgoCD
if kubectl get application tinyolly -n argocd &>/dev/null; then
    echo "🔄 Updating ArgoCD Application with image tags and chart version..."

    # Patch the Application with both chart version and image tags
    kubectl patch application tinyolly -n argocd --type=merge -p "{
      \"spec\": {
        \"source\": {
          \"targetRevision\": \"$CHART_VERSION\",
          \"helm\": {
            \"valuesObject\": {
              \"frontend\": {
                \"image\": {
                  \"repository\": \"$INTERNAL_REGISTRY/tinyolly/tinyolly\",
                  \"tag\": \"$IMAGE_VERSION\"
                }
              },
              \"webui\": {
                \"image\": {
                  \"repository\": \"$INTERNAL_REGISTRY/tinyolly/tinyolly-ui\",
                  \"tag\": \"$IMAGE_VERSION\"
                }
              },
              \"opampServer\": {
                \"image\": {
                  \"repository\": \"$INTERNAL_REGISTRY/tinyolly/opamp-server\",
                  \"tag\": \"$IMAGE_VERSION\"
                }
              },
              \"otlpReceiver\": {
                \"image\": {
                  \"repository\": \"$INTERNAL_REGISTRY/tinyolly/tinyolly\",
                  \"tag\": \"$IMAGE_VERSION\"
                },
                \"env\": [
                  {
                    \"name\": \"MODE\",
                    \"value\": \"receiver\"
                  }
                ]
              },
              \"otelCollector\": {
                \"enabled\": true
              },
              \"instrumentation\": {
                \"enabled\": true
              }
            }
          }
        }
      }
    }"

    echo "✓ Patched ArgoCD Application"
    echo ""

    # Trigger a hard refresh and sync
    echo "🔄 Triggering ArgoCD sync..."
    argocd app sync tinyolly --force --async 2>/dev/null || {
        echo "⚠️  argocd CLI not available, using kubectl instead"
        kubectl patch application tinyolly -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
    }

    echo ""
    echo "✅ Deployment initiated!"
    echo ""
    echo "To watch the sync progress:"
    echo "  kubectl get application tinyolly -n argocd -w"
    echo ""
    echo "To view sync status:"
    echo "  argocd app get tinyolly"
    echo ""
    echo "To view logs:"
    echo "  kubectl logs -n tinyolly -l app.kubernetes.io/component=webui -f"
else
    echo "⚠️  ArgoCD Application not yet created in cluster"
    echo "   Commit the changes to $ARGOCD_APP_FILE"
    echo "   ArgoCD will create the Application on next sync"
    echo ""
fi

echo "📋 Image versions being deployed:"
echo "  • Frontend (API):  $INTERNAL_REGISTRY/tinyolly/tinyolly:$IMAGE_VERSION"
echo "  • WebUI (nginx):   $INTERNAL_REGISTRY/tinyolly/tinyolly-ui:$IMAGE_VERSION"
echo "  • OpAMP Server:    $INTERNAL_REGISTRY/tinyolly/opamp-server:$IMAGE_VERSION"
echo "  • OTLP Receiver:   $INTERNAL_REGISTRY/tinyolly/tinyolly:$IMAGE_VERSION (MODE=receiver)"
echo ""
