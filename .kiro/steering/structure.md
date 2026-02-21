# Project Structure

## Repository Organization

```
shuren/
├── backend/          # FastAPI backend application
├── frontend/         # Client application (iOS/Android/Web)
├── worker/           # Background job workers
├── docs/
│   ├── product/      # Product documentation
│   └── technichal/   # Technical documentation
└── README.md
```

## Backend Structure

The backend follows a layered architecture pattern:

### API Layer (`app/api/`)
- REST endpoints organized by version (`v1/`)
- Endpoint modules by domain: `onboarding.py`, `profiles.py`, `workouts.py`, `meals.py`, `chat.py`
- Dependency injection for auth, database sessions, and shared logic

### Agent Layer (`app/agents/`)
Six specialized AI agents, each with domain expertise:
1. **Workout Planning Agent** - Creates and manages workout plans
2. **Diet Planning Agent** - Builds meal plans and provides nutrition guidance
3. **Supplement Guidance Agent** - Provides non-medical supplement information
4. **Tracking & Adjustment Agent** - Monitors adherence and adapts plans
5. **Scheduling & Reminder Agent** - Manages notifications and timing
6. **Conversational General Assistant** - Handles casual queries and motivation

Each agent:
- Inherits from `BaseAgent` class
- Has access to user context and database
- Defines domain-specific tools/functions
- Uses LLM with specialized prompts

### LiveKit Integration (`app/livekit_agents/`)
- `voice_agent.py` - Voice-based coaching sessions
- `text_agent.py` - Text-based chat interface
- `agent_runner.py` - Background worker process

### Data Layer (`app/models/` and `app/schemas/`)
- **Models**: SQLAlchemy ORM models (database tables)
- **Schemas**: Pydantic models for API request/response validation
- Separation ensures clean API contracts independent of database structure

### Service Layer (`app/services/`)
Business logic that orchestrates between agents, database, and external services:
- `onboarding_service.py` - Onboarding flow management
- `profile_service.py` - User profile operations
- `agent_orchestrator.py` - Routes queries to appropriate agents

### Core Utilities (`app/core/`)
- `security.py` - Authentication, JWT, encryption
- `cache.py` - Redis caching utilities
- `events.py` - Event handlers and webhooks
- `config.py` - Environment configuration

### Database (`app/db/`)
- `base.py` - Base model class
- `session.py` - Async database session management
- `migrations/` - Alembic migration files

## Database Schema

### Core Entities
- `users` - User identity and authentication
- `onboarding_states` - Onboarding progress tracking
- `user_profiles` - Current active configuration (single source of truth)
- `user_profile_versions` - Immutable audit log of changes

### Preferences & Plans
- `fitness_goals` - Goal definitions with quantifiable targets
- `physical_constraints` - Equipment, injuries, limitations
- `dietary_preferences` - Diet type, restrictions, allergies
- `meal_plans` - Fixed nutritional structure
- `meal_schedules` - Meal timing for notifications
- `workout_schedules` - Workout days and timing
- `hydration_preferences` - Water intake reminders
- `lifestyle_baselines` - Energy, stress, sleep tracking

### Design Patterns
- **Third Normal Form (3NF)** for core entities
- **Versioned preferences** - All changes tracked with timestamps
- **Soft deletes** - `deleted_at` timestamp for data lineage
- **JSONB fields** - Flexible storage for evolving preferences
- **Enum tables** - Type safety via reference tables

## Documentation Structure

### Product Documentation (`docs/product/`)
- `What-is-Shuren.md` - Product vision and features
- `RFP.md` - Functional requirements (no implementation details)

### Technical Documentation (`docs/technichal/`)
- `backend_schema.md` - Complete database schema design
- `backend_trd.md` - Technical architecture and stack decisions
- `Onboarding.md` - Detailed onboarding flow specification

## Naming Conventions

### Database
- Tables: `snake_case`, plural nouns (e.g., `users`, `meal_plans`)
- Columns: `snake_case`
- Primary keys: `id` (UUID)
- Foreign keys: `{table_singular}_id` (e.g., `user_id`)
- Timestamps: `created_at`, `updated_at`, `deleted_at`
- Booleans: `is_*` or `has_*` prefix

### Python Code
- Files/modules: `snake_case`
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### API Endpoints
- RESTful conventions: `/api/v1/resource` or `/api/v1/resource/{id}`
- Actions as sub-resources: `/api/v1/users/{id}/profile/lock`
- Versioned: `/api/v1/`, `/api/v2/`

## Key Architectural Patterns

1. **Agent-Based Architecture** - Specialized AI agents for each domain
2. **Async-First** - All I/O operations use async/await
3. **Dependency Injection** - FastAPI's DI system for clean separation
4. **Repository Pattern** - Service layer abstracts database operations
5. **Event-Driven** - Celery for background tasks and scheduled jobs
6. **Immutable History** - Version tables for audit trails
7. **Cache-Aside** - Redis caching with explicit invalidation
