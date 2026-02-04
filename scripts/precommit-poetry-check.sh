#!/bin/bash
# Pre-commit hook to validate Poetry lock files are in sync
set -e

echo "Checking Poetry files..."

# shellcheck disable=SC2043
for dir in apps/api apps/demo apps/demo-otel-agent; do
    if [ -f "$dir/pyproject.toml" ]; then
        echo "Checking $dir..."
        cd "$dir" || exit 1

        # Check if poetry.lock exists and is in sync
        if [ -f "poetry.lock" ]; then
            poetry check --lock
        else
            echo "Warning: No poetry.lock in $dir"
        fi

        cd - > /dev/null || exit 1
    fi
done

echo "Poetry checks passed!"
