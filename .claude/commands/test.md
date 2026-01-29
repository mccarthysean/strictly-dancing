---
description: Run unit tests (backend pytest, frontend vitest)
---

# Run Unit Tests

Run the Strictly Dancing test suite.

## Quick Commands

```bash
# Backend tests
cd /home/sean/git_wsl/strictly-dancing/backend && uv run pytest

# Frontend tests
cd /home/sean/git_wsl/strictly-dancing/frontend && bun run test

# Backend with coverage
cd /home/sean/git_wsl/strictly-dancing/backend && uv run pytest --cov=app --cov-report=term-missing

# Frontend with coverage
cd /home/sean/git_wsl/strictly-dancing/frontend && bun run test:coverage
```

## Arguments: $ARGUMENTS

If arguments provided, run the specified tests.

## Test Organization

### Backend (`backend/tests/`)
| Directory | Description |
|-----------|-------------|
| `unit/` | Pure unit tests, mocked dependencies |
| `integration/` | API endpoint tests with database |
| `services/` | Business logic tests |

### Frontend (`frontend/src/**/__tests__/`)
| File | Description |
|------|-------------|
| `*.test.ts` | Unit tests for hooks, utilities |
| `*.test.tsx` | Component tests |

## Debugging Failed Tests

```bash
# Run single failing test with verbose output
cd /home/sean/git_wsl/strictly-dancing/backend
uv run pytest tests/path/to/test.py::TestClass::test_name -vvs
```
