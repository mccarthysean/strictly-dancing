---
name: TanStack Query API Integration
description: Use TanStack React Query with OpenAPI-generated $api client for type-safe data fetching. CRITICAL - Never use fetch() directly, always use $api.useQuery() and $api.useMutation() with OpenAPI types from api.gen.ts. Use when fetching API data, calling endpoints, implementing queries/mutations, handling loading states, or integrating with FastAPI backend.
allowed-tools: [Read, Write, Edit, Bash]
---

# TanStack Query API Integration Skill

## Purpose

Use TanStack React Query with OpenAPI-generated `$api` client for type-safe, efficient data fetching in React components.

## When to Use This Skill

- Fetching data from FastAPI backend
- Calling API endpoints from React components
- Implementing mutations (POST/PUT/DELETE)
- Managing loading and error states
- Type-safe API integration with OpenAPI types
- Replacing direct fetch() calls

## Critical Rules

### NEVER Use Direct fetch()

```typescript
// NEVER DO THIS
const response = await fetch('/api/endpoint');
const data = await response.json();

// ALWAYS DO THIS
const { data } = $api.useQuery("get", "/endpoint", {...});
```

**Exception**: Auth endpoints not in OpenAPI spec use native fetch with `credentials: "include"`.

### NEVER Use any or unknown Types

```typescript
// NEVER DO THIS
const data: any = await response.json();

// ALWAYS DO THIS
import type { components } from "@/types/api.gen";
type HostProfile = components["schemas"]["HostProfileResponse"];
```

## Import Patterns

### API Client Import
```typescript
import { $api } from "@/lib/api";
```

### OpenAPI Type Import
```typescript
import type { components } from "@/types/api.gen";

type HostProfile = components["schemas"]["HostProfileResponse"];
type Booking = components["schemas"]["BookingResponse"];
type User = components["schemas"]["UserResponse"];
```

## $api.useQuery Patterns

### Basic GET
```typescript
const { data, isLoading, isError, error } = $api.useQuery(
  "get",
  "/api/v1/hosts",
  {}
);
```

### With Path Parameters
```typescript
const { data: host } = $api.useQuery(
  "get",
  "/api/v1/hosts/{host_id}",
  {
    params: {
      path: { host_id: hostId },
    },
  },
  {
    enabled: !!hostId,
  }
);
```

### With Query Parameters
```typescript
const { data } = $api.useQuery(
  "get",
  "/api/v1/hosts",
  {
    params: {
      query: { lat: latitude, lng: longitude, radius_km: 10 },
    },
  },
  {
    enabled: !!latitude && !!longitude,
  }
);
```

### Data Transformation with select
```typescript
const { data: count } = $api.useQuery(
  "get",
  "/api/v1/bookings/pending/count",
  {},
  {
    select: (data) => data.count,
  }
);
```

## $api.useMutation Patterns

### Basic Mutation
```typescript
const createBooking = $api.useMutation("post", "/api/v1/bookings", {
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["get", "/api/v1/bookings"] });
  },
});

// Call with body
createBooking.mutate({ body: { host_id: 1, date: "2025-01-28" } });
```

### With Path Parameters
```typescript
const cancelBooking = $api.useMutation("delete", "/api/v1/bookings/{booking_id}", {
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["get", "/api/v1/bookings"] });
  },
});

// Call with params
cancelBooking.mutate({ params: { path: { booking_id: 123 } } });
```

### With Both Path and Body
```typescript
const updateHost = $api.useMutation("patch", "/api/v1/hosts/{host_id}", {
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["get", "/api/v1/hosts"] });
  },
});

// Call with both
updateHost.mutate({
  params: { path: { host_id: hostId } },
  body: { bio: "Updated bio" },
});
```

## Key Differences from axios

### Data Access - NO .data wrapper
```typescript
// openapi-react-query returns data directly
const { data: host } = useHost(hostId);

// WRONG - no .data property
host.data.display_name

// CORRECT - access directly
host.display_name
```

### Query Keys - Automatic
```typescript
// DON'T specify queryKey with $api
$api.useQuery("get", "/api/v1/hosts", {}, { queryKey: ["hosts"] }); // ERROR!

// Keys are auto-generated from method + path + params
$api.useQuery("get", "/api/v1/hosts", {}); // Key: ["get", "/api/v1/hosts", {}]
```

### Mutation Arguments - Structured
```typescript
// OLD axios pattern
mutation.mutate(hostId, hostData);

// NEW openapi-fetch pattern
mutation.mutate({
  params: { path: { host_id: hostId } },
  body: hostData,
});
```

## Paginated Data

API returns paginated responses with this structure:
```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
```

Access pattern:
```typescript
const { data: hostsData } = useHosts({ lat, lng });
const hosts = hostsData?.items || [];
const totalHosts = hostsData?.total || 0;
```

## Auth Endpoints (Native fetch)

Auth endpoints are NOT in OpenAPI spec. Use native fetch:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

const response = await fetch(`${API_BASE_URL}/auth/session`, {
  credentials: "include",
});
```

## Type Generation

After FastAPI changes:
```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run generate-types
```

This updates `src/types/api.gen.ts` with the latest OpenAPI schema.

## Best Practices

### DO:
1. **Use `$api.useQuery()` for GET requests**
2. **Use `$api.useMutation()` for mutations**
3. **Import types from `components["schemas"]`**
4. **Use `enabled` for conditional queries**
5. **Use `select` to transform data**
6. **Use `??` for nullish coalescing (not `||`)**
7. **Regenerate types after backend changes**

### DON'T:
1. **Don't use direct `fetch()` calls** (except auth)
2. **Don't use `any` or `unknown` types**
3. **Don't specify custom `queryKey`** - auto-generated
4. **Don't access `.data` on returned data** - it's direct
5. **Don't use old `api` import** - use `$api`

## Integration

This skill automatically activates when:
- Fetching data from API
- Calling FastAPI endpoints
- Using TanStack Query hooks
- Implementing data fetching in React
- Type-safe API integration needed
