.PHONY: ci lint lint-backend lint-frontend test test-backend test-frontend type-check format install build build-backend build-frontend help dev-start dev-stop quick-check

help:
	@echo "Available commands:"
	@echo "  make ci              - Run all CI checks"
	@echo "  make lint            - Lint backend and frontend"
	@echo "  make lint-backend    - Lint backend only"
	@echo "  make lint-frontend   - Lint frontend only"
	@echo "  make test            - Run all tests"
	@echo "  make test-backend    - Run backend tests"
	@echo "  make test-frontend   - Run frontend tests"
	@echo "  make type-check      - Type check backend and frontend"
	@echo "  make format          - Format backend and frontend code"
	@echo "  make build           - Build backend and frontend"
	@echo "  make install         - Install all dependencies"
	@echo ""
	@echo "Development helpers (solo operator optimized):"
	@echo "  make dev-start       - Start development servers"
	@echo "  make dev-stop        - Stop development servers"
	@echo "  make quick-check     - Quick health check before commit"

ci: lint type-check test build
	@echo "✅ All CI checks passed!"

lint: lint-backend lint-frontend

lint-backend:
	@echo "🔍 Linting backend..."
	ruff check src/ tests/
	ruff format --check src/ tests/
	mypy src/ --config-file pyproject.toml

lint-frontend:
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint
	cd frontend && npm run type-check

test: test-backend test-frontend

test-backend:
	@echo "🧪 Running backend tests..."
	pytest tests/unit/ tests/integration/ -v --cov=src --cov-report=term --cov-fail-under=50

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test -- --watchAll=false

type-check:
	@echo "🔎 Type checking..."
	mypy src/ --config-file pyproject.toml
	cd frontend && npm run type-check

format:
	@echo "✨ Formatting code..."
	ruff format src/ tests/
	cd frontend && npm run format || echo "No format script in frontend"

build: build-backend build-frontend

build-backend:
	@echo "🏗️  Building backend..."
	@if [ -f Dockerfile.prod ]; then \
		docker build -f Dockerfile.prod -t podcast-analytics-api:test .; \
	elif [ -f Dockerfile ]; then \
		docker build -f Dockerfile -t podcast-analytics-api:test .; \
	else \
		echo "No Dockerfile found, skipping backend build"; \
	fi

build-frontend:
	@echo "🏗️  Building frontend..."
	cd frontend && npm run build

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	cd frontend && npm ci

dev-start:
	@echo "🚀 Starting development servers..."
	@./scripts/dev.sh start

dev-stop:
	@echo "🛑 Stopping development servers..."
	@./scripts/dev.sh stop

quick-check:
	@echo "🔍 Running quick health check..."
	@./scripts/quick-check.sh
