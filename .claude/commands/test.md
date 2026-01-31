---
description: Run unit tests (backend pytest, frontend vitest)
---

# Run Unit Tests

Run the Strictly Dancing test suite using the centralized test script.

## Quick Commands

**ALWAYS use the test script:**

```bash
# Run ALL tests (backend + frontend)
bash /workspaces/strictly-dancing/scripts/run-tests.sh

# Backend only
bash /workspaces/strictly-dancing/scripts/run-tests.sh backend

# Frontend only
bash /workspaces/strictly-dancing/scripts/run-tests.sh frontend

# Fast mode (skip slow tests) - for quick iteration
bash /workspaces/strictly-dancing/scripts/run-tests.sh fast

# With coverage - before PRs
bash /workspaces/strictly-dancing/scripts/run-tests.sh coverage

# Re-run failed tests only
bash /workspaces/strictly-dancing/scripts/run-tests.sh failed

# Frontend watch mode
bash /workspaces/strictly-dancing/scripts/run-tests.sh watch
```

## Arguments: $ARGUMENTS

Pass arguments to the test runner:
```bash
bash /workspaces/strictly-dancing/scripts/run-tests.sh backend -v   # Verbose
bash /workspaces/strictly-dancing/scripts/run-tests.sh backend -x   # Stop on first failure
```

## Direct Commands (when needed)

```bash
# Backend - single test file
cd /workspaces/strictly-dancing/backend
uv run pytest tests/unit/test_auth.py -v

# Backend - single test function with output
uv run pytest tests/unit/test_auth.py::test_login -vvs

# Frontend - specific test
cd /workspaces/strictly-dancing/frontend
bun run test -- src/hooks/__tests__/useAuth.test.ts
```

## Test Organization

### Backend (`backend/tests/`)
| Directory | Description |
|-----------|-------------|
| `unit/` | Pure unit tests, mocked dependencies |
| `integration/` | API endpoint tests with database |
| `services/` | Business logic tests |

### Frontend (`frontend/src/**/__tests__/`)
| Pattern | Description |
|---------|-------------|
| `*.test.ts` | Unit tests for hooks, utilities |
| `*.test.tsx` | Component tests |

## Debugging Failed Tests

```bash
cd /workspaces/strictly-dancing/backend
uv run pytest tests/path/to/test.py::test_function -vvs --pdb
```
