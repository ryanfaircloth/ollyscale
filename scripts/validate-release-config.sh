#!/bin/bash
# Test script to validate release-please configuration

set -e

echo "🔍 Validating release-please configuration..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Test 1: Check manifest matches config
echo "2️⃣  Checking manifest matches config..."
manifest_paths=$(jq -r 'keys[]' .release-please-manifest.json)
for path in $manifest_paths; do
    if jq -e ".packages.\"$path\"" release-please-config.json > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $path has config${NC}"
    else
        echo -e "${RED}❌ $path missing config${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Test 2: Check for duplicate components
echo "2️⃣  Checking for duplicate component names..."
components=$(jq -r '.packages[].component' release-please-config.json | sort)
duplicates=$(echo "$components" | uniq -d)
if [ -z "$duplicates" ]; then
    echo -e "${GREEN}✅ All component names are unique${NC}"
else
    echo -e "${RED}❌ Duplicate component names found:${NC}"
    echo "$duplicates"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 3: Validate extra-files paths exist
echo "3️⃣  Validating extra-files paths exist..."
while IFS='|' read -r package_path file_path; do
    full_path="${package_path}/${file_path}"
    if [[ "$file_path" == *"*"* ]]; then
        echo -e "${YELLOW}⏭️  Skipping glob pattern: $full_path${NC}"
    elif [ -f "$full_path" ]; then
        echo -e "${GREEN}✅ $full_path exists${NC}"
    else
        echo -e "${RED}❌ $full_path does not exist${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done < <(jq -r '.packages | to_entries[] | .key as $pkg | .value["extra-files"][]? | "\($pkg)|\(if type == "string" then . else .path end)"' release-please-config.json)
echo ""

# Test 4: Check bumpDependents configuration
echo "4️⃣  Checking bumpDependents configuration..."
echo -e "${YELLOW}Chart dependencies:${NC}"
jq -r '.packages["charts/ollyscale"]["extra-files"][] | select(.bumpDependents) | "  - \(.jsonpath) → component: \(.component)"' release-please-config.json
echo ""

# Test 5: Validate component references in bumpDependents
echo "5️⃣  Validating bumpDependents component references..."
all_components=$(jq -r '.packages[].component' release-please-config.json)
while read -r comp; do
    if echo "$all_components" | grep -q "^${comp}$"; then
        echo -e "${GREEN}✅ Component '$comp' exists${NC}"
    else
        echo -e "${RED}❌ Component '$comp' not found in config${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done < <(jq -r '.packages["charts/ollyscale"]["extra-files"][] | select(.bumpDependents) | .component' release-please-config.json)
echo ""

# Test 6: Count configured components
echo "6️⃣  Component summary..."
echo -e "${YELLOW}Total components: $(jq '.packages | length' release-please-config.json)${NC}"
echo -e "${YELLOW}Apps: $(jq '[.packages | to_entries[] | select(.key | startswith("apps/"))] | length' release-please-config.json)${NC}"
echo -e "${YELLOW}Charts: $(jq '[.packages | to_entries[] | select(.key | startswith("charts/"))] | length' release-please-config.json)${NC}"
echo ""

# Test 7: Verify image tag patterns in values.yaml
echo "7️⃣  Checking image tags in values.yaml..."
if grep -q 'tag: v0.0.0' charts/ollyscale/values.yaml; then
    echo -e "${GREEN}✅ Found placeholder image tags${NC}"
else
    echo -e "${YELLOW}⚠️  No placeholder tags found (may be OK if already set)${NC}"
fi
echo ""

# Summary
echo "================================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✨ All validation checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Merge to main branch"
    echo "  2. Make a test commit with conventional format"
    echo "  3. Verify release-please creates PRs"
    echo "  4. Test the complete release flow"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS error(s)${NC}"
    echo "Please fix the errors before proceeding."
    exit 1
fi
