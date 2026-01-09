#!/bin/bash

# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

set -e

# TinyOlly Release Script
# Creates git tag, pushes to remote, and creates GitHub release
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

echo "=========================================="
echo "TinyOlly Release: $VERSION"
echo "=========================================="
echo ""

# Check if tag already exists locally
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "Tag $VERSION already exists locally"
else
    # Check release notes exist
    RELEASE_NOTES="release-notes/RELEASE-NOTES-$VERSION.md"
    if [ ! -f "$RELEASE_NOTES" ]; then
        echo "Error: Release notes file '$RELEASE_NOTES' not found"
        exit 1
    fi

    echo "Creating git tag $VERSION..."
    git tag -a "$VERSION" -m "Release $VERSION"
    echo "Created tag $VERSION"
fi
echo ""

# Push tag to remote
echo "Pushing tag to origin..."
git push origin "$VERSION"
echo "Pushed tag $VERSION"
echo ""

# Create GitHub release
RELEASE_NOTES="release-notes/RELEASE-NOTES-$VERSION.md"
if [ -f "$RELEASE_NOTES" ]; then
    echo "Creating GitHub release..."
    if gh release view "$VERSION" >/dev/null 2>&1; then
        echo "GitHub release $VERSION already exists"
    else
        gh release create "$VERSION" --title "TinyOlly $VERSION" --notes-file "$RELEASE_NOTES"
        echo "Created GitHub release $VERSION"
    fi
else
    echo "Warning: No release notes found at $RELEASE_NOTES"
    echo "Creating GitHub release without notes..."
    if gh release view "$VERSION" >/dev/null 2>&1; then
        echo "GitHub release $VERSION already exists"
    else
        gh release create "$VERSION" --title "TinyOlly $VERSION" --generate-notes
        echo "Created GitHub release $VERSION"
    fi
fi
echo ""

echo "=========================================="
echo "Release $VERSION Complete!"
echo "=========================================="
echo ""
echo "View release: https://github.com/tinyolly/tinyolly/releases/tag/$VERSION"
echo ""
