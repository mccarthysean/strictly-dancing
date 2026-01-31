#!/bin/bash
# Run Strictly Dancing unit tests
# Usage: ./scripts/run-tests.sh [backend|frontend|all|fast]

set -e

PROJECT_ROOT="/workspaces/strictly-dancing"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

run_backend_tests() {
    echo -e "${BLUE}Running backend tests...${NC}"
    cd "$BACKEND_DIR"
    uv run pytest tests/ -q "$@"
    echo -e "${GREEN}Backend tests passed!${NC}"
}

run_frontend_tests() {
    echo -e "${BLUE}Running frontend tests...${NC}"
    cd "$FRONTEND_DIR"
    bun run test "$@"
    echo -e "${GREEN}Frontend tests passed!${NC}"
}

run_fast_tests() {
    echo -e "${YELLOW}Running fast tests (skipping slow markers)...${NC}"
    cd "$BACKEND_DIR"
    uv run pytest tests/ -q -m "not slow" "$@"
    echo -e "${GREEN}Fast backend tests passed!${NC}"
    echo ""
    cd "$FRONTEND_DIR"
    bun run test "$@"
    echo -e "${GREEN}Fast frontend tests passed!${NC}"
}

show_usage() {
    echo "Strictly Dancing Test Runner"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  all       Run all tests (default)"
    echo "  backend   Run backend tests only"
    echo "  frontend  Run frontend tests only"
    echo "  fast      Run tests excluding slow markers"
    echo "  watch     Run frontend tests in watch mode"
    echo "  coverage  Run all tests with coverage"
    echo "  failed    Re-run only failed tests"
    echo ""
    echo "Options:"
    echo "  Any additional arguments are passed to the test runner"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 backend -v         # Run backend tests verbose"
    echo "  $0 backend -x         # Stop on first failure"
    echo "  $0 frontend           # Run frontend tests"
    echo "  $0 fast               # Skip slow tests"
    echo "  $0 watch              # Frontend watch mode"
    echo "  $0 coverage           # Full coverage report"
    echo "  $0 failed             # Re-run failed tests"
}

case "${1:-all}" in
    all)
        shift 2>/dev/null || true
        run_backend_tests "$@"
        echo ""
        run_frontend_tests "$@"
        echo ""
        echo -e "${GREEN}All tests passed!${NC}"
        ;;
    backend)
        shift
        run_backend_tests "$@"
        ;;
    frontend)
        shift
        run_frontend_tests "$@"
        ;;
    fast)
        shift 2>/dev/null || true
        run_fast_tests "$@"
        echo ""
        echo -e "${GREEN}All fast tests passed!${NC}"
        ;;
    watch)
        shift 2>/dev/null || true
        cd "$FRONTEND_DIR"
        bun run test:watch "$@"
        ;;
    coverage)
        shift 2>/dev/null || true
        echo -e "${BLUE}Running backend tests with coverage...${NC}"
        cd "$BACKEND_DIR"
        uv run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html "$@"
        echo ""
        echo -e "${BLUE}Running frontend tests with coverage...${NC}"
        cd "$FRONTEND_DIR"
        bun run test:coverage "$@"
        echo ""
        echo -e "${GREEN}Coverage reports generated!${NC}"
        echo "  Backend:  $BACKEND_DIR/htmlcov/index.html"
        echo "  Frontend: $FRONTEND_DIR/coverage/index.html"
        ;;
    failed)
        shift 2>/dev/null || true
        echo -e "${YELLOW}Re-running failed tests...${NC}"
        cd "$BACKEND_DIR"
        uv run pytest tests/ --lf -q "$@"
        echo -e "${GREEN}Failed tests now pass!${NC}"
        ;;
    -h|--help|help)
        show_usage
        ;;
    *)
        echo "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
