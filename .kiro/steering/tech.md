# Technical Stack

## Backend

**Framework**: FastAPI 0.109+ (Python 3.11+)
- Async-first architecture for handling concurrent agent interactions
- Automatic OpenAPI/Swagger documentation
- Pydantic validation for type-safe data models

**Package Manager**: Poetry
- Dependency management and virtual environment handling
- Lock file for reproducible builds
- Separate dev and production dependencies

**ASGI Server**: Uvicorn with Gunicorn workers

**Key Libraries**:
- `sqlalchemy 2.0+`: ORM with async support
- `alembic`: Database migrations
- `pydantic 2.0+`: Data validation
- `asyncpg`: Async PostgreSQL driver
- `redis[hiredis]`: Async Redis client
- `celery`: Background tasks and scheduling
- `python-jose[cryptography]`: JWT authentication

## Database

**Primary Database**: PostgreSQL 15+
- JSONB support for flexible preference storage
- Strong ACID compliance
- Row-Level Security (RLS) for data isolation
- Async operations via asyncpg

**Caching**: Redis 7.0+
- Session state management
- User profile caching (24h TTL)
- Cache invalidation on profile updates

## Real-Time Communication

**LiveKit**: Voice and text agent interactions
- WebRTC infrastructure for low-latency voice
- Built-in agent framework for AI orchestration
- Supports both voice and text modalities

**AI/LLM**:
- Anthropic Claude (primary LLM)
- OpenAI (for LiveKit voice features)
- Deepgram (Speech-to-Text)
- Cartesia (Text-to-Speech)

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings (Pydantic)
│   ├── api/v1/endpoints/    # REST endpoints
│   ├── agents/              # 6 specialized AI agents
│   ├── livekit_agents/      # LiveKit integration
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── core/                # Security, cache, events
│   └── db/                  # Database session, migrations
├── tests/
├── alembic/                 # Database migrations
├── pyproject.toml           # Poetry configuration
└── poetry.lock              # Locked dependencies
```

## Common Commands

### Poetry Package Management
```bash
# Install all dependencies (including dev)
poetry install

# Install only production dependencies
poetry install --without dev

# Add a new dependency
poetry add package-name

# Add a dev dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Activate virtual environment
poetry shell

# Run command in Poetry environment
poetry run <command>
```

### Development
```bash
# Start development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with multiple workers (production)
poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Start Celery worker (background tasks)
poetry run celery -A app.core.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
poetry run celery -A app.core.celery_app beat --loglevel=info
```

### Database
```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_onboarding.py
```

### Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Rebuild after code changes
docker-compose up -d --build

# Stop all services
docker-compose down
```

## Environment Configuration

Configuration managed via Pydantic `BaseSettings` in `app/config.py`:
- Database URL (PostgreSQL)
- Redis URL
- LiveKit credentials (URL, API key, API secret)
- AI API keys (Anthropic, OpenAI, Deepgram, Cartesia)
- JWT secret and algorithm
- Push notification credentials (FCM)
- S3/storage credentials

All settings loaded from `.env` file or environment variables.

## Performance Targets

- User profile query: < 50ms
- Onboarding state load: < 30ms
- Complete AI context load: < 100ms
- Save onboarding step: < 200ms

## Deployment

- Docker Compose for local/staging
- Production options: AWS ECS Fargate, DigitalOcean, Hetzner
- PostgreSQL managed service recommended
- Redis managed service or self-hosted
- LiveKit can be self-hosted or cloud-hosted
