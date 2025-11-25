# Developer Onboarding Guide

Welcome to the Podcast Analytics & Sponsorship Platform! This guide will help you get set up and start contributing.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 20+** - [Download](https://nodejs.org/)
- **PostgreSQL 15+** - [Download](https://www.postgresql.org/download/) or use Docker
- **Redis 7+** - [Download](https://redis.io/download/) or use Docker
- **Docker & Docker Compose** (optional but recommended) - [Download](https://www.docker.com/)
- **Git** - [Download](https://git-scm.com/)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd podcast-analytics-platform
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, set:
# - DATABASE_URL or POSTGRES_* variables
# - JWT_SECRET (generate with: openssl rand -hex 32)
# - ENCRYPTION_KEY (generate with: openssl rand -hex 32)
```

### 3. Install Dependencies

**Option A: Using Make (Recommended)**

```bash
make install
```

**Option B: Manual Installation**

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install
```

### 4. Start Database Services

**Option A: Using Docker Compose (Recommended)**

```bash
make dev-db
# or
docker-compose up -d postgres redis
```

**Option B: Local Installation**

Ensure PostgreSQL and Redis are running locally.

### 5. Run Database Migrations

```bash
make db-migrate
# or
./scripts/db-migrate-local.sh
```

### 6. Start Development Servers

**Terminal 1: Backend**

```bash
make dev-backend
# or
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Frontend**

```bash
make dev-frontend
# or
cd frontend && npm run dev
```

### 7. Verify Installation

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Frontend: http://localhost:3000
- Health Check: http://localhost:8000/health

## Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run tests and linting**
   ```bash
   make test
   make lint
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Quality

**Before committing:**
```bash
# Format code
make format

# Run linting
make lint

# Run type checking
make type-check

# Run tests
make test
```

**Using pre-commit hooks:**
```bash
# Install pre-commit hooks
make pre-commit-install
# or
pip install pre-commit
pre-commit install
```

Pre-commit hooks will automatically:
- Format code
- Run linting
- Check types
- Run tests (on staged files)

## Project Structure

```
podcast-analytics-platform/
├── src/                    # Backend source code
│   ├── api/               # API route handlers
│   ├── database/          # Database connections
│   ├── services/          # Business logic
│   └── main.py            # Application entry point
├── frontend/              # Next.js frontend
│   ├── app/               # Next.js app router pages
│   ├── components/        # React components
│   └── public/            # Static assets
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── db/                    # Database migrations
├── scripts/               # Utility scripts
├── docs/                  # Documentation
└── docker-compose.yml     # Local development services
```

## Common Tasks

### Running Tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend

# With coverage
make test-coverage

# E2E tests
make test-e2e
```

### Database Operations

```bash
# Run migrations
make db-migrate

# Validate schema
make db-validate

# Reset database (WARNING: destructive)
make db-reset

# Backup database
make db-backup

# Restore database
make db-restore FILE=backup.sql
```

### Environment Management

```bash
# Check environment variables
make env-check

# Generate .env.example
make env-example
```

### Building

```bash
# Build everything
make build

# Backend only
make build-backend

# Frontend only
make build-frontend
```

## Development Tools

### VS Code Setup

1. Install recommended extensions (VS Code will prompt you)
2. Or install manually:
   ```bash
   code --install-extension ms-python.python
   code --install-extension dbaeumer.vscode-eslint
   code --install-extension esbenp.prettier-vscode
   ```

### Useful VS Code Commands

- `Ctrl+Shift+P` → "Python: Select Interpreter" - Choose Python 3.11+
- `Ctrl+Shift+P` → "TypeScript: Select TypeScript Version" - Use workspace version

### Debugging

**Backend (VS Code):**
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/main.py",
      "module": "uvicorn",
      "args": ["src.main:app", "--reload"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

**Frontend (VS Code):**
- Use Chrome DevTools
- Or install "Debugger for Chrome" extension

## API Development

### Adding a New Endpoint

1. Create route handler in `src/api/`
2. Register route in `src/api/route_registration.py`
3. Add tests in `tests/`
4. Update API documentation

**Example:**
```python
# src/api/example.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def get_example():
    return {"message": "Hello, World!"}
```

### Testing API Endpoints

```bash
# Using curl
curl http://localhost:8000/api/v1/health

# Using httpie
http GET http://localhost:8000/api/v1/health

# Using the interactive docs
# Visit http://localhost:8000/api/docs
```

## Frontend Development

### Adding a New Page

1. Create page in `frontend/app/`
2. Add components in `frontend/components/`
3. Add tests
4. Update navigation if needed

**Example:**
```typescript
// frontend/app/example/page.tsx
export default function ExamplePage() {
  return <div>Example Page</div>;
}
```

### API Integration

```typescript
// Use React Query for API calls
import { useQuery } from '@tanstack/react-query';

function usePodcasts() {
  return useQuery({
    queryKey: ['podcasts'],
    queryFn: async () => {
      const res = await fetch('/api/v1/podcasts');
      return res.json();
    }
  });
}
```

## Database Development

### Creating a Migration

```bash
make db-migrate-create NAME=add_new_table
```

Edit the generated migration file, then:

```bash
make db-migrate
```

### Database Schema

- Master schema: `db/migrations/99999999999999_master_schema.sql`
- Validate schema: `make db-validate`

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Kill process
kill -9 <PID>
```

**Database connection errors:**
- Check PostgreSQL is running: `docker-compose ps`
- Verify connection string in `.env`
- Check database exists: `make shell-db`

**Module not found:**
- Reinstall dependencies: `make install`
- Check Python path: `echo $PYTHONPATH`
- Verify virtual environment is activated

**Type errors:**
- Run type checker: `make type-check`
- Check TypeScript version matches
- Clear cache: `rm -rf frontend/.next`

### Getting Help

1. Check documentation in `docs/`
2. Review existing code for examples
3. Ask in team chat/Slack
4. Create an issue on GitHub

## Best Practices

### Code Style

- Follow PEP 8 for Python
- Follow ESLint/Prettier for TypeScript
- Use type hints in Python
- Use TypeScript types (avoid `any`)

### Testing

- Write tests for new features
- Aim for 70%+ coverage
- Test edge cases
- Test error conditions

### Git Workflow

- Use descriptive commit messages
- Keep commits small and focused
- Write clear PR descriptions
- Request reviews before merging

### Documentation

- Document complex logic
- Update API docs with changes
- Keep README up to date
- Add comments for non-obvious code

## Next Steps

1. **Explore the codebase**
   - Read `docs/stack-discovery.md` for architecture overview
   - Review `docs/api.md` for API documentation
   - Check `docs/security-audit.md` for security practices

2. **Pick a first issue**
   - Look for "good first issue" labels
   - Start with small bug fixes
   - Ask for help if stuck

3. **Set up your development environment**
   - Configure VS Code
   - Install pre-commit hooks
   - Set up debugging

4. **Join the team**
   - Introduce yourself
   - Ask questions
   - Share your progress

## Resources

- **API Documentation:** http://localhost:8000/api/docs
- **Architecture:** `docs/stack-discovery.md`
- **Deployment:** `docs/deploy-strategy.md`
- **Security:** `docs/security-audit.md`
- **CI/CD:** `docs/ci-overview.md`

## Support

If you encounter issues or have questions:

1. Check this guide first
2. Review existing documentation
3. Ask in team chat
4. Create an issue on GitHub

Welcome to the team! 🎉

---

**Last Updated:** 2024-12-XX
