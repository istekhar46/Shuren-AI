---
inclusion: always
---

# Poetry Usage Guide

This project uses **Poetry** for Python dependency management and virtual environment handling.

## Why Poetry?

- **Dependency Resolution**: Automatically resolves and locks dependencies
- **Virtual Environment**: Manages isolated Python environments
- **Reproducible Builds**: `poetry.lock` ensures consistent installations
- **Dev Dependencies**: Separate production and development dependencies

## Key Commands

### Installation & Setup

```bash
# Install Poetry (if not installed)
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Install without dev dependencies (production)
poetry install --without dev

# Activate virtual environment
poetry shell
```

### Running Commands

**IMPORTANT**: Always prefix commands with `poetry run` or activate the shell first.

```bash
# Option 1: Use poetry run
poetry run pytest
poetry run uvicorn app.main:app --reload
poetry run alembic upgrade head

# Option 2: Activate shell first
poetry shell
pytest
uvicorn app.main:app --reload
alembic upgrade head
```

### Dependency Management

```bash
# Add production dependency
poetry add fastapi

# Add dev dependency
poetry add --group dev pytest

# Update all dependencies
poetry update

# Update specific package
poetry update sqlalchemy

# Show installed packages
poetry show

# Show dependency tree
poetry show --tree
```

### Common Development Commands

```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Start development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "description"
```

## Project Configuration

Dependencies are defined in `pyproject.toml`:

```toml
[project]
dependencies = [
    "fastapi (>=0.128.0,<0.129.0)",
    "sqlalchemy (>=2.0.46,<3.0.0)",
    # ... other production dependencies
]

[dependency-groups]
dev = [
    "pytest (>=9.0.2,<10.0.0)",
    "pytest-asyncio (>=1.3.0,<2.0.0)",
    # ... other dev dependencies
]
```

## Important Notes

1. **Always use `poetry run`** when executing commands outside the Poetry shell
2. **Never use `pip install`** directly - use `poetry add` instead
3. **Commit `poetry.lock`** to version control for reproducible builds
4. **Don't commit `.venv/`** directory (it's in `.gitignore`)

## Troubleshooting

```bash
# Recreate virtual environment
poetry env remove python
poetry install

# Clear cache
poetry cache clear pypi --all

# Show virtual environment path
poetry env info --path

# List all virtual environments
poetry env list
```

## Agent Instructions

When implementing tasks:
- Use `poetry run` prefix for all Python commands
- Add new dependencies with `poetry add` (not pip)
- Run tests with `poetry run pytest`
- Start servers with `poetry run uvicorn` or `poetry run gunicorn`
- Execute migrations with `poetry run alembic`
