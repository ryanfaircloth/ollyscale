# ollyScale Rebranding - Phase 0 Complete

## Pre-Flight Checks ✅

1. **Tagged pre-rebrand state:** `pre-ollyscale-rebrand`
2. **Audit complete:** Found 2,052 references to "tinyolly" or "TinyOlly"
3. **Major areas identified:**
   - `.kind/` Terraform configurations (~50+ files)
   - Helm charts (`charts/tinyolly*/`)
   - Source code (`apps/tinyolly/`, `apps/tinyolly-ui/`)
   - Documentation (`docs/`, `README.md`, `CONTRIBUTING.md`)
   - CI/CD (`.github/`, `scripts/`, `Makefile`)
   - Docker files and configs

## Files That MUST Keep TinyOlly Attribution

- `LICENSE-BSD3-ORIGINAL` - Original license
- `REBRANDING-PLAN.md` - This planning document
- Copyright headers in unmodified upstream files
- Git history (immutable)

## Ready for Phase 1: Foundation (Licensing & Core Docs)

Next steps:

1. Create LICENSE (AGPL-3.0)
2. Create NOTICE file
3. Create header templates
4. Update README with origins section
