# Development Servers Architecture

## Two-Tier Stack

```
┌─────────────────────────────────────────┐
│  Vite (Port 5175)                       │
│  React PWA + TypeScript Frontend        │
│  Hot Module Replacement                 │
│  URL: http://localhost:5175             │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  FastAPI (Port 8001)                    │
│  REST API with OpenAPI docs             │
│  uvicorn --reload                       │
│  URL: http://localhost:8001             │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  PostgreSQL (AWS RDS Dev)               │
│  ijack-dev.c9lvkaunz4dq.us-west-2.rds   │
│  Database: strictly_dancing             │
└─────────────────────────────────────────┘
```

## File Locations

### Logs
All logs stored in `/home/sean/git_wsl/strictly-dancing/.logs/`:
- `fastapi.log` - FastAPI uvicorn output
- `vite.log` - Vite dev server output

### PID Files
Process IDs tracked in `/home/sean/git_wsl/strictly-dancing/.pids/`:
- `fastapi.pid`
- `vite.pid`

### Configuration
- Docker Compose: `/home/sean/git_wsl/strictly-dancing/docker-compose.yml`
- Backend env: `/home/sean/git_wsl/strictly-dancing/backend/.env`
- Frontend env: `/home/sean/git_wsl/strictly-dancing/frontend/.env`

## URLs

### Direct URLs
- Frontend: `http://localhost:5175`
- API Docs: `http://localhost:8001/docs`
- API Root: `http://localhost:8001/`

## Database Configuration

**Development** (default):
- Host: `ijack-dev.c9lvkaunz4dq.us-west-2.rds.amazonaws.com`
- Database: `strictly_dancing`
- MCP Database: `dev`

**Production**:
- Host: `ijack.c9lvkaunz4dq.us-west-2.rds.amazonaws.com`
- Database: `strictly_dancing`
- MCP Database: `prod`

## Integration with Other Skills

- **playwright-testing**: Ensure servers are running before E2E tests
- **database-operations**: Use `mcp__mcp-postgres-sd__*` tools for queries
- **type-generation**: Run `generate-types` after FastAPI changes
