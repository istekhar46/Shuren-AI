"""
Integration tests for voice session endpoints.

This module tests the LiveKit voice session management endpoints:
- POST /api/v1/voice-sessions/start - Create voice session
- GET /api/v1/voice-sessions/{room_name}/status - Get session status
- DELETE /api/v1/voice-sessions/{room_name} - End session
- GET /api/v1/voice-sessions/active - List active sessions
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.models.user import User
from livekit import api


# Mock LiveKit API responses
def create_mock_room(room_name: str, metadata: str, num_participants: int = 0):
    """Create a mock LiveKit room object."""
    mock_room = MagicMock()
    mock_room.name = room_name
    mock_room.metadata = metadata
    mock_room.num_participants = num_participants
    mock_room.creation_time = int(datetime.now(timezone.utc).timestamp())
    return mock_room


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_voice_session(authenticated_client):
    """
    Test creating a voice session.
    
    Validates:
    - POST /api/v1/voice-sessions/start returns 200
    - Response contains room_name, token, livekit_url, agent_type, expires_at
    - room_name contains "fitness-voice"
    - agent_type matches request
    """
    client, user = authenticated_client
    
    # Mock LiveKit API
    with patch("app.api.v1.endpoints.voice_sessions.get_livekit_api") as mock_get_api:
        mock_livekit = MagicMock()
        mock_room = create_mock_room(
            room_name=f"fitness-voice-{user.id}-test1234",
            metadata='{"user_id": "' + str(user.id) + '", "agent_type": "workout", "mode": "voice", "created_at": "2026-02-08T10:00:00"}',
            num_participants=0
        )
        
        # Mock create_room to return the mock room
        mock_livekit.room.create_room = AsyncMock(return_value=mock_room)
        mock_get_api.return_value = mock_livekit
        
        # Make request
        response = await client.post(
            "/api/v1/voice-sessions/start",
            json={"agent_type": "workout"}
        )
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "room_name" in data
        assert "token" in data
        assert "livekit_url" in data
        assert "agent_type" in data
        assert "expires_at" in data
        
        # Verify room name format
        assert "fitness-voice" in data["room_name"]
        assert str(user.id) in data["room_name"]
        
        # Verify agent type matches request
        assert data["agent_type"] == "workout"
        
        # Verify token is non-empty
        assert len(data["token"]) > 0
        
        # Verify livekit_url is present
        assert data["livekit_url"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_session_status(authenticated_client):
    """
    Test getting session status.
    
    Validates:
    - GET /api/v1/voice-sessions/{room_name}/status returns 200
    - Response contains room_name, active, participants, agent_connected
    """
    client, user = authenticated_client
    
    # Mock LiveKit API
    with patch("app.api.v1.endpoints.voice_sessions.get_livekit_api") as mock_get_api:
        mock_livekit = MagicMock()
        
        # First create a session
        room_name = f"fitness-voice-{user.id}-test5678"
        mock_room = create_mock_room(
            room_name=room_name,
            metadata='{"user_id": "' + str(user.id) + '", "agent_type": "workout", "mode": "voice", "created_at": "2026-02-08T10:00:00"}',
            num_participants=1
        )
        
        mock_livekit.room.create_room = AsyncMock(return_value=mock_room)
        mock_livekit.room.get_room = AsyncMock(return_value=mock_room)
        mock_get_api.return_value = mock_livekit
        
        # Create session
        create_response = await client.post(
            "/api/v1/voice-sessions/start",
            json={"agent_type": "workout"}
        )
        assert create_response.status_code == 200
        created_room_name = create_response.json()["room_name"]
        
        # Get session status
        status_response = await client.get(
            f"/api/v1/voice-sessions/{created_room_name}/status"
        )
        
        # Assert response
        assert status_response.status_code == 200
        data = status_response.json()
        
        # Verify response structure
        assert "room_name" in data
        assert "active" in data
        assert "participants" in data
        assert "agent_connected" in data
        
        # Verify room_name matches
        assert data["room_name"] == created_room_name
        
        # Verify status fields are correct types
        assert isinstance(data["active"], bool)
        assert isinstance(data["participants"], int)
        assert isinstance(data["agent_connected"], bool)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_end_session(authenticated_client):
    """
    Test ending a session.
    
    Validates:
    - DELETE /api/v1/voice-sessions/{room_name} returns 200
    - Response contains status="ended"
    - Subsequent status query returns 404
    """
    client, user = authenticated_client
    
    # Mock LiveKit API
    with patch("app.api.v1.endpoints.voice_sessions.get_livekit_api") as mock_get_api:
        mock_livekit = MagicMock()
        
        # Create a session first
        room_name = f"fitness-voice-{user.id}-test9abc"
        mock_room = create_mock_room(
            room_name=room_name,
            metadata='{"user_id": "' + str(user.id) + '", "agent_type": "diet", "mode": "voice", "created_at": "2026-02-08T10:00:00"}',
            num_participants=0
        )
        
        mock_livekit.room.create_room = AsyncMock(return_value=mock_room)
        mock_livekit.room.get_room = AsyncMock(return_value=mock_room)
        mock_livekit.room.delete_room = AsyncMock()
        mock_get_api.return_value = mock_livekit
        
        # Create session
        create_response = await client.post(
            "/api/v1/voice-sessions/start",
            json={"agent_type": "diet"}
        )
        assert create_response.status_code == 200
        created_room_name = create_response.json()["room_name"]
        
        # End session
        delete_response = await client.delete(
            f"/api/v1/voice-sessions/{created_room_name}"
        )
        
        # Assert response
        assert delete_response.status_code == 200
        data = delete_response.json()
        
        # Verify response structure
        assert "status" in data
        assert "room_name" in data
        
        # Verify status is "ended"
        assert data["status"] == "ended"
        assert data["room_name"] == created_room_name
        
        # Verify subsequent status query returns 404
        # Mock get_room to raise NOT_FOUND error
        mock_error = api.TwirpError(
            code=api.TwirpErrorCode.NOT_FOUND,
            msg="Room not found",
            status=404
        )
        mock_livekit.room.get_room = AsyncMock(side_effect=mock_error)
        
        status_response = await client.get(
            f"/api/v1/voice-sessions/{created_room_name}/status"
        )
        assert status_response.status_code == 404
        # The error message comes from the global error handler
        assert status_response.json()["detail"] in ["Session not found", "Resource not found"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_active_sessions(authenticated_client):
    """
    Test listing active sessions.
    
    Validates:
    - GET /api/v1/voice-sessions/active returns 200
    - sessions array contains at least 2 items
    - Each session has required fields
    """
    client, user = authenticated_client
    
    # Mock LiveKit API
    with patch("app.api.v1.endpoints.voice_sessions.get_livekit_api") as mock_get_api:
        mock_livekit = MagicMock()
        
        # Create 2 sessions with different agent types
        room1_name = f"fitness-voice-{user.id}-testdef1"
        room2_name = f"fitness-voice-{user.id}-testdef2"
        
        mock_room1 = create_mock_room(
            room_name=room1_name,
            metadata='{"user_id": "' + str(user.id) + '", "agent_type": "workout", "mode": "voice", "created_at": "2026-02-08T10:00:00"}',
            num_participants=1
        )
        
        mock_room2 = create_mock_room(
            room_name=room2_name,
            metadata='{"user_id": "' + str(user.id) + '", "agent_type": "diet", "mode": "voice", "created_at": "2026-02-08T10:15:00"}',
            num_participants=2
        )
        
        # Mock create_room to return different rooms
        call_count = [0]
        async def create_room_side_effect(*args, **kwargs):
            call_count[0] += 1
            return mock_room1 if call_count[0] == 1 else mock_room2
        
        mock_livekit.room.create_room = AsyncMock(side_effect=create_room_side_effect)
        
        # Mock list_rooms to return both rooms
        mock_livekit.room.list_rooms = AsyncMock(return_value=[mock_room1, mock_room2])
        
        mock_get_api.return_value = mock_livekit
        
        # Create first session
        response1 = await client.post(
            "/api/v1/voice-sessions/start",
            json={"agent_type": "workout"}
        )
        assert response1.status_code == 200
        
        # Create second session
        response2 = await client.post(
            "/api/v1/voice-sessions/start",
            json={"agent_type": "diet"}
        )
        assert response2.status_code == 200
        
        # List active sessions
        list_response = await client.get("/api/v1/voice-sessions/active")
        
        # Assert response
        assert list_response.status_code == 200
        data = list_response.json()
        
        # Verify response structure
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
        
        # Verify at least 2 sessions
        assert len(data["sessions"]) >= 2
        
        # Verify each session has required fields
        for session in data["sessions"]:
            assert "room_name" in session
            assert "agent_type" in session
            assert "participants" in session
            assert "created_at" in session


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unauthorized_access(client: AsyncClient):
    """
    Test unauthorized access to voice session endpoints.
    
    Validates:
    - POST /api/v1/voice-sessions/start without JWT returns 401
    """
    # Attempt to create session without authentication
    response = await client.post(
        "/api/v1/voice-sessions/start",
        json={"agent_type": "general"}
    )
    
    # Assert 401 Unauthorized
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_access_other_user_session(authenticated_client, db_session):
    """
    Test accessing another user's session.
    
    Validates:
    - User B attempting to GET status of User A's session returns 403
    - Detail contains "Not your session"
    """
    from app.core.security import hash_password, create_access_token
    from uuid import uuid4
    
    client, user_a = authenticated_client
    
    # Create User B
    user_b = User(
        id=uuid4(),
        email="userb@example.com",
        hashed_password=hash_password("password123"),
        full_name="User B",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_b)
    
    # Mock LiveKit API
    with patch("app.api.v1.endpoints.voice_sessions.get_livekit_api") as mock_get_api:
        mock_livekit = MagicMock()
        
        # User A creates a session
        room_name = f"fitness-voice-{user_a.id}-testghi1"
        mock_room = create_mock_room(
            room_name=room_name,
            metadata='{"user_id": "' + str(user_a.id) + '", "agent_type": "workout", "mode": "voice", "created_at": "2026-02-08T10:00:00"}',
            num_participants=1
        )
        
        mock_livekit.room.create_room = AsyncMock(return_value=mock_room)
        mock_livekit.room.get_room = AsyncMock(return_value=mock_room)
        mock_get_api.return_value = mock_livekit
        
        # User A creates session
        response_a = await client.post(
            "/api/v1/voice-sessions/start",
            json={"agent_type": "workout"}
        )
        assert response_a.status_code == 200
        user_a_room = response_a.json()["room_name"]
        
        # Create authenticated client for User B
        token_b = create_access_token({"user_id": str(user_b.id)})
        client.headers["Authorization"] = f"Bearer {token_b}"
        
        # User B attempts to get status of User A's session
        response_b = await client.get(
            f"/api/v1/voice-sessions/{user_a_room}/status"
        )
        
        # Assert 403 Forbidden
        assert response_b.status_code == 403
        data = response_b.json()
        assert "Not your session" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_room_not_found(authenticated_client):
    """
    Test accessing a non-existent room.
    
    Validates:
    - GET /api/v1/voice-sessions/nonexistent-room/status returns 404
    - Detail contains "Session not found"
    """
    client, user = authenticated_client
    
    # Mock LiveKit API to raise NOT_FOUND error
    with patch("app.api.v1.endpoints.voice_sessions.get_livekit_api") as mock_get_api:
        mock_livekit = MagicMock()
        
        # Mock get_room to raise NOT_FOUND error
        mock_error = api.TwirpError(
            code=api.TwirpErrorCode.NOT_FOUND,
            msg="Room not found",
            status=404
        )
        mock_livekit.room.get_room = AsyncMock(side_effect=mock_error)
        mock_get_api.return_value = mock_livekit
        
        # Attempt to get status of non-existent room
        response = await client.get(
            "/api/v1/voice-sessions/nonexistent-room-12345/status"
        )
        
        # Assert 404 Not Found
        assert response.status_code == 404
        data = response.json()
        # The error message comes from the global error handler
        assert data["detail"] in ["Session not found", "Resource not found"]
