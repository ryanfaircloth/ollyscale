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

# Build ALL TinyOlly images locally (multi-arch)
# Usage: ./build-all.sh [version]
# Example: ./build-all.sh v2.1.0
#
# This builds: core, demo, ebpf-demo, and ai-demo images
# To push after building, run: ./03-push-all.sh [version]

VERSION=${1:-"latest"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "TinyOlly - Build ALL Images (No Push)"
echo "=========================================="
echo "Version: $VERSION"
echo ""

# Build core images
echo ""
echo ">>> Building Core Images..."
echo ""
bash "$SCRIPT_DIR/02-build-core.sh" "$VERSION"

# Build demo images
echo ""
echo ">>> Building Demo Images..."
echo ""
bash "$SCRIPT_DIR/02-build-demo.sh" "$VERSION"

# Build eBPF demo images
echo ""
echo ">>> Building eBPF Demo Images..."
echo ""
bash "$SCRIPT_DIR/02-build-ebpf-demo.sh" "$VERSION"

# Build AI demo image
echo ""
echo ">>> Building AI Demo Image..."
echo ""
bash "$SCRIPT_DIR/02-build-ai-demo.sh" "$VERSION"

echo ""
echo "=========================================="
echo "✓ ALL images built locally!"
echo "=========================================="
echo ""
echo "Core images:"
echo "  - tinyolly/tinyolly:$VERSION (unified UI + OTLP receiver)"
echo "  - tinyolly/opamp-server:$VERSION"
echo ""
echo "Demo images:"
echo "  - tinyolly/demo-frontend:$VERSION"
echo "  - tinyolly/demo-backend:$VERSION"
echo ""
echo "eBPF Demo images:"
echo "  - tinyolly/ebpf-frontend:$VERSION"
echo "  - tinyolly/ebpf-backend:$VERSION"
echo ""
echo "AI Demo image:"
echo "  - tinyolly/ai-agent-demo:$VERSION"
echo ""
echo "Next step - push to registry:"
echo "  ./03-push-all.sh $VERSION"
echo ""
