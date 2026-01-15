# TinyOlly Versioning Strategy

## Problem Statement

Previously, we used a monorepo approach where:

- All components shared releases via the root package
- Unclear what changed in each release
- Users couldn't assess risk independently per component
- Containers weren't built when only charts were "released"

## Solution: Independent Component Versioning with Separate PRs

### Versioning Model

Each **shipped component** has its own independent version:

```text
apps/tinyolly              → Container: ghcr.io/ryanfaircloth/tinyolly/tinyolly:v38.0.0
apps/tinyolly-ui           → Container: ghcr.io/ryanfaircloth/tinyolly/tinyolly-ui:v1.0.0
apps/opamp-server          → Container: ghcr.io/ryanfaircloth/tinyolly/opamp-server:v3.0.0
apps/demo                  → Container: ghcr.io/ryanfaircloth/tinyolly/demo:v2.0.0
apps/demo-otel-agent       → Container: ghcr.io/ryanfaircloth/tinyolly/demo-otel-agent:v0.3.4

charts/tinyolly            → Helm: oci://ghcr.io/ryanfaircloth/tinyolly/charts/tinyolly:0.3.1
charts/tinyolly-demos      → Helm: oci://ghcr.io/ryanfaircloth/tinyolly/charts/tinyolly-demos:2.0.0
charts/tinyolly-demo-otel-agent → Helm: oci://ghcr.io/ryanfaircloth/tinyolly/charts/tinyolly-demo-otel-agent:0.1.4
```

### Dependency Graph

```text
┌─────────────────┐
│ apps/tinyolly   │────┐
│    v38.0.0      │    │
└─────────────────┘    │
                       │
┌─────────────────┐    │
│ apps/tinyolly-ui│────┼──> charts/tinyolly (v0.3.1)
│    v1.0.0       │    │     References all three dependencies
└─────────────────┘    │
                       │
┌─────────────────┐    │
│ apps/opamp      │────┘
│    v3.0.0       │
└─────────────────┘

┌─────────────────┐
│ apps/demo       │────────> charts/tinyolly-demos (v2.0.0)
│    v2.0.0       │
└─────────────────┘

┌─────────────────┐
│ apps/demo-      │────────> charts/tinyolly-demo-otel-agent (v0.1.4)
│ otel-agent      │
│    v0.3.4       │
└─────────────────┘
```

### Release Workflow

#### Scenario 1: Fix bug in tinyolly backend

1. **Commit**: `fix(backend): resolve span parsing issue`
2. **Release-Please Creates**:
   - PR: `chore: release tinyolly 38.0.1`
   - Updates: `apps/tinyolly/CHANGELOG.md`, `.release-please-manifest.json`
3. **When Merged**:
   - Builds & pushes: `ghcr.io/ryanfaircloth/tinyolly/tinyolly:v38.0.1`
   - **Chart NOT auto-bumped** (chart maintainer decides when to adopt)

#### Scenario 2: Add feature to opamp-server

1. **Commit**: `feat(opamp): add collector config templates`
2. **Release-Please Creates**:
   - PR: `chore: release opamp-server 3.1.0`
3. **When Merged**:
   - Builds & pushes: `ghcr.io/ryanfaircloth/tinyolly/opamp-server:v3.1.0`
   - Chart still references v3.0.0

#### Scenario 3: Update chart to new dependencies

1. **Manual Commit**:

   ```yaml
   # charts/tinyolly/values.yaml
   tinyolly:
     image:
       tag: v38.0.1  # Updated from v38.0.0
   webui:
     image:
       tag: v1.0.0   # Unchanged
   opampServer:
     image:
       tag: v3.1.0   # Updated from v3.0.0
   ```

   Commit: `chore(chart): update to tinyolly v38.0.1 and opamp v3.1.0`
2. **Release-Please Creates**:
   - PR: `chore: release helm-tinyolly 0.3.2`
3. **When Merged**:
   - Packages & pushes chart: `tinyolly:0.3.2`

### Benefits

tinyolly-ui:v1.0.0` = Unchanged

- `

1. **Clear Risk Assessment**: Users can see exactly what changed
   - `tinyolly:v38.0.0 → v38.0.1` = Backend patch
   - `opamp-server:v3.0.0` = Unchanged
   - `helm-tinyolly:0.3.2` = Chart updated

2. **Independent Release Cadence**:
   - Backend can release frequently
   - Chart releases only when adopting new versions
   - Demo apps release independently

3. **Semantic Versioning Clarity**:
   - Each component follows SemVer independently
   - Breaking changes clear per component

4. **Container Builds Work**:
   - Each component PR triggers its own container build
   - Workflow checks version changes, not paths_released

### Trade-offs

**Pro:**

- Maximum clarity for users
- Components can evolve at different rates
- Chart versions are deliberate, not automatic

**Con:**

- Manual step to update chart dependencies
- Could drift if chart isn't updated regularly
- More PRs to review (though they're smaller and clearer)

### Alternative Considered: Linked Versions

Using release-please's `linked-versions` plugin would make all related components share the same version:

- `apps/tinyolly-ui:v38.1.0`  ← Same version even if unchanged
- `apps/tinyolly:v38.1.0`
- `apps/opamp-server:v38.1.0`  ← Same version even if unchanged
- `charts/tinyolly:v38.1.0`

**Why we rejected this**: Defeats the purpose of independent versioning. Users can't tell what actually changed.

### Automation Options

If manual chart updates become tedious, we could add a bot that:

1. Watches for app releases
2. Auto-creates PR to bump chart dependencies
3. Maintainer reviews and merges

This preserves deliberate chart releases while reducing toil.

## Implementation

### Config Changes

1. **Removed monorepo root** from `.release-please-manifest.json`
2. **Set `separate-pull-requests: true`** in `release-please-config.json`
3. **Updated GitHub Actions** to detect version changes instead of paths_released

### Workflow

Developers just need to:

1. Use conventional commits: `fix:`, `feat:`, etc.
2. Review and merge release PRs when ready
3. Update chart values.yaml when ready to adopt new versions

Release-please and GitHub Actions handle the rest.
