# Design Document: Fix Authentication System

## Overview

This design addresses three critical authentication failures in the Shuren Backend API:

1. **Database Connection Protocol**: The DATABASE_URL uses `postgres://` but SQLAlchemy with asyncpg requires `postgresql+asyncpg://`
2. **Missing Registration Field**: The registration schema requires `full_name` but tests don't provide it
3. **Incomplete Test Data**: Test scripts and Postman collections lack required fields

The fix involves updating the database configuration, ensuring schema consistency, and updating all test data. This is a bug fix rather than a new feature, focusing on making existing functionality work correctly.

## Architecture

### Current State

```
┌─────────────────┐
│  .env file      │
│  DATABASE_URL=  │
│  postgres://... │ ❌ Wrong protocol
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  SQLAlchemy Engine      │
│  (expects asyncpg)      │ ❌ Connection fails
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Auth Endpoints         │
│  - register (requires   │
│    full_name)           │ ❌ Tests don't send it
│  - login                │
└─────────────────────────┘
```

### Target State

```
┌─────────────────────────┐
│  .env file              │
│  DATABASE_URL=          │
│  postgresql+asyncpg://  │ ✅ Correct protocol
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Config (with fallback) │
│  - Auto-converts old    │
│    postgres:// format   │ ✅ Backward compatible
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  SQLAlchemy Engine      │
│  (asyncpg connection)   │ ✅ Connection works
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Auth Endpoints         │
│  - register (email,     │
│    password, full_name) │ ✅ All fields provided
│  - login                │ ✅ Works correctly
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Test Suite             │
│  - Includes full_name   │ ✅ Complete test data
│  - Validates all fields │
└─────────────────────────┘
```

## Components and Interfaces

### 1. Database Configuration Module

**Location**: `backend/app/config.py`

**Current Implementation**:
```python
class Settings(BaseSettings):
    DATABASE_URL: str
    # ... other settings
```

**Updated Implementation**:
```python
class Settings(BaseSettings):
    DATABASE_URL: str
    
    @property
    def async_database_url(self) -> str:
        """Convert DATABASE_URL to asyncpg format if needed."""
        if self.DATABASE_URL.startswith("postgres://"):
            return self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL
```

**Interface**:
- Input: `DATABASE_URL` from environment
- Output: `async_database_url` property with correct protocol
- Behavior: Automatically converts legacy `postgres://` format to `postgresql+asyncpg://`

### 2. Database Session Factory

**Location**: `backend/app/db/session.py`

**Current Implementation**:
```python
engine = create_async_engine(settings.DATABASE_URL)
```

**Updated Implementation**:
```python
engine = create_async_engine(settings.async_database_url)
```

**Interface**:
- Uses `async_database_url` property instead of raw `DATABASE_URL`
- Ensures asyncpg driver is used for all connections

### 3. Registration Schema

**Location**: `backend/app/schemas/auth.py`

**Current Implementation** (already correct):
```python
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
```

**Validation**:
- No changes needed to schema
- Schema is already correct and requires `full_name`
- Issue is in test data, not schema definition

### 4. Registration Endpoint

**Location**: `backend/app/api/v1/endpoints/auth.py`

**Current Implementation** (already correct):
```python
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    # Implementation uses user_data.full_name
```

**Validation**:
- No changes needed to endpoint
- Endpoint correctly uses `UserRegister` schema
- Issue is in test data, not endpoint implementation

### 5. Test Data Updates

**Location**: `test-api-endpoints.js`

**Current Implementation**:
```javascript
const registerData = {
    email: testEmail,
    password: testPassword
};
```

**Updated Implementation**:
```javascript
const registerData = {
    email: testEmail,
    password: testPassword,
    full_name: "Test User"
};
```

**Location**: `.postman.json` (Postman Collection)

**Current Implementation**:
```json
{
    "body": {
        "mode": "raw",
        "raw": "{\"email\":\"{{email}}\",\"password\":\"{{password}}\"}"
    }
}
```

**Updated Implementation**:
```json
{
    "body": {
        "mode": "raw",
        "raw": "{\"email\":\"{{email}}\",\"password\":\"{{password}}\",\"full_name\":\"{{full_name}}\"}"
    }
}
```

## Data Models

### User Model

**Location**: `backend/app/models/user.py`

**Current Schema** (no changes needed):
```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

**Validation**:
- Model already includes `full_name` field
- Database migrations already create this column
- No schema changes required

### JWT Token Structure

**Current Structure** (no changes needed):
```python
{
    "sub": "user_id",  # User UUID as string
    "email": "user@example.com",
    "exp": 1234567890  # Expiration timestamp
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I identified the following consolidations:

**Redundancies Eliminated:**
- Properties 2.3, 2.4, 2.5 (specific field validation errors) are covered by Property 2.1 (all required fields validation)
- Property 3.3 (non-existent user) is covered by Property 3.2 (invalid credentials)
- Property 7.3 (expired token returns 401) is covered by Property 7.2 (expired token validation)
- Property 6.3 (no plain text passwords) is covered by Property 6.1 (password hashing)

**Properties to Combine:**
- Properties 3.4 and 7.4 (token structure and signing) can be combined into one comprehensive token generation property
- Properties 8.1 and 8.2 (success responses) can be tested together as response format consistency

### Correctness Properties

**Property 1: Database URL Protocol Conversion**

*For any* DATABASE_URL string that starts with `postgres://` or `postgresql://`, the `async_database_url` property should return a URL with the `postgresql+asyncpg://` protocol, preserving all other URL components (host, port, database, credentials).

**Validates: Requirements 1.1, 1.3**

---

**Property 2: Registration Field Validation**

*For any* registration request, if any required field (email, password, full_name) is missing, the Registration_Endpoint should return a 422 status code with a descriptive error message indicating which field is missing.

**Validates: Requirements 2.1, 2.3, 2.4, 2.5**

---

**Property 3: Successful User Registration**

*For any* valid registration data containing email, password, and full_name, the Registration_Endpoint should create a new user account and return a 201 status code with user details (excluding password).

**Validates: Requirements 2.2, 8.1**

---

**Property 4: Successful Authentication**

*For any* registered user, when valid credentials (email and password) are provided to the Login_Endpoint, it should return a 200 status code with a JWT token and token_type.

**Validates: Requirements 3.1, 8.2**

---

**Property 5: Invalid Credentials Rejection**

*For any* login attempt with invalid credentials (wrong password or non-existent user), the Login_Endpoint should return a 401 status code with an error message.

**Validates: Requirements 3.2, 3.3, 8.4**

---

**Property 6: JWT Token Structure and Signing**

*For any* successfully authenticated user, the generated JWT token should contain the user's ID and email in the payload, be signed with the JWT_SECRET_KEY, and have an expiration time of 24 hours from generation.

**Validates: Requirements 3.4, 7.1, 7.4**

---

**Property 7: Protected Endpoint Access**

*For any* valid JWT token, when used in a request to a protected endpoint, the Auth_System should validate the token and grant access (return non-401 status).

**Validates: Requirements 3.5**

---

**Property 8: Expired Token Rejection**

*For any* JWT token with an expiration time in the past, when used in a request, the Auth_System should return a 401 unauthorized error.

**Validates: Requirements 7.2, 7.3**

---

**Property 9: Password Hashing**

*For any* user registration, the stored password in the database should be a bcrypt hash (not the plain text password), and subsequent login attempts should successfully verify against this hash.

**Validates: Requirements 6.1, 6.2, 6.3**

---

**Property 10: Password Security in Errors**

*For any* error response from the Auth_System, the response body and logs should not contain plain text passwords.

**Validates: Requirements 6.4, 5.3**

---

**Property 11: Validation Error Format**

*For any* validation error (422 status), the response should include field-level error details indicating which fields failed validation and why.

**Validates: Requirements 5.1, 8.3**

---

## Error Handling

### Error Categories

1. **Validation Errors (422)**
   - Missing required fields
   - Invalid email format
   - Password requirements not met
   - Response includes field-level details

2. **Authentication Errors (401)**
   - Invalid credentials
   - Expired JWT token
   - Missing JWT token
   - Invalid JWT token signature
   - Response includes generic error message (no sensitive details)

3. **Database Errors (500)**
   - Connection failures
   - Query execution errors
   - Transaction failures
   - Response includes generic error message
   - Detailed error logged server-side

4. **Duplicate User Errors (409)**
   - Email already registered
   - Response indicates email conflict

### Error Response Format

All error responses follow this structure:

```json
{
    "detail": "Human-readable error message",
    "field_errors": [  // Only for 422 validation errors
        {
            "field": "full_name",
            "message": "Field required"
        }
    ]
}
```

### Logging Strategy

- **INFO**: Successful authentication, registration
- **WARNING**: Failed login attempts (rate limiting concern)
- **ERROR**: Database connection failures, unexpected errors
- **NEVER LOG**: Plain text passwords, JWT secrets

## Testing Strategy

### Dual Testing Approach

This fix requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of database URL conversion
- Integration with real database (connection test)
- Specific error cases (missing full_name, invalid email)
- JWT token generation and validation examples
- Test data completeness verification

**Property-Based Tests** focus on:
- Universal properties across all valid inputs
- Database URL conversion for any valid URL format
- Registration validation for any combination of missing fields
- Password hashing for any password string
- JWT token structure for any user data
- Error response format consistency

### Property-Based Testing Configuration

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: `# Feature: fix-authentication-system, Property N: [property text]`
- Use Hypothesis strategies for generating test data:
  - `st.emails()` for email addresses
  - `st.text(min_size=8)` for passwords
  - `st.text(min_size=1)` for full names
  - `st.one_of()` for URL protocol variations

**Example Test Structure**:
```python
from hypothesis import given, strategies as st
import pytest

@pytest.mark.property
@given(
    email=st.emails(),
    password=st.text(min_size=8, max_size=100),
    full_name=st.text(min_size=1, max_size=100)
)
async def test_property_3_successful_registration(
    email: str, 
    password: str, 
    full_name: str,
    client: AsyncClient,
    db_session: AsyncSession
):
    """
    Feature: fix-authentication-system, Property 3: Successful User Registration
    For any valid registration data, registration should succeed with 201 status.
    """
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == full_name
    assert "password" not in data
```

### Unit Test Coverage

**Critical Unit Tests**:
1. Database connection with correct protocol (integration test)
2. Registration with all fields succeeds
3. Registration without full_name fails with 422
4. Login with valid credentials succeeds
5. Login with invalid credentials fails with 401
6. JWT token contains correct user data
7. Expired token is rejected
8. Password is hashed in database
9. Test scripts include full_name field
10. Postman collection includes full_name field

### Test Execution

```bash
# Run all tests
poetry run pytest

# Run only property-based tests
poetry run pytest -m property

# Run only unit tests
poetry run pytest -m unit

# Run with coverage
poetry run pytest --cov=app --cov-report=html
```

### Success Criteria

- All property-based tests pass (100+ iterations each)
- All unit tests pass
- Test pass rate improves from 21% to 80%+
- Code coverage for auth module: 90%+
- No passwords in logs or error responses
- Database connection succeeds on startup
