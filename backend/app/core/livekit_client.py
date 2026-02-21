"""
LiveKit client module for room management and access token generation.

This module provides a singleton LiveKit API client and utilities for
generating access tokens for participants to join LiveKit rooms.
"""

from datetime import timedelta
from functools import lru_cache
from livekit import api

from app.core.config import settings


@lru_cache()
def get_livekit_api() -> api.LiveKitAPI:
    """
    Get LiveKit API client (singleton pattern).
    
    This function creates and caches a single instance of the LiveKit API client
    for the lifetime of the application. The singleton pattern ensures efficient
    resource usage and connection pooling.
    
    The client is initialized with credentials from the application settings:
    - LIVEKIT_URL: WebSocket URL for LiveKit server
    - LIVEKIT_API_KEY: API key for authentication
    - LIVEKIT_API_SECRET: API secret for signing requests
    
    Returns:
        api.LiveKitAPI: Singleton LiveKit API client instance
        
    Example:
        >>> livekit_api = get_livekit_api()
        >>> room = await livekit_api.room.create_room("my-room")
    """
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
    """
    Create LiveKit access token for a participant.
    
    Generates a JWT token that grants a participant permission to join a specific
    LiveKit room with specified capabilities. The token is signed with the
    LiveKit API secret and includes identity, name, and room grants.
    
    Args:
        identity: Unique identifier for the participant (typically user_id)
        name: Display name for the participant (typically email or username)
        room_name: Name of the LiveKit room the participant can join
        can_publish: Whether participant can publish audio/video tracks (default: True)
        can_subscribe: Whether participant can subscribe to other tracks (default: True)
        can_publish_data: Whether participant can publish data messages (default: True)
        
    Returns:
        str: JWT token string that can be used to connect to the LiveKit room
        
    Example:
        >>> token = create_access_token(
        ...     identity="user-123",
        ...     name="john@example.com",
        ...     room_name="fitness-voice-123-abc123"
        ... )
        >>> # Client uses this token to connect to LiveKit room
    
    Note:
        - Token has a time-to-live (TTL) of 6 hours (21600 seconds)
        - Token is scoped to a specific room (cannot join other rooms)
        - Identity claim prevents participant impersonation
        - Token must be kept secure and not exposed in logs
    """
    # Create access token with API credentials
    token = api.AccessToken(
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET
    )
    
    # Set participant identity and name
    token.with_identity(identity)
    token.with_name(name)
    
    # Create video grants with room permissions
    grants = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=can_publish,
        can_subscribe=can_subscribe,
        can_publish_data=can_publish_data
    )
    
    # Apply grants to token
    token.with_grants(grants)
    
    # Set token expiration to 6 hours
    token.with_ttl(timedelta(hours=6))
    
    # Generate and return JWT string
    return token.to_jwt()
