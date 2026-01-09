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

# Build TinyOlly core images locally (multi-arch)
# Usage: ./build-core.sh [version]
# Example: ./build-core.sh v2.1.0
#
# NOTE: Uses --no-cache for fresh builds. Does NOT push to Docker Hub.
# To push, run: ./03-push-core.sh [version]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../../docker"

VERSION=${1:-"latest"}
CONTAINER_REGISTRY=${CONTAINER_REGISTRY:-"tinyolly"}  # Default to Docker Hub (tinyolly), can be overridden with ghcr.io/ryanfaircloth
PLATFORMS="linux/amd64,linux/arm64"

echo "=========================================="
echo "TinyOlly Core - Build (No Push)"
echo "=========================================="
echo "Registry: $CONTAINER_REGISTRY"
echo "Version: $VERSION"
echo "Platforms: $PLATFORMS"
echo "Cache: disabled (fresh build)"
echo ""

# Ensure buildx builder exists and is active
echo "Setting up Docker Buildx..."
docker buildx create --name tinyolly-builder --use 2>/dev/null || docker buildx use tinyolly-builder
docker buildx inspect --bootstrap
echo ""

echo "Building images in dependency order..."
echo ""

# Image 1: Python base (no dependencies)
echo "----------------------------------------"
echo "Building python-base..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  --no-cache \
  -f dockerfiles/Dockerfile.tinyolly-python-base \
  -t $CONTAINER_REGISTRY/python-base:latest \
  -t $CONTAINER_REGISTRY/python-base:$VERSION \
  --load .
echo "✓ Built $CONTAINER_REGISTRY/python-base:$VERSION"
echo ""

# Image 2: OTLP Receiver (depends on python-base)
echo "----------------------------------------"
echo "Building otlp-receiver..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  --no-cache \
  -f dockerfiles/Dockerfile.tinyolly-otlp-receiver \
  --build-arg APP_DIR=tinyolly-otlp-receiver \
  -t $CONTAINER_REGISTRY/otlp-receiver:latest \
  -t $CONTAINER_REGISTRY/otlp-receiver:$VERSION \
  --load .
echo "✓ Built $CONTAINER_REGISTRY/otlp-receiver:$VERSION"
echo ""

# Image 3: UI (depends on python-base)
echo "----------------------------------------"
echo "Building ui..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  --no-cache \
  -f dockerfiles/Dockerfile.tinyolly-ui \
  --build-arg APP_DIR=tinyolly-ui \
  -t $CONTAINER_REGISTRY/ui:latest \
  -t $CONTAINER_REGISTRY/ui:$VERSION \
  --load .
echo "✓ Built $CONTAINER_REGISTRY/ui:$VERSION"
echo ""

# Image 4: OpAMP Server (independent Go build)
echo "----------------------------------------"
echo "Building opamp-server..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  --no-cache \
  -f dockerfiles/Dockerfile.tinyolly-opamp-server \
  -t $CONTAINER_REGISTRY/opamp-server:latest \
  -t $CONTAINER_REGISTRY/opamp-server:$VERSION \
  --load .
echo "✓ Built $CONTAINER_REGISTRY/opamp-server:$VERSION"
echo ""

# Image 5: OTel Supervisor (independent)
echo "----------------------------------------"
echo "Building otel-supervisor..."
echo "----------------------------------------"
docker buildx build --platform $PLATFORMS \
  --no-cache \
  -f dockerfiles/Dockerfile.otel-supervisor \
  -t $CONTAINER_REGISTRY/otel-supervisor:latest \
  -t $CONTAINER_REGISTRY/otel-supervisor:$VERSION \
  --load .
echo "✓ Built $CONTAINER_REGISTRY/otel-supervisor:$VERSION"
echo ""

echo "=========================================="
echo "✓ All core images built locally!"
echo "=========================================="
echo ""
echo "Built images:"
echo "  - $CONTAINER_REGISTRY/python-base:$VERSION"
echo "  - $CONTAINER_REGISTRY/otlp-receiver:$VERSION"
echo "  - $CONTAINER_REGISTRY/ui:$VERSION"
echo "  - $CONTAINER_REGISTRY/opamp-server:$VERSION"
echo "  - $CONTAINER_REGISTRY/otel-supervisor:$VERSION"
echo ""
echo "Next step - push to registry:"
echo "  ./03-push-core.sh $VERSION"
echo ""
