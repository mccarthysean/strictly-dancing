---
name: unit-testing
description: Run fast unit tests for backend (pytest) and frontend (vitest). Use when running tests, debugging test failures, checking if tests pass, or after code changes that need verification.
allowed-tools: [Bash, Read, Grep]
---

# Unit Testing

Run the Strictly Dancing test suite quickly and efficiently.

## Quick Start

### Backend Tests
```bash
# Run ALL backend tests
cd /home/sean/git_wsl/strictly-dancing/backend && uv run pytest

# Quick run with minimal output
cd /home/sean/git_wsl/strictly-dancing/backend && uv run pytest tests/ -q

# Stop on first failure
cd /home/sean/git_wsl/strictly-dancing/backend && uv run pytest tests/ -x

# Verbose output
cd /home/sean/git_wsl/strictly-dancing/backend && uv run pytest tests/ -v

# With coverage
cd /home/sean/git_wsl/strictly-dancing/backend && uv run pytest tests/ --cov=app --cov-report=term-missing
```

### Frontend Tests
```bash
# Run ALL frontend tests
cd /home/sean/git_wsl/strictly-dancing/frontend && bun run test

# Watch mode
cd /home/sean/git_wsl/strictly-dancing/frontend && bun run test:watch

# With coverage
cd /home/sean/git_wsl/strictly-dancing/frontend && bun run test:coverage
```

## Test Organization

### Backend (`/home/sean/git_wsl/strictly-dancing/backend/tests/`)
| Directory | Description |
|-----------|-------------|
| `unit/` | Pure unit tests, mocked dependencies |
| `integration/` | API endpoint tests with database |
| `services/` | Business logic tests |
| `routers/` | API endpoint integration |

### Frontend (`/home/sean/git_wsl/strictly-dancing/frontend/src/**/__tests__/`)
| File | Description |
|------|-------------|
| `*.test.ts` | Unit tests for hooks, utilities |
| `*.test.tsx` | Component tests |

## Writing New Tests

### Backend Pattern
```python
@pytest.mark.asyncio
async def test_something(self, db_session):
    """One-line description of what this tests."""
    # Arrange
    host = await create_test_host(db_session, display_name="Test Host")

    # Act
    result = await some_function(db_session, host.id)

    # Assert
    assert result is not None
```

### Frontend Pattern
```typescript
it("does something", async () => {
  // Render with query client
  const { result } = renderHook(() => useSomeHook(), { wrapper: createWrapper() });

  // Wait for async operations
  await waitFor(() => expect(result.current.isSuccess).toBe(true));

  // Assert
  expect(result.current.data).toEqual(expected);
});
```

## Debugging Failed Tests

```bash
# Run single failing test with verbose output
cd /home/sean/git_wsl/strictly-dancing/backend
uv run pytest tests/path/to/test.py::TestClass::test_name -vvs
```

## Test Infrastructure

### Backend
- **Database**: In-memory SQLite (fast, no PostgreSQL needed)
- **Fixtures**: `tests/conftest.py` - db_session, test clients
- **Factories**: `tests/factories.py` - UserFactory, HostProfileFactory, etc.
- **Mocks**: `tests/mocks.py` - MockEmailService, etc.

### Frontend
- **Runner**: Vitest with jsdom environment
- **API Mocking**: MSW (Mock Service Worker)
- **Setup**: `src/test/setup.ts`
- **Handlers**: `src/test/mocks/handlers.ts`

## Pre-Commit Testing

Always run tests before committing:
```bash
# Backend
cd /home/sean/git_wsl/strictly-dancing/backend
uv run ruff check --fix . && uv run ruff format .
uv run pytest

# Frontend
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run lint
bun run test
```
