# Quick Setup Guide

**Last Updated:** 2024-12

## Complete Setup (Automated)

Run the complete setup script to set up everything:

```bash
./scripts/complete-setup.sh
```

This will:
1. Install backend dependencies
2. Install frontend dependencies
3. Start infrastructure (Docker Compose)
4. Run database migrations
5. Optionally seed demo data

## Manual Setup

### 1. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
./scripts/db-migrate-local.sh

# Start backend
uvicorn src.main:app --reload
```

### 2. Frontend Setup

```bash
cd frontend
npm ci
npm run dev
```

### 3. Infrastructure

```bash
# Start Docker Compose services
docker-compose up -d
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Required variables:**
- `DATABASE_URL` or `POSTGRES_*` variables
- `REDIS_HOST` and `REDIS_PORT`
- `JWT_SECRET` (minimum 32 characters)
- `ENCRYPTION_KEY` (minimum 32 characters)

## Verify Setup

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
open http://localhost:3000

# Validate environment
python scripts/env-doctor.py
```

## Next Steps

- Read `docs/launch-readiness-report.md` for production readiness
- Review `docs/deployment-runbook.md` for deployment procedures
- Check `docs/api.md` for API documentation
