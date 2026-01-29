#!/bin/bash
set -e

echo "=== Strictly Dancing Dev Container Setup ==="

# Fix ownership of mounted directories
echo ""
echo "Setting up persistent credential directories..."

for dir in "$HOME/.claude" "$HOME/.config/gh" "$HOME/.aws"; do
    if [ -d "$dir" ]; then
        sudo chown -R vscode:vscode "$dir"
    fi
done

# Claude Code configuration
if [ -d "$HOME/.claude" ]; then
    chmod 700 "$HOME/.claude"
    if [ -f "$HOME/.claude/.credentials.json" ]; then
        chmod 600 "$HOME/.claude/.credentials.json"
        echo "Found existing Claude Code credentials"
    else
        echo "No Claude Code credentials found"
        echo "Run 'claude' to authenticate"
    fi
else
    echo "Claude directory not mounted"
fi

# GitHub CLI configuration
if [ -d "$HOME/.config/gh" ]; then
    chmod 700 "$HOME/.config/gh"
    if [ -f "$HOME/.config/gh/hosts.yml" ]; then
        chmod 600 "$HOME/.config/gh/hosts.yml"
        echo "Found existing GitHub CLI credentials"
    else
        echo "No GitHub CLI credentials found (run 'gh auth login')"
    fi
fi

# AWS configuration
if [ -d "$HOME/.aws" ]; then
    chmod 700 "$HOME/.aws"
    if [ -f "$HOME/.aws/credentials" ]; then
        chmod 600 "$HOME/.aws/credentials"
        echo "Found existing AWS credentials"
    fi
fi

# Install backend dependencies if pyproject.toml exists
if [ -f "/workspaces/strictly-dancing/backend/pyproject.toml" ]; then
    echo ""
    echo "Installing backend dependencies..."
    cd /workspaces/strictly-dancing/backend
    uv pip install --system -e ".[dev]" --quiet 2>/dev/null || uv pip install --system -e ".[dev]" || echo "Backend deps not ready yet"
fi

# Install frontend dependencies if package.json exists
if [ -f "/workspaces/strictly-dancing/frontend/package.json" ]; then
    echo ""
    echo "Installing frontend dependencies..."
    cd /workspaces/strictly-dancing/frontend
    bun install --silent 2>/dev/null || bun install || echo "Frontend deps not ready yet"
fi

echo ""
echo "=========================================="
echo "Strictly Dancing Dev Container Ready!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Run 'docker compose up -d mcp-postgres redis' to start services"
echo "  2. Run 'claude' to start Claude Code CLI"
echo "  3. Use Ralph Wiggum for TDD: ./scripts/ralph-external-loop.sh <plan>"
echo ""
