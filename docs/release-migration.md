# Migration from semantic-release to release-please

This document explains the migration from semantic-release to release-please and what changed.

## Why Migrate?

The previous semantic-release system had challenges with:

- Complex multi-package coordination requiring custom plugins
- All components released together even when only one changed
- Difficulty managing cross-component dependencies
- Complex configuration spread across multiple `.releaserc.json` files

The new release-please system provides:

- **Native multi-package support** - no special plugins needed
- **Separate releases** - each component releases independently
- **bumpDependents feature** - automatic version bumping when dependencies change
- **Simpler configuration** - single `release-please-config.json` file
- **Better visibility** - separate PRs for each component release

## What Changed

### Configuration Files

**Removed:**

- Individual `.releaserc.json` files in `apps/*/` and `charts/*/` ✅ COMPLETED
- Root `.releaserc.json` ✅ COMPLETED
- `.multi-releaserc.json` ✅ COMPLETED
- All semantic-release dependencies from `package.json` ✅ COMPLETED
- `.github/workflows/semantic-release.yml` ✅ COMPLETED

**Added:**

- `release-please-config.json` - Main configuration for all components
- `.release-please-manifest.json` - Version tracking manifest

### GitHub Workflows

**Removed:**

- `.github/workflows/semantic-release.yml` - Completely removed ✅ COMPLETED

**Added:**

- `.github/workflows/release-please.yml` - New release workflow supporting multiple branches

### Version Management

**Before (semantic-release):**

```bash
# All components released together when main is updated
git push origin main
# semantic-release runs and releases everything with changes
```

**After (release-please):**

```bash
# Commit with conventional commit format
git commit -m "feat(ollyscale): add new API endpoint"
git push origin main

# release-please creates/updates PR for ollyscale component
# Merge the PR to trigger the release
```

### Dependency Management

**Before (semantic-release):**

- Each component's `.releaserc.json` had `semantic-release-yaml` plugin
- Manually specified which values.yaml fields to update
- No automatic chart version bumping

**After (release-please):**

- App components update their image tags in values.yaml via `extra-files`
- Chart has `bumpDependents: true` entries that watch for these changes
- Chart version automatically bumps when any dependency changes

## Migration Steps

### For Developers

1. **Commit message format stays the same** - Continue using Conventional Commits
2. **Review release PRs** - release-please creates PRs that need to be reviewed and merged
3. **Watch for dependency bumps** - Chart releases may happen automatically due to bumpDependents

### For Maintainers

1. **Bootstrap versions** - Initial versions set in `.release-please-manifest.json`
2. **Monitor first releases** - Verify the workflow works correctly
3. **Update documentation** - Point to new release system docs
4. **Remove old configs** - After successful migration, remove semantic-release configs

## Configuration Details

### Component Configuration

Each component in `release-please-config.json` has:

```json
{
  "apps/ollyscale": {
    "component": "ollyscale",           // Tag prefix: ollyscale-v1.0.0
    "release-type": "python",           // Handles Python version files
    "package-name": "@ollyscale/ollyscale",
    "extra-files": [                    // Additional files to update
      {
        "type": "yaml",
        "path": "charts/ollyscale/values.yaml",
        "jsonpath": "$.frontend.image.tag"
      }
    ]
  }
}
```

### Dependency Management

The chart configuration uses `bumpDependents`:

```json
{
  "charts/ollyscale": {
    "component": "chart-ollyscale",
    "release-type": "helm",
    "extra-files": [
      {
        "type": "yaml",
        "path": "charts/ollyscale/values.yaml",
        "jsonpath": "$.frontend.image.tag",
        "component": "ollyscale",       // Watch this component
        "bumpDependents": true          // Bump chart when ollyscale changes
      }
    ]
  }
}
```

## Release Flow Comparison

### semantic-release Flow

```text
1. Push to main
2. semantic-release runs for all workspaces
3. Each workspace checks for changes
4. Versions bumped, CHANGELOGs updated
5. Docker images built and pushed
6. Git tags created
7. GitHub releases created
```

**Issues:**

- All workspaces processed even if unchanged
- Single workflow must handle all build types
- Complex plugin configuration per workspace
- No dependency tracking between components

### release-please Flow

```text
1. Push to main
2. release-please creates/updates PR per component with changes
3. Review and merge PR
4. release-please creates release tag
5. Workflow triggered by release tag
6. Build and publish component (Docker/Helm)
7. GitHub release created with notes
```

**Benefits:**

- Only changed components get PRs
- Review releases before they happen
- Matrix strategy handles builds cleanly
- bumpDependents tracks component relationships

## Example Scenarios

### Scenario 1: App Change

```bash
# Make a change to ollyscale backend
git commit -m "feat(ollyscale): add trace filtering"
git push origin main

# Results:
# 1. release-please creates PR for apps/ollyscale
# 2. PR updates version to 2.2.0 in package.json
# 3. PR updates frontend.image.tag in values.yaml to v2.2.0
# 4. bumpDependents detects this change
# 5. release-please also creates PR for charts/ollyscale
# 6. Chart version bumps to 0.2.0

# Merge both PRs to release
```

### Scenario 2: Chart-Only Change

```bash
# Update chart templates
git commit -m "feat(chart-ollyscale): add podDisruptionBudget"
git push origin main

# Results:
# 1. release-please creates PR for charts/ollyscale only
# 2. Chart version bumps to 0.2.0
# No app component changes needed
```

### Scenario 3: Multiple App Changes

```bash
# Make changes to UI and backend
git commit -m "feat(ollyscale-ui): improve timeline view"
git commit -m "fix(ollyscale): handle null span attributes"
git push origin main

# Results:
# 1. release-please creates PR for apps/ollyscale-ui
# 2. release-please creates PR for apps/ollyscale
# 3. release-please creates PR for charts/ollyscale (due to bumpDependents)
# All can be reviewed and merged independently
```

## Troubleshooting

### Release PR not created

**Check:**

1. Commits follow Conventional Commit format
2. Commits are in correct component directory
3. Commits pushed to `main` branch
4. `.release-please-manifest.json` has entry for component

### Chart not bumped when app changes

**Check:**

1. App component has `extra-files` entry updating `values.yaml`
2. Chart has matching `bumpDependents: true` entry
3. Component name matches exactly in both places

### Build fails after release

**Check:**

1. Dockerfile exists and is valid
2. GitHub token has packages:write permission
3. Image name in workflow matches ghcr.io registry

## Rollback Plan

If the migration needs to be rolled back:

1. Re-enable semantic-release workflow:

   ```yaml
   # Remove "if: false" from .github/workflows/semantic-release.yml
   ```

2. Restore `.releaserc.json` files from git history:

   ```bash
   git checkout <previous-commit> -- apps/*/.releaserc.json charts/*/.releaserc.json
   ```

3. Remove release-please configuration:

   ```bash
   git rm release-please-config.json .release-please-manifest.json
   git rm .github/workflows/release-please.yml
   ```

## Questions?

See [docs/release-system.md](release-system.md) for complete documentation or open an issue on GitHub.
