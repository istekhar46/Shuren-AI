"""
Voice session endpoints for LiveKit-based voice coaching interactions.

This module provides REST API endpoints for managing voice coaching sessions:
- POST /start: Create a new voice session and generate access token
- GET /{room_name}/status: Query session status and participant info
- DELETE /{room_name}: End a voice session and clean up resources
- GET /active: List all active sessions for the authenticated user
"""

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from livekit import api

from app.core.deps import get_current_user
from app.core.livekit_client import get_livekit_api, create_access_token
from app.core.config import settings
from app.models.user import User
from app.schemas.voice_session import (
    VoiceSessionRequest,
    VoiceSessionResponse,
    VoiceSessionStatus,
)


# Create router for voice session endpoints
router = APIRouter()

# Logger for voice session operations
logger = logging.getLogger(__name__)


@router.post("/start", response_model=VoiceSessionResponse, status_code=status.HTTP_200_OK)
async def start_voice_session(
    request: VoiceSessionRequest,
    current_user: Annotated[User, Depends(get_current_user)]
) -> VoiceSessionResponse:
    """
    Create a new voice coaching session.
    
    This endpoint:
    1. Generates a unique LiveKit room name
    2. Creates a LiveKit room with metadata (user_id, agent_type, mode, created_at)
    3. Generates an access token for the user to join the room
    4. Returns room details and token for client connection
    
    The room is configured with:
    - empty_timeout: 300 seconds (5 minutes) - room closes if empty
    - max_participants: 2 (user + AI agent)
    
    Args:
        request: VoiceSessionRequest with agent_type
        current_user: Authenticated user from JWT token
        
    Returns:
        VoiceSessionResponse with room_name, token, livekit_url, agent_type, expires_at
        
    Raises:
        HTTPException(401): If authentication fails
        HTTPException(500): If room creation or token generation fails
    """
    try:
        # Get LiveKit API client
        livekit_api = get_livekit_api()
        
        # Generate unique room name: fitness-voice-{user_id}-{random_hex}
        room_name = f"fitness-voice-{current_user.id}-{secrets.token_hex(4)}"
        
        # Create room metadata
        metadata = {
            "user_id": str(current_user.id),
            "agent_type": request.agent_type,
            "mode": "voice",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create LiveKit room
        room = await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps(metadata),
                empty_timeout=300,  # 5 minutes
                max_participants=2  # user + agent
            )
        )
        
        # Log room creation
        logger.info(
            f"Created voice session room: {room_name} for user {current_user.id} "
            f"with agent_type={request.agent_type}"
        )
        
        # Generate access token for user
        token = create_access_token(
            identity=str(current_user.id),
            name=current_user.email,
            room_name=room_name
        )
        
        # Calculate token expiration (6 hours from now)
        expires_at = datetime.utcnow() + timedelta(hours=6)
        
        # Return session response
        return VoiceSessionResponse(
            room_name=room_name,
            token=token,
            livekit_url=settings.LIVEKIT_URL,
            agent_type=request.agent_type,
            expires_at=expires_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create voice session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create voice session"
        )


@router.get("/{room_name}/status", response_model=VoiceSessionStatus, status_code=status.HTTP_200_OK)
async def get_session_status(
    room_name: str,
    current_user: Annotated[User, Depends(get_current_user)]
) -> VoiceSessionStatus:
    """
    Get status of a voice session.
    
    This endpoint:
    1. Fetches room information from LiveKit
    2. Verifies the requesting user owns the session
    3. Returns room status including participant count and agent connection status
    
    Args:
        room_name: LiveKit room identifier
        current_user: Authenticated user from JWT token
        
    Returns:
        VoiceSessionStatus with room_name, active, participants, agent_connected, created_at
        
    Raises:
        HTTPException(401): If authentication fails
        HTTPException(403): If user does not own the session
        HTTPException(404): If room not found
        HTTPException(500): If LiveKit API error occurs
    """
    try:
        # Get LiveKit API client
        livekit_api = get_livekit_api()
        
        # Fetch room information using list_rooms with filter
        response = await livekit_api.room.list_rooms(
            api.ListRoomsRequest(names=[room_name])
        )
        
        # Check if room exists
        if not response.rooms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        room = response.rooms[0]
        
        # Parse room metadata
        try:
            metadata = json.loads(room.metadata) if room.metadata else {}
        except json.JSONDecodeError:
            metadata = {}
        
        # Verify user owns this session
        if metadata.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your session"
            )
        
        # Calculate active status (any participants connected)
        active = room.num_participants > 0
        
        # Calculate agent_connected status (2+ participants means agent joined)
        agent_connected = room.num_participants >= 2
        
        # Parse created_at timestamp
        created_at = None
        if "created_at" in metadata:
            try:
                created_at = datetime.fromisoformat(metadata["created_at"])
            except (ValueError, TypeError):
                pass
        
        # Return session status
        return VoiceSessionStatus(
            room_name=room_name,
            active=active,
            participants=room.num_participants,
            agent_connected=agent_connected,
            created_at=created_at
        )
        
    except api.TwirpError as e:
        if e.code == api.TwirpErrorCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        logger.error(f"LiveKit API error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions (403, 404)
        raise
    except Exception as e:
        logger.error(f"Failed to get session status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{room_name}", status_code=status.HTTP_200_OK)
async def end_session(
    room_name: str,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    End a voice session and delete the LiveKit room.
    
    This endpoint:
    1. Fetches room information to verify ownership
    2. Verifies the requesting user owns the session
    3. Deletes the LiveKit room
    4. Returns confirmation
    
    Args:
        room_name: LiveKit room identifier
        current_user: Authenticated user from JWT token
        
    Returns:
        dict with status="ended" and room_name
        
    Raises:
        HTTPException(401): If authentication fails
        HTTPException(403): If user does not own the session
        HTTPException(404): If room not found
        HTTPException(500): If LiveKit API error occurs
    """
    try:
        # Get LiveKit API client
        livekit_api = get_livekit_api()
        
        # Fetch room to verify ownership using list_rooms with filter
        response = await livekit_api.room.list_rooms(
            api.ListRoomsRequest(names=[room_name])
        )
        
        # Check if room exists
        if not response.rooms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        room = response.rooms[0]
        
        # Parse room metadata
        try:
            metadata = json.loads(room.metadata) if room.metadata else {}
        except json.JSONDecodeError:
            metadata = {}
        
        # Verify user owns this session
        if metadata.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your session"
            )
        
        # Delete the room
        await livekit_api.room.delete_room(
            api.DeleteRoomRequest(room=room_name)
        )
        
        # Log session termination
        logger.info(
            f"Ended voice session room: {room_name} for user {current_user.id}"
        )
        
        # Return confirmation
        return {
            "status": "ended",
            "room_name": room_name
        }
        
    except api.TwirpError as e:
        if e.code == api.TwirpErrorCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        logger.error(f"LiveKit API error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions (403, 404)
        raise
    except Exception as e:
        logger.error(f"Failed to end session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/active", status_code=status.HTTP_200_OK)
async def list_active_sessions(
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    List all active voice sessions for the authenticated user.
    
    This endpoint:
    1. Fetches all LiveKit rooms
    2. Filters rooms to only include those owned by the requesting user
    3. Returns list of session summaries
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        dict with "sessions" key containing list of session dicts
        Each session dict contains: room_name, agent_type, participants, created_at
        
    Raises:
        HTTPException(401): If authentication fails
        HTTPException(500): If LiveKit API error occurs
    """
    try:
        # Get LiveKit API client
        livekit_api = get_livekit_api()
        
        # List all rooms
        response = await livekit_api.room.list_rooms(api.ListRoomsRequest())
        
        # Filter and build session list
        sessions = []
        for room in response.rooms:
            try:
                # Parse room metadata
                metadata = json.loads(room.metadata) if room.metadata else {}
                
                # Only include rooms owned by current user
                if metadata.get("user_id") == str(current_user.id):
                    # Parse created_at timestamp
                    created_at = None
                    if "created_at" in metadata:
                        try:
                            created_at = datetime.fromisoformat(metadata["created_at"])
                        except (ValueError, TypeError):
                            pass
                    
                    # Build session summary
                    session = {
                        "room_name": room.name,
                        "agent_type": metadata.get("agent_type", "general"),
                        "participants": room.num_participants,
                        "created_at": created_at.isoformat() if created_at else None
                    }
                    sessions.append(session)
                    
            except json.JSONDecodeError:
                # Skip rooms with invalid metadata
                continue
        
        # Return sessions list
        return {"sessions": sessions}
        
    except Exception as e:
        logger.error(f"Failed to list active sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list active sessions"
        )
