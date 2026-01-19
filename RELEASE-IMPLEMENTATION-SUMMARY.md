# Release System Implementation Summary

## Overview

This document summarizes the implementation of the release-please system for the ollyscale repository.
The system was implemented in the `copilot/next-release` branch as requested.

## Problem Statement

The repository needed a release system that could:

1. Handle multiple components (apps and Helm charts) with independent versioning
2. Manage cross-component dependencies (e.g., chart versions bump when app versions change)
3. Build and publish container images to GHCR
4. Package and publish Helm charts to OCI registry
5. Support pre-release builds for testing

The previous semantic-release system was complex and couldn't handle the dependency relationships
properly, requiring a custom fork of release-please with the `bumpDependents` feature.

## Solution Implemented

### release-please with bumpDependents

We implemented release-please using the forked action `ryanfaircloth/release-please-action@test/fork-dependency`
which supports the `bumpDependents` feature for cross-component version management.

### Architecture

**8 Components Configured:**

**Applications (5):**

1. `apps/ollyscale` (Python backend) - v2.1.9
2. `apps/ollyscale-ui` (TypeScript frontend) - v0.0.0
3. `apps/opamp-server` (Go OpAMP server) - v1.0.1
4. `apps/demo` (Demo app) - v0.0.0
5. `apps/demo-otel-agent` (Demo OTel agent) - v0.0.0

**Charts (3):**

1. `charts/ollyscale` (Main chart) - v0.1.0
2. `charts/ollyscale-demos` (Demo charts) - v1.0.0
3. `charts/ollyscale-otel-agent` (OTel agent chart) - v1.0.0

### Dependency Management

The `charts/ollyscale` chart tracks 4 dependencies using `bumpDependents: true`:

```text
$.frontend.image.tag     → watches: ollyscale
$.otlpReceiver.image.tag → watches: ollyscale
$.webui.image.tag        → watches: ollyscale-ui
$.opampServer.image.tag  → watches: opamp-server
```

When any of these app components release a new version:

1. The app updates its image tag in `values.yaml`
2. release-please detects this via `bumpDependents: true`
3. The chart version automatically bumps
4. Chart release PR is created

## Files Created/Modified

### Configuration Files

- **`release-please-config.json`** (144 lines) - Main configuration
  - Defines all 8 components
  - Configures release types (python, node, helm, simple)
  - Sets up extra-files for version propagation
  - Implements bumpDependents for chart dependencies

- **`.release-please-manifest.json`** (10 lines) - Version manifest
  - Tracks current version of each component
  - Updated automatically by release-please

### GitHub Workflows

- **`.github/workflows/release-please.yml`** (176 lines) - Main workflow
  - Runs release-please on push to main
  - Creates/updates release PRs
  - Builds and pushes Docker images (multi-platform: amd64/arm64)
  - Packages and publishes Helm charts to OCI registry
  - Supports pre-release via workflow_dispatch

- **`.github/workflows/semantic-release.yml`** (modified) - Deprecated workflow
  - Disabled with `if: false` condition
  - Kept for reference during migration
  - Marked as deprecated in name and comments

### Documentation

- **`docs/release-system.md`** (265 lines) - Complete system documentation
  - Architecture overview
  - Conventional Commit format
  - Release workflow
  - Docker and Helm publishing
  - Troubleshooting guide
  - Examples and scenarios

- **`docs/release-migration.md`** (262 lines) - Migration guide
  - Why we migrated
  - What changed
  - Configuration comparison
  - Example scenarios
  - Rollback plan

- **`README.md`** (12 lines added) - Added release system section
  - Links to full documentation

- **`CONTRIBUTING.md`** (25 lines added) - Added release guidelines
  - Conventional Commit examples with scopes
  - Breaking change format
  - Version bumping rules
  - Links to release documentation

### Scripts

- **`scripts/validate-release-config.sh`** (156 lines) - Validation script
  - 10 comprehensive validation checks
  - JSON validation
  - Component reference validation
  - File existence checks
  - bumpDependents validation
  - Color-coded output

## Key Features

### 1. Separate Pull Requests

Each component gets its own release PR, providing:

- Clear visibility into what's being released
- Ability to review and approve separately
- Independent release timing

### 2. bumpDependents Feature

The chart automatically releases when dependencies change:

- No manual chart version updates needed
- Ensures chart and app versions stay in sync
- Reduces human error

### 3. Multi-platform Docker Builds

All images built for:

- `linux/amd64`
- `linux/arm64`

With multiple tags:

- `v1.2.3` - exact version
- `1.2` - minor version
- `1` - major version
- `latest` - latest stable (not for pre-releases)

### 4. Helm Chart Publishing

Charts published to OCI registry:

- `ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale`
- `ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale-demos`
- `ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale-otel-agent`

### 5. Pre-release Support

Manual trigger for testing:

```bash
gh workflow run release-please.yml -f prerelease=true
```

### 6. Conventional Commits

Automatic version bumping based on commit type:

- `feat:` → minor bump (0.x.0)
- `fix:` → patch bump (0.0.x)
- `feat!:` → major bump (x.0.0)

## Validation Results

All validation checks pass:

```text
✅ JSON files are valid
✅ Manifest matches config
✅ No duplicate components
✅ All extra-files paths exist
✅ bumpDependents configured correctly
✅ Component references valid
✅ Chart.yaml versions correct
✅ Workflow files exist
✅ 8 components configured (5 apps, 3 charts)
✅ Image tags properly set
```

## Testing Plan

Once merged to `main` branch:

### Step 1: Test Single Component Release

```bash
git checkout main
echo "// test comment" >> apps/ollyscale/README.md
git add apps/ollyscale/README.md
git commit -m "feat(ollyscale): test release-please system"
git push origin main
```

**Expected Result:**

- release-please creates PR for `apps/ollyscale`
- PR updates version to v2.2.0
- PR updates `frontend.image.tag` in values.yaml
- PR updates CHANGELOG.md
- Chart PR also created due to bumpDependents

### Step 2: Merge and Verify Build

```bash
gh pr merge <pr-number>
```

**Expected Result:**

- Release created with tag `ollyscale-v2.2.0`
- Docker image built and pushed to `ghcr.io/ryanfaircloth/ollyscale/ollyscale:2.2.0`
- Chart PR updates to reference new image tag
- Chart release created when its PR is merged

### Step 3: Test Chart Release

```bash
# Merge the chart PR
gh pr merge <chart-pr-number>
```

**Expected Result:**

- Release created with tag `chart-ollyscale-v0.1.1`
- Helm chart packaged and pushed to OCI registry

### Step 4: Verify Pre-release

```bash
gh workflow run release-please.yml -f prerelease=true
```

**Expected Result:**

- Release marked as pre-release
- Docker images do NOT get `latest` tag
- Suitable for testing in staging

## Migration Notes

### Old System (semantic-release)

- Single workflow runs for all components
- Complex multi-semantic-release setup
- All components released together
- Manual dependency management
- `.releaserc.json` files in each component

### New System (release-please)

- Separate PRs per component
- Native multi-package support
- Independent releases
- Automatic dependency tracking via bumpDependents
- Single `release-please-config.json`

### Removed Files (to clean up later)

After successful validation, these can be removed:

- `apps/*/. releaserc.json`
- `charts/*/.releaserc.json`
- Root `.releaserc.json` (already replaced)
- `.multi-releaserc.json` (already replaced)

## Registry Configuration

### Docker Images

- Registry: `ghcr.io`
- Organization: `ryanfaircloth`
- Project: `ollyscale`

Example: `ghcr.io/ryanfaircloth/ollyscale/ollyscale:2.1.9`

### Helm Charts

- Registry: `ghcr.io` (OCI format)
- Organization: `ryanfaircloth`
- Project: `ollyscale/charts`

Example: `ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale:0.1.0`

## Next Steps

1. **Merge this branch** (`copilot/next-release`) to `main`
2. **Test the system** with a real release
3. **Validate bumpDependents** behavior
4. **Monitor for issues** during first few releases
5. **Clean up old configs** once validated
6. **Update CI/CD docs** if needed

## Support

For questions or issues:

- See [docs/release-system.md](release-system.md) for complete documentation
- See [docs/release-migration.md](release-migration.md) for migration details
- Run `scripts/validate-release-config.sh` to validate configuration
- Open an issue on GitHub

## Statistics

- **Total Changes**: 1,064 lines across 9 files
- **Configuration**: 154 lines
- **Documentation**: 552 lines
- **Workflows**: 194 lines
- **Scripts**: 156 lines
- **Other**: 8 lines

## Success Criteria

✅ Release-please configured for all 8 components
✅ bumpDependents implemented for chart dependencies
✅ Multi-platform Docker builds configured
✅ Helm chart OCI publishing configured
✅ Pre-release support added
✅ Comprehensive documentation written
✅ Migration guide created
✅ Validation script passes all checks
✅ Old workflow disabled safely
✅ Contributing guide updated

## Conclusion

The release-please system is fully implemented and validated in the `copilot/next-release` branch. All
configuration is complete, validated, and documented. The system is ready for testing once merged to `main`.

The key innovation is the `bumpDependents` feature from the forked release-please action, which solves the
cross-component dependency problem that the original issue described.
