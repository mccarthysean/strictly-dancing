#!/bin/bash
# ralph-external-loop.sh - External Ralph loop with CONTEXT.md continuity
#
# This script runs Claude Code in a loop. Each iteration reads prd.json and
# CONTEXT.md for state, works on one task, then the script checks for completion.
#
# Usage:
#   ./scripts/ralph-external-loop.sh <plan-folder> [options]
#
# Options:
#   -m, --model <model>       Model to use: haiku, sonnet, opus (default: opus)
#   -i, --max-iterations <n>  Maximum iterations (default: 50)
#   -p, --promise <text>      Completion promise text (default: PLAN_COMPLETE)
#   -d, --dangerous           Enable --dangerously-skip-permissions (autonomous mode)
#                             Uses IS_SANDBOX=1 to allow running as root in containers
#   -h, --help                Show this help
#
# Examples:
#   # Interactive mode (will prompt for permissions)
#   ./scripts/ralph-external-loop.sh 2026-01-28-feature-phase1-foundation
#
#   # Autonomous mode (works as root with IS_SANDBOX=1)
#   ./scripts/ralph-external-loop.sh my-plan --dangerous
#
#   # With model selection
#   ./scripts/ralph-external-loop.sh my-plan -m haiku -i 30
#   ./scripts/ralph-external-loop.sh my-plan --model opus --max-iterations 100
#
# Run in background with logging:
#   nohup ./scripts/ralph-external-loop.sh my-plan -d > ralph.log 2>&1 &

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
MAX_ITERATIONS=50
COMPLETION_PROMISE="PLAN_COMPLETE"
MODEL="opus"
PLAN_FOLDER=""
DANGEROUS_MODE=false

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Show help
show_help() {
    head -30 "$0" | tail -28 | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -i|--max-iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        -p|--promise)
            COMPLETION_PROMISE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        -d|--dangerous)
            DANGEROUS_MODE=true
            shift
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage"
            exit 1
            ;;
        *)
            if [[ -z "$PLAN_FOLDER" ]]; then
                PLAN_FOLDER="$1"
            else
                echo -e "${RED}Unexpected argument: $1${NC}"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required argument
if [[ -z "$PLAN_FOLDER" ]]; then
    echo -e "${RED}ERROR: Plan folder is required${NC}"
    echo "Usage: $0 <plan-folder> [options]"
    echo "Use --help for more options"
    exit 1
fi

# Validate dangerous mode requirements
if [[ "$DANGEROUS_MODE" == "true" ]]; then
    # Use IS_SANDBOX=1 to allow --dangerously-skip-permissions as root in containers
    # This is the official Anthropic solution for sandboxed environments
    export IS_SANDBOX=1
    echo -e "${YELLOW}Running in DANGEROUS mode (--dangerously-skip-permissions with IS_SANDBOX=1)${NC}"
else
    echo -e "${CYAN}Running in INTERACTIVE mode (will prompt for permissions)${NC}"
fi

# Unset ANTHROPIC_API_KEY to force Claude Code to use Max subscription
# instead of API credits (user may have this set for other applications)
unset ANTHROPIC_API_KEY

# Determine plan path - support both full path and folder name
if [[ "$PLAN_FOLDER" == /* ]]; then
    PLAN_PATH="$PLAN_FOLDER"
else
    PLAN_PATH="$PROJECT_ROOT/ralph/$PLAN_FOLDER"
fi

# Validate plan exists
if [[ ! -f "$PLAN_PATH/prd.json" ]]; then
    echo -e "${RED}ERROR: prd.json not found at $PLAN_PATH${NC}"
    echo "Available plans:"
    ls -1 "$PROJECT_ROOT/ralph/" 2>/dev/null | head -10 || echo "  No plans found"
    exit 1
fi

# Create CONTEXT.md if it doesn't exist
if [[ ! -f "$PLAN_PATH/CONTEXT.md" ]]; then
    cat > "$PLAN_PATH/CONTEXT.md" << EOF
# Progress Log for $(basename "$PLAN_FOLDER")

Created: $(date -Iseconds)

---

EOF
    echo -e "${YELLOW}Created CONTEXT.md${NC}"
fi

# Create output log file
LOG_FILE="$PLAN_PATH/ralph-loop-$(date +%Y%m%d-%H%M%S).log"

# Build the base prompt
read -r -d '' BASE_PROMPT << 'PROMPT_EOF' || true
Execute the TDD development plan at PLAN_PATH_PLACEHOLDER/

## Your Mission
You are executing a Ralph Wiggum PRD plan. Read the files, find the next incomplete task, and complete it following TDD methodology.

## Instructions
1. Read prd.json for tasks and acceptance criteria
2. Read CONTEXT.md for previous progress
3. Find the NEXT incomplete task (one where passes: false)
4. Follow TDD workflow:
   - Write failing tests first
   - Implement code to make tests pass
   - Refactor if needed
5. When task passes all criteria, update prd.json: set passes: true
6. Append a progress entry to CONTEXT.md
7. Commit your changes with a descriptive message
8. If ALL tasks are complete, output <promise>COMPLETION_PROMISE_PLACEHOLDER</promise>

## Critical Rules
- Only work on ONE task per iteration
- Never skip acceptance criteria - implement everything
- Check existing tests before writing new ones
- Read settings.json to use only allowed commands
- If blocked, document the blocker in CONTEXT.md

## Completion Signal
When ALL tasks in prd.json have passes: true:
- Run tests to verify everything passes
- Run linting to ensure code quality
- Then output: <promise>COMPLETION_PROMISE_PLACEHOLDER</promise>
PROMPT_EOF

# Replace placeholders
BASE_PROMPT="${BASE_PROMPT//PLAN_PATH_PLACEHOLDER/$PLAN_PATH}"
BASE_PROMPT="${BASE_PROMPT//COMPLETION_PROMISE_PLACEHOLDER/$COMPLETION_PROMISE}"

# Header
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           Ralph External Loop - Strictly Dancing             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Plan:${NC}       $PLAN_PATH"
echo -e "${BLUE}Model:${NC}      $MODEL"
echo -e "${BLUE}Max Iter:${NC}   $MAX_ITERATIONS"
echo -e "${BLUE}Promise:${NC}    $COMPLETION_PROMISE"
echo -e "${BLUE}Log:${NC}        $LOG_FILE"
echo ""

# Log header
{
    echo "=== Ralph External Loop Started ==="
    echo "Plan: $PLAN_PATH"
    echo "Model: $MODEL"
    echo "Max Iterations: $MAX_ITERATIONS"
    echo "Completion Promise: $COMPLETION_PROMISE"
    echo "Started: $(date -Iseconds)"
    echo ""
} >> "$LOG_FILE"

# Main loop
for i in $(seq 1 "$MAX_ITERATIONS"); do
    echo -e "${GREEN}╭──────────────────────────────────────────────────────────────╮${NC}"
    echo -e "${GREEN}│ Iteration $i/$MAX_ITERATIONS                                        ${NC}"
    echo -e "${GREEN}│ Started: $(date -Iseconds)                            ${NC}"
    echo -e "${GREEN}╰──────────────────────────────────────────────────────────────╯${NC}"

    # Show current task status
    if [[ -f "$PLAN_PATH/prd.json" ]]; then
        TOTAL_TASKS=$(jq '.tasks | length' "$PLAN_PATH/prd.json" 2>/dev/null || echo "?")
        COMPLETED_TASKS=$(jq '[.tasks[] | select(.passes == true)] | length' "$PLAN_PATH/prd.json" 2>/dev/null || echo "?")
        NEXT_TASK=$(jq -r '.tasks[] | select(.passes != true) | .id' "$PLAN_PATH/prd.json" 2>/dev/null | head -1)
        NEXT_TASK_NAME=$(jq -r --arg id "$NEXT_TASK" '.tasks[] | select(.id == $id) | .title' "$PLAN_PATH/prd.json" 2>/dev/null || echo "Unknown")

        echo -e "${BLUE}  Progress: ${COMPLETED_TASKS}/${TOTAL_TASKS} tasks complete${NC}"
        if [[ -n "$NEXT_TASK" ]]; then
            echo -e "${YELLOW}  Next task: ${NEXT_TASK} - ${NEXT_TASK_NAME}${NC}"
        fi
        echo ""
    fi

    # Build iteration-specific prompt
    ITERATION_PROMPT="$BASE_PROMPT

---
ITERATION: $i of $MAX_ITERATIONS
TIMESTAMP: $(date -Iseconds)

Begin by reading prd.json and CONTEXT.md to understand current state.
Then identify and complete the next incomplete task."

    # Run Claude
    echo -e "${YELLOW}Running Claude...${NC}"

    # Build Claude command based on mode
    CLAUDE_ARGS=(-p "$ITERATION_PROMPT" --model "$MODEL" --verbose --output-format stream-json)
    if [[ "$DANGEROUS_MODE" == "true" ]]; then
        CLAUDE_ARGS+=(--dangerously-skip-permissions)
    fi

    # Find claude binary - check common locations
    CLAUDE_BIN=""
    for path in "/root/.local/bin/claude" "$HOME/.local/bin/claude" "$(which claude 2>/dev/null)"; do
        if [[ -x "$path" ]]; then
            CLAUDE_BIN="$path"
            break
        fi
    done

    if [[ -z "$CLAUDE_BIN" ]]; then
        echo -e "${RED}ERROR: claude command not found${NC}"
        echo "Install Claude Code: curl -fsSL https://claude.ai/install.sh | bash"
        exit 1
    fi

    # Create temp file for capturing output while streaming
    TEMP_OUTPUT=$(mktemp)
    trap "rm -f $TEMP_OUTPUT" EXIT

    # Start heartbeat in background to show activity
    (
        HEARTBEAT_COUNT=0
        while true; do
            sleep 10
            HEARTBEAT_COUNT=$((HEARTBEAT_COUNT + 1))
            ELAPSED=$((HEARTBEAT_COUNT * 10))
            # Print heartbeat on same line, overwriting previous
            printf "\r${CYAN}  ⏱  Still working... %dm %02ds elapsed${NC}    " $((ELAPSED / 60)) $((ELAPSED % 60))
        done
    ) &
    HEARTBEAT_PID=$!
    # Kill heartbeat when script exits or continues
    trap "kill $HEARTBEAT_PID 2>/dev/null; rm -f $TEMP_OUTPUT" EXIT

    # Stream output to terminal in real-time while capturing to temp file
    echo "─────────────────────────────────────────────────────────────"
    set +e
    stdbuf -oL "$CLAUDE_BIN" "${CLAUDE_ARGS[@]}" 2>&1 | stdbuf -oL tee "$TEMP_OUTPUT" | while IFS= read -r line; do
        # Try to parse as JSON and extract interesting events
        if echo "$line" | jq -e '.type' >/dev/null 2>&1; then
            EVENT_TYPE=$(echo "$line" | jq -r '.type // empty')
            case "$EVENT_TYPE" in
                "assistant")
                    # Show assistant thinking/response
                    MSG=$(echo "$line" | jq -r '.message.content[]? | select(.type=="text") | .text // empty' 2>/dev/null | head -c 200)
                    if [[ -n "$MSG" ]]; then
                        echo -e "${CYAN}💭 $MSG${NC}"
                    fi
                    ;;
                "content_block_start")
                    # Show when a tool is being called
                    TOOL=$(echo "$line" | jq -r '.content_block.name // empty' 2>/dev/null)
                    if [[ -n "$TOOL" ]]; then
                        echo -e "${YELLOW}🔧 Tool: $TOOL${NC}"
                    fi
                    ;;
                "content_block_delta")
                    # Show tool input being streamed (truncated)
                    DELTA=$(echo "$line" | jq -r '.delta.partial_json // empty' 2>/dev/null | head -c 100)
                    if [[ -n "$DELTA" ]]; then
                        printf "${BLUE}   %s${NC}" "$DELTA"
                    fi
                    # Show text being streamed
                    TEXT=$(echo "$line" | jq -r '.delta.text // empty' 2>/dev/null)
                    if [[ -n "$TEXT" ]]; then
                        printf "%s" "$TEXT"
                    fi
                    ;;
                "content_block_stop")
                    echo ""  # Newline after tool input
                    ;;
                "result")
                    # Show final result
                    RESULT=$(echo "$line" | jq -r '.result // empty' 2>/dev/null | head -c 500)
                    if [[ -n "$RESULT" ]]; then
                        echo -e "${GREEN}✓ Result: $RESULT${NC}"
                    fi
                    ;;
            esac
        else
            # Not JSON, just print raw (could be error output)
            echo "$line"
        fi
    done
    EXIT_CODE=${PIPESTATUS[0]}
    set -e

    # Stop heartbeat
    kill $HEARTBEAT_PID 2>/dev/null || true
    printf "\r%80s\r" " "  # Clear heartbeat line
    echo "─────────────────────────────────────────────────────────────"

    # Read captured output for promise checking
    OUTPUT=$(cat "$TEMP_OUTPUT")

    # Log full output
    {
        echo "=== Iteration $i ==="
        echo "Exit Code: $EXIT_CODE"
        echo "$OUTPUT"
        echo ""
    } >> "$LOG_FILE"

    # Check for completion promise
    if echo "$OUTPUT" | grep -q "<promise>$COMPLETION_PROMISE</promise>"; then
        echo ""
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                    PLAN COMPLETE!                             ║${NC}"
        echo -e "${GREEN}║ Finished at iteration $i                                      ${NC}"
        echo -e "${GREEN}║ Time: $(date -Iseconds)                              ${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"

        # Log completion
        {
            echo "=== PLAN COMPLETE ==="
            echo "Completed at iteration $i"
            echo "Finished: $(date -Iseconds)"
        } >> "$LOG_FILE"

        # Run final verification
        echo ""
        echo -e "${YELLOW}Running final verification...${NC}"

        cd "$PROJECT_ROOT"
        echo "Running backend tests..."
        cd backend && uv run pytest 2>&1 | tail -20 || echo -e "${RED}Some tests failed${NC}"

        echo "Running linting..."
        ruff check . 2>&1 | tail -10 || echo -e "${RED}Ruff found issues${NC}"

        exit 0
    fi

    # Check prd.json for all tasks complete (backup check)
    if jq -e '[.tasks[].passes] | all' "$PLAN_PATH/prd.json" >/dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}All tasks in prd.json marked complete!${NC}"
        echo "Claude may not have output the promise. Check CONTEXT.md for details."
        exit 0
    fi

    # Check for errors
    if [[ $EXIT_CODE -ne 0 ]]; then
        echo -e "${RED}Claude exited with error code $EXIT_CODE${NC}"
        echo "Check $LOG_FILE for details"
        # Continue anyway - might be recoverable
    fi

    # Show what changed in this iteration
    echo -e "${CYAN}Iteration $i complete.${NC}"

    # Quick status check
    if [[ -f "$PLAN_PATH/prd.json" ]]; then
        NEW_COMPLETED=$(jq '[.tasks[] | select(.passes == true)] | length' "$PLAN_PATH/prd.json" 2>/dev/null || echo "?")
        echo -e "${BLUE}  Tasks completed: ${NEW_COMPLETED}/${TOTAL_TASKS}${NC}"
    fi

    # Show recent git activity
    RECENT_COMMITS=$(git log --oneline -1 --since="5 minutes ago" 2>/dev/null || true)
    if [[ -n "$RECENT_COMMITS" ]]; then
        echo -e "${GREEN}  Recent commit: ${RECENT_COMMITS}${NC}"
    fi

    # Show last progress entry from CONTEXT.md
    if [[ -f "$PLAN_PATH/CONTEXT.md" ]]; then
        LAST_ENTRY=$(grep -E "^## (Iteration|Task|Progress)" "$PLAN_PATH/CONTEXT.md" 2>/dev/null | tail -1 || true)
        if [[ -n "$LAST_ENTRY" ]]; then
            echo -e "${YELLOW}  Last logged: ${LAST_ENTRY}${NC}"
        fi
    fi

    echo ""
    echo -e "${CYAN}Continuing to next iteration...${NC}"
    echo ""

    # Small delay between iterations to avoid rate limiting
    sleep 3
done

echo ""
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║            Max iterations ($MAX_ITERATIONS) reached                    ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Plan may not be complete. Check:"
echo "  - $PLAN_PATH/prd.json for task status"
echo "  - $PLAN_PATH/CONTEXT.md for progress"
echo "  - $LOG_FILE for full output"

# Log max iterations
{
    echo "=== MAX ITERATIONS REACHED ==="
    echo "Stopped at iteration $MAX_ITERATIONS"
    echo "Finished: $(date -Iseconds)"
} >> "$LOG_FILE"

exit 1
