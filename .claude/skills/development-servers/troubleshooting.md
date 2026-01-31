# Development Servers Troubleshooting

## Problem: Servers Won't Start

**Symptoms:**
- Script hangs or times out
- PID files exist but processes are dead
- "Address already in use" errors

**Solution:**
```bash
# Use the script's built-in cleanup
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh stop
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh start

# The script automatically:
# - Kills orphaned processes on ports 8001, 5175
# - Cleans up stale PID files
# - Validates health checks before returning
```

## Problem: Database Connection Error

**Symptoms:**
- FastAPI fails to connect to PostgreSQL
- Connection refused errors

**Solution:**
```bash
# Verify AWS RDS Dev is accessible
curl -v telnet://ijack-dev.c9lvkaunz4dq.us-west-2.rds.amazonaws.com:5432

# Check .env file has correct credentials
cat /home/sean/git_wsl/strictly-dancing/backend/.env

# Then start FastAPI
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh start-fastapi
```

## Problem: Frontend Can't Reach API

**Symptoms:**
- CORS errors in browser console
- Network errors in React app

**Diagnosis:**
```bash
# Check both servers are running
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh status

# Test direct connections
curl http://localhost:8001/docs
curl http://localhost:5175
```

**Solution:**
- Ensure both servers are running
- Check CORS settings in FastAPI backend
- Verify API URL configuration in frontend

## Problem: Dependencies Not Installed

**Solution:**
```bash
cd /home/sean/git_wsl/strictly-dancing/backend
uv sync
```

## Problem: Node Modules Missing

**Solution:**
```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun install
```

## Problem: Types Out of Sync

**Symptoms:**
- TypeScript errors about missing properties
- API responses don't match expected types

**Solution:**
```bash
# Ensure FastAPI is running
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh status

# Regenerate types
bash /home/sean/git_wsl/strictly-dancing/scripts/dev-servers.sh generate-types
```

## Best Practices

1. **ALWAYS use dev-servers.sh script** - NEVER use direct commands
2. **Always check status first** - Don't assume servers are running
3. **Use curl for health checks** - Much faster than Playwright
4. **Only use Playwright for visual verification** - Save tokens
5. **Check logs before restarting** - Understand the problem first
6. **Clean restart when in doubt** - Use `dev-servers.sh restart`
7. **Port cleanup is automatic** - The script kills orphaned processes on startup
