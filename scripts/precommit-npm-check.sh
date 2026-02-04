#!/bin/bash
# Check npm package-lock.json is in sync with package.json

set -e

FAILED=0

# shellcheck disable=SC2043  # Single directory is intentional
for dir in apps/web-ui; do
    if [ ! -f "$dir/package.json" ]; then
        continue
    fi

    echo "Checking npm dependencies in $dir..."

    if [ ! -f "$dir/package-lock.json" ]; then
        echo "ERROR: $dir/package-lock.json missing. Run: cd $dir && npm install"
        FAILED=1
        continue
    fi

    cd "$dir" || exit 1
    # Run npm ci dry-run and capture output
    if ! npm_output=$(npm ci --dry-run --prefer-offline 2>&1); then
        echo "ERROR: $dir npm dependencies out of sync."
        echo "$npm_output"
        echo "Fix by running: cd $dir && npm install"
        FAILED=1
    fi
    cd - >/dev/null || exit 1
done

if [ $FAILED -eq 1 ]; then
    exit 1
fi

echo "✓ npm dependencies are in sync"
