---
name: playwright-testing-agent
description: Specialized sub-agent for browser automation and visual testing that operates independently to reduce main agent context usage. Use for ALL Playwright operations.
tools: mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_console_messages, mcp__playwright__browser_network_requests, mcp__playwright__browser_wait_for, mcp__playwright__browser_click, mcp__playwright__browser_type, mcp__playwright__browser_fill_form, mcp__playwright__browser_hover, mcp__playwright__browser_resize
---

# Playwright Testing Agent

**Purpose**: Specialized sub-agent for browser automation and visual testing that operates independently to reduce main agent context usage.

## Agent Capabilities

This agent specializes in:
- Browser navigation and interaction via Playwright MCP
- Visual regression testing with screenshots
- Page accessibility validation
- Performance monitoring (console errors, network requests)
- Multi-page testing workflows
- Test result summarization and reporting

## When to Use This Agent

**ABSOLUTE RULE**: Use this agent for ALL Playwright operations. Never invoke Playwright MCP tools directly in the main agent.

Use the Playwright Testing Agent when you need to:
- Test multiple pages in sequence without polluting main context
- Capture and compare visual screenshots
- Verify UI components and design implementation
- Check for console errors or network issues
- Validate responsive design across viewports
- Test user workflows and interactions
- Fill forms and test authentication flows

## Invocation Pattern

```typescript
Task({
  subagent_type: "playwright-testing-agent",
  description: "Test Strictly Dancing pages with Playwright",
  prompt: `Test the following pages:

## Pages to Test
- http://host.docker.internal:5175/ (Home)
- http://host.docker.internal:5175/hosts (Host Search)
- http://host.docker.internal:5175/login (Login)

## Testing Requirements
For each page:
1. Navigate to the page
2. Wait for content to load
3. Capture page snapshot for structure validation
4. Take screenshot for visual validation
5. Check console for errors/warnings
6. Verify key UI elements are present

## Test Results Format
For each page, return:
- Page URL
- Console status (errors/warnings count)
- Key elements found (yes/no)
- Screenshot filename
- Overall status (PASS/FAIL)

## Important
- Use Playwright MCP tools exclusively
- Keep each test concise
- Return structured summary without screenshots in context
- Store screenshots in /workspaces/strictly-dancing/.playwright-screenshots/`
})
```

## URL Configuration

**CRITICAL**: Playwright MCP runs in a Docker container and cannot access localhost directly.

| Service | URL from Playwright Container |
|---------|------------------------------|
| Frontend (Vite) | `http://host.docker.internal:5175/` |
| Backend (FastAPI) | `http://host.docker.internal:8001/` |
| API Docs | `http://host.docker.internal:8001/docs` |

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

## Expected Output Format

```markdown
## Playwright Testing Agent Report

### Test Summary
- Total Pages Tested: 3
- Passed: 3
- Failed: 0
- Warnings: 1

### Page-by-Page Results

#### 1. Home Page (/)
- **URL**: http://host.docker.internal:5175/
- **Status**: ✅ PASS
- **Console**: 0 errors, 0 warnings
- **Key Elements**:
  - ✅ Hero section with CTA
  - ✅ Navigation bar
  - ✅ Footer
- **Screenshot**: home-page.png

#### 2. Host Search (/hosts)
- **URL**: http://host.docker.internal:5175/hosts
- **Status**: ✅ PASS
- **Console**: 0 errors, 1 warning (React dev mode)
- **Key Elements**:
  - ✅ Search filters
  - ✅ Host cards grid
  - ✅ Map component
- **Screenshot**: hosts-page.png

#### 3. Login (/login)
- **URL**: http://host.docker.internal:5175/login
- **Status**: ✅ PASS
- **Console**: 0 errors, 0 warnings
- **Key Elements**:
  - ✅ Email input field
  - ✅ Submit button
  - ✅ Magic link instructions
- **Screenshot**: login-page.png

### Issues Found
- None

### Recommendations
- Consider adding loading skeletons for better UX
```

## Common Test Scenarios

### Smoke Test (All Main Pages)
```typescript
Task({
  subagent_type: "playwright-testing-agent",
  description: "Smoke test all pages",
  prompt: `Quick smoke test of main pages:
    - http://host.docker.internal:5175/
    - http://host.docker.internal:5175/hosts
    - http://host.docker.internal:5175/login
    - http://host.docker.internal:5175/register

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
    2. Verify email input is present
    3. Enter test email: test@example.com
    4. Click submit button
    5. Verify success message appears
    6. Check for any console errors

    Return structured results with screenshots.`
})
```

### Host Profile Test
```typescript
Task({
  subagent_type: "playwright-testing-agent",
  description: "Test host profile page",
  prompt: `Test host profile display:
    1. Navigate to http://host.docker.internal:5175/hosts
    2. Wait for host cards to load
    3. Click on first host card
    4. Verify profile page loads with:
       - Host photo
       - Dance styles list
       - Availability calendar
       - Book now button
    5. Take screenshots at each step

    Return pass/fail with details.`
})
```

### Booking Flow Test
```typescript
Task({
  subagent_type: "playwright-testing-agent",
  description: "Test booking flow",
  prompt: `Test the booking workflow:
    1. Navigate to a host profile
    2. Click "Book Now" button
    3. Select date and time
    4. Fill booking form
    5. Verify booking confirmation
    6. Check for any API errors in network tab

    Return comprehensive test results.`
})
```

## Agent Benefits

- **Reduced Context Usage**: Screenshots and verbose Playwright output stay in sub-agent
- **Parallel Testing**: Multiple test agents can run concurrently
- **Focused Reports**: Only essential results returned to main agent
- **Reusable**: Same agent pattern for all testing workflows
- **Scalable**: Can test many pages without context exhaustion

## Prerequisites

Before testing, ensure services are running:
```bash
# Start development servers
bash /workspaces/strictly-dancing/scripts/dev-servers.sh start

# Verify servers are running
bash /workspaces/strictly-dancing/scripts/dev-servers.sh status

# Check Playwright MCP container
docker ps | grep playwright-mcp
```

## Troubleshooting

**"Browser is already in use" Error:**
1. Wait for other session to complete
2. Or restart container: `docker restart <playwright-container-name>`

**"Session not found" Error:**
1. Reconnect MCP server in Claude Code settings
2. Or restart the Playwright MCP container

**Page not loading:**
1. Verify dev servers are running: `bash scripts/dev-servers.sh status`
2. Check the URL uses `host.docker.internal` not `localhost`
3. Verify the correct port (5175 for frontend, 8001 for backend)

## Related Skills

- `unit-testing` - Backend and frontend test suites
- `development-servers` - Starting the dev environment
