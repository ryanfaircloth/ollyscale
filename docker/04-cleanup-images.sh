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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TinyOlly - Local Docker Images Cleanup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Find all TinyOlly-related images
echo -e "${BLUE}Searching for TinyOlly Docker images...${NC}"
echo ""

IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "tinyolly|demo-frontend|demo-backend" || true)

if [ -z "$IMAGES" ]; then
    echo -e "${YELLOW}No TinyOlly-related images found${NC}"
    echo ""
    echo -e "${GREEN}Nothing to clean up!${NC}"
    exit 0
fi

# Display images that will be removed
echo -e "${YELLOW}The following Docker images will be removed:${NC}"
echo ""
docker images | grep -E "REPOSITORY|tinyolly|demo-frontend|demo-backend"
echo ""

# Calculate total size
TOTAL_SIZE=$(docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}" | grep -E "tinyolly|demo-frontend|demo-backend" | awk '{print $2}' | sed 's/MB//;s/GB/*1024/;s/KB\/1024/' | bc 2>/dev/null | awk '{sum+=$1} END {printf "%.1f", sum}' || echo "unknown")
echo -e "${BLUE}Total size: ${TOTAL_SIZE}MB${NC}"
echo ""

# Confirm deletion
read -p "$(echo -e ${YELLOW}Do you want to remove these images? [y/N]:${NC} )" -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Removing Docker images...${NC}"
echo ""

# Remove each image
COUNT=0
for IMAGE in $IMAGES; do
    echo -e "${YELLOW}→ Removing ${IMAGE}...${NC}"
    if docker rmi "$IMAGE" 2>/dev/null; then
        COUNT=$((COUNT + 1))
    else
        echo -e "${RED}  Failed to remove ${IMAGE} (may be in use)${NC}"
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Cleanup complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✓ Removed ${COUNT} image(s)${NC}"
echo ""

# Check if any images remain
REMAINING=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "tinyolly|demo-frontend|demo-backend" || true)
if [ -n "$REMAINING" ]; then
    echo -e "${YELLOW}Note: Some images could not be removed (likely in use by running containers):${NC}"
    docker images | grep -E "REPOSITORY|tinyolly|demo-frontend|demo-backend"
    echo ""
    echo -e "${YELLOW}Stop containers first with:${NC}"
    echo "  ./02-stop-core.sh"
    echo "  cd ../docker-demo && docker-compose down"
    echo "  cd ../docker-ai-agent-demo && docker-compose down"
fi

echo ""
echo -e "${BLUE}To clean up dangling images and build cache, run:${NC}"
echo "  docker image prune -a"
echo ""
