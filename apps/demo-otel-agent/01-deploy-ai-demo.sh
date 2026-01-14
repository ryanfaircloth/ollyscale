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

# Trap to prevent terminal exit
trap 'echo "Script interrupted"; exit 0' INT TERM

echo "========================================================"
echo "  TinyOlly - Deploy AI Agent Demo (Ollama + Auto-Instrumentation)"
echo "========================================================"
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "✗ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "✗ docker-compose is not installed or not in PATH"
    exit 1
fi

# Check if TinyOlly core is running
echo "Checking if TinyOlly core is running..."
if ! docker ps 2>/dev/null | grep -q "otel-collector"; then
    echo "✗ OTel Collector not found"
    echo ""
    echo "Please start TinyOlly core first:"
    echo "  cd ../docker"
    echo "  ./01-start-core.sh"
    echo ""
    exit 1
fi

if ! docker ps 2>/dev/null | grep -q "tinyolly-otlp-receiver"; then
    echo "✗ TinyOlly OTLP Receiver not found"
    echo ""
    echo "Please start TinyOlly core first:"
    echo "  cd ../docker"
    echo "  ./01-start-core.sh"
    echo ""
    exit 1
fi

echo "✓ TinyOlly core is running"
echo ""

# Deploy AI demo
echo "Deploying AI Agent demo with Ollama..."
echo ""
echo "NOTE: First run will pull the Ollama image and tinyllama model (~1.5GB total)."
echo "      This may take a few minutes..."
echo ""

# Pull images from Docker Hub
echo "Pulling AI agent demo image from Docker Hub..."
docker-compose pull
PULL_EXIT_CODE=$?

if [ $PULL_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "✗ Failed to pull AI agent demo image from Docker Hub (exit code: $PULL_EXIT_CODE)"
    echo "  Note: For local builds, use ./01-deploy-ai-demo-local.sh"
    exit 1
fi

docker-compose up -d
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "✗ Failed to deploy AI agent demo (exit code: $EXIT_CODE)"
    echo "Check the error messages above for details"
    exit 1
fi

echo ""
echo "========================================================"
echo "  AI Agent Demo Deployed!"
echo "========================================================"
echo ""
echo "Services:"
echo "  - Ollama (tinyllama model): http://localhost:11434"
echo "  - AI Agent: generating traces every 15 seconds"
echo ""
echo "TinyOlly UI: http://localhost:5002"
echo "  → Click 'AI Agents' tab to see GenAI traces"
echo ""
echo "Watch agent logs:"
echo "  docker-compose logs -f ai-agent"
echo ""
echo "Watch Ollama logs:"
echo "  docker-compose logs -f ollama"
echo ""
echo "To stop AI demo:"
echo "  ./02-stop-ai-demo.sh"
echo ""
echo "To cleanup (remove volumes):"
echo "  ./03-cleanup-ai-demo.sh"
echo ""
