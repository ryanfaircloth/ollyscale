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


# Generate traffic to custom demo applications (demo-frontend and demo-backend)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Demo app URL - uses HTTPRoute FQDN
FRONTEND_URL="https://demo-frontend.ollyscale.test:49443"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ollyScale Custom Demo Traffic Generator${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if frontend is accessible
if ! curl -s -k -o /dev/null -w "%{http_code}" "$FRONTEND_URL/" | grep -q "200"; then
    echo -e "${YELLOW}⚠ Frontend not accessible at ${FRONTEND_URL}${NC}"
    echo -e "${YELLOW}Make sure:${NC}"
    echo -e "  1. Custom demo is deployed via Helm/ArgoCD"
    echo -e "  2. HTTPRoute is configured: ${CYAN}kubectl get httproute demo-frontend -n ollyscale-demos${NC}"
    echo -e "  3. Envoy Gateway is running: ${CYAN}kubectl get gateway cluster-gateway -n envoy-gateway-system${NC}"
    echo ""
    echo -e "${YELLOW}Attempting to generate traffic anyway...${NC}"
    echo ""
fi

echo -e "${CYAN}Generating traffic to custom demo application...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Counter
REQUEST_COUNT=0

while true; do
    # Randomly choose an endpoint
    RAND=$((RANDOM % 100))

    if [ $RAND -lt 10 ]; then
        # 10% - Error endpoint
        ENDPOINT="/error"
        echo -e "${YELLOW}[$REQUEST_COUNT] Calling ${ENDPOINT}${NC}"
        curl -s -k "$FRONTEND_URL$ENDPOINT" > /dev/null
    elif [ $RAND -lt 30 ]; then
        # 20% - Calculate endpoint
        ENDPOINT="/calculate"
        echo -e "${GREEN}[$REQUEST_COUNT] Calling ${ENDPOINT}${NC}"
        curl -s -k "$FRONTEND_URL$ENDPOINT" > /dev/null
    elif [ $RAND -lt 50 ]; then
        # 20% - Hello endpoint
        ENDPOINT="/hello"
        echo -e "${GREEN}[$REQUEST_COUNT] Calling ${ENDPOINT}${NC}"
        curl -s -k "$FRONTEND_URL$ENDPOINT" > /dev/null
    else
        # 50% - Process order (complex multi-service trace)
        ENDPOINT="/process-order"
        echo -e "${CYAN}[$REQUEST_COUNT] Calling ${ENDPOINT} (distributed trace)${NC}"
        RESPONSE=$(curl -s -k "$FRONTEND_URL$ENDPOINT")

        # Show order status
        if echo "$RESPONSE" | grep -q '"status":"success"'; then
            ORDER_ID=$(echo "$RESPONSE" | grep -o '"order_id":[0-9]*' | cut -d':' -f2)
            echo -e "  ${GREEN}✓ Order $ORDER_ID completed${NC}"
        elif echo "$RESPONSE" | grep -q '"status":"failed"'; then
            echo -e "  ${YELLOW}⚠ Order failed${NC}"
        fi
    fi

    REQUEST_COUNT=$((REQUEST_COUNT + 1))

    # Random delay between requests
    DELAY=$(awk -v min=0.5 -v max=2.0 'BEGIN{srand(); print min+rand()*(max-min)}')
    sleep $DELAY
done
