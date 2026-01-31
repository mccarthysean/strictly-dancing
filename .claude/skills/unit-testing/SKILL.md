---
name: unit-testing
description: Run fast unit tests for backend (pytest) and frontend (vitest). Use when running tests, debugging test failures, checking if tests pass, or after code changes that need verification.
allowed-tools: [Bash, Read, Grep]
---

# Unit Testing

Run the Strictly Dancing test suite quickly and efficiently.

## Quick Start - Use the Test Script

**ALWAYS use the test script for running tests:**

```bash
# Run ALL tests (backend + frontend)
bash /workspaces/strictly-dancing/scripts/run-tests.sh

# Backend only
bash /workspaces/strictly-dancing/scripts/run-tests.sh backend

# Frontend only
bash /workspaces/strictly-dancing/scripts/run-tests.sh frontend

# Fast mode (skip slow tests)
bash /workspaces/strictly-dancing/scripts/run-tests.sh fast

# With coverage
bash /workspaces/strictly-dancing/scripts/run-tests.sh coverage

# Re-run failed tests only
bash /workspaces/strictly-dancing/scripts/run-tests.sh failed

# Frontend watch mode
bash /workspaces/strictly-dancing/scripts/run-tests.sh watch
```

## Direct Commands (when needed)

### Backend Tests
```bash
cd /workspaces/strictly-dancing/backend

# Quick run with minimal output
uv run pytest tests/ -q

# Stop on first failure
uv run pytest tests/ -x

# Verbose output
uv run pytest tests/ -v

# Single test file
uv run pytest tests/unit/test_auth.py -v

# Single test function
uv run pytest tests/unit/test_auth.py::test_login -vvs

# With coverage
uv run pytest tests/ --cov=app --cov-report=term-missing
```

### Frontend Tests
```bash
cd /workspaces/strictly-dancing/frontend

# Run all tests
bun run test

# Watch mode
bun run test:watch

# With coverage
bun run test:coverage
```

## Test Organization

### Backend (`/workspaces/strictly-dancing/backend/tests/`)
| Directory | Description |
|-----------|-------------|
| `unit/` | Pure unit tests, mocked dependencies |
| `integration/` | API endpoint tests with database |
| `services/` | Business logic tests |
| `routers/` | API endpoint integration |

### Frontend (`/workspaces/strictly-dancing/frontend/src/**/__tests__/`)
| Pattern | Description |
|---------|-------------|
| `*.test.ts` | Unit tests for hooks, utilities |
| `*.test.tsx` | Component tests |

## Writing New Tests

### Backend Pattern
```python
import pytest
from tests.factories import UserFactory, HostProfileFactory

@pytest.mark.asyncio
async def test_host_profile_creation(db_session):
    """Test creating a new host profile."""
    # Arrange
    user = await UserFactory.create(db_session)

    # Act
    host = await HostProfileFactory.create(db_session, user_id=user.id)

    # Assert
    assert host.id is not None
    assert host.user_id == user.id
```

### Frontend Pattern
```typescript
import { renderHook, waitFor } from "@testing-library/react";
import { createWrapper } from "@/test/utils";

it("fetches host profiles", async () => {
  const { result } = renderHook(
    () => useHostProfiles(),
    { wrapper: createWrapper() }
  );

  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data).toHaveLength(3);
});
```

## Test Infrastructure

### Backend
- **Database**: In-memory SQLite (fast, no PostgreSQL needed)
- **Fixtures**: `tests/conftest.py` - db_session, test clients
- **Factories**: `tests/factories.py` - UserFactory, HostProfileFactory, BookingFactory
- **Mocks**: `tests/mocks.py` - MockEmailService, MockStripeService

### Frontend
- **Runner**: Vitest with jsdom environment
- **API Mocking**: MSW (Mock Service Worker)
- **Setup**: `src/test/setup.ts`
- **Handlers**: `src/test/mocks/handlers.ts`

## Debugging Failed Tests

```bash
# Run single failing test with full output
cd /workspaces/strictly-dancing/backend
uv run pytest tests/path/to/test.py::test_function_name -vvs

# Show local variables on failure
uv run pytest tests/ -l

# Drop into debugger on failure
uv run pytest tests/ --pdb
```

## Marking Slow Tests

For tests that take >1 second, mark them as slow:

```python
@pytest.mark.slow
def test_complex_booking_flow(db_session):
    """This test involves multiple API calls."""
    ...
```

Then skip them during development:
```bash
bash /workspaces/strictly-dancing/scripts/run-tests.sh fast
```

## Pre-Commit Testing

Always run tests before committing:
```bash
# Quick check
bash /workspaces/strictly-dancing/scripts/run-tests.sh fast

# Full check before PR
bash /workspaces/strictly-dancing/scripts/run-tests.sh coverage
```

## Coverage Requirements

- **Backend**: Minimum 80% line coverage
- **Frontend**: Minimum 70% line coverage
- **Critical paths** (auth, payments): 100% coverage

Coverage reports are generated at:
- Backend: `/workspaces/strictly-dancing/backend/htmlcov/index.html`
- Frontend: `/workspaces/strictly-dancing/frontend/coverage/index.html`
