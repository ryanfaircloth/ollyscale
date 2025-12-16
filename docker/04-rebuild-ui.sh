#!/bin/bash
set +e  # Don't exit on errors

echo "========================================================"
echo "  TinyOlly - Rebuild UI Only"
echo "========================================================"
echo ""

# Rebuild and restart only the tinyolly-ui service
echo "Rebuilding tinyolly-ui..."
docker-compose -f docker-compose-tinyolly-core.yml build tinyolly-ui
BUILD_EXIT_CODE=$?

if [ $BUILD_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "✗ Failed to build tinyolly-ui (exit code: $BUILD_EXIT_CODE)"
    exit 1
fi

echo ""
echo "Restarting tinyolly-ui..."
docker-compose -f docker-compose-tinyolly-core.yml up -d --no-deps --force-recreate tinyolly-ui
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "✗ Failed to restart tinyolly-ui (exit code: $EXIT_CODE)"
    exit 1
fi

echo ""
echo "✓ TinyOlly UI rebuilt and restarted"
echo ""
echo "TinyOlly UI: http://localhost:5005"
echo ""
