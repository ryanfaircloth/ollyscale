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

# Build ollyScale AI Agent demo image locally (multi-arch)
# Usage: ./build-ai-demo.sh [version]
# Example: ./build-ai-demo.sh v2.1.0
#
# NOTE: Uses --no-cache for fresh builds. Does NOT push to Docker Hub.
# To push, run: ./03-push-ai-demo.sh [version]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../../docker-ai-agent-demo"

VERSION=${1:-"latest"}
CONTAINER_REGISTRY=${CONTAINER_REGISTRY:-"ghcr.io/ryanfaircloth/ollyscale"}
PLATFORMS="linux/amd64,linux/arm64"

echo "=========================================="
echo "ollyScale AI Demo - Build (No Push)"
echo "=========================================="
echo "Registry: $CONTAINER_REGISTRY"
echo "Version: $VERSION"
echo "Platforms: $PLATFORMS"
echo "Cache: disabled (fresh build)"
echo ""

# Ensure buildx builder exists
echo "Setting up Docker Buildx..."
docker buildx create --name ollyscale-builder --use 2>/dev/null || docker buildx use ollyscale-builder
docker buildx inspect --bootstrap
echo ""

# Build ai-agent-demo
echo "----------------------------------------"
echo "Building ai-agent-demo..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  --no-cache \
  -f Dockerfile \
  -t $CONTAINER_REGISTRY/ai-agent-demo:latest \
  -t $CONTAINER_REGISTRY/ai-agent-demo:$VERSION \
  $BUILD_ACTION .
echo "✓ Built $CONTAINER_REGISTRY/ai-agent-demo:$VERSION"
echo ""

echo "=========================================="
echo "✓ AI demo image built locally!"
echo "=========================================="
echo ""
echo "Built image:"
echo "  - $CONTAINER_REGISTRY/ai-agent-demo:$VERSION"
echo ""
echo "Next step - push to registry:"
echo "  ./03-push-ai-demo.sh $VERSION"
echo ""
