# Quick Start: New Build System

## Install Task Runner

```bash
# macOS
brew install go-task/tap/go-task

# Linux
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin

# Verify installation
task --version
```

## Basic Commands

```bash
# See all available commands
task --list

# Check your environment
task check

# Create local KIND cluster
task up

# Build and deploy everything
task deploy

# Build only (no deployment)
task build-and-push

# Clean up
task down
```

## Quick Examples

### Build a single component

```bash
task build:api        # Just the API backend
task build:web-ui     # Just the web UI
```

### Custom version

```bash
VERSION=1.2.3 task build-and-push
```

### Force Docker (instead of auto-detected Podman)

```bash
CONTAINER_RUNTIME=docker task build
```

## Differences from Old System

| Old                                | New                   | Notes              |
| ---------------------------------- | --------------------- | ------------------ |
| `make deploy`                      | `task deploy`         | Same functionality |
| `make up`                          | `task up`             | Create cluster     |
| `./charts/build-and-push-local.sh` | `task build-and-push` | Simpler            |
| `make lint`                        | `task lint`           | Pre-commit checks  |

## For CI/CD

The same Taskfile works in GitHub Actions:

```yaml
- name: Build all images
  env:
    CI: "true"
    VERSION: "1.2.3"
  run: task build
```

## Need Help?

- Full guide: [docs/build-system-migration.md](build-system-migration.md)
- List tasks: `task --list`
- Task docs: <https://taskfile.dev/>

## Why Task Instead of Make?

- ✅ Automatic Podman/Docker detection
- ✅ Better variable handling
- ✅ YAML instead of Makefile syntax
- ✅ Built-in dependency management
- ✅ Same config for local and CI
- ✅ Cross-platform (works on Windows too)
