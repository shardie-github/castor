# Deployment Setup Guide

This document provides step-by-step instructions for setting up database connections, environment variables, CI/CD pipelines, monitoring dashboards, and payment processing integration.

## Table of Contents

1. [Database Connections](#database-connections)
2. [Environment Variables](#environment-variables)
3. [CI/CD Pipeline Configuration](#cicd-pipeline-configuration)
4. [Monitoring Dashboards (Grafana)](#monitoring-dashboards-grafana)
5. [Payment Processing (Stripe)](#payment-processing-stripe)
6. [Integration Testing](#integration-testing)

## Database Connections

### PostgreSQL/TimescaleDB Setup

The application uses PostgreSQL with TimescaleDB extension for time-series data.

**Connection Module:** `src/database/postgres.py` and `src/database/timescale.py`

**Features:**
- Connection pooling (min 5, max 20 connections)
- Health checks
- Async operations using `asyncpg`
- TimescaleDB hypertable creation
- Continuous aggregates
- Data retention policies

**Usage:**
```python
from src.database import PostgresConnection, TimescaleConnection
from src.config import config

# Initialize PostgreSQL connection
postgres = PostgresConnection(
    host=config.database.postgres_host,
    port=config.database.postgres_port,
    database=config.database.postgres_database,
    user=config.database.postgres_user,
    password=config.database.postgres_password
)

await postgres.initialize()

# Initialize TimescaleDB connection (extends PostgreSQL)
timescale = TimescaleConnection(
    host=config.database.postgres_host,
    port=config.database.postgres_port,
    database=config.database.postgres_database,
    user=config.database.postgres_user,
    password=config.database.postgres_password
)

await timescale.initialize()

# Create hypertable for time-series data
await timescale.create_hypertable("listener_metrics", "timestamp")
```

### Redis Setup

Redis is used for caching and session management.

**Connection Module:** `src/database/redis.py`

**Features:**
- Async Redis operations
- Key-value storage with expiration
- Health checks
- JSON serialization support

**Usage:**
```python
from src.database import RedisConnection
from src.config import config

redis = RedisConnection(
    host=config.database.redis_host,
    port=config.database.redis_port,
    password=config.database.redis_password
)

await redis.initialize()

# Store value with expiration
await redis.set("key", "value", ex=3600)

# Retrieve value
value = await redis.get("key")
```

### Docker Compose Setup

Start all infrastructure services:

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (TimescaleDB) on port 5432
- Redis on port 6379
- Prometheus on port 9090
- Grafana on port 3000

## Environment Variables

### Configuration File

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Required Variables

**Database:**
- `POSTGRES_HOST` - PostgreSQL host (default: localhost)
- `POSTGRES_PORT` - PostgreSQL port (default: 5432)
- `POSTGRES_DATABASE` - Database name (default: podcast_analytics)
- `POSTGRES_USER` - Database user (default: postgres)
- `POSTGRES_PASSWORD` - Database password
- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `REDIS_PASSWORD` - Redis password (optional)

**Security:**
- `JWT_SECRET` - Secret key for JWT tokens (generate random string)
- `ENCRYPTION_KEY` - Encryption key for sensitive data (generate random string)

**Stripe:**
- `STRIPE_SECRET_KEY` - Stripe secret key (starts with `sk_`)
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key (starts with `pk_`)

**External Services:**
- `SENDGRID_API_KEY` - SendGrid API key for emails
- `AWS_ACCESS_KEY_ID` - AWS access key (for S3, SES)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key

**Monitoring:**
- `PROMETHEUS_PORT` - Prometheus port (default: 9090)
- `GRAFANA_URL` - Grafana URL (default: http://localhost:3000)

**Environment:**
- `ENVIRONMENT` - Environment name (development, staging, production)
- `DEBUG` - Debug mode (true/false)

### Configuration Module

The configuration is loaded via `src/config/__init__.py`:

```python
from src.config import config

# Access configuration
db_host = config.database.postgres_host
stripe_key = config.stripe_secret_key
```

## CI/CD Pipeline Configuration

### GitHub Actions Workflows

**CI Pipeline:** `.github/workflows/ci.yml`
- Linting (flake8, black, mypy, ESLint, TypeScript)
- Unit tests (Python, JavaScript)
- Integration tests (with PostgreSQL and Redis)
- E2E tests (Playwright)
- Code coverage
- Build Docker images

**Deploy Pipeline:** `.github/workflows/deploy.yml`
- Deploy to staging (on `develop` branch)
- Deploy to production (on `main` branch)
- Database migrations
- Smoke tests

### Required GitHub Secrets

Configure these secrets in GitHub repository settings:

1. **Container Registry:**
   - `CONTAINER_REGISTRY` - Container registry URL
   - `REGISTRY_USERNAME` - Registry username
   - `REGISTRY_PASSWORD` - Registry password

2. **Database:**
   - `PRODUCTION_DATABASE_URL` - Production database connection string

3. **Stripe:**
   - `STRIPE_SECRET_KEY` - Stripe secret key for production
   - `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret

4. **Other Services:**
   - `SENDGRID_API_KEY` - SendGrid API key
   - `AWS_ACCESS_KEY_ID` - AWS access key
   - `AWS_SECRET_ACCESS_KEY` - AWS secret key

### Docker Build

The `Dockerfile` creates a production-ready image:

```bash
docker build -t podcast-analytics:latest .
```

## Monitoring Dashboards (Grafana)

### Dashboard Configuration

Dashboards are automatically provisioned from `grafana/dashboards/`:

1. **System Health Dashboard** (`system-health.json`)
   - System uptime
   - API request rate
   - API latency (p50, p95, p99)
   - Error rate
   - Database connections
   - Cache hit rate

2. **Business Metrics Dashboard** (`business-metrics.json`)
   - Active users
   - Campaigns created
   - Reports generated
   - Revenue
   - User growth
   - Campaign performance
   - Attribution events
   - Report generation time

### Accessing Grafana

1. Start services: `docker-compose up -d`
2. Access Grafana: http://localhost:3000
3. Login: `admin` / `admin` (change password on first login)
4. Dashboards are automatically available

### Prometheus Data Source

Prometheus is configured as the default data source in `grafana/provisioning/datasources/prometheus.yml`.

### Metrics Endpoint

The application exposes metrics at `/metrics` endpoint (Prometheus format).

## Payment Processing (Stripe)

### Stripe Integration

**Module:** `src/payments/stripe.py`

**Features:**
- Customer creation
- Payment intent creation and confirmation
- Subscription management
- Invoice generation
- Webhook processing

### Setup

1. **Get Stripe API Keys:**
   - Sign up at https://stripe.com
   - Get test keys from Dashboard → Developers → API keys
   - Add to `.env`:
     ```
     STRIPE_SECRET_KEY=sk_test_...
     STRIPE_PUBLISHABLE_KEY=pk_test_...
     ```

2. **Configure Webhook:**
   - In Stripe Dashboard → Developers → Webhooks
   - Add endpoint: `https://your-domain.com/api/webhooks/stripe`
   - Copy webhook signing secret
   - Add to `.env`: `STRIPE_WEBHOOK_SECRET=whsec_...`

### Usage

```python
from src.payments.stripe import StripePaymentProcessor
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

processor = StripePaymentProcessor(
    MetricsCollector(),
    EventLogger()
)

# Create customer
customer = await processor.create_customer(
    email="user@example.com",
    name="John Doe"
)

# Create payment intent
payment_intent = await processor.create_payment_intent(
    amount=10.00,
    currency="usd",
    customer_id=customer.id
)

# Confirm payment
confirmed = await processor.confirm_payment(
    payment_intent.intent_id,
    payment_method_id="pm_..."
)

# Create subscription
subscription = await processor.create_subscription(
    customer_id=customer.id,
    price_id="price_..."
)
```

### Webhook Processing

The billing automation module (`src/automation/billing.py`) has been updated to use Stripe for actual payment processing instead of placeholders.

## Integration Testing

### Database Tests

**File:** `tests/integration/test_database.py`

Tests PostgreSQL and Redis connections:

```bash
pytest tests/integration/test_database.py -v
```

### Stripe Tests

**File:** `tests/integration/test_stripe.py`

Tests Stripe integration (requires test API key):

```bash
pytest tests/integration/test_stripe.py -v
```

### Running All Integration Tests

```bash
# Start infrastructure
docker-compose up -d

# Run tests
pytest tests/integration/ -v
```

## Next Steps

1. **Database Migrations:** Create migration scripts using Alembic or similar
2. **Production Deployment:** Configure Kubernetes manifests or Terraform
3. **Monitoring Alerts:** Set up Alertmanager rules for Prometheus
4. **Backup Strategy:** Configure database backups
5. **SSL/TLS:** Set up SSL certificates for production
6. **Rate Limiting:** Configure Redis-based rate limiting in production
7. **Email Service:** Configure SendGrid or AWS SES for production emails

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

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

---

*Last Updated: [Current Date]*
