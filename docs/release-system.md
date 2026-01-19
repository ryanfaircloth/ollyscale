# Release System Documentation

## Overview

This project uses [release-please](https://github.com/googleapis/release-please) with a custom fork that
supports the `bumpDependents` feature for managing cross-component version dependencies.

## Architecture

### Components

The repository contains multiple components that are released independently:

**Applications (Container Images):**

- `apps/ollyscale` - Python backend → `ghcr.io/ryanfaircloth/ollyscale/ollyscale`
- `apps/ollyscale-ui` - TypeScript frontend → `ghcr.io/ryanfaircloth/ollyscale/ollyscale-ui`
- `apps/opamp-server` - Go OpAMP server → `ghcr.io/ryanfaircloth/ollyscale/opamp-server`
- `apps/demo` - Demo application → `ghcr.io/ryanfaircloth/ollyscale/demo`
- `apps/demo-otel-agent` - Demo OTel agent → `ghcr.io/ryanfaircloth/ollyscale/demo-otel-agent`

**Helm Charts:**

- `charts/ollyscale` - Main application chart → `ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale`
- `charts/ollyscale-demos` - Demo charts → `ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale-demos`
- `charts/ollyscale-otel-agent` - OTel agent chart → `ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale-otel-agent`

### Dependency Management with bumpDependents

The `bumpDependents` feature automatically bumps the Helm chart version when any of its application
dependencies are released. This is configured in `release-please-config.json`:

```json
{
  "charts/ollyscale": {
    "extra-files": [
      {
        "type": "yaml",
        "path": "charts/ollyscale/values.yaml",
        "jsonpath": "$.frontend.image.tag",
        "component": "ollyscale",
        "bumpDependents": true
      }
    ]
  }
}
```

When `apps/ollyscale` gets a new release:

1. The app's version is bumped (e.g., `v2.1.9` → `v2.1.10`)
2. The app updates `charts/ollyscale/values.yaml` with `frontend.image.tag: v2.1.10`
3. The chart detects this change via `bumpDependents: true`
4. The chart version is automatically bumped (e.g., `0.1.0` → `0.1.1`)

## Release Workflow

### Supported Branches

The release-please workflow triggers on pushes to these branches:

- **`main`** - Stable releases (Docker images tagged with `latest`)
- **`develop`** - Pre-release builds
- **`next-release`** - Pre-release builds for minor version testing
- **`next-release-major`** - Pre-release builds for major version testing

**Pre-release behavior:**

- All branches except `main` produce pre-release builds
- Pre-release Docker images do NOT get the `latest` tag
- GitHub releases marked as pre-releases
- Images labeled with `org.opencontainers.image.prerelease=true`

### Automatic Releases

1. **Commit with Conventional Commit messages** to any supported branch:
   - `feat:` - triggers a minor version bump (0.x.0)
   - `fix:` - triggers a patch version bump (0.0.x)
   - `feat!:` or `BREAKING CHANGE:` - triggers a major version bump (x.0.0)

2. **release-please creates/updates PRs** for each component that has unreleased changes:
   - One PR per component (separate-pull-requests: true)
   - Includes CHANGELOG updates
   - Updates version in package files

3. **Merge the release PR** to trigger the release:
   - Builds and pushes Docker images (multi-platform: amd64/arm64)
   - Packages and publishes Helm charts to OCI registry
   - Creates GitHub releases with notes

### Manual Pre-releases

For testing releases before production:

```bash
# Trigger via GitHub UI or gh CLI on any branch
gh workflow run release-please.yml -f prerelease=true
```

Pre-releases:

- Tagged as pre-release in GitHub
- Docker images do NOT get the `latest` tag
- Useful for testing in staging environments

## Configuration Files

### release-please-config.json

Main configuration file defining:

- Component locations (`packages`)
- Release types (python, node, helm, simple)
- Extra files to update (version files, image tags)
- Dependency relationships (`bumpDependents`)

### .release-please-manifest.json

Tracks the current version of each component. This file is automatically updated by release-please when releases are created.

```json
{
  "apps/ollyscale": "2.1.9",
  "apps/ollyscale-ui": "0.0.0",
  "charts/ollyscale": "0.1.0"
}
```

## Conventional Commit Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**

- `feat`: New feature (minor bump)
- `fix`: Bug fix (patch bump)
- `docs`: Documentation changes (no bump)
- `chore`: Maintenance tasks (no bump)
- `refactor`: Code refactoring (no bump)
- `test`: Test updates (no bump)
- `ci`: CI/CD changes (no bump)

**Scopes (optional):**

- Component names: `ollyscale`, `ollyscale-ui`, `opamp-server`, `chart-ollyscale`
- Functional areas: `api`, `ui`, `storage`, `ingestion`

**Examples:**

```bash
# Feature in ollyscale backend
git commit -m "feat(ollyscale): add span filtering API"

# Fix in UI
git commit -m "fix(ollyscale-ui): correct trace timeline rendering"

# Breaking change
git commit -m "feat(api)!: redesign OTLP ingestion endpoint

BREAKING CHANGE: The OTLP endpoint now requires authentication headers."

# Chart update
git commit -m "feat(chart-ollyscale): add support for external Redis"
```

## Release Tags

Components are tagged with their component name prefix:

- `ollyscale-v2.1.9` - ollyscale backend
- `ollyscale-ui-v1.0.0` - ollyscale UI
- `opamp-server-v1.0.1` - OpAMP server
- `chart-ollyscale-v0.1.0` - ollyscale Helm chart
- `demo-v0.1.0` - Demo application
- `demo-otel-agent-v0.1.0` - Demo OTel agent

## Docker Image Tags

Each release creates multiple Docker image tags:

```text
ghcr.io/ryanfaircloth/ollyscale/ollyscale:2.1.9      # Exact version
ghcr.io/ryanfaircloth/ollyscale/ollyscale:2.1        # Minor version
ghcr.io/ryanfaircloth/ollyscale/ollyscale:2          # Major version
ghcr.io/ryanfaircloth/ollyscale/ollyscale:latest     # Latest (production only)
```

## Helm Chart Publishing

Charts are published to OCI registry:

```bash
# Add the chart repository
helm repo add ollyscale oci://ghcr.io/ryanfaircloth/ollyscale/charts

# Install a specific version
helm install ollyscale oci://ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale --version 0.1.0

# Install latest version
helm install ollyscale oci://ghcr.io/ryanfaircloth/ollyscale/charts/ollyscale
```

## Troubleshooting

### Release PR not created

Check that:

1. Commits follow Conventional Commit format
2. Changes are in the component's directory
3. Commits were pushed to `main` branch

### Chart not bumped when app changes

Verify in `release-please-config.json`:

1. The app component updates the chart's `values.yaml` in its `extra-files`
2. The chart has corresponding entry with `bumpDependents: true`
3. The `component` name matches exactly

### Build failures

Check GitHub Actions logs:

1. Docker build step - may need to fix Dockerfile issues
2. Helm package step - may need to fix Chart.yaml issues
3. Registry push step - check credentials and permissions

## Development Workflow

### Testing Changes Locally

```bash
# Build locally
cd apps/ollyscale
docker build -t ollyscale:dev -f Dockerfile .

# Test Helm chart
cd charts/ollyscale
helm install ollyscale-dev . --values values-local-dev.yaml
```

### Validating Release Configuration

Run the validation checks locally:

```bash
# Validate JSON files
jq empty release-please-config.json
jq empty .release-please-manifest.json

# Check for duplicate components
jq -r '.packages[].component' release-please-config.json | sort | uniq -d

# Verify extra-files exist
jq -r '.packages[] | .["extra-files"][]? | if type == "string" then . else .path end' \
  release-please-config.json | while read -r file; do
  [ -f "$file" ] && echo "✅ $file" || echo "❌ $file"
done
```

## Migration from semantic-release

The old semantic-release system has been replaced with release-please. Key differences:

**semantic-release (old):**

- Single monolithic release for all components
- Required `@anolilab/multi-semantic-release` plugin
- Complex plugin configuration per component
- Released everything together

**release-please (new):**

- Independent releases per component
- Native multi-package support
- Simpler configuration
- `bumpDependents` handles cross-component dependencies
- Separate PRs for better visibility

## References

- [release-please documentation](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Forked release-please with bumpDependents](https://github.com/ryanfaircloth/release-please-action/tree/test/fork-dependency)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Helm OCI Registry](https://helm.sh/docs/topics/registries/)
