---
name: "ralph-wiggum"
description: "Ralph Wiggum iterative TDD development planning. Use when creating development plans, starting TDD workflows, resuming Ralph plans, tracking iterative progress, or managing PRD-based features. Triggers on: ralph, plan, TDD, iterative, PRD, feature plan, bugfix plan, acceptance criteria."
---

# Ralph Wiggum - Iterative TDD Development

Structured plan management for iterative Test-Driven Development with detailed PRD documents, CONTEXT.md progress logging, and Playwright verification.

## Core Concept

Ralph Wiggum is an **external AI development loop**:

1. Create a detailed PRD document (`prd.json`) with tasks and acceptance criteria
2. Create a progress log (`CONTEXT.md`) that persists between iterations
3. Run `ralph-external-loop.sh` which spawns Claude Code repeatedly
4. Each iteration: Claude reads files, completes one task, exits
5. Script checks if all tasks complete, spawns next iteration if not
6. Loop continues until completion promise detected OR max iterations

**Key Files:**

- `/project/ralph/{plan-folder}/prd.json` - Tasks with `passes: false` → `true`
- `/project/ralph/{plan-folder}/CONTEXT.md` - Append-only progress log
- `/project/ralph/{plan-folder}/ralph-loop-*.log` - Iteration logs

---

## Quick Reference

| Command         | Purpose                                   |
| --------------- | ----------------------------------------- |
| `/ralph-plan`   | Create new PRD and CONTEXT.md             |
| `/ralph-loop`   | Start external iterative development loop |

---

## Phase 1: Creating a Detailed PRD

### Step 1: Gather Requirements for the GitHub Issue

Ask the user for:

- **Title**: What is the feature/bugfix about?
- **Type**: `feature`, `bugfix`, `refactor`, `epic`, or `spike`
- **Description**: Detailed description
- **Priority for the GitHub Issue**: `very-high`, `high`, `low`, `very-low`
- **Story Points**: 1, 2, 3, 5, 8, or 13 (Fibonacci)
- **GitHub Issue**: Create one? (optional - some plans are local only)

### Step 2: Design Tasks with TDD Phases

Break down into tasks, each achievable in one iteration (~4K-8K tokens):

| Phase          | Purpose            | Typical Tasks                       |
| -------------- | ------------------ | ----------------------------------- |
| discovery      | Understand problem | Read patterns, analyze code         |
| design         | Plan approach      | Write test specs, design components |
| implementation | Write code + tests | Implement features, run tests AFTER |
| testing        | Verify quality     | Run comprehensive test suite        |
| validation     | Final checks       | Playwright E2E, cleanup             |

#### CRITICAL: Task Sizing Guidelines

**Tasks MUST be small enough for Claude to complete in a single iteration.** If tasks are too large:
- Claude may mark them as "N/A" or "deferred"
- Claude may think they are too complex and skip them
- Claude may exceed the ~200K token context window limit

**Good task sizing:**
- 1-3 files modified per task
- Clear, focused acceptance criteria (3-5 items)
- Verifiable in under 5 minutes of work

**Bad task sizing:**
- "Update all raw SQL queries in rcom.py" (too broad - split by endpoint)
- "Complete migration for entire module" (too vague - split by function)
- "Fix all issues" (not actionable - list specific issues)

**Split large tasks:**
Instead of: "Update part_lifecycle.py with all conditionals"
Use:
- T001: Update part_lifecycle.py warranty endpoints
- T002: Update part_lifecycle.py lifecycle endpoints
- T003: Update part_lifecycle.py quality endpoints

**Rule of thumb:** If a task requires reading more than 500 lines of code OR editing more than 3 functions, split it.

For each task define:

- **Task ID**: T001, T002, T003, etc.
- **Title**: Short, descriptive title
- **Phase**: One of the above phases
- **Dependencies**: Which tasks must complete first
- **Acceptance Criteria**: AC01, AC02, etc. with verification types
- **Playwright Verification**: What to verify in browser (if applicable)

### Step 3: Create Plan Folder and PRD

```bash
# Create folder
PLAN_FOLDER="$(date +%Y-%m-%d)-{type}-{slug}"
mkdir -p /project/ralph/${PLAN_FOLDER}
```

**PRD Structure (prd.json):**

```json
{
  "id": "2026-01-18-refactor-admin-views",
  "version": "1.0.0",
  "metadata": {
    "title": "Migrate Admin Views to @admin_model",
    "description": "Detailed description...",
    "type": "refactor",
    "priority": "high",
    "story_points": 13,
    "created_at": "2026-01-18T00:00:00Z",
    "github_issue": null,
    "github_issue_number": null,
    "author": "claude-code"
  },
  "completion": {
    "promise": "PLAN_COMPLETE",
    "criteria": [
      {
        "id": "CC01",
        "description": "All unit tests pass",
        "verification": "test",
        "verification_command": "cd /project && uv run pytest fast_api/tests/ -v",
        "passes": false
      },
      {
        "id": "CC02",
        "description": "TypeScript build succeeds",
        "verification": "build",
        "verification_command": "cd /project/flask_app/app/inertia/react && bun run tsc",
        "passes": false
      }
    ]
  },
  "tasks": [
    {
      "id": "T001",
      "title": "Setup: Create _legacy folder",
      "description": "Move existing files to _legacy for gradual migration",
      "passes": false,
      "phase": "discovery",
      "dependencies": [],
      "acceptance_criteria": [
        {
          "id": "AC01",
          "criterion": "_legacy folder created with all files",
          "verification": "file_exists",
          "met": false
        },
        {
          "id": "AC02",
          "criterion": "Playwright verifies app still works",
          "verification": "playwright",
          "met": false
        }
      ],
      "testing": {
        "playwright_verification": [
          "Navigate to /admin/tables/users - verify loads",
          "Check console for errors"
        ]
      }
    }
  ],
  "global_context": {
    "playwright_verification_required": true,
    "playwright_verification_note": "EVERY task verified with playwright-testing-agent"
  }
}
```

### Step 4: Create CONTEXT.md

```bash
cat > /project/ralph/${PLAN_FOLDER}/CONTEXT.md << 'EOF'
# CONTEXT.md - {Plan Title}

## Plan Overview
- **PRD**: `prd.json`
- **Created**: {date}
- **Type**: {type}
- **Story Points**: {points}

## Goal
{Description of what we're achieving}

## Key Principles
- **TDD (Test After)**: Write code + tests together, run tests AFTER
- **Playwright Verification**: EVERY task verified before marking complete
- {Add any plan-specific principles}

---

## Progress Log

<!-- Append entries below as tasks are completed -->
EOF
```

### Step 5: (Optional) Create GitHub Issue

Only if tracking is needed:

```bash
gh issue create \
  --title "[Ralph] {Plan Title}" \
  --label "enhancement" \
  --body "## Plan
**PRD**: \`/project/ralph/{plan-folder}/prd.json\`

## Tasks
- [ ] T001: {title}
- [ ] T002: {title}
..."

# Add to IJACK Roadmap
gh project item-add 12 --owner ijack-technologies --url <ISSUE_URL>
```

---

## Phase 2: Starting the Ralph External Loop

### Overview

The external loop is a bash script that:
1. Runs Claude Code as a subprocess
2. Claude reads prd.json, completes ONE task, exits
3. Script checks if all tasks are complete
4. If not complete, spawns another Claude iteration
5. Continues until completion OR max iterations

### Running the External Loop

**From within Claude Code session:**

Tell the user to run this command in a **separate terminal**:

```bash
# Interactive mode (prompts for permissions)
./scripts/ralph-external-loop.sh 2026-01-26-feature-work-order-migration

# Autonomous mode (no prompts - for containers/CI)
./scripts/ralph-external-loop.sh 2026-01-26-feature-work-order-migration --dangerous

# With options
./scripts/ralph-external-loop.sh my-plan -m opus -i 100 -d

# Run in background with logging
nohup ./scripts/ralph-external-loop.sh my-plan -d > ralph.log 2>&1 &
```

### Command Options

| Option | Description |
|--------|-------------|
| `-m, --model <model>` | Model: haiku, sonnet, opus (default: opus) |
| `-i, --max-iterations <n>` | Max iterations (default: 50) |
| `-p, --promise <text>` | Completion promise (default: PLAN_COMPLETE) |
| `-d, --dangerous` | Skip permission prompts (autonomous mode) |

### What Happens During the Loop

Each iteration:
1. Script displays progress (X/Y tasks complete)
2. Spawns Claude Code with the task prompt
3. Claude reads prd.json and CONTEXT.md
4. Claude works on ONE incomplete task
5. Claude updates prd.json (`passes: true`) and CONTEXT.md
6. Claude commits changes and exits
7. Script checks for completion promise in output
8. If all tasks done, runs final verification and exits
9. Otherwise, starts next iteration

### Monitoring Progress

```bash
# Watch the log file
tail -f /project/ralph/{plan-folder}/ralph-loop-*.log

# Check task status
jq '.tasks | map({id, title, passes})' /project/ralph/{plan-folder}/prd.json

# Check iteration count
head -10 /project/ralph/{plan-folder}/ralph-loop-*.log
```

---

## Phase 3: Working in Each Iteration

### TDD Approach (Test After)

**Don't waste time running tests you know will fail:**

1. **Write tests AND implementation together** - Tests define requirements
2. **Run tests AFTER writing both** - Verify everything works in one pass
3. **Only run tests when you expect them to pass**

#### Test Requirements for Every Task

Every implementation task MUST include:

1. **Unit tests written** - Test the specific functionality added
2. **Tests run quickly** - Under 30 seconds for the relevant test file
3. **All tests pass** - No skipped or failing tests
4. **Test coverage** - Key code paths and edge cases tested

**Test checklist before marking task complete:**
```bash
# Run tests for the changed files
uv run pytest <path/to/tests> -v --tb=short

# Verify test file exists
ls fast_api/tests/path/test_*.py

# Check test count increased
uv run pytest <path/to/tests> --collect-only | tail -5
```

**DO NOT mark a task as `passes: true` if:**
- No tests were written for new code
- Tests fail or are skipped
- Tests take more than 60 seconds to run

### Playwright Verification (MANDATORY)

**EVERY UI-facing task must be verified with the playwright-testing-agent subagent to PROVE completion:**

```python
# Use Task tool with subagent_type="playwright-testing-agent"
{
  "subagent_type": "playwright-testing-agent",
  "prompt": "Navigate to /admin/tables/users. Verify table loads. Check console for errors.",
  "description": "Verify users table works"
}
```

**Never call `mcp__playwright__*` tools directly** - always use the subagent.

#### What Playwright Verification Must Include

1. **Navigate to the feature** - Actually load the page/component
2. **Verify functionality** - Test the specific acceptance criteria
3. **Check for errors** - Console messages, network errors, visual issues
4. **Take screenshot** - Visual proof of working feature

**The Playwright agent MUST report success before a task is marked `passes: true`.**

If Playwright verification fails:
- Fix the issue immediately
- Re-run Playwright verification
- Only mark complete when verification passes

### Updating Progress

After each task:

1. **Update prd.json** - Set `acceptance_criteria[].met = true`, then `task.passes = true`
2. **Append to CONTEXT.md**:

```markdown
### Entry [E-001] 2026-01-18T15:30:00Z

**Task**: T001 - Create \_legacy folder
**Status**: ✅ DONE
**Progress**: 1/25 tasks | Blockers: 0

**Accomplished**:

- Created \_legacy folder
- Moved 32 files
- Updated imports in router.py

**Evidence**:

- Tests: ✅ All passing
- Playwright: ✅ Admin tables load correctly

**Next**: → T002: Integrate simplified module
```

3. **Commit changes**:

```bash
git add path/to/file1.py path/to/file2.py
git commit -m "feat(admin): T001 - Create _legacy folder

Completes T001 for admin-views-migration

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Critical Rules

### 🚫 PERMISSION-FREE EXECUTION (in dangerous mode)

When running with `--dangerous`, ONLY use pre-approved commands. Any command requiring permission will STOP the agent.

| Task          | Approved Command       | Avoid              |
| ------------- | ---------------------- | ------------------ |
| Tests         | `uv run pytest ...`    | `python -m pytest` |
| Python lint   | `ruff check --fix .`   | -                  |
| Python format | `ruff format .`        | -                  |
| TS build      | `bun run tsc`          | -                  |
| Git add       | `git add path/to/file` | `git add -A`       |
| JSON editing  | `edit tool`            | `python -c`        |
| File editing  | `edit tool`            | `cat`              |

**🚫 NEVER use `python -c` or `python3 -c`** - these require permission.

### 🚨 NEVER Skip Requirements

**Every acceptance criterion MUST be implemented. NO EXCEPTIONS.**

If a requirement is difficult:

1. Break it into sub-tasks
2. Research first (Context7, docs)
3. Build required infrastructure
4. Document blocker in CONTEXT.md

**Never mark a task complete when criteria aren't met.**

### Fix Issues When Found

Don't work around problems - fix them:

- Server won't start? Fix root cause
- Import errors? Fix immediately
- Lint failures? Fix before continuing
- Type errors? Resolve them

---

## Completion Promise

When ALL completion criteria have `passes: true`:

```
<promise>PLAN_COMPLETE</promise>
```

**STRICT RULES:**

- Use `<promise>` XML tags EXACTLY as shown
- The statement MUST be completely TRUE
- Do NOT output false statements to exit
- Do NOT lie even if you think you should exit

The loop is designed to continue until the promise is genuinely true.

---

## Reference Files

- `/project/ralph/README.md` - Full documentation
- `/project/ralph/_templates/` - PRD templates
- `/project/scripts/ralph-external-loop.sh` - External loop script

---

## Phase 4: Supervising the External Loop (Two-Level AI)

### The Monitoring Pattern

For complex plans, use **two levels of AI**:

1. **External Claude** - Runs in the loop, executes individual tasks
2. **Supervising Claude** - Monitors progress, ensures quality, intervenes if needed

### Starting Supervised Execution

**Recommended: Use Claude Code Background Task Feature**

From within a Claude Code session, use the Bash tool with `run_in_background: true`:

```json
{
  "command": "/project/scripts/ralph-external-loop.sh <plan-folder> --dangerous -i 100",
  "run_in_background": true,
  "timeout": 600000
}
```

This gives you:
- Real-time output visibility in Claude Code
- Background task ID for monitoring
- Output file at `/tmp/claude/-project/tasks/<task-id>.output`

### Monitoring with Background Tasks

1. **Check output with TaskOutput tool:**
```json
{
  "task_id": "<background-task-id>",
  "block": false,
  "timeout": 5000
}
```

2. **Or read the output file directly:**
```bash
tail -50 /tmp/claude/-project/tasks/<task-id>.output
```

3. **Check task completion in prd.json:**
```bash
grep '"passes":' /project/ralph/<plan-folder>/prd.json
```

4. **Read CONTEXT.md for progress:**
Use the Read tool to see iteration entries.

### Alternative: Background with nohup

For long-running loops where you want to disconnect:

```bash
nohup ./scripts/ralph-external-loop.sh <plan-folder> -d -i 100 > /project/ralph/<plan-folder>/ralph-run.log 2>&1 &
echo "PID: $!"
```

Monitor with:
```bash
tail -50 /project/ralph/<plan-folder>/ralph-run.log
```

### Quality Verification After Each Task

- Read CONTEXT.md for progress entries
- Check that acceptance criteria are actually met
- Verify tests pass
- Review code changes if needed

### Supervisor Responsibilities

| Check | How |
|-------|-----|
| Task completed correctly | Read prd.json, verify `passes: true` |
| Code quality | Run `ruff check` on changed files |
| Tests pass | Run test commands from prd.json |
| No skipped criteria | Compare CONTEXT.md entries to acceptance criteria |
| Proper commits | Check `git log --oneline -5` |
| TDD followed | Verify unit tests exist and pass |
| Playwright verified | Confirm browser testing was done |

### TDD Enforcement (Supervisor Role)

**For each completed task, the supervisor MUST verify:**

1. **Unit tests exist** - Check for new test files or test additions
2. **Tests run quickly** - Fast feedback loop is critical
3. **Tests pass** - Run `uv run pytest <path> -v` on relevant tests
4. **Coverage adequate** - Key code paths are tested

**Example TDD verification:**
```bash
# Check if tests were added
git diff --name-only HEAD~1 | grep -E "test_.*\.py$"

# Run tests for the changed area
uv run pytest fast_api/tests/services/ -v --tb=short

# Check coverage if needed
uv run pytest --cov=fast_api/app/services --cov-report=term-missing
```

### Playwright Verification Enforcement

**The supervisor MUST ensure Playwright testing is done for UI-facing tasks:**

1. **Spawn playwright-testing-agent** for each task with UI impact
2. **Verify specific acceptance criteria** - Not just "page loads"
3. **Check console for errors** - JS errors indicate problems
4. **Screenshot evidence** - Capture proof of working features

**Example Playwright verification:**
```python
# Use Task tool with subagent
{
  "subagent_type": "playwright-testing-agent",
  "prompt": """
    Navigate to https://app.rcom/admin/work-orders
    1. Verify the work order table loads with data
    2. Check console for JavaScript errors
    3. Take screenshot as evidence
    4. Click on a work order row and verify detail page loads
  """,
  "description": "Verify work order migration - admin table"
}
```

### Quality Gates Before Moving to Next Task

Before allowing the loop to proceed, verify:

1. **Syntax check passes** - `python -c "from module import ..."` works
2. **Linting passes** - `ruff check <file> && ruff format --check <file>`
3. **Unit tests pass** - Relevant test suite runs green
4. **Playwright verified** - For UI tasks, browser tests confirm functionality
5. **CONTEXT.md updated** - Progress entry documents what was done
6. **prd.json updated** - Task marked `passes: true`

### Intervention Scenarios

**If external Claude gets stuck:**
- Check log for errors
- Read CONTEXT.md for blockers
- Kill the loop: `pkill -f ralph-external-loop`
- Fix the issue manually
- Restart the loop

**If task marked complete but criteria not met:**
- Edit prd.json to set `passes: false`
- Add note to CONTEXT.md explaining what was missed
- Loop will retry the task

**If tests fail after task completion:**
- Stop the loop
- Fix the failing tests
- Update prd.json and CONTEXT.md
- Restart the loop

### Example Monitoring Session

```bash
# Start loop
nohup ./scripts/ralph-external-loop.sh my-plan -d > ralph-run.log 2>&1 &

# Check every 2-5 minutes
while true; do
    echo "=== $(date) ==="
    tail -20 ralph-run.log
    jq '.tasks | map(select(.passes == true)) | length' prd.json
    sleep 120
done
```

---

## Troubleshooting

### Loop doesn't progress

- Check log file: `tail -f /project/ralph/{plan}/ralph-loop-*.log`
- Verify prd.json has incomplete tasks: `jq '.tasks[] | select(.passes != true)' prd.json`
- Check CONTEXT.md for blockers

### Claude keeps working on same task

- Ensure prd.json is being updated with `passes: true`
- Check file permissions on prd.json
- Look for errors in CONTEXT.md

### Max iterations reached

- Check how many tasks remain
- Consider increasing with `-i 100`
- Look for stuck tasks in CONTEXT.md

### Permission errors in dangerous mode

- Avoid `python -c` commands
- Use Edit tool instead of `sed` or `cat`
- Use approved commands from the table above
