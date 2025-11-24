# Local Development Guide

**Last Updated:** 2024  
**Purpose:** Step-by-step guide for setting up local development environment

---

## Prerequisites

### Required Software

- **Python 3.11+** - Backend runtime
- **Node.js 20+** - Frontend runtime
- **npm 9+** - Frontend package manager
- **Docker & Docker Compose** - Database and Redis
- **PostgreSQL client** (`psql`) - Database migrations (optional)

### Verify Installation

```bash
python --version  # Should be 3.11+
node --version    # Should be 20+
npm --version     # Should be 9+
docker --version  # Should be installed
docker-compose --version  # Should be installed
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd podcast-analytics-platform
```

### 2. Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local configuration
# Minimum required:
# - DATABASE_URL (or POSTGRES_* variables)
# - JWT_SECRET (generate with: openssl rand -base64 32)
# - ENCRYPTION_KEY (generate with: openssl rand -base64 32)
```

### 3. Start Infrastructure

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to be ready (10-15 seconds)
sleep 10
```

### 4. Run Database Migrations

```bash
# Apply master schema migration
./scripts/db-migrate-local.sh
```

### 5. Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm ci
cd ..
```

### 6. Start Development Servers

**Terminal 1 - Backend:**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 7. Verify Setup

- **Backend:** http://localhost:8000
  - Health check: http://localhost:8000/health
  - API docs: http://localhost:8000/api/docs

- **Frontend:** http://localhost:3000

---

## Detailed Setup

### Backend Setup

#### Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure Backend

**Environment Variables (`.env`):**
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/podcast_analytics

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security (generate strong secrets)
JWT_SECRET=your-local-jwt-secret-min-32-chars-long
ENCRYPTION_KEY=your-local-encryption-key-min-32-chars-long

# Environment
ENVIRONMENT=development
DEBUG=true

# CORS (allow frontend)
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

#### Run Backend

```bash
# Development server (with auto-reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or use Makefile
make dev-start  # Starts both backend and frontend
```

---

### Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm ci  # Uses package-lock.json for reproducible installs
```

#### Configure Frontend

**Environment Variables (`.env.local` in `frontend/` directory):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_SUPABASE_URL=  # Optional
NEXT_PUBLIC_SUPABASE_ANON_KEY=  # Optional
```

#### Run Frontend

```bash
npm run dev  # Starts Next.js dev server on http://localhost:3000
```

---

### Database Setup

#### Start PostgreSQL with TimescaleDB

```bash
# Using Docker Compose (recommended)
docker-compose up -d postgres

# Verify it's running
docker-compose ps postgres
```

#### Apply Migrations

```bash
# Using migration script (recommended)
./scripts/db-migrate-local.sh

# Or manually with psql
psql postgresql://postgres:postgres@localhost:5432/podcast_analytics \
  -f db/migrations/99999999999999_master_schema.sql
```

#### Verify Database

```bash
# Connect to database
psql postgresql://postgres:postgres@localhost:5432/podcast_analytics

# Check tables
\dt

# Check TimescaleDB hypertables
SELECT * FROM timescaledb_information.hypertables;
```

---

### Redis Setup

#### Start Redis

```bash
# Using Docker Compose
docker-compose up -d redis

# Verify it's running
docker-compose ps redis
```

#### Test Redis Connection

```bash
# Connect to Redis
docker exec -it podcast_analytics_redis redis-cli

# Test
PING  # Should return PONG
```

---

## Development Workflow

### Running Tests

**Backend Tests:**
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_analytics.py -v
```

**Frontend Tests:**
```bash
cd frontend
npm test  # Run tests
npm run test:watch  # Watch mode
npm run test:coverage  # With coverage
```

### Code Quality

**Backend:**
```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/

# Or use Makefile
make lint-backend
```

**Frontend:**
```bash
cd frontend
npm run lint  # ESLint
npm run type-check  # TypeScript
```

### Running CI Checks Locally

```bash
# Run all CI checks
make ci

# Or individually
make lint
make test
make type-check
make build
```

---

## Common Tasks

### Seed Demo Data

```bash
# Set DATABASE_URL in environment
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/podcast_analytics

# Run seed script
python scripts/seed-demo-data.py
```

### Reset Database

```bash
# Drop and recreate database
docker-compose down -v postgres
docker-compose up -d postgres
sleep 10
./scripts/db-migrate-local.sh
```

### View Logs

```bash
# Backend logs (if running in terminal)
# Already visible in terminal

# Database logs
docker-compose logs postgres

# Redis logs
docker-compose logs redis

# All services
docker-compose logs
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop specific service
docker-compose stop postgres

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

---

## Troubleshooting

### Database Connection Issues

**Error:** `could not connect to server`

**Solutions:**
1. Verify PostgreSQL is running: `docker-compose ps postgres`
2. Check connection string in `.env`
3. Wait for PostgreSQL to be ready (10-15 seconds after start)
4. Check port 5432 is not in use: `lsof -i :5432`

### Redis Connection Issues

**Error:** `Connection refused`

**Solutions:**
1. Verify Redis is running: `docker-compose ps redis`
2. Check `REDIS_HOST` and `REDIS_PORT` in `.env`
3. Test connection: `docker exec -it podcast_analytics_redis redis-cli PING`

### Frontend Build Issues

**Error:** `Module not found` or build failures

**Solutions:**
1. Delete `node_modules` and reinstall: `rm -rf node_modules && npm ci`
2. Clear Next.js cache: `rm -rf .next`
3. Check Node version: `node --version` (should be 20+)
4. Check for TypeScript errors: `npm run type-check`

### Backend Import Issues

**Error:** `ModuleNotFoundError`

**Solutions:**
1. Verify virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.11+)
4. Verify `src/` is in Python path

### Migration Issues

**Error:** `relation already exists` or migration failures

**Solutions:**
1. Check if migration was already applied
2. Verify TimescaleDB extension is available
3. Check migration file syntax
4. Review database logs: `docker-compose logs postgres`

---

## Development Tips

### Hot Reload

- **Backend:** `uvicorn --reload` automatically reloads on code changes
- **Frontend:** Next.js automatically reloads on code changes

### Database Changes

1. Create new migration file in `db/migrations/`
2. Test locally: `./scripts/db-migrate-local.sh`
3. Commit migration file
4. CI will validate migration

### Environment Variables

- **Backend:** Use `.env` file (loaded by `python-dotenv`)
- **Frontend:** Use `.env.local` file (Next.js convention)
- **Never commit:** `.env` or `.env.local` (already in `.gitignore`)

### Debugging

**Backend:**
- Use `print()` or `logging` for debugging
- Check logs in terminal where `uvicorn` is running
- Use FastAPI docs: http://localhost:8000/api/docs

**Frontend:**
- Use browser DevTools (F12)
- Check Next.js terminal output
- Use React DevTools extension

---

## Next Steps

1. **Read Documentation:**
   - `docs/stack-discovery.md` - Technology stack overview
   - `docs/backend-strategy.md` - Backend architecture
   - `docs/frontend-hosting-strategy.md` - Frontend deployment

2. **Explore Codebase:**
   - `src/` - Backend source code
   - `frontend/app/` - Frontend pages
   - `frontend/components/` - React components

3. **Run Tests:**
   - `make test` - Run all tests
   - `make lint` - Check code quality

4. **Start Developing:**
   - Create feature branch
   - Make changes
   - Run tests and lint
   - Submit PR

---

## Summary

**Setup Time:** 10-15 minutes

**Key Commands:**
```bash
# Start infrastructure
docker-compose up -d postgres redis

# Run migrations
./scripts/db-migrate-local.sh

# Install dependencies
pip install -r requirements.txt
cd frontend && npm ci

# Start servers
uvicorn src.main:app --reload  # Backend
npm run dev  # Frontend
```

**Verification:**
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000
- Database: `psql postgresql://postgres:postgres@localhost:5432/podcast_analytics`

**Need Help?** Check troubleshooting section or review documentation in `docs/`.
