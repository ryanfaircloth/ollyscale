# TinyOlly Release Process

TinyOlly uses [release-please](https://github.com/googleapis/release-please) for automated releases in our monorepo.

## How It Works

1. **Make changes** using [Conventional Commits](https://www.conventionalcommits.org/)
2. **Merge to main** - release-please creates/updates a release PR automatically
3. **Review release PR** - check versions, changelogs, and changes
4. **Merge release PR** - triggers automated builds and releases

## Conventional Commit Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types (determine version bump)

- `feat:` - New feature (minor version bump)
- `fix:` - Bug fix (patch version bump)
- `perf:` - Performance improvement (patch version bump)
- `docs:` - Documentation only (no release)
- `style:` - Code style changes (no release)
- `refactor:` - Code refactoring (patch version bump if in scope)
- `test:` - Test changes (no release)
- `build:` - Build system changes (no release)
- `ci:` - CI configuration changes (no release)
- `chore:` - Other changes (no release)

**Breaking Changes**: Add `!` after type or `BREAKING CHANGE:` in footer for major version bump

### Scopes (optional but recommended)

**Container Components:**

- `tinyolly` - Core platform (apps/tinyolly)
- `opamp` - OpAMP server (apps/opamp-server)
- `demo` - Demo application (apps/demo)
- `ai-agent` - AI agent demo (apps/ai-agent-demo)

**Helm Charts:**

- `helm/tinyolly` - Main platform chart
- `helm/demos` - Demos chart
- `helm/ai-agent` - AI agent chart

**General:**

- `deps` - Dependency updates
- `*` - Multiple components (use sparingly)

## Examples

### Container Changes

```bash
# New feature in tinyolly (minor bump: 2.2.2 → 2.3.0)
feat(tinyolly): add GenAI span filtering

# Bug fix in opamp-server (patch bump: 1.0.0 → 1.0.1)
fix(opamp): handle nil pointer in config validation

# Performance improvement (patch bump)
perf(demo): optimize database query for metrics

# Breaking change (major bump: 0.3.0 → 1.0.0)
feat(ai-agent)!: migrate to Ollama 2.0 API

BREAKING CHANGE: Ollama 1.x no longer supported
```

### Helm Chart Changes

```bash
# New chart feature (minor bump)
feat(helm/tinyolly): add PVC for persistent storage

# Chart bug fix (patch bump)
fix(helm/demos): correct service port configuration

# Chart breaking change (major bump)
feat(helm/tinyolly)!: require Kubernetes 1.28+

BREAKING CHANGE: Dropped support for Kubernetes < 1.28
```

### Multi-Component Changes

```bash
# Affects both containers and triggers chart update
feat(tinyolly,opamp): add mutual TLS authentication

# Multiple charts
docs(helm/tinyolly,helm/demos): update README with examples
```

### No Release Examples

```bash
# Documentation only
docs: update API documentation

# CI changes
ci: add workflow for dependency updates

# Test changes
test(tinyolly): add integration tests for filtering

# Build changes
build: update base Python image to 3.12
```

## Release PR Workflow

### When Changes Are Pushed to Main

1. Release-please analyzes commits since last release
2. Determines which components need version bumps
3. Creates/updates a **single release PR** with:
   - Updated `.release-please-manifest.json` (single source of truth)
   - Updated CHANGELOG.md for each component
   - Updated Chart.yaml versions for Helm charts
   - All changes in one PR

### Example Release PR

```
Title: chore: release main

Components to be released:
- tinyolly: 2.2.2 → 2.3.0
- opamp-server: 1.0.0 → 1.0.1
- helm-tinyolly: 0.1.1 → 0.2.0

Changes:
- Updated apps/tinyolly/VERSION
- Updated apps/tinyolly/CHANGELOG.md
- Updated apps/opamp-server/VERSION
- Updated apps/opamp-server/CHANGELOG.md
- Updated charts/tinyolly/Chart.yaml
- Updated charts/tinyolly/CHANGELOG.md
```

### When Release PR Is Merged

1. **GitHub releases** created for each component with tags:
   - `tinyolly-v2.3.0`
   - `opamp-server-v1.0.1`
   - `helm-tinyolly-v0.2.0`

2. **Container images** built and pushed:
   - `ghcr.io/tinyolly/tinyolly:v2.3.0` (+ `:latest`)
   - `ghcr.io/tinyolly/opamp-server:v1.0.1` (+ `:latest`)

3. **Helm charts** packaged and pushed:
   - `oci://ghcr.io/tinyolly/charts/tinyolly:0.2.0`
   - Chart's `values.yaml` updated with new image versions

## Version Strategy

### Container Images

Each container maintains independent semantic versioning:

```
tinyolly:         v2.3.0
opamp-server:     v1.0.1
demo:             v0.5.2
ai-agent-demo:    v0.3.1
```

### Helm Charts

Charts have two version fields:

- **`version`**: Chart's semantic version (no 'v' prefix)
- **`appVersion`**: Version of primary application

**Release triggers:**

- Direct changes to chart files
- Dependency container version bumps
- Manual version bump in manifest

## Local Development

Local development builds **bypass release-please**:

```bash
# Build for local KIND cluster (no version tracking)
cd charts
./build-and-push-local.sh v2.3.0-my-feature

# Or use existing build scripts
cd scripts/build
./02-build-all.sh local-test
```

Local builds:

- Use custom version tags (e.g., `local-`, feature names)
- Push only to local registry
- Don't update manifest (versions managed by release-please only)
- Don't trigger releases

## Manual Version Bumps

If you need to force a version bump without code changes:

```bash
# Update manifest file
vim .release-please-manifest.json

# Change version for component:
{
  "apps/tinyolly": "2.3.0",  # Bump this
  ...
}

# Commit with chore type (won't trigger another bump)
git add .release-please-manifest.json
git commit -m "chore: bump tinyolly to v2.3.0"
git push origin main
```

## Coordinated Releases

### Scenario: Both tinyolly and opamp-server updated

```bash
# Commit 1
feat(tinyolly): add TLS support

# Commit 2
feat(opamp): add TLS configuration endpoint

# Result: Single release PR with:
# - tinyolly: 2.2.2 → 2.3.0
# - opamp-server: 1.0.0 → 1.1.0
# - helm-tinyolly: 0.1.1 → 0.2.0 (dependency bump)
```

Release-please automatically:

- Bumps both containers
- Bumps helm chart once (not twice)
- Updates chart's values.yaml with both new image versions

## Troubleshooting

### Release PR not created

- Check commit messages follow conventional commits
- Verify commits have releasable types (`feat`, `fix`, `perf`)
- Check `.release-please-manifest.json` has correct initial versions

### Wrong version bump

- Check commit type (`feat` = minor, `fix` = patch)
- Verify `BREAKING CHANGE` in footer for major bumps
- Look at release PR description for bump reasoning

### Container not building after release

- Check workflow logs in Actions tab
- Verify Dockerfile exists and is correct
- Check GHCR permissions

### Helm chart has wrong image versions

- Check `.release-please-manifest.json` for correct versions
- Verify `values.yaml` structure matches workflow expectations
- Ensure workflow's `yq` commands reference manifest correctly

## Best Practices

1. **One logical change per commit** - easier to review and revert
2. **Use descriptive scopes** - helps track which components changed
3. **Write clear descriptions** - these become CHANGELOG entries
4. **Test before merging to main** - releases are automatic
5. **Review release PR carefully** - check all versions and changelogs
6. **Keep breaking changes to majors** - minimize disruption

## Tools

### Commitlint (optional)

Enforce conventional commits with pre-commit hooks:

```bash
npm install -g @commitlint/cli @commitlint/config-conventional
echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js

# Add to .git/hooks/commit-msg or use husky
```

### Commit Message Templates

```bash
# Set git template
git config commit.template .gitmessage

# .gitmessage content:
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>
#
# Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
# Scopes: tinyolly, opamp, demo, ai-agent, helm/tinyolly, helm/demos, helm/ai-agent
```

## Migration from Current Process

1. ✅ Release-please configured
2. ✅ **VERSION files removed** (manifest is single source of truth)
3. ✅ Manifest initialized with current versions
4. ✅ GitHub Actions workflow created
5. ✅ Team documentation updated
6. ✅ Conventional commits in use
7. ✅ Multiple successful releases completed
8. ✅ Old release workflow deprecated

## References

- [Release Please Documentation](https://github.com/googleapis/release-please)
- [Conventional Commits Spec](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
