# Contributing to ollyScale

Thank you for your interest in contributing to ollyScale! This guide will help you get started.

## About ollyScale

ollyScale is based on the excellent TinyOlly project and maintains compatibility with the OpenTelemetry ecosystem. We welcome contributions that enhance the platform while respecting both the original TinyOlly codebase (BSD-3-Clause) and new ollyScale features (AGPL-3.0).

## Development Setup

### Prerequisites

- Python 3.11+
- Go 1.23+ (for OpAMP server)
- Docker Desktop or Podman
- KIND (Kubernetes in Docker) for Kubernetes testing
- Git
- Pre-commit

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/ryanfaircloth/ollyscale.git
cd ollyscale

# Setup pre-commit hooks (required)
make precommit-setup

# Or manually
pip install pre-commit
pre-commit install
```

## Code Quality

### Pre-commit Hooks

We use pre-commit hooks to maintain code quality. **All commits must pass pre-commit checks.**

```bash
# Setup hooks (first time)
make precommit-setup

# Run checks manually
make lint

# Run with auto-fix
make lint-fix
```

**Checks include:**

- **Python**: ruff (replaces black, isort, flake8, pylint)
- **YAML**: yamlfmt + validation
- **JSON**: prettier + validation
- **Shell**: shellcheck
- **Docker**: hadolint
- **Helm**: helm lint
- **Go**: golangci-lint
- **Markdown**: markdownlint
- **Terraform**: fmt + validate

See [docs/precommit.md](docs/precommit.md) for detailed documentation.

### Python Code Style

- **Formatter**: ruff (120 char line length)
- **Linting**: ruff with comprehensive rules
- **Imports**: Sorted by ruff (isort rules)
- **Type hints**: Encouraged but not required
- **Config**: [`pyproject.toml`](pyproject.toml)

**Example:**

```python
"""Module docstring."""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import settings
from common.storage import RedisStorage


async def my_function(param: str) -> dict:
    """Function docstring.

    Args:
        param: Description of param

    Returns:
        Dictionary with results
    """
    result = await storage.get_data(param)
    return {"data": result}
```

### Docker Best Practices

- Use multi-stage builds
- Pin base image versions (e.g., `python:3.11-slim`)
- Run as non-root user
- Minimize layers
- Use `.dockerignore`
- Pass hadolint checks

### Helm Chart Guidelines

- Follow Helm best practices
- Use `values.yaml` for all configuration
- Include helpful comments
- Test with `helm lint`
- Version charts semantically

### Go Code Style

- Follow standard Go conventions
- Use `gofmt` and `goimports`
- Pass `golangci-lint` checks
- Write table-driven tests
- Handle all errors

## Testing

### Python Tests

```bash
cd apps/ollyscale
poetry install --with test
poetry run pytest
```

### Manual Testing

```bash
# Docker deployment
cd docker
./01-start-core.sh

# Kubernetes deployment
make up
cd charts
./build-and-push-local.sh v2.x.x-test
```

## Git Workflow

### Branching Strategy

- `main`: Stable releases
- `develop`: Development branch
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Hotfixes: `hotfix/description`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions/changes
- `chore`: Build/tooling changes
- `ci`: CI/CD changes

**Examples:**

```bash
git commit -m "feat(ui): add service map zoom controls"
git commit -m "fix(storage): handle missing trace IDs gracefully"
git commit -m "docs: update Kubernetes deployment guide"
git commit -m "chore: update dependencies"
```

**Scopes (optional):**
- Component names: `ollyscale`, `ollyscale-ui`, `opamp-server`, `chart-ollyscale`
- Functional areas: `ui`, `api`, `storage`, `ingestion`, `opamp`

**Breaking Changes:**

For breaking changes, use `!` after the type or add `BREAKING CHANGE:` in the footer:

```bash
git commit -m "feat(api)!: redesign OTLP endpoint authentication"
# or
git commit -m "feat(api): redesign OTLP endpoint

BREAKING CHANGE: The endpoint now requires Bearer token authentication."
```

**Version Bumping:**

Commits trigger automatic version bumps based on type:
- `feat:` → Minor version bump (0.x.0)
- `fix:` → Patch version bump (0.0.x)
- `feat!:` or `BREAKING CHANGE:` → Major version bump (x.0.0)

See [docs/release-system.md](docs/release-system.md) for complete release process documentation.

### Pull Request Process

1. **Create a feature branch** from `develop`:

   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit**:

   ```bash
   git add .
   git commit -m "feat: add new feature"
   # Pre-commit hooks run automatically
   ```

3. **Push and create PR**:

   ```bash
   git push origin feature/my-feature
   # Create PR on GitHub targeting 'develop' branch
   ```

4. **PR Requirements**:
   - All pre-commit checks pass
   - CI/CD workflows pass
   - Code review approval
   - Up-to-date with target branch

5. **After merge**:

   ```bash
   git checkout develop
   git pull origin develop
   git branch -d feature/my-feature
   ```

## Building and Testing

### Docker Builds

```bash
cd scripts/build
./01-login.sh                # Login to registry
./02-build-all.sh            # Build all images
./03-push-all.sh             # Push to registry
```

### Local Kubernetes Testing

```bash
# Create/update cluster
make up

# Build and deploy local changes
cd charts
./build-and-push-local.sh v2.x.x-dev

# Update ArgoCD
cd ../.kind
terraform apply -replace='kubectl_manifest.observability_applications["observability/ollyscale.yaml"]' -auto-approve

# Check deployment
kubectl get pods -n ollyscale
kubectl logs -n ollyscale deployment/ollyscale-webui -f
```

### Cleaning Test Data

```bash
# Docker
docker exec ollyscale-redis redis-cli FLUSHDB

# Kubernetes
kubectl exec -n ollyscale ollyscale-redis-0 -- redis-cli FLUSHDB
```

## Documentation

### Adding Documentation

- Documentation lives in `docs/`
- Use Markdown format
- Follow existing structure
- Include code examples
- Add images to `docs/images/`

### Building Docs Locally

```bash
# Install dependencies
pip install -r docs/requirements.txt

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

## Release Process

Releases are automated using Release Please. See [docs/release-process.md](docs/release-process.md).

## Getting Help

- **Documentation**: [https://ryanfaircloth.github.io/ollyscale/](https://ryanfaircloth.github.io/ollyscale/)
- **Issues**: [GitHub Issues](https://github.com/ryanfaircloth/ollyscale/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ryanfaircloth/ollyscale/discussions)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the BSD 3-Clause License.

---

**Thank you for contributing to ollyScale!** 🎉
