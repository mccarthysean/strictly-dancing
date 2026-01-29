# Ralph Wiggum TDD Plans

This folder contains Ralph Wiggum iterative TDD development plans for the Strictly Dancing project.

## Reference Documents

- **PRD.md** - Product Requirements Document (full project requirements)
- **PLAN.md** - Technology stack and architecture plan
- **IMPLEMENTATION-PLAN.md** - Detailed implementation phases and steps

## Active Plans

### 2026-01-28-feature-phase1-foundation
Phase 1 Foundation setup:
- T001: Initialize Backend FastAPI Project ✅
- T002: Configure Backend Core Settings
- T003: Configure Database Connection
- T004: Initialize Alembic Migrations
- T005: Create User Database Model
- T006: Create User Pydantic Schemas
- T007: Implement User Repository Layer
- T008: Initialize PWA Frontend Project
- T009: Configure Frontend API Client
- T010: Create Homepage Route

## Running Ralph Wiggum

```bash
# Start the external loop (from project root)
./scripts/ralph-external-loop.sh 2026-01-28-feature-phase1-foundation --dangerous

# Monitor progress
tail -f ralph/2026-01-28-feature-phase1-foundation/ralph-loop-*.log

# Check task status
jq '.tasks | map({id, title, passes})' ralph/2026-01-28-feature-phase1-foundation/prd.json
```

## Plan Structure

Each plan folder contains:
- `prd.json` - Tasks with acceptance criteria (`passes: false` → `true`)
- `CONTEXT.md` - Append-only progress log
- `ralph-loop-*.log` - Iteration logs (gitignored)
