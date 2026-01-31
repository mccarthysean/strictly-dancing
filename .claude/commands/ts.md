Think carefully and make a detailed plan to find and fix ALL TypeScript build errors one by one. Use the **typescript-fix** skill for systematic error detection and resolution with advanced type system analysis. Don't use scripts to fix multiple files at once, since these are too error-prone. Instead, think hard about each fix, and fix it manually. After each fix, run the type-check again to see whether it's actually fixed. ALWAYS use strong TypeScript typing instead of `any` or `unknown` types, since `bun run lint` (eslint) will catch all those `any` types as errors.

## Quick Development Iteration

For rapid development feedback, use the TypeScript compiler directly:

```bash
cd /workspaces/strictly-dancing/frontend
bun run tsc
```

This catches:
- TypeScript type errors
- Missing imports/exports
- Type mismatches
- Invalid syntax

## Full Build Validation

**MANDATORY before committing:** Run the full build to catch ALL errors:

```bash
cd /workspaces/strictly-dancing/frontend
bun run build
```

This catches everything that `tsc` catches PLUS:
- Vite bundling errors
- Missing asset references
- TanStack Router plugin errors
- All plugin failures

## Type Imports

The `api.gen.ts` file contains the OpenAPI types generated from FastAPI.
ALWAYS get the types for an API response by importing them. NEVER create custom TypeScript interfaces:

```typescript
import type { components } from "@/types/api.gen";
type HostProfileResponse = components["schemas"]["HostProfileResponse"];
```

## Code Quality and Formatting

Next, run ESLint to catch any additional issues. ALWAYS use strong TypeScript typing, rather than `any` and `unknown` types.

```bash
cd /workspaces/strictly-dancing/frontend
bun run lint
```

## Pre-Commit Checklist

Before committing TypeScript changes:
1. `bun run tsc` - Quick type-check passes
2. `bun run build` - **MANDATORY:** Full build passes
3. `bun run lint` - ESLint passes

Finally, commit the changes.
