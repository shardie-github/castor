# Podcast Analytics & Sponsorship Platform

## Overview

A comprehensive modular system for podcast analytics, sponsor campaign management, and automated reporting with built-in monetization, telemetry, and continuous measurement.

## Architecture

See [architecture/system-architecture.md](architecture/system-architecture.md) for detailed system architecture diagram showing data flow from ingestion through processing, analytics, frontend, partner APIs, and reporting endpoints.

## Core Modules

### 1. RSS/Feed Ingestion (`src/ingestion/rss_ingest.py`)
- RSS feed polling (every 15 minutes)
- Episode metadata extraction
- Feed validation & normalization
- Telemetry: ingestion_latency, feed_errors, poll_success_rate

### 2. Analytics Store (`src/analytics/analytics_store.py`)
- Time-series data storage
- Listener metrics aggregation
- Attribution event tracking
- Campaign performance calculations
- Telemetry: query_latency, storage_usage

### 3. Campaign Management (`src/campaigns/campaign_manager.py`)
- Campaign CRUD operations
- Sponsor relationship management
- Campaign lifecycle management
- Attribution configuration
- Telemetry: api_latency, operation_duration

### 4. Reporting Export (`src/reporting/report_generator.py`)
- Report template management
- PDF/CSV/Excel generation
- ROI calculations
- Automated report scheduling
- Telemetry: report_generation_time, pdf_size

### 5. User Management (`src/users/user_manager.py`)
- User authentication (OAuth, JWT)
- Role-based access control (RBAC)
- Subscription/billing integration
- Telemetry: auth_latency, user_operations

### 6. Background Task Agents (`src/agents/background_tasks.py`)
- Feed update scheduling
- Analytics aggregation
- Anomaly detection
- Alert generation
- Telemetry: task_success_rate, task_duration

## Monetization

See [monetization/pricing-plan.md](monetization/pricing-plan.md) for detailed pricing tiers and conversion logic.

### Pricing Tiers
- **Free**: $0/month - Basic features for solo podcasters
- **Starter**: $29/month - Advanced analytics and unlimited campaigns
- **Professional**: $99/month - API access, white-labeling, advanced features
- **Enterprise**: Custom pricing - Unlimited features, team collaboration, dedicated support

### Conversion Logic
- Automated freemium conversion based on usage signals
- Usage-based upsell triggers
- Persona-specific pricing recommendations
- Pricing events linked to product use

## Telemetry & Observability

### Metrics Collection (`src/telemetry/metrics.py`)
- Prometheus-compatible metrics
- Counter, Gauge, Histogram, Summary metrics
- Operational telemetry (latency, uptime, error rates)

### Event Logging (`src/telemetry/events.py`)
- User action events
- Feature usage tracking
- Friction/confusion signals
- Auto-support flow triggers
- Marketing/analytics integration

## Continuous Measurement

### Measurement Framework (`src/measurement/continuous_metrics.py`)
- **NPS Tracking**: Net Promoter Score calculation
- **Time to Complete**: Task completion time tracking
- **Success/Failure Rates**: Task success rate metrics
- **Feature Usage**: Feature adoption tracking
- **Satisfaction Scores**: User satisfaction measurement

### In-Line Metrics
Every feature includes:
- Usage tracking
- Satisfaction scores (1-10 scale)
- NPS calculation
- Time to complete
- Success/failure rates

## Marketing/Event Logging

### Auto-Support Flows
- Friction detection per page/feature
- Confusion signal logging
- Automatic support trigger
- Contextual help display

### Event Categories
- Page views
- User actions
- Feature usage
- Friction signals
- Support triggers
- Conversion events

## Key Telemetry Points

### User KPIs
- Time to First Value
- Campaign Renewal Rate
- Report Generation Rate
- Attribution Setup Completion
- Support Request Rate
- Feature Adoption Rate
- NPS Score

### Operational Telemetry
- Service Uptime
- Latency Percentiles (p50, p95, p99)
- Error Rates
- Throughput
- Queue Depth
- Database Performance

### Support Flow Metrics
- Support Ticket Volume
- Resolution Time
- First Response Time
- Self-Service Success Rate
- Friction Detection Rate

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL (for relational data)
- InfluxDB/TimescaleDB (for time-series data)
- Redis (for caching)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python manage.py migrate

# Start services
python manage.py runserver
```

### Development

```bash
# Run tests
pytest

# Run linter
flake8 src/

# Run type checker
mypy src/
```

## Project Structure

```
/workspace
├── architecture/
│   └── system-architecture.md      # System architecture diagram
├── monetization/
│   └── pricing-plan.md              # Pricing tiers and conversion logic
├── research/                        # Research documents
├── validation/                      # Validation frameworks
├── src/
│   ├── ingestion/                   # RSS/feed ingestion
│   ├── analytics/                   # Analytics store
│   ├── campaigns/                   # Campaign management
│   ├── reporting/                   # Report generation
│   ├── users/                       # User management
│   ├── agents/                      # Background tasks
│   ├── monetization/                # Pricing logic
│   ├── telemetry/                   # Metrics & events
│   └── measurement/                 # Continuous measurement
└── README.md
```

## Documentation

- [System Architecture](architecture/system-architecture.md)
- [Pricing Plan](monetization/pricing-plan.md)
- [User Personas](research/user-persona-matrix.md)
- [Analytics Events](validation/analytics-events.md)
- [Leading Indicators](validation/leading-indicators.md)

## License

See [LICENSE](LICENSE) file for details.

---

*Last Updated: [Current Date]*
*Version: 1.0*
