# Sub-Doc 4: LiveKit Infrastructure Setup

## Document Information
**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Ready for Implementation  
**Parent:** [00-PHASE-2-OVERVIEW.md](./00-PHASE-2-OVERVIEW.md)  
**Dependencies:** Phase 1 (Auth), Sub-Doc 1 (Foundation)

---

## Objective

Set up LiveKit infrastructure for voice interactions:
- LiveKit server (cloud or self-hosted)
- Room management
- Access token generation
- FastAPI integration for session creation
- Client connection flow

**Note:** This sub-doc focuses on infrastructure only. Voice agent implementation is in Sub-Doc 5.

---

## Prerequisites Verification

```bash
# Verify auth system works
poetry run pytest backend/tests/test_auth_endpoints.py -v

# Verify JWT tokens work
python -c "from app.core.security import create_access_token; print('✓')"
```

---

## LiveKit Setup Options

### Option 1: LiveKit Cloud (Recommended for Development)

1. Sign up at https://cloud.livekit.io
2. Create a project
3. Get credentials:
   - `LIVEKIT_URL` (wss://your-project.livekit.cloud)
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`

### Option 2: Self-Hosted LiveKit

**File:** `docker-compose.yml` (add to existing)

```yaml
services:
  # ... existing services ...
  
  livekit:
    image: livekit/livekit-server:v1.7
    command: --config /livekit.yaml
    ports:
      - "7880:7880"   # HTTP
      - "7881:7881"   # HTTPS
      - "7882:7882"   # WebRTC
      - "50000-50100:50000-50100/udp"  # WebRTC UDP
    volumes:
      - ./livekit.yaml:/livekit.yaml
    environment:
      - LIVEKIT_KEYS=APIxxxxxx: secretxxxx
```

**File:** `livekit.yaml`

```yaml
port: 7880
rtc:
  port_range_start: 50000
  port_range_end: 50100
  use_external_ip: true

keys:
  APIxxxxxx: secretxxxx

logging:
  level: info
```

---

## Implementation Steps

### Step 1: Install LiveKit SDK

**File:** `backend/pyproject.toml`

```toml
[tool.poetry.dependencies]
livekit = "^0.17.0"
livekit-api = "^0.6.0"
```

```bash
poetry install
```

---

### Step 2: Update Configuration

**File:** `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # LiveKit Configuration
    LIVEKIT_URL: str = Field(..., description="LiveKit server URL")
    LIVEKIT_API_KEY: str = Field(..., description="LiveKit API key")
    LIVEKIT_API_SECRET: str = Field(..., description="LiveKit API secret")
    LIVEKIT_WORKER_NUM_IDLE: int = Field(default=2, description="Number of idle agent workers")
```

**File:** `backend/.env.example`

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxx
LIVEKIT_API_SECRET=secretxxxx
LIVEKIT_WORKER_NUM_IDLE=2
```

---

### Step 3: Create LiveKit Client Dependency

**File:** `backend/app/core/livekit_client.py`

```python
"""LiveKit client for room and token management"""
from livekit import api
from functools import lru_cache

from app.core.config import settings


@lru_cache()
def get_livekit_api() -> api.LiveKitAPI:
    """Get LiveKit API client (singleton)"""
    return api.LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET
    )


def create_access_token(
    identity: str,
    name: str,
    room_name: str,
    can_publish: bool = True,
    can_subscribe: bool = True,
    can_publish_data: bool = True
) -> str:
    """Create LiveKit access token for a participant
    
    Args:
        identity: Unique participant identifier (user_id)
        name: Display name
        room_name: Room to join
        can_publish: Can publish audio/video
        can_subscribe: Can subscribe to others
        can_publish_data: Can send data messages
        
    Returns:
        JWT token string
    """
    token = api.AccessToken(
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET
    )
    
    token.with_identity(identity)
    token.with_name(name)
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=can_publish,
        can_subscribe=can_subscribe,
        can_publish_data=can_publish_data
    ))
    
    # Token valid for 6 hours
    token.with_ttl(6 * 60 * 60)
    
    return token.to_jwt()
```

---

### Step 4: Create Voice Session Schemas

**File:** `backend/app/schemas/voice_session.py`

```python
"""Voice session schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VoiceSessionRequest(BaseModel):
    """Request to start a voice session"""
    agent_type: str = Field(default="general", description="workout | diet | general")


class VoiceSessionResponse(BaseModel):
    """Response with session details"""
    room_name: str
    token: str
    livekit_url: str
    agent_type: str
    expires_at: datetime


class VoiceSessionStatus(BaseModel):
    """Voice session status"""
    room_name: str
    active: bool
    participants: int
    agent_connected: bool
    created_at: Optional[datetime] = None
```

---

### Step 5: Create Voice Session Endpoints

**File:** `backend/app/api/v1/endpoints/voice_sessions.py`

```python
"""Voice session management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
import secrets
import json
import logging

from app.core.deps import get_current_user
from app.core.livekit_client import get_livekit_api, create_access_token
from app.models.user import User
from app.schemas.voice_session import (
    VoiceSessionRequest,
    VoiceSessionResponse,
    VoiceSessionStatus
)
from livekit import api

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/start", response_model=VoiceSessionResponse)
async def start_voice_session(
    request: VoiceSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a LiveKit voice session for the user
    
    This endpoint:
    1. Creates a LiveKit room with user metadata
    2. Generates access token for user
    3. Triggers agent worker dispatch (automatic via LiveKit)
    4. Returns connection details to client
    """
    
    try:
        livekit_api = get_livekit_api()
        
        # Create unique room name
        room_name = f"fitness-voice-{current_user.id}-{secrets.token_hex(4)}"
        
        # Create room with metadata
        room = await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps({
                    "user_id": str(current_user.id),
                    "agent_type": request.agent_type,
                    "mode": "voice",
                    "created_at": datetime.utcnow().isoformat()
                }),
                empty_timeout=300,  # 5 minutes
                max_participants=2  # User + agent
            )
        )
        
        logger.info(f"Created room {room_name} for user {current_user.id}")
        
        # Generate access token for user
        token = create_access_token(
            identity=str(current_user.id),
            name=current_user.email,
            room_name=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        )
        
        return VoiceSessionResponse(
            room_name=room_name,
            token=token,
            livekit_url=settings.LIVEKIT_URL,
            agent_type=request.agent_type,
            expires_at=datetime.utcnow() + timedelta(hours=6)
        )
        
    except Exception as e:
        logger.error(f"Failed to create voice session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create voice session")


@router.get("/{room_name}/status", response_model=VoiceSessionStatus)
async def get_session_status(
    room_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of active voice session"""
    
    try:
        livekit_api = get_livekit_api()
        
        # Get room info
        room = await livekit_api.room.get_room(room_name)
        
        # Check if user owns this room
        metadata = json.loads(room.metadata or "{}")
        if metadata.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not your session")
        
        return VoiceSessionStatus(
            room_name=room_name,
            active=room.num_participants > 0,
            participants=room.num_participants,
            agent_connected=room.num_participants >= 2,
            created_at=datetime.fromtimestamp(room.creation_time)
        )
        
    except api.TwirpError as e:
        if e.code == "not_found":
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{room_name}")
async def end_session(
    room_name: str,
    current_user: User = Depends(get_current_user)
):
    """End a voice session"""
    
    try:
        livekit_api = get_livekit_api()
        
        # Verify ownership
        room = await livekit_api.room.get_room(room_name)
        metadata = json.loads(room.metadata or "{}")
        if metadata.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not your session")
        
        # Delete room
        await livekit_api.room.delete_room(room_name)
        
        logger.info(f"Ended session {room_name}")
        
        return {"status": "ended", "room_name": room_name}
        
    except api.TwirpError as e:
        if e.code == "not_found":
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def list_active_sessions(
    current_user: User = Depends(get_current_user)
):
    """List user's active voice sessions"""
    
    try:
        livekit_api = get_livekit_api()
        
        # List all rooms
        rooms = await livekit_api.room.list_rooms()
        
        # Filter user's rooms
        user_rooms = []
        for room in rooms:
            metadata = json.loads(room.metadata or "{}")
            if metadata.get("user_id") == str(current_user.id):
                user_rooms.append({
                    "room_name": room.name,
                    "agent_type": metadata.get("agent_type"),
                    "participants": room.num_participants,
                    "created_at": datetime.fromtimestamp(room.creation_time).isoformat()
                })
        
        return {"sessions": user_rooms}
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sessions")
```

---

### Step 6: Register Voice Session Router

**File:** `backend/app/api/v1/__init__.py`

```python
from app.api.v1.endpoints import voice_sessions  # Add

api_router.include_router(
    voice_sessions.router,
    prefix="/voice-sessions",
    tags=["voice-sessions"]
)
```

---

### Step 7: Create Tests

**File:** `backend/tests/test_voice_sessions.py`

```python
"""Tests for voice session endpoints"""
import pytest


@pytest.mark.asyncio
async def test_create_voice_session(authenticated_client):
    """Test creating a voice session"""
    client, user = authenticated_client
    
    response = await client.post(
        "/api/v1/voice-sessions/start",
        json={"agent_type": "workout"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "room_name" in data
    assert "token" in data
    assert "livekit_url" in data
    assert data["agent_type"] == "workout"
    assert "fitness-voice" in data["room_name"]


@pytest.mark.asyncio
async def test_get_session_status(authenticated_client):
    """Test getting session status"""
    client, user = authenticated_client
    
    # Create session
    create_response = await client.post(
        "/api/v1/voice-sessions/start",
        json={"agent_type": "general"}
    )
    room_name = create_response.json()["room_name"]
    
    # Get status
    response = await client.get(f"/api/v1/voice-sessions/{room_name}/status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["room_name"] == room_name
    assert "active" in data
    assert "participants" in data


@pytest.mark.asyncio
async def test_end_session(authenticated_client):
    """Test ending a session"""
    client, user = authenticated_client
    
    # Create session
    create_response = await client.post(
        "/api/v1/voice-sessions/start",
        json={"agent_type": "diet"}
    )
    room_name = create_response.json()["room_name"]
    
    # End session
    response = await client.delete(f"/api/v1/voice-sessions/{room_name}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ended"


@pytest.mark.asyncio
async def test_list_active_sessions(authenticated_client):
    """Test listing active sessions"""
    client, user = authenticated_client
    
    # Create a session
    await client.post(
        "/api/v1/voice-sessions/start",
        json={"agent_type": "workout"}
    )
    
    # List sessions
    response = await client.get("/api/v1/voice-sessions/active")
    
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) >= 1
```

---

## Verification Checklist

- [ ] LiveKit server accessible
- [ ] LiveKit SDK installed
- [ ] Configuration updated
- [ ] Client dependency created
- [ ] Voice session endpoints implemented
- [ ] Router registered
- [ ] Tests pass
- [ ] Can create rooms
- [ ] Can generate tokens

**Final Test:**
```bash
# Test LiveKit connection
poetry run python -c "from app.core.livekit_client import get_livekit_api; print(get_livekit_api())"

# Run tests
poetry run pytest backend/tests/test_voice_sessions.py -v
```

---

## Client Integration Example

For frontend developers:

```typescript
// Example: Connect to LiveKit room
import { Room } from 'livekit-client';

async function startVoiceSession() {
  // 1. Get session from API
  const response = await fetch('/api/v1/voice-sessions/start', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ agent_type: 'workout' })
  });
  
  const { room_name, token: lkToken, livekit_url } = await response.json();
  
  // 2. Connect to LiveKit room
  const room = new Room();
  await room.connect(livekit_url, lkToken);
  
  // 3. Enable microphone
  await room.localParticipant.setMicrophoneEnabled(true);
  
  // 4. Listen for agent responses
  room.on('trackSubscribed', (track, publication, participant) => {
    if (track.kind === 'audio') {
      const audioElement = track.attach();
      document.body.appendChild(audioElement);
    }
  });
}
```

---

## Success Criteria

✅ LiveKit server accessible  
✅ Can create rooms  
✅ Can generate tokens  
✅ Endpoints working  
✅ Tests pass  
✅ API documented  

**Estimated Time:** 2-3 days

**Next:** [05-LIVEKIT-VOICE-AGENT.md](./05-LIVEKIT-VOICE-AGENT.md)
