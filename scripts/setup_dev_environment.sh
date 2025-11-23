#!/bin/bash
# One-Command Developer Environment Setup
# Run this script to set up a complete development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.11+ is required but not found"
        exit 1
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        print_success "Node.js $NODE_VERSION found"
    else
        print_error "Node.js 20+ is required but not found"
        exit 1
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker found"
    else
        print_info "Docker not found (optional, but recommended)"
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        print_success "Docker Compose found"
    else
        print_info "Docker Compose not found (optional, but recommended)"
    fi
}

# Setup Python environment
setup_python() {
    print_header "Setting Up Python Environment"
    
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    print_info "Activating virtual environment..."
    source venv/bin/activate || source venv/Scripts/activate
    
    print_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt --quiet
    print_success "Python dependencies installed"
}

# Setup Node.js environment
setup_node() {
    print_header "Setting Up Node.js Environment"
    
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        print_info "Installing Node.js dependencies..."
        npm ci --silent
        print_success "Node.js dependencies installed"
    else
        print_info "Node.js dependencies already installed"
    fi
    
    cd ..
}

# Setup environment file
setup_env() {
    print_header "Setting Up Environment Variables"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_info "Creating .env file from .env.example..."
            cp .env.example .env
            print_success ".env file created"
            print_info "Please edit .env file with your configuration"
        else
            print_error ".env.example not found"
        fi
    else
        print_info ".env file already exists"
    fi
}

# Setup database
setup_database() {
    print_header "Setting Up Database"
    
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        print_info "Starting database services with Docker Compose..."
        docker-compose up -d postgres redis || docker compose up -d postgres redis
        print_success "Database services started"
        print_info "Waiting for database to be ready..."
        sleep 5
    else
        print_info "Docker Compose not available, skipping database setup"
        print_info "Please ensure PostgreSQL and Redis are running"
    fi
}

# Run migrations
run_migrations() {
    print_header "Running Database Migrations"
    
    if [ -f "scripts/run_migrations.py" ]; then
        print_info "Running migrations..."
        source venv/bin/activate || source venv/Scripts/activate
        python scripts/run_migrations.py || print_info "Migrations script not available or failed"
    else
        print_info "Migration script not found, skipping"
    fi
}

# Verify setup
verify_setup() {
    print_header "Verifying Setup"
    
    # Check Python packages
    source venv/bin/activate || source venv/Scripts/activate
    if python -c "import fastapi" 2>/dev/null; then
        print_success "FastAPI installed"
    else
        print_error "FastAPI not installed"
    fi
    
    # Check Node packages
    if [ -d "frontend/node_modules" ]; then
        print_success "Frontend dependencies installed"
    else
        print_error "Frontend dependencies not installed"
    fi
    
    # Check environment file
    if [ -f ".env" ]; then
        print_success ".env file exists"
    else
        print_error ".env file missing"
    fi
}

# Main execution
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Developer Environment Setup           ║${NC}"
    echo -e "${BLUE}║  Podcast Analytics Platform            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    check_prerequisites
    setup_python
    setup_node
    setup_env
    setup_database
    run_migrations
    verify_setup
    
    print_header "Setup Complete!"
    echo ""
    print_success "Development environment is ready!"
    echo ""
    print_info "Next steps:"
    echo "  1. Edit .env file with your configuration"
    echo "  2. Start the backend: uvicorn src.main:app --reload"
    echo "  3. Start the frontend: cd frontend && npm run dev"
    echo ""
    print_info "For more information, see README.md"
    echo ""
}

main
