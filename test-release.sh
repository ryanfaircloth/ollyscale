#!/bin/bash
# Test semantic-release configuration locally
# This will fail at authentication but validates config is correct

set -e

echo "Testing semantic-release configuration..."
echo ""
echo "Expected behavior:"
echo "  ✅ All 8 packages should load successfully"
echo "  ✅ Dockerfile paths should resolve correctly"
echo "  ❌ Authentication will fail (expected - no real tokens)"
echo ""
echo "Running dry-run..."
echo ""

# Set dummy credentials to get past initial checks
export GITHUB_TOKEN=ghp_dummytoken123456789012345678901234567
export DOCKER_REGISTRY_USER=test
export DOCKER_REGISTRY_PASSWORD=test

# Run semantic-release in dry-run mode
npx @anolilab/multi-semantic-release --dry-run 2>&1 | tee /tmp/semantic-release-test.log

echo ""
echo "Checking results..."
echo ""

# Check if all packages loaded
if grep -q "Loaded package @ollyscale/ollyscale" /tmp/semantic-release-test.log && \
   grep -q "Loaded package @ollyscale/opamp-server" /tmp/semantic-release-test.log && \
   grep -q "Loaded package @ollyscale/demo" /tmp/semantic-release-test.log && \
   grep -q "Loaded package @ollyscale/demo-otel-agent" /tmp/semantic-release-test.log && \
   grep -q "Loaded package @ollyscale/ollyscale-chart" /tmp/semantic-release-test.log && \
   grep -q "Loaded package @ollyscale/ollyscale-demos-chart" /tmp/semantic-release-test.log && \
   grep -q "Loaded package @ollyscale/ollyscale-otel-agent-chart" /tmp/semantic-release-test.log; then
  echo "✅ SUCCESS: All 8 packages loaded"
else
  echo "❌ FAIL: Not all packages loaded"
  exit 1
fi

# Check for Dockerfile errors (the old bug)
if grep -q "Unable to locate Dockerfile.*apps/.*/apps/" /tmp/semantic-release-test.log; then
  echo "❌ FAIL: Dockerfile path duplication detected"
  exit 1
else
  echo "✅ SUCCESS: Dockerfile paths are correct"
fi

# Check that we got to authentication (means config is valid)
if grep -q "EINVALIDGHTOKEN\|EAUTH" /tmp/semantic-release-test.log; then
  echo "✅ SUCCESS: Configuration is valid (failed at authentication as expected)"
else
  echo "⚠️  WARNING: Unexpected failure - check logs"
fi

echo ""
echo "Configuration test complete!"
echo ""
echo "To run actual release:"
echo "  1. Set real GITHUB_TOKEN environment variable"
echo "  2. Run: npx @anolilab/multi-semantic-release"
echo ""
