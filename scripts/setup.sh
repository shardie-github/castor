#!/bin/bash
# Complete Infrastructure Setup Script
# Sets up and starts all infrastructure

set -e

echo "=========================================="
echo "Podcast Analytics - Complete Setup"
echo "=========================================="
echo ""

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "Error: Docker not found. Please install Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose not found. Please install Docker Compose."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.11+."
    exit 1
fi

echo "✓ Prerequisites met"
echo ""

# Step 2: Setup environment
echo "Step 2: Setting up environment..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env file from .env.example"
        echo "  Please review and update .env with your configuration"
    else
        echo "✗ .env.example not found"
        exit 1
    fi
else
    echo "✓ .env file already exists"
fi
echo ""

# Step 3: Install Python dependencies
echo "Step 3: Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip3 install -q -r requirements.txt
    echo "✓ Python dependencies installed"
else
    echo "✗ requirements.txt not found"
    exit 1
fi
echo ""

# Step 4: Start infrastructure
echo "Step 4: Starting infrastructure services..."
bash scripts/start_infrastructure.sh
echo ""

# Step 5: Initialize database
echo "Step 5: Initializing database..."
python3 scripts/init_db.py
echo ""

# Step 6: Health check
echo "Step 6: Running health checks..."
python3 scripts/check_health.py
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Infrastructure is running:"
echo "  - PostgreSQL:    localhost:5432"
echo "  - Redis:         localhost:6379"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Grafana:       http://localhost:3000"
echo ""
echo "To start the API server:"
echo "  uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
