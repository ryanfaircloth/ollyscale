# Release-Please Implementation Summary

## What Was Implemented

Release-please is now configured for TinyOlly's monorepo with automated semantic versioning and coordinated releases.

## Files Created/Modified

### Configuration Files

- ✅ `release-please-config.json` - Component definitions and release strategy
- ✅ `.release-please-manifest.json` - Current version tracking
- ✅ `.github/workflows/release-please.yml` - Automated release workflow

### Version Tracking Files

- ✅ `apps/tinyolly/VERSION` → 2.2.2
- ✅ `.release-please-manifest.json` - Single source of truth for all versions
- ✅ `charts/tinyolly/Chart.yaml` → appVersion synced from manifest
- ✅ `charts/tinyolly-demos/Chart.yaml` → appVersion synced from manifest
- ✅ `charts/tinyolly-demo-otel-agent/Chart.yaml` → appVersion synced from manifest

### Documentation & Scripts

- ✅ `docs/release-process.md` - Complete usage guide
- ✅ `scripts/release/validate-commit-msg.sh` - Commit message validation
- ❌ `VERSION` files - **REMOVED** - versions managed only by release-please manifest

## How It Works

### 1. Developer Workflow

```bash
# Make changes and commit with conventional commits
git commit -m "feat(tinyolly): add new feature"
git push origin main
```

### 2. Automatic Release PR

- Release-please analyzes commits since last release
- Creates/updates a **single PR** with all version bumps
- Updates VERSION files, CHANGELOG.md, Chart.yaml files
- PR shows exactly what will be released

### 3. Merge Release PR

- Merging triggers automated builds
- Container images built and pushed to GHCR
- Helm charts packaged and pushed to OCI registry
- GitHub releases created with changelogs

## Component Versioning

| Component            | Type   | Version | Tag Format                    |
| -------------------- | ------ | ------- | ----------------------------- |
| tinyolly             | Python | 2.2.2   | `tinyolly-v2.2.2`             |
| opamp-server         | Go     | 1.0.0   | `opamp-server-v1.0.0`         |
| demo                 | Python | 0.5.0   | `demo-v0.5.0`                 |
| demo-otel-agent      | Python | 0.3.0   | `demo-otel-agent-v0.3.0`      |
| helm-tinyolly        | Helm   | 0.1.1   | `helm-tinyolly-v0.1.1`        |
| helm-demos           | Helm   | 0.1.5   | `helm-demos-v0.1.5`           |
| helm-demo-otel-agent | Helm   | 0.1.0   | `helm-demo-otel-agent-v0.1.0` |

## Conventional Commit Examples

```bash
# Container releases
feat(tinyolly): add GenAI span filtering        # tinyolly 2.2.2 → 2.3.0
fix(opamp): handle nil pointer                   # opamp 1.0.0 → 1.0.1
perf(demo): optimize query performance           # demo 0.5.0 → 0.5.1

# Helm chart releases
feat(helm/tinyolly): add ingress annotations     # helm-tinyolly 0.1.1 → 0.2.0
fix(helm/demos): correct service port            # helm-demos 0.1.5 → 0.1.6

# Breaking changes
feat(ai-agent)!: migrate to Ollama 2.0          # ai-agent 0.3.0 → 1.0.0

# Multi-component (triggers coordinated release)
feat(tinyolly,opamp): add mutual TLS            # Both bump, chart bumps once

# No release
docs: update README                              # No version bump
ci: fix workflow syntax                          # No version bump
```

## Dependency Coordination

When container images are released, their dependent Helm charts **automatically update**:

```
feat(tinyolly): new feature
feat(opamp): new feature
  ↓
tinyolly: 2.2.2 → 2.3.0
opamp-server: 1.0.0 → 1.1.0
  ↓
helm-tinyolly: 0.1.1 → 0.2.0 (SINGLE release)
  - values.yaml updated with both new image versions
  - appVersion set to v2.3.0 (tinyolly version)
```

## GitHub Workflow

### On Push to Main

1. `release-please.yml` workflow runs
2. Analyzes commits for conventional commit patterns
3. Creates/updates release PR

### When Release PR is Merged

1. **Container builds** - Parallel builds for changed components
   - Multi-arch (amd64/arm64)
   - Pushed to `ghcr.io/tinyolly/*`
   - Tagged with version + `:latest`

2. **Helm charts** - Sequential after container builds
   - Updates values.yaml with new image versions
   - Packages chart
   - Pushes to `oci://ghcr.io/tinyolly/charts`

3. **GitHub Releases** - Created for each component
   - Release notes from CHANGELOG
   - Tagged appropriately

## Local Development

Local development is **unchanged** - use existing scripts:

```bash
# Local KIND cluster builds (bypass release-please)
cd charts
./build-and-push-local.sh v2.3.0-my-feature

# Manual image builds
cd scripts/build
./02-build-all.sh local-test
```

Local builds don't update VERSION files or trigger releases.

## Next Steps

### Immediate

1. ✅ Test by making a conventional commit to main
2. ✅ Review generated release PR
3. ✅ Verify version bumps are correct
4. ✅ Merge release PR and verify builds

### Optional Enhancements

- [ ] Install commitlint pre-commit hook (enforce conventional commits)
- [ ] Add GitHub branch protection to require conventional commit format
- [ ] Set up commit message template for git
- [ ] Add release badges to README
- [ ] Configure release notifications (Slack, Discord, etc.)

### Migration from Old Process

- [ ] Document old release workflow is deprecated
- [ ] Update team documentation
- [ ] Train team on conventional commits
- [ ] Archive old `.github/workflows/release.yml`

## Testing the Implementation

```bash
# 1. Make a test change with conventional commit
git checkout -b test-release-please
echo "# Test" >> README.md
git add README.md
git commit -m "docs: test release-please setup"
git push origin test-release-please

# 2. Create PR and merge to main
# 3. Check Actions tab for release-please workflow
# 4. Review generated release PR
# 5. Merge release PR and verify builds
```

## Benefits

✅ **Automated versioning** - No manual version bumps  
✅ **Single release PR** - All components in one place  
✅ **Coordinated releases** - Charts update when containers change  
✅ **Auto-generated changelogs** - Per component  
✅ **Parallel builds** - Fast CI pipeline  
✅ **GitHub releases** - Professional release notes  
✅ **Future-proof** - Easy to add new components  
✅ **Local dev preserved** - Existing workflows still work

## References

- [Release Please Docs](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [TinyOlly Release Process](./release-process.md) - Detailed guide
