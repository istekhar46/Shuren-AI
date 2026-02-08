# Implementation Plan: LiveKit Infrastructure

## Overview

This implementation plan establishes the LiveKit infrastructure for real-time voice interactions in the Shuren fitness coaching application. The tasks are organized to build incrementally: first setting up configuration and dependencies, then implementing the core LiveKit client, followed by API endpoints, and finally comprehensive testing. Each task builds on previous work to ensure a stable foundation before adding complexity.

## Tasks

- [x] 1. Install LiveKit SDK dependencies
  - Add `livekit` package (version ^0.17.0) to pyproject.toml using `poetry add`
  - Add `livekit-api` package (version ^0.6.0) to pyproject.toml using `poetry add`
  - Run `poetry install` to install new dependencies
  - Verify installation by importing livekit and livekit-api in Python
  - _Requirements: 1.1_

- [x] 2. Update configuration for LiveKit credentials
  - [x] 2.1 Add LiveKit settings to Settings class in `app/core/config.py`
    - Add `LIVEKIT_URL: str` field with description "LiveKit server URL (wss://...)"
    - Add `LIVEKIT_API_KEY: str` field with description "LiveKit API key"
    - Add `LIVEKIT_API_SECRET: str` field with description "LiveKit API secret"
    - Add `LIVEKIT_WORKER_NUM_IDLE: int` field with default=2 and description
    - All fields except LIVEKIT_WORKER_NUM_IDLE should be required (no defaults)
    - _Requirements: 1.2, 1.4, 10.1, 10.2, 10.3_
  
  - [x] 2.2 Update .env.example with LiveKit configuration
    - Add section header "# LiveKit Configuration"
    - Add LIVEKIT_URL example with placeholder URL
    - Add LIVEKIT_API_KEY example with placeholder key
    - Add LIVEKIT_API_SECRET example with placeholder secret
    - Add LIVEKIT_WORKER_NUM_IDLE with default value 2
    - Include comments explaining each variable
    - _Requirements: 1.4, 10.5_
  
  - [ ]* 2.3 Write unit tests for configuration validation
    - Test that Settings raises validation error when LIVEKIT_URL is missing
    - Test that Settings raises validation error when LIVEKIT_API_KEY is missing
    - Test that Settings raises validation error when LIVEKIT_API_SECRET is missing
    - Test that LIVEKIT_WORKER_NUM_IDLE defaults to 2
    - _Requirements: 1.5, 10.4_

- [x] 3. Create LiveKit client module
  - [x] 3.1 Implement get_livekit_api() singleton function in `app/core/livekit_client.py`
    - Import `livekit.api` and `functools.lru_cache`
    - Import settings from `app.core.config`
    - Create `get_livekit_api()` function decorated with `@lru_cache()`
    - Return `api.LiveKitAPI(url=settings.LIVEKIT_URL, api_key=settings.LIVEKIT_API_KEY, api_secret=settings.LIVEKIT_API_SECRET)`
    - Add docstring explaining singleton pattern
    - _Requirements: 1.3_
  
  - [x] 3.2 Implement create_access_token() function in `app/core/livekit_client.py`
    - Create function with parameters: identity, name, room_name, can_publish, can_subscribe, can_publish_data
    - Set default values: can_publish=True, can_subscribe=True, can_publish_data=True
    - Create `api.AccessToken` with API key and secret from settings
    - Call `token.with_identity(identity)`, `token.with_name(name)`
    - Create `api.VideoGrants` with room_join=True, room=room_name, and permission flags
    - Call `token.with_grants(grants)`
    - Set TTL to 6 hours: `token.with_ttl(6 * 60 * 60)`
    - Return `token.to_jwt()`
    - Add comprehensive docstring with parameter descriptions
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [ ]* 3.3 Write unit tests for token generation
    - **Property 1: Token Validity**
    - Test that generated token is a non-empty string
    - Test that token can be decoded (valid JWT format)
    - Test that decoded token contains identity claim matching user_id
    - Test that decoded token contains name claim matching email
    - Test that decoded token contains room grant for specified room
    - Test that token TTL is 6 hours (21600 seconds)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ] 4. Create voice session schemas
  - [ ] 4.1 Create VoiceSessionRequest schema in `app/schemas/voice_session.py`
    - Import BaseModel and Field from pydantic
    - Create VoiceSessionRequest class with agent_type field
    - Set agent_type default to "general" with description listing valid types
    - Add docstring explaining the request schema
    - _Requirements: 3.1_
  
  - [ ] 4.2 Create VoiceSessionResponse schema in `app/schemas/voice_session.py`
    - Import datetime from datetime module
    - Create VoiceSessionResponse class with fields: room_name, token, livekit_url, agent_type, expires_at
    - Add field descriptions for each field
    - Add docstring explaining the response schema
    - _Requirements: 3.7_
  
  - [x] 4.3 Create VoiceSessionStatus schema in `app/schemas/voice_session.py`
    - Import Optional from typing
    - Create VoiceSessionStatus class with fields: room_name, active, participants, agent_connected, created_at
    - Set created_at as Optional[datetime]
    - Add field descriptions
    - Add docstring explaining the status schema
    - _Requirements: 4.4_

- [x] 5. Implement voice session endpoints
  - [x] 5.1 Create POST /api/v1/voice-sessions/start endpoint in `app/api/v1/endpoints/voice_sessions.py`
    - Import required modules: APIRouter, Depends, HTTPException, datetime, timedelta, secrets, json, logging
    - Import get_current_user from app.core.deps
    - Import get_livekit_api, create_access_token from app.core.livekit_client
    - Import User model and voice session schemas
    - Import livekit.api
    - Create router = APIRouter()
    - Create logger = logging.getLogger(__name__)
    - Implement start_voice_session endpoint with VoiceSessionRequest and current_user dependency
    - Generate unique room name: `f"fitness-voice-{current_user.id}-{secrets.token_hex(4)}"`
    - Create metadata dict with user_id, agent_type, mode="voice", created_at
    - Call livekit_api.room.create_room() with name, metadata (JSON string), empty_timeout=300, max_participants=2
    - Log room creation at INFO level
    - Generate access token using create_access_token()
    - Return VoiceSessionResponse with room details and token
    - Wrap in try/except to catch exceptions and return 500 error
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_
  
  - [x] 5.2 Create GET /api/v1/voice-sessions/{room_name}/status endpoint
    - Implement get_session_status endpoint with room_name path parameter and current_user dependency
    - Call livekit_api.room.get_room(room_name)
    - Parse room.metadata JSON
    - Verify metadata["user_id"] == str(current_user.id), raise 403 if not
    - Calculate active status: room.num_participants > 0
    - Calculate agent_connected: room.num_participants >= 2
    - Convert room.creation_time to datetime
    - Return VoiceSessionStatus
    - Handle api.TwirpError with code "not_found" → 404
    - Handle other exceptions → 500
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 5.3 Create DELETE /api/v1/voice-sessions/{room_name} endpoint
    - Implement end_session endpoint with room_name path parameter and current_user dependency
    - Call livekit_api.room.get_room(room_name) to verify ownership
    - Parse metadata and verify user_id matches current_user.id, raise 403 if not
    - Call livekit_api.room.delete_room(room_name)
    - Log session termination at INFO level
    - Return dict with status="ended" and room_name
    - Handle api.TwirpError with code "not_found" → 404
    - Handle other exceptions → 500
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [x] 5.4 Create GET /api/v1/voice-sessions/active endpoint
    - Implement list_active_sessions endpoint with current_user dependency
    - Call livekit_api.room.list_rooms()
    - Iterate through rooms and parse metadata for each
    - Filter rooms where metadata["user_id"] == str(current_user.id)
    - Build list of session dicts with room_name, agent_type, participants, created_at
    - Return dict with "sessions" key containing the list
    - Handle exceptions and return 500 error
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 6. Register voice sessions router
  - [x] 6.1 Import voice_sessions module in `app/api/v1/__init__.py`
    - Add import: `from app.api.v1.endpoints import voice_sessions`
    - _Requirements: 9.1_
  
  - [x] 6.2 Include voice_sessions router in api_router
    - Call `api_router.include_router(voice_sessions.router, prefix="/voice-sessions", tags=["voice-sessions"])`
    - Ensure this is added after existing router includes
    - _Requirements: 9.1, 9.5_

- [x] 7. Checkpoint - Verify basic functionality
  - Ensure all tests pass: `poetry run pytest`
  - Verify LiveKit configuration is loaded correctly
  - Test that endpoints are registered in OpenAPI docs at /api/docs
  - Ensure no import errors or syntax issues

- [x] 8. Write integration tests for voice session endpoints
  - [x]* 8.1 Write test for creating voice session in `backend/tests/test_voice_sessions.py`
    - Create test_create_voice_session async function with authenticated_client fixture
    - POST to /api/v1/voice-sessions/start with agent_type="workout"
    - Assert response status 200
    - Assert response contains room_name, token, livekit_url, agent_type, expires_at
    - Assert room_name contains "fitness-voice"
    - Assert agent_type matches request
    - _Requirements: 3.1, 3.7_
  
  - [x]* 8.2 Write test for getting session status
    - Create test_get_session_status async function with authenticated_client fixture
    - First create a session via POST /api/v1/voice-sessions/start
    - Extract room_name from response
    - GET /api/v1/voice-sessions/{room_name}/status
    - Assert response status 200
    - Assert response contains room_name, active, participants, agent_connected
    - _Requirements: 4.1, 4.4_
  
  - [x]* 8.3 Write test for ending session
    - Create test_end_session async function with authenticated_client fixture
    - Create a session first
    - DELETE /api/v1/voice-sessions/{room_name}
    - Assert response status 200
    - Assert response contains status="ended"
    - Verify subsequent status query returns 404
    - _Requirements: 5.3, 5.4_
  
  - [x]* 8.4 Write test for listing active sessions
    - Create test_list_active_sessions async function with authenticated_client fixture
    - Create 2 sessions with different agent types
    - GET /api/v1/voice-sessions/active
    - Assert response status 200
    - Assert sessions array contains at least 2 items
    - Assert each session has required fields
    - _Requirements: 6.1, 6.3_
  
  - [x]* 8.5 Write test for unauthorized access
    - Create test_unauthorized_access async function with unauthenticated client
    - POST to /api/v1/voice-sessions/start without JWT token
    - Assert response status 401
    - _Requirements: 7.1, 7.4_
  
  - [x]* 8.6 Write test for accessing other user's session
    - Create test_access_other_user_session async function with two authenticated users
    - User A creates a session
    - User B attempts to GET status of User A's session
    - Assert response status 403
    - Assert detail contains "Not your session"
    - _Requirements: 4.3, 7.3, 7.5_
  
  - [x]* 8.7 Write test for room not found
    - Create test_room_not_found async function with authenticated_client
    - GET /api/v1/voice-sessions/nonexistent-room/status
    - Assert response status 404
    - Assert detail contains "Session not found"
    - _Requirements: 4.5, 5.5_

- [x] 9. Write property-based tests
  - [x]* 9.1 Write property test for unique room names
    - **Property 3: Unique Room Names**
    - Use Hypothesis to generate 100 random user IDs
    - For each user ID, generate room name using the naming pattern
    - Collect all room names in a set
    - Assert len(room_names) == 100 (all unique)
    - Tag: **Feature: livekit-infrastructure, Property 3: Unique Room Names**
    - _Requirements: 3.2_
  
  - [x]* 9.2 Write property test for token validity
    - **Property 1: Token Validity**
    - Use Hypothesis to generate random user IDs (UUIDs), emails, and room names
    - For each combination, call create_access_token()
    - Decode token using jose.jwt.decode() with API secret
    - Assert decoded token contains "identity" claim matching user_id
    - Assert decoded token contains "name" claim matching email
    - Assert decoded token contains "video" grants with room_join=True
    - Run 100 iterations minimum
    - Tag: **Feature: livekit-infrastructure, Property 1: Token Validity**
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_
  
  - [x]* 9.3 Write property test for metadata integrity
    - **Property 4: Room Metadata Integrity**
    - Use Hypothesis to generate random user IDs and agent types
    - For each combination, create metadata dict as done in endpoint
    - Serialize to JSON string and parse back
    - Assert parsed metadata contains user_id, agent_type, mode, created_at
    - Assert user_id is valid UUID string format
    - Assert agent_type is one of: workout, diet, supplement, tracker, scheduler, general
    - Assert mode == "voice"
    - Run 100 iterations minimum
    - Tag: **Feature: livekit-infrastructure, Property 4: Room Metadata Integrity**
    - _Requirements: 3.3_
  
  - [x]* 9.4 Write property test for session filtering
    - **Property 5: Session Filtering**
    - Create 10 test users
    - For each user, create 3 mock rooms with metadata containing their user_id
    - For each user, simulate list_active_sessions logic (filter by user_id)
    - Assert returned sessions only contain that user's sessions (3 sessions)
    - Assert no sessions from other users are included
    - Run 100 iterations minimum
    - Tag: **Feature: livekit-infrastructure, Property 5: Session Filtering**
    - _Requirements: 6.2_

- [x] 10. Final checkpoint - Comprehensive testing
  - Run all tests with coverage: `poetry run pytest --cov=app --cov-report=html`
  - Verify coverage is at least 80% for new code
  - Check that all property tests pass with 100 iterations
  - Verify OpenAPI documentation at /api/docs includes all voice session endpoints
  - Test manual flow: create session → get status → end session
  - Ensure all error cases are handled correctly (401, 403, 404, 500)

## Notes

- Tasks marked with `*` are optional test tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across randomized inputs
- Integration tests validate specific examples and error conditions
- All endpoints require JWT authentication via existing get_current_user dependency
- LiveKit SDK handles WebRTC complexity - we only manage rooms and tokens
- This infrastructure is ready for Sub-Doc 5 (Voice Agent implementation)
