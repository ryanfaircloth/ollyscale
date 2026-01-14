# TinyOlly KIND Cluster Configuration

## Quick Start

### Production/POC Mode (uses ghcr.io)

```bash
make up  # Uses ghcr.io/ryanfaircloth/tinyolly images
```

### Development Mode (uses local registry)

```bash
# Build local images with timestamp version (0.0.TIMESTAMP)
make build

# Deploy with local images
make up
```

## How It Works

1. **`make up`** (default): Uses production images from `ghcr.io/ryanfaircloth/tinyolly`

2. **`make build`**:
   - Builds images locally with version `0.0.$(timestamp)`
   - Pushes to local registry at `registry.tinyolly.test:49443`
   - Creates `.kind/terraform.tfvars` with local configuration (gitignored)

3. **`make up`** (after build): Uses local images from `.kind/terraform.tfvars`

4. **Switch back to production**: Delete `.kind/terraform.tfvars` and run `make up`

## Implementation Details

1. **Terraform Variables** (`.kind/variables.tf`):
   - `use_local_registry` - boolean, defaults to `false` (ghcr.io)
   - `tinyolly_tag`, `opamp_tag`, `demo_tag` - version tags

2. **Terraform Locals** (`.kind/locals.tf`):
   - Conditionally sets `image_registry` and `chart_registry`
   - Local: `docker-registry.registry.svc.cluster.local:5000/tinyolly`
   - Remote: `ghcr.io/ryanfaircloth/tinyolly`

3. **ArgoCD Templates** (`.kind/modules/main/argocd-applications/observability/tinyolly.yaml`):
   - Uses template variables: `${image_registry}` and `${chart_registry}`
   - Terraform renders templates at apply time

4. **Local Build** (`make build`):
   - Runs `charts/build-and-push-local.sh` with timestamp version
   - Generates `terraform.tfvars` with local configuration
   - File is gitignored to keep git clean

## Benefits

✅ **Clean Git**: `terraform.tfvars` is gitignored, no version churn in YAML  
✅ **Simple Workflow**: `make build` → `make up` for development  
✅ **POC/Demo Ready**: `make up` works immediately with public images  
✅ **Timestamp Versions**: `0.0.TIMESTAMP` format for local builds  
✅ **Easy Reset**: Delete `terraform.tfvars` to switch back to production

## Production Image Tags

Default versions from ghcr.io:

- TinyOlly UI: `v30.0.1`
- OpAMP Server: `v1.0.0`
- OTLP Receiver: `v30.0.1` (same image as UI)
- Demo: `v0.5.0`
- Demo Agent: `v0.3.0`
