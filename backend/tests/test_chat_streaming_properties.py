"""
Property-based tests for chat text streaming feature.

This module tests universal correctness properties of the streaming implementation
using Hypothesis for property-based testing with 100+ iterations per property.

Feature: chat-text-streaming
"""

import json
import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import AsyncGenerator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.user import User
from app.models.onboarding import OnboardingState
from app.models.profile import UserProfile
from app.models.conversation import ConversationMessage
from app.core.security import create_access_token
from sqlalchemy import select


# ============================================================================
# Property 1: SSE Format Compliance
# Feature: chat-text-streaming, Property 1: SSE Format Compliance
# Validates: Requirements 1.1, 1.2, 1.4, 1.5, 1.8
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.property
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    message=st.text(min_size=1, max_size=200, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
        blacklist_characters='\n\r\t'
    ))
)
async def test_property_sse_format_compliance(
    message: str,
    authenticated_client_with_profile: tuple[AsyncClient, User],
    db_session: AsyncSession
):
    """
    Property 1: SSE Format Compliance
    
    For any streaming request (regular or onboarding), all events sent by the 
    backend should follow the SSE specification format:
    - Chunk events as `data: {"chunk": "text"}\n\n`
    - Completion events as `data: {"done": true, "agent_type": "name"}\n\n`
    - Error events as `data: {"error": "message"}\n\n`
    
    Feature: chat-text-streaming, Property 1: SSE Format Compliance
    Validates: Requirements 1.1, 1.2, 1.4, 1.5, 1.8
    """
    client, user = authenticated_client_with_profile
    
    # Test regular chat streaming endpoint
    response = await client.post(
        "/api/v1/chat/stream",
        json={"message": message}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Parse SSE events
    events = []
    content = response.text
    
    # Split by double newline to get individual events
    raw_events = content.strip().split('\n\n')
    
    for raw_event in raw_events:
        if raw_event.startswith('data: '):
            event_data = raw_event[6:]  # Remove 'data: ' prefix
            try:
                parsed_data = json.loads(event_data)
                events.append(parsed_data)
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON in SSE event: {event_data}")
    
    # Verify at least one event was sent
    assert len(events) > 0, "No events received from stream"
    
    # Verify all events follow SSE format
    for event in events:
        assert isinstance(event, dict), f"Event is not a dict: {event}"
        
        # Each event must have exactly one of: chunk, done, or error
        keys = set(event.keys())
        valid_keys = {'chunk', 'done', 'error', 'agent_type'}
        
        assert keys.issubset(valid_keys), f"Invalid keys in event: {keys}"
        
        # Verify event type
        if 'chunk' in event:
            # Chunk event
            assert isinstance(event['chunk'], str), "Chunk must be a string"
        elif 'done' in event:
            # Completion event
            assert event['done'] is True, "Done must be True"
            assert 'agent_type' in event, "Completion event must include agent_type"
            assert isinstance(event['agent_type'], str), "Agent type must be a string"
        elif 'error' in event:
            # Error event
            assert isinstance(event['error'], str), "Error must be a string"
        else:
            pytest.fail(f"Event has no valid type indicator: {event}")
    
    # Verify last event is a completion or error event
    last_event = events[-1]
    assert 'done' in last_event or 'error' in last_event, \
        "Last event must be completion or error"


# ============================================================================
# Property 2: Streaming Persistence Round-Trip
# Feature: chat-text-streaming, Property 2: Streaming Persistence Round-Trip
# Validates: Requirements 1.6
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.property
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    message=st.text(min_size=1, max_size=200, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
        blacklist_characters='\n\r\t'
    ))
)
async def test_property_streaming_persistence_round_trip(
    message: str,
    authenticated_client_with_profile: tuple[AsyncClient, User],
    db_session: AsyncSession
):
    """
    Property 2: Streaming Persistence Round-Trip
    
    For any message that is streamed, after streaming completes, querying the 
    database should return the complete accumulated response.
    
    Feature: chat-text-streaming, Property 2: Streaming Persistence Round-Trip
    Validates: Requirements 1.6
    """
    client, user = authenticated_client_with_profile
    
    # Stream a message
    response = await client.post(
        "/api/v1/chat/stream",
        json={"message": message}
    )
    
    assert response.status_code == 200
    
    # Parse SSE events and accumulate chunks
    accumulated_response = ""
    content = response.text
    raw_events = content.strip().split('\n\n')
    
    for raw_event in raw_events:
        if raw_event.startswith('data: '):
            event_data = raw_event[6:]
            try:
                parsed_data = json.loads(event_data)
                if 'chunk' in parsed_data:
                    accumulated_response += parsed_data['chunk']
            except json.JSONDecodeError:
                pass
    
    # Query database for the conversation
    stmt = select(ConversationMessage).where(
        ConversationMessage.user_id == user.id,
        ConversationMessage.role == 'assistant'
    ).order_by(ConversationMessage.created_at.desc()).limit(1)
    
    result = await db_session.execute(stmt)
    db_message = result.scalar_one_or_none()
    
    # Verify message was saved to database
    assert db_message is not None, "Message not found in database"
    
    # Verify database content matches accumulated response
    assert db_message.content == accumulated_response, \
        f"Database content mismatch. Expected: {accumulated_response}, Got: {db_message.content}"
    
    # Verify user message was also saved
    stmt = select(ConversationMessage).where(
        ConversationMessage.user_id == user.id,
        ConversationMessage.role == 'user'
    ).order_by(ConversationMessage.created_at.desc()).limit(1)
    
    result = await db_session.execute(stmt)
    user_message = result.scalar_one_or_none()
    
    assert user_message is not None, "User message not found in database"
    assert user_message.content == message, \
        f"User message content mismatch. Expected: {message}, Got: {user_message.content}"


# ============================================================================
# Helper Functions
# ============================================================================


def parse_sse_events(content: str) -> list[dict]:
    """Parse SSE event stream content into list of event dictionaries.
    
    Args:
        content: Raw SSE stream content
        
    Returns:
        List of parsed event dictionaries
    """
    events = []
    raw_events = content.strip().split('\n\n')
    
    for raw_event in raw_events:
        if raw_event.startswith('data: '):
            event_data = raw_event[6:]
            try:
                parsed_data = json.loads(event_data)
                events.append(parsed_data)
            except json.JSONDecodeError:
                # Skip invalid JSON
                pass
    
    return events
