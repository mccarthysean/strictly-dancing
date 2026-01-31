---
name: development-servers
description: Manage FastAPI and Vite development servers with automated troubleshooting. Use when starting the application, after code changes, when servers crash, verifying servers are running, or troubleshooting errors. Always use the dev-servers.sh script for server operations. (project)
allowed-tools: [Bash, Read]
---

# Development Servers Skill

Manage FastAPI and Vite development servers using the centralized `dev-servers.sh` script.

**CRITICAL: ALWAYS use the `dev-servers.sh` script for ALL server operations.**

## Server Stack

| Service | Port | Description |
|---------|------|-------------|
| FastAPI | 8001 | REST API backend with OpenAPI |
| Vite | 5175 | React PWA frontend with HMR |
| PostgreSQL | - | AWS RDS Dev (ijack-dev/strictly_dancing) |

## Core Commands

```bash
# Start all servers
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh start

# Stop all servers
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh stop

# Restart all servers
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh restart

# Check status
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh status

# View logs (all or specific service)
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh logs
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh logs fastapi
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh logs vite
```

## Individual Services

```bash
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh start-fastapi
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh start-vite
```

## Utility Commands

```bash
# Run database migrations
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh migrate

# Generate TypeScript types from OpenAPI
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh generate-types
```

## URLs

- Frontend: `http://localhost:5175`
- API Docs: `http://localhost:8001/docs`
- API Root: `http://localhost:8001/`

## Quick Verification

Use curl for health checks (minimal token usage):

```bash
# Check status (~50 tokens)
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh status

# Quick health check (~100 tokens)
curl -f http://localhost:8001/docs && echo "FastAPI OK"
curl -f http://localhost:5175 && echo "Vite OK"
```

## Common Workflows

### After Git Pull
```bash
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh restart
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh migrate
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh status
```

### After API Changes
```bash
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh status
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh generate-types
```

## Auto-Reload

All services have auto-reload enabled:
- **FastAPI**: uvicorn `--reload` monitors `/app` directory
- **Vite**: Built-in hot module replacement

Manual restart only needed for:
- Environment variable changes
- Package installations
- Configuration file changes
- Database schema migrations

## Reference Files

For detailed troubleshooting and configuration:
- `troubleshooting.md` - Common problems and solutions
- `architecture.md` - Server architecture and file locations
