#!/bin/bash

echo "=== Starting Strictly Dancing Dev Environment ==="

# Ensure HOME is set correctly for vscode user
export HOME="/home/vscode"

# Ensure paths are set
export PATH="$HOME/.claude/local/bin:$HOME/.bun/bin:$HOME/.local/bin:$PATH"

# Update Claude Code to latest version
echo "Updating Claude Code to latest..."
if command -v claude &> /dev/null; then
    if claude update 2>/dev/null; then
        echo "Claude Code updated: $(claude --version 2>/dev/null)"
    else
        echo "Update command failed, reinstalling..."
        curl -fsSL https://claude.ai/install.sh | bash -s -- latest
        echo "Claude Code reinstalled: $(claude --version 2>/dev/null)"
    fi
else
    echo "Claude Code not found, installing..."
    curl -fsSL https://claude.ai/install.sh | bash -s -- latest
    echo "Claude Code installed: $(claude --version 2>/dev/null)"
fi

echo "Dev environment ready!"
echo ""
echo "Quick commands:"
echo "  docker compose up -d mcp-postgres redis  # Start services"
echo "  cd backend && uvicorn app.main:app --reload --port 8001  # Start API"
echo "  cd frontend && bun run dev  # Start frontend"
echo "  claude  # Start Claude Code CLI"
echo "  ./scripts/ralph-external-loop.sh <plan> --dangerous  # Run Ralph Wiggum"
