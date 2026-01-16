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

# Push ALL ollyScale images to container registry
# Usage: ./push-all.sh [version]
# Example: ./push-all.sh v2.1.0
#
# This pushes: core, demo, ebpf-demo, and ai-demo images
# Run ./build-all.sh first to build the images

VERSION=${1:-"latest"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "ollyScale - Push ALL Images to Container Registry"
echo "=========================================="
echo "Version: $VERSION"
echo ""

# Push core images
echo ""
echo ">>> Pushing Core Images..."
echo ""
bash "$SCRIPT_DIR/03-push-core.sh" "$VERSION"

# Push demo images
echo ""
echo ">>> Pushing Demo Images..."
echo ""
bash "$SCRIPT_DIR/03-push-demo.sh" "$VERSION"

# Push eBPF demo images
echo ""
echo ">>> Pushing eBPF Demo Images..."
echo ""
bash "$SCRIPT_DIR/03-push-ebpf-demo.sh" "$VERSION"

# Push AI demo image
echo ""
echo ">>> Pushing AI Demo Image..."
echo ""
bash "$SCRIPT_DIR/03-push-ai-demo.sh" "$VERSION"

echo ""
echo "=========================================="
echo "✓ ALL images pushed to registry!"
echo "=========================================="
echo ""
echo "Published images:"
echo "  - ollyscale/ollyscale:$VERSION (unified UI + OTLP receiver)"
echo "  - ollyscale/opamp-server:$VERSION"
echo "  - ollyscale/demo-frontend:$VERSION"
echo "  - ollyscale/demo-backend:$VERSION"
echo "  - ollyscale/ebpf-frontend:$VERSION"
echo "  - ollyscale/ebpf-backend:$VERSION"
echo "  - ollyscale/ai-agent-demo:$VERSION"
echo ""
