# Design Document: API Endpoint Completion

## Overview

This design implements two missing API endpoints to achieve 100% test coverage in the Shuren fitness backend:

1. **GET /api/v1/dishes** - Returns a paginated, filterable list of all dishes
2. **POST /api/v1/chat/sessions** - Creates a new chat session for AI agent interaction

Both endpoints follow existing architectural patterns, reuse established service layer methods, and maintain consistency with the current API design. The implementation focuses on minimal code changes by leveraging existing infrastructure.

## Architecture

### System Context

```
┌─────────────┐
│   Frontend  │
│  (Mobile/   │
│    Web)     │
└──────┬──────┘
       │ HTTP/REST
       │ JWT Auth
       ▼
┌─────────────────────────────────────┐
│      FastAPI Application            │
│  ┌───────────────────────────────┐  │
│  │   API v1 Router               │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Dishes Router          │  │  │
│  │  │  - GET /dishes (NEW)    │  │  │
│  │  │  - GET /dishes/search   │  │  │
│  │  │  - GET /dishes/{id}     │  │  │
│  │  └─────────────────────────┘  │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Chat Router (NEW REG)  │  │  │
│  │  │  - POST /sessions (NEW) │  │  │
│  │  │  - POST /message        │  │  │
│  │  │  - GET /history         │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   Service Layer               │  │
│  │  - DishService (existing)     │  │
│  │  - ChatService (existing)     │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  PostgreSQL │
│   Database  │
└─────────────┘
```

### Design Decisions

**Decision 1: Reuse Existing Service Methods**
- Rationale: DishService.search_dishes() and ChatService.create_session() already implement the required business logic
- Impact: Minimal code changes, consistent behavior, reduced testing burden
- Alternative Considered: Create new service methods - rejected due to code duplication

**Decision 2: GET /dishes as Wrapper Around /dishes/search**
- Rationale: The search endpoint already supports all required filters and pagination
- Impact: Single source of truth for dish querying logic
- Alternative Considered: Separate implementation - rejected due to maintenance overhead

**Decision 3: POST /sessions vs POST /session/start**
- Rationale: Test expects /sessions endpoint, existing /session/start serves different purpose
- Impact: Two endpoints for session creation with slightly different semantics
- Alternative Considered: Modify existing endpoint - rejected to avoid breaking changes

**Decision 4: Register Chat Router in API v1**
- Rationale: Chat endpoints currently not accessible via /api/v1 prefix
- Impact: Consistent URL structure across all endpoints
- Alternative Considered: Keep chat separate - rejected due to inconsistency

## Components and Interfaces

### Component 1: Dishes List Endpoint

**Location:** `backend/app/api/v1/endpoints/dishes.py`

**Interface:**
```python
@router.get(
    "/",
    response_model=List[DishSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all dishes"
)
async def list_dishes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    meal_type: Annotated[str | None, Query()] = None,
    diet_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0
) -> List[DishSummaryResponse]:
    """
    List all dishes with optional filters and pagination.
    
    Returns a paginated list of dishes. Automatically excludes dishes
    containing user's allergens. Supports filtering by meal type and
    diet type. Results ordered by popularity score.
    
    Query Parameters:
    - meal_type: Filter by meal type (breakfast, lunch, dinner, snack, pre_workout, post_workout)
    - diet_type: Filter by diet type (vegetarian, vegan)
    - limit: Maximum results (1-100, default 50)
    - offset: Skip N results (default 0)
    
    Returns:
    - Array of DishSummaryResponse objects
    
    Status Codes:
    - 200: Success
    - 400: Invalid parameters
    - 401: Unauthorized
    """
```

**Dependencies:**
- `get_current_user`: Authentication dependency (existing)
- `get_db`: Database session dependency (existing)
- `DishService`: Service layer for dish operations (existing)
- `DishSummaryResponse`: Pydantic response schema (existing)

**Behavior:**
1. Extract authenticated user from JWT token
2. Get database session from dependency injection
3. Extract user's allergen preferences from profile
4. Call DishService.search_dishes() with filters and allergen exclusions
5. Convert results to DishSummaryResponse objects
6. Return array of dish summaries

### Component 2: Chat Sessions Endpoint

**Location:** `backend/app/api/v1/endpoints/chat.py`

**Interface:**
```python
@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create chat session"
)
async def create_chat_session(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    session_create: ChatSessionCreate | None = None
) -> ChatSessionResponse:
    """
    Create new chat session.
    
    Creates a new conversation context for AI agent interaction.
    If no request body provided, creates a "general" session type.
    
    Request Body (optional):
    - session_type: Type of session (general, workout, meal, supplement, tracking)
    - context_data: Additional context as JSON object
    
    Returns:
    - ChatSessionResponse with session details
    
    Status Codes:
    - 201: Session created
    - 401: Unauthorized
    - 422: Validation error
    """
```

**Dependencies:**
- `get_current_user`: Authentication dependency (existing)
- `get_db`: Database session dependency (existing)
- `ChatService`: Service layer for chat operations (existing)
- `ChatSessionCreate`: Pydantic request schema (existing)
- `ChatSessionResponse`: Pydantic response schema (existing)

**Behavior:**
1. Extract authenticated user from JWT token
2. Get database session from dependency injection
3. If no request body provided, create default ChatSessionCreate with type "general"
4. Call ChatService.create_session() with user_id and session data
5. Convert result to ChatSessionResponse
6. Return session details with HTTP 201 Created

### Component 3: Router Registration

**Location:** `backend/app/api/v1/__init__.py`

**Interface:**
```python
# Import chat router
from app.api.v1.endpoints import chat

# Register chat router
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)
```

**Dependencies:**
- `chat.router`: Chat endpoint router (existing)
- `api_router`: API v1 router (existing)

**Behavior:**
1. Import chat router from endpoints module
2. Register router with API v1 router
3. Apply "/chat" prefix to all chat endpoints
4. Tag endpoints with "Chat" for OpenAPI documentation

## Data Models

### Existing Models (No Changes Required)

**DishSummaryResponse** (from `app/schemas/dish.py`):
```python
class DishSummaryResponse(BaseModel):
    id: UUID
    name: str
    name_hindi: str | None
    meal_type: str
    cuisine_type: str
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    prep_time_minutes: int
    cook_time_minutes: int
    total_time_minutes: int
    difficulty_level: str
    is_vegetarian: bool
    is_vegan: bool
```

**ChatSessionCreate** (from `app/schemas/chat.py`):
```python
class ChatSessionCreate(BaseModel):
    session_type: str = "general"
    context_data: dict | None = None
```

**ChatSessionResponse** (from `app/schemas/chat.py`):
```python
class ChatSessionResponse(BaseModel):
    id: UUID
    session_type: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    last_activity_at: datetime
```

### Data Flow

**GET /api/v1/dishes Flow:**
```
Request → Authentication → Extract User Profile → Get Allergens
    → Call DishService.search_dishes(filters, exclude_allergens)
    → Query Database (with indexes)
    → Convert to DishSummaryResponse[]
    → Return JSON Response
```

**POST /api/v1/chat/sessions Flow:**
```
Request → Authentication → Parse Request Body (or use default)
    → Call ChatService.create_session(user_id, session_data)
    → Insert into chat_sessions table
    → Return ChatSessionResponse
    → HTTP 201 Created
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following testable properties. During reflection, I found several opportunities to consolidate:

**Consolidation 1:** Requirements 1.3 and 1.4 (limit and offset) can be combined into a single pagination property that tests both behaviors together.

**Consolidation 2:** Requirements 1.5 and 1.6 (meal_type and diet_type filtering) follow the same pattern and can be tested with a single filter property that works for any filter type.

**Consolidation 3:** Requirements 2.6, 2.8, and 2.9 (response structure, status, and timestamps) all relate to session creation invariants and can be combined into a single property about session initialization.

**Redundancy Elimination:** Requirement 6.2 is redundant with 2.6, so it's excluded. Requirements 5.1-5.5 are implementation details, not observable properties. Requirements 3.1-3.5 are tested implicitly by endpoint functionality.

### Properties for GET /api/v1/dishes

**Property 1: Pagination Correctness**

*For any* valid limit and offset values, requesting dishes with those parameters should return at most `limit` results, and the results should be different from a request with offset=0 (assuming sufficient dishes exist).

**Validates: Requirements 1.3, 1.4**

**Property 2: Filter Correctness**

*For any* valid filter parameter (meal_type or diet_type) and filter value, all returned dishes should match the specified filter criteria.

**Validates: Requirements 1.5, 1.6**

**Property 3: Allergen Exclusion**

*For any* user with allergen preferences, no returned dish should contain any of those allergens in its contains_allergens array.

**Validates: Requirements 1.7**

**Property 4: Response Schema Compliance**

*For any* dish returned by the endpoint, the response object should contain all required fields from DishSummaryResponse schema (id, name, meal_type, cuisine_type, calories, protein_g, carbs_g, fats_g, prep_time_minutes, cook_time_minutes, total_time_minutes, difficulty_level, is_vegetarian, is_vegan).

**Validates: Requirements 6.1**

**Property 5: Empty Result Handling**

*For any* filter combination that matches no dishes, the endpoint should return an empty array [] rather than null or error.

**Validates: Requirements 6.4**

**Property 6: Error Response Format**

*For any* invalid request parameters (limit > 100, negative offset), the endpoint should return an error response with a "detail" field containing an error message.

**Validates: Requirements 5.5, 6.3**

### Properties for POST /api/v1/chat/sessions

**Property 7: Session Type Preservation**

*For any* valid session_type value in the request body, the created session should have that exact session_type in the response.

**Validates: Requirements 2.3**

**Property 8: Context Data Persistence**

*For any* context_data object in the request body, the created session should store that context data (verifiable by retrieving the session).

**Validates: Requirements 2.5**

**Property 9: Session Initialization Invariants**

*For any* newly created session, the response should contain all required fields (id, session_type, status, started_at, ended_at, last_activity_at), the status should be "active", ended_at should be null, and started_at and last_activity_at should be approximately equal to the current timestamp (within 5 seconds).

**Validates: Requirements 2.6, 2.8, 2.9**

**Property 10: Timestamp Format Compliance**

*For any* timestamp field in the response (started_at, last_activity_at), the value should be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.ffffffZ or similar).

**Validates: Requirements 6.5**

## Error Handling

### Authentication Errors

**Scenario:** User attempts to access endpoint without JWT token
- **Response:** HTTP 401 Unauthorized
- **Body:** `{"detail": "Not authenticated"}`
- **Handled By:** FastAPI's `get_current_user` dependency

**Scenario:** User provides invalid or expired JWT token
- **Response:** HTTP 401 Unauthorized
- **Body:** `{"detail": "Could not validate credentials"}`
- **Handled By:** JWT validation in authentication dependency

### Validation Errors

**Scenario:** User provides limit > 100 for GET /dishes
- **Response:** HTTP 422 Unprocessable Entity
- **Body:** FastAPI validation error with field details
- **Handled By:** Pydantic query parameter validation

**Scenario:** User provides negative offset for GET /dishes
- **Response:** HTTP 422 Unprocessable Entity
- **Body:** FastAPI validation error with field details
- **Handled By:** Pydantic query parameter validation

**Scenario:** User provides invalid session_type for POST /chat/sessions
- **Response:** HTTP 422 Unprocessable Entity
- **Body:** FastAPI validation error with enum details
- **Handled By:** Pydantic request body validation

### Database Errors

**Scenario:** Database connection fails during request
- **Response:** HTTP 500 Internal Server Error
- **Body:** `{"detail": "Internal server error"}`
- **Handled By:** FastAPI exception handlers
- **Logging:** Error logged with full stack trace

**Scenario:** Database query timeout
- **Response:** HTTP 504 Gateway Timeout
- **Body:** `{"detail": "Request timeout"}`
- **Handled By:** Database session timeout configuration

### Service Layer Errors

**Scenario:** DishService.search_dishes() raises exception
- **Response:** HTTP 500 Internal Server Error
- **Body:** `{"detail": "Internal server error"}`
- **Handled By:** Endpoint try-catch block (if needed) or FastAPI default handler

**Scenario:** ChatService.create_session() raises exception
- **Response:** HTTP 500 Internal Server Error
- **Body:** `{"detail": "Internal server error"}`
- **Handled By:** Endpoint try-catch block (if needed) or FastAPI default handler

### Edge Cases

**Scenario:** User profile has no dietary preferences
- **Behavior:** Treat as no allergen exclusions, return all matching dishes
- **Handled By:** Null-safe allergen extraction in endpoint

**Scenario:** No dishes match filter criteria
- **Behavior:** Return empty array []
- **Handled By:** Service layer returns empty list, endpoint returns it as-is

**Scenario:** POST /chat/sessions with no request body
- **Behavior:** Create session with default type "general" and empty context_data
- **Handled By:** Optional request body parameter with default value

## Testing Strategy

### Dual Testing Approach

This feature requires both **unit tests** and **property-based tests** for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs
- Together they provide comprehensive coverage: unit tests catch concrete bugs, property tests verify general correctness

### Unit Testing

**Focus Areas:**
- Specific examples demonstrating correct behavior
- Edge cases (empty results, missing profile data, default values)
- Error conditions (authentication failures, validation errors)
- Integration points (service layer calls, database queries)

**Example Unit Tests:**

```python
# GET /dishes endpoint
async def test_list_dishes_returns_200(authenticated_client):
    """Test that authenticated request returns 200 OK"""
    client, user = authenticated_client
    response = await client.get("/api/v1/dishes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

async def test_list_dishes_unauthorized(client):
    """Test that unauthenticated request returns 401"""
    response = await client.get("/api/v1/dishes")
    assert response.status_code == 401

async def test_list_dishes_default_limit(authenticated_client):
    """Test that default limit is 50"""
    client, user = authenticated_client
    response = await client.get("/api/v1/dishes")
    assert response.status_code == 200
    dishes = response.json()
    assert len(dishes) <= 50

async def test_list_dishes_empty_results(authenticated_client):
    """Test that no matches returns empty array"""
    client, user = authenticated_client
    response = await client.get("/api/v1/dishes?meal_type=nonexistent")
    assert response.status_code == 200
    assert response.json() == []

# POST /chat/sessions endpoint
async def test_create_session_returns_201(authenticated_client):
    """Test that session creation returns 201 Created"""
    client, user = authenticated_client
    response = await client.post("/api/v1/chat/sessions")
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "active"

async def test_create_session_with_type(authenticated_client):
    """Test that session_type is preserved"""
    client, user = authenticated_client
    response = await client.post(
        "/api/v1/chat/sessions",
        json={"session_type": "workout"}
    )
    assert response.status_code == 201
    assert response.json()["session_type"] == "workout"

async def test_create_session_default_type(authenticated_client):
    """Test that default session_type is 'general'"""
    client, user = authenticated_client
    response = await client.post("/api/v1/chat/sessions")
    assert response.status_code == 201
    assert response.json()["session_type"] == "general"
```

### Property-Based Testing

**Framework:** Hypothesis (Python property-based testing library)

**Configuration:**
- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Tag format: `# Feature: api-endpoint-completion, Property N: [property text]`

**Property Test Examples:**

```python
from hypothesis import given, strategies as st

@given(
    limit=st.integers(min_value=1, max_value=100),
    offset=st.integers(min_value=0, max_value=1000)
)
async def test_property_pagination_correctness(
    limit: int,
    offset: int,
    authenticated_client,
    db_session
):
    """
    Feature: api-endpoint-completion, Property 1: Pagination Correctness
    
    For any valid limit and offset values, requesting dishes with those
    parameters should return at most limit results.
    """
    client, user = authenticated_client
    
    response = await client.get(
        f"/api/v1/dishes?limit={limit}&offset={offset}"
    )
    
    assert response.status_code == 200
    dishes = response.json()
    assert len(dishes) <= limit

@given(
    meal_type=st.sampled_from([
        "breakfast", "lunch", "dinner", "snack", 
        "pre_workout", "post_workout"
    ])
)
async def test_property_filter_correctness(
    meal_type: str,
    authenticated_client
):
    """
    Feature: api-endpoint-completion, Property 2: Filter Correctness
    
    For any valid filter parameter, all returned dishes should match
    the specified filter criteria.
    """
    client, user = authenticated_client
    
    response = await client.get(f"/api/v1/dishes?meal_type={meal_type}")
    
    assert response.status_code == 200
    dishes = response.json()
    
    for dish in dishes:
        assert dish["meal_type"] == meal_type

@given(
    session_type=st.sampled_from([
        "general", "workout", "meal", "supplement", "tracking"
    ]),
    context_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.text(), st.integers(), st.booleans())
    )
)
async def test_property_session_type_preservation(
    session_type: str,
    context_data: dict,
    authenticated_client
):
    """
    Feature: api-endpoint-completion, Property 7: Session Type Preservation
    
    For any valid session_type value in the request body, the created
    session should have that exact session_type in the response.
    """
    client, user = authenticated_client
    
    response = await client.post(
        "/api/v1/chat/sessions",
        json={
            "session_type": session_type,
            "context_data": context_data
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["session_type"] == session_type
```

### Integration Testing

**Test Suite:** `test-api-endpoints.js` (existing Node.js test suite)

**Purpose:** Verify end-to-end functionality from HTTP request to database

**Coverage:**
- GET /api/v1/dishes returns 200 OK with dish array
- POST /api/v1/chat/sessions returns 201 Created with session object
- All 19 tests pass (100% pass rate)

**Execution:**
```bash
# Start backend server
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run integration tests (in separate terminal)
node test-api-endpoints.js
```

**Success Criteria:**
- Output shows "19/19 tests passing (100%)"
- No failed tests in the summary
- Both new endpoints return expected status codes and data structures

### Test Organization

```
backend/tests/
├── test_dishes_endpoints.py       # Unit tests for GET /dishes
├── test_chat_endpoints.py         # Unit tests for POST /chat/sessions
├── test_dishes_properties.py      # Property tests for dishes endpoint
└── test_chat_properties.py        # Property tests for chat endpoint
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_dishes_endpoints.py

# Run property tests only
poetry run pytest -m property

# Run unit tests only
poetry run pytest -m unit

# Run integration tests
node test-api-endpoints.js
```

### Coverage Goals

- **Unit Test Coverage:** 100% of new endpoint code
- **Property Test Coverage:** All 10 correctness properties implemented
- **Integration Test Coverage:** 100% pass rate on test-api-endpoints.js
- **Overall Coverage:** Maintain or improve current 89% backend coverage
