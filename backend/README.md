# Shuren Backend

FastAPI backend for the Shuren AI fitness application.

## Features

### Chat-Based Onboarding
- **Conversational Flow**: Users complete onboarding through natural chat interactions with specialized AI agents
- **9-State System**: Streamlined onboarding process (reduced from 11 steps to 9 states)
- **Agent Routing**: Automatic routing to appropriate specialized agents based on onboarding state
- **Progress Tracking**: Rich progress metadata for UI indicators with completion percentage
- **Incremental Persistence**: Progress saved after each state, allowing users to resume anytime

### State Consolidation (11 → 9)
The onboarding flow has been optimized from 11 steps to 9 states:
- **State 1**: Fitness Level Assessment (Workout Planning Agent)
- **State 2**: Primary Fitness Goals (Workout Planning Agent)
- **State 3**: Workout Preferences & Constraints - *merged from old steps 4 & 5* (Workout Planning Agent)
- **State 4**: Diet Preferences & Restrictions (Diet Planning Agent)
- **State 5**: Fixed Meal Plan Selection (Diet Planning Agent)
- **State 6**: Meal Timing Schedule (Scheduling & Reminder Agent)
- **State 7**: Workout Schedule (Scheduling & Reminder Agent)
- **State 8**: Hydration Schedule (Scheduling & Reminder Agent)
- **State 9**: Supplement Preferences - *optional* (Supplement Guidance Agent)

### Agent Function Tools
Specialized agents can save onboarding data via function tools:
- **Workout Planning Agent**: `save_fitness_level()`, `save_fitness_goals()`, `save_workout_constraints()`
- **Diet Planning Agent**: `save_dietary_preferences()`, `save_meal_plan()`
- **Scheduling Agent**: `save_meal_schedule()`, `save_workout_schedule()`, `save_hydration_schedule()`
- **Supplement Agent**: `save_supplement_preferences()`

All tools internally call the REST API with validation, maintaining a single source of truth.

### Access Control & Feature Locking
- **Pre-Onboarding**: Only chat onboarding endpoint accessible, all other features locked
- **Post-Onboarding**: All features unlocked, only general agent accessible
- **Dynamic Access Control**: `/api/v1/users/me` endpoint provides access control flags for UI

### Agent Routing & Observability
- **Onboarding Mode**: Specialized agents during onboarding, general agent post-onboarding
- **Agent Context Logging**: All agent operations logged with context for debugging and analytics
- **Routing History**: Agent routing history tracked in database for each state transition

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

## API Endpoints

### New Endpoints (v1.0.0)

**Onboarding Progress**
```bash
GET /api/v1/onboarding/progress
```
Returns rich progress metadata including current state, completed states, state metadata, and completion percentage.

**Onboarding Chat**
```bash
POST /api/v1/chat/onboarding
```
Handle chat-based onboarding with automatic agent routing. Agents can save data via function tools, advancing the state automatically.

### Modified Endpoints (v1.0.0)

**Get Current User**
```bash
GET /api/v1/users/me
```
Now includes `access_control` object with feature lock flags and onboarding progress.

**Save Onboarding Step**
```bash
POST /api/v1/onboarding/step
```
Now supports 9 states (was 11) and accepts optional `X-Agent-Context` header for agent logging.

**Chat**
```bash
POST /api/v1/chat
```
Enforces access control: requires completed onboarding, forces general agent only.

### Complete API Documentation

See [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for:
- Detailed endpoint descriptions
- Request/response examples
- Validation rules for each state
- Error codes and handling
- State-to-agent mapping

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

### Onboarding State Migration

The database schema has been updated to support the new 9-state onboarding system:

**Changes:**
- Added `agent_history` JSONB column to track agent routing
- Updated constraint from `current_step <= 11` to `current_step <= 9`
- Data migration script consolidates 11 steps → 9 states
- Original data preserved in `_migration_metadata` for rollback

**Run Migration:**
```bash
poetry run alembic upgrade head
```

**Rollback Migration:**
```bash
poetry run alembic downgrade -1
```

The migration automatically:
- Remaps existing step data to new state numbers
- Merges old steps 4 & 5 into new state 3
- Preserves original data for rollback capability
- Updates current_step values accordingly

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

# Run property-based tests only
poetry run pytest -m property

# Run integration tests only
poetry run pytest -m integration

# Run specific test file
poetry run pytest tests/test_onboarding_chat_integration.py
```

### Test Coverage

The backend includes comprehensive test coverage:
- **Unit Tests**: Individual component testing with specific examples
- **Property-Based Tests**: Universal properties tested across all inputs using Hypothesis
- **Integration Tests**: End-to-end flow testing across multiple components

**Key Test Areas:**
- Onboarding state consolidation and validation
- Agent routing based on onboarding state
- Access control enforcement
- Progress calculation and tracking
- Agent function tool invocation
- Data migration integrity

**Coverage Target:** 80%+ for core business logic

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # REST API endpoints
│   │   ├── onboarding.py    # Onboarding endpoints (progress, state, step, complete)
│   │   ├── chat.py          # Chat endpoints (chat, onboarding chat, stream, history)
│   │   ├── auth.py          # Authentication endpoints (register, login, users/me)
│   │   └── ...              # Other endpoints
│   ├── agents/              # AI agent implementations
│   │   ├── onboarding_tools.py  # Common helper for agent function tools (NEW)
│   │   ├── workout_planner.py   # Workout Planning Agent (with onboarding tools)
│   │   ├── diet_planner.py      # Diet Planning Agent (with onboarding tools)
│   │   ├── scheduler.py         # Scheduling Agent (with onboarding tools)
│   │   ├── supplement_guide.py  # Supplement Agent (with onboarding tools)
│   │   └── ...                  # Other agents
│   ├── models/              # SQLAlchemy database models
│   │   └── onboarding.py    # OnboardingState model (updated with agent_history)
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── onboarding.py    # Onboarding schemas (progress, state, step)
│   │   └── chat.py          # Chat schemas (onboarding chat request/response)
│   ├── services/            # Business logic layer
│   │   ├── onboarding_service.py  # Onboarding logic (updated with new methods)
│   │   └── agent_orchestrator.py  # Agent routing (updated with onboarding_mode)
│   ├── core/                # Security, config, utilities
│   └── db/                  # Database session management
├── alembic/                 # Database migrations
│   └── versions/            # Migration scripts (includes state consolidation)
├── docs/                    # Documentation (NEW)
│   └── API_DOCUMENTATION.md # Complete API reference
├── tests/                   # Test suite
│   ├── test_onboarding_*.py      # Onboarding tests
│   ├── test_chat_*.py            # Chat endpoint tests
│   ├── test_*_properties.py      # Property-based tests
│   └── test_integration_*.py     # Integration tests
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
