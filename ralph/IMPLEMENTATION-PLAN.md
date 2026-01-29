# Dance Host Marketplace - GitHub Repository Setup Plan

## Objective

Create a new GitHub repository under `mccarthysean` for a global dance host marketplace, set up the complete project structure with:
- **PWA Web App** (React + TanStack Router, following spartans-hockey patterns)
- **React Native Mobile Apps** (iOS/Android via Expo)
- **FastAPI Backend** (shared by both web and mobile)
- **AWS RDS PostgreSQL** (using existing ijack RDS instances)
- **Ralph Wiggum TDD automation**

---

## PROJECT NAME: TBD

**Name to be decided before implementation.** Options under consideration:
- DanceHost
- LeadAndFollow
- DanceCompanion
- HostFlow
- (User to provide final choice)

Placeholder `{PROJECT_NAME}` and `{project-name}` used throughout this plan.

---

## Phase 1: Create GitHub Repository

### Step 1.1: Create Remote Repository
```bash
gh repo create mccarthysean/{project-name} --public --description "Global Dance Host Marketplace - PWA + React Native + FastAPI"
```

### Step 1.2: Initialize Local Repository
```bash
mkdir -p /home/sean/git_wsl/{project-name}
cd /home/sean/git_wsl/{project-name}
git init
git remote add origin git@github.com:mccarthysean/{project-name}.git
```

---

## Phase 2: Copy Core Documentation Files

### Step 2.1: Copy and Rename PRD
- Source: `/home/sean/git_wsl/DancePartner-PRD.md`
- Destination: `/home/sean/git_wsl/{project-name}/PRD.md`
- **Modifications needed**: Update project name references

### Step 2.2: Copy and Rename Plan
- Source: `/home/sean/git_wsl/DancePartner-Plan.md`
- Destination: `/home/sean/git_wsl/{project-name}/PLAN.md`
- **Modifications needed**: Add PWA section, update project name

---

## Phase 3: Create Directory Structure

**Hybrid architecture: PWA Web App + React Native Mobile + Shared Backend**

Following spartans-hockey patterns for PWA, PRD Section 3.1 for mobile:

```
{project-name}/
├── CLAUDE.md                    # AI assistant context (CRITICAL)
├── CONTEXT.md                   # Current state tracking
├── PRD.md                       # Product Requirements Document
├── PLAN.md                      # Technology stack plan
├── .gitignore
├── README.md
│
├── frontend/                    # PWA Web App (React + Vite)
│   ├── src/
│   │   ├── routes/              # TanStack Router file-based routes
│   │   ├── components/          # Reusable UI components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/
│   │   │   ├── api/             # OpenAPI client ($api.ts)
│   │   │   └── utils.ts
│   │   ├── contexts/            # React Context (AuthContext)
│   │   ├── types/               # Generated TypeScript types (api.gen.ts)
│   │   └── main.tsx
│   ├── vite.config.ts           # Vite + PWA configuration
│   ├── package.json             # Bun-based dependencies
│   └── tsconfig.json
│
├── apps/
│   └── mobile/                  # React Native Expo app
│       ├── app/                 # Expo Router pages
│       ├── components/          # Reusable UI components
│       ├── hooks/               # Custom React hooks
│       ├── services/            # API client, storage
│       ├── stores/              # Zustand state stores
│       ├── types/               # TypeScript definitions (from OpenAPI)
│       └── utils/               # Helper functions
│
├── packages/
│   └── shared/                  # Shared types, constants, validation schemas
│       ├── types/               # TypeScript types (exported to both web & mobile)
│       └── validation/          # Zod schemas (shared validation)
│
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── routers/             # FastAPI route handlers (API v1)
│   │   ├── core/                # Config, security, deps
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic layer
│   │   ├── repositories/        # Data access layer
│   │   └── workers/             # Celery background tasks
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
│
├── mcp-postgres-server/         # PostgreSQL MCP server
│   ├── app/
│   │   └── main.py
│   ├── Dockerfile
│   ├── .env.example
│   └── requirements.txt
│
├── scripts/
│   ├── ralph-external-loop.sh   # Ralph Wiggum TDD automation
│   └── dev-servers.sh           # Start/stop development servers
│
├── ralph/                       # Ralph Wiggum plans directory
│   ├── _templates/
│   │   └── prd.template.json
│   └── README.md
│
├── e2e/                         # Playwright browser tests (web)
│
├── docker-compose.yml           # Local development
├── docker-compose.production.yml
├── .mcp.json                    # MCP server configuration
│
└── .claude/
    ├── settings.json            # Claude Code settings
    ├── commands/                # Slash commands
    │   ├── dev-servers.md
    │   ├── generate-types.md
    │   └── test.md
    └── skills/
        ├── ralph-wiggum/
        │   ├── SKILL.md
        │   └── reference.md
        ├── tanstack-router/
        ├── tanstack-query/
        └── playwright-testing/
```

---

## Phase 4: Copy Ralph Wiggum Files

### Step 4.1: Copy External Loop Script
- Source: `/home/sean/git_wsl/rcom/scripts/ralph-external-loop.sh`
- Destination: `/home/sean/git_wsl/{project-name}/scripts/ralph-external-loop.sh`
- Modifications needed:
  - Update default plan path from `/project/ralph/` to `./ralph/`
  - Update verification script paths

### Step 4.2: Copy Ralph Wiggum Skill
- Source: `/home/sean/git_wsl/rcom/.claude/skills/ralph-wiggum/SKILL.md`
- Destination: `/home/sean/git_wsl/{project-name}/.claude/skills/ralph-wiggum/SKILL.md`
- Source: `/home/sean/git_wsl/rcom/.claude/skills/ralph-wiggum/reference.md`
- Destination: `/home/sean/git_wsl/{project-name}/.claude/skills/ralph-wiggum/reference.md`
- Modifications needed:
  - Update project-specific paths
  - Remove rcom-specific commands
  - Add project-specific test commands

---

## Phase 5: Create MCP PostgreSQL Server

### Step 5.1: Copy MCP Server Structure (from spartans-hockey)
- Source: `/home/sean/git_wsl/spartans-hockey/mcp-postgres-server/`
- Destination: `/home/sean/git_wsl/{project-name}/mcp-postgres-server/`

### Step 5.2: Create Adapted main.py
Based on spartans-hockey pattern with project database configuration:
- **Dev database**: `ijack-dev.c9lvkaunz4dq.us-west-2.rds.amazonaws.com:5432/{project_name}`
- **Prod database**: `ijack.c9lvkaunz4dq.us-west-2.rds.amazonaws.com:5432/{project_name}`
- Uses existing ijack RDS instances with new database

### Step 5.3: Create Database on RDS
```sql
-- Connect to ijack-dev RDS and create database
CREATE DATABASE {project_name};
\c {project_name}
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
```

### Step 5.4: Create .mcp.json Configuration
```json
{
  "mcpServers": {
    "mcp-postgres": {
      "type": "http",
      "url": "http://{project-name}-mcp-postgres:5005/mcp"
    }
  }
}
```

---

## Phase 6: Create CLAUDE.md

Create comprehensive AI assistant instructions including:

1. **Project Overview**
   - Tech Stack: PWA (React + Vite) + React Native Expo + FastAPI + AWS RDS PostgreSQL + Stripe Connect
   - Core philosophy: DRY, SOLID, KISS, TDD
   - Three clients sharing one backend: Web PWA, iOS, Android

2. **Critical Rules**
   - TypeScript strict mode, no `any`/`unknown`
   - MCP PostgreSQL for all database operations
   - Playwright via subagent only
   - Ralph Wiggum for iterative development
   - Generate types from OpenAPI after backend changes

3. **Quick Commands**
   - Backend: `cd backend && uv run pytest`
   - Web Frontend: `cd frontend && bun run dev`
   - Mobile: `cd apps/mobile && bun run start`
   - Types: `bun run generate-types` (generates for both web and mobile)
   - Lint: `ruff check --fix . && ruff format .`

4. **Architecture Overview**
   - Clean architecture layers (API → Service → Repository → Model)
   - Module structure for Users, Bookings, Payments, Messaging
   - PWA uses TanStack Router + TanStack Query (following spartans-hockey)
   - Mobile uses Expo Router + Zustand + React Query

5. **Type Safety Pipeline**
   - Backend: FastAPI generates OpenAPI schema automatically
   - Web: `openapi-typescript` generates `api.gen.ts`
   - Mobile: Same types exported to `apps/mobile/types/`
   - Zero manual type duplication

6. **Database Configuration**
   - AWS RDS PostgreSQL with PostGIS
   - Connection pooling patterns
   - Alembic migrations
   - MCP server for development queries

7. **Skills & Agents Available**
   - ralph-wiggum (TDD automation)
   - database-operations
   - playwright-testing
   - tanstack-router
   - tanstack-query

---

## Phase 7: Create Supporting Files

### Step 7.1: Create .gitignore
Standard patterns for:
- Python (`__pycache__/`, `.venv/`, `*.pyc`)
- Node (`node_modules/`, `.expo/`)
- Environment (`.env`, `.env.local`)
- IDE (`.vscode/`, `.idea/`)
- Generated types (`api.gen.ts`)

### Step 7.2: Create README.md
Basic project introduction with:
- Project description
- Quick start instructions
- Tech stack overview (PWA + Mobile + Backend)
- Link to PRD.md

### Step 7.3: Create CONTEXT.md Template
```markdown
# {PROJECT_NAME} - Current Context

## Active Task
- **ID**: None
- **Status**: Project initialization

## Recently Completed
(None yet)

## Test Status
- Backend: Not yet set up
- Web Frontend: Not yet set up
- Mobile: Not yet set up

## Next Steps
1. Complete Phase 1 tasks from PRD
```

### Step 7.4: Create docker-compose.yml
Based on spartans-hockey pattern with additions for mobile:
```yaml
services:
  dev:
    # Development container with FastAPI + Vite
    ports:
      - "5175:5175"   # Vite PWA dev server
      - "8001:8001"   # FastAPI backend
    volumes:
      - .:/app

  mcp-postgres:
    # PostgreSQL MCP server for database queries
    ports:
      - "5005:5005"

  playwright-mcp:
    # E2E testing for PWA
    ports:
      - "8932:8932"

  redis:
    # Cache, sessions, WebSocket pub/sub
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Step 7.5: Create Claude Code Settings
`.claude/settings.json` with approved commands for Ralph Wiggum dangerous mode.

### Step 7.6: Create PWA Configuration (vite.config.ts)
Based on spartans-hockey PWA config:
- Service Worker registration
- Workbox runtime caching
- Manifest for home screen installation
- Offline support

### Step 7.7: Create Type Generation Scripts
```json
// package.json scripts
{
  "generate-types": "openapi-typescript http://localhost:8001/openapi.json -o frontend/src/types/api.gen.ts && cp frontend/src/types/api.gen.ts apps/mobile/types/"
}
```

---

## Phase 8: Create Initial Ralph Wiggum PRD

### Step 8.1: Create PRD for Phase 1 Foundation Tasks

Create `/home/sean/git_wsl/{project-name}/ralph/2026-01-28-feature-phase1-foundation/prd.json`

Target PRD Tasks 1.1-1.5 (modified for PWA + Mobile):
- **T001**: Initialize Monorepo Structure (Task 1.1) - includes `/frontend` PWA directory
- **T002**: Initialize Backend FastAPI Project (Task 1.2)
- **T003**: Configure Database Connection (Task 1.3 - AWS RDS)
- **T004**: Create User Database Model (Task 1.4)
- **T005**: Implement User Repository Layer (Task 1.5)
- **T006**: Initialize PWA Web Frontend (NEW - TanStack Router + Vite)

Each task will have:
- Clear acceptance criteria from the PRD
- Test requirements (TDD)
- Dependencies properly set

### Step 8.2: Create CONTEXT.md for the Ralph Plan

```markdown
# CONTEXT.md - Phase 1 Foundation

## Plan Overview
- **PRD**: `prd.json`
- **Created**: 2026-01-28
- **Type**: feature
- **Story Points**: 15

## Goal
Establish project infrastructure, database connectivity, and basic user management.
Set up both PWA web frontend and backend foundations.

## Key Principles
- **TDD**: Write tests alongside implementation
- **AWS RDS**: Use existing ijack RDS with project database
- **Clean Architecture**: API → Service → Repository → Model
- **Type Safety**: OpenAPI → TypeScript types for both web and mobile

---

## Progress Log

<!-- Append entries below as tasks are completed -->
```

---

## Phase 9: Initial Commit and Push

```bash
cd /home/sean/git_wsl/{project-name}
git add .
git commit -m "Initial project setup with PWA + Mobile + Ralph Wiggum TDD

- Hybrid architecture: PWA web app + React Native mobile
- Frontend: TanStack Router + Query (following spartans-hockey patterns)
- Mobile: Expo Router + Zustand (following PRD)
- CLAUDE.md for AI-assisted development
- Ralph Wiggum external loop script and skill
- MCP PostgreSQL server for AWS RDS database operations
- Docker Compose for local development
- Type generation pipeline: OpenAPI → TypeScript
- AWS RDS configuration using existing ijack instances

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

git push -u origin main
```

## Phase 10: Create Database on AWS RDS

```bash
# Connect to ijack-dev RDS via existing MCP or psql
psql -h ijack-dev.c9lvkaunz4dq.us-west-2.rds.amazonaws.com -U master -d postgres

# Create database
CREATE DATABASE {project_name};

# Connect and add extensions
\c {project_name}
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
```

---

## Key Files to Create

| File | Purpose |
|------|---------|
| `CLAUDE.md` | AI assistant instructions (critical) |
| `CONTEXT.md` | Current state tracking |
| `PRD.md` | Product requirements (copied + updated) |
| `PLAN.md` | Tech stack recommendations (copied + PWA added) |
| `frontend/vite.config.ts` | PWA configuration |
| `frontend/src/routes/__root.tsx` | TanStack Router global layout |
| `frontend/src/lib/api/client.ts` | OpenAPI fetch client |
| `scripts/ralph-external-loop.sh` | TDD automation loop |
| `scripts/dev-servers.sh` | Development server management |
| `.claude/skills/ralph-wiggum/SKILL.md` | Ralph Wiggum skill |
| `.claude/skills/ralph-wiggum/reference.md` | Quick reference |
| `.claude/commands/generate-types.md` | Type generation command |
| `mcp-postgres-server/app/main.py` | PostgreSQL MCP server |
| `docker-compose.yml` | Local development containers |
| `.mcp.json` | MCP server configuration |
| `.claude/settings.json` | Approved commands |
| `ralph/_templates/prd.template.json` | PRD template |

---

## Verification

After setup is complete:
1. Verify GitHub repo exists: `gh repo view mccarthysean/{project-name}`
2. Verify all files are committed: `git status`
3. Verify MCP server structure is correct
4. Verify Ralph Wiggum script is executable: `chmod +x scripts/ralph-external-loop.sh`
5. Test Claude Code can read CLAUDE.md
6. Verify PWA structure matches spartans-hockey patterns
7. Verify type generation script works

---

## Notes on AWS RDS vs Supabase

The PRD mentions Supabase, but per user request, we're using AWS RDS instead:

| PRD Component | Replacement |
|---------------|-------------|
| Supabase PostgreSQL | AWS RDS PostgreSQL with PostGIS |
| Supabase Realtime | FastAPI WebSockets + Redis Pub/Sub |
| Supabase Auth | Custom JWT auth (already in PRD) |
| Supabase Storage | AWS S3 (future) |

The MCP PostgreSQL server from spartans-hockey provides the same database introspection capabilities.

---

## Architecture Summary: PWA + Mobile Sharing Backend

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                   │
├─────────────────────┬─────────────────────┬─────────────────────┤
│    PWA Web App      │    iOS App          │    Android App      │
│  (React + Vite)     │  (React Native)     │  (React Native)     │
│  TanStack Router    │  Expo Router        │  Expo Router        │
│  TanStack Query     │  Zustand + RQ       │  Zustand + RQ       │
└─────────┬───────────┴──────────┬──────────┴──────────┬──────────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    FastAPI Backend      │
                    │    (OpenAPI Schema)     │
                    │    REST + WebSockets    │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼─────────┐ ┌──────────▼──────────┐ ┌────────▼────────┐
│  AWS RDS          │ │  Redis              │ │  Stripe Connect │
│  PostgreSQL       │ │  Cache/Pub-Sub      │ │  Payments       │
│  + PostGIS        │ │  WebSocket coord    │ │                 │
└───────────────────┘ └─────────────────────┘ └─────────────────┘
```

### Type Safety Flow
```
FastAPI Pydantic Schemas
         │
         ▼
   OpenAPI JSON Schema
         │
    ┌────┴────┐
    ▼         ▼
frontend/   apps/mobile/
api.gen.ts  types/api.gen.ts
```

---

## To Resume This Plan

Once you have chosen a project name:
1. Replace all `{project-name}` placeholders with the lowercase-hyphenated name (e.g., `dance-host`)
2. Replace all `{project_name}` placeholders with the lowercase-underscore name (e.g., `dance_host`)
3. Replace all `{PROJECT_NAME}` placeholders with the display name (e.g., `DanceHost`)
4. Run the commands in order from Phase 1 through Phase 10

**Source Files Referenced:**
- PRD: `/home/sean/git_wsl/DancePartner-PRD.md`
- Tech Plan: `/home/sean/git_wsl/DancePartner-Plan.md`
- Spartans Hockey (PWA patterns): `/home/sean/git_wsl/spartans-hockey/`
- Ralph Wiggum (TDD automation): `/home/sean/git_wsl/rcom/.claude/skills/ralph-wiggum/`
