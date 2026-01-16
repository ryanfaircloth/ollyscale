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

echo "========================================================"
echo "  ollyScale - Install MkDocs"
echo "========================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is not installed or not in PATH"
    echo "Please install Python 3 first"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "✗ pip3 is not installed or not in PATH"
    echo "Please install pip3 first"
    exit 1
fi

echo "Installing MkDocs and required plugins..."
echo ""

# Install MkDocs and plugins
pip3 install mkdocs mkdocs-material pymdown-extensions

echo ""
echo "========================================================"
echo "  MkDocs Installation Complete!"
echo "========================================================"
echo ""
echo "Installed packages:"
echo "  - mkdocs: Static site generator"
echo "  - mkdocs-material: Material theme for MkDocs"
echo "  - pymdown-extensions: Markdown extensions"
echo ""
echo "To serve documentation locally:"
echo "  mkdocs serve"
echo ""
echo "To build documentation:"
echo "  mkdocs build"
echo ""
echo "To deploy to GitHub Pages:"
echo "  ./mkdocs-deploy.sh"
echo ""
