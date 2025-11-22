#!/bin/bash
# Development helper script for solo operators
# Quick commands to get things done fast

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Setup development environment
setup() {
    print_info "Setting up development environment..."
    
    # Check Python
    if ! command_exists python3; then
        print_warning "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check Node.js
    if ! command_exists node; then
        print_warning "Node.js not found. Please install Node.js 20+"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    # Install frontend dependencies
    if [ -d "frontend" ]; then
        print_info "Installing frontend dependencies..."
        cd frontend
        npm ci --silent
        cd ..
    fi
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_info "Please edit .env with your configuration"
        else
            print_warning "No .env.example found. You'll need to create .env manually"
        fi
    fi
    
    print_success "Setup complete!"
}

# Start development servers
start() {
    print_info "Starting development servers..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start backend in background
    print_info "Starting backend API..."
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/backend.pid
    
    # Start frontend if it exists
    if [ -d "frontend" ]; then
        print_info "Starting frontend..."
        cd frontend
        npm run dev > /tmp/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > /tmp/frontend.pid
        cd ..
    fi
    
    print_success "Development servers started!"
    print_info "Backend: http://localhost:8000"
    print_info "Backend API docs: http://localhost:8000/api/docs"
    if [ -d "frontend" ]; then
        print_info "Frontend: http://localhost:3000"
    fi
    print_info "Logs: /tmp/backend.log and /tmp/frontend.log"
    print_info "To stop: ./scripts/dev.sh stop"
}

# Stop development servers
stop() {
    print_info "Stopping development servers..."
    
    if [ -f "/tmp/backend.pid" ]; then
        BACKEND_PID=$(cat /tmp/backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_success "Backend stopped"
        fi
        rm /tmp/backend.pid
    fi
    
    if [ -f "/tmp/frontend.pid" ]; then
        FRONTEND_PID=$(cat /tmp/frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            print_success "Frontend stopped"
        fi
        rm /tmp/frontend.pid
    fi
    
    # Kill any remaining processes
    pkill -f "uvicorn src.main:app" || true
    pkill -f "next dev" || true
}

# Run tests
test() {
    print_info "Running tests..."
    source venv/bin/activate
    
    # Set test environment variables
    export SKIP_ENV_VALIDATION=true
    export ENVIRONMENT=test
    
    pytest tests/ -v "$@"
}

# Run linting
lint() {
    print_info "Running linters..."
    source venv/bin/activate
    
    ruff check src/ tests/
    ruff format --check src/ tests/
    mypy src/ --config-file pyproject.toml || print_warning "Type checking found issues (non-blocking)"
}

# Format code
format() {
    print_info "Formatting code..."
    source venv/bin/activate
    
    ruff format src/ tests/
    print_success "Code formatted!"
}

# Run database migrations
migrate() {
    print_info "Running database migrations..."
    source venv/bin/activate
    
    if [ -f "scripts/run_migrations.py" ]; then
        python scripts/run_migrations.py
    else
        print_warning "Migration script not found. Skipping migrations."
    fi
}

# Clean up temporary files
clean() {
    print_info "Cleaning up..."
    
    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove test coverage
    rm -rf htmlcov/ .coverage coverage.xml 2>/dev/null || true
    
    # Remove frontend build
    if [ -d "frontend/.next" ]; then
        rm -rf frontend/.next
    fi
    
    print_success "Cleanup complete!"
}

# Show help
help() {
    echo "Development Helper Script"
    echo ""
    echo "Usage: ./scripts/dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Set up development environment"
    echo "  start     - Start development servers"
    echo "  stop      - Stop development servers"
    echo "  test      - Run tests"
    echo "  lint      - Run linters"
    echo "  format    - Format code"
    echo "  migrate   - Run database migrations"
    echo "  clean     - Clean temporary files"
    echo "  help      - Show this help message"
    echo ""
}

# Main command handler
case "${1:-help}" in
    setup)
        setup
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    test)
        test "${@:2}"
        ;;
    lint)
        lint
        ;;
    format)
        format
        ;;
    migrate)
        migrate
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_warning "Unknown command: $1"
        help
        exit 1
        ;;
esac
