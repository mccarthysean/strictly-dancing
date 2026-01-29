# CONTEXT.md - Phase 1 Foundation

## Plan Overview
- **PRD**: `prd.json`
- **Created**: 2026-01-28
- **Type**: feature
- **Story Points**: 13

## Goal
Establish project infrastructure, FastAPI backend, database connectivity, user model, repository layer, and PWA frontend foundation.

## Key Principles
- **TDD**: Write tests alongside implementation, run tests AFTER
- **AWS RDS**: Use ijack-dev RDS with strictly_dancing database
- **Clean Architecture**: API -> Service -> Repository -> Model
- **Type Safety**: OpenAPI -> TypeScript types for frontend

## Project Structure
```
strictly-dancing/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py    # App entry point
│   │   ├── core/      # Config, database, dependencies
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── repositories/  # Data access layer
│   │   └── routers/   # API endpoints
│   ├── tests/         # pytest tests
│   └── alembic/       # Database migrations
└── frontend/          # PWA web app
    ├── src/
    │   ├── routes/    # TanStack Router pages
    │   ├── lib/api/   # OpenAPI client
    │   └── types/     # Generated TypeScript types
    └── vite.config.ts
```

## Task Dependencies
```
T001 (FastAPI init)
  └── T002 (Config)
       └── T003 (Database)
            └── T004 (Alembic)
                 └── T005 (User model)
                      └── T006 (Schemas)
                           └── T007 (Repository)

T001 (FastAPI init)
  └── T008 (Frontend init)
       └── T009 (API client)
            └── T010 (Homepage)
```

---

## Progress Log

<!-- Append entries below as tasks are completed -->

### Entry [E-001] 2026-01-28T21:35:00Z

**Task**: T001 - Initialize Backend FastAPI Project
**Status**: DONE
**Progress**: 1/10 tasks | Blockers: 0

**Accomplished**:
- Created pyproject.toml with FastAPI, SQLAlchemy, Pydantic, pytest dependencies
- Created backend/app/main.py with FastAPI app factory and health endpoint
- Created test suite with conftest.py and unit tests
- All 2 tests passing (test_health_endpoint_returns_200, test_health_endpoint_returns_json)

**Evidence**:
- Tests: All passing (2/2)
- Files: pyproject.toml, app/main.py, tests/unit/test_health.py

**Next**: T002 - Configure Backend Core Settings
