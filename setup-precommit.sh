#!/bin/bash
# Setup pre-commit hooks for ollyScale

set -e

echo "🔧 Setting up pre-commit hooks for ollyScale..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
else
    echo "✅ pre-commit is already installed"
fi

# Install the git hooks
echo "🔗 Installing git hooks..."
pre-commit install

# Install commit-msg hook for conventional commits (optional)
echo "📝 Installing commit-msg hook..."
pre-commit install --hook-type commit-msg || echo "⚠️  commit-msg hook not configured (optional)"

# Run pre-commit on all files to check current state
echo "🧪 Running pre-commit on all files (this may take a while)..."
pre-commit run --all-files || {
    echo "⚠️  Some checks failed. This is normal for first-time setup."
    echo "💡 The hooks will now run automatically on git commit."
    echo "💡 To run manually: pre-commit run --all-files"
    echo "💡 To update hooks: pre-commit autoupdate"
    exit 0
}

echo "✨ Pre-commit setup complete!"
echo ""
echo "📚 Usage:"
echo "  • Hooks run automatically on: git commit"
echo "  • Run manually on all files:  pre-commit run --all-files"
echo "  • Run on specific files:      pre-commit run --files <file1> <file2>"
echo "  • Skip hooks (not recommended): git commit --no-verify"
echo "  • Update hooks to latest:     pre-commit autoupdate"
echo ""
echo "🔍 Configured checks:"
echo "  • Python: ruff (lint + format)"
echo "  • YAML: validation + formatting"
echo "  • JSON: validation + formatting"
echo "  • Shell: shellcheck"
echo "  • Docker: hadolint"
echo "  • Helm: helm lint"
echo "  • Go: golangci-lint"
echo "  • Markdown: markdownlint"
echo "  • Terraform: fmt + validate"
