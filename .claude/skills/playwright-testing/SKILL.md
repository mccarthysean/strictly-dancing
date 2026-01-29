---
name: Playwright Testing
description: Token-optimized E2E browser testing with Playwright MCP achieving 80-90% token reduction through intelligent subagent delegation. Use for automated browser interactions, visual testing, form workflows, and UI validation.
allowed-tools: [mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_click, mcp__playwright__browser_type, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_console_messages, mcp__playwright__browser_wait_for, mcp__playwright__browser_fill_form, mcp__playwright__browser_hover, mcp__playwright__browser_resize, Read, Bash]
performance:
  token_reduction: 87%
  session_startup: 947 tokens (vs 13,678)
  e2e_test_average: 6K tokens (vs 45K)
---

# Playwright Testing Skill

## Purpose

Automate browser testing with Playwright MCP using intelligent token optimization through mandatory subagent delegation. Achieves 87% average token reduction.

## CRITICAL: ALL Playwright Operations -> Subagent

**ABSOLUTE RULE**: Never invoke Playwright MCP tools directly in main agent. ALL Playwright operations MUST use subagent delegation.

**Why?** Playwright consumes 500-1K tokens per operation:
- Navigation: 500-1K tokens
- Click/Type: 300-800 tokens
- Snapshot: 800+ tokens
- Screenshots: 2-5K tokens

**Result**: 93% token reduction via subagent (13,678 -> 947 tokens per session)

## When to Use

- Any Playwright MCP tool needed
- Browser automation tasks
- UI interaction testing
- User workflow validation
- Console error checking
- Visual testing
- Form workflows
- E2E testing workflows

**NO EXCEPTIONS** - If you need Playwright, use subagent.

## Quick Start: Testing Agent

**For ALL Playwright testing, use the general-purpose subagent:**

```typescript
Task({
  subagent_type: "general-purpose",
  description: "Test Strictly Dancing pages with Playwright",
  prompt: `Act as the Playwright Testing Agent. Test the following pages:

  Pages: /, /hosts, /login

  For each page:
  1. Navigate to http://host.docker.internal:5175/...
  2. Capture snapshot
  3. Take screenshot
  4. Check console for errors
  5. Verify key elements load

  Return structured summary with pass/fail status.
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
// CORRECT: Use host.docker.internal
mcp__playwright__browser_navigate({
  url: "http://host.docker.internal:5175/"
});

// WRONG: Don't use localhost
mcp__playwright__browser_navigate({
  url: "http://localhost:5175/"  // Won't work from container!
});
```

**URLs:**
- **Frontend**: `http://host.docker.internal:5175/`
- **Backend API**: `http://host.docker.internal:8001/`
- **API Docs**: `http://host.docker.internal:8001/docs`

## Prerequisites

Before running Playwright tests, ensure services are running:

```bash
# Start Playwright MCP container (via rcom)
cd /home/sean/git_wsl/rcom && docker compose up -d playwright-mcp

# Start development servers
cd /home/sean/git_wsl/strictly-dancing/backend && uv run uvicorn app.main:app --reload --port 8001
cd /home/sean/git_wsl/strictly-dancing/frontend && bun run dev

# Check container status
docker ps | grep playwright-mcp
```

## Token Optimization Strategies

### 1. Intelligent Caching (100% Reduction on Hits)
```typescript
// First visit: ~800 tokens
mcp__playwright__browser_navigate({ url: "http://host.docker.internal:5175/" });
// Second visit: 0 tokens (cached!)
mcp__playwright__browser_navigate({ url: "http://host.docker.internal:5175/" });
```

### 2. Strategic Snapshots (90% Reduction)
```typescript
// GOOD: Snapshot once, reuse refs
mcp__playwright__browser_snapshot(); // Get all refs
mcp__playwright__browser_click({ element: "Button 1", ref: "btn-1" });
mcp__playwright__browser_click({ element: "Button 2", ref: "btn-2" });

// WASTEFUL: Snapshot after every action
```

### 3. Batch Form Operations (73% Reduction)
```typescript
// Single batch call for form filling
mcp__playwright__browser_fill_form({
  fields: [
    { name: "Email", type: "textbox", ref: "input-email", value: "test@example.com" },
    { name: "Password", type: "textbox", ref: "input-password", value: "securepass123" }
  ]
});
```

## Core Operations

### Navigation & Waiting
```typescript
mcp__playwright__browser_navigate({ url: "http://host.docker.internal:5175/hosts" });
mcp__playwright__browser_wait_for({ text: "Find a Dance Host", time: 2 });
```

### Page Inspection
```typescript
mcp__playwright__browser_snapshot();  // Accessibility tree
mcp__playwright__browser_take_screenshot({ filename: "hosts-page.png" });
mcp__playwright__browser_console_messages();  // Check errors
```

### Interactions
```typescript
mcp__playwright__browser_click({ element: "Login button", ref: "btn-login" });
mcp__playwright__browser_type({ element: "Email", ref: "input-email", text: "test@example.com" });
```

## Performance Metrics

| Scenario | Standard | Optimized | Reduction |
|----------|----------|-----------|-----------|
| Session Startup | 13,678 | 947 | **93%** |
| Navigate + Snapshot | 8,000 | 800 | **90%** |
| Navigate (cached) | 8,000 | 0 | **100%** |
| Form Workflow | 33,000 | 4,000 | **88%** |
| **Full E2E Test** | **45,000** | **6,000** | **87%** |

## Common Test Scenarios

### Smoke Test (Quick Verification)
Test that all main pages load without errors:
```typescript
Task({
  subagent_type: "general-purpose",
  description: "Smoke test Strictly Dancing",
  prompt: `Test these pages:
    - http://host.docker.internal:5175/ (Home)
    - http://host.docker.internal:5175/hosts (Host Search)
    - http://host.docker.internal:5175/login (Login)

    For each: navigate, check console errors, verify page loads.
    Return pass/fail summary.`
})
```

### Authentication Flow Test
```typescript
Task({
  subagent_type: "general-purpose",
  description: "Test Strictly Dancing login flow",
  prompt: `Test the login flow:
    1. Navigate to http://host.docker.internal:5175/login
    2. Verify login form elements present
    3. Take snapshot of form
    4. Check for any console errors
    5. Verify email input accepts text

    Return structured results.`
})
```

### Host Search Test
```typescript
Task({
  subagent_type: "general-purpose",
  description: "Test Strictly Dancing host search",
  prompt: `Test the host search page:
    1. Navigate to http://host.docker.internal:5175/hosts
    2. Wait for data to load
    3. Take snapshot
    4. Verify host cards appear
    5. Check for API errors in console/network

    Return pass/fail with details.`
})
```

## Health Check

```bash
# Check container status
docker ps | grep playwright-mcp

# View container logs
docker logs rcom-playwright-mcp-1

# Test connectivity from container
docker exec rcom-playwright-mcp-1 nc -z host.docker.internal 5175
```

**"Browser is already in use" Error:**
This means another session is using the browser. Options:
1. Wait for other session to complete
2. Restart the container: `docker restart rcom-playwright-mcp-1`

**"Session not found" Error:**
1. Reconnect MCP server in Claude Code settings
2. Or restart container: `docker restart rcom-playwright-mcp-1`

## Related Skills

- `unit-testing` - Backend test suite execution
