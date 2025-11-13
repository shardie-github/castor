# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+ (for frontend)
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

## Quick Start

### 1. Environment Setup

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Start Infrastructure Services

```bash
# Start PostgreSQL, Redis, Prometheus, and Grafana
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Database Setup

```bash
# Run migrations (when implemented)
python manage.py migrate

# Or manually create tables using schema-definition.md
```

### 4. Start Backend Services

```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Access Services

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t podcast-analytics:latest .

# Run container
docker run -d \
  --name podcast-analytics \
  -p 8000:8000 \
  --env-file .env \
  podcast-analytics:latest
```

### Using Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services
```

## Monitoring Setup

### Grafana Dashboards

1. Access Grafana at http://localhost:3000
2. Login with admin/admin
3. Dashboards are automatically provisioned from `grafana/dashboards/`

### Prometheus Metrics

- Metrics endpoint: http://localhost:8000/metrics
- Prometheus UI: http://localhost:9090

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically:
1. Runs tests on push/PR
2. Builds Docker images
3. Deploys to staging/production

Configure secrets in GitHub:
- `CONTAINER_REGISTRY`
- `REGISTRY_USERNAME`
- `REGISTRY_PASSWORD`
- `PRODUCTION_DATABASE_URL`

## Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec -it podcast_analytics_postgres psql -U postgres -d podcast_analytics

# Check Redis
docker exec -it podcast_analytics_redis redis-cli ping
```

### Service Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api
```

## Environment Variables

See `.env.example` for all required environment variables.

Key variables:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`
- `REDIS_HOST`, `REDIS_PORT`
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`
- `JWT_SECRET`, `ENCRYPTION_KEY`

---

*Last Updated: [Current Date]*
