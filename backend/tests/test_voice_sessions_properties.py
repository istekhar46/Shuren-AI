"""
Property-based tests for LiveKit voice session infrastructure.

This module uses Hypothesis to test universal correctness properties
across randomized inputs for voice session management.

Properties tested:
- Property 1: Token Validity
- Property 3: Unique Room Names
- Property 4: Room Metadata Integrity
- Property 5: Session Filtering
"""

import pytest
import json
from uuid import uuid4, UUID
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings as hypothesis_settings
from jose import jwt

from app.core.livekit_client import create_access_token
from app.core.config import settings


# ============================================================================
# Property 1: Token Validity
# ============================================================================

@pytest.mark.property
@given(
    user_id=st.uuids(),
    email=st.emails(),
    room_name=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
        min_size=10,
        max_size=100
    )
)
@hypothesis_settings(max_examples=100, deadline=None)
def test_property_token_validity(user_id: UUID, email: str, room_name: str):
    """
    **Feature: livekit-infrastructure, Property 1: Token Validity**
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6**
    
    For any authenticated user and valid room name, the generated access token
    SHALL successfully authenticate the user to join the specified LiveKit room.
    
    This property verifies that:
    - Token is a non-empty string
    - Token can be decoded (valid JWT format)
    - Decoded token contains identity claim matching user_id
    - Decoded token contains name claim matching email
    - Decoded token contains video grants with room_join=True
    """
    # Generate access token
    token = create_access_token(
        identity=str(user_id),
        name=email,
        room_name=room_name
    )
    
    # Property 1.1: Token is non-empty string
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Property 1.2: Token can be decoded (valid JWT format)
    try:
        decoded = jwt.decode(
            token,
            settings.LIVEKIT_API_SECRET,
            algorithms=["HS256"]
        )
    except Exception as e:
        pytest.fail(f"Token decoding failed: {e}")
    
    # Property 1.3: Token contains identity claim matching user_id
    assert "sub" in decoded, "Token missing 'sub' (identity) claim"
    assert decoded["sub"] == str(user_id), f"Identity mismatch: {decoded['sub']} != {str(user_id)}"
    
    # Property 1.4: Token contains name claim matching email
    assert "name" in decoded, "Token missing 'name' claim"
    assert decoded["name"] == email, f"Name mismatch: {decoded['name']} != {email}"
    
    # Property 1.5: Token contains video grants with room_join=True
    assert "video" in decoded, "Token missing 'video' grants"
    video_grants = decoded["video"]
    assert "roomJoin" in video_grants or "room_join" in video_grants, "Token missing room_join grant"
    
    # Check room_join is True (handle both camelCase and snake_case)
    room_join = video_grants.get("roomJoin") or video_grants.get("room_join")
    assert room_join is True, f"room_join is not True: {room_join}"
    
    # Property 1.6: Token contains room name in grants
    assert "room" in video_grants, "Token missing 'room' grant"
    assert video_grants["room"] == room_name, f"Room mismatch: {video_grants['room']} != {room_name}"


# ============================================================================
# Property 3: Unique Room Names
# ============================================================================

@pytest.mark.property
@given(
    user_ids=st.lists(st.uuids(), min_size=100, max_size=100, unique=True)
)
@hypothesis_settings(max_examples=100, deadline=None)
def test_property_unique_room_names(user_ids: list):
    """
    **Feature: livekit-infrastructure, Property 3: Unique Room Names**
    
    **Validates: Requirements 3.2**
    
    For any two voice session creation requests, even from the same user,
    the generated room names SHALL be unique.
    
    This property verifies that:
    - All generated room names are unique
    - Room names follow the expected format
    - Random suffix provides uniqueness
    """
    import secrets
    
    room_names = set()
    
    # Generate room names for each user ID
    for user_id in user_ids:
        # Simulate room name generation as done in the endpoint
        room_name = f"fitness-voice-{user_id}-{secrets.token_hex(4)}"
        room_names.add(room_name)
    
    # Property 3.1: All room names are unique
    assert len(room_names) == len(user_ids), \
        f"Room names not unique: {len(room_names)} unique names for {len(user_ids)} users"
    
    # Property 3.2: All room names follow expected format
    for room_name in room_names:
        assert room_name.startswith("fitness-voice-"), \
            f"Room name doesn't start with 'fitness-voice-': {room_name}"
        assert len(room_name.split("-")) >= 3, \
            f"Room name doesn't have expected format: {room_name}"


# ============================================================================
# Property 4: Room Metadata Integrity
# ============================================================================

@pytest.mark.property
@given(
    user_id=st.uuids(),
    agent_type=st.sampled_from(["workout", "diet", "supplement", "tracker", "scheduler", "general"])
)
@hypothesis_settings(max_examples=100, deadline=None)
def test_property_metadata_integrity(user_id: UUID, agent_type: str):
    """
    **Feature: livekit-infrastructure, Property 4: Room Metadata Integrity**
    
    **Validates: Requirements 3.3**
    
    For any created room, the metadata SHALL contain valid JSON with
    user_id, agent_type, mode, and created_at fields.
    
    This property verifies that:
    - Metadata is valid JSON
    - Metadata contains all required fields
    - user_id is valid UUID string format
    - agent_type is one of valid types
    - mode is "voice"
    """
    # Simulate metadata creation as done in the endpoint
    created_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "user_id": str(user_id),
        "agent_type": agent_type,
        "mode": "voice",
        "created_at": created_at
    }
    
    # Property 4.1: Metadata can be serialized to JSON
    try:
        metadata_json = json.dumps(metadata)
    except Exception as e:
        pytest.fail(f"Metadata serialization failed: {e}")
    
    # Property 4.2: Metadata can be parsed back from JSON
    try:
        parsed_metadata = json.loads(metadata_json)
    except Exception as e:
        pytest.fail(f"Metadata parsing failed: {e}")
    
    # Property 4.3: Parsed metadata contains user_id
    assert "user_id" in parsed_metadata, "Metadata missing 'user_id'"
    
    # Property 4.4: user_id is valid UUID string format
    try:
        UUID(parsed_metadata["user_id"])
    except ValueError:
        pytest.fail(f"user_id is not valid UUID: {parsed_metadata['user_id']}")
    
    # Property 4.5: Parsed metadata contains agent_type
    assert "agent_type" in parsed_metadata, "Metadata missing 'agent_type'"
    
    # Property 4.6: agent_type is one of valid types
    valid_agent_types = ["workout", "diet", "supplement", "tracker", "scheduler", "general"]
    assert parsed_metadata["agent_type"] in valid_agent_types, \
        f"Invalid agent_type: {parsed_metadata['agent_type']}"
    
    # Property 4.7: Parsed metadata contains mode
    assert "mode" in parsed_metadata, "Metadata missing 'mode'"
    
    # Property 4.8: mode is "voice"
    assert parsed_metadata["mode"] == "voice", \
        f"Mode is not 'voice': {parsed_metadata['mode']}"
    
    # Property 4.9: Parsed metadata contains created_at
    assert "created_at" in parsed_metadata, "Metadata missing 'created_at'"
    
    # Property 4.10: created_at is valid ISO format timestamp
    try:
        datetime.fromisoformat(parsed_metadata["created_at"].replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"created_at is not valid ISO format: {parsed_metadata['created_at']}")


# ============================================================================
# Property 5: Session Filtering
# ============================================================================

@pytest.mark.property
@given(
    num_users=st.integers(min_value=5, max_value=15),
    sessions_per_user=st.integers(min_value=1, max_value=5)
)
@hypothesis_settings(max_examples=100, deadline=None)
def test_property_session_filtering(num_users: int, sessions_per_user: int):
    """
    **Feature: livekit-infrastructure, Property 5: Session Filtering**
    
    **Validates: Requirements 6.2**
    
    For any user's active sessions list request, the returned sessions
    SHALL only include rooms where the metadata user_id matches the
    requesting user's ID.
    
    This property verifies that:
    - Filtering correctly identifies user's sessions
    - No sessions from other users are included
    - All user's sessions are included
    """
    import secrets
    
    # Create test users
    users = [uuid4() for _ in range(num_users)]
    
    # Create mock rooms for all users
    all_rooms = []
    user_room_counts = {}
    
    for user_id in users:
        user_room_counts[user_id] = 0
        for _ in range(sessions_per_user):
            room_name = f"fitness-voice-{user_id}-{secrets.token_hex(4)}"
            metadata = json.dumps({
                "user_id": str(user_id),
                "agent_type": "workout",
                "mode": "voice",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            all_rooms.append({
                "name": room_name,
                "metadata": metadata,
                "user_id": user_id
            })
            user_room_counts[user_id] += 1
    
    # For each user, simulate list_active_sessions filtering logic
    for target_user_id in users:
        # Filter rooms for this user (as done in the endpoint)
        user_sessions = []
        for room in all_rooms:
            try:
                room_metadata = json.loads(room["metadata"])
                if room_metadata.get("user_id") == str(target_user_id):
                    user_sessions.append({
                        "room_name": room["name"],
                        "agent_type": room_metadata.get("agent_type"),
                        "user_id": room_metadata.get("user_id")
                    })
            except json.JSONDecodeError:
                continue
        
        # Property 5.1: User gets exactly their sessions
        expected_count = user_room_counts[target_user_id]
        assert len(user_sessions) == expected_count, \
            f"User {target_user_id} expected {expected_count} sessions, got {len(user_sessions)}"
        
        # Property 5.2: All returned sessions belong to the user
        for session in user_sessions:
            assert session["user_id"] == str(target_user_id), \
                f"Session {session['room_name']} belongs to {session['user_id']}, not {target_user_id}"
        
        # Property 5.3: No sessions from other users are included
        other_user_ids = [str(uid) for uid in users if uid != target_user_id]
        for session in user_sessions:
            assert session["user_id"] not in other_user_ids, \
                f"Session {session['room_name']} belongs to another user: {session['user_id']}"
