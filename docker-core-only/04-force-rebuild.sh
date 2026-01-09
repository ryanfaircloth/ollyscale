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

set +e  # Don't exit on errors

echo "TinyOlly Force Rebuild (Clean Cache) - No OTel Collector"
echo "=================================================="
echo ""
echo "This will:"
echo "  1. Stop all running containers"
echo "  2. Remove all images"
echo "  3. Clear Docker build cache"
echo "  4. Rebuild everything from scratch"
echo ""
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Step 1: Stopping containers..."
docker compose -f docker-compose-tinyolly-core.yml down

echo ""
echo "Step 2: Clearing Redis data..."
docker exec tinyolly-redis redis-cli -p 6579 FLUSHALL 2>/dev/null || true

echo ""
echo "Step 3: Clearing cached collector config..."
docker volume rm tinyolly-otel-supervisor-data 2>/dev/null || true

echo ""
echo "Step 4: Removing TinyOlly images..."
docker compose -f docker-compose-tinyolly-core.yml down --rmi all

echo ""
echo "Step 5: Cleaning Docker build cache..."
docker builder prune -f

echo ""
echo "Step 6: Rebuilding from scratch (no cache)..."
docker compose -f docker-compose-tinyolly-core.yml build --no-cache

echo ""
echo "Step 7: Starting services..."
docker compose -f docker-compose-tinyolly-core.yml up -d

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "✗ Failed to start services (exit code: $EXIT_CODE)"
    echo "Check the error messages above for details"
    exit 1
fi

echo ""
echo "✓ Force rebuild complete!"
echo ""
echo "TinyOlly UI:       http://localhost:5005"
echo "OTLP Endpoint:     localhost:4343 (gRPC only, for external collector)"
echo "OpAMP WebSocket:   ws://localhost:4320/v1/opamp (for external collector config management)"
echo ""

