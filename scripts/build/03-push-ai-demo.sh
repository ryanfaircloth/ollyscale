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

# Push ollyScale AI Agent demo image to container registry
# Usage: ./push-ai-demo.sh [version]
# Example: ./push-ai-demo.sh v2.1.0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VERSION=${1:-"latest"}
CONTAINER_REGISTRY=${CONTAINER_REGISTRY:-"ghcr.io/ryanfaircloth/ollyscale"}

echo "=========================================="
echo "ollyScale AI Demo - Push to Container Registry"
echo "=========================================="
echo "Registry: $CONTAINER_REGISTRY"
echo "Version: $VERSION"
echo ""

echo "Pushing $CONTAINER_REGISTRY/ai-agent-demo:$VERSION..."
docker push $CONTAINER_REGISTRY/ai-agent-demo:$VERSION
docker push $CONTAINER_REGISTRY/ai-agent-demo:latest
echo "✓ Pushed $CONTAINER_REGISTRY/ai-agent-demo:$VERSION"
echo ""

echo "=========================================="
echo "✓ AI demo image pushed to registry!"
echo "=========================================="
echo ""
echo "Published image:"
echo "  - $CONTAINER_REGISTRY/ai-agent-demo:$VERSION"
echo ""
