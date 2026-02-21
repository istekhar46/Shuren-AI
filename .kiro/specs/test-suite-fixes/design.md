# Design Document: Test Suite Fixes

## Overview

This design addresses 43 failing tests in the Shuren backend test suite across six categories: missing schema definitions, incomplete API responses, external API quota limits, event loop management issues, integration test failures, and error message mismatches. The solution involves adding missing schemas, completing response fields, implementing quota handling, fixing async resource management, correcting endpoint routing, and updating error message assertions.

The fixes are designed to be minimally invasive, maintaining all 343 currently passing tests while restoring the 43 failing tests to passing status.

## Architecture

### Component Overview

The test suite fixes span multiple layers of the application:

1. **Schema Layer** (`app/schemas/`): Add missing Pydantic schemas for API responses
2. **Endpoint Layer** (`app/api/v1/endpoints/`): Ensure complete response data and proper imports
3. **Service Layer** (`app/services/`): Verify service implementations return complete data
4. **Test Layer** (`backend/tests/`): Fix test fixtures, async resource management, and assertions

### Affected Components

- **Chat Schemas** (`app/schemas/chat.py`): Add `ChatMessageResponse` schema
- **Chat Endpoints** (`app/api/v1/endpoints/chat.py`): Import and use `ChatService`
- **Dish Schemas** (`app/schemas/dish.py`): Already includes `cuisine_type` - verify usage
- **Meal Template Service** (`app/services/meal_template_service.py`): Ensure complete macro fields
- **Test Fixtures** (`backend/tests/conftest.py`): Add meal template fixtures
- **Property Tests** (`backend/tests/test_chat_properties.py`): Fix AsyncClient lifecycle
- **Agent Tests** (`backend/tests/test_*_agent.py`): Add quota error handling
- **Integration Tests** (`backend/tests/test_integration_e2e.py`): Fix endpoint routing
- **Shopping List Tests** (`backend/tests/test_shopping_list_endpoints.py`): Update error assertions

## Components and Interfaces

### 1. ChatMessageResponse Schema

**Purpose**: Provide a Pydantic schema for individual chat message responses used in test mocking.

**Location**: `backend/app/schemas/chat.py`

**Schema Definition**:
```python
class ChatMessageResponse(BaseModel):
    """
    Schema for individual chat message response.
    
    Used for returning single message data in chat operations,
    particularly for session-based messaging and test mocking.
    """
    id: UUID = Field(..., description="Unique message identifier")
    session_id: UUID = Field(..., description="Chat session identifier")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content text")
    agent_type: Optional[str] = Field(
        None,
        description="Agent type for assistant messages"
    )
    created_at: datetime = Field(..., description="Message creation timestamp")
    
    class Config:
        from_attributes = True
```

**Integration**: Import in `test_chat_endpoints.py` for mock response creation.

### 2. ChatService Import

**Purpose**: Make `ChatService` available in chat endpoints module for test mocking.

**Location**: `backend/app/api/v1/endpoints/chat.py`

**Implementation**: Add import statement at module level:
```python
from app.services.chat_service import ChatService
```

**Note**: If `ChatService` doesn't exist, create a minimal service class or update tests to mock the correct service (likely `AgentOrchestrator`).

### 3. Meal Template Response Completion

**Purpose**: Ensure all meal template responses include complete nutritional macro fields.

**Affected Endpoints**:
- `GET /api/v1/meals/today` → `TodayMealsResponse`
- `GET /api/v1/meals/template` → `MealTemplateResponse`

**Required Fields**:
- `total_carbs_g`: Total carbohydrates for the day/period
- `total_fats_g`: Total fats for the day/period
- `cuisine_type`: Cuisine type for each dish (already in schema, verify population)

**Implementation Location**: `backend/app/api/v1/endpoints/meal_templates.py`

**Changes Required**:
1. In `get_today_meals()`: Verify service returns `total_carbs_g` and `total_fats_g`
2. In `get_meal_template()`: Verify template transformation includes all macro fields
3. In `regenerate_meal_template()`: Verify response includes all macro fields

**Service Layer**: `backend/app/services/meal_template_service.py`
- Ensure `get_today_meals()` calculates and returns `total_carbs_g` and `total_fats_g`
- Verify dish responses include `cuisine_type` from database model

### 4. Test Fixture Enhancements

**Purpose**: Ensure test users have active meal templates for service tests.

**Location**: `backend/tests/conftest.py`

**New Fixtures**:
```python
@pytest.fixture
async def user_with_active_meal_template(db_session: AsyncSession, test_user: User):
    """Create a test user with an active meal template."""
    # Create meal plan
    meal_plan = MealPlan(
        profile_id=test_user.profile.id,
        target_calories=2200,
        target_protein_g=165,
        target_carbs_g=220,
        target_fats_g=73
    )
    db_session.add(meal_plan)
    
    # Create meal schedules
    schedules = [
        MealSchedule(
            profile_id=test_user.profile.id,
            meal_name="Breakfast",
            scheduled_time=time(8, 0),
            day_of_week=0
        ),
        # ... more schedules
    ]
    for schedule in schedules:
        db_session.add(schedule)
    
    await db_session.commit()
    
    # Generate meal template
    service = MealTemplateService(db_session)
    template = await service.generate_template(
        profile_id=test_user.profile.id,
        week_number=1
    )
    
    return test_user, template
```

**Usage**: Update meal template service tests to use this fixture instead of basic `test_user`.

### 5. API Quota Error Handling

**Purpose**: Gracefully handle Google Gemini API quota errors in tests.

**Affected Tests**:
- `backend/tests/test_diet_planner_agent.py`
- `backend/tests/test_general_assistant_agent.py`
- `backend/tests/test_langchain_foundation.py`

**Implementation Strategy**:

**Option A: Skip on Quota Error** (Recommended for CI/CD)
```python
import pytest
from google.api_core.exceptions import ResourceExhausted

@pytest.fixture(autouse=True)
def skip_on_quota_error():
    """Skip tests if Gemini API quota is exceeded."""
    yield
    # Pytest will handle the skip if ResourceExhausted is raised

def test_diet_planner_agent():
    try:
        # Test code that calls Gemini API
        result = agent.process_query("meal plan")
        assert result is not None
    except ResourceExhausted as e:
        pytest.skip(f"Gemini API quota exceeded: {e}")
```

**Option B: Mock Gemini Responses** (Recommended for unit tests)
```python
@pytest.fixture
def mock_gemini_client(monkeypatch):
    """Mock Gemini API client to avoid quota issues."""
    mock_response = MagicMock()
    mock_response.text = "Mocked diet plan response"
    
    mock_client = MagicMock()
    mock_client.generate_content.return_value = mock_response
    
    monkeypatch.setattr(
        "app.agents.diet_planner_agent.genai.GenerativeModel",
        lambda *args, **kwargs: mock_client
    )
    return mock_client
```

**Recommendation**: Use Option B (mocking) for unit tests to ensure consistent, fast test execution. Use Option A (skip) only for integration tests that require real API calls.

### 6. AsyncClient Lifecycle Management

**Purpose**: Fix "Event loop is closed" errors in property tests by properly managing AsyncClient lifecycle.

**Affected Tests**: `backend/tests/test_chat_properties.py` - `TestUserDataIsolation` class

**Problem**: AsyncClient instances are created but not properly closed before the event loop closes, causing RuntimeError.

**Solution**: Use async context managers for AsyncClient lifecycle.

**Implementation**:
```python
class TestUserDataIsolation:
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_history_retrieval_isolation(
        self,
        num_messages_user1: int,
        num_messages_user2: int,
        db_session: AsyncSession
    ):
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        # Create users...
        user1 = User(...)
        user2 = User(...)
        # ... user creation code ...
        
        # Use async context managers for clients
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client1:
            token1 = create_access_token({"user_id": str(user1.id)})
            client1.headers["Authorization"] = f"Bearer {token1}"
            
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client2:
                token2 = create_access_token({"user_id": str(user2.id)})
                client2.headers["Authorization"] = f"Bearer {token2}"
                
                # Create messages...
                # ... message creation code ...
                
                # Make requests
                response1 = await client1.get("/api/v1/chat/history")
                response2 = await client2.get("/api/v1/chat/history")
                
                # Assertions...
                assert response1.status_code == 200
                assert response2.status_code == 200
                # ... more assertions ...
        
        # Clients are automatically closed when exiting context managers
```

**Key Changes**:
1. Replace `AsyncClient(...)` with `async with AsyncClient(...) as client:`
2. Nest context managers for multiple clients
3. Remove manual `await client.aclose()` calls (handled by context manager)
4. Ensure all async operations complete before exiting context

### 7. Integration Test Endpoint Routing

**Purpose**: Fix integration tests that expect 201 status codes but receive 404.

**Affected Tests**: `backend/tests/test_integration_e2e.py`

**Problem Analysis**:
- Tests expect `POST /api/v1/chat/sessions` to return 201
- Tests expect response to include 'id' key
- Current implementation may be using different endpoint or response structure

**Investigation Required**:
1. Check if `POST /api/v1/chat/sessions` endpoint exists
2. Verify endpoint returns 201 status code
3. Verify response includes 'id' field

**Potential Solutions**:

**If endpoint doesn't exist**: Add session creation endpoint to `chat.py`:
```python
@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    request: ChatSessionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ChatSessionResponse:
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        session_type=request.session_type or "general",
        status="active",
        context_data=request.context_data or {}
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return ChatSessionResponse(
        id=session.id,
        session_type=session.session_type,
        status=session.status,
        started_at=session.started_at,
        last_activity_at=session.last_activity_at,
        ended_at=session.ended_at
    )
```

**If endpoint exists but returns wrong status**: Update endpoint to return 201.

**If response missing 'id'**: Update response schema to include 'id' field.

### 8. Shopping List Error Message Fix

**Purpose**: Update test assertions to match actual error message format.

**Affected Tests**: `backend/tests/test_shopping_list_endpoints.py`

**Problem**: Test expects specific error message text that doesn't match actual implementation.

**Solution**:
1. Run the failing test to capture actual error message
2. Update test assertion to match actual message
3. Alternatively, update implementation to match expected message (if test expectation is correct)

**Implementation**:
```python
# Before (failing):
assert "error message text" in response.json()["detail"]

# After (fixed):
assert "actual error message text" in response.json()["detail"]
```

**Investigation Required**: Examine the actual error message returned by the endpoint to determine correct assertion.

## Data Models

### Existing Models (No Changes Required)

- **ConversationMessage**: Already has all required fields (role, content, agent_type, created_at)
- **ChatSession**: Already has session management fields
- **Dish**: Already includes `cuisine_type` field
- **MealTemplate**: Already has template structure
- **TemplateMeal**: Already links meals to dishes

### Schema Additions

**ChatMessageResponse** (New):
- `id`: UUID - Message identifier
- `session_id`: UUID - Session identifier
- `role`: str - "user" or "assistant"
- `content`: str - Message text
- `agent_type`: Optional[str] - Agent type for assistant messages
- `created_at`: datetime - Creation timestamp

**ChatSessionResponse** (New, if needed):
- `id`: UUID - Session identifier
- `session_type`: str - Session type
- `status`: str - Session status
- `started_at`: datetime - Start timestamp
- `last_activity_at`: datetime - Last activity timestamp
- `ended_at`: Optional[datetime] - End timestamp

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Schema Completeness

*For any* API response schema used in the application, all fields referenced in tests and documentation should be defined and properly typed in the Pydantic schema.

**Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.3**

### Property 2: Response Field Consistency

*For any* meal template or dish response, all nutritional macro fields (calories, protein_g, carbs_g, fats_g) and classification fields (cuisine_type, meal_type) should be present and populated with valid values.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: HTTP Status Code Correctness

*For any* API endpoint, validation errors should return 422 status codes, successful creations should return 201, successful retrievals should return 200, and missing resources should return 404.

**Validates: Requirements 1.4, 5.1**

### Property 4: Async Resource Cleanup

*For any* test that creates AsyncClient instances or other async resources, those resources should be closed before the event loop closes, preventing "Event loop is closed" errors.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 8.2**

### Property 5: Test Isolation

*For any* test execution, database records, HTTP clients, and external resources should be isolated per test and cleaned up after test completion, ensuring no data leakage between test runs.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

### Property 6: Backward Compatibility

*For any* schema or service modification, all currently passing tests (343 tests) should continue to pass, ensuring no regressions are introduced.

**Validates: Requirements 7.1, 7.2, 7.3**

## Error Handling

### API Quota Errors

**Error Type**: `google.api_core.exceptions.ResourceExhausted`

**Handling Strategy**:
1. **Unit Tests**: Mock Gemini API responses to avoid quota consumption
2. **Integration Tests**: Catch `ResourceExhausted` and skip test with clear message
3. **CI/CD**: Configure environment variables to use mocked responses by default

**Implementation**:
```python
try:
    result = await agent.process_query(query)
except ResourceExhausted as e:
    pytest.skip(f"Gemini API quota exceeded: {e}")
```

### Event Loop Errors

**Error Type**: `RuntimeError: Event loop is closed`

**Root Cause**: AsyncClient not closed before event loop cleanup

**Prevention**:
1. Always use async context managers: `async with AsyncClient(...) as client:`
2. Ensure all async operations complete before exiting context
3. Avoid manual `await client.aclose()` (context manager handles it)

### Import Errors

**Error Type**: `ImportError`, `AttributeError`

**Root Cause**: Missing schema definitions or service imports

**Prevention**:
1. Add missing schemas to appropriate schema modules
2. Add missing imports to endpoint modules
3. Verify imports in test files match actual module structure

### Validation Errors

**Error Type**: HTTP 422 vs HTTP 404

**Root Cause**: Incorrect status code for validation failures

**Prevention**:
1. Ensure FastAPI/Pydantic validation returns 422
2. Ensure missing resources return 404
3. Update test assertions to expect correct status codes

## Testing Strategy

### Unit Tests

**Purpose**: Verify individual components work correctly in isolation.

**Coverage**:
- Schema validation (ChatMessageResponse, ChatSessionResponse)
- Service method completeness (meal template macros)
- Error message formatting (shopping list)

**Examples**:
```python
def test_chat_message_response_schema():
    """Verify ChatMessageResponse schema validates correctly."""
    data = {
        "id": uuid4(),
        "session_id": uuid4(),
        "role": "assistant",
        "content": "Test response",
        "agent_type": "workout",
        "created_at": datetime.now()
    }
    response = ChatMessageResponse(**data)
    assert response.role == "assistant"
    assert response.agent_type == "workout"

def test_meal_template_includes_macros():
    """Verify meal template response includes all macro fields."""
    response = get_today_meals(user, db)
    assert "total_carbs_g" in response
    assert "total_fats_g" in response
    assert response["total_carbs_g"] > 0
```

### Integration Tests

**Purpose**: Verify components work together correctly.

**Coverage**:
- Chat endpoint with session creation
- Meal template generation with complete data
- End-to-end conversation flows

**Examples**:
```python
async def test_chat_session_creation_integration(authenticated_client):
    """Verify chat session creation returns 201 with id."""
    client, user = authenticated_client
    response = await client.post(
        "/api/v1/chat/sessions",
        json={"session_type": "workout"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["session_type"] == "workout"
```

### Property-Based Tests

**Purpose**: Verify universal properties hold across all valid inputs.

**Configuration**: Minimum 100 iterations per property test.

**Coverage**:
- AsyncClient lifecycle management across random test scenarios
- Response field completeness across random data
- Test isolation across random test execution orders

**Examples**:
```python
@given(
    num_clients=st.integers(min_value=1, max_value=5),
    num_requests=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100)
async def test_async_client_lifecycle_property(num_clients, num_requests):
    """
    Property: AsyncClient instances are properly closed.
    
    For any number of clients and requests, all clients should be
    closed before event loop closes, preventing RuntimeError.
    """
    # Feature: test-suite-fixes, Property 4: Async Resource Cleanup
    
    clients = []
    try:
        for _ in range(num_clients):
            async with AsyncClient(base_url="http://test") as client:
                clients.append(client)
                for _ in range(num_requests):
                    response = await client.get("/health")
                    assert response.status_code in [200, 404]
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            pytest.fail("AsyncClient not properly closed before event loop closure")
        raise
```

### Regression Tests

**Purpose**: Ensure fixes don't break existing functionality.

**Strategy**:
1. Run full test suite before fixes: Record 343 passing tests
2. Implement fixes incrementally
3. Run full test suite after each fix: Verify 343 tests still pass
4. Final verification: 386 total tests pass (343 + 43)

**Command**:
```bash
# Run full test suite with coverage
poetry run pytest --cov=app --cov-report=html -v

# Verify test count
poetry run pytest --collect-only | grep "test session starts"
```

### Test Execution Order

1. **Phase 1: Schema Fixes** (Low Risk)
   - Add ChatMessageResponse schema
   - Add ChatService import
   - Run chat endpoint tests: 14 tests should pass

2. **Phase 2: Response Completion** (Medium Risk)
   - Add total_carbs_g and total_fats_g to meal responses
   - Verify cuisine_type population
   - Add meal template fixtures
   - Run meal template tests: 13 tests should pass

3. **Phase 3: Quota Handling** (Low Risk)
   - Add mock implementations for Gemini API
   - Add skip logic for quota errors
   - Run agent tests: 6 tests should pass or skip

4. **Phase 4: Event Loop Fixes** (Medium Risk)
   - Update AsyncClient usage to context managers
   - Run property tests: 3 tests should pass

5. **Phase 5: Integration Fixes** (Medium Risk)
   - Fix endpoint routing or add missing endpoints
   - Update response schemas
   - Run integration tests: 2 tests should pass

6. **Phase 6: Error Message Fixes** (Low Risk)
   - Update error message assertions
   - Run shopping list tests: 1 test should pass

7. **Phase 7: Full Regression** (Critical)
   - Run complete test suite
   - Verify 386 tests pass
   - Verify no new failures

### Test Tagging

All tests should use appropriate pytest markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.property` - Property-based tests
- `@pytest.mark.slow` - Tests that take >1 second

### CI/CD Integration

**Pre-commit Checks**:
- Run unit tests only (fast feedback)
- Verify no import errors
- Check schema validation

**Pull Request Checks**:
- Run full test suite
- Generate coverage report
- Verify 386 tests pass
- Ensure coverage >= 80%

**Main Branch Checks**:
- Run full test suite with property tests (max examples)
- Run integration tests against staging environment
- Generate and archive coverage reports

## Notes

### Implementation Priority

1. **High Priority** (Blocking other tests):
   - ChatMessageResponse schema (blocks 14 tests)
   - Meal template response fields (blocks 13 tests)

2. **Medium Priority** (Intermittent failures):
   - API quota handling (blocks 6 tests intermittently)
   - Event loop management (blocks 3 tests)

3. **Low Priority** (Isolated failures):
   - Integration test routing (blocks 2 tests)
   - Shopping list error message (blocks 1 test)

### Risk Assessment

**Low Risk Changes**:
- Adding new schemas (no existing code affected)
- Adding imports (no behavior change)
- Mocking external APIs (test-only change)
- Updating test assertions (test-only change)

**Medium Risk Changes**:
- Modifying response data (could affect frontend)
- Changing AsyncClient usage (could affect other tests)
- Adding new endpoints (could affect routing)

**High Risk Changes**:
- None identified (all changes are additive or test-only)

### Rollback Strategy

If fixes cause regressions:
1. Identify failing tests
2. Revert specific commit causing failure
3. Re-run test suite to verify 343 tests pass
4. Investigate root cause
5. Implement alternative fix
6. Re-test incrementally

### Performance Considerations

- Mocking Gemini API improves test speed (no network calls)
- Property tests with 100 iterations may take longer (acceptable for thorough validation)
- AsyncClient context managers have negligible performance impact
- Test fixtures with meal template generation may add setup time (cache where possible)

### Future Improvements

1. **Test Data Factories**: Use factory_boy or similar for generating test data
2. **Shared Fixtures**: Extract common fixtures to conftest.py for reuse
3. **Test Utilities**: Create helper functions for common test patterns
4. **Mock Server**: Consider using a mock server for external API calls
5. **Parallel Execution**: Enable pytest-xdist for faster test execution
