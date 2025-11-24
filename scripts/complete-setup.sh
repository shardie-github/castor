#!/usr/bin/env bash
# Complete Setup Script
# Sets up the entire development environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Complete Development Environment Setup ===${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

MISSING_DEPS=()

if ! command -v python3 &> /dev/null; then
    MISSING_DEPS+=("python3")
fi

if ! command -v node &> /dev/null; then
    MISSING_DEPS+=("node")
fi

if ! command -v docker &> /dev/null && ! command -v docker-compose &> /dev/null; then
    MISSING_DEPS+=("docker")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}Missing dependencies: ${MISSING_DEPS[*]}${NC}"
    echo "Please install missing dependencies and try again."
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Step 1: Install backend dependencies
echo -e "${BLUE}Step 1: Installing backend dependencies...${NC}"
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi
echo ""

# Step 2: Install frontend dependencies
echo -e "${BLUE}Step 2: Installing frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm ci
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ node_modules already exists${NC}"
fi
cd ..
echo ""

# Step 3: Start infrastructure
echo -e "${BLUE}Step 3: Starting infrastructure (Docker Compose)...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
    echo "Waiting for services to be ready..."
    sleep 10
    echo -e "${GREEN}✓ Infrastructure started${NC}"
else
    echo -e "${YELLOW}⚠ Docker Compose not found, skipping infrastructure${NC}"
fi
echo ""

# Step 4: Run database migrations
echo -e "${BLUE}Step 4: Running database migrations...${NC}"
if [ -f "scripts/db-migrate-local.sh" ]; then
    chmod +x scripts/db-migrate-local.sh
    ./scripts/db-migrate-local.sh || {
        echo -e "${YELLOW}⚠ Migration failed (database may not be ready)${NC}"
    }
else
    echo -e "${YELLOW}⚠ Migration script not found${NC}"
fi
echo ""

# Step 5: Seed demo data (optional)
echo -e "${BLUE}Step 5: Seeding demo data (optional)...${NC}"
read -p "Seed demo data? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "scripts/seed-demo-data.py" ]; then
        export SKIP_ENV_VALIDATION="true"
        export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/podcast_analytics"
        export JWT_SECRET="dev_secret_key_min_32_chars_long_for_local_dev"
        export ENCRYPTION_KEY="dev_encryption_key_min_32_chars_long_for_local"
        python3 scripts/seed-demo-data.py || {
            echo -e "${YELLOW}⚠ Seed data failed${NC}"
        }
    else
        echo -e "${YELLOW}⚠ Seed script not found${NC}"
    fi
else
    echo "Skipping seed data"
fi
echo ""

# Step 6: Verify setup
echo -e "${BLUE}Step 6: Verifying setup...${NC}"

# Check backend
if python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}✓ Backend dependencies verified${NC}"
else
    echo -e "${RED}✗ Backend dependencies not installed${NC}"
fi

# Check frontend
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✓ Frontend dependencies verified${NC}"
else
    echo -e "${RED}✗ Frontend dependencies not installed${NC}"
fi

# Check database
if command -v psql &> /dev/null; then
    if psql "postgresql://postgres:postgres@localhost:5432/podcast_analytics" -c "SELECT 1;" &>/dev/null; then
        echo -e "${GREEN}✓ Database connection verified${NC}"
    else
        echo -e "${YELLOW}⚠ Database not accessible${NC}"
    fi
fi

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Start backend:  make dev-start  (or: uvicorn src.main:app --reload)"
echo "  2. Start frontend: cd frontend && npm run dev"
echo "  3. Visit: http://localhost:3000"
echo ""
echo "Useful commands:"
echo "  - Run tests: make test"
echo "  - Run lint: make lint"
echo "  - Check health: curl http://localhost:8000/health"
echo ""
