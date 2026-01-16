# ollyScale Rebranding Plan

## Overview

Complete rebranding from ollyScale to ollyScale, including licensing changes, container/chart naming
strategy, and CI/CD improvements for future forks.

## Licensing Strategy

### Phase 1: License Files

- [x] Rename `LICENSE` to `LICENSE-BSD3-ORIGINAL` (preserve ollyScale's original license)
- [x] Create `LICENSE` with AGPL-3.0
- [x] Create `NOTICE` file acknowledging ollyScale origins and dual licensing
- [x] Create `LICENSE-HEADER-AGPL.txt` template for new/modified files
- [x] Create `LICENSE-HEADER-BSD3.txt` template for original ollyScale files

### Phase 2: File Headers

**Original ollyScale files (keep BSD-3-Clause header):**

- Files we didn't significantly modify from upstream
- Add comment noting "Originally from ollyScale project"

**Modified/New files (add AGPL header):**

- Files we created: `.kind/`, rebranding configs, new features
- Files significantly modified (>30% changes)
- Include: "Based on ollyScale (BSD-3-Clause), see LICENSE-BSD3-ORIGINAL"

## Naming Strategy

### Container/Chart Function-Based Naming (RECOMMENDED)

**Benefit:** Future forks can use our automation without rebranding
**Approach:** Use generic functional names in containers/charts, brand only in docs/UI

**Container Images:**

- `ollyscale/ui` → `observability-platform/ui` or keep `ollyscale/ui`
- `ollyscale/otlp-receiver` → `observability-platform/otlp-receiver`
- `ollyscale/opamp-server` → `observability-platform/opamp-server`

**Helm Charts:**

- `ollyscale` → `observability-platform` or `ollyscale`
- `ollyscale-demos` → `observability-demos`
- `ollyscale-demo-otel-agent` → `otel-agent-demo`

**Decision Point:** Should we use brand-neutral names or ollyScale brand?

- Option A: `observability-platform/*` (fork-friendly)
- Option B: `ollyscale/*` (clear branding)
- **Recommendation:** Option A for containers, Option B for marketing materials

### Kubernetes Resources

- Namespace: `ollyscale` → `observability` or `ollyscale`
- Service names: functional (ui, receiver, opamp-server)
- Deployment names: match service names

## Rebranding Checklist

### 1. Documentation & Marketing

- [ ] `README.md` - Add "Origins" section, update all references
- [ ] `CONTRIBUTING.md` - Update repository URLs, project name
- [ ] `docs/` directory - All markdown files
- [ ] `docs/images/` - Logo files (ollyscaletitle.svg, etc.) **→ Phase 7**
- [ ] `mkdocs.yml` - Site name, repo URL
- [ ] Repository description on GitHub
- [ ] Social media preview image **→ Phase 7**
- [ ] Favicon and app icons **→ Phase 7**

### 1a. UI/UX Improvements (Phase 7)

- [ ] Design new ollyScale logo and brand identity
- [ ] Define new color scheme and CSS variables
- [ ] Identify and document current UX issues
- [ ] Redesign problematic UI components
- [ ] Update theme/styling across all pages
- [ ] Test accessibility and responsive design
- [ ] Update all screenshots with new UI

### 2. CI/CD & Automation Scripts

**Use Environment Variables Strategy:**

```bash
# Instead of hardcoded:
REPO="ollyscale/ollyscale"

# Use:
GH_ORG="${GH_ORG:-ollyscale}"
GH_REPO="${GH_REPO:-observability-platform}"
CONTAINER_REGISTRY="${CONTAINER_REGISTRY:-ghcr.io}"
```

**Files to Update:**

- [ ] `.github/workflows/*.yml` - All workflow files
- [ ] `.github/dependabot.yml` - Directory paths, labels
- [ ] `scripts/build/*.sh` - Image names, registry paths
- [ ] `scripts/release/*.sh` - Release automation
- [ ] `charts/build-and-push-local.sh` - Local build script
- [ ] `charts/deploy-to-argocd.sh` - Deployment automation
- [ ] `Makefile` - All targets and variables

### 3. Helm Charts

- [ ] `charts/ollyscale/Chart.yaml` - name, description, home, sources
- [ ] `charts/ollyscale/values.yaml` - image repositories, names
- [ ] `charts/ollyscale/templates/*.yaml` - labels, annotations, names
- [ ] `charts/ollyscale-demos/Chart.yaml`
- [ ] `charts/ollyscale-demos/values.yaml`
- [ ] `charts/ollyscale-demo-otel-agent/Chart.yaml`
- [ ] Consider: Rename chart directories to function-based names

### 4. Kubernetes/KIND Configuration

- [ ] `.kind/modules/main/main.tf` - Cluster name, namespaces
- [ ] `.kind/modules/main/variables.tf` - Variable names, defaults
- [ ] `.kind/modules/ollyscale/*.tf` - Module name, resource names
- [ ] `.kind/modules/ollyscale/argocd-applications/observability/*.yaml`
- [ ] `.kind/terraform.auto.tfvars` - Variable values
- [ ] Consider: Rename `.kind/modules/ollyscale/` to `.kind/modules/observability/`

### 5. Source Code - Python

**Backend (`apps/ollyscale/`):**

- [ ] Directory name: `apps/ollyscale/` → `apps/observability-platform/` or `apps/ollyscale/`
- [ ] `app/__init__.py` - Service name, metadata
- [ ] `app/main.py` - FastAPI title, description, version
- [ ] `models.py` - Model names if branded
- [ ] `requirements.txt` - Package names if published
- [ ] Import statements across all Python files
- [ ] Add AGPL headers to modified files

### 6. Source Code - TypeScript/JavaScript

**Frontend (`apps/ollyscale-ui/`):**

- [ ] Directory name: `apps/ollyscale-ui/` → `apps/ui/`
- [ ] `package.json` - name, description, repository
- [ ] `src/` - All TypeScript imports, API endpoints
- [ ] Page titles, branding text in UI
- [ ] Add AGPL headers to modified files

### 7. Source Code - Go

**OpAMP Server (`apps/opamp-server/`):**

- [ ] `go.mod` - module path
- [ ] `main.go` - Service name, logging
- [ ] Add AGPL headers if modified

### 8. Docker & Containers

- [ ] `docker/dockerfiles/Dockerfile.ollyscale-ui` - Rename, update labels
- [ ] `docker/dockerfiles/Dockerfile.ollyscale-otlp-receiver` - Rename
- [ ] `docker/dockerfiles/Dockerfile.opamp-server` - Update labels
- [ ] `docker/apps/` - Build context references
- [ ] Container labels: `org.opencontainers.image.*`

### 9. Configuration Files

- [ ] `config/otelcol/` - Config file comments, service names
- [ ] `pyproject.toml` - Project name, URLs if used
- [ ] `release-please-config.json` - Package names, paths
- [ ] `.gitignore` - Path references
- [ ] `renovate.json` - Labels, automerge rules

### 10. Demo Applications

- [ ] `apps/demo/` - Service names, endpoints
- [ ] `apps/demo-otel-agent/` - Configuration references

### 11. GitHub Configuration

- [ ] `.github/ISSUE_TEMPLATE/` - Project name references
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` - Update if exists
- [ ] `.github/CODEOWNERS` - Update if exists
- [ ] Repository settings (Description, Website, Topics)

### 12. DNS and Ingress

- [ ] HTTPRoute host patterns (*.ollyscale.test →*.ollyscale.test)
- [ ] Certificate names and DNS references
- [ ] `/etc/hosts` or `hostctl` entries documentation
- [ ] Ingress annotations and labels

### 13. Redis Keys and Data Migration

- [ ] Review Redis key prefixes (span:, trace:, etc.)
- [ ] Document if migration needed for existing data
- [ ] Update storage.py if keys contain project name

### 14. Git History and Tags

- [ ] Tag current state: `git tag pre-ollyscale-rebrand`
- [ ] Update git remote to new repository name
- [ ] Plan for GitHub repo redirect setup

## Implementation Phases

### Dependency Tree & Execution Order

```text
Phase 0: Pre-Flight (no dependencies)
├─ Tag: pre-ollyscale-rebrand
├─ Audit: grep for all ollyscale references
└─ Review: Identify files that must keep ollyScale

Phase 1: Foundation (depends on Phase 0)
├─ 1.1 Licensing (no dependencies)
│   ├─ Create LICENSE (AGPL-3.0)
│   ├─ Create NOTICE file
│   ├─ Create LICENSE-HEADER-AGPL.txt
│   └─ Create LICENSE-HEADER-BSD3.txt
│   [VALIDATE & COMMIT]
│
└─ 1.2 Core Documentation (depends on 1.1)
    ├─ README.md - Add origins section
    ├─ README.md - Update references (keep ollyScale in origins)
    └─ CONTRIBUTING.md - Update basic references
    [VALIDATE & COMMIT] - COMPLETED

Phase 2: Infrastructure (depends on Phase 1)
├─ 2.1 Makefile Variables (no dependencies within phase)
│   ├─ Add PROJECT_NAME, PROJECT_SLUG variables
│   ├─ Add GH_ORG, GH_REPO variables
│   ├─ Add REGISTRY, REGISTRY_ORG variables
│   ├─ Update all targets to use variables
│   └─ Test: make --dry-run to verify
│   [VALIDATE & COMMIT] - COMPLETED
│
├─ 2.2 Build Scripts (depends on 2.1)
│   ├─ scripts/build/*.sh - Parameterize
│   ├─ scripts/release/*.sh - Parameterize
│   ├─ charts/build-and-push-local.sh - Parameterize [COMPLETED]
│   └─ Test: Run build script with defaults
│   [VALIDATE & COMMIT] - PARTIALLY COMPLETED
│
└─ 2.3 GitHub Workflows (depends on 2.1)
    ├─ .github/workflows/*.yml - Add env vars
    ├─ .github/dependabot.yml - Update paths
    └─ Test: Validate YAML syntax
    [VALIDATE & COMMIT]

Phase 3: Kubernetes/Helm (depends on Phase 2)
├─ 3.1 Helm Chart Renaming (critical path)
│   ├─ Rename charts/ollyscale/ → charts/ollyscale/ [COMPLETED]
│   ├─ Update Chart.yaml (name, description, home, sources) [COMPLETED]
│   ├─ Update values.yaml (image repos, names)
│   ├─ Update all templates/*.yaml (labels, annotations)
│   └─ Test: helm lint charts/ollyscale [COMPLETED - PASSED]
│   [VALIDATE & COMMIT] - PARTIALLY COMPLETED
│
├─ 3.2 Additional Charts (depends on 3.1)
│   ├─ Rename charts/ollyscale-demos/ → charts/ollyscale-demos/ [COMPLETED]
│   ├─ Rename charts/ollyscale-demo-otel-agent/ → charts/ollyscale-otel-agent/ [COMPLETED]
│   └─ Update all Chart.yaml and values.yaml [COMPLETED]
│   [VALIDATE & COMMIT] - COMPLETED
│
└─ 3.3 Terraform/KIND (depends on 3.1, 3.2)
    ├─ Rename .kind/modules/ollyscale/ → .kind/modules/ollyscale/
    ├─ Update main.tf, variables.tf
    ├─ Update argocd-applications/*.yaml
    ├─ Update terraform.auto.tfvars
    ├─ Test: terraform validate
    └─ Test: terraform plan (should show renames)
    [VALIDATE & COMMIT]

Phase 4: Source Code (depends on Phase 3)
├─ 4.1 Python Backend (parallel with 4.2, 4.3)
│   ├─ Rename apps/ollyscale/ → apps/ollyscale/
│   ├─ Update app/main.py (title, description)
│   ├─ Update all imports across files
│   ├─ Add AGPL headers to modified files
│   ├─ Update requirements.txt if needed
│   └─ Test: Python syntax check, imports
│   [VALIDATE & COMMIT]
│
├─ 4.2 TypeScript Frontend (parallel with 4.1, 4.3)
│   ├─ Rename apps/ollyscale-ui/ → apps/ollyscale-ui/
│   ├─ Update package.json
│   ├─ Update src/ imports and API endpoints
│   ├─ Add AGPL headers to modified files
│   └─ Test: npm run build (or lint)
│   [VALIDATE & COMMIT]
│
└─ 4.3 Go OpAMP (parallel with 4.1, 4.2)
    ├─ Update go.mod module path if needed
    ├─ Update main.go service name
    ├─ Add AGPL headers if modified
    └─ Test: go build
    [VALIDATE & COMMIT]

Phase 5: Docker & Containers (depends on Phase 4)
├─ 5.1 Dockerfiles
│   ├─ Rename Dockerfile.ollyscale-ui → Dockerfile.ollyscale-ui
│   ├─ Rename Dockerfile.ollyscale-otlp-receiver → Dockerfile.ollyscale-receiver
│   ├─ Update all labels (org.opencontainers.image.*)
│   └─ Update docker-compose.yml if exists
│   [VALIDATE & COMMIT]
│
└─ 5.2 Build & Test (depends on 5.1, critical validation)
    ├─ Test: Build all containers locally
    ├─ Test: Tag with ollyscale names
    ├─ Test: Push to local registry
    └─ Document any build issues
    [VALIDATE & COMMIT]

Phase 6: Configuration Files (depends on Phase 5)
├─ config/otelcol/ - Update comments, service names
├─ pyproject.toml - Update if exists
├─ release-please-config.json - Update paths
├─ .gitignore - Update path references
├─ renovate.json - Update labels
└─ Test: Validate all config files
[VALIDATE & COMMIT]

Phase 7: Full Integration Test (depends on Phase 6)
├─ 7.1 Deploy to KIND
│   ├─ make up (should use new ollyscale configs)
│   ├─ make deploy (build and deploy ollyscale)
│   ├─ Verify: kubectl get po -n ollyscale
│   ├─ Verify: All pods Running
│   └─ Check logs for old "ollyscale" references
│   [VALIDATE & COMMIT if issues fixed]
│
├─ 7.2 Functional Testing
│   ├─ Access UI at https://ollyscale.ollyscale.test:49443
│   ├─ Send test telemetry
│   ├─ Verify traces, logs, metrics display
│   ├─ Test service map generation
│   └─ Verify OTel Demo still works
│   [VALIDATE & COMMIT if issues fixed]
│
└─ 7.3 Final Cleanup
    ├─ Search: grep -r "ollyscale" (except allowed files)
    ├─ Update any missed references
    ├─ Update DNS/ingress docs
    └─ Update .github/ config
    [VALIDATE & COMMIT]

Phase 8: Visual Identity & UX (depends on Phase 7 stable)
├─ Design new logo
├─ Define color scheme
├─ Update CSS/theme variables
├─ Fix identified UX issues
├─ Update all images/screenshots
└─ Test visual changes
[VALIDATE & COMMIT]

Phase 9: Documentation Polish (depends on Phase 8)
├─ Update all remaining docs
├─ Create migration guide
├─ Update mkdocs site
└─ Final review
[VALIDATE & COMMIT]
```

### Critical Path

1. **Must complete in order:** Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7
2. **Can parallelize:** Within Phase 2 (2.1 → 2.2 and 2.3 in parallel)
3. **Can parallelize:** Phase 4 (4.1, 4.2, 4.3 all in parallel)
4. **Blocker phases:** 3.1 (Helm renaming) blocks everything after
5. **Validation gate:** Phase 7 must fully pass before Phase 8

### Execution Rules

1. **One task at a time:** Complete each sub-section fully
2. **Validate before commit:** Test that changes work as expected
3. **Commit frequently:** After each [VALIDATE & COMMIT] checkpoint
4. **Stop if blocked:** If something fails, fix before proceeding
5. **Document issues:** Note any problems in commit message
6. **Ask before major decisions:** Confirm approach for complex changes

### Phase 0: Pre-Flight (no dependencies)

1. Tag current state: `git tag pre-ollyscale-rebrand`
2. Review all `grep` results for ollyscale references
3. Create list of files that MUST keep ollyScale attribution
4. Backup current working cluster if needed

### Phase 1: Foundation (Licensing & Core Docs)

1. Create license files (AGPL, NOTICE)
2. Create header templates
3. Update README with origins section
4. Update main documentation

### Phase 2: Infrastructure (CI/CD & Automation)

1. Update Makefile with variables
2. Update GitHub workflows with GH_ORG/GH_REPO
3. Update build scripts with parameterization
4. Test local builds work

### Phase 3: Kubernetes & Charts (Technical Foundation)

1. Decide: Function-based vs. branded names
2. Update Helm chart names/values
3. Update Kubernetes manifests
4. Update Terraform configurations
5. Test deployment to KIND cluster

### Phase 4: Source Code (Application Layer)

1. Rename source directories
2. Update imports and namespaces
3. Add AGPL headers to modified files
4. Update package configurations
5. Test application builds

### Phase 5: Validation & Testing

1. Full build test (images + charts)
2. Deployment test to local KIND
3. Verify all services running
4. Check logs for old references
5. Test OTel Demo still works

### Phase 6: Polish & Documentation

1. Update all remaining docs
2. Create migration guide for fork users
3. Update screenshots/demos if branded
4. Final review for missed references

### Phase 7: Visual Identity & UX Improvements

1. Design new ollyScale logo and branding assets
2. Update `docs/images/` - Replace ollyscaletitle.svg and all logos
3. Implement new color scheme across UI
4. Update favicon and social media preview images
5. Redesign problematic UI components (fix UX issues)
6. Update CSS/theme variables for new brand colors
7. Test visual changes across all pages
8. Update screenshots in documentation with new UI
9. Create brand guidelines document if needed

## Testing Strategy

After each phase:

```bash
# 1. Check for remaining references
grep -r "ollyScale\|ollyscale" . --exclude-dir=.git --exclude-dir=node_modules \
  --exclude="REBRANDING-PLAN.md" --exclude="LICENSE-BSD3-ORIGINAL"

# 2. Test build
make deploy

# 3. Test deployment
kubectl get po -A | grep -v Running

# 4. Test functionality
# Access UI, send test telemetry, verify data flow
```

## Variables to Parameterize

### Environment Variables for CI/CD

```bash
# Organization & Repository
GH_ORG="${GH_ORG:-ollyscale}"
GH_REPO="${GH_REPO:-observability-platform}"

# Container Registry
CONTAINER_REGISTRY="${CONTAINER_REGISTRY:-ghcr.io}"
CONTAINER_ORG="${CONTAINER_ORG:-$GH_ORG}"

# Helm/OCI Registry
HELM_REGISTRY="${HELM_REGISTRY:-ghcr.io}"
HELM_ORG="${HELM_ORG:-$GH_ORG}"

# Branding (for forks)
PROJECT_NAME="${PROJECT_NAME:-ollyScale}"
PROJECT_NAME_LOWER="${PROJECT_NAME_LOWER:-ollyscale}"

# Kubernetes
K8S_NAMESPACE="${K8S_NAMESPACE:-observability}"
```

### Makefile Variables

```makefile
# Project configuration
PROJECT_NAME ?= ollyScale
PROJECT_SLUG ?= ollyscale
GH_ORG ?= ollyscale
GH_REPO ?= observability-platform

# Container configuration
REGISTRY ?= ghcr.io
REGISTRY_ORG ?= $(GH_ORG)
IMAGE_PREFIX ?= $(REGISTRY)/$(REGISTRY_ORG)

# Kubernetes
CLUSTER_NAME ?= $(PROJECT_SLUG)
NAMESPACE ?= observability
```

## Fork-Friendly Design Principles

1. **Parameterize Everything:** No hardcoded org/repo names in automation
2. **Functional Naming:** Container/chart names describe function, not brand
3. **Docs Separate from Code:** Brand only in docs, not in technical names
4. **Clear Origins:** Always acknowledge ollyScale in NOTICE file
5. **License Clarity:** Dual licensing clearly documented

## What Stays as "ollyScale"

**Files that MUST retain ollyScale references:**

1. `LICENSE-BSD3-ORIGINAL` - Original license file
2. `NOTICE` - Origins and attribution section
3. `README.md` - "Origins" section only
4. Copyright headers in files unchanged from upstream
5. Git commit history (immutable)
6. Any direct quotes or attributions in documentation

**Where ollyScale becomes ollyScale:**

- All active branding (UI, docs, marketing)
- Container images and chart names
- Kubernetes resources (namespaces, services, deployments)
- Source code package names and imports
- CI/CD configurations
- DNS and ingress hostnames
- GitHub repository name and settings

## Risk Mitigation

### Breaking Changes

- Database keys (Redis) may contain old names → Migration needed?
- API endpoints might be hardcoded in client code
- DNS/hostnames in ingress configurations

### Rollback Plan

- Keep branch for 1:1 comparison
- Tag pre-rebrand state: `git tag pre-ollyscale-rebrand`
- Document all namespace/name changes for troubleshooting

## Decision Log

### Decisions Made

- **License:** AGPL-3.0 for new/modified code, preserve BSD-3-Clause for original
- **Approach:** Systematic phase-by-phase with testing between phases
- **CI/CD:** Parameterize all org/repo/registry references
- **Container naming:** Branded `ollyscale/*` (ollyscale/ui, ollyscale/receiver, ollyscale/opamp-server)
- **Kubernetes namespace:** `ollyscale`
- **Helm chart names:** Branded `ollyscale`, `ollyscale-demos`, `ollyscale-otel-agent`
- **Repository name:** Rename from `ollyscale` to `ollyscale`
- **Python package:** `ollyscale` (if published to PyPI)
- **Container registry:** `ghcr.io/ryanfaircloth/ollyscale`
- **Visual identity:** New logo, color scheme, and UX improvements in Phase 7 (after technical rebrand is stable)

## Notes

- This document will be updated as we progress
- Each completed item will be checked off
- Any issues or blockers will be documented here
- Consider creating migration guide for existing ollyScale users
