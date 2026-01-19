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

# Test 1: Validate JSON files
echo "1️⃣  Validating JSON files..."
if jq empty release-please-config.json 2>/dev/null; then
    echo -e "${GREEN}✅ release-please-config.json is valid JSON${NC}"
else
    echo -e "${RED}❌ release-please-config.json is invalid JSON${NC}"
    ERRORS=$((ERRORS + 1))
fi

if jq empty .release-please-manifest.json 2>/dev/null; then
    echo -e "${GREEN}✅ .release-please-manifest.json is valid JSON${NC}"
else
    echo -e "${RED}❌ .release-please-manifest.json is invalid JSON${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 2: Check manifest matches config
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

# Test 3: Check for duplicate components
echo "3️⃣  Checking for duplicate component names..."
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

# Test 4: Validate extra-files paths exist
echo "4️⃣  Validating extra-files paths exist..."
while read -r file; do
    if [[ "$file" == *"*"* ]]; then
        echo -e "${YELLOW}⏭️  Skipping glob pattern: $file${NC}"
    elif [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file does not exist${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done < <(jq -r '.packages[] | .["extra-files"][]? | if type == "string" then . else .path end' release-please-config.json)
echo ""

# Test 5: Check bumpDependents configuration
echo "5️⃣  Checking bumpDependents configuration..."
echo -e "${YELLOW}Chart dependencies:${NC}"
jq -r '.packages["charts/ollyscale"]["extra-files"][] | select(.bumpDependents) | "  - \(.jsonpath) → component: \(.component)"' release-please-config.json
echo ""

# Test 6: Validate component references in bumpDependents
echo "6️⃣  Validating bumpDependents component references..."
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


# Test 7: Check Chart.yaml versions
echo "7️⃣  Checking Chart.yaml versions..."
for chart in charts/*/Chart.yaml; do
    if [ -f "$chart" ]; then
        version=$(grep '^version:' "$chart" | awk '{print $2}')
        if echo "$version" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' > /dev/null; then
            echo -e "${GREEN}✅ $chart version: $version${NC}"
        else
            echo -e "${RED}❌ Invalid version in $chart: $version${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done
echo ""

# Test 8: Check workflow file exists
echo "8️⃣  Checking workflow files..."
if [ -f ".github/workflows/release-please.yml" ]; then
    echo -e "${GREEN}✅ release-please workflow exists${NC}"
else
    echo -e "${RED}❌ release-please workflow missing${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ -f ".github/workflows/validate-release-config.yml" ]; then
    echo -e "${GREEN}✅ validation workflow exists${NC}"
else
    echo -e "${RED}❌ validation workflow missing${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 9: Count configured components
echo "9️⃣  Component summary..."
echo -e "${YELLOW}Total components: $(jq '.packages | length' release-please-config.json)${NC}"
echo -e "${YELLOW}Apps: $(jq '[.packages | to_entries[] | select(.key | startswith("apps/"))] | length' release-please-config.json)${NC}"
echo -e "${YELLOW}Charts: $(jq '[.packages | to_entries[] | select(.key | startswith("charts/"))] | length' release-please-config.json)${NC}"
echo ""

# Test 10: Verify image tag patterns in values.yaml
echo "🔟  Checking image tags in values.yaml..."
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
