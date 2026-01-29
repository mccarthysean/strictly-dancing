Lint and format Python and TypeScript code, fixing any problems found.

## Step 1: Python Linting (Ruff) and testing

```bash
cd /home/sean/git_wsl/strictly-dancing/backend
uv run ruff check --fix .
uv run ruff format .

# Ensure all tests run quickly and pass
uv run pytest
```

Follow Python PEP 8 and use type hints.

## Step 2: TypeScript Build

Run the full TypeScript build to catch type errors:

```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run build
```

ALWAYS use strong TypeScript typing instead of `any` or `unknown` types.

## Step 3: ESLint

```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run lint
```

## Step 4: Fix Issues

For each error found:

1. Read the file and understand the context
2. Fix the issue manually (don't use automated scripts)
3. Run the check again to verify the fix

## Type Imports

The `api.gen.ts` file contains OpenAPI types generated from the FastAPI backend.
ALWAYS import types from this file. NEVER create custom TypeScript interfaces:

```typescript
import type { components } from "@/types/api.gen";
type HostProfileResponse = components["schemas"]["HostProfileResponse"];
```

## Finally

Commit the changes when all checks pass.
