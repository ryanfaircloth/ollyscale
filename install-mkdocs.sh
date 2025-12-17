#!/bin/bash
set -e

echo "========================================================"
echo "  TinyOlly - Install MkDocs"
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
