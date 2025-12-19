#!/bin/bash
set -e

# TinyOlly Release Script
# Creates git tag, pushes to remote, and builds/pushes Docker images
#
# Usage: ./release.sh <version>
# Example: ./release.sh v2.0.0

VERSION=${1:-""}

if [ -z "$VERSION" ]; then
    echo "Error: Version is required"
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh v2.0.0"
    exit 1
fi

# Validate version format
if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format vX.Y.Z (e.g., v2.0.0)"
    exit 1
fi

# Extract version without 'v' prefix for comparison
VERSION_NUM=${VERSION#v}

echo "=========================================="
echo "TinyOlly Release: $VERSION"
echo "=========================================="
echo ""

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: You have uncommitted changes"
    echo ""
    git status --short
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "Error: Tag $VERSION already exists"
    echo "Use 'git tag -d $VERSION' to delete it first if you want to re-release"
    exit 1
fi

# Check release notes exist
RELEASE_NOTES="RELEASE-NOTES-$VERSION.md"
if [ ! -f "$RELEASE_NOTES" ]; then
    echo "Warning: Release notes file '$RELEASE_NOTES' not found"
    read -p "Continue without release notes? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Check version in main.py matches
MAIN_PY_VERSION=$(grep -o 'version="[^"]*"' docker/apps/tinyolly-ui/app/main.py | head -1 | sed 's/version="//;s/"//')
if [ "$MAIN_PY_VERSION" != "$VERSION_NUM" ]; then
    echo "Warning: Version in docker/apps/tinyolly-ui/app/main.py is '$MAIN_PY_VERSION'"
    echo "         but you're releasing '$VERSION_NUM'"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo "Pre-flight checks passed!"
echo ""

# Step 1: Create annotated git tag
echo "----------------------------------------"
echo "Step 1: Creating git tag $VERSION"
echo "----------------------------------------"
if [ -f "$RELEASE_NOTES" ]; then
    # Use release notes as tag message
    git tag -a "$VERSION" -m "Release $VERSION" -m "$(cat $RELEASE_NOTES)"
else
    git tag -a "$VERSION" -m "Release $VERSION"
fi
echo "Created tag $VERSION"
echo ""

# Step 2: Push tag to remote
echo "----------------------------------------"
echo "Step 2: Pushing tag to remote"
echo "----------------------------------------"
read -p "Push tag $VERSION to origin? [Y/n] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Skipping push. Run 'git push origin $VERSION' later."
else
    git push origin "$VERSION"
    echo "Pushed tag $VERSION to origin"
fi
echo ""

# Step 3: Build and push Docker images
echo "----------------------------------------"
echo "Step 3: Build and push Docker images"
echo "----------------------------------------"
read -p "Build and push Docker images to Docker Hub? [Y/n] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Skipping Docker build. Run the following later:"
    echo "  cd docker && ./build-and-push-images.sh $VERSION"
    echo "  cd docker-demo && ./build-and-push-demo-images.sh $VERSION"
    echo "  cd docker-ai-agent-demo && ./build-and-push-ai-demo-image.sh $VERSION"
else
    echo "Building core images..."
    (cd docker && ./build-and-push-images.sh "$VERSION")
    echo ""

    read -p "Build and push demo images? [Y/n] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "Building demo images..."
        (cd docker-demo && ./build-and-push-demo-images.sh "$VERSION")
        echo ""

        echo "Building AI demo image..."
        (cd docker-ai-agent-demo && ./build-and-push-ai-demo-image.sh "$VERSION")
    fi
fi
echo ""

# Step 4: Deploy documentation (optional)
echo "----------------------------------------"
echo "Step 4: Deploy documentation"
echo "----------------------------------------"
read -p "Deploy documentation to GitHub Pages? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./mkdocs-deploy.sh
    echo "Documentation deployed"
else
    echo "Skipping documentation deployment"
fi
echo ""

echo "=========================================="
echo "Release $VERSION Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - Git tag: $VERSION"
echo "  - Docker images: tinyolly/*:$VERSION"
if [ -f "$RELEASE_NOTES" ]; then
    echo "  - Release notes: $RELEASE_NOTES"
fi
echo ""
echo "Next steps:"
echo "  1. Verify images: docker pull tinyolly/ui:$VERSION"
echo "  2. Test deployment: cd docker && ./01-start-core.sh"
echo "  3. Create GitHub Release at:"
echo "     https://github.com/tinyolly/tinyolly/releases/new?tag=$VERSION"
echo ""
