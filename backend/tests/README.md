# Test Suite Documentation

This directory contains the test suite for the Shuren backend application.

## Test Configuration

### Pytest Configuration

Test configuration is defined in `pyproject.toml` under `[tool.pytest.ini_options]`:

- **Async Mode**: `asyncio_mode = "auto"` - Automatically detects and runs async tests
- **Test Discovery**: Tests are discovered in the `tests/` directory with pattern `test_*.py`
- **Markers**: Tests can be marked with categories (unit, integration, property, etc.)
- **Coverage**: Coverage reporting is configured to track code coverage

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_auth_endpoints.py

# Run specific test
poetry run pytest tests/test_auth_endpoints.py::TestRegisterEndpoint::test_register_success

# Run tests by marker
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m property

# Run with coverage report
poetry run pytest --cov=app --cov-report=html

# Run and open coverage report
poetry run pytest --cov=app --cov-report=html
# Then open htmlcov/index.html in browser
```

## Test Fixtures

The `conftest.py` file provides shared fixtures for all tests:

### Database Fixtures

#### `db_session`
Provides a clean database session for each test. Creates all tables before the test and drops them after.

```python
async def test_create_user(db_session: AsyncSession):
    user = User(email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
```

#### `client`
Provides an async HTTP client for API testing with database session override.

```python
async def test_api_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/users")
    assert response.status_code == 200
```

### User Fixtures

#### `test_user`
Creates a test user with email/password authentication.

```python
async def test_user_profile(test_user: User):
    assert test_user.email == "testuser@example.com"
    assert test_user.hashed_password is not None
```

#### `oauth_user`
Creates a test user with Google OAuth authentication.

```python
async def test_oauth_flow(oauth_user: User):
    assert oauth_user.oauth_provider == "google"
    assert oauth_user.hashed_password is None
```

#### `authenticated_client`
Provides an HTTP client with JWT authentication header set.

```python
async def test_protected_endpoint(authenticated_client):
    client, user = authenticated_client
    response = await client.get("/api/v1/profiles/me")
    assert response.status_code == 200
```

#### `completed_onboarding_user`
Creates a user with completed onboarding and locked profile.

```python
async def test_profile_operations(completed_onboarding_user):
    user, profile = completed_onboarding_user
    assert profile.is_locked is True
```

### Data Fixtures

#### `sample_onboarding_data`
Provides complete valid onboarding data for all 11 steps.

```python
def test_onboarding_flow(sample_onboarding_data: dict):
    assert sample_onboarding_data["step_1"]["age"] == 28
    assert sample_onboarding_data["step_2"]["fitness_level"] == "intermediate"
```

#### `minimal_onboarding_data`
Provides minimal valid onboarding data with only required fields.

```python
def test_minimal_onboarding(minimal_onboarding_data: dict):
    assert minimal_onboarding_data["step_2"]["fitness_level"] == "beginner"
```

#### `invalid_onboarding_data`
Provides invalid onboarding data for validation testing.

```python
def test_validation_errors(invalid_onboarding_data: dict):
    # Test that validation catches invalid data
    assert invalid_onboarding_data["step_1"]["age"] == 15  # Too young
```

## Test Database Setup

Tests use a separate test database to avoid polluting development data.

### Automatic Test Database

The test fixtures automatically:
1. Convert the `DATABASE_URL` to use a test database (prefixed with `test_`)
2. Create all tables before each test
3. Drop all tables after each test

### Manual Test Database Creation

If you need to manually create the test database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create test database
CREATE DATABASE test_shuren;

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE test_shuren TO your_user;
```

### Environment Variables

Ensure your `.env` file has the correct `DATABASE_URL`:

```env
DATABASE_URL=postgresql://user:password@localhost/shuren
```

The test suite will automatically use `test_shuren` database.

## Test Categories

Tests are organized by category using pytest markers:

- **unit**: Unit tests for individual components
- **integration**: Integration tests requiring database
- **property**: Property-based tests using Hypothesis
- **slow**: Tests that take significant time to run
- **auth**: Authentication and authorization tests
- **onboarding**: Onboarding flow tests
- **profile**: User profile tests

### Running Tests by Category

```bash
# Run only unit tests
poetry run pytest -m unit

# Run only integration tests
poetry run pytest -m integration

# Run only property-based tests
poetry run pytest -m property

# Exclude slow tests
poetry run pytest -m "not slow"
```

## Writing New Tests

### Unit Test Example

```python
import pytest
from app.core.security import hash_password, verify_password

def test_password_hashing():
    """Test password hashing and verification."""
    password = "mySecurePassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongPassword", hashed)
```

### Integration Test Example

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

@pytest.mark.integration
async def test_create_user_in_database(db_session: AsyncSession):
    """Test creating a user in the database."""
    user = User(
        email="newuser@example.com",
        hashed_password=hash_password("password"),
        full_name="New User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.id is not None
    assert user.created_at is not None
```

### API Test Example

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_endpoint(client: AsyncClient):
    """Test user registration endpoint."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securePassword123",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

### Property-Based Test Example

```python
import pytest
from hypothesis import given, strategies as st
from app.core.security import hash_password, verify_password

@pytest.mark.property
@given(password=st.text(min_size=8, max_size=100))
def test_password_hashing_property(password: str):
    """Property: Hashed password should always verify correctly."""
    hashed = hash_password(password)
    assert verify_password(password, hashed)
```

## Coverage Reporting

Coverage is configured to:
- Track all code in the `app/` directory
- Exclude tests, migrations, and cache directories
- Show missing lines in reports
- Generate HTML reports in `htmlcov/` directory

### Viewing Coverage

```bash
# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Open coverage report
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

## Troubleshooting

### Database Connection Errors

If you see database connection errors:
1. Ensure PostgreSQL is running
2. Verify `DATABASE_URL` in `.env` is correct
3. Create the test database manually if needed
4. Check that the database user has proper permissions

### Async Test Errors

If async tests fail with event loop errors:
1. Ensure `pytest-asyncio` is installed
2. Check that `asyncio_mode = "auto"` is set in `pyproject.toml`
3. Use `@pytest.mark.asyncio` decorator for async tests

### Import Errors

If you see import errors:
1. Ensure you're running tests with `poetry run pytest`
2. Check that all dependencies are installed: `poetry install`
3. Verify you're in the correct directory (`backend/`)

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Use fixtures to ensure proper setup and teardown
3. **Naming**: Use descriptive test names that explain what is being tested
4. **Assertions**: Use clear assertions with helpful error messages
5. **Coverage**: Aim for >80% code coverage on core business logic
6. **Speed**: Keep tests fast; use mocks for external dependencies when appropriate
7. **Documentation**: Add docstrings to complex tests explaining their purpose
