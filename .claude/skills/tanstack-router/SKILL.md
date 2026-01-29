---
name: TanStack Router Patterns
description: Implement TanStack Router with type-safe routes, navigation, and file-based routing. Create routes, handle route parameters, manage search params, and implement layouts. CRITICAL - Always use 'from' props in Link components. Use when creating routes, implementing routing, fixing router errors, or adding navigation.
allowed-tools: [Read, Write, Edit, Bash]
---

# TanStack Router Patterns Skill

## Purpose
Implement TanStack Router with proper type safety and file-based routing for the Strictly Dancing frontend.

## When to Use This Skill
- Creating TanStack Router routes
- Fixing router type errors
- Navigation with Link components
- Search parameter type safety
- Route layouts

## Critical: Link Components

### Always Use `from` Props
```typescript
// CORRECT: Explicit routing context
<Link from="/hosts" to="/hosts/$hostId" params={{ hostId }}>
  View Host
</Link>

<Link from="/hosts/$hostId" to=".." search={(prev) => prev}>
  Back
</Link>

// INCORRECT: Missing from prop causes type errors
<Link to="/hosts">
  Hosts
</Link>
```

## File-Based Routing

### Route File Structure
```
src/routes/
├── __root.tsx           # Root route with layout
├── index.tsx            # Home route (/)
├── hosts/
│   ├── index.tsx        # /hosts
│   └── $hostId.tsx      # /hosts/:hostId
├── bookings/
│   ├── index.tsx        # /bookings
│   └── $bookingId.tsx   # /bookings/:bookingId
└── profile/
    └── index.tsx        # /profile
```

### Route File Pattern
```typescript
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/hosts/$hostId")({
  component: HostDetail,
  loader: async ({ params }) => {
    return fetchHost(params.hostId);
  },
});

function HostDetail() {
  const host = Route.useLoaderData();
  const { hostId } = Route.useParams();

  return <div>{host.display_name}</div>;
}
```

## Router Creation

### Root Route
```typescript
// src/routes/__root.tsx
import { createRootRoute, Outlet } from "@tanstack/react-router";

export const Route = createRootRoute({
  component: RootComponent,
});

function RootComponent() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main>
        <Outlet />
      </main>
    </div>
  );
}
```

## Search Parameter Type Safety

### Define Search Params Schema
```typescript
import { z } from "zod";

const hostSearchSchema = z.object({
  page: z.number().optional().default(1),
  search: z.string().optional(),
  danceStyle: z.string().optional(),
  sort: z.enum(["rating", "price", "distance"]).optional(),
});

export const Route = createFileRoute("/hosts")({
  validateSearch: hostSearchSchema,
  component: HostList,
});
```

### Type-Safe Search Updates
```typescript
<Link
  from="/hosts"
  to="/hosts"
  search={(prev) => ({ ...prev, page: 2 })}
>
  Next Page
</Link>

// In component
const navigate = Route.useNavigate();

navigate({
  search: (prev) => ({
    ...prev,
    sort: "rating",
  }),
});
```

## Navigation Patterns

### Programmatic Navigation
```typescript
import { useNavigate } from "@tanstack/react-router";

const MyComponent = () => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate({
      to: "/hosts/$hostId",
      params: { hostId: "123" },
      search: { tab: "reviews" },
    });
  };

  return <button onClick={handleClick}>Go to Host</button>;
};
```

## Loader Patterns

### Data Loading
```typescript
export const Route = createFileRoute("/hosts/$hostId")({
  loader: async ({ params }) => {
    const host = await fetchHost(params.hostId);
    if (!host) {
      throw new Error("Host not found");
    }
    return { host };
  },
  component: HostDetail,
});

function HostDetail() {
  const { host } = Route.useLoaderData();
  return <div>{host.display_name}</div>;
}
```

## Error Handling

### Error Boundaries
```typescript
export const Route = createFileRoute("/hosts/$hostId")({
  component: HostDetail,
  errorComponent: ({ error }) => (
    <div>
      <h1>Error Loading Host</h1>
      <p>{error.message}</p>
    </div>
  ),
  notFoundComponent: () => <div>Host not found</div>,
});
```

## Layout Routes

### Layout Pattern
```typescript
// routes/_layout.tsx
export const Route = createFileRoute("/_layout")({
  component: Layout,
});

function Layout() {
  return (
    <div>
      <Sidebar />
      <Outlet />
    </div>
  );
}

// routes/_layout/dashboard.tsx
export const Route = createFileRoute("/_layout/dashboard")({
  component: Dashboard,
});
```

## Common Pitfalls

### Missing `from` Props
```typescript
// Causes type errors in multi-route apps
<Link to="/somewhere">Go</Link>

// Should be:
<Link from="/current" to="/somewhere">Go</Link>
```

### Incorrect Search Type
```typescript
// Don't use any
search: (prev: any) => ({ ...prev, page: 2 })

// Use proper type
search: (prev: SearchParams) => ({ ...prev, page: 2 })
```

## Build and Type Check

```bash
cd /home/sean/git_wsl/strictly-dancing/frontend
bun run build  # Includes route tree generation
```

## Integration
This skill automatically activates when:
- Working with TanStack Router
- Creating or modifying routes
- Fixing router type errors
- Implementing navigation
- Link component usage
- Search parameter handling
