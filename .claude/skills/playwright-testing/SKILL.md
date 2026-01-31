---
name: playwright-testing
description: Token-optimized E2E browser testing with Playwright MCP achieving 80-90% token reduction through mandatory subagent delegation. ALL Playwright operations MUST use the playwright-testing-agent. Use for automated browser interactions, visual testing, form workflows, and UI validation.
allowed-tools: [Task, Read, Bash]
performance:
  token_reduction: 87%
  session_startup: 947 tokens (vs 13,678)
  e2e_test_average: 6K tokens (vs 45K)
---

# Playwright Testing Skill

## Purpose

Automate browser testing with Playwright MCP using intelligent token optimization through **mandatory subagent delegation**. Achieves 87% average token reduction.

## 🚨 CRITICAL: ALL Playwright Operations → Subagent

**ABSOLUTE RULE**: Never invoke Playwright MCP tools directly in main agent. ALL Playwright operations MUST use the `playwright-testing-agent` subagent.

**Why?** Playwright consumes 500-1K tokens per operation:
- Navigation: 500-1K tokens
- Click/Type: 300-800 tokens
- Snapshot: 800+ tokens
- Screenshots: 2-5K tokens

**Result**: 93% token reduction via subagent (13,678 → 947 tokens per session)

## When to Use

- Any Playwright MCP tool needed
- Browser automation tasks
- UI interaction testing
- User workflow validation
- Console error checking
- Visual testing
- Form workflows
- E2E testing workflows

**NO EXCEPTIONS** — If you need Playwright, use subagent.

## Quick Start: Testing Agent

**For ALL Playwright testing, use the playwright-testing-agent:**

```typescript
Task({
  subagent_type: "playwright-testing-agent",
  description: "Test Strictly Dancing pages",
  prompt: `Test the following pages:

  Pages: /, /hosts, /login

  For each page:
  1. Navigate to http://host.docker.internal:5175/...
  2. Capture snapshot
  3. Take screenshot
  4. Check console for errors
  5. Verify key elements load

  Return structured summary with pass/fail status.
  Store screenshots in /workspaces/strictly-dancing/.playwright-screenshots/
  DO NOT include screenshots in response.`
})
```

**Benefits:**
- 80-90% less context usage - Screenshots stay in sub-agent
- Parallel testing - Multiple agents can run concurrently
- Focused reports - Only essential results returned

## Critical: Use host.docker.internal URLs

Playwright MCP runs in a Docker container and cannot access localhost directly.

```typescript
// ✅ CORRECT: Use host.docker.internal
mcp__playwright__browser_navigate({
  url: "http://host.docker.internal:5175/"
});

// ❌ WRONG: Don't use localhost
mcp__playwright__browser_navigate({
  url: "http://localhost:5175/"  // Won't work from container!
});
```

**URLs:**
- **Frontend**: `http://host.docker.internal:5175/`
- **Backend API**: `http://host.docker.internal:8001/`
- **API Docs**: `http://host.docker.internal:8001/docs`

## Common Test Scenarios

### Smoke Test (Quick Verification)
```typescript
Task({
  subagent_type: "playwright-testing-agent",
  description: "Smoke test Strictly Dancing",
  prompt: `Test these pages:
    - http://host.docker.internal:5175/ (Home)
    - http://host.docker.internal:5175/hosts (Host Search)
    - http://host.docker.internal:5175/login (Login)
    - http://host.docker.internal:5175/register (Register)

    For each: navigate, check console errors, verify page loads.
    Return pass/fail summary.`
})
```

### Authentication Flow Test
```typescript
Task({
  subagent_type: "playwright-testing-agent",
  description: "Test login flow",
  prompt: `Test the magic link login flow:
    1. Navigate to http://host.docker.internal:5175/login
    2. Verify login form elements present
    3. Take snapshot of form
    4. Enter email: test@example.com
    5. Click submit button
    6. Check for any console errors
    7. Verify success message

    Return structured results.`
})
```

### Host Search Test
```typescript
Task({
  subagent_type: "playwright-testing-agent",
  description: "Test host search",
  prompt: `Test the host search page:
    1. Navigate to http://host.docker.internal:5175/hosts
    2. Wait for host cards to load
    3. Take snapshot
    4. Verify search filters are present
    5. Verify host cards display correctly
    6. Check for API errors in console/network

    Return pass/fail with details.`
})
```

### Booking Flow Test
```typescript
Task({
  subagent_type: "playwright-testing-agent",
  description: "Test booking flow",
  prompt: `Test the complete booking workflow:
    1. Navigate to http://host.docker.internal:5175/hosts
    2. Click on a host card
    3. Verify host profile loads
    4. Click "Book Now" button
    5. Fill booking form (date, time, notes)
    6. Submit booking
    7. Verify confirmation

    Return comprehensive test results with screenshots.`
})
```

## Token Optimization Strategies

### 1. Always Use Subagent (93% Reduction)
```typescript
// ✅ CORRECT: Use subagent for all Playwright operations
Task({
  subagent_type: "playwright-testing-agent",
  description: "Test page",
  prompt: "Navigate to /hosts and take a screenshot"
})

// ❌ WRONG: Never call Playwright directly
mcp__playwright__browser_navigate({ url: "..." })  // Don't do this!
```

### 2. Batch Multiple Pages in One Agent Call
```typescript
// ✅ EFFICIENT: Test multiple pages in one agent call
Task({
  subagent_type: "playwright-testing-agent",
  prompt: `Test these 5 pages: /, /hosts, /login, /register, /about
           Return summary for all pages.`
})

// ❌ WASTEFUL: Separate agent calls for each page
```

### 3. Request Structured Summaries Only
```typescript
// ✅ GOOD: Request summary without screenshots in response
prompt: `... Return pass/fail summary. DO NOT include screenshots in response.`

// ❌ WASTEFUL: Requesting screenshot data in response
```

## Performance Metrics

| Scenario | Standard | With Subagent | Reduction |
|----------|----------|---------------|-----------|
| Session Startup | 13,678 | 947 | **93%** |
| Navigate + Snapshot | 8,000 | 800 | **90%** |
| Form Workflow | 33,000 | 4,000 | **88%** |
| **Full E2E Test** | **45,000** | **6,000** | **87%** |

## Prerequisites

Before running Playwright tests:

```bash
# 1. Start development servers
bash /workspaces/strictly-dancing/scripts/dev-servers.sh start

# 2. Verify servers are running
bash /workspaces/strictly-dancing/scripts/dev-servers.sh status

# 3. Check Playwright MCP container is running
docker ps | grep playwright-mcp
```

## Health Check

```bash
# Check Playwright container status
docker ps | grep playwright-mcp

# View container logs
docker logs <playwright-container-name>

# Test connectivity from container
docker exec <playwright-container-name> nc -z host.docker.internal 5175
```

## Troubleshooting

**"Browser is already in use" Error:**
1. Wait for other session to complete
2. Restart the container: `docker restart <playwright-container-name>`

**"Session not found" Error:**
1. Reconnect MCP server in Claude Code settings (Ctrl/Cmd + Shift + P → MCP: Manage Servers)
2. Or restart the Playwright MCP container

**Page not loading:**
1. Verify dev servers: `bash /workspaces/strictly-dancing/scripts/dev-servers.sh status`
2. Ensure URL uses `host.docker.internal` not `localhost`
3. Check correct port (5175 for frontend, 8001 for backend)

## Related Skills

- `unit-testing` - Fast pytest and vitest tests
- `development-servers` - Starting the dev environment

## Related Agents

- `playwright-testing-agent` - The specialized agent for all Playwright operations
