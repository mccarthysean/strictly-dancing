# Generate TypeScript Types from OpenAPI

Generate TypeScript types from the FastAPI OpenAPI schema.

## Prerequisites

The FastAPI server must be running to fetch the OpenAPI schema.

## Command

```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run generate-types
```

This will:
1. Fetch the OpenAPI schema from `http://localhost:8001/openapi.json`
2. Generate TypeScript types in `src/types/api.gen.ts`

## Usage

Import types from the generated file:

```typescript
import type { components } from "@/types/api.gen";

type HostProfile = components["schemas"]["HostProfileResponse"];
type Booking = components["schemas"]["BookingResponse"];
type User = components["schemas"]["UserResponse"];
```

## When to Run

Run this command after:
- Adding or modifying FastAPI endpoints
- Changing Pydantic models
- Updating API response schemas

## Troubleshooting

If the command fails:
1. Ensure FastAPI is running: `curl http://localhost:8001/openapi.json`
2. Check for Python errors in the FastAPI logs
3. Restart the FastAPI server if needed
