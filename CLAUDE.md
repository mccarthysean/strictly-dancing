# Strictly Dancing - Claude Code Instructions

## Project Overview

Global dance host marketplace connecting travelers and dance enthusiasts with qualified dance hosts.

**Stack:**
- **PWA Web App**: React + Vite + TanStack Router/Query
- **Mobile Apps**: React Native + Expo (iOS/Android)
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Payments**: Stripe Connect
- **Database**: AWS RDS PostgreSQL with PostGIS

## Core Philosophy

- **DRY, SOLID, KISS**: All code must follow these principles
- **TDD**: Test-Driven Development with Ralph Wiggum automation
- **Type Safety**: TypeScript strict mode, no `any`/`unknown`
- **Evidence First**: Verify patterns and APIs before implementation

## Critical Rules

### TypeScript Safety (Non-Negotiable)

- **NEVER** use `any` or `unknown` - find types in `api.gen.ts` or use generics
- **NEVER** declare return types - rely on TypeScript inference
- **NEVER** use `||` for coalescing - use `??` (nullish coalescing)
- **NEVER** create barrel files - import directly from source

### Database Operations (MCP Only)

- **ALWAYS** use MCP PostgreSQL tools (`mcp__mcp-postgres__*`), never psql or Python SQL
- Two databases: `dev` (ijack-dev RDS), `prod` (ijack RDS)

### Git Safety

- Only commit files YOU modified
- Use `git add <specific-files>` not `git add -A`
- NEVER amend commits after hook failures - create NEW commits

## Quick Commands

```bash
# Backend
cd backend && uv run pytest                    # Run tests
cd backend && uv run uvicorn app.main:app --reload --port 8001

# Web Frontend (PWA)
cd frontend && bun run dev                     # Dev server on port 5175
cd frontend && bun run build                   # Production build
cd frontend && bun run generate-types          # Generate API types

# Mobile
cd apps/mobile && bun run start                # Expo dev server

# Type Generation (CRITICAL after FastAPI changes)
bun run generate-types

# Python Linting
cd backend && ruff check --fix . && ruff format .

# TypeScript Linting
cd frontend && bun run tsc
```

## Architecture

### Directory Structure

```
strictly-dancing/
├── frontend/              # PWA Web App (React + Vite)
│   ├── src/
│   │   ├── routes/        # TanStack Router pages
│   │   ├── components/    # Reusable UI components
│   │   ├── lib/api/       # OpenAPI client ($api.ts)
│   │   ├── contexts/      # React Context (AuthContext)
│   │   └── types/         # Generated TypeScript types
│   └── vite.config.ts     # PWA configuration
│
├── apps/mobile/           # React Native Expo app
│   ├── app/               # Expo Router pages
│   ├── stores/            # Zustand state stores
│   └── types/             # TypeScript types (from OpenAPI)
│
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── routers/       # API endpoints
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── repositories/  # Data access layer
│   └── tests/
│
├── ralph/                 # Ralph Wiggum TDD plans
└── mcp-postgres-server/   # PostgreSQL MCP server
```

### Clean Architecture Layers

```
API Layer (FastAPI Routes)
        ↓
Service Layer (Business Logic)
        ↓
Repository Layer (Data Access)
        ↓
Model Layer (SQLAlchemy ORM)
```

## Type Safety Pipeline

```
FastAPI Pydantic Schemas
         ↓
   OpenAPI JSON Schema
         ↓
    ┌────┴────┐
    ▼         ▼
frontend/   apps/mobile/
api.gen.ts  types/api.gen.ts
```

**After ANY FastAPI change:**
```bash
cd frontend && bun run generate-types
```

## Database Configuration

- **Dev**: `ijack-dev.c9lvkaunz4dq.us-west-2.rds.amazonaws.com:5432/strictly_dancing`
- **Prod**: `ijack.c9lvkaunz4dq.us-west-2.rds.amazonaws.com:5432/strictly_dancing`

### Key Tables

| Table | Purpose |
|-------|---------|
| users | Base user accounts |
| host_profiles | Extended host info with PostGIS location |
| dance_styles | Master list of dance styles |
| host_dance_styles | Host-style junction with skill levels |
| bookings | Session records with Stripe payment IDs |
| reviews | Post-session ratings |
| conversations | Chat threads |
| messages | Chat messages |

## React Development (PWA)

### API Integration

```typescript
// ALWAYS use $api.useQuery() / $api.useMutation()
// NEVER use fetch() directly

import { $api } from '@/lib/api/$api';

// Query example
const { data: hosts } = $api.useQuery('get', '/api/v1/hosts', {
  params: { query: { lat: 40.7, lng: -74.0, radius_km: 10 } }
});

// Mutation example
const createBooking = $api.useMutation('post', '/api/v1/bookings');
```

### TanStack Router

```typescript
// ALWAYS use 'from' props in Link components
<Link from="/hosts" to="/hosts/$hostId" params={{ hostId: '123' }}>
  View Host
</Link>
```

## Mobile Development (React Native)

### State Management

- **Zustand**: Global state (auth, user preferences)
- **React Query**: Server state (API data)
- **expo-secure-store**: Token persistence

## Ralph Wiggum TDD

### Starting a Plan

```bash
# Create plan folder
mkdir -p ralph/$(date +%Y-%m-%d)-feature-<slug>

# Create prd.json with tasks
# Create CONTEXT.md for progress

# Run the loop
./scripts/ralph-external-loop.sh $(date +%Y-%m-%d)-feature-<slug> --dangerous
```

### Task Requirements

Every task MUST have:
1. Clear acceptance criteria (3-5 items)
2. Test requirements (unit + integration)
3. Dependencies specified
4. Phase (discovery/design/implementation/testing/validation)

## Anti-Patterns (Never Do)

- Use `any`/`unknown` in TypeScript
- Use `||` instead of `??`
- Create barrel files (index.ts re-exports)
- Skip linting before commits
- Auto-commit without explicit request
- Use psql or Python SQL queries instead of MCP
- Skip tests for new functionality
- Mark tasks complete without meeting all acceptance criteria

## Environment Variables

| Variable | Description |
|----------|-------------|
| DATABASE_URL | PostgreSQL connection string |
| REDIS_URL | Redis connection string |
| JWT_SECRET_KEY | RSA private key for JWT |
| STRIPE_SECRET_KEY | Stripe API secret |
| STRIPE_WEBHOOK_SECRET | Stripe webhook signing |

## Testing

### Backend (pytest)

```bash
cd backend && uv run pytest                    # All tests
cd backend && uv run pytest -v --tb=short      # Verbose with short traceback
cd backend && uv run pytest tests/unit/        # Unit tests only
```

### Frontend (vitest)

```bash
cd frontend && bun run test                    # All tests
cd frontend && bun run test:watch              # Watch mode
```

### Coverage Requirements

- Backend: Minimum 80% line coverage
- Frontend: Minimum 70% line coverage
- Critical paths (auth, payments): 100% coverage

## AWS RDS vs Supabase

The PRD mentions Supabase, but we're using AWS RDS instead:

| PRD Component | Replacement |
|---------------|-------------|
| Supabase PostgreSQL | AWS RDS PostgreSQL with PostGIS |
| Supabase Realtime | FastAPI WebSockets + Redis Pub/Sub |
| Supabase Auth | Custom JWT auth |
| Supabase Storage | AWS S3 (future) |
