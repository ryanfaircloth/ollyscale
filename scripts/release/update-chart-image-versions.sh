#!/usr/bin/env bash
# Update Helm chart values.yaml with latest container versions
# Used by release-please workflow and manual updates
# Usage: ./update-chart-image-versions.sh <chart-name>

set -euo pipefail

CHART_NAME=${1:-}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../.."

if [ -z "$CHART_NAME" ]; then
    echo "Usage: $0 <chart-name>"
    echo "Example: $0 tinyolly"
    exit 1
fi

CHART_PATH="$REPO_ROOT/charts/$CHART_NAME"

if [ ! -d "$CHART_PATH" ]; then
    echo "❌ Chart not found: $CHART_PATH"
    exit 1
fi

echo "Updating image versions in $CHART_NAME chart..."

case "$CHART_NAME" in
    "tinyolly")
        # Update tinyolly and opamp-server image versions
        if [ -f "$REPO_ROOT/apps/tinyolly/VERSION" ]; then
            TINYOLLY_VERSION=$(cat "$REPO_ROOT/apps/tinyolly/VERSION")
            echo "  tinyolly: v$TINYOLLY_VERSION"

            # Update values.yaml
            sed -i.bak "s|tag: .*# tinyolly|tag: \"v${TINYOLLY_VERSION}\" # tinyolly|" "$CHART_PATH/values.yaml"

            # Update Chart.yaml appVersion
            sed -i.bak "s|^appVersion: .*|appVersion: \"v${TINYOLLY_VERSION}\"|" "$CHART_PATH/Chart.yaml"
        fi

        if [ -f "$REPO_ROOT/apps/opamp-server/VERSION" ]; then
            OPAMP_VERSION=$(cat "$REPO_ROOT/apps/opamp-server/VERSION")
            echo "  opamp-server: v$OPAMP_VERSION"
            sed -i.bak "s|tag: .*# opamp-server|tag: \"v${OPAMP_VERSION}\" # opamp-server|" "$CHART_PATH/values.yaml"
        fi
        ;;

    "tinyolly-demos")
        if [ -f "$REPO_ROOT/apps/demo/VERSION" ]; then
            DEMO_VERSION=$(cat "$REPO_ROOT/apps/demo/VERSION")
            echo "  demo: v$DEMO_VERSION"
            sed -i.bak "s|tag: .*# demo|tag: \"v${DEMO_VERSION}\" # demo|" "$CHART_PATH/values.yaml"
            sed -i.bak "s|^appVersion: .*|appVersion: \"v${DEMO_VERSION}\"|" "$CHART_PATH/Chart.yaml"
        fi
        ;;

    "tinyolly-demo-otel-agent")
        if [ -f "$REPO_ROOT/apps/demo-otel-agent/VERSION" ]; then
            AI_VERSION=$(cat "$REPO_ROOT/apps/demo-otel-agent/VERSION")
            echo "  demo-otel-agent: v$AI_VERSION"
            sed -i.bak "s|tag: .*# demo-otel-agent|tag: \"v${AI_VERSION}\" # demo-otel-agent|" "$CHART_PATH/values.yaml"
            sed -i.bak "s|^appVersion: .*|appVersion: \"v${AI_VERSION}\"|" "$CHART_PATH/Chart.yaml"
        fi
        ;;

    *)
        echo "❌ Unknown chart: $CHART_NAME"
        exit 1
        ;;
esac

# Clean up backup files
rm -f "$CHART_PATH/values.yaml.bak" "$CHART_PATH/Chart.yaml.bak"

echo "✅ Updated $CHART_NAME chart with latest image versions"
