# Testing Guidelines

## Testing Framework

**Primary Framework**: pytest with async support
- `pytest-asyncio`: Async test execution
- `pytest-cov`: Code coverage reporting
- `hypothesis`: Property-based testing
- `httpx`: Async HTTP client for API testing

## Test Organization

### Test Structure
```
backend/tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_*_endpoints.py      # API endpoint tests
├── test_*_service.py        # Service layer tests
├── test_*_properties.py     # Property-based tests
└── test_integration_*.py    # Integration tests
```

### Test Categories (Markers)
- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests requiring database
- `@pytest.mark.property` - Property-based tests using Hypothesis
- `@pytest.mark.slow` - Tests that take significant time
- `@pytest.mark.auth` - Authentication/authorization tests
- `@pytest.mark.onboarding` - Onboarding flow tests
- `@pytest.mark.profile` - User profile tests

## Running Tests

### Basic Commands
```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_auth_endpoints.py

# Run tests by marker
poetry run pytest -m unit
poetry run pytest -m "not slow"

# Run specific test function
poetry run pytest tests/test_auth_endpoints.py::test_register_user

# Verbose output
poetry run pytest -v

# Show print statements
poetry run pytest -s
```

### Coverage
- Target: 80%+ coverage for core business logic
- HTML reports generated in `htmlcov/` directory
- View coverage: Open `htmlcov/index.html` in browser

## Test Fixtures

### Database Fixtures
- `db_session` - Clean database session for each test
- `client` - Async HTTP client with test database
- `test_user` - User with email/password auth
- `oauth_user` - User with OAuth authentication
- `authenticated_client` - HTTP client with JWT token
- `completed_onboarding_user` - User with completed onboarding

### Data Fixtures
- `sample_onboarding_data` - Complete valid onboarding data
- `minimal_onboarding_data` - Minimal valid onboarding data
- `invalid_onboarding_data` - Invalid data for validation tests
- `sample_ingredients` - 10 common ingredients
- `sample_dishes` - 12 dishes covering all meal types
- `user_with_meal_template` - User with meal template and schedules
- `vegetarian_user` - User with vegetarian preferences
- `user_with_allergies` - User with dairy and egg allergies

### Fixture Usage
```python
async def test_something(db_session: AsyncSession, test_user: User):
    # db_session and test_user are automatically provided
    result = await some_operation(test_user.id, db_session)
    assert result is not None
```

## Test Patterns

### API Endpoint Tests
```python
async def test_endpoint(authenticated_client):
    client, user = authenticated_client
    
    # Test successful request
    response = await client.post("/api/v1/resource", json={"data": "value"})
    assert response.status_code == 200
    data = response.json()
    assert data["field"] == "expected"
    
    # Test validation error
    response = await client.post("/api/v1/resource", json={})
    assert response.status_code == 422
```

### Service Layer Tests
```python
async def test_service(db_session: AsyncSession, test_user: User):
    # Test business logic
    result = await service_function(test_user.id, db_session)
    
    # Verify database state
    assert result.status == "expected"
    
    # Verify side effects
    db_record = await db_session.get(Model, result.id)
    assert db_record is not None
```

### Property-Based Tests
```python
from hypothesis import given, strategies as st

@given(
    age=st.integers(min_value=18, max_value=100),
    weight=st.floats(min_value=40.0, max_value=200.0)
)
async def test_property(age: int, weight: float, db_session: AsyncSession):
    # Test that property holds for all valid inputs
    result = await calculate_something(age, weight)
    assert result > 0  # Property: result is always positive
```

## Best Practices

### Test Isolation
- Each test should be independent
- Use fixtures to set up clean state
- Don't rely on test execution order
- Clean up resources in fixtures

### Assertions
- Use descriptive assertion messages
- Test one concept per test function
- Verify both success and failure cases
- Check error messages and status codes

### Async Tests
- Always use `async def` for async tests
- Use `await` for all async operations
- pytest-asyncio handles event loop automatically

### Database Tests
- Use `db_session` fixture for clean database
- Commit changes explicitly: `await db_session.commit()`
- Refresh objects after commit: `await db_session.refresh(obj)`
- Test database constraints and validations

### API Tests
- Test all HTTP methods (GET, POST, PUT, DELETE)
- Verify status codes and response structure
- Test authentication and authorization
- Test validation errors (422)
- Test not found errors (404)
- Test permission errors (403)

### Property-Based Tests
- Use Hypothesis for testing universal properties
- Define smart strategies that match domain constraints
- Test invariants that should always hold
- Let Hypothesis find edge cases

## Common Patterns

### Testing Protected Endpoints
```python
async def test_protected_endpoint(authenticated_client):
    client, user = authenticated_client
    response = await client.get("/api/v1/protected")
    assert response.status_code == 200

async def test_unauthorized_access(client: AsyncClient):
    # No auth token
    response = await client.get("/api/v1/protected")
    assert response.status_code == 401
```

### Testing Validation
```python
async def test_validation_error(authenticated_client):
    client, user = authenticated_client
    
    # Missing required field
    response = await client.post("/api/v1/resource", json={})
    assert response.status_code == 422
    data = response.json()
    assert "field_errors" in data
```

### Testing Database Operations
```python
async def test_create_record(db_session: AsyncSession, test_user: User):
    # Create
    record = Model(user_id=test_user.id, name="test")
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)
    
    # Verify
    assert record.id is not None
    assert record.name == "test"
```

## Debugging Tests

### Print Debugging
```bash
# Show print statements
poetry run pytest -s

# Show local variables on failure
poetry run pytest -l
```

### Debugging Specific Tests
```bash
# Run single test with verbose output
poetry run pytest tests/test_file.py::test_function -v -s

# Stop on first failure
poetry run pytest -x

# Drop into debugger on failure
poetry run pytest --pdb
```

### Common Issues
- **Database connection errors**: Check DATABASE_URL in .env
- **Async errors**: Ensure all async functions use `await`
- **Fixture not found**: Check fixture scope and imports
- **Test isolation**: Ensure tests don't share mutable state

## CI/CD Integration

Tests should run automatically on:
- Pull requests
- Commits to main branch
- Pre-deployment checks

Minimum requirements for passing:
- All tests pass
- Coverage >= 80% for new code
- No critical security issues
