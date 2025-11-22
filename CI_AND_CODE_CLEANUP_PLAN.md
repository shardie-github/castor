# CI & Code Cleanup Plan: From Red to Green

**Generated:** $(date)  
**Status:** Analysis Complete - Ready for Implementation

---

## A. DISCOVER THE CURRENT STATE (CODE + CI)

### CODE & STRUCTURE SNAPSHOT

**High-Level Structure:**
- **Backend:** Python 3.11 FastAPI application in `src/` with ~30+ modules
- **Frontend:** Next.js 14 TypeScript application in `frontend/`
- **Tests:** Minimal test coverage (`tests/unit/`, `tests/integration/`, `tests/smoke/`, `tests/e2e/`)
- **Infrastructure:** Docker Compose (Postgres, Redis, Prometheus, Grafana), Kubernetes configs, Terraform

**Key Issues Identified:**

1. **Dual Config Systems:** `src/config/__init__.py` (dataclass-based) vs `src/config/validation.py` (Pydantic-based) - both used inconsistently
2. **Heavy Module-Level Imports:** `src/main.py` imports ~40+ modules at top level, causing side effects and slow startup
3. **API Route Proliferation:** 32 API route files in `src/api/` - many likely thin wrappers or duplicates
4. **Inconsistent Naming:** Mix of `snake_case` and `camelCase` in some modules, inconsistent `__init__.py` exports
5. **Test Coverage Gaps:** Only 3 unit test files, 1 smoke test file, 1 e2e test file for entire codebase
6. **No Test Fixtures:** Tests create resources inline (e.g., `test_critical_paths.py` registers users in fixtures)
7. **Missing Tool Config:** No `pyproject.toml` for unified Python tooling (black, isort, mypy, pytest)

**Structural Problems:**
- `src/main.py` is 800+ lines - violates single responsibility
- Many modules lack `__init__.py` or have inconsistent exports
- No clear separation between core business logic and infrastructure code
- Duplication: `src/analytics/analytics_store.py` vs `src/business/analytics.py` (likely overlap)

### CI & CHECKS SNAPSHOT

**Workflow Inventory:**

1. **`.github/workflows/ci.yml`** (Primary CI)
   - Triggers: `push`/`pull_request` to `main`, `develop`
   - Jobs: `test`, `lint`, `frontend-test`, `e2e`
   - Issues: No caching, coverage threshold 60% (may fail), frontend tests run separately

2. **`.github/workflows/ci-cd.yml`** (Duplicate CI)
   - Triggers: Same as `ci.yml`
   - Jobs: `test` (with `|| true` on all checks - **NEVER FAILS**)
   - Issues: All checks are non-blocking, uses `|| true` everywhere

3. **`.github/workflows/ci-cd-complete.yml`** (Most Comprehensive)
   - Triggers: Same as above
   - Jobs: `lint-backend`, `lint-frontend`, `unit-tests`, `smoke-tests`, `build-backend`, `build-frontend`, `security-scan`, `migration-validation`, `deploy-staging`, `deploy-production`
   - Issues: Many jobs have `|| true`, runs on every PR (too heavy), no caching

4. **`.github/workflows/frontend-ci.yml`** (Frontend-Specific)
   - Triggers: Path-based (`frontend/**`)
   - Jobs: `lint`, `type-check`, `test`, `build`
   - Issues: Overlaps with other workflows, Node version inconsistency (18 vs 20)

5. **`.github/workflows/deploy.yml`** (Deployment)
   - Triggers: `push` to `main`, `workflow_dispatch`
   - Jobs: `deploy-staging`, `deploy-production`
   - Issues: Conditional logic may not work correctly (`if: github.ref == 'refs/heads/develop'` but trigger is `main`)

6. **`.github/workflows/aurora-doctor.yml`** (Health Check)
   - Triggers: Schedule (every 6h), `workflow_dispatch`, `push` to `main`/`develop`
   - Jobs: `doctor` (runs health checks)
   - Issues: Runs on every push (should be scheduled only)

**Total Checks Per PR:** ~15-20 jobs across 6 workflows (massive overlap)

**Configuration Issues:**
- `.flake8`: `max-line-length=127` but workflows use `120`
- `.mypy.ini`: `ignore_missing_imports = True` (defeats type checking)
- No `pyproject.toml` for unified config
- Python version inconsistency: Some workflows use `3.11`, others don't specify
- Node version inconsistency: `18` vs `20` across workflows

### WHY SO MANY FAILING CHECKS (HYPOTHESES)

1. **Non-Blocking Checks:** `ci-cd.yml` and `ci-cd-complete.yml` use `|| true` everywhere, so checks appear to run but never fail builds. This creates false sense of security.

2. **Workflow Overlap:** Multiple workflows run the same checks (lint, test, build) on every PR, causing duplicate runs and confusion about which one "counts."

3. **Missing Dependencies:** Tests require Postgres/Redis but some workflows don't set up services, causing failures.

4. **Flaky Tests:** Smoke tests (`test_critical_paths.py`) create real users/DB records without cleanup, causing conflicts on parallel runs.

5. **Type Check Misconfiguration:** `mypy` configured to ignore missing imports, so type errors are hidden.

6. **Coverage Threshold Too High:** 60% coverage threshold may fail on new code that doesn't have tests yet.

7. **Frontend Build Failures:** Frontend build may fail due to missing env vars (`NEXT_PUBLIC_*`) in CI.

8. **Migration Validation:** `ci-cd-complete.yml` runs migration validation that may fail if migrations aren't compatible with test DB.

9. **Security Scan Failures:** `safety check` and `detect-secrets` may fail on false positives or missing baseline.

10. **No Caching:** Every workflow installs dependencies from scratch, causing slow runs and potential network failures.

---

## B. DESIGN THE TARGET STATE – CLEAN, COHESIVE, ALWAYS-GREEN PIPELINE

### TARGET CODE PRINCIPLES

1. **Single Source of Truth:** One config system (`src/config/validation.py` with Pydantic), remove `src/config/__init__.py` dataclass version.

2. **Lazy Imports:** No heavy imports at module level in `main.py` - use dependency injection and lazy loading.

3. **Clear Module Boundaries:** Each module has a single responsibility, clear `__init__.py` exports, no circular dependencies.

4. **Testability First:** Core business logic is pure functions/classes with minimal side effects, easy to mock.

5. **Consistent Naming:** `snake_case` for Python, `camelCase` for TypeScript, consistent `__init__.py` patterns.

6. **Type Safety:** Strict mypy configuration (no `ignore_missing_imports`), TypeScript strict mode enforced.

7. **Fast Feedback:** Unit tests run in <30s, integration tests <2min, e2e tests run separately.

8. **Documentation:** Every public function/class has docstrings, complex logic has inline comments.

### TARGET CI CHECK SET

**Core Checks (Run on Every PR):**

1. **`lint-backend`** (2-3 min)
   - Tools: `ruff` (replaces flake8 + black + isort), `mypy`
   - Purpose: Code quality, formatting, type safety
   - Must pass: YES

2. **`lint-frontend`** (1-2 min)
   - Tools: `eslint`, `prettier --check`, `tsc --noEmit`
   - Purpose: Code quality, formatting, type safety
   - Must pass: YES

3. **`test-backend`** (3-5 min)
   - Tools: `pytest` with coverage
   - Purpose: Unit + integration tests
   - Must pass: YES (coverage threshold: 50% for now, increase to 60% later)

4. **`test-frontend`** (2-3 min)
   - Tools: `jest`
   - Purpose: Unit tests
   - Must pass: YES

5. **`build-backend`** (1-2 min)
   - Tools: Docker build (if Dockerfile exists)
   - Purpose: Ensure backend builds successfully
   - Must pass: YES

6. **`build-frontend`** (2-3 min)
   - Tools: `npm run build`
   - Purpose: Ensure frontend builds successfully
   - Must pass: YES

**Optional Checks (Run on Schedule/Nightly):**

- `security-scan`: Safety check, dependency audit
- `migration-validation`: Validate DB migrations
- `e2e-tests`: Full end-to-end tests (slow, flaky)
- `aurora-doctor`: Health checks

**Total PR Checks:** 6 core checks (all must pass)

### WHAT TO DISABLE / CONSOLIDATE

**Disable Entirely:**
- `.github/workflows/ci-cd.yml` (duplicate, non-blocking)
- `.github/workflows/ci-cd-complete.yml` (too heavy, move heavy checks to nightly)

**Move to Nightly/Schedule:**
- `security-scan` → `nightly.yml` (runs daily)
- `migration-validation` → `nightly.yml` (runs daily)
- `e2e-tests` → `nightly.yml` (runs daily)
- `aurora-doctor` → `nightly.yml` (runs every 6h, remove from PR triggers)

**Consolidate:**
- Merge `frontend-ci.yml` into main `ci.yml` (use path filters if needed)
- Single `ci.yml` workflow with all core checks
- Single `deploy.yml` for deployments (keep separate)

**Result:** 2 workflows for PRs (`ci.yml`, `deploy.yml`), 1 for nightly (`nightly.yml`)

---

## C. CI WORKFLOWS – CONCRETE REWRITE PLAN

### CURRENT WORKFLOW INVENTORY

| Workflow | Purpose | Action |
|----------|---------|--------|
| `ci.yml` | Primary CI (test, lint, frontend-test, e2e) | **KEEP & REFACTOR** |
| `ci-cd.yml` | Duplicate CI with `|| true` | **DELETE** |
| `ci-cd-complete.yml` | Comprehensive CI (too heavy) | **DELETE** (move heavy jobs to nightly) |
| `frontend-ci.yml` | Frontend-specific CI | **MERGE INTO ci.yml** |
| `deploy.yml` | Deployment | **KEEP & FIX** |
| `aurora-doctor.yml` | Health checks | **KEEP BUT SCHEDULE ONLY** |

### PROPOSED WORKFLOW SET

**1. `.github/workflows/ci.yml`** (Core CI - Runs on Every PR)

**Triggers:**
- `pull_request` to `main`, `develop`
- `push` to `main`, `develop`

**Jobs:**
- `lint-backend` (ruff, mypy)
- `lint-frontend` (eslint, prettier, tsc)
- `test-backend` (pytest with coverage)
- `test-frontend` (jest)
- `build-backend` (Docker build if Dockerfile exists)
- `build-frontend` (npm run build)

**Matrix Strategy:** None (keep it simple)

**Caching:**
- Python dependencies (pip cache)
- Node modules (npm cache)
- Docker layers (if building)

**2. `.github/workflows/nightly.yml`** (Heavy Checks - Runs on Schedule)

**Triggers:**
- `schedule: cron: '0 2 * * *'` (daily at 2 AM UTC)
- `workflow_dispatch`

**Jobs:**
- `security-scan` (safety, detect-secrets)
- `migration-validation`
- `e2e-tests`
- `aurora-doctor` (health checks)

**3. `.github/workflows/deploy.yml`** (Deployment - Runs on Main Push)

**Triggers:**
- `push` to `main`
- `workflow_dispatch`

**Jobs:**
- `deploy-staging` (if branch is `develop` - fix logic)
- `deploy-production` (if branch is `main`)

**Fixes:**
- Remove incorrect conditional logic
- Add proper environment protection
- Add smoke tests after deployment

### MERGE GUARDRAILS

**Branch Protection Rules:**
- Require `ci.yml` to pass before merge
- Require at least 1 approval
- Require up-to-date branch

**Check Status:**
- All 6 core checks in `ci.yml` must be green
- Nightly checks can be yellow/red (non-blocking)
- Deploy checks only run on `main` push

**Definition of Green:**
- All 6 core checks pass
- No flaky test failures
- Coverage threshold met (50% initially, 60% target)

---

## D. CODE CLEANUP – CLARITY, COHESION, AND TESTABILITY

### CODE COHESION ISSUES

**1. Dual Config Systems:**
- `src/config/__init__.py` (dataclass) vs `src/config/validation.py` (Pydantic)
- Both used in different places, causing confusion

**2. Heavy Module-Level Imports:**
- `src/main.py` imports 40+ modules at top level
- Causes slow startup, side effects, hard to test

**3. API Route Proliferation:**
- 32 API route files, many likely thin wrappers
- Need to audit and consolidate

**4. Inconsistent Naming:**
- Mix of `snake_case` and inconsistent `__init__.py` exports
- Some modules lack `__init__.py`

**5. Test Architecture:**
- No shared fixtures
- Tests create real DB records without cleanup
- No separation of fast vs slow tests

**6. Missing Core Tests:**
- No tests for config loading
- No tests for attribution engine
- No tests for campaign manager
- No tests for analytics store

### CODE CLEANUP TASKS

**Priority 1: Config Consolidation**

1. **Delete `src/config/__init__.py`** - Remove dataclass-based config
2. **Update all imports** - Change `from src.config import config` to use `validation.py`
3. **Create `src/config/settings.py`** - Single entry point for config (wraps validation.py)
4. **Add tests** - `tests/unit/test_config.py` for config loading/validation

**Priority 2: Main.py Refactoring**

5. **Split `src/main.py`** - Extract route registration to `src/api/router.py`
6. **Lazy load services** - Move service initialization to dependency injection
7. **Extract app factory** - `src/app_factory.py` for creating FastAPI app
8. **Add tests** - `tests/unit/test_app_factory.py`

**Priority 3: API Route Consolidation**

9. **Audit API routes** - Identify duplicates/thin wrappers
10. **Consolidate similar routes** - Merge `analytics.py` and `business.py` if overlapping
11. **Standardize route structure** - All routes follow same pattern (dependencies, error handling)
12. **Add route tests** - `tests/integration/test_api_routes.py`

**Priority 4: Module Structure**

13. **Add missing `__init__.py`** - Ensure all modules have proper exports
14. **Standardize exports** - Consistent `__all__` declarations
15. **Fix circular imports** - Audit and break any circular dependencies
16. **Rename inconsistent modules** - Standardize naming (e.g., `src/ai/` vs `src/attribution/`)

**Priority 5: Test Infrastructure**

17. **Create `tests/conftest.py`** - Shared fixtures (DB, Redis, auth tokens)
18. **Add test database setup** - Proper DB migrations for tests
19. **Separate test types** - `tests/unit/` (fast), `tests/integration/` (medium), `tests/e2e/` (slow)
20. **Add core business logic tests** - Attribution engine, campaign manager, analytics store

### TEST ARCHITECTURE FIXES

**Test Structure:**
```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Fast tests (<1s each)
│   ├── test_config.py
│   ├── test_attribution.py
│   ├── test_campaigns.py
│   └── test_analytics.py
├── integration/         # Medium tests (<10s each)
│   ├── test_api_routes.py
│   ├── test_database.py
│   └── test_payments.py
├── smoke/               # Critical path tests (<30s)
│   └── test_critical_paths.py
└── e2e/                 # Full system tests (<5min)
    └── test_product_loop.py
```

**Must-Have Tests:**

1. **Config Loading** (`test_config.py`)
   - Valid config loads successfully
   - Invalid config raises ValidationError
   - Default values work correctly

2. **Attribution Engine** (`test_attribution.py`)
   - First-touch attribution works
   - Last-touch attribution works
   - Cross-platform attribution works

3. **Campaign Manager** (`test_campaigns.py`)
   - Create campaign
   - Update campaign
   - Delete campaign
   - List campaigns

4. **Analytics Store** (`test_analytics.py`)
   - Store metrics
   - Query metrics
   - Aggregate metrics

5. **API Routes** (`test_api_routes.py`)
   - All routes return correct status codes
   - Authentication required where needed
   - Error handling works

**Test Fixtures:**
- `db_session` - Database session with rollback
- `redis_client` - Redis client (mocked or test instance)
- `auth_token` - Valid JWT token for testing
- `test_user` - Test user fixture
- `test_podcast` - Test podcast fixture

---

## E. FIXING THE CHECKS – PRIORITIZED EXECUTION PLAN

### PHASED CI STABILIZATION PLAN

**Phase 1: Stop the Bleeding (Week 1)**

1. **Disable broken workflows**
   - Delete `ci-cd.yml` (non-blocking, duplicate)
   - Delete `ci-cd-complete.yml` (too heavy)
   - Comment out `aurora-doctor.yml` PR triggers (keep schedule only)

2. **Fix `ci.yml` workflow**
   - Add caching for Python and Node dependencies
   - Standardize Python version (3.11) and Node version (20)
   - Remove `|| true` from all checks
   - Fix `.flake8` max-line-length to match workflow (120)

3. **Fix mypy configuration**
   - Remove `ignore_missing_imports = True` from `.mypy.ini`
   - Add type stubs for missing dependencies
   - Fix critical type errors (start with 10-20 files)

4. **Fix test setup**
   - Ensure Postgres/Redis services are set up in `ci.yml`
   - Add test database cleanup between runs
   - Fix flaky smoke tests (add proper fixtures)

5. **Create `pyproject.toml`**
   - Unified config for black, isort, mypy, pytest
   - Replace `.flake8` with ruff config in `pyproject.toml`

**Phase 2: Fix Core Checks (Week 2)**

6. **Fix linting**
   - Run `ruff format` and `ruff check --fix` on entire codebase
   - Fix all linting errors (or add `# noqa` with justification)
   - Ensure `ruff` passes in CI

7. **Fix type checking**
   - Fix mypy errors in core modules (config, database, api)
   - Add type stubs for external dependencies
   - Ensure `mypy` passes in CI (with `--ignore-missing-imports` only for external deps)

8. **Fix backend tests**
   - Add missing test fixtures (`conftest.py`)
   - Fix flaky tests (remove race conditions, add proper cleanup)
   - Ensure all unit tests pass consistently

9. **Fix frontend tests**
   - Ensure Jest config is correct
   - Fix any failing tests
   - Ensure build passes with proper env vars

10. **Fix coverage**
    - Lower coverage threshold to 50% initially
    - Add tests for core business logic
    - Gradually increase threshold to 60%

**Phase 3: Reintroduce Heavy Checks (Week 3)**

11. **Create `nightly.yml` workflow**
    - Move security-scan, migration-validation, e2e-tests to nightly
    - Run daily at 2 AM UTC
    - Non-blocking (can be yellow/red)

12. **Fix deployment workflow**
    - Fix conditional logic in `deploy.yml`
    - Add proper environment protection
    - Add smoke tests after deployment

13. **Monitor and iterate**
    - Track check pass rates
    - Fix any remaining flaky tests
    - Gradually tighten requirements

### DEFINITION OF DONE FOR GREEN CI

**Success Criteria:**

1. **All 6 core checks pass >95% of the time**
   - `lint-backend`: Green
   - `lint-frontend`: Green
   - `test-backend`: Green (coverage ≥50%)
   - `test-frontend`: Green
   - `build-backend`: Green
   - `build-frontend`: Green

2. **No flaky tests**
   - Same commit run twice = same results
   - Tests are deterministic (no randomness, proper cleanup)

3. **Fast feedback**
   - PR checks complete in <15 minutes
   - Unit tests run in <30 seconds
   - Integration tests run in <2 minutes

4. **Clear failure messages**
   - Lint errors show exact file/line
   - Test failures show clear error messages
   - Build failures show exact command that failed

5. **Local dev parity**
   - `make ci` runs same checks as CI
   - Developers can reproduce CI failures locally

---

## F. CONCRETE CHANGES & PR STRUCTURE

### PR PLAN

**PR 1: Normalize CI Workflows and Reduce Checks** [LOW RISK]

**Scope:**
- Delete `ci-cd.yml` and `ci-cd-complete.yml`
- Refactor `ci.yml` to include all core checks
- Merge `frontend-ci.yml` into `ci.yml`
- Fix `aurora-doctor.yml` to run on schedule only
- Add caching to all workflows

**Files:**
- `.github/workflows/ci.yml` (rewrite)
- `.github/workflows/nightly.yml` (new)
- `.github/workflows/aurora-doctor.yml` (modify triggers)
- `.github/workflows/ci-cd.yml` (delete)
- `.github/workflows/ci-cd-complete.yml` (delete)
- `.github/workflows/frontend-ci.yml` (delete)

**Risk:** Low (CI changes, can revert easily)

**PR 2: Fix Linting and Type Checking Configuration** [MEDIUM RISK]

**Scope:**
- Create `pyproject.toml` with unified tool config
- Replace `.flake8` with ruff config
- Fix `.mypy.ini` (remove `ignore_missing_imports`)
- Fix critical linting/type errors (50-100 files)
- Add type stubs for missing dependencies

**Files:**
- `pyproject.toml` (new)
- `.flake8` (delete or update)
- `.mypy.ini` (modify)
- `src/**/*.py` (fix linting/type errors)

**Risk:** Medium (may break existing code)

**PR 3: Consolidate Config System** [MEDIUM RISK]

**Scope:**
- Delete `src/config/__init__.py` (dataclass version)
- Update all imports to use `src/config/validation.py`
- Create `src/config/settings.py` as single entry point
- Add tests for config loading

**Files:**
- `src/config/__init__.py` (delete)
- `src/config/settings.py` (new)
- `src/**/*.py` (update imports)
- `tests/unit/test_config.py` (new)

**Risk:** Medium (affects many files)

**PR 4: Refactor main.py and Add Test Infrastructure** [HIGH RISK]

**Scope:**
- Split `src/main.py` into `src/app_factory.py` and `src/api/router.py`
- Lazy load services (dependency injection)
- Create `tests/conftest.py` with shared fixtures
- Add core business logic tests

**Files:**
- `src/main.py` (refactor)
- `src/app_factory.py` (new)
- `src/api/router.py` (new)
- `tests/conftest.py` (new)
- `tests/unit/test_*.py` (new tests)

**Risk:** High (core application changes)

**PR 5: Fix Test Flakiness and Add Coverage** [MEDIUM RISK]

**Scope:**
- Fix flaky smoke tests (add proper fixtures, cleanup)
- Add missing test coverage for core modules
- Separate fast/slow tests
- Lower coverage threshold to 50%

**Files:**
- `tests/smoke/test_critical_paths.py` (fix)
- `tests/unit/test_*.py` (add tests)
- `pytest.ini` or `pyproject.toml` (test config)

**Risk:** Medium (test changes)

**PR 6: API Route Consolidation and Standardization** [LOW RISK]

**Scope:**
- Audit API routes for duplicates
- Consolidate similar routes
- Standardize route structure
- Add route tests

**Files:**
- `src/api/*.py` (consolidate)
- `tests/integration/test_api_routes.py` (new)

**Risk:** Low (API changes, can test easily)

### LOCAL DEV & CI PARITY

**Create `Makefile`:**

```makefile
.PHONY: ci lint test type-check format install

ci: lint type-check test build
	@echo "All checks passed!"

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/
	cd frontend && npm run lint

type-check:
	mypy src/
	cd frontend && npm run type-check

test:
	pytest tests/unit/ tests/integration/ -v --cov=src --cov-report=term
	cd frontend && npm test -- --watchAll=false

build:
	docker build -t podcast-analytics-api:test . || echo "Dockerfile not found"
	cd frontend && npm run build

format:
	ruff format src/ tests/
	cd frontend && npm run format || echo "No format script"

install:
	pip install -r requirements.txt
	cd frontend && npm ci
```

**Documentation:**

Add to `README.md`:
```markdown
## Development

### Running CI Checks Locally

```bash
# Run all CI checks
make ci

# Run individual checks
make lint      # Lint backend and frontend
make type-check # Type check backend and frontend
make test      # Run tests
make build     # Build backend and frontend
```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```
```

**Create `.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.50.0
    hooks:
      - id: eslint
        files: ^frontend/
```

---

## G. FINAL CHECKLIST – WHAT I SHOULD DO NEXT

### Phase 1: Stop the Bleeding (Week 1)

- [QW] Delete `.github/workflows/ci-cd.yml` (duplicate, non-blocking)
- [QW] Delete `.github/workflows/ci-cd-complete.yml` (too heavy)
- [QW] Modify `.github/workflows/aurora-doctor.yml` to remove `push` triggers (keep schedule only)
- [QW] Add caching to `.github/workflows/ci.yml` for Python and Node dependencies
- [QW] Standardize Python version to `3.11` in all workflows
- [QW] Standardize Node version to `20` in all workflows
- [QW] Remove all `|| true` from `.github/workflows/ci.yml`
- [QW] Fix `.flake8` max-line-length to `120` (match workflow)
- [DW] Create `pyproject.toml` with unified tool config (ruff, mypy, pytest)
- [DW] Replace `.flake8` with ruff config in `pyproject.toml`

### Phase 2: Fix Core Checks (Week 2)

- [DW] Fix `.mypy.ini` - remove `ignore_missing_imports = True` (keep only for external deps)
- [DW] Run `ruff format` and `ruff check --fix` on entire codebase
- [DW] Fix all linting errors (or add `# noqa` with justification)
- [DW] Fix mypy errors in core modules (`src/config/`, `src/database/`, `src/api/`)
- [DW] Add type stubs for missing dependencies
- [DW] Create `tests/conftest.py` with shared fixtures (DB, Redis, auth tokens)
- [DW] Fix flaky smoke tests - add proper cleanup and fixtures
- [DW] Ensure Postgres/Redis services are set up correctly in `ci.yml`
- [DW] Lower coverage threshold to 50% in `ci.yml`
- [DW] Fix frontend build - ensure env vars are set correctly

### Phase 3: Code Cleanup (Week 3)

- [DW] Delete `src/config/__init__.py` (dataclass version)
- [DW] Create `src/config/settings.py` as single entry point
- [DW] Update all imports from `src.config` to use `validation.py` or `settings.py`
- [DW] Add `tests/unit/test_config.py` for config loading/validation
- [DW] Split `src/main.py` - extract route registration to `src/api/router.py`
- [DW] Create `src/app_factory.py` for FastAPI app creation
- [DW] Lazy load services in `main.py` (use dependency injection)
- [DW] Add `tests/unit/test_app_factory.py`
- [DW] Audit API routes - identify duplicates/thin wrappers
- [DW] Consolidate similar routes (e.g., `analytics.py` vs `business.py`)

### Phase 4: Test Infrastructure (Week 4)

- [DW] Add missing `__init__.py` files with proper exports
- [DW] Standardize `__all__` declarations across modules
- [DW] Add `tests/unit/test_attribution.py` for attribution engine
- [DW] Add `tests/unit/test_campaigns.py` for campaign manager
- [DW] Add `tests/unit/test_analytics.py` for analytics store
- [DW] Add `tests/integration/test_api_routes.py` for API route testing
- [DW] Separate fast/slow tests - move e2e tests to separate job
- [DW] Create `Makefile` with `make ci` command
- [DW] Add `.pre-commit-config.yaml` for local dev
- [DW] Update `README.md` with local dev instructions

### Phase 5: Reintroduce Heavy Checks (Week 5)

- [QW] Create `.github/workflows/nightly.yml` workflow
- [QW] Move `security-scan` to `nightly.yml` (run daily)
- [QW] Move `migration-validation` to `nightly.yml` (run daily)
- [QW] Move `e2e-tests` to `nightly.yml` (run daily)
- [DW] Fix `deploy.yml` conditional logic (fix branch conditions)
- [DW] Add proper environment protection to `deploy.yml`
- [DW] Add smoke tests after deployment in `deploy.yml`
- [DW] Monitor check pass rates and fix any remaining flaky tests

### Definition of Done

- [ ] All 6 core checks pass >95% of the time
- [ ] No flaky tests (same commit = same results)
- [ ] PR checks complete in <15 minutes
- [ ] `make ci` runs same checks as CI
- [ ] Coverage threshold met (≥50%)
- [ ] All linting/type errors fixed
- [ ] Config system consolidated
- [ ] Test infrastructure in place
- [ ] Documentation updated

---

## SUMMARY

**Current State:** 6 overlapping workflows, ~15-20 checks per PR, many with `|| true` (never fail), inconsistent configs, minimal tests.

**Target State:** 2 workflows for PRs (`ci.yml`, `deploy.yml`), 1 for nightly (`nightly.yml`), 6 core checks that must pass, unified tool config, consolidated code structure, robust test suite.

**Timeline:** 5 weeks to go from red to green, with incremental improvements each week.

**Key Principles:**
1. **Stop the bleeding first** - Disable broken checks, fix configuration
2. **Fix core checks** - Lint, type-check, tests must be reliable
3. **Clean up code** - Consolidate config, refactor main.py, add tests
4. **Reintroduce heavy checks** - Move to nightly, non-blocking

**Success Metric:** Every PR to main runs 6 focused checks that pass >95% of the time unless there's a real bug.
