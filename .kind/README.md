# ollyScale KIND Cluster Configuration

## Quick Start

### Production/POC Mode (uses ghcr.io)

```bash
task up  # Uses ghcr.io/ryanfaircloth/ollyscale images
```

### Development Mode (uses local registry)

```bash
# Build local images with timestamp version (0.0.TIMESTAMP)
task deploy

# Or just create cluster
task up
```

## How It Works

1. **`task up`** (default): Uses production images from `ghcr.io/ryanfaircloth/ollyscale`

2. **`task deploy`**:
   - Runs lint and tests first (validation)
   - Builds images locally with version `0.0.$(timestamp)`
   - Pushes to local registry at `registry.ollyscale.test:49443`
   - Creates `.kind/terraform.tfvars` with local configuration (gitignored)
   - Applies terraform to deploy

3. **`task up`** (after build): Uses local images from `.kind/terraform.tfvars`

4. **Switch back to production**: Delete `.kind/terraform.tfvars` and run `task up`

## Implementation Details

1. **Terraform Variables** (`.kind/variables.tf`):
   - `use_local_registry` - boolean, defaults to `false` (ghcr.io)
   - `ollyscale_tag`, `opamp_tag`, `demo_tag` - version tags

2. **Terraform Locals** (`.kind/locals.tf`):
   - Conditionally sets `image_registry` and `chart_registry`
   - Local: `docker-registry.registry.svc.cluster.local:5000/ollyscale`
   - Remote: `ghcr.io/ryanfaircloth/ollyscale`

3. **ArgoCD Templates** (`.kind/modules/main/argocd-applications/observability/ollyscale.yaml`):
   - Uses template variables: `${image_registry}` and `${chart_registry}`
   - Terraform renders templates at apply time

4. **Local Build** (`task deploy`):
   - Runs validation (lint + tests) first
   - Builds and pushes images with timestamp version
   - Generates `terraform.tfvars` with local configuration
   - File is gitignored to keep git clean

## Benefits

✅ **Clean Git**: `terraform.tfvars` is gitignored, no version churn in YAML  
✅ **Simple Workflow**: `task deploy` for full development build  
✅ **POC/Demo Ready**: `task up` works immediately with public images  
✅ **Validation**: Lint and tests run before every build  
✅ **Timestamp Versions**: `0.0.TIMESTAMP` format for local builds  
✅ **Easy Reset**: Delete `terraform.tfvars` to switch back to production

## Production Image Tags

Default versions from ghcr.io:

- ollyScale UI: `v30.0.1`
- OpAMP Server: `v1.0.0`
- OTLP Receiver: `v30.0.1` (same image as UI)
- Demo: `v0.5.0`
- Demo Agent: `v0.3.0`
