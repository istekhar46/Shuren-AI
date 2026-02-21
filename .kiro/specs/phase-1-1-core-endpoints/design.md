# Design Document: Phase 1.1 Core Endpoints

## Overview

Phase 1.1 Core Endpoints extends the Shuren backend with three critical API modules: workout management, meal management, and AI chat interaction. This phase introduces comprehensive workout plan storage (including exercises, sets, and reps), completes the meal plan API, and establishes the foundation for conversational AI assistance.

The design follows the established patterns from Phase 1 Foundation, maintaining consistency in authentication, error handling, and profile locking mechanisms. All endpoints are async-first, use Pydantic validation, and respect the "fixed plans with flexible execution" principle.

**Key Design Goals:**
- Store complete workout plans with progressive overload tracking
- Provide fast, efficient access to workout and meal data
- Enable AI chat interaction through REST endpoints
- Maintain sub-100ms read and sub-200ms write performance
- Ensure data consistency through profile versioning

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                   │
│  workouts.py  │  meals.py  │  chat.py                   │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│  WorkoutService │ MealService │ ChatService             │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Data Layer (SQLAlchemy)               │
│  Models: WorkoutPlan, WorkoutDay, Exercise, etc.        │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                   │
└─────────────────────────────────────────────────────────┘
```

### Request Flow

1. **Authentication**: JWT validation via `get_current_user` dependency
2. **Validation**: Pydantic schema validation on request body
3. **Authorization**: Verify user owns the requested resource
4. **Business Logic**: Service layer handles profile locking, versioning
5. **Database**: Async SQLAlchemy operations
6. **Response**: Pydantic schema serialization


## Components and Interfaces

### Database Schema Extensions

#### New Tables for Workout Plan Storage

**workout_plans**
```sql
CREATE TABLE workout_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Plan metadata
    plan_name VARCHAR(255) NOT NULL,
    plan_description TEXT,
    duration_weeks INTEGER NOT NULL,
    days_per_week INTEGER NOT NULL,
    
    -- Plan rationale
    plan_rationale TEXT,
    
    -- Lock status
    is_locked BOOLEAN DEFAULT TRUE,
    locked_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_duration CHECK (duration_weeks >= 1 AND duration_weeks <= 52),
    CONSTRAINT valid_days_per_week CHECK (days_per_week >= 1 AND days_per_week <= 7)
);

CREATE UNIQUE INDEX idx_workout_plans_user_id ON workout_plans(user_id);
CREATE INDEX idx_workout_plans_updated ON workout_plans(updated_at DESC);
```

**workout_days**
```sql
CREATE TABLE workout_days (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_plan_id UUID NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
    
    -- Day identification
    day_number INTEGER NOT NULL,
    day_name VARCHAR(255) NOT NULL,
    
    -- Focus areas
    muscle_groups TEXT[] NOT NULL,
    workout_type VARCHAR(50) NOT NULL,
    
    -- Metadata
    description TEXT,
    estimated_duration_minutes INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_day_number CHECK (day_number >= 1 AND day_number <= 7),
    CONSTRAINT valid_workout_type CHECK (
        workout_type IN ('strength', 'cardio', 'hiit', 'active_recovery', 'rest')
    ),
    CONSTRAINT unique_plan_day UNIQUE(workout_plan_id, day_number)
);

CREATE INDEX idx_workout_days_plan ON workout_days(workout_plan_id, day_number);
```


**workout_exercises**
```sql
CREATE TABLE workout_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_day_id UUID NOT NULL REFERENCES workout_days(id) ON DELETE CASCADE,
    exercise_library_id UUID NOT NULL REFERENCES exercise_library(id),
    
    -- Exercise order
    exercise_order INTEGER NOT NULL,
    
    -- Sets and reps
    sets INTEGER NOT NULL,
    reps_min INTEGER,
    reps_max INTEGER,
    reps_target INTEGER,
    
    -- Weight and progression
    weight_kg DECIMAL(6,2),
    weight_progression_type VARCHAR(50),
    
    -- Rest periods
    rest_seconds INTEGER NOT NULL DEFAULT 60,
    
    -- Notes
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_sets CHECK (sets >= 1 AND sets <= 20),
    CONSTRAINT valid_reps CHECK (
        (reps_target IS NOT NULL AND reps_target >= 1 AND reps_target <= 100) OR
        (reps_min IS NOT NULL AND reps_max IS NOT NULL AND reps_min <= reps_max)
    ),
    CONSTRAINT valid_rest CHECK (rest_seconds >= 0 AND rest_seconds <= 600),
    CONSTRAINT valid_progression CHECK (
        weight_progression_type IS NULL OR
        weight_progression_type IN ('linear', 'percentage', 'rpe_based', 'none')
    ),
    CONSTRAINT unique_day_exercise_order UNIQUE(workout_day_id, exercise_order)
);

CREATE INDEX idx_workout_exercises_day ON workout_exercises(workout_day_id, exercise_order);
CREATE INDEX idx_workout_exercises_library ON workout_exercises(exercise_library_id);
```

**exercise_library**
```sql
CREATE TABLE exercise_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Exercise identification
    exercise_name VARCHAR(255) NOT NULL UNIQUE,
    exercise_slug VARCHAR(255) NOT NULL UNIQUE,
    
    -- Classification
    exercise_type VARCHAR(50) NOT NULL,
    primary_muscle_group VARCHAR(100) NOT NULL,
    secondary_muscle_groups TEXT[],
    
    -- Equipment
    equipment_required TEXT[] NOT NULL DEFAULT '{}',
    
    -- Difficulty
    difficulty_level VARCHAR(50) NOT NULL,
    
    -- Instructions
    description TEXT NOT NULL,
    instructions TEXT NOT NULL,
    
    -- Media
    gif_url TEXT,
    video_url TEXT,
    
    -- Metadata
    is_compound BOOLEAN DEFAULT FALSE,
    is_unilateral BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_exercise_type CHECK (
        exercise_type IN ('strength', 'cardio', 'flexibility', 'plyometric', 'olympic')
    ),
    CONSTRAINT valid_difficulty CHECK (
        difficulty_level IN ('beginner', 'intermediate', 'advanced')
    )
);

CREATE INDEX idx_exercise_library_type ON exercise_library(exercise_type);
CREATE INDEX idx_exercise_library_muscle ON exercise_library(primary_muscle_group);
CREATE INDEX idx_exercise_library_difficulty ON exercise_library(difficulty_level);
CREATE INDEX idx_exercise_library_equipment ON exercise_library USING GIN (equipment_required);
```


**chat_sessions**
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session metadata
    session_type VARCHAR(50) NOT NULL DEFAULT 'general',
    context_data JSONB DEFAULT '{}'::jsonb,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_session_type CHECK (
        session_type IN ('general', 'workout', 'meal', 'supplement', 'tracking')
    ),
    CONSTRAINT valid_status CHECK (
        status IN ('active', 'completed', 'abandoned')
    )
);

CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id, started_at DESC);
CREATE INDEX idx_chat_sessions_active ON chat_sessions(user_id, status) 
    WHERE status = 'active';
```

**chat_messages**
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    
    -- Metadata
    agent_type VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_role CHECK (
        role IN ('user', 'assistant', 'system')
    ),
    CONSTRAINT valid_agent_type CHECK (
        agent_type IS NULL OR
        agent_type IN ('workout_planning', 'diet_planning', 'supplement_guidance', 
                      'tracking_adjustment', 'scheduling_reminder', 'conversational')
    )
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX idx_chat_messages_recent ON chat_messages(session_id) 
    WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7 days';
```


### API Endpoints

#### Workout Endpoints (`/api/v1/workouts`)

**GET /api/v1/workouts/plan**
- Returns complete workout plan with all days and exercises
- Response includes exercise library details (name, GIF URL, instructions)
- Performance: < 100ms (uses eager loading)

**GET /api/v1/workouts/plan/day/{day_number}**
- Returns specific workout day with all exercises
- Includes complete exercise details from library
- Performance: < 100ms

**GET /api/v1/workouts/today**
- Returns today's workout based on workout_schedules and current day
- Matches day of week to workout_days
- Returns 404 if no workout scheduled today
- Performance: < 100ms

**GET /api/v1/workouts/week**
- Returns this week's workout schedule with exercise summaries
- Includes day names, muscle groups, estimated duration
- Performance: < 100ms

**PATCH /api/v1/workouts/plan**
- Updates workout plan (requires unlocked profile)
- Validates profile lock status
- Creates profile version if locked profile is modified
- Request body: WorkoutPlanUpdate schema
- Performance: < 200ms

**GET /api/v1/workouts/schedule**
- Returns workout schedule (days and timing)
- Uses existing workout_schedules table
- Performance: < 100ms

**PATCH /api/v1/workouts/schedule**
- Updates workout schedule (requires unlocked profile)
- Validates profile lock status
- Request body: WorkoutScheduleUpdate schema
- Performance: < 200ms


#### Meal Endpoints (`/api/v1/meals`)

**GET /api/v1/meals/plan**
- Returns meal plan (calories, macros, meal count)
- Uses existing meal_plans table
- Performance: < 100ms

**PATCH /api/v1/meals/plan**
- Updates meal plan (requires unlocked profile)
- Validates profile lock status
- Creates profile version if locked profile is modified
- Request body: MealPlanUpdate schema
- Performance: < 200ms

**GET /api/v1/meals/schedule**
- Returns meal schedule (timing for all meals)
- Uses existing meal_schedules table
- Performance: < 100ms

**PATCH /api/v1/meals/schedule**
- Updates meal schedule timing
- Validates time format (HH:MM)
- Request body: MealScheduleUpdate schema
- Performance: < 200ms

**GET /api/v1/meals/today**
- Returns today's meal schedule with timing
- Filters meal_schedules for active meals
- Performance: < 100ms

**GET /api/v1/meals/next**
- Returns next upcoming meal based on current time
- Queries meal_schedules, finds next scheduled_time > now
- Returns 404 if no more meals today
- Performance: < 100ms


#### Chat Endpoints (`/api/v1/chat`)

**POST /api/v1/chat/message**
- Sends message to AI agent and receives response
- Creates session if none exists
- Updates last_activity_at timestamp
- Request body: ChatMessageRequest schema
- Response: ChatMessageResponse schema
- Performance: Variable (depends on LLM response time)

**POST /api/v1/chat/session/start**
- Creates new chat session
- Accepts optional session_type and context_data
- Request body: ChatSessionCreate schema
- Response: ChatSession schema
- Performance: < 200ms

**GET /api/v1/chat/history**
- Returns conversation history for user
- Supports pagination (limit, offset)
- Filters by session_id if provided
- Query params: session_id (optional), limit (default 50), offset (default 0)
- Performance: < 100ms

**DELETE /api/v1/chat/session/{session_id}**
- Ends chat session (marks as completed)
- Updates ended_at timestamp
- Returns 404 if session not found or not owned by user
- Performance: < 200ms


## Data Models

### Pydantic Schemas

#### Workout Schemas

**WorkoutPlanResponse**
```python
class ExerciseLibraryBase(BaseModel):
    id: UUID
    exercise_name: str
    exercise_slug: str
    exercise_type: str
    primary_muscle_group: str
    secondary_muscle_groups: List[str]
    equipment_required: List[str]
    difficulty_level: str
    description: str
    instructions: str
    gif_url: Optional[str]
    is_compound: bool
    is_unilateral: bool

class WorkoutExerciseResponse(BaseModel):
    id: UUID
    exercise_order: int
    sets: int
    reps_min: Optional[int]
    reps_max: Optional[int]
    reps_target: Optional[int]
    weight_kg: Optional[Decimal]
    weight_progression_type: Optional[str]
    rest_seconds: int
    notes: Optional[str]
    exercise: ExerciseLibraryBase

class WorkoutDayResponse(BaseModel):
    id: UUID
    day_number: int
    day_name: str
    muscle_groups: List[str]
    workout_type: str
    description: Optional[str]
    estimated_duration_minutes: Optional[int]
    exercises: List[WorkoutExerciseResponse]

class WorkoutPlanResponse(BaseModel):
    id: UUID
    plan_name: str
    plan_description: Optional[str]
    duration_weeks: int
    days_per_week: int
    plan_rationale: Optional[str]
    is_locked: bool
    workout_days: List[WorkoutDayResponse]
    created_at: datetime
    updated_at: datetime
```

**WorkoutPlanUpdate**
```python
class ExerciseUpdate(BaseModel):
    exercise_library_id: UUID
    exercise_order: int
    sets: int = Field(ge=1, le=20)
    reps_min: Optional[int] = Field(None, ge=1, le=100)
    reps_max: Optional[int] = Field(None, ge=1, le=100)
    reps_target: Optional[int] = Field(None, ge=1, le=100)
    weight_kg: Optional[Decimal] = Field(None, ge=0)
    weight_progression_type: Optional[str] = None
    rest_seconds: int = Field(default=60, ge=0, le=600)
    notes: Optional[str] = None

class WorkoutDayUpdate(BaseModel):
    day_number: int = Field(ge=1, le=7)
    day_name: str
    muscle_groups: List[str]
    workout_type: str
    description: Optional[str] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=15, le=180)
    exercises: List[ExerciseUpdate]

class WorkoutPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    plan_description: Optional[str] = None
    duration_weeks: Optional[int] = Field(None, ge=1, le=52)
    days_per_week: Optional[int] = Field(None, ge=1, le=7)
    workout_days: Optional[List[WorkoutDayUpdate]] = None
```

**WorkoutScheduleResponse**
```python
class WorkoutScheduleResponse(BaseModel):
    id: UUID
    monday_workout: bool
    tuesday_workout: bool
    wednesday_workout: bool
    thursday_workout: bool
    friday_workout: bool
    saturday_workout: bool
    sunday_workout: bool
    preferred_workout_time: Optional[time]
    preferred_workout_duration_minutes: Optional[int]
    workout_reminder_enabled: bool
    reminder_offset_minutes: int
    is_locked: bool
```

**WorkoutScheduleUpdate**
```python
class WorkoutScheduleUpdate(BaseModel):
    monday_workout: Optional[bool] = None
    tuesday_workout: Optional[bool] = None
    wednesday_workout: Optional[bool] = None
    thursday_workout: Optional[bool] = None
    friday_workout: Optional[bool] = None
    saturday_workout: Optional[bool] = None
    sunday_workout: Optional[bool] = None
    preferred_workout_time: Optional[time] = None
    preferred_workout_duration_minutes: Optional[int] = Field(None, ge=15, le=180)
    workout_reminder_enabled: Optional[bool] = None
    reminder_offset_minutes: Optional[int] = Field(None, ge=-120, le=0)
```


#### Meal Schemas

**MealPlanResponse**
```python
class MealPlanResponse(BaseModel):
    id: UUID
    meals_per_day: int
    daily_calories_target: int
    daily_calories_min: int
    daily_calories_max: int
    protein_grams_target: Decimal
    carbs_grams_target: Decimal
    fats_grams_target: Decimal
    protein_percentage: Decimal
    carbs_percentage: Decimal
    fats_percentage: Decimal
    plan_rationale: Optional[str]
    is_locked: bool
    created_at: datetime
    updated_at: datetime
```

**MealPlanUpdate**
```python
class MealPlanUpdate(BaseModel):
    meals_per_day: Optional[int] = Field(None, ge=2, le=8)
    daily_calories_target: Optional[int] = Field(None, ge=1000, le=5000)
    daily_calories_min: Optional[int] = Field(None, ge=1000, le=5000)
    daily_calories_max: Optional[int] = Field(None, ge=1000, le=5000)
    protein_grams_target: Optional[Decimal] = Field(None, gt=0)
    carbs_grams_target: Optional[Decimal] = Field(None, gt=0)
    fats_grams_target: Optional[Decimal] = Field(None, gt=0)
```

**MealScheduleResponse**
```python
class MealScheduleItemResponse(BaseModel):
    id: UUID
    meal_number: int
    meal_name: str
    scheduled_time: time
    notification_offset_minutes: int
    earliest_time: Optional[time]
    latest_time: Optional[time]
    is_active: bool

class MealScheduleResponse(BaseModel):
    meals: List[MealScheduleItemResponse]
```

**MealScheduleUpdate**
```python
class MealScheduleItemUpdate(BaseModel):
    meal_number: int = Field(ge=1, le=10)
    meal_name: Optional[str] = None
    scheduled_time: Optional[time] = None
    notification_offset_minutes: Optional[int] = Field(None, ge=-120, le=0)
    earliest_time: Optional[time] = None
    latest_time: Optional[time] = None
    is_active: Optional[bool] = None

class MealScheduleUpdate(BaseModel):
    meals: List[MealScheduleItemUpdate]
```


#### Chat Schemas

**ChatMessageRequest**
```python
class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    session_id: Optional[UUID] = None
    session_type: Optional[str] = Field(default='general')
    context_data: Optional[Dict[str, Any]] = None
```

**ChatMessageResponse**
```python
class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    agent_type: Optional[str]
    created_at: datetime
```

**ChatSessionCreate**
```python
class ChatSessionCreate(BaseModel):
    session_type: str = Field(default='general')
    context_data: Optional[Dict[str, Any]] = None
```

**ChatSessionResponse**
```python
class ChatSessionResponse(BaseModel):
    id: UUID
    session_type: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    last_activity_at: datetime
```

**ChatHistoryResponse**
```python
class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]
    total: int
    limit: int
    offset: int
```


### Service Layer Design

#### WorkoutService

**Responsibilities:**
- Retrieve workout plans with eager loading of related data
- Validate profile lock status before modifications
- Create profile versions when locked profiles are modified
- Match current day to workout schedule
- Calculate next scheduled workout

**Key Methods:**
```python
class WorkoutService:
    async def get_workout_plan(self, user_id: UUID) -> WorkoutPlan
    async def get_workout_day(self, user_id: UUID, day_number: int) -> WorkoutDay
    async def get_today_workout(self, user_id: UUID) -> Optional[WorkoutDay]
    async def get_week_workouts(self, user_id: UUID) -> List[WorkoutDay]
    async def update_workout_plan(self, user_id: UUID, update: WorkoutPlanUpdate) -> WorkoutPlan
    async def get_workout_schedule(self, user_id: UUID) -> WorkoutSchedule
    async def update_workout_schedule(self, user_id: UUID, update: WorkoutScheduleUpdate) -> WorkoutSchedule
    async def check_profile_lock(self, user_id: UUID) -> bool
    async def create_profile_version(self, user_id: UUID, reason: str) -> None
```

#### MealService

**Responsibilities:**
- Retrieve meal plans and schedules
- Validate profile lock status before modifications
- Create profile versions when locked profiles are modified
- Calculate next meal based on current time
- Validate meal timing and macro calculations

**Key Methods:**
```python
class MealService:
    async def get_meal_plan(self, user_id: UUID) -> MealPlan
    async def update_meal_plan(self, user_id: UUID, update: MealPlanUpdate) -> MealPlan
    async def get_meal_schedule(self, user_id: UUID) -> List[MealSchedule]
    async def update_meal_schedule(self, user_id: UUID, update: MealScheduleUpdate) -> List[MealSchedule]
    async def get_today_meals(self, user_id: UUID) -> List[MealSchedule]
    async def get_next_meal(self, user_id: UUID) -> Optional[MealSchedule]
    async def check_profile_lock(self, user_id: UUID) -> bool
    async def create_profile_version(self, user_id: UUID, reason: str) -> None
    async def validate_macro_percentages(self, update: MealPlanUpdate) -> bool
```

#### ChatService

**Responsibilities:**
- Manage chat sessions and messages
- Route messages to appropriate AI agents (future integration)
- Store conversation history
- Handle session lifecycle

**Key Methods:**
```python
class ChatService:
    async def send_message(self, user_id: UUID, request: ChatMessageRequest) -> ChatMessageResponse
    async def create_session(self, user_id: UUID, create: ChatSessionCreate) -> ChatSession
    async def get_history(self, user_id: UUID, session_id: Optional[UUID], limit: int, offset: int) -> ChatHistoryResponse
    async def end_session(self, user_id: UUID, session_id: UUID) -> None
    async def get_or_create_session(self, user_id: UUID, session_type: str) -> ChatSession
    async def route_to_agent(self, message: str, context: Dict) -> str  # Future: AI agent integration
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Data Persistence Round-Trip

*For any* data entity (workout plan, workout day, exercise, meal plan, meal schedule), storing the entity then immediately retrieving it should return data equivalent to the original input.

**Validates: Requirements 1.1, 1.2, 1.3, 4.3, 5.3, 7.3**

**Rationale:** This is a fundamental round-trip property that ensures data integrity across the persistence layer. It validates that serialization, database storage, and deserialization preserve all fields correctly.

### Property 2: Profile Lock Authorization

*For any* modification attempt (workout plan, workout schedule, meal plan, meal schedule) on a profile where `is_locked=True`, the system should reject the request with HTTP 403 status and include an explanation in the response.

**Validates: Requirements 4.1, 4.2, 5.1, 5.2, 7.1, 7.2, 10.3**

**Rationale:** This property enforces the "no silent changes" principle. Users must explicitly unlock their profile before making modifications, ensuring they understand when their core configuration changes.

### Property 3: Profile Version Creation

*For any* locked profile that is unlocked and modified, the system should create exactly one profile version record before applying changes, and that version should contain the complete pre-modification state.

**Validates: Requirements 4.4, 5.4, 7.5, 11.1, 11.2**

**Rationale:** This ensures audit trail completeness. Every modification to a locked profile is tracked, enabling rollback and historical analysis.

### Property 4: Input Validation Rejection

*For any* invalid input data (negative sets, invalid time format, out-of-range values), the system should reject the request with HTTP 422 status and include specific validation error details in the response.

**Validates: Requirements 1.8, 4.5, 7.4, 10.1**

**Rationale:** This property ensures data quality at the API boundary. Invalid data should never reach the database layer.

### Property 5: User Data Isolation

*For any* user attempting to access data (workout plan, meal plan, chat session) belonging to a different user, the system should reject the request with HTTP 403 status.

**Validates: Requirements 1.5, 8.5, 9.2**

**Rationale:** This enforces data isolation and prevents unauthorized cross-user access. Each user should only access their own data.

### Property 6: Response Completeness

*For any* successful API response, all required fields defined in the response schema should be present and non-null (unless explicitly marked as optional).

**Validates: Requirements 2.1, 2.2, 2.5, 6.1, 6.2**

**Rationale:** This ensures API contract compliance. Clients should be able to rely on the presence of required fields in responses.

### Property 7: Exercise Library Reference Integrity

*For any* workout exercise, the referenced exercise_library_id should exist in the exercise_library table, and retrieving the exercise should include complete library details (name, GIF URL, instructions).

**Validates: Requirements 1.4, 1.7**

**Rationale:** This ensures referential integrity and that workout responses include all necessary information for users to perform exercises correctly.

### Property 8: Chronological Message Ordering

*For any* chat history request, messages should be returned in chronological order (oldest to newest) based on created_at timestamp.

**Validates: Requirements 8.3**

**Rationale:** This ensures conversation coherence. Chat history must be presented in the order messages were sent.

### Property 9: Session State Transitions

*For any* chat session, the state transitions should follow the valid sequence: active → completed (or abandoned), and once a session is ended, it should have a non-null ended_at timestamp.

**Validates: Requirements 8.2, 8.4**

**Rationale:** This ensures session lifecycle correctness. Sessions should follow predictable state transitions.

### Property 10: Time-Based Filtering Correctness

*For any* request for "next" scheduled item (next workout, next meal), the system should return the item with the earliest scheduled time that is after the current time, or null if no such item exists.

**Validates: Requirements 3.2, 6.4**

**Rationale:** This ensures correct time-based filtering logic. Users should receive accurate information about upcoming scheduled items.

### Property 11: Authentication Requirement

*For any* protected endpoint request without a valid JWT token, the system should reject the request with HTTP 401 status.

**Validates: Requirements 9.1**

**Rationale:** This enforces authentication requirements. All protected endpoints must verify user identity.

### Property 12: Error Response Consistency

*For any* error condition (404 not found, 500 internal error), the system should return the appropriate HTTP status code and include an error message in a consistent response format.

**Validates: Requirements 10.2, 10.4**

**Rationale:** This ensures consistent error handling across all endpoints. Clients can rely on predictable error response structures.

### Property 13: Profile Version Immutability

*For any* profile version record, once created, it should never be deleted or modified (immutable audit trail).

**Validates: Requirements 11.5**

**Rationale:** This ensures audit trail integrity. Historical records must be preserved for compliance and debugging.

### Property 14: Timestamp Presence

*For any* created entity (workout plan, meal plan, chat session, chat message), the created_at timestamp should be present and set to a value within 1 second of the current time.

**Validates: Requirements 11.3**

**Rationale:** This ensures temporal tracking of all entities. Timestamps are critical for ordering, filtering, and audit purposes.

### Property 15: API Response Format Consistency

*For any* successful API response, the response should follow the defined Pydantic schema structure with consistent field naming (snake_case) and type serialization.

**Validates: Requirements 13.2**

**Rationale:** This ensures API consistency. All endpoints should follow the same response format conventions.


## Error Handling

### Error Response Format

All errors follow a consistent format:

```python
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str]
    field_errors: Optional[Dict[str, List[str]]]
```

### HTTP Status Codes

| Status Code | Usage | Example |
|-------------|-------|---------|
| 200 OK | Successful GET request | Retrieve workout plan |
| 201 Created | Successful POST creating resource | Create chat session |
| 204 No Content | Successful DELETE | End chat session |
| 400 Bad Request | Malformed request | Invalid JSON |
| 401 Unauthorized | Missing or invalid JWT | No auth token |
| 403 Forbidden | Profile locked or unauthorized access | Modify locked profile |
| 404 Not Found | Resource doesn't exist | Workout day not found |
| 422 Unprocessable Entity | Validation error | Invalid sets value |
| 500 Internal Server Error | Unexpected server error | Database connection failure |

### Error Handling Patterns

**Profile Lock Errors:**
```python
if profile.is_locked:
    raise HTTPException(
        status_code=403,
        detail="Profile is locked. Unlock profile before making modifications.",
        error_code="PROFILE_LOCKED"
    )
```

**Validation Errors:**
```python
# Pydantic automatically raises 422 with field-level details
class WorkoutPlanUpdate(BaseModel):
    duration_weeks: int = Field(ge=1, le=52)  # Validates range
```

**Not Found Errors:**
```python
workout_plan = await db.get(WorkoutPlan, user_id=user_id)
if not workout_plan:
    raise HTTPException(
        status_code=404,
        detail="Workout plan not found for user",
        error_code="WORKOUT_PLAN_NOT_FOUND"
    )
```

**Authorization Errors:**
```python
if resource.user_id != current_user.id:
    raise HTTPException(
        status_code=403,
        detail="Not authorized to access this resource",
        error_code="UNAUTHORIZED_ACCESS"
    )
```

### Exception Handling Middleware

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )
```


## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Both testing approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing

**Library:** [Hypothesis](https://hypothesis.readthedocs.io/) for Python

**Configuration:**
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: phase-1-1-core-endpoints, Property {number}: {property_text}`

**Example Property Test:**
```python
from hypothesis import given, strategies as st
import pytest

# Feature: phase-1-1-core-endpoints, Property 1: Data Persistence Round-Trip
@given(
    plan_name=st.text(min_size=1, max_size=255),
    duration_weeks=st.integers(min_value=1, max_value=52),
    days_per_week=st.integers(min_value=1, max_value=7)
)
@pytest.mark.asyncio
async def test_workout_plan_persistence_roundtrip(
    plan_name, duration_weeks, days_per_week, db_session
):
    """For any workout plan data, storing then retrieving should return equivalent data."""
    # Create workout plan
    workout_plan = WorkoutPlan(
        user_id=test_user_id,
        plan_name=plan_name,
        duration_weeks=duration_weeks,
        days_per_week=days_per_week
    )
    db_session.add(workout_plan)
    await db_session.commit()
    
    # Retrieve workout plan
    retrieved = await db_session.get(WorkoutPlan, workout_plan.id)
    
    # Assert equivalence
    assert retrieved.plan_name == plan_name
    assert retrieved.duration_weeks == duration_weeks
    assert retrieved.days_per_week == days_per_week
```

### Unit Testing

**Library:** pytest with pytest-asyncio

**Focus Areas:**
- Specific examples demonstrating correct behavior
- Edge cases (empty results, boundary values)
- Error conditions (locked profiles, invalid input)
- Integration between components

**Example Unit Tests:**
```python
@pytest.mark.asyncio
async def test_get_workout_plan_returns_complete_structure():
    """Verify workout plan response includes all days and exercises."""
    response = await client.get(
        "/api/v1/workouts/plan",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "workout_days" in data
    assert len(data["workout_days"]) > 0
    assert "exercises" in data["workout_days"][0]

@pytest.mark.asyncio
async def test_modify_locked_profile_returns_403():
    """Verify locked profile prevents modifications."""
    # Ensure profile is locked
    await lock_user_profile(test_user_id)
    
    response = await client.patch(
        "/api/v1/workouts/plan",
        json={"duration_weeks": 12},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "locked" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_next_meal_returns_upcoming_meal():
    """Verify next meal calculation based on current time."""
    # Set up meals at 8:00, 12:00, 18:00
    # Mock current time as 10:00
    with freeze_time("2026-01-28 10:00:00"):
        response = await client.get(
            "/api/v1/meals/next",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scheduled_time"] == "12:00:00"
```

### Test Coverage Goals

- **Line coverage**: > 90%
- **Branch coverage**: > 85%
- **Property test iterations**: 100 per property
- **Integration test coverage**: All endpoint combinations

### Test Data Management

**Fixtures:**
```python
@pytest.fixture
async def test_user(db_session):
    """Create test user with completed onboarding."""
    user = User(
        email="test@example.com",
        external_auth_id="test_auth_id",
        onboarding_completed=True
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture
async def test_workout_plan(db_session, test_user):
    """Create test workout plan with exercises."""
    plan = WorkoutPlan(
        user_id=test_user.id,
        plan_name="Test Plan",
        duration_weeks=12,
        days_per_week=4
    )
    db_session.add(plan)
    await db_session.commit()
    return plan
```

### Performance Testing

While not part of correctness properties, performance should be validated:

```python
@pytest.mark.performance
async def test_workout_plan_query_performance():
    """Verify workout plan queries complete within 100ms."""
    start = time.time()
    response = await client.get(
        "/api/v1/workouts/plan",
        headers={"Authorization": f"Bearer {token}"}
    )
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 0.1  # 100ms
```

### Database Migration Testing

```python
@pytest.mark.migration
async def test_new_tables_created():
    """Verify all new tables exist after migration."""
    tables = await db.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public'"
    )
    table_names = [row[0] for row in tables]
    
    assert "workout_plans" in table_names
    assert "workout_days" in table_names
    assert "workout_exercises" in table_names
    assert "exercise_library" in table_names
    assert "chat_sessions" in table_names
    assert "chat_messages" in table_names
```


## Implementation Notes

### Database Migration Strategy

**Migration Order:**
1. Create exercise_library table (reference data)
2. Create workout_plans table
3. Create workout_days table (depends on workout_plans)
4. Create workout_exercises table (depends on workout_days and exercise_library)
5. Create chat_sessions table
6. Create chat_messages table (depends on chat_sessions)

**Migration File:**
```bash
poetry run alembic revision --autogenerate -m "add_workout_and_chat_tables"
```

**Seed Data:**
The exercise_library table should be seeded with common exercises during migration:
- Compound movements (squats, deadlifts, bench press, rows)
- Isolation exercises (bicep curls, tricep extensions, lateral raises)
- Cardio exercises (running, cycling, rowing)
- Include GIF URLs from a reliable source

### Performance Optimization

**Eager Loading:**
```python
# Load workout plan with all related data in single query
workout_plan = await db.execute(
    select(WorkoutPlan)
    .options(
        selectinload(WorkoutPlan.workout_days)
        .selectinload(WorkoutDay.exercises)
        .selectinload(WorkoutExercise.exercise_library)
    )
    .where(WorkoutPlan.user_id == user_id)
)
```

**Indexes:**
All foreign keys and frequently queried fields have indexes defined in the schema. Additional composite indexes may be added based on query patterns.

**Caching Strategy:**
- Workout plans: Cache for 1 hour (rarely change)
- Meal plans: Cache for 1 hour (rarely change)
- Exercise library: Cache for 24 hours (static reference data)
- Chat sessions: No caching (real-time data)

### Security Considerations

**SQL Injection Prevention:**
- Use SQLAlchemy ORM (parameterized queries)
- Never construct raw SQL with user input

**Authorization:**
- All endpoints verify user_id matches authenticated user
- Profile lock checks prevent unauthorized modifications

**Input Sanitization:**
- Pydantic validation on all inputs
- String length limits on text fields
- Numeric range validation

**Rate Limiting:**
- Chat endpoints: 60 requests/minute per user
- Other endpoints: 120 requests/minute per user

### Dependency Requirements

**New Dependencies:**
```bash
# Property-based testing
poetry add --group dev hypothesis

# No new production dependencies needed
# (FastAPI, SQLAlchemy, Pydantic already available from Phase 1)
```

### API Documentation

FastAPI automatically generates OpenAPI documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

All endpoints should include:
- Summary and description
- Request/response examples
- Possible error responses
- Authentication requirements

### Future Enhancements

**Phase 1.1 establishes the foundation for:**
1. **AI Agent Integration**: Chat endpoints will route to specialized agents
2. **Progressive Overload Tracking**: Exercise history for weight progression
3. **Workout Logging**: Track completed workouts and actual performance
4. **Meal Logging**: Track actual meals consumed vs planned
5. **LiveKit Integration**: Voice-based coaching through chat interface

### Monitoring and Observability

**Key Metrics:**
- Endpoint latency (p50, p95, p99)
- Error rates by endpoint and status code
- Profile lock rejection rate
- Chat message volume
- Database query performance

**Logging:**
- All profile modifications logged with user_id and reason
- All errors logged with stack traces
- Chat messages logged for debugging (with privacy considerations)

**Alerts:**
- Endpoint latency p95 > 200ms
- Error rate > 1%
- Database connection pool exhaustion
- Profile version creation failures

