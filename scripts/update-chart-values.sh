#!/bin/bash
# Update chart values.yaml with new component versions
# Usage: update-chart-values.sh <component> <version>

set -e

COMPONENT=$1
VERSION=$2

if [ -z "$COMPONENT" ] || [ -z "$VERSION" ]; then
    echo "Usage: update-chart-values.sh <component> <version>"
    exit 1
fi

# Ensure yq is available
if ! command -v yq &> /dev/null; then
    echo "Error: yq is required but not installed"
    exit 1
fi

# Format version with 'v' prefix if not already present
if [[ ! "$VERSION" =~ ^v ]]; then
    VERSION="v${VERSION}"
fi

case "$COMPONENT" in
    ollyscale)
        echo "Updating ollyscale image tag to $VERSION in charts/ollyscale/values.yaml"
        yq eval ".api.image.tag = \"$VERSION\"" -i charts/ollyscale/values.yaml
        ;;
    web-ui)
        echo "Updating web-ui image tag to $VERSION in charts/ollyscale/values.yaml"
        yq eval ".webui.image.tag = \"$VERSION\"" -i charts/ollyscale/values.yaml
        ;;
    opamp-server)
        echo "Updating opamp-server image tag to $VERSION in charts/ollyscale/values.yaml"
        yq eval ".opampServer.image.tag = \"$VERSION\"" -i charts/ollyscale/values.yaml
        ;;
    demo)
        echo "Updating demo image tags to $VERSION in charts/ollyscale-demos/values.yaml"
        yq eval ".frontend.image.tag = \"$VERSION\"" -i charts/ollyscale-demos/values.yaml
        yq eval ".backend.image.tag = \"$VERSION\"" -i charts/ollyscale-demos/values.yaml
        ;;
    demo-otel-agent)
        echo "Updating demo-otel-agent image tag to $VERSION in charts/ollyscale-otel-agent/values.yaml"
        yq eval ".agent.image.tag = \"$VERSION\"" -i charts/ollyscale-otel-agent/values.yaml
        ;;
    *)
        echo "Error: Unknown component '$COMPONENT'"
        exit 1
        ;;
esac

echo "✓ Successfully updated $COMPONENT to $VERSION"
