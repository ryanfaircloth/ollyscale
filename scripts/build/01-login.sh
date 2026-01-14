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

# Helper script to login to Docker Hub
# Run this before building and pushing images

echo "Docker Hub Login"
echo "================"
echo ""
echo "You'll need your Docker Hub credentials:"
echo "  Username: (your Docker Hub username)"
echo "  Password: (use an access token, not your password)"
echo ""
echo "To create an access token:"
echo "  1. Go to https://hub.docker.com/settings/security"
echo "  2. Click 'New Access Token'"
echo "  3. Name it 'tinyolly-builds' with Read & Write permissions"
echo "  4. Use the token instead of your password below"
echo ""

if docker login; then
    echo ""
    echo "✓ Login successful!"
    echo ""
    echo "Next steps:"
    echo ""
    echo "  Step 2 - Build images:"
    echo "    ./02-build-all.sh v2.1.0   # Build all images"
    echo "    ./02-build-core.sh v2.1.0  # Build core only"
    echo ""
    echo "  Step 3 - Push to Docker Hub:"
    echo "    ./03-push-all.sh v2.1.0    # Push all images"
    echo "    ./03-push-core.sh v2.1.0   # Push core only"
else
    echo ""
    echo "✗ Login failed. Please try again."
    exit 1
fi
