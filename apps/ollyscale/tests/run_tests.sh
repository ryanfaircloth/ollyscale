#!/bin/bash
# Run TinyOlly UI tests
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=========================================="
echo "TinyOlly UI Tests"
echo "=========================================="

# Install test dependencies if needed
if ! python -c "import pytest" 2>/dev/null; then
    echo "Installing test dependencies..."
    pip install -r requirements-test.txt
fi

# Run tests with coverage
echo ""
echo "Running tests..."
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html:tests/coverage_html

echo ""
echo "=========================================="
echo "Tests complete!"
echo "=========================================="
echo "Coverage report: tests/coverage_html/index.html"
