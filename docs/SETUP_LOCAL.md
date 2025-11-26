# Local Setup Guide

**Quick path from fresh clone → app running locally**

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL client (`psql`) - optional

**Verify:**
```bash
python --version  # 3.11+
node --version    # 20+
docker --version
```

---

## Setup (5 minutes)

### 1. Clone & Environment
```bash
git clone <repo-url>
cd podcast-analytics-platform
cp .env.example .env
# Edit .env: Set DATABASE_URL (or use defaults for local)
```

### 2. Start Infrastructure
```bash
docker-compose up -d postgres redis
sleep 10  # Wait for services
```

### 3. Run Migrations
```bash
./scripts/db-migrate-local.sh
```

### 4. Install Dependencies
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm ci && cd ..
```

### 5. Start Servers

**Terminal 1 - Backend:**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend && npm run dev
```

### 6. Verify
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/api/docs

---

## Using Makefile (Alternative)

```bash
make setup      # Install deps + start DB + migrate
make dev        # Start backend + frontend
```

---

## Common Commands

```bash
make test              # Run tests
make lint             # Lint code
make db-migrate       # Run migrations
make db-reset         # Reset local DB (destructive)
docker-compose down   # Stop services
```

---

## Troubleshooting

**Database connection fails:**
- Check PostgreSQL is running: `docker-compose ps postgres`
- Wait 10-15 seconds after starting
- Verify `.env` has correct `DATABASE_URL`

**Port conflicts:**
- Backend (8000): Change in `uvicorn` command
- Frontend (3000): Change in `frontend/package.json`
- PostgreSQL (5432): Change in `docker-compose.yml`

**Frontend build fails:**
```bash
cd frontend
rm -rf node_modules .next
npm ci
```

**Backend import errors:**
- Verify virtual environment activated
- Reinstall: `pip install -r requirements.txt`

---

## Next Steps

- Read: [`docs/local-dev.md`](local-dev.md) - Detailed development guide
- Read: [`docs/deploy-strategy.md`](deploy-strategy.md) - Production deployment
- Read: [`README.md`](../README.md) - Project overview

---

**Setup complete?** See [`docs/FOUNDER_MANUAL.md`](FOUNDER_MANUAL.md) for what to do next.
