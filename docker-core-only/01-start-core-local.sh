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

echo "Starting TinyOlly Core (No OTel Collector) - LOCAL BUILD MODE"
echo "================================================================"
echo ""
echo "This script builds images locally instead of using Docker Hub."
echo "For production deployments, use ./01-start-core.sh instead."
echo ""
echo "Starting observability stack:"
echo "  - TinyOlly OTLP Receiver (listening on 4343)"
echo "  - TinyOlly OpAMP Server (listening on 4320/4321)"
echo "  - Redis"
echo "  - TinyOlly Frontend (web UI)"
echo ""
echo "NOTE: No OpenTelemetry Collector included."
echo "      Use your external collector (e.g., Elastic EDOT) and point it to:"
echo "      http://tinyolly-otlp-receiver:4343"
echo ""
echo "      Optional: Configure your external collector to connect to OpAMP server:"
echo "      ws://localhost:4320/v1/opamp (WebSocket endpoint)"
echo ""

echo "Building images locally..."
echo ""

# Build the shared Python base image first (using ../docker as context)
echo "Building shared Python base image..."
docker build -t tinyolly/python-base:latest -f ../docker/dockerfiles/Dockerfile.tinyolly-python-base ../docker
if [ $? -ne 0 ]; then
    echo "✗ Failed to build shared base image"
    exit 1
fi
echo "✓ Base image built"
echo ""

# This prevents stale remote configs from persisting across restarts
echo "Clearing cached collector config..."
docker volume rm tinyolly-otel-supervisor-data 2>/dev/null || true

# Clear Redis data from previous runs
# This removes stale traces, metrics, and logs for a clean start
echo "Clearing Redis data..."
docker exec tinyolly-redis redis-cli -p 6579 FLUSHALL 2>/dev/null || true

# Use docker-compose with local build config
docker compose -f docker-compose-tinyolly-core-local.yml up -d --build --force-recreate 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "✗ Failed to start core services (exit code: $EXIT_CODE)"
    echo "Check the error messages above for details"
    exit 1
fi

echo ""
echo "Services started!"
echo ""

echo "TinyOlly UI:       http://localhost:5005"
echo "OTLP Endpoint:     localhost:4343 (gRPC only, for external collector)"
echo "OpAMP WebSocket:   ws://localhost:4320/v1/opamp (for external collector config management)"
echo ""
echo "Next steps:"
echo "  1. Configure your external collector to send telemetry to: localhost:4343 (gRPC)"
echo "     Note: TinyOlly receiver only supports gRPC. For HTTP, use a collector that"
echo "           accepts HTTP and forwards via gRPC."
echo "  2. (Optional) Configure your external collector to connect to OpAMP server:"
echo "     ws://localhost:4320/v1/opamp - this enables remote config management via TinyOlly UI"
echo "  3. Open TinyOlly UI: http://localhost:5005"
echo "  4. Stop services:    ./02-stop-core.sh"
echo ""
