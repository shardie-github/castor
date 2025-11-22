# Quick Start: CI & Code Cleanup

This guide provides a quick reference for implementing the CI and code cleanup plan.

## 🚀 Phase 1: Stop the Bleeding (Do This First)

### Step 1: Replace CI Workflows

```bash
# Backup old workflows
mkdir -p .github/workflows/backup
mv .github/workflows/ci-cd.yml .github/workflows/backup/
mv .github/workflows/ci-cd-complete.yml .github/workflows/backup/
mv .github/workflows/frontend-ci.yml .github/workflows/backup/

# Use new workflows
cp .github/workflows/ci.yml.new .github/workflows/ci.yml
cp .github/workflows/nightly.yml.new .github/workflows/nightly.yml

# Fix aurora-doctor.yml (remove push triggers)
# Edit .github/workflows/aurora-doctor.yml and remove:
#   push:
#     branches: [ main, develop ]
```

### Step 2: Add Unified Config

```bash
# Add pyproject.toml
cp pyproject.toml.new pyproject.toml

# Update .flake8 to match (or delete it)
# Update .mypy.ini to remove ignore_missing_imports = True
```

### Step 3: Install Ruff (Replaces flake8 + black + isort)

```bash
pip install ruff
```

### Step 4: Test Locally

```bash
# Install make dependencies
pip install -r requirements.txt

# Copy Makefile
cp Makefile.new Makefile

# Run CI checks locally
make ci
```

## 🔧 Phase 2: Fix Core Checks

### Step 1: Fix Linting

```bash
# Auto-fix what can be fixed
ruff format src/ tests/
ruff check --fix src/ tests/

# Review remaining issues
ruff check src/ tests/
```

### Step 2: Fix Type Checking

```bash
# Run mypy
mypy src/ --config-file pyproject.toml

# Fix errors one module at a time
# Start with: src/config/, src/database/, src/api/
```

### Step 3: Fix Tests

```bash
# Run tests
pytest tests/ -v

# Fix flaky tests (add proper fixtures, cleanup)
# See tests/conftest.py for examples
```

## 📋 Phase 3: Code Cleanup

### Step 1: Consolidate Config

```bash
# 1. Create src/config/settings.py (single entry point)
# 2. Update all imports from src.config to use settings.py
# 3. Delete src/config/__init__.py (dataclass version)
# 4. Add tests: tests/unit/test_config.py
```

### Step 2: Refactor main.py

```bash
# 1. Create src/app_factory.py (app creation)
# 2. Create src/api/router.py (route registration)
# 3. Refactor src/main.py to use app_factory
# 4. Add tests: tests/unit/test_app_factory.py
```

### Step 4: Add Test Infrastructure

```bash
# 1. Create tests/conftest.py with shared fixtures
# 2. Add core business logic tests
# 3. Separate fast/slow tests
```

## ✅ Verification Checklist

After each phase, verify:

- [ ] `make ci` runs successfully locally
- [ ] All 6 core checks pass in GitHub Actions
- [ ] No `|| true` in workflows (checks actually fail on errors)
- [ ] Tests are deterministic (run twice = same results)
- [ ] Coverage threshold met (≥50%)

## 🎯 Success Criteria

**You're done when:**
1. All 6 core checks pass >95% of the time
2. PR checks complete in <15 minutes
3. `make ci` runs same checks as CI
4. No flaky tests
5. Code is cleaner and more maintainable

## 📚 Reference Files

- **Full Plan:** `CI_AND_CODE_CLEANUP_PLAN.md`
- **New Workflows:** `.github/workflows/*.new`
- **New Config:** `pyproject.toml.new`
- **Makefile:** `Makefile.new`
- **Pre-commit:** `.pre-commit-config.yaml.new`

## 🆘 Troubleshooting

### "Ruff not found"
```bash
pip install ruff
```

### "Mypy errors on external deps"
Check `pyproject.toml` - external deps should be in `[[tool.mypy.overrides]]`

### "Tests fail in CI but pass locally"
- Check environment variables (DATABASE_URL, REDIS_URL, etc.)
- Ensure services (Postgres, Redis) are set up in workflow
- Check for race conditions or missing cleanup

### "Coverage too low"
- Lower threshold temporarily: `--cov-fail-under=40`
- Add tests for core business logic
- Gradually increase threshold

## 🔄 Next Steps

1. **Week 1:** Implement Phase 1 (stop bleeding)
2. **Week 2:** Implement Phase 2 (fix core checks)
3. **Week 3:** Implement Phase 3 (code cleanup)
4. **Week 4:** Add test infrastructure
5. **Week 5:** Reintroduce heavy checks (nightly)

---

**Remember:** Incremental progress is better than perfect. Get CI green first, then improve code quality.
