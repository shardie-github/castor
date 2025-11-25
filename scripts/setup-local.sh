#!/bin/bash
# Local Development Setup Script
# One-command setup for local development environment

set -e

echo "🚀 Setting up local development environment..."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 20+ first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ All prerequisites met!"
echo ""

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

source venv/bin/activate
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python dependencies installed"
echo ""

# Set up environment variables
echo "⚙️  Setting up environment variables..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
        echo "⚠️  Please edit .env with your configuration"
    else
        echo "⚠️  .env.example not found, creating basic .env..."
        cat > .env << EOF
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/podcast_analytics

# Security
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
        echo "✅ Created basic .env file"
    fi
else
    echo "✅ .env file already exists"
fi
echo ""

# Start Docker services
echo "🐳 Starting Docker services (PostgreSQL, Redis)..."
docker-compose up -d postgres redis
echo "✅ Docker services started"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5
until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   Waiting..."
    sleep 2
done
echo "✅ PostgreSQL is ready"
echo ""

# Run database migrations
echo "🗄️  Running database migrations..."
if [ -f "scripts/db-migrate-local.sh" ]; then
    bash scripts/db-migrate-local.sh
    echo "✅ Database migrations completed"
else
    echo "⚠️  Migration script not found, skipping..."
fi
echo ""

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already installed"
fi
cd ..
echo ""

# Validate environment
echo "🔍 Validating environment..."
python3 scripts/validate-env.py
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration (if needed)"
echo "2. Start backend: uvicorn src.main:app --reload"
echo "3. Start frontend: cd frontend && npm run dev"
echo ""
echo "Backend will be available at: http://localhost:8000"
echo "Frontend will be available at: http://localhost:3000"
echo "API docs will be available at: http://localhost:8000/api/docs"
