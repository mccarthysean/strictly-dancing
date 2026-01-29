---
name: tanstack-table
description: Build flexible, headless data tables using TanStack Table (React Table v8) with React, TypeScript, and FastAPI integration. Create column definitions, implement sorting/filtering/pagination, customize cell renderers, handle row selection, integrate with shadcn/ui. MOBILE-FIRST design with horizontal scroll or card layouts. Ideal for custom designs, form integration, and datasets <10K rows. Use when building data tables, custom table UI, sorting/filtering, pagination, or full UI control.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# TanStack Table (React Table v8)

## Purpose

Headless UI library for creating customizable data tables with complete control over markup and styling. Use for datasets under 10K rows where custom design and form integration are priorities.

## When to Use

- Creating data tables with custom designs
- Implementing sorting, filtering, pagination
- Building tables with row selection or expansion
- Integrating tables with TanStack Form
- Need full control over table markup/styling
- Smaller datasets (<10K rows)

**Keywords**: TanStack Table, React Table, useReactTable, ColumnDef, createColumnHelper, headless table

## Quick Start

```typescript
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { useState, useMemo } from "react";

type Host = { id: number; name: string; rating: number };

function HostsTable({ data }: { data: Host[] }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });

  const columns = useMemo<ColumnDef<Host>[]>(
    () => [
      { accessorKey: "name", header: "Name" },
      { accessorKey: "rating", header: "Rating" },
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting, pagination },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return <TableGrid table={table} />;
}
```

## Critical Rules

### DO
- Memoize columns with `useMemo`
- Use `manualPagination: true` for server-side data
- Use `table.options.meta` for cell updates
- Import types from `@/types/api.gen`
- Use `createColumnHelper` for type-safe columns

### DON'T
- Use `any` or `unknown` types
- Mutate `row.original` directly
- Mix server and client pagination
- Forget to set `pageCount` for server-side
- Recreate columns on every render

## Mobile-First Design (CRITICAL)

### Strategy 1: Horizontal Scroll
```typescript
<div className="w-full overflow-x-auto">
  <table className="min-w-[600px] w-full">{/* content */}</table>
</div>
```

### Strategy 2: Responsive Column Visibility
```typescript
{
  accessorKey: "details",
  header: "Details",
  meta: { className: "hidden md:table-cell" },  // Hide on mobile
}
```

### Strategy 3: Card Layout on Mobile
```typescript
<>
  {/* Cards for mobile */}
  <div className="space-y-4 md:hidden">
    {data.map((item) => <Card key={item.id}>{/* content */}</Card>)}
  </div>
  {/* Table for desktop */}
  <div className="hidden md:block">
    <Table>{/* table content */}</Table>
  </div>
</>
```

## Row Models

| Model | Purpose |
|-------|---------|
| `getCoreRowModel()` | Required - basic row data |
| `getSortedRowModel()` | Client-side sorting |
| `getFilteredRowModel()` | Client-side filtering |
| `getPaginationRowModel()` | Client-side pagination |
| `getExpandedRowModel()` | Row expansion/sub-rows |

## Common Imports

```typescript
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getExpandedRowModel,
  flexRender,
  createColumnHelper,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState,
  type VisibilityState,
  type ExpandedState,
  type PaginationState,
} from "@tanstack/react-table";

import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
```

## Server-Side Pagination Pattern

```typescript
const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 50 });

const { data } = $api.useQuery("get", "/api/v1/hosts", {
  params: {
    query: {
      skip: pagination.pageIndex * pagination.pageSize,
      limit: pagination.pageSize,
    },
  },
});

const table = useReactTable({
  data: data?.items || [],
  columns,
  state: { pagination },
  onPaginationChange: setPagination,
  getCoreRowModel: getCoreRowModel(),
  manualPagination: true,
  pageCount: Math.ceil((data?.total || 0) / pagination.pageSize),
});
```

## Editable Cells Pattern

```typescript
// Prevent page reset on data changes
function useSkipper() {
  const shouldSkipRef = React.useRef(true);
  const shouldSkip = shouldSkipRef.current;
  const skip = React.useCallback(() => { shouldSkipRef.current = false; }, []);
  React.useEffect(() => { shouldSkipRef.current = true; });
  return [shouldSkip, skip] as const;
}

// Table with meta for updates
const table = useReactTable({
  data,
  columns,
  autoResetPageIndex,
  meta: {
    updateData: (rowIndex: number, columnId: string, value: unknown) => {
      skipAutoResetPageIndex();
      setData((old) => old.map((row, i) =>
        i === rowIndex ? { ...row, [columnId]: value } : row
      ));
    },
  },
});
```

## External Documentation

- [TanStack Table Docs](https://tanstack.com/table/latest/docs/introduction)
- [Shadcn/ui Table](https://ui.shadcn.com/docs/components/table)
