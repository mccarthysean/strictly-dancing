---
name: Code Quality
description: Maintain code quality with Ruff for Python and ESLint/TypeScript for frontend. Run linters, fix issues, and ensure consistent formatting. Use when linting code, fixing style issues, or preparing to commit.
allowed-tools: [Bash, Read, Edit]
---

# Code Quality Skill

## Purpose
Maintain code quality and consistent formatting for the Strictly Dancing project.

## When to Use This Skill
- Before committing code
- Fixing linting errors
- Formatting code
- Code review preparation
- CI/CD failures

## Python (Backend)

### Ruff Linting
```bash
cd /home/sean/git_wsl/strictly-dancing/backend

# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Full lint and format
uv run ruff check --fix . && uv run ruff format .
```

### Python Best Practices
- Use type hints for all function parameters and returns
- Follow PEP 8 style guidelines
- Use descriptive variable names
- Keep functions small and focused
- Use docstrings for public functions

### Example
```python
# Good
async def get_host_by_id(
    host_id: int,
    db: AsyncSession,
) -> HostProfile | None:
    """Fetch a host profile by their ID.

    Args:
        host_id: The unique host identifier.
        db: Database session.

    Returns:
        The host profile if found, None otherwise.
    """
    result = await db.execute(
        select(HostProfile).where(HostProfile.id == host_id)
    )
    return result.scalar_one_or_none()


# Bad
async def get_host(id, db):
    result = await db.execute(select(HostProfile).where(HostProfile.id == id))
    return result.scalar_one_or_none()
```

## TypeScript (Frontend)

### TypeScript Build
```bash
cd /home/sean/git_wsl/strictly-dancing/frontend

# Quick type check
bun run tsc --noEmit

# Full build (includes all checks)
bun run build
```

### ESLint
```bash
cd /home/sean/git_wsl/strictly-dancing/frontend

# Check for issues
bun run lint

# Auto-fix issues
bun run lint --fix
```

### TypeScript Best Practices
- Never use `any` or `unknown` types
- Import types from OpenAPI-generated schema
- Use nullish coalescing (`??`) not OR (`||`)
- Use `const` over `let` when value doesn't change
- Prefer explicit returns in arrow functions

### Example
```typescript
// Good
import type { components } from "@/types/api.gen";

type HostProfile = components["schemas"]["HostProfileResponse"];

const getHostName = (host: HostProfile): string => {
  return host.display_name ?? "Unknown";
};

// Bad
const getHostName = (host: any) => {
  return host.display_name || "Unknown";
};
```

## Pre-Commit Checklist

### Full Quality Check
```bash
# Backend
cd /home/sean/git_wsl/strictly-dancing/backend
uv run ruff check --fix .
uv run ruff format .

# Frontend
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run build
bun run lint

# Generate types if backend changed
bun run generate-types
```

## Common Issues

### Python

#### Import Order
Ruff auto-fixes import order. If you see import errors:
```bash
ruff check --fix --select I .
```

#### Line Length
Default max line length is 88 characters. Break long lines:
```python
# Too long
result = await db.execute(select(HostProfile).where(HostProfile.user_id == user_id).order_by(HostProfile.rating))

# Split across lines
result = await db.execute(
    select(HostProfile)
    .where(HostProfile.user_id == user_id)
    .order_by(HostProfile.rating)
)
```

### TypeScript

#### Missing Types
```typescript
// Error: Property 'name' does not exist
const name = data.name;

// Import the type
import type { components } from "@/types/api.gen";
type HostProfile = components["schemas"]["HostProfileResponse"];
const host: HostProfile = data;
const name = host.display_name;
```

#### Null/Undefined Handling
```typescript
// Using || can cause issues
const value = data.count || 0;  // If count is 0, returns 0 incorrectly

// Use nullish coalescing
const value = data.count ?? 0;  // Only returns 0 if count is null/undefined
```

## Integration
This skill automatically activates when:
- Running linters
- Fixing code style issues
- Preparing to commit code
- CI/CD check failures
- Code review
