# Design Document: LiveKit Infrastructure

## Overview

This design document specifies the implementation of LiveKit infrastructure for real-time voice interactions in the Shuren fitness coaching application. LiveKit is an open-source WebRTC platform that provides low-latency audio/video communication infrastructure. This implementation establishes the foundation for voice-based coaching sessions by setting up LiveKit server connectivity, room management, access token generation, and RESTful API endpoints for session lifecycle management.

The design follows a layered architecture pattern:
- **Configuration Layer**: Environment-based LiveKit credentials and settings
- **Client Layer**: Singleton LiveKit API client for room and token operations
- **Service Layer**: Business logic for session creation, status queries, and termination
- **API Layer**: RESTful endpoints for client applications to manage voice sessions
- **Security Layer**: JWT authentication and user ownership verification

This infrastructure is designed to be deployment-flexible, supporting both LiveKit Cloud (managed service) and self-hosted LiveKit servers. The implementation integrates seamlessly with the existing FastAPI authentication system and follows established patterns for dependency injection, error handling, and API documentation.

## Architecture

### System Context

```
┌─────────────────┐
│  Client App     │
│ (iOS/Android/   │
│     Web)        │
└────────┬────────┘
         │ HTTPS/REST
         │ (JWT Auth)
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│  ┌───────────────────────────────────┐  │
│  │  Voice Session Endpoints          │  │
│  │  /api/v1/voice-sessions/*         │  │
│  └──────────────┬────────────────────┘  │
│                 │                        │
│  ┌──────────────▼────────────────────┐  │
│  │  LiveKit Client (Singleton)       │  │
│  │  - Room Management                │  │
│  │  - Token Generation               │  │
│  └──────────────┬────────────────────┘  │
│                 │                        │
│  ┌──────────────▼────────────────────┐  │
│  │  Configuration (Pydantic)         │  │
│  │  - LIVEKIT_URL                    │  │
│  │  - LIVEKIT_API_KEY                │  │
│  │  - LIVEKIT_API_SECRET             │  │
│  └───────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │ WebRTC/gRPC
                  ▼
         ┌────────────────────┐
         │  LiveKit Server    │
         │  (Cloud or Self-   │
         │   Hosted)          │
         └────────────────────┘
```

### Component Interaction Flow

**Voice Session Creation Flow:**
```
1. Client → POST /api/v1/voice-sessions/start (JWT token, agent_type)
2. Backend → Validate JWT, extract user
3. Backend → Generate unique room name
4. Backend → Create LiveKit room with metadata
5. Backend → Generate access token for user
6. Backend → Return room details + token to client
7. Client → Connect to LiveKit room using token
8. LiveKit → Dispatch agent worker (automatic)
```

**Session Status Query Flow:**
```
1. Client → GET /api/v1/voice-sessions/{room_name}/status (JWT token)
2. Backend → Validate JWT, extract user
3. Backend → Fetch room info from LiveKit
4. Backend → Verify user owns room (check metadata)
5. Backend → Return room status (active, participants, agent_connected)
```

**Session Termination Flow:**
```
1. Client → DELETE /api/v1/voice-sessions/{room_name} (JWT token)
2. Backend → Validate JWT, extract user
3. Backend → Fetch room info from LiveKit
4. Backend → Verify user owns room
5. Backend → Delete LiveKit room
6. Backend → Return confirmation
```

## Components and Interfaces

### 1. Configuration Module (`app/core/config.py`)

**Purpose**: Centralized configuration management for LiveKit credentials and settings.

**Additions to Settings Class**:
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # LiveKit Configuration
    LIVEKIT_URL: str = Field(..., description="LiveKit server URL (wss://...)")
    LIVEKIT_API_KEY: str = Field(..., description="LiveKit API key")
    LIVEKIT_API_SECRET: str = Field(..., description="LiveKit API secret")
    LIVEKIT_WORKER_NUM_IDLE: int = Field(
        default=2, 
        description="Number of idle agent workers to maintain"
    )
```

**Validation**:
- All LiveKit fields are required (no defaults)
- Pydantic will raise validation error at startup if missing
- LIVEKIT_URL must be a valid WebSocket URL (wss:// or ws://)

**Environment Variables**:
```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxx
LIVEKIT_API_SECRET=secretxxxx
LIVEKIT_WORKER_NUM_IDLE=2
```

### 2. LiveKit Client Module (`app/core/livekit_client.py`)

**Purpose**: Singleton LiveKit API client and token generation utilities.

**Interface**:
```python
@lru_cache()
def get_livekit_api() -> api.LiveKitAPI:
    """Get LiveKit API client (singleton pattern)"""
    
def create_access_token(
    identity: str,
    name: str,
    room_name: str,
    can_publish: bool = True,
    can_subscribe: bool = True,
    can_publish_data: bool = True
) -> str:
    """Create LiveKit access token for a participant"""
```

**LiveKitAPI Client**:
- Singleton instance created via `@lru_cache()`
- Initialized with URL, API key, and API secret from settings
- Provides methods: `room.create_room()`, `room.get_room()`, `room.delete_room()`, `room.list_rooms()`
- Thread-safe for concurrent requests

**Access Token Generation**:
- Creates JWT token signed with LIVEKIT_API_SECRET
- Includes identity (user_id), name (email), and room grants
- VideoGrants specify: room_join=True, room=room_name, can_publish, can_subscribe, can_publish_data
- TTL set to 6 hours (21600 seconds)
- Returns JWT string for client to use in LiveKit connection

**Security Considerations**:
- API secret never exposed to clients
- Tokens scoped to specific rooms (can't join other rooms)
- Tokens expire after 6 hours
- Identity claim prevents impersonation

### 3. Voice Session Schemas (`app/schemas/voice_session.py`)

**Purpose**: Pydantic models for request/response validation and API documentation.

**VoiceSessionRequest**:
```python
class VoiceSessionRequest(BaseModel):
    agent_type: str = Field(
        default="general",
        description="Type of agent: workout | diet | supplement | tracker | scheduler | general"
    )
```

**VoiceSessionResponse**:
```python
class VoiceSessionResponse(BaseModel):
    room_name: str  # Unique room identifier
    token: str  # LiveKit access token (JWT)
    livekit_url: str  # WebSocket URL for LiveKit connection
    agent_type: str  # Requested agent type
    expires_at: datetime  # Token expiration timestamp
```

**VoiceSessionStatus**:
```python
class VoiceSessionStatus(BaseModel):
    room_name: str  # Room identifier
    active: bool  # True if any participants connected
    participants: int  # Number of current participants
    agent_connected: bool  # True if agent has joined (participants >= 2)
    created_at: Optional[datetime]  # Room creation timestamp
```

**Validation Rules**:
- agent_type must be one of: workout, diet, supplement, tracker, scheduler, general
- room_name follows pattern: "fitness-voice-{uuid}-{hex}"
- token is a valid JWT string
- livekit_url is a valid WebSocket URL
- expires_at is in UTC timezone

### 4. Voice Session Endpoints (`app/api/v1/endpoints/voice_sessions.py`)

**Purpose**: RESTful API endpoints for voice session lifecycle management.

#### Endpoint: POST /api/v1/voice-sessions/start

**Request**:
```json
{
  "agent_type": "workout"
}
```

**Response (200)**:
```json
{
  "room_name": "fitness-voice-123e4567-e89b-12d3-a456-426614174000-a1b2c3d4",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "livekit_url": "wss://your-project.livekit.cloud",
  "agent_type": "workout",
  "expires_at": "2026-02-03T10:30:00Z"
}
```

**Logic**:
1. Authenticate user via JWT (get_current_user dependency)
2. Generate unique room name: `f"fitness-voice-{user.id}-{secrets.token_hex(4)}"`
3. Create room metadata: `{"user_id": str(user.id), "agent_type": agent_type, "mode": "voice", "created_at": utcnow}`
4. Call `livekit_api.room.create_room()` with:
   - name: room_name
   - metadata: JSON string
   - empty_timeout: 300 seconds
   - max_participants: 2
5. Generate access token for user
6. Log room creation event
7. Return VoiceSessionResponse

**Error Responses**:
- 401: Invalid or missing JWT token
- 500: LiveKit API error (room creation failed)

#### Endpoint: GET /api/v1/voice-sessions/{room_name}/status

**Response (200)**:
```json
{
  "room_name": "fitness-voice-123e4567-e89b-12d3-a456-426614174000-a1b2c3d4",
  "active": true,
  "participants": 2,
  "agent_connected": true,
  "created_at": "2026-02-03T09:30:00Z"
}
```

**Logic**:
1. Authenticate user via JWT
2. Call `livekit_api.room.get_room(room_name)`
3. Parse room metadata JSON
4. Verify `metadata["user_id"] == str(current_user.id)`
5. Calculate active status: `room.num_participants > 0`
6. Calculate agent_connected: `room.num_participants >= 2`
7. Return VoiceSessionStatus

**Error Responses**:
- 401: Invalid or missing JWT token
- 403: User does not own this session
- 404: Room not found
- 500: LiveKit API error

#### Endpoint: DELETE /api/v1/voice-sessions/{room_name}

**Response (200)**:
```json
{
  "status": "ended",
  "room_name": "fitness-voice-123e4567-e89b-12d3-a456-426614174000-a1b2c3d4"
}
```

**Logic**:
1. Authenticate user via JWT
2. Call `livekit_api.room.get_room(room_name)` to verify ownership
3. Parse metadata and verify user_id
4. Call `livekit_api.room.delete_room(room_name)`
5. Log termination event
6. Return confirmation

**Error Responses**:
- 401: Invalid or missing JWT token
- 403: User does not own this session
- 404: Room not found
- 500: LiveKit API error

#### Endpoint: GET /api/v1/voice-sessions/active

**Response (200)**:
```json
{
  "sessions": [
    {
      "room_name": "fitness-voice-123e4567-e89b-12d3-a456-426614174000-a1b2c3d4",
      "agent_type": "workout",
      "participants": 2,
      "created_at": "2026-02-03T09:30:00Z"
    },
    {
      "room_name": "fitness-voice-123e4567-e89b-12d3-a456-426614174000-b2c3d4e5",
      "agent_type": "diet",
      "participants": 1,
      "created_at": "2026-02-03T10:15:00Z"
    }
  ]
}
```

**Logic**:
1. Authenticate user via JWT
2. Call `livekit_api.room.list_rooms()`
3. For each room, parse metadata JSON
4. Filter rooms where `metadata["user_id"] == str(current_user.id)`
5. Build list of session summaries
6. Return sessions list

**Error Responses**:
- 401: Invalid or missing JWT token
- 500: LiveKit API error

### 5. Router Registration (`app/api/v1/__init__.py`)

**Integration**:
```python
from app.api.v1.endpoints import voice_sessions

api_router.include_router(
    voice_sessions.router,
    prefix="/voice-sessions",
    tags=["voice-sessions"]
)
```

**Full Path**: `/api/v1/voice-sessions/*`

**OpenAPI Tags**: `["voice-sessions"]` for documentation grouping

## Data Models

### Room Metadata Structure

**Format**: JSON string stored in LiveKit room metadata field

**Schema**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "agent_type": "workout",
  "mode": "voice",
  "created_at": "2026-02-03T09:30:00.123456"
}
```

**Fields**:
- `user_id` (string): UUID of the user who created the session
- `agent_type` (string): Type of agent requested (workout, diet, supplement, tracker, scheduler, general)
- `mode` (string): Always "voice" for this implementation
- `created_at` (string): ISO 8601 timestamp in UTC

**Usage**:
- Stored when room is created
- Retrieved for ownership verification
- Used to filter user's sessions in list endpoint

### Room Naming Convention

**Pattern**: `fitness-voice-{user_id}-{random_hex}`

**Example**: `fitness-voice-123e4567-e89b-12d3-a456-426614174000-a1b2c3d4`

**Components**:
- Prefix: `fitness-voice-` (identifies application and mode)
- User ID: Full UUID of the user
- Random suffix: 4-byte hex string (8 characters) for uniqueness

**Rationale**:
- Globally unique across all users and sessions
- User ID in name enables quick filtering
- Random suffix prevents collisions for concurrent sessions
- Descriptive prefix aids debugging and monitoring

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Token Validity

*For any* authenticated user and valid room name, the generated access token SHALL successfully authenticate the user to join the specified LiveKit room.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

### Property 2: Room Ownership Verification

*For any* room status query or termination request, the system SHALL only allow access if the requesting user's ID matches the user_id in the room metadata.

**Validates: Requirements 4.2, 4.3, 5.1, 5.2, 7.3**

### Property 3: Unique Room Names

*For any* two voice session creation requests, even from the same user, the generated room names SHALL be unique.

**Validates: Requirements 3.2**

### Property 4: Room Metadata Integrity

*For any* created room, the metadata SHALL contain valid JSON with user_id, agent_type, mode, and created_at fields.

**Validates: Requirements 3.3**

### Property 5: Session Filtering

*For any* user's active sessions list request, the returned sessions SHALL only include rooms where the metadata user_id matches the requesting user's ID.

**Validates: Requirements 6.2**

### Property 6: Authentication Enforcement

*For any* voice session endpoint request without a valid JWT token, the system SHALL return a 401 Unauthorized error.

**Validates: Requirements 7.1, 7.4**

### Property 7: Room Configuration Consistency

*For any* created room, the room SHALL have empty_timeout of 300 seconds and max_participants of 2.

**Validates: Requirements 3.4, 3.5**

### Property 8: Token Expiration

*For any* generated access token, the token SHALL have a TTL of exactly 6 hours (21600 seconds).

**Validates: Requirements 2.5**

### Property 9: Error Response Consistency

*For any* endpoint error (401, 403, 404, 500), the response SHALL include a "detail" field with a descriptive message.

**Validates: Requirements 8.2, 8.3, 8.4**

### Property 10: Configuration Validation

*For any* application startup, IF any required LiveKit configuration (URL, API key, API secret) is missing, THEN the application SHALL fail to start with a validation error.

**Validates: Requirements 1.2, 10.1, 10.2, 10.3, 10.4**

## Error Handling

### Error Categories

**1. Authentication Errors (401)**
- Missing JWT token
- Invalid JWT token
- Expired JWT token
- Malformed token

**Response Format**:
```json
{
  "detail": "Invalid token: {reason}",
  "error_code": "UNAUTHORIZED"
}
```

**2. Authorization Errors (403)**
- User does not own the session
- Attempting to access another user's room

**Response Format**:
```json
{
  "detail": "Not your session",
  "error_code": "FORBIDDEN"
}
```

**3. Not Found Errors (404)**
- Room does not exist
- Room was deleted

**Response Format**:
```json
{
  "detail": "Session not found",
  "error_code": "NOT_FOUND"
}
```

**4. Server Errors (500)**
- LiveKit API connection failure
- Room creation failure
- Unexpected exceptions

**Response Format**:
```json
{
  "detail": "Failed to create voice session",
  "error_code": "INTERNAL_ERROR"
}
```

### Error Handling Strategy

**Logging**:
- INFO level: Room creation, status queries, termination (successful operations)
- WARNING level: Authorization failures (403), not found errors (404)
- ERROR level: LiveKit API errors, unexpected exceptions (with full stack trace)

**Exception Handling**:
```python
try:
    # LiveKit API call
    room = await livekit_api.room.create_room(...)
except api.TwirpError as e:
    if e.code == "not_found":
        raise HTTPException(status_code=404, detail="Session not found")
    logger.error(f"LiveKit API error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Security Considerations**:
- Never expose LiveKit API secrets in error messages
- Never expose internal stack traces to clients
- Log full error details server-side for debugging
- Return generic error messages to clients

### Retry Strategy

**No Automatic Retries**:
- Voice sessions are user-initiated and synchronous
- Failed requests should be retried by the client
- Automatic retries could create duplicate rooms

**Client Guidance**:
- If room creation fails (500), client should retry after 1-2 seconds
- If room not found (404), client should create a new session
- If authorization fails (403), client should not retry (invalid request)

## Testing Strategy

### Unit Tests

**Token Generation Tests** (`test_livekit_client.py`):
- Test token contains correct identity (user_id)
- Test token contains correct name (email)
- Test token contains correct room grants
- Test token has 6-hour TTL
- Test token is valid JWT format
- Test token can be decoded with API secret

**Configuration Tests** (`test_config.py`):
- Test LiveKit settings are loaded from environment
- Test validation error when LIVEKIT_URL is missing
- Test validation error when LIVEKIT_API_KEY is missing
- Test validation error when LIVEKIT_API_SECRET is missing

### Integration Tests

**Voice Session Endpoint Tests** (`test_voice_sessions.py`):

**Test: Create Voice Session**
- Given: Authenticated user
- When: POST /api/v1/voice-sessions/start with agent_type="workout"
- Then: Response 200 with room_name, token, livekit_url, agent_type, expires_at
- And: room_name contains "fitness-voice"
- And: token is non-empty string
- And: agent_type matches request

**Test: Get Session Status**
- Given: Authenticated user with active session
- When: GET /api/v1/voice-sessions/{room_name}/status
- Then: Response 200 with room_name, active, participants, agent_connected, created_at
- And: room_name matches request
- And: active is boolean
- And: participants is integer

**Test: End Session**
- Given: Authenticated user with active session
- When: DELETE /api/v1/voice-sessions/{room_name}
- Then: Response 200 with status="ended" and room_name
- And: Subsequent status query returns 404

**Test: List Active Sessions**
- Given: Authenticated user with 2 active sessions
- When: GET /api/v1/voice-sessions/active
- Then: Response 200 with sessions array
- And: sessions array contains 2 items
- And: Each session has room_name, agent_type, participants, created_at

**Test: Unauthorized Access**
- Given: No JWT token
- When: POST /api/v1/voice-sessions/start
- Then: Response 401 with error detail

**Test: Access Other User's Session**
- Given: User A creates session
- And: User B is authenticated
- When: User B requests GET /api/v1/voice-sessions/{user_a_room}/status
- Then: Response 403 with "Not your session" detail

**Test: Room Not Found**
- Given: Authenticated user
- When: GET /api/v1/voice-sessions/nonexistent-room/status
- Then: Response 404 with "Session not found" detail

### Property-Based Tests

**Property Test: Unique Room Names** (Hypothesis)
- Generate: 100 random user IDs
- For each: Create voice session
- Assert: All room names are unique
- **Feature: livekit-infrastructure, Property 3: Unique Room Names**

**Property Test: Token Validity** (Hypothesis)
- Generate: Random user IDs, emails, room names
- For each: Generate access token
- Assert: Token can be decoded with API secret
- Assert: Token identity matches user_id
- Assert: Token name matches email
- Assert: Token grants include room_join=True
- **Feature: livekit-infrastructure, Property 1: Token Validity**

**Property Test: Metadata Integrity** (Hypothesis)
- Generate: Random user IDs, agent types
- For each: Create room with metadata
- Assert: Metadata is valid JSON
- Assert: Metadata contains user_id, agent_type, mode, created_at
- Assert: user_id is valid UUID string
- Assert: agent_type is one of valid types
- **Feature: livekit-infrastructure, Property 4: Room Metadata Integrity**

**Property Test: Session Filtering** (Hypothesis)
- Generate: 10 users, each creates 3 sessions
- For each user: List active sessions
- Assert: Returned sessions only contain user's own sessions
- Assert: No sessions from other users are included
- **Feature: livekit-infrastructure, Property 5: Session Filtering**

### Test Configuration

**Minimum Iterations**: 100 per property test (due to randomization)

**Test Database**: Use test database with clean state per test

**LiveKit Mock**: For unit tests, mock LiveKit API client to avoid external dependencies

**LiveKit Integration**: For integration tests, use real LiveKit Cloud or test server

**Test Fixtures**:
- `authenticated_client`: HTTP client with valid JWT token
- `test_user`: User instance for testing
- `livekit_api_mock`: Mocked LiveKit API client
- `voice_session`: Created voice session for testing

### Coverage Goals

- Unit tests: 100% coverage of token generation and configuration
- Integration tests: 100% coverage of all endpoint paths (success and error cases)
- Property tests: Validate universal properties across randomized inputs
- End-to-end: Manual testing with real LiveKit server and client application
