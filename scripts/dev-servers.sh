#!/bin/bash

# dev-servers.sh - Development Server Manager for Strictly Dancing
# Manages FastAPI and Vite servers with auto-reload (uses AWS RDS Dev for database)
# Usage: ./scripts/dev-servers.sh {start|stop|restart|logs|status}

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Directories
LOG_DIR="$PROJECT_ROOT/.logs"
PID_DIR="$PROJECT_ROOT/.pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

# PID and log files
PID_FASTAPI="$PID_DIR/fastapi.pid"
PID_VITE="$PID_DIR/vite.pid"
LOG_FASTAPI="$LOG_DIR/fastapi.log"
LOG_VITE="$LOG_DIR/vite.log"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Wait for service to be healthy
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=0

    log_info "Waiting for $service to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_success "$service is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    log_error "$service failed to start within ${max_attempts}s"
    return 1
}

# Kill processes using required ports to prevent "address already in use" errors
kill_port_processes() {
    local service_name=$1
    local port=$2

    # Check if anything is using the port
    if lsof -ti:"$port" > /dev/null 2>&1; then
        log_warning "$service_name port $port is in use, killing processes..."
        lsof -ti:"$port" | xargs -r kill -9 2>/dev/null || true
        sleep 1

        # Verify port is now free
        if lsof -ti:"$port" > /dev/null 2>&1; then
            log_error "Failed to free port $port for $service_name"
            return 1
        else
            log_success "Port $port freed for $service_name"
        fi
    fi
    return 0
}

# Start FastAPI with uvicorn and auto-reload
start_fastapi() {
    if is_running "$PID_FASTAPI"; then
        log_warning "FastAPI is already running"
        return 0
    fi

    # Kill any processes using FastAPI port
    kill_port_processes "FastAPI" 8001 || return 1

    log_info "Starting FastAPI with uvicorn (auto-reload enabled)..."

    cd "$PROJECT_ROOT/backend"

    # Start uvicorn with reload (using uv to ensure venv)
    nohup uv run uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8001 \
        --reload \
        --reload-dir app \
        > "$LOG_FASTAPI" 2>&1 &

    echo $! > "$PID_FASTAPI"

    # Wait for FastAPI to be ready
    if wait_for_service "FastAPI" "http://localhost:8001/docs" 20; then
        log_success "FastAPI started (PID: $(cat "$PID_FASTAPI")) - http://localhost:8001"
        return 0
    else
        rm -f "$PID_FASTAPI"
        return 1
    fi
}

# Start Vite frontend server
start_vite() {
    if is_running "$PID_VITE"; then
        log_warning "Vite is already running"
        return 0
    fi

    # Kill any processes using Vite port
    kill_port_processes "Vite" 5175 || return 1

    log_info "Starting Vite dev server..."

    cd "$PROJECT_ROOT/frontend"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_error "Node modules not found. Run: bun install"
        return 1
    fi

    # Start Vite
    nohup bun run dev > "$LOG_VITE" 2>&1 &

    echo $! > "$PID_VITE"

    # Wait for Vite to be ready
    sleep 3

    if wait_for_service "Vite" "http://localhost:5175" 20; then
        log_success "Vite started (PID: $(cat "$PID_VITE")) - http://localhost:5175"
        return 0
    else
        rm -f "$PID_VITE"
        return 1
    fi
}

# Stop a service
stop_service() {
    local service=$1
    local pid_file=$2

    if ! is_running "$pid_file"; then
        log_warning "$service is not running"
        return 0
    fi

    local pid=$(cat "$pid_file")
    log_info "Stopping $service (PID: $pid)..."

    # Send SIGTERM for graceful shutdown
    kill -TERM "$pid" 2>/dev/null || true

    # Wait up to 10 seconds for graceful shutdown
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done

    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warning "$service didn't stop gracefully, forcing..."
        kill -9 "$pid" 2>/dev/null || true
    fi

    rm -f "$pid_file"
    log_success "$service stopped"
}

# Start all services
start_all() {
    log_info "Starting all development servers..."
    echo ""

    start_fastapi || { log_error "Failed to start FastAPI"; return 1; }
    echo ""

    start_vite || { log_error "Failed to start Vite"; return 1; }
    echo ""

    log_success "All services started successfully!"
    echo ""
    show_status
}

# Stop all services
stop_all() {
    log_info "Stopping all development servers..."
    echo ""

    # Stop in reverse order
    stop_service "Vite" "$PID_VITE"
    stop_service "FastAPI" "$PID_FASTAPI"

    echo ""
    log_success "All services stopped"
}

# Show service status
show_status() {
    echo -e "${CYAN}=== Strictly Dancing Development Server Status ===${NC}"
    echo ""

    # Database info (AWS RDS Dev)
    echo -e "${GREEN}●${NC} Database    : AWS RDS Dev (ijack-dev.*.rds.amazonaws.com/strictly_dancing)"

    # FastAPI status
    if is_running "$PID_FASTAPI"; then
        echo -e "${GREEN}●${NC} FastAPI     : Running (PID: $(cat "$PID_FASTAPI")) - http://localhost:8001"
    else
        echo -e "${RED}○${NC} FastAPI     : Stopped"
    fi

    # Vite status
    if is_running "$PID_VITE"; then
        echo -e "${GREEN}●${NC} Vite        : Running (PID: $(cat "$PID_VITE")) - http://localhost:5175"
    else
        echo -e "${RED}○${NC} Vite        : Stopped"
    fi

    echo ""
    echo -e "${CYAN}Logs directory: ${NC}$LOG_DIR"
    echo -e "${CYAN}PIDs directory: ${NC}$PID_DIR"
    echo ""
    echo -e "${CYAN}Direct URLs:${NC}"
    echo "  Frontend:     http://localhost:5175"
    echo "  API Docs:     http://localhost:8001/docs"
    echo "  API Root:     http://localhost:8001/"
}

# Show logs
show_logs() {
    local service=$1

    if [ -z "$service" ]; then
        # Show all logs with color coding
        log_info "Showing aggregated logs (Ctrl+C to exit)..."
        echo ""

        # Use tail with color prefixes
        tail -f \
            "$LOG_FASTAPI" \
            "$LOG_VITE" \
            2>/dev/null | while IFS= read -r line; do
                if [[ $line == *"$LOG_FASTAPI"* ]]; then
                    echo -e "${BLUE}[FastAPI]${NC} ${line#*:}"
                elif [[ $line == *"$LOG_VITE"* ]]; then
                    echo -e "${MAGENTA}[Vite]${NC} ${line#*:}"
                else
                    echo "$line"
                fi
            done
    else
        # Show specific service log
        case $service in
            fastapi|backend)
                log_info "Showing FastAPI logs (Ctrl+C to exit)..."
                tail -f "$LOG_FASTAPI"
                ;;
            vite|frontend)
                log_info "Showing Vite logs (Ctrl+C to exit)..."
                tail -f "$LOG_VITE"
                ;;
            *)
                log_error "Unknown service: $service"
                log_info "Available services: fastapi, vite"
                return 1
                ;;
        esac
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running Alembic migrations against AWS RDS Dev..."
    cd "$PROJECT_ROOT/backend"
    uv run alembic upgrade head
    log_success "Migrations complete"
}

# Generate API types for frontend
generate_types() {
    if ! is_running "$PID_FASTAPI"; then
        log_error "FastAPI must be running to generate types"
        return 1
    fi

    log_info "Generating TypeScript types from OpenAPI..."
    cd "$PROJECT_ROOT/frontend"
    bun run generate-types
    log_success "Types generated"
}

# Main command handler
case "${1:-}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        echo ""
        sleep 2
        start_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    start-fastapi|fastapi|backend)
        start_fastapi
        ;;
    start-vite|vite|frontend)
        start_vite
        ;;
    migrate)
        run_migrations
        ;;
    generate-types|types)
        generate_types
        ;;
    *)
        echo "Strictly Dancing Development Server Manager"
        echo ""
        echo "Usage: $0 {command} [options]"
        echo ""
        echo "Commands:"
        echo "  start           Start all development servers (FastAPI, Vite)"
        echo "  stop            Stop all development servers"
        echo "  restart         Restart all development servers"
        echo "  status          Show status of all services"
        echo "  logs [svc]      Show logs (optional: fastapi|vite)"
        echo ""
        echo "Individual Services:"
        echo "  start-fastapi   Start only FastAPI backend"
        echo "  start-vite      Start only Vite frontend"
        echo ""
        echo "Utilities:"
        echo "  migrate         Run Alembic database migrations (AWS RDS Dev)"
        echo "  generate-types  Generate TypeScript types from OpenAPI"
        echo ""
        echo "Features:"
        echo "  - Database: AWS RDS Dev (ijack-dev/strictly_dancing)"
        echo "  - FastAPI: uvicorn with --reload"
        echo "  - Vite: Built-in HMR"
        echo "  - Aggregated log viewing with color-coded output"
        echo "  - PID tracking for process management"
        echo ""
        echo "Direct URLs:"
        echo "  Frontend:  http://localhost:5175"
        echo "  API:       http://localhost:8001"
        echo ""
        exit 1
        ;;
esac
