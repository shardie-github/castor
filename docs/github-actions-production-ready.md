# Production-Ready GitHub Actions Workflows

This document describes all the GitHub Actions workflows configured for production readiness.

## Overview

The repository includes comprehensive CI/CD workflows that ensure code quality, security, performance, and compliance before code reaches production.

## Workflow Categories

### 1. Continuous Integration (CI)

#### `ci.yml`
- **Purpose**: Core CI pipeline for linting, testing, and building
- **Triggers**: PR and push to main/develop
- **Jobs**:
  - Backend linting (ruff, mypy)
  - Frontend linting (ESLint, TypeScript)
  - Backend tests with coverage
  - Frontend tests with coverage
  - Docker image builds
  - Frontend builds

#### `pr-backend-validation.yml`
- **Purpose**: Backend-specific validation on PR commits
- **Triggers**: PR to main/develop
- **Jobs**:
  - Migration validation
  - Environment variable validation
  - Schema validation and health checks
  - Database migrations (optional, triggered with `[migrate]` in PR title)
  - Security audits
  - Setup validation

### 2. Code Quality

#### `code-quality-gates.yml`
- **Purpose**: Enforce code quality standards
- **Triggers**: PR and push to main/develop
- **Jobs**:
  - Code coverage checks (≥50% required)
  - Cyclomatic complexity analysis
  - Maintainability index checks
  - Code duplication detection
  - Lint quality scoring (pylint ≥7.0)

### 3. Security

#### `security-scan.yml`
- **Purpose**: Comprehensive security scanning
- **Triggers**: Weekly schedule, PR, push, manual
- **Jobs**:
  - Secrets scanning (Gitleaks, TruffleHog)
  - Backend dependency vulnerability scanning (pip-audit)
  - Frontend dependency vulnerability scanning (npm audit)
  - Code security scanning (Bandit)

#### `docker-scan.yml`
- **Purpose**: Docker image security and best practices
- **Triggers**: PR/push when Dockerfiles change, manual
- **Jobs**:
  - Dockerfile linting (hadolint)
  - Container vulnerability scanning (Trivy)
  - Image size optimization checks
  - Layer analysis

### 4. Performance

#### `performance-tests.yml`
- **Purpose**: Performance and load testing
- **Triggers**: PR when API/services change, manual
- **Jobs**:
  - API response time checks (<500ms avg, <1s max)
  - Load testing (Locust)
  - Database query performance
  - Frontend bundle size checks (<50MB)

### 5. API & Contracts

#### `api-contract-tests.yml`
- **Purpose**: API contract validation and compatibility
- **Triggers**: PR when API changes, manual
- **Jobs**:
  - OpenAPI schema validation
  - Breaking changes detection
  - Contract testing (Schemathesis)

### 6. Documentation

#### `documentation-checks.yml`
- **Purpose**: Ensure documentation quality
- **Triggers**: PR when docs change, manual
- **Jobs**:
  - Docstring coverage (≥60%)
  - README validation
  - Markdown linting
  - API documentation checks

### 7. Compliance

#### `license-compliance.yml`
- **Purpose**: License compliance checking
- **Triggers**: PR, push, weekly schedule
- **Jobs**:
  - Backend dependency license checking
  - Frontend dependency license checking
  - Repository license file validation
  - GPL/AGPL license detection

### 8. Release Management

#### `release-automation.yml`
- **Purpose**: Automated release process
- **Triggers**: Tag push (v*.*.*), manual dispatch
- **Jobs**:
  - Version format validation
  - CHANGELOG validation
  - GitHub release creation
  - Docker image building and tagging

### 9. Pre-commit & Standards

#### `pre-commit-validation.yml`
- **Purpose**: Enforce commit and branch standards
- **Triggers**: PR, manual
- **Jobs**:
  - Pre-commit hooks execution
  - Commit message format validation
  - Branch naming convention checks

#### `pr-requirements.yml`
- **Purpose**: PR quality gates
- **Triggers**: PR opened/updated
- **Jobs**:
  - PR title format check
  - PR description validation
  - Issue linking check
  - Test coverage requirement
  - Breaking changes documentation

### 10. Environment & Configuration

#### `environment-parity.yml`
- **Purpose**: Environment consistency checks
- **Triggers**: PR when env/config changes, manual
- **Jobs**:
  - Environment file parity
  - Required variables documentation
  - Hardcoded secrets detection
  - Configuration validation

### 11. Testing

#### `e2e-tests.yml`
- **Purpose**: End-to-end testing
- **Triggers**: PR, manual
- **Jobs**:
  - Full stack E2E tests with Playwright
  - Service integration tests

#### `smoke-tests.yml`
- **Purpose**: Production smoke tests
- **Triggers**: Push to main, manual
- **Jobs**:
  - Critical path smoke tests
  - Production health checks

### 12. Database

#### `db-migrate.yml`
- **Purpose**: Database migration management
- **Triggers**: Push when migrations change, manual
- **Jobs**:
  - Migration validation
  - Staging migrations
  - Production migrations (manual approval)

#### `test-migrations.yml`
- **Purpose**: Migration testing
- **Triggers**: PR when migrations change
- **Jobs**:
  - Migration rollback testing
  - Schema validation

## Workflow Dependencies

```
PR Created
  ├── pr-requirements.yml (PR quality gates)
  ├── pre-commit-validation.yml (Standards)
  ├── ci.yml (Core CI)
  ├── pr-backend-validation.yml (Backend validation)
  ├── code-quality-gates.yml (Quality checks)
  ├── security-scan.yml (Security)
  ├── docker-scan.yml (If Dockerfiles changed)
  ├── performance-tests.yml (If API changed)
  ├── api-contract-tests.yml (If API changed)
  ├── documentation-checks.yml (If docs changed)
  ├── license-compliance.yml (Compliance)
  ├── environment-parity.yml (If config changed)
  └── e2e-tests.yml (Full stack tests)

Push to Main
  ├── All PR checks
  ├── smoke-tests.yml (Production smoke tests)
  └── db-migrate.yml (If migrations changed)

Tag Push (v*.*.*)
  └── release-automation.yml (Release process)
```

## Quality Gates

### Required Checks (Must Pass)
- ✅ CI (linting, tests, builds)
- ✅ Code Quality Gates (coverage, complexity)
- ✅ Security Scan (no critical vulnerabilities)
- ✅ PR Requirements (title, description, tests)

### Recommended Checks (Warnings)
- ⚠️ Performance Tests (should pass but not blocking)
- ⚠️ Documentation Checks (warnings for missing docs)
- ⚠️ License Compliance (warnings for non-standard licenses)

## Configuration

### Required Secrets

See `docs/github-actions-pr-validation.md` for complete list. Key secrets:
- Database URLs (Supabase, staging, production)
- Supabase credentials
- JWT_SECRET, ENCRYPTION_KEY
- Docker registry credentials (for releases)

### Environment Variables

Most workflows use GitHub secrets. Some workflows require:
- `STAGING_DATABASE_URL` - For test migrations
- `PRODUCTION_DATABASE_URL` - For production migrations
- `DOCKER_REGISTRY` - For release artifacts

## Best Practices

1. **Always run checks locally** before pushing
2. **Fix failing checks** before requesting review
3. **Add tests** for new features
4. **Update documentation** with code changes
5. **Document breaking changes** in PR description
6. **Link related issues** in PR description
7. **Use conventional commits** for commit messages
8. **Keep PRs focused** - one feature/fix per PR

## Troubleshooting

### Workflow Not Running
- Check workflow file syntax
- Verify trigger conditions (paths, branches)
- Check GitHub Actions permissions

### Tests Failing
- Review test logs in Actions tab
- Run tests locally to reproduce
- Check for flaky tests

### Security Scan Failing
- Review vulnerability reports
- Update dependencies if needed
- Request exception if false positive

### Performance Tests Failing
- Check response time thresholds
- Optimize slow queries/endpoints
- Review bundle size optimizations

## Monitoring

- **GitHub Actions**: View workflow runs in Actions tab
- **Codecov**: Coverage reports and trends
- **GitHub Security**: Vulnerability alerts
- **Artifacts**: Test results, reports (30-90 day retention)

## Continuous Improvement

Workflows are continuously improved based on:
- Team feedback
- Industry best practices
- Security advisories
- Performance requirements

## Related Documentation

- [PR Backend Validation](./github-actions-pr-validation.md)
- [CI/CD Pipeline Setup](../README_SETUP.md)
- [Testing Guide](../tests/README.md)
- [Security Practices](../docs/security.md)
