---
name: TypeScript Type Generation
description: Generate TypeScript types from FastAPI OpenAPI schemas. Run 'bun run generate-types' after any FastAPI changes to update frontend types and maintain type safety. CRITICAL - Always regenerate types after modifying FastAPI endpoints. Use when adding API endpoints, modifying Pydantic schemas, or fixing TypeScript API type errors.
allowed-tools: [Bash, Read]
---

# TypeScript Type Generation Skill

## Purpose
Generate and synchronize TypeScript type definitions from FastAPI's OpenAPI schema to maintain type safety between backend and frontend.

## When to Use This Skill
- After making FastAPI endpoint changes
- After modifying Pydantic schemas
- When TypeScript shows missing type errors
- Before committing backend changes that affect API contracts
- When frontend needs access to new API types

## Critical Workflow

### ALWAYS Generate Types After FastAPI Changes
```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run generate-types
```

This command:
1. Fetches OpenAPI schema from FastAPI at `http://localhost:8001/openapi.json`
2. Generates TypeScript types using `openapi-typescript`
3. Updates `src/types/api.gen.ts`

## Using Generated Types

### Import Pattern (ALWAYS Use This)
```typescript
import type { components } from "@/types/api.gen";

// Extract type from components.schemas
type HostProfile = components["schemas"]["HostProfileResponse"];
type Booking = components["schemas"]["BookingResponse"];
type User = components["schemas"]["UserResponse"];
```

### NEVER Create Custom Interfaces
```typescript
// INCORRECT: Don't create custom interfaces
interface HostProfileResponse {
  id: number;
  display_name: string;
}

// CORRECT: Use generated types
import type { components } from "@/types/api.gen";
type HostProfileResponse = components["schemas"]["HostProfileResponse"];
```

## Common Type Patterns

### API Response Types
```typescript
import type { components } from "@/types/api.gen";

// Single resource
type HostProfile = components["schemas"]["HostProfileResponse"];
type Booking = components["schemas"]["BookingResponse"];

// Create/Update types
type HostProfileCreate = components["schemas"]["HostProfileCreate"];
type HostProfileUpdate = components["schemas"]["HostProfileUpdate"];
```

### Using with React Query
```typescript
import type { components } from "@/types/api.gen";

type HostProfile = components["schemas"]["HostProfileResponse"];

const { data } = useQuery<HostProfile[]>({
  queryKey: ["hosts"],
  queryFn: () => api.hosts.list(),
});
```

## Type Generation Process

### Prerequisites
- FastAPI server must be running on `http://localhost:8001`
- OpenAPI schema endpoint available at `/openapi.json`

### Manual Generation Steps
If automatic generation fails:

1. **Verify FastAPI is running**:
```bash
curl http://localhost:8001/openapi.json | head -20
```

2. **Check for schema errors**:
```bash
curl http://localhost:8001/openapi.json | jq '.components.schemas | keys'
```

3. **Regenerate types**:
```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run generate-types
```

4. **Verify generation**:
```bash
ls -lh /home/sean/git_wsl/strictly-dancing/frontend/src/types/api.gen.ts
```

## Troubleshooting

### FastAPI Server Not Running
Start the FastAPI development server:
```bash
cd /home/sean/git_wsl/strictly-dancing/backend
uv run uvicorn app.main:app --reload --port 8001
```

### Type Not Found
If a type doesn't exist in `api.gen.ts`:
1. Check if the Pydantic model exists in FastAPI
2. Verify the schema is included in OpenAPI spec
3. Regenerate types: `bun run generate-types`
4. Check FastAPI endpoint has proper response_model

## Integration with Development Workflow

### Before Committing Backend Changes
```bash
# 1. Make FastAPI changes
cd /home/sean/git_wsl/strictly-dancing/backend
# ... edit files ...

# 2. Generate types
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run generate-types

# 3. Verify TypeScript build
bun run build

# 4. Commit both backend and generated types
git add .
```

## Best Practices

1. **Generate after every FastAPI change**: Don't let types get out of sync
2. **Never edit api.gen.ts manually**: It's auto-generated
3. **Always use generated types**: Never create custom interfaces for API types
4. **Commit generated types**: Include in version control for team sync
5. **Verify build after generation**: Run `bun run build` to catch type errors

## Type Safety Benefits

- **Compile-time safety**: Catch API contract mismatches before runtime
- **Autocomplete**: IDE provides accurate suggestions for API types
- **Refactoring confidence**: TypeScript catches breaking changes
- **Documentation**: Types serve as API documentation
- **Single source of truth**: FastAPI Pydantic models define types

## Integration
This skill automatically activates when:
- Making FastAPI endpoint changes
- Modifying Pydantic schemas
- Encountering TypeScript type errors related to API
- Seeing "Property does not exist" errors for API responses
- Preparing to commit backend changes
