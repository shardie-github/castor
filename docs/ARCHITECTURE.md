# System Architecture

Complete architecture documentation for the Podcast Analytics & Sponsorship Platform.

## Overview

The platform is built as a modular, scalable system supporting multi-tenancy, real-time analytics, attribution tracking, and AI-powered features.

## Architecture Principles

1. **Modularity**: Clear separation of concerns with independent modules
2. **Scalability**: Horizontal scaling support for all components
3. **Reliability**: High availability with redundancy and failover
4. **Security**: Multi-layer security with RBAC/ABAC
5. **Observability**: Comprehensive logging, metrics, and tracing
6. **Multi-tenancy**: Complete tenant isolation

## System Components

### Frontend (Next.js)

**Location**: `frontend/`

**Technology Stack:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- TanStack Query
- Zustand

**Key Features:**
- Server-side rendering (SSR)
- Static site generation (SSG)
- Progressive Web App (PWA)
- Offline support
- Real-time updates

**Architecture:**
```
frontend/
├── app/              # Next.js App Router pages
├── components/       # Reusable React components
├── lib/              # Utilities and helpers
└── public/           # Static assets
```

### Backend (FastAPI)

**Location**: `src/`

**Technology Stack:**
- FastAPI
- Python 3.11+
- AsyncIO
- Pydantic
- SQLAlchemy

**Key Features:**
- Async/await throughout
- Automatic OpenAPI documentation
- Request validation
- Dependency injection
- Middleware pipeline

**Architecture:**
```
src/
├── api/              # API route handlers
├── analytics/        # Analytics processing
├── attribution/      # Attribution engine
├── campaigns/        # Campaign management
├── database/         # Database connections
├── ingestion/        # Data ingestion
├── reporting/        # Report generation
├── security/         # Authentication & authorization
├── telemetry/        # Metrics & logging
└── main.py           # Application entry point
```

### Database Layer

#### PostgreSQL (Primary)

**Purpose**: Relational data storage

**Tables:**
- `users` - User accounts
- `podcasts` - Podcast metadata
- `episodes` - Episode metadata
- `campaigns` - Campaign data
- `sponsors` - Sponsor information
- `reports` - Generated reports

**Features:**
- ACID compliance
- Foreign key constraints
- Indexes for performance
- Row-level security (RLS)

#### TimescaleDB (Time-Series)

**Purpose**: Time-series data storage

**Hypertables:**
- `listener_events` - Listener activity events
- `attribution_events` - Attribution tracking events

**Features:**
- Automatic partitioning by time
- Compression for old data
- Continuous aggregates
- Retention policies

#### Redis (Cache & Sessions)

**Purpose**: Caching and session management

**Use Cases:**
- API response caching
- Session storage
- Rate limiting
- Real-time data

### Data Flow

#### Ingestion Flow

```
External Sources (RSS, APIs)
    ↓
Ingestion Layer (rss_ingest.py, host_apis.py)
    ↓
Validation & Normalization
    ↓
PostgreSQL (podcasts, episodes)
    ↓
TimescaleDB (listener_events)
```

#### Attribution Flow

```
Conversion Sources (Pixels, Promo Codes, UTM)
    ↓
Attribution Engine (attribution_engine.py)
    ↓
Cross-Device Matching
    ↓
Demographic Enrichment
    ↓
TimescaleDB (attribution_events)
    ↓
ROI Calculations
```

#### Reporting Flow

```
Campaigns + Listener Events + Attribution Events
    ↓
Analytics Aggregation
    ↓
ROI Calculations
    ↓
Report Generation (PDF/CSV/Excel)
    ↓
Storage (reports table)
    ↓
Email Delivery / Download
```

## Multi-Tenancy

### Tenant Isolation

- **Database-level**: Row-level security (RLS) policies
- **Application-level**: Tenant context middleware
- **API-level**: Tenant ID validation

### Tenant Management

- Automatic tenant creation
- Tenant-specific configurations
- Resource quotas per tenant
- Billing per tenant

## Security Architecture

### Authentication

- **OAuth 2.0**: Standard OAuth flow
- **JWT Tokens**: Stateless authentication
- **MFA**: Multi-factor authentication support
- **API Keys**: For programmatic access

### Authorization

- **RBAC**: Role-based access control
- **ABAC**: Attribute-based access control
- **Permission Engine**: Unified permission system

### Security Layers

1. **Network**: HTTPS/TLS encryption
2. **Application**: Input validation, SQL injection prevention
3. **Database**: Row-level security, encrypted connections
4. **API**: Rate limiting, request signing

## Observability

### Metrics (Prometheus)

- **Application Metrics**: Request rates, latencies, errors
- **Business Metrics**: User actions, conversions, revenue
- **Infrastructure Metrics**: CPU, memory, disk, network

### Logging (Structured JSON)

- **Application Logs**: Request/response logging
- **Error Logs**: Exception tracking
- **Audit Logs**: Security events

### Tracing (OpenTelemetry)

- **Distributed Tracing**: Request flow across services
- **Performance Profiling**: Identify bottlenecks
- **Dependency Mapping**: Service dependencies

### Dashboards (Grafana)

- **Operational Dashboards**: System health, performance
- **Business Dashboards**: User metrics, revenue
- **Alerting**: Automated alerts on thresholds

## Deployment Architecture

### Containerization

- **Docker**: Container images
- **Docker Compose**: Local development
- **Kubernetes**: Production orchestration

### Infrastructure

- **Compute**: Auto-scaling containers
- **Database**: Managed PostgreSQL/TimescaleDB
- **Cache**: Managed Redis
- **Storage**: Object storage for reports/assets

### CI/CD

- **GitHub Actions**: CI/CD pipeline
- **Automated Testing**: Unit, integration, E2E
- **Automated Deployment**: Staging → Production
- **Migration Validation**: Schema checks

## Scalability

### Horizontal Scaling

- **Stateless API**: Scale API instances independently
- **Database Read Replicas**: Distribute read load
- **Caching Layer**: Reduce database load
- **CDN**: Static asset delivery

### Performance Optimization

- **Database Indexing**: Optimized queries
- **Query Optimization**: Efficient data access
- **Caching Strategy**: Multi-level caching
- **Async Processing**: Background jobs

## Disaster Recovery

### Backup Strategy

- **Database Backups**: Daily automated backups
- **Point-in-Time Recovery**: Transaction log backups
- **Offsite Storage**: Backup replication

### Failover

- **Primary/Secondary**: Active-passive setup
- **Automatic Failover**: Health check-based
- **Data Replication**: Real-time sync

## Integration Points

### External APIs

- **Podcast Platforms**: Apple Podcasts, Spotify, Google
- **Payment Processing**: Stripe
- **Email Service**: SendGrid
- **Cloud Storage**: AWS S3

### Webhooks

- **Incoming**: Receive events from external services
- **Outgoing**: Send events to subscribers
- **Signature Verification**: Secure webhook delivery

## Future Enhancements

1. **Microservices**: Split into independent services
2. **Event-Driven**: Message queue for async processing
3. **GraphQL API**: Alternative to REST
4. **Mobile Apps**: Native iOS/Android apps
5. **Real-Time**: WebSocket support for live updates

---

*Last Updated: 2024-01-15*
*Architecture Version: 1.0*
