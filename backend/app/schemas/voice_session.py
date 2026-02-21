"""Voice Session API Pydantic schemas for LiveKit voice interactions"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VoiceSessionRequest(BaseModel):
    """
    Schema for requesting a new voice coaching session.
    
    The agent_type determines which specialized AI agent will handle
    the voice interaction (workout, diet, supplement, tracker, scheduler, or general).
    """
    agent_type: str = Field(
        default="general",
        description="Type of agent: workout | diet | supplement | tracker | scheduler | general"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "workout"
            }
        }


class VoiceSessionResponse(BaseModel):
    """
    Schema for voice session creation response.
    
    Contains all information needed for the client to connect to the LiveKit room,
    including the access token, room name, and session metadata.
    """
    room_name: str = Field(
        ...,
        description="Unique LiveKit room identifier"
    )
    token: str = Field(
        ...,
        description="LiveKit access token (JWT) for joining the room"
    )
    livekit_url: str = Field(
        ...,
        description="WebSocket URL for LiveKit connection"
    )
    agent_type: str = Field(
        ...,
        description="Type of agent that will handle this session"
    )
    expires_at: datetime = Field(
        ...,
        description="Token expiration timestamp (UTC)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "room_name": "fitness-voice-123e4567-e89b-12d3-a456-426614174000-a1b2c3d4",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "livekit_url": "wss://your-project.livekit.cloud",
                "agent_type": "workout",
                "expires_at": "2026-02-07T16:30:00Z"
            }
        }


class VoiceSessionStatus(BaseModel):
    """
    Schema for voice session status information.
    
    Provides real-time status of a LiveKit room including participant count,
    connection status, and whether the AI agent has joined the session.
    """
    room_name: str = Field(
        ...,
        description="LiveKit room identifier"
    )
    active: bool = Field(
        ...,
        description="True if any participants are currently connected to the room"
    )
    participants: int = Field(
        ...,
        description="Number of current participants in the room"
    )
    agent_connected: bool = Field(
        ...,
        description="True if the AI agent has joined the room (participants >= 2)"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Room creation timestamp (UTC)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "room_name": "fitness-voice-123e4567-e89b-12d3-a456-426614174000-a1b2c3d4",
                "active": True,
                "participants": 2,
                "agent_connected": True,
                "created_at": "2026-02-07T09:30:00Z"
            }
        }
