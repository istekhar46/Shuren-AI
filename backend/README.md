# Shuren Backend

FastAPI backend for the Shuren AI fitness application.

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (Python package manager)
- PostgreSQL database

### Setup

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Configure environment:**
   ```bash
   # Copy example config
   cp .env.example .env
   
   # Edit .env and set:
   # - DATABASE_URL (your PostgreSQL connection)
   # - JWT_SECRET_KEY (generate a secure key)
   # - LLM API keys (Anthropic/OpenAI/Google)
   ```

3. **Run database migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

4. **Start the server:**
   ```bash
   # Windows
   run_local.bat
   
   # Linux/Mac
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc

## Database Management

### Reset Database (Drop all tables)
```bash
poetry run python scripts/reset_db.py
poetry run alembic upgrade head
```

### Check Database Status
```bash
poetry run python scripts/check_db.py
```

### Create New Migration
```bash
poetry run alembic revision --autogenerate -m "description"
poetry run alembic upgrade head
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # REST API endpoints
│   ├── agents/              # AI agent implementations
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic layer
│   ├── core/                # Security, config, utilities
│   └── db/                  # Database session management
├── alembic/                 # Database migrations
├── tests/                   # Test suite
└── run_local.bat           # Windows startup script
```

## Common Issues

### Database Connection Error
- Verify DATABASE_URL in .env is correct
- Ensure PostgreSQL is running
- For cloud databases (Aiven, etc.), asyncpg handles SSL automatically

### Migration Conflicts
- If migrations are out of sync, use `reset_db.py` to start fresh
- Always run `alembic upgrade head` after resetting

### Import Errors
- Make sure you're using Poetry: `poetry run <command>`
- Or activate the shell: `poetry shell`
