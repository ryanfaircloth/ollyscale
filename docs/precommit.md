# Pre-commit Configuration for ollyScale

This project uses [pre-commit](https://pre-commit.com/) to maintain code quality and consistency across all languages and tools.

## Quick Start

```bash
# Install and setup hooks
make precommit-setup

# Or manually
pip install pre-commit
pre-commit install
```

## What Gets Checked

### Python

- **ruff**: Linting and formatting (replaces black, isort, flake8, pylint)
  - Auto-fixes import sorting, formatting, and common issues
  - Config: [`pyproject.toml`](pyproject.toml)

### YAML

- **yamlfmt**: Formatting and style consistency
- **check-yaml**: Syntax validation
- Config: [`.yamlfmt`](.yamlfmt)

### JSON

- **prettier**: Formatting
- **check-json**: Syntax validation

### Shell Scripts

- **shellcheck**: Linting for bash/sh scripts
- Catches common bugs and anti-patterns

### Docker

- **hadolint**: Dockerfile linting
- Enforces best practices (layer caching, security, maintainability)
- Config: [`.hadolint.yaml`](.hadolint.yaml)

### Helm

- **helmlint**: Validates Helm chart structure and templates
- Runs on all charts in `charts/`

### Go

- **golangci-lint**: Comprehensive Go linting
- Auto-fixes when possible

### Markdown

- **markdownlint**: Style and syntax checking
- Config: [`.markdownlint.yaml`](.markdownlint.yaml)

### Terraform

- **terraform fmt**: Format HCL files
- **terraform validate**: Validate configuration

### General

- Trailing whitespace removal
- End-of-file fixer
- Large file detection (>1MB)
- Private key detection
- Merge conflict detection

## Usage

### Automatic (Recommended)

Hooks run automatically on `git commit`. If checks fail, the commit is blocked:

```bash
git add .
git commit -m "feat: add new feature"
# Pre-commit runs, auto-fixes issues, then commits
```

### Manual

```bash
# Run all checks
make lint
# Or: pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run hadolint-docker --all-files

# Run on specific files
pre-commit run --files apps/ollyscale/main.py apps/demo/backend.py

# Update hooks to latest versions
pre-commit autoupdate
```

### Skip Hooks (Not Recommended)

```bash
# Skip all hooks (emergency only)
git commit --no-verify -m "hotfix"

# Skip specific files by adding to exclude in .pre-commit-config.yaml
```

## Configuration Files

- [`.pre-commit-config.yaml`](.pre-commit-config.yaml) - Main hook configuration
- [`pyproject.toml`](pyproject.toml) - Python/ruff settings
- [`.hadolint.yaml`](.hadolint.yaml) - Docker linting rules
- [`.markdownlint.yaml`](.markdownlint.yaml) - Markdown style rules
- [`.yamlfmt`](.yamlfmt) - YAML formatting rules

## Troubleshooting

### Hooks fail on first run

This is normal. Pre-commit will auto-fix many issues. Run again:

```bash
git add .
git commit -m "fix: apply pre-commit auto-fixes"
```

### "command not found: pre-commit"

```bash
pip install pre-commit
pre-commit install
```

### Hook installation fails

```bash
# Clear cache and reinstall
pre-commit clean
pre-commit install --install-hooks
```

### Specific hook keeps failing

```bash
# Run in verbose mode for debugging
pre-commit run <hook-id> --all-files --verbose

# Temporarily skip hook (not recommended)
SKIP=<hook-id> git commit -m "message"
```

## Adding New Hooks

1. Find the hook at [pre-commit.com hooks](https://pre-commit.com/hooks.html)
2. Add to `.pre-commit-config.yaml`:

   ```yaml
   - repo: https://github.com/org/repo
     rev: v1.0.0
     hooks:
       - id: hook-name
         args: [--option]
   ```

3. Install: `pre-commit install --install-hooks`
4. Test: `pre-commit run hook-name --all-files`

## CI Integration

Pre-commit checks run in GitHub Actions workflows. See [`.github/workflows/`](.github/workflows/).

## Performance

- **First run**: Slower (downloads and caches tools)
- **Subsequent runs**: Fast (only changed files)
- **Full run**: `pre-commit run --all-files` takes ~2-5 minutes

## Best Practices

1. **Run before pushing**: `make lint` or `pre-commit run --all-files`
2. **Commit auto-fixes separately**: Let pre-commit fix, then review changes
3. **Keep hooks updated**: `pre-commit autoupdate` monthly
4. **Don't skip hooks**: They catch real issues before code review
5. **Fix root causes**: If a hook fails repeatedly, fix the underlying issue

## Ruff Configuration Highlights

- **Target**: Python 3.11+
- **Line length**: 120 characters
- **Enabled checks**:
  - Code quality (pyflakes, pycodestyle)
  - Import sorting (isort)
  - Security (bandit subset)
  - Complexity (pylint subset)
  - Modern Python (pyupgrade)
- **Auto-fix**: Most issues fixed automatically
- **Config**: [`pyproject.toml`](pyproject.toml)

## Docker Linting Highlights

- **Ignored rules**:
  - DL3008: Pin apt versions (handled by base images)
  - DL3013: Pin pip versions (requirements.txt handles this)
- **Trusted registries**: docker.io, ghcr.io, gcr.io, registry.k8s.io
- **Config**: [`.hadolint.yaml`](.hadolint.yaml)

## Support

- Pre-commit docs: <https://pre-commit.com>
- Ruff docs: <https://docs.astral.sh/ruff>
- Hadolint docs: <https://github.com/hadolint/hadolint>
- Project issues: <https://github.com/ryanfaircloth/ollyscale/issues>
