# TinyOlly Semantic Release Strategy Proposal

## Overview

This proposal outlines a comprehensive semantic release strategy for TinyOlly's multi-component architecture using semantic commits, automated versioning, and intelligent dependency-triggered releases.

## Current State

### Components

- **Container Images:**
  - `tinyolly` (unified UI + OTLP receiver) - Core platform
  - `opamp-server` (Go) - Agent management server
  - `demo` - Unified demo application
  - `ai-agent-demo` - AI/LLM demo application

- **Helm Charts:**
  - `tinyolly` - Main platform chart (depends on tinyolly + opamp-server images)
  - `tinyolly-demos` - Demo applications chart (depends on demo image)
  - `tinyolly-ai-agent` - AI agent chart (depends on ai-agent-demo image)

### Current Issues

- Manual versioning across all components
- No automated changelog generation
- Helm charts don't track their dependency versions properly
- No coordination between component releases and dependent releases
- Local dev scripts mix version management with builds

---

## Proposed Solution

### Architecture Principles

1. **Independent Component Versioning**: Each component (container or chart) maintains its own semantic version
2. **Dependency-Aware Releases**: Changes trigger automatic releases of dependent components
3. **Monorepo Structure**: Use semantic-release in monorepo mode with workspace plugins
4. **Conventional Commits**: Enforce semantic commit format for automatic version bumping
5. **Automated Changelogs**: Generate CHANGELOG.md per component from commit history

### Component Versioning Strategy

#### Container Images

Each container image follows semantic versioning independently:

```
tinyolly:          v2.3.0 → v2.4.0 (feat commit)
opamp-server:      v1.2.1 → v1.2.2 (fix commit)
demo:              v0.5.0 → v0.6.0 (feat commit)
ai-agent-demo:     v0.3.0 → v0.3.0 (no changes)
```

**Version Format**: `v{major}.{minor}.{patch}`
**Tags**: Container images tagged with full version (e.g., `ghcr.io/tinyolly/tinyolly:v2.4.0`)

#### Helm Charts

Helm charts have **two version fields**:

- **`version`**: Chart's own semantic version (no 'v' prefix per Helm spec)
- **`appVersion`**: Version of the primary application container(s)

**Versioning Rules:**

1. **tinyolly chart**:
   - `version`: Independent semantic version (e.g., `2.1.0`)
   - `appVersion`: Matches tinyolly container version (e.g., `v2.4.0`)
   - Auto-bumps when: tinyolly OR opamp-server images change, OR chart files change
   - Bump type: Highest of (dependent container bump, own changes bump)

2. **tinyolly-demos chart**:
   - `version`: Independent semantic version
   - `appVersion`: Matches demo container version
   - Auto-bumps when: demo image changes OR chart files change

3. **tinyolly-ai-agent chart**:
   - `version`: Independent semantic version
   - `appVersion`: Matches ai-agent-demo container version
   - Auto-bumps when: ai-agent-demo image changes OR chart files change

**Example Flow:**

```
# Scenario: tinyolly gets feat commit, opamp-server gets fix commit

1. tinyolly container:    v2.3.0 → v2.4.0 (feat)
2. opamp-server container: v1.2.1 → v1.2.2 (fix)
3. tinyolly chart:         2.0.5 → 2.1.0 (feat - highest bump from dependencies)
   - appVersion: v2.4.0 (latest tinyolly)
   - Update values.yaml with both image versions
   - Single release triggered despite 2 dependency changes
```

### Directory Structure

```
/
├── .github/
│   ├── workflows/
│   │   ├── semantic-release.yml         # Main orchestration workflow
│   │   ├── build-containers.yml         # Reusable container build workflow
│   │   ├── release-helm-chart.yml       # Reusable Helm chart workflow
│   │   └── test.yml                     # Existing test workflow
│   └── ...
├── .releaserc.js                        # Root semantic-release config
├── apps/
│   ├── tinyolly/
│   │   ├── .releaserc.js               # Component-specific config
│   │   ├── CHANGELOG.md                # Auto-generated
│   │   ├── package.json                # Version tracking
│   │   └── ...
│   ├── opamp-server/
│   │   ├── .releaserc.js
│   │   ├── CHANGELOG.md
│   │   ├── package.json
│   │   └── ...
│   ├── demo/
│   │   ├── .releaserc.js
│   │   ├── CHANGELOG.md
│   │   ├── package.json
│   │   └── ...
│   └── ai-agent-demo/
│       ├── .releaserc.js
│       ├── CHANGELOG.md
│       ├── package.json
│       └── ...
├── charts/
│   ├── tinyolly/
│   │   ├── .releaserc.js
│   │   ├── CHANGELOG.md
│   │   ├── package.json                # Version + dependency tracking
│   │   ├── Chart.yaml
│   │   └── ...
│   ├── tinyolly-demos/
│   │   ├── .releaserc.js
│   │   ├── CHANGELOG.md
│   │   ├── package.json
│   │   └── ...
│   └── tinyolly-ai-agent/
│       ├── .releaserc.js
│       ├── CHANGELOG.md
│       ├── package.json
│       └── ...
└── scripts/
    └── release/
        ├── update-chart-versions.js     # Updates Chart.yaml with new versions
        ├── check-dependencies.js        # Determines if chart needs release
        └── ...
```

### Semantic Commit Format

**Required format**: `<type>(<scope>): <subject>`

**Types** (determines version bump):

- `feat`: Minor version bump (new feature)
- `fix`: Patch version bump (bug fix)
- `perf`: Patch version bump (performance improvement)
- `BREAKING CHANGE`: Major version bump (in footer)
- `docs`, `style`, `refactor`, `test`, `chore`: No version bump

**Scopes** (determines which components release):

- `tinyolly`: Changes to apps/tinyolly
- `opamp`: Changes to apps/opamp-server
- `demo`: Changes to apps/demo
- `ai-agent`: Changes to apps/ai-agent-demo
- `helm/tinyolly`: Changes to charts/tinyolly
- `helm/demos`: Changes to charts/tinyolly-demos
- `helm/ai-agent`: Changes to charts/tinyolly-ai-agent

**Examples:**

```bash
# Releases tinyolly container v2.4.0, triggers tinyolly chart release
feat(tinyolly): add GenAI span filtering

# Releases opamp-server v1.2.2, triggers tinyolly chart release
fix(opamp): handle nil pointer in config validation

# Releases demo container v0.6.0, triggers tinyolly-demos chart release
feat(demo)!: rewrite frontend with new API

BREAKING CHANGE: Demo API endpoints changed to /v2/

# Releases tinyolly chart only (no container changes)
feat(helm/tinyolly): add ingress annotations for rate limiting

# Multi-component change (single commit can affect multiple scopes)
feat(tinyolly,opamp): add mutual TLS support

# Releases both containers, triggers single tinyolly chart release
```

### Workflow Architecture

#### 1. Main Orchestration Workflow (`semantic-release.yml`)

Triggered on: `push` to `main` branch

```yaml
name: Semantic Release

on:
  push:
    branches:
      - main

jobs:
  # Phase 1: Determine what changed
  analyze:
    runs-on: ubuntu-latest
    outputs:
      tinyolly_changed: ${{ steps.changes.outputs.tinyolly }}
      opamp_changed: ${{ steps.changes.outputs.opamp }}
      demo_changed: ${{ steps.changes.outputs.demo }}
      ai_agent_changed: ${{ steps.changes.outputs.ai_agent }}
      chart_tinyolly_changed: ${{ steps.changes.outputs.chart_tinyolly }}
      chart_demos_changed: ${{ steps.changes.outputs.chart_demos }}
      chart_ai_agent_changed: ${{ steps.changes.outputs.chart_ai_agent }}
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0 # Full history for semantic-release

      - name: Detect changed paths
        id: changes
        uses: dorny/paths-filter@v3
        with:
          filters: |
            tinyolly:
              - 'apps/tinyolly/**'
            opamp:
              - 'apps/opamp-server/**'
            demo:
              - 'apps/demo/**'
            ai_agent:
              - 'apps/ai-agent-demo/**'
            chart_tinyolly:
              - 'charts/tinyolly/**'
            chart_demos:
              - 'charts/tinyolly-demos/**'
            chart_ai_agent:
              - 'charts/tinyolly-ai-agent/**'

  # Phase 2: Release containers (parallel)
  release-tinyolly:
    needs: analyze
    if: needs.analyze.outputs.tinyolly_changed == 'true'
    uses: ./.github/workflows/release-container.yml
    with:
      component: tinyolly
      context: apps/tinyolly
      dockerfile: apps/tinyolly/Dockerfile
      image_name: tinyolly/tinyolly
    secrets: inherit

  release-opamp:
    needs: analyze
    if: needs.analyze.outputs.opamp_changed == 'true'
    uses: ./.github/workflows/release-container.yml
    with:
      component: opamp-server
      context: apps/opamp-server
      dockerfile: apps/opamp-server/Dockerfile
      image_name: tinyolly/opamp-server
    secrets: inherit

  release-demo:
    needs: analyze
    if: needs.analyze.outputs.demo_changed == 'true'
    uses: ./.github/workflows/release-container.yml
    with:
      component: demo
      context: apps/demo
      dockerfile: apps/demo/Dockerfile
      image_name: tinyolly/demo
    secrets: inherit

  release-ai-agent:
    needs: analyze
    if: needs.analyze.outputs.ai_agent_changed == 'true'
    uses: ./.github/workflows/release-container.yml
    with:
      component: ai-agent-demo
      context: apps/ai-agent-demo
      dockerfile: apps/ai-agent-demo/Dockerfile
      image_name: tinyolly/ai-agent-demo
    secrets: inherit

  # Phase 3: Release Helm charts (depends on container releases)
  release-chart-tinyolly:
    needs: [release-tinyolly, release-opamp]
    if: |
      always() &&
      (needs.analyze.outputs.tinyolly_changed == 'true' ||
       needs.analyze.outputs.opamp_changed == 'true' ||
       needs.analyze.outputs.chart_tinyolly_changed == 'true')
    uses: ./.github/workflows/release-helm-chart.yml
    with:
      chart: tinyolly
      depends_on: "tinyolly,opamp-server"
    secrets: inherit

  release-chart-demos:
    needs: [release-demo]
    if: |
      always() &&
      (needs.analyze.outputs.demo_changed == 'true' ||
       needs.analyze.outputs.chart_demos_changed == 'true')
    uses: ./.github/workflows/release-helm-chart.yml
    with:
      chart: tinyolly-demos
      depends_on: "demo"
    secrets: inherit

  release-chart-ai-agent:
    needs: [release-ai-agent]
    if: |
      always() &&
      (needs.analyze.outputs.ai_agent_changed == 'true' ||
       needs.analyze.outputs.chart_ai_agent_changed == 'true')
    uses: ./.github/workflows/release-helm-chart.yml
    with:
      chart: tinyolly-ai-agent
      depends_on: "ai-agent-demo"
    secrets: inherit
```

#### 2. Reusable Container Release Workflow

```yaml
# .github/workflows/release-container.yml
name: Release Container

on:
  workflow_call:
    inputs:
      component:
        required: true
        type: string
      context:
        required: true
        type: string
      dockerfile:
        required: true
        type: string
      image_name:
        required: true
        type: string
    outputs:
      version:
        description: "Released version"
        value: ${{ jobs.release.outputs.version }}

jobs:
  release:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.semantic.outputs.new_release_version }}
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install semantic-release
        run: |
          npm install -g semantic-release \
            @semantic-release/git \
            @semantic-release/changelog \
            @semantic-release/github \
            @semantic-release/exec

      - name: Run semantic-release
        id: semantic
        working-directory: ${{ inputs.context }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          npx semantic-release
          echo "new_release_version=$(cat package.json | jq -r '.version')" >> $GITHUB_OUTPUT

      - name: Set up QEMU
        if: steps.semantic.outputs.new_release_version != ''
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        if: steps.semantic.outputs.new_release_version != ''
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        if: steps.semantic.outputs.new_release_version != ''
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        if: steps.semantic.outputs.new_release_version != ''
        uses: docker/build-push-action@v6
        with:
          context: ${{ inputs.context }}
          file: ${{ inputs.dockerfile }}
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ghcr.io/${{ inputs.image_name }}:v${{ steps.semantic.outputs.new_release_version }}
            ghcr.io/${{ inputs.image_name }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

#### 3. Reusable Helm Chart Release Workflow

```yaml
# .github/workflows/release-helm-chart.yml
name: Release Helm Chart

on:
  workflow_call:
    inputs:
      chart:
        required: true
        type: string
      depends_on:
        required: true
        type: string # Comma-separated list of container components

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Setup Helm
        uses: azure/setup-helm@v4

      - name: Get dependency versions
        id: deps
        run: |
          # Read versions from released container package.json files
          # Set outputs for each dependency
          node scripts/release/get-dependency-versions.js \
            --chart=${{ inputs.chart }} \
            --depends-on="${{ inputs.depends_on }}"

      - name: Update Chart.yaml with dependency versions
        run: |
          node scripts/release/update-chart-versions.js \
            --chart=${{ inputs.chart }} \
            --versions="${{ steps.deps.outputs.versions }}"

      - name: Install semantic-release
        run: |
          npm install -g semantic-release \
            @semantic-release/git \
            @semantic-release/changelog \
            @semantic-release/github \
            @semantic-release/exec

      - name: Run semantic-release for chart
        working-directory: charts/${{ inputs.chart }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          npx semantic-release

      - name: Package and push Helm chart
        run: |
          VERSION=$(cat charts/${{ inputs.chart }}/Chart.yaml | grep '^version:' | awk '{print $2}')

          cd charts
          helm package ${{ inputs.chart }}

          echo ${{ secrets.GITHUB_TOKEN }} | helm registry login ghcr.io \
            -u ${{ github.actor }} --password-stdin

          helm push ${{ inputs.chart }}-${VERSION}.tgz \
            oci://ghcr.io/tinyolly/charts
```

### Semantic Release Configuration

#### Container Component `.releaserc.js`

Example for `apps/tinyolly/.releaserc.js`:

```javascript
module.exports = {
  branches: ["main"],
  tagFormat: "tinyolly-v${version}",
  plugins: [
    [
      "@semantic-release/commit-analyzer",
      {
        preset: "conventionalcommits",
        releaseRules: [
          { type: "feat", release: "minor" },
          { type: "fix", release: "patch" },
          { type: "perf", release: "patch" },
          { type: "refactor", scope: "tinyolly", release: "patch" },
        ],
      },
    ],
    [
      "@semantic-release/release-notes-generator",
      {
        preset: "conventionalcommits",
        presetConfig: {
          types: [
            { type: "feat", section: "Features" },
            { type: "fix", section: "Bug Fixes" },
            { type: "perf", section: "Performance" },
            { type: "refactor", section: "Refactoring", hidden: false },
            { type: "docs", section: "Documentation", hidden: false },
          ],
        },
      },
    ],
    "@semantic-release/changelog",
    [
      "@semantic-release/npm",
      {
        npmPublish: false, // We only use package.json for version tracking
      },
    ],
    [
      "@semantic-release/git",
      {
        assets: ["package.json", "CHANGELOG.md"],
        message: "chore(release): tinyolly ${nextRelease.version}\n\n${nextRelease.notes}",
      },
    ],
    [
      "@semantic-release/github",
      {
        successComment: false,
        releasedLabels: false,
      },
    ],
  ],
};
```

#### Helm Chart `.releaserc.js`

Example for `charts/tinyolly/.releaserc.js`:

```javascript
module.exports = {
  branches: ["main"],
  tagFormat: "helm-tinyolly-v${version}",
  plugins: [
    [
      "@semantic-release/commit-analyzer",
      {
        preset: "conventionalcommits",
        releaseRules: [
          // Trigger release on dependency updates (handled by update-chart-versions.js)
          { message: "*deps(helm/tinyolly)*", release: "minor" },
          { type: "feat", scope: "helm/tinyolly", release: "minor" },
          { type: "fix", scope: "helm/tinyolly", release: "patch" },
        ],
      },
    ],
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    [
      "@semantic-release/exec",
      {
        prepareCmd: "node ../../scripts/release/sync-chart-version.js ${nextRelease.version}",
      },
    ],
    [
      "@semantic-release/npm",
      {
        npmPublish: false,
      },
    ],
    [
      "@semantic-release/git",
      {
        assets: ["package.json", "Chart.yaml", "values.yaml", "CHANGELOG.md"],
        message: "chore(release): helm/tinyolly ${nextRelease.version}\n\n${nextRelease.notes}",
      },
    ],
    [
      "@semantic-release/github",
      {
        successComment: false,
      },
    ],
  ],
};
```

### Helper Scripts

#### `scripts/release/update-chart-versions.js`

```javascript
#!/usr/bin/env node
const fs = require("fs");
const yaml = require("js-yaml");

// Read dependency versions and update Chart.yaml + values.yaml
// Usage: node update-chart-versions.js --chart=tinyolly --versions='{"tinyolly":"v2.4.0","opamp-server":"v1.2.2"}'

const args = process.argv.slice(2).reduce((acc, arg) => {
  const [key, value] = arg.split("=");
  acc[key.replace("--", "")] = value;
  return acc;
}, {});

const chartPath = `charts/${args.chart}`;
const versions = JSON.parse(args.versions);

// Update Chart.yaml appVersion
const chartYaml = yaml.load(fs.readFileSync(`${chartPath}/Chart.yaml`, "utf8"));
const primaryComponent = Object.keys(versions)[0];
chartYaml.appVersion = versions[primaryComponent];
fs.writeFileSync(`${chartPath}/Chart.yaml`, yaml.dump(chartYaml));

// Update values.yaml image tags
let valuesYaml = fs.readFileSync(`${chartPath}/values.yaml`, "utf8");
for (const [component, version] of Object.entries(versions)) {
  // Update image tags for each component
  const componentKey = component.replace("-", "_");
  valuesYaml = valuesYaml.replace(
    new RegExp(`(${componentKey}:\\s*\\n\\s*image:\\s*\\n.*?tag:\\s*).*`, "g"),
    `$1"${version}"`
  );
}
fs.writeFileSync(`${chartPath}/values.yaml`, valuesYaml);

console.log(`Updated ${args.chart} with versions:`, versions);
```

### Local Development Workflow

Local dev scripts **bypass semantic-release** for rapid iteration:

```bash
# Current behavior preserved:
cd charts
./build-and-push-local.sh v2.2.0-my-feature

# Or build all for local testing:
cd scripts/build
./02-build-all.sh local-test
```

Local builds:

- Use `local-` prefix or custom tags
- Push to local registry only
- Do NOT trigger semantic-release or update version files
- Suitable for KIND cluster testing

### Migration Plan

#### Phase 1: Setup (Week 1)

1. Add `package.json` to all component directories (containers + charts)
2. Create `.releaserc.js` for each component
3. Add helper scripts in `scripts/release/`
4. Update `.github/workflows/` with new workflow files
5. Add `commitlint` config for commit message validation

#### Phase 2: Documentation (Week 1)

1. Update `CONTRIBUTING.md` with semantic commit guidelines
2. Document release process in `docs/release-process.md`
3. Add commit message examples and tooling recommendations
4. Set up pre-commit hooks for commit message validation

#### Phase 3: Dry Run (Week 2)

1. Run semantic-release with `--dry-run` flag
2. Verify version bumps and changelogs
3. Test container builds and Helm chart packaging
4. Validate dependency resolution logic

#### Phase 4: Gradual Rollout (Week 2-3)

1. Enable for `tinyolly` container first
2. Enable for `opamp-server` container
3. Enable for demo containers
4. Enable for Helm charts with full dependency tracking
5. Deprecate manual release workflow

#### Phase 5: Enforcement (Week 4)

1. Make semantic commits required via GitHub branch protection
2. Archive old build scripts (keep for reference)
3. Update all documentation to reference new process
4. Train team on semantic commit practices

### Benefits

1. **Automated Versioning**: No manual version bumps, semantic commits drive everything
2. **Coordinated Releases**: Helm charts automatically track container versions
3. **Single Release Per Change**: Multiple container updates trigger one chart release
4. **Comprehensive Changelogs**: Auto-generated from commits per component
5. **Parallel Builds**: Container images build simultaneously (faster CI)
6. **Dependency Tracking**: Charts know exactly which container versions they depend on
7. **Future-Proof**: Easy to add new components (just add directory + config)
8. **Local Dev Unchanged**: Fast iteration with `build-and-push-local.sh` preserved
9. **GitHub Releases**: Automatic release notes for each component
10. **Rollback Support**: Clear version history and dependency tracking

### Rollout Checklist

- [ ] Create `package.json` files for all components
- [ ] Create `.releaserc.js` configurations
- [ ] Implement `update-chart-versions.js` helper script
- [ ] Implement `get-dependency-versions.js` helper script
- [ ] Create new GitHub Actions workflows
- [ ] Add commitlint configuration
- [ ] Update documentation (CONTRIBUTING.md, release-process.md)
- [ ] Set up pre-commit hooks repository
- [ ] Dry run semantic-release on test branch
- [ ] Enable for `apps/tinyolly` (pilot)
- [ ] Enable for remaining containers
- [ ] Enable for Helm charts with dependency tracking
- [ ] Configure GitHub branch protection rules
- [ ] Team training on semantic commits
- [ ] Archive old release scripts
- [ ] Monitor first production releases

### Tools & Dependencies

```json
{
  "devDependencies": {
    "semantic-release": "^23.0.0",
    "@semantic-release/changelog": "^6.0.3",
    "@semantic-release/commit-analyzer": "^12.0.0",
    "@semantic-release/git": "^10.0.1",
    "@semantic-release/github": "^10.0.0",
    "@semantic-release/npm": "^12.0.0",
    "@semantic-release/exec": "^6.0.3",
    "@semantic-release/release-notes-generator": "^13.0.0",
    "@commitlint/cli": "^18.0.0",
    "@commitlint/config-conventional": "^18.0.0",
    "husky": "^9.0.0",
    "js-yaml": "^4.1.0"
  }
}
```

### Appendix: Semantic Commit Cheat Sheet

```bash
# Features (minor bump)
feat(tinyolly): add span filtering API
feat(helm/tinyolly): add PVC for persistent storage

# Bug fixes (patch bump)
fix(opamp): correct nil pointer dereference
fix(demo): resolve race condition in metrics

# Breaking changes (major bump)
feat(tinyolly)!: migrate to OTLP 1.0 protocol

BREAKING CHANGE: Old OTLP 0.x clients not supported

# Performance improvements (patch bump)
perf(tinyolly): optimize Redis connection pooling

# Refactoring (patch bump with scope filter)
refactor(tinyolly): extract storage layer to separate package

# No release (documentation, tests, chores)
docs: update API documentation
test(tinyolly): add integration tests for span storage
chore: update dependencies
ci: fix release workflow syntax

# Multi-scope (releases multiple components)
feat(tinyolly,opamp): add mutual TLS authentication
```
