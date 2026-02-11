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

## LiveKit Voice Agent Worker

The voice agent worker handles real-time voice interactions with users through LiveKit.

### Prerequisites

- LiveKit server credentials (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
- Deepgram API key for Speech-to-Text
- Cartesia API key for Text-to-Speech
- LLM API key (OpenAI, Anthropic, or Google)

### Configuration

Add these to your `.env` file:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_WORKER_NUM_IDLE=2

# Voice Service Configuration
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key
VOICE_LLM_PROVIDER=openai  # or anthropic, google
VOICE_CONTEXT_CACHE_TTL=3600
VOICE_MAX_RESPONSE_TOKENS=150
```

### Running the Worker

**Development Mode (with hot-reload):**
```bash
# Windows
app\livekit_agents\start_worker.bat

# Linux/Mac
poetry run python app/livekit_agents/voice_agent_worker.py dev
```

**Production Mode:**
```bash
poetry run python app/livekit_agents/voice_agent_worker.py start
```

### Verify Worker Status

When the worker starts successfully, you should see:
```
INFO … livekit.agents     starting worker
INFO … livekit.agents     registered worker
```

The worker will:
- Connect to your LiveKit server
- Register as available for voice sessions
- Listen for room connections
- Handle voice interactions with pre-loaded user context

### Troubleshooting

**Missing LIVEKIT_URL error:**
- Ensure `.env` file exists in backend directory
- Verify LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET are set

**Import errors:**
- Run from backend directory: `cd backend`
- Use Poetry: `poetry run python app/livekit_agents/voice_agent_worker.py dev`

**Connection errors:**
- Verify LiveKit credentials are correct
- Check network connectivity to LiveKit server
- Ensure firewall allows WebSocket connections

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
