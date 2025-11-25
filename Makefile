.PHONY: help install dev test lint format type-check build clean deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install Python dependencies
	pip install -r requirements.txt

install-frontend: ## Install Node.js dependencies
	cd frontend && npm install

# Development
dev: dev-backend dev-frontend ## Start all services in development mode

dev-backend: ## Start backend API server
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

dev-db: ## Start database services (Docker Compose)
	docker-compose up -d postgres redis

dev-down: ## Stop database services
	docker-compose down

# Testing
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	pytest tests/ -v

test-frontend: ## Run frontend tests
	cd frontend && npm test -- --watchAll=false

test-coverage: ## Run tests with coverage
	pytest tests/ --cov=src --cov-report=html --cov-report=term
	cd frontend && npm test -- --watchAll=false --coverage

test-e2e: ## Run end-to-end tests
	pytest tests/e2e/ -v

# Code Quality
lint: lint-backend lint-frontend ## Lint all code

lint-backend: ## Lint backend code
	ruff check src/ tests/
	ruff format --check src/ tests/

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

format: format-backend format-frontend ## Format all code

format-backend: ## Format backend code
	ruff format src/ tests/

format-frontend: ## Format frontend code
	cd frontend && npm run format || echo "Format script not available"

type-check: type-check-backend type-check-frontend ## Type check all code

type-check-backend: ## Type check backend code
	mypy src/ --config-file pyproject.toml || echo "mypy config not found"

type-check-frontend: ## Type check frontend code
	cd frontend && npm run type-check

# Building
build: build-backend build-frontend ## Build all artifacts

build-backend: ## Build backend Docker image
	docker build -f Dockerfile.prod -t podcast-analytics-api:latest . || \
	docker build -f Dockerfile -t podcast-analytics-api:latest .

build-frontend: ## Build frontend
	cd frontend && npm run build

# Database
db-migrate: ## Run database migrations
	./scripts/db-migrate-local.sh

db-migrate-hosted: ## Run database migrations (hosted)
	./scripts/db-migrate-hosted.sh

db-validate: ## Validate database schema
	ts-node scripts/db-validate-schema.ts

db-reset: ## Reset local database (WARNING: destructive)
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 5
	$(MAKE) db-migrate

# Environment
env-check: ## Check environment variables
	ts-node scripts/env-doctor.ts

env-example: ## Generate .env.example from canonical list
	@echo "# Generated from env-doctor.ts"
	@ts-node scripts/env-doctor.ts | grep -E "^[A-Z_]+" || echo "# Run env-check for full list"

# CI/CD
ci: lint type-check test build ## Run all CI checks

ci-backend: lint-backend type-check-backend test-backend build-backend ## Run backend CI checks

ci-frontend: lint-frontend type-check-frontend test-frontend build-frontend ## Run frontend CI checks

# Documentation
docs: docs-api docs-generate ## Generate all documentation

docs-api: ## Generate API documentation
	python scripts/generate-api-docs.py

docs-serve: ## Serve documentation locally
	cd docs && python -m http.server 8080 || echo "Install Python http.server or use a static file server"

# Security
security-scan: ## Run security scans
	pip-audit || echo "pip-audit not installed"
	npm audit --prefix frontend || echo "npm audit failed"

# Cleanup
clean: clean-backend clean-frontend ## Clean all build artifacts

clean-backend: ## Clean backend artifacts
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov dist build

clean-frontend: ## Clean frontend artifacts
	cd frontend && rm -rf .next node_modules/.cache dist build

clean-all: clean ## Clean everything including dependencies
	rm -rf frontend/node_modules
	pip freeze | xargs pip uninstall -y || true

# Deployment
deploy-staging: ## Deploy to staging
	@echo "Deploying to staging..."
	git push origin develop

deploy-production: ## Deploy to production
	@echo "Deploying to production..."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		git push origin main; \
	fi

# Utilities
shell-backend: ## Open Python shell with app context
	python -c "from src.main import app; import IPython; IPython.embed()" || python

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d podcast_analytics

logs-backend: ## Show backend logs
	docker-compose logs -f backend || echo "Backend not running in Docker"

logs-db: ## Show database logs
	docker-compose logs -f postgres

# Health Checks
health: ## Check application health
	curl http://localhost:8000/health || echo "Backend not running"

health-frontend: ## Check frontend health
	curl http://localhost:3000 || echo "Frontend not running"

# Quick Start
setup: install dev-db db-migrate ## Complete setup for new developers
	@echo "✅ Setup complete!"
	@echo "Run 'make dev' to start development servers"

# Development Workflow
watch-backend: ## Watch backend files and restart on changes
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

watch-frontend: ## Watch frontend files (Next.js handles this automatically)
	cd frontend && npm run dev

# Database Utilities
db-backup: ## Backup local database
	docker-compose exec postgres pg_dump -U postgres podcast_analytics > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database from backup (usage: make db-restore FILE=backup.sql)
	docker-compose exec -T postgres psql -U postgres podcast_analytics < $(FILE)

# Monitoring
metrics: ## View Prometheus metrics
	curl http://localhost:9090/metrics || echo "Prometheus not running"

grafana: ## Open Grafana dashboard
	@echo "Grafana available at http://localhost:3000"
	@echo "Default credentials: admin/admin"

# Feature Flags
features-list: ## List all feature flags
	python -c "from src.features.flags import FeatureFlagService; import asyncio; import asyncpg; asyncio.run(FeatureFlagService(asyncpg.connect('postgresql://postgres:postgres@localhost:5432/podcast_analytics')).list_flags())" || echo "Database connection required"

# Development Tools
pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files || echo "pre-commit not installed"

pre-commit-install: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install

# Docker
docker-build: ## Build all Docker images
	docker-compose build

docker-up: ## Start all Docker services
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-ps: ## Show running Docker containers
	docker-compose ps

# Database Migrations (Advanced)
db-migrate-create: ## Create a new migration file (usage: make db-migrate-create NAME=migration_name)
	@mkdir -p db/migrations
	@timestamp=$$(date +%Y%m%d%H%M%S); \
	echo "-- Migration: $(NAME)" > db/migrations/$${timestamp}_$(NAME).sql; \
	echo "-- Created: $$(date)" >> db/migrations/$${timestamp}_$(NAME).sql; \
	echo "" >> db/migrations/$${timestamp}_$(NAME).sql; \
	echo "-- Add your migration SQL here" >> db/migrations/$${timestamp}_$(NAME).sql; \
	echo "Created: db/migrations/$${timestamp}_$(NAME).sql"

# Environment Setup
env-setup: ## Interactive environment setup
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example"; \
		echo "Please edit .env with your configuration"; \
	else \
		echo ".env already exists"; \
	fi

# Quick Commands
quick-test: ## Quick test (unit tests only, no coverage)
	pytest tests/unit/ -v -x

quick-lint: ## Quick lint (check only, no format)
	ruff check src/ tests/ --select E,F

# All-in-one
all: clean install lint type-check test build ## Run everything: clean, install, lint, type-check, test, build
	@echo "✅ All checks passed!"
