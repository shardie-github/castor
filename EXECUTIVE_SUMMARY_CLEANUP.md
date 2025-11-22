# Executive Summary: CI & Code Cleanup Plan

## Problem Statement

**Current State:**
- 6 overlapping GitHub workflows running ~15-20 checks per PR
- Many checks use `|| true` (never fail, creating false sense of security)
- Inconsistent tool configurations (flake8 vs ruff, mypy ignoring imports)
- Minimal test coverage (only 3 unit test files for entire codebase)
- Dual config systems causing confusion
- Heavy module-level imports slowing startup
- Flaky tests due to missing fixtures and cleanup

**Impact:**
- Every PR shows many failing checks
- Developers can't tell which checks matter
- CI is unreliable and slow
- Code quality is inconsistent
- Hard to maintain and extend

## Solution Overview

**Target State:**
- 2 workflows for PRs (`ci.yml`, `deploy.yml`), 1 for nightly (`nightly.yml`)
- 6 core checks that must pass (lint-backend, lint-frontend, test-backend, test-frontend, build-backend, build-frontend)
- Unified tool configuration (`pyproject.toml`)
- Consolidated code structure (single config system, refactored main.py)
- Robust test infrastructure (shared fixtures, proper cleanup)
- Fast feedback (<15 min PR checks)

## Implementation Plan

### Phase 1: Stop the Bleeding (Week 1)
- Delete duplicate workflows (`ci-cd.yml`, `ci-cd-complete.yml`)
- Consolidate into single `ci.yml` workflow
- Add caching and fix configurations
- Remove `|| true` from all checks

### Phase 2: Fix Core Checks (Week 2)
- Fix linting (ruff replaces flake8/black/isort)
- Fix type checking (proper mypy config)
- Fix tests (add fixtures, fix flakiness)
- Lower coverage threshold to 50%

### Phase 3: Code Cleanup (Week 3)
- Consolidate config system (remove dual configs)
- Refactor main.py (split into app_factory + router)
- Consolidate API routes
- Standardize module structure

### Phase 4: Test Infrastructure (Week 4)
- Add shared test fixtures (`conftest.py`)
- Add core business logic tests
- Separate fast/slow tests
- Create `Makefile` for local dev

### Phase 5: Reintroduce Heavy Checks (Week 5)
- Move heavy checks to `nightly.yml` (security, migrations, e2e)
- Fix deployment workflow
- Monitor and iterate

## Success Metrics

**Definition of Done:**
- ✅ All 6 core checks pass >95% of the time
- ✅ No flaky tests (same commit = same results)
- ✅ PR checks complete in <15 minutes
- ✅ `make ci` runs same checks as CI
- ✅ Coverage threshold met (≥50%)

## Risk Assessment

| Phase | Risk Level | Mitigation |
|-------|-----------|------------|
| Phase 1 (CI Changes) | Low | Can revert easily, workflows are versioned |
| Phase 2 (Linting/Type) | Medium | Fix incrementally, start with core modules |
| Phase 3 (Config Refactor) | Medium | Update imports systematically, add tests |
| Phase 4 (Main.py Refactor) | High | Test thoroughly, use feature flags if needed |
| Phase 5 (Heavy Checks) | Low | Non-blocking, can disable if needed |

## Timeline

**Total Duration:** 5 weeks

**Week 1:** Stop bleeding (CI workflow consolidation)
**Week 2:** Fix core checks (lint, type, tests)
**Week 3:** Code cleanup (config, main.py, routes)
**Week 4:** Test infrastructure (fixtures, coverage)
**Week 5:** Heavy checks (nightly, deployment)

## Key Deliverables

1. **New CI Workflow** (`.github/workflows/ci.yml`)
   - 6 core checks that must pass
   - Proper caching and error handling
   - Fast feedback (<15 min)

2. **Unified Tool Config** (`pyproject.toml`)
   - Ruff for linting/formatting
   - Mypy for type checking
   - Pytest for testing

3. **Local Dev Experience** (`Makefile`)
   - `make ci` runs same checks as CI
   - Pre-commit hooks for quality

4. **Code Improvements**
   - Consolidated config system
   - Refactored main.py
   - Better test infrastructure

## Next Steps

1. **Review** this plan and the detailed document (`CI_AND_CODE_CLEANUP_PLAN.md`)
2. **Start with Phase 1** - implement new CI workflows
3. **Test locally** using `make ci`
4. **Iterate** - fix issues as they arise
5. **Monitor** - track check pass rates and improve

## Files Created

- `CI_AND_CODE_CLEANUP_PLAN.md` - Comprehensive plan (all sections A-G)
- `QUICK_START_CLEANUP.md` - Quick reference guide
- `.github/workflows/ci.yml.new` - New CI workflow
- `.github/workflows/nightly.yml.new` - Nightly checks workflow
- `pyproject.toml.new` - Unified tool configuration
- `Makefile.new` - Local dev commands
- `.pre-commit-config.yaml.new` - Pre-commit hooks

## Questions?

Refer to:
- **Full Plan:** `CI_AND_CODE_CLEANUP_PLAN.md`
- **Quick Start:** `QUICK_START_CLEANUP.md`
- **Workflow Files:** `.github/workflows/*.new`
- **Config Files:** `*.new`

---

**Remember:** The goal is to go from "25 failed checks every commit" to "6 focused checks that almost always pass unless there's a real bug."
