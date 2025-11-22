# Contributing Guide

**Welcome!** We're thrilled you're interested in contributing. This guide will help you get started, whether you're fixing a bug, adding a feature, or improving documentation.

**Who This Is For**: Developers, designers, technical writers, and anyone who wants to make this platform better. No contribution is too small.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd podcast-analytics-platform
   ```

2. **Set up backend**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   
   # Run migrations
   python scripts/run_migrations.py
   
   # Start development server
   uvicorn src.main:app --reload
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches
- `docs/*`: Documentation branches

### Code Style

#### Python

- Follow PEP 8
- Use Black for formatting
- Use type hints
- Maximum line length: 120 characters

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type check
mypy src/
```

#### TypeScript/JavaScript

- Follow ESLint rules
- Use Prettier for formatting
- Use TypeScript for type safety

```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

### Testing

#### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_example.py
```

#### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

#### Integration Tests

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/

# Cleanup
docker-compose -f docker-compose.test.yml down
```

### Database Migrations

1. **Create a migration**
   ```bash
   python scripts/create_migration.py --name add_new_table
   ```

2. **Validate migration**
   ```bash
   python scripts/validate_migrations.py
   ```

3. **Run migrations**
   ```bash
   python scripts/run_migrations.py
   ```

4. **Rollback migration**
   ```bash
   python scripts/rollback_migration.py --migration 001
   ```

### Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Build process or auxiliary tool changes

Example:
```
feat: Add user authentication endpoint

- Implement JWT-based authentication
- Add login/logout endpoints
- Add password hashing
```

### Pull Request Process

1. **Create a branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: Add new feature"
   ```

3. **Push and create PR**
   ```bash
   git push origin feature/my-feature
   ```

4. **PR Requirements**
   - All tests must pass
   - Code must be linted and formatted
   - Documentation updated if needed
   - Migration validation passes
   - At least one reviewer approval

### Code Review Guidelines

- Be respectful and constructive
- Focus on code, not the person
- Explain reasoning for suggestions
- Approve when satisfied
- Request changes if needed

## Project Structure

```
/
├── src/              # Backend source code
├── frontend/         # Frontend source code
├── migrations/       # Database migrations
├── tests/            # Test files
├── scripts/          # Utility scripts
├── docs/              # Documentation
└── docker-compose.yml # Docker configuration
```

## Adding New Features

### Backend API

1. Create route handler in `src/api/`
2. Add business logic in appropriate module
3. Add database models if needed
4. Write tests
5. Update API documentation

### Frontend Component

1. Create component in `frontend/components/`
2. Add to appropriate page
3. Write tests
4. Update Storybook (if applicable)

### Database Changes

1. Create migration
2. Update schema documentation
3. Test migration up and down
4. Update ORM models if needed

## Debugging

### Backend

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with debugger
python -m pdb src/main.py
```

### Frontend

```bash
# Enable React DevTools
# Install browser extension

# Debug in browser
# Use browser DevTools
```

### Database

```bash
# Connect to database
psql -h localhost -U postgres -d podcast_analytics

# View logs
docker-compose logs postgres
```

## Documentation

- **API Documentation**: Update `docs/API_DOCUMENTATION.md`
- **Architecture**: Update `docs/ARCHITECTURE.md`
- **README**: Update `README.md` for user-facing changes
- **Code Comments**: Add docstrings to functions/classes

## Getting Help

Stuck? We've got your back:

- **GitHub Issues**: Found a bug or have a feature idea? [Open an issue](https://github.com/yourusername/podcast-analytics-platform/issues)
- **GitHub Discussions**: Want to discuss an idea before coding? [Start a discussion](https://github.com/yourusername/podcast-analytics-platform/discussions)
- **Questions**: Not sure where something goes? Ask! We're here to help.

## Your First Contribution

New to open source? Here's how to make your first contribution:

1. **Find something to work on**: Look for issues labeled `good first issue` or `help wanted`
2. **Fork the repo**: Click the "Fork" button at the top
3. **Make your changes**: Follow the development workflow above
4. **Submit a PR**: We'll review it and help you get it merged

Don't worry about making mistakes—we all started somewhere. The important thing is that you're contributing.

## Code of Conduct

Be respectful, be kind, be constructive. We're all here to build something great together.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing!** Every contribution makes this platform better. 🎉
