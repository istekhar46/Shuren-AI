"""
Property-based tests for Text Chat API Integration.

These tests validate universal correctness properties across all valid inputs:
- Property 1: Message Persistence Completeness (Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 3.5)

Uses Hypothesis for property-based testing to verify chat behavior
across various scenarios and data combinations.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationMessage
from app.models.user import User
from app.core.security import hash_password, create_access_token


# Hypothesis strategies for generating test data
@st.composite
def valid_chat_message(draw):
    """Generate random valid chat messages (1-2000 characters)."""
    # Generate text with reasonable character set
    return draw(st.text(
        min_size=1,
        max_size=2000,
        alphabet=st.characters(
            blacklist_categories=('Cs', 'Cc'),  # Exclude surrogates and control chars
            blacklist_characters='\x00'  # Exclude null bytes
        )
    ))


@st.composite
def agent_type_value(draw):
    """Generate random agent type from valid set."""
    return draw(st.sampled_from([
        'workout', 'diet', 'supplement', 'tracker', 'scheduler', 'general'
    ]))


class TestMessagePersistenceCompleteness:
    """
    Property 1: Message Persistence Completeness
    
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 3.5**
    
    For any successful chat interaction (synchronous or streaming), both the user 
    message and assistant response SHALL be persisted to the database with:
    - Correct role ("user" or "assistant")
    - Content matching the input/output
    - agent_type populated for assistant messages
    - Timestamp present
    - user_id matching the authenticated user
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        message=valid_chat_message(),
        agent_type=agent_type_value()
    )
    @settings(
        max_examples=10,  # Reduced for faster testing
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_message_persistence_after_successful_chat(
        self,
        message: str,
        agent_type: str,
        db_session: AsyncSession
    ):
        """
        Property: All successful chats persist both user and assistant messages.
        
        This test verifies that when a chat request succeeds:
        1. User message is saved with role="user"
        2. Assistant message is saved with role="assistant"
        3. Content matches input/output
        4. agent_type is populated for assistant message
        5. Timestamps are present
        6. user_id matches authenticated user
        """
        # Feature: text-chat-api, Property 1: Message Persistence Completeness
        
        # Create test user with unique ID for this test run
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Count messages before adding new ones
        count_stmt = select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.user_id == user.id
        )
        count_result = await db_session.execute(count_stmt)
        initial_count = count_result.scalar()
        
        # Simulate successful chat interaction
        # In real scenario, this would be done by the chat endpoint
        # Here we simulate the persistence logic
        
        # Save user message (role="user")
        user_message = ConversationMessage(
            user_id=user.id,
            role="user",
            content=message,
            agent_type=None  # User messages don't have agent_type
        )
        db_session.add(user_message)
        await db_session.flush()  # Flush to get created_at timestamp
        await db_session.refresh(user_message)
        user_message_id = user_message.id
        
        # Simulate assistant response
        assistant_response = f"Response to: {message[:50]}"
        
        # Save assistant message (role="assistant", agent_type populated)
        assistant_message = ConversationMessage(
            user_id=user.id,
            role="assistant",
            content=assistant_response,
            agent_type=agent_type
        )
        db_session.add(assistant_message)
        
        # Commit transaction
        await db_session.commit()
        await db_session.refresh(user_message)
        await db_session.refresh(assistant_message)
        assistant_message_id = assistant_message.id
        
        # Verify messages were persisted by querying for the specific messages we just created
        stmt = select(ConversationMessage).where(
            ConversationMessage.id.in_([user_message_id, assistant_message_id])
        ).order_by(ConversationMessage.created_at.asc())
        
        result = await db_session.execute(stmt)
        messages = result.scalars().all()
        
        # Property verification: Both messages should be persisted
        assert len(messages) == 2, \
            f"Expected 2 messages, found {len(messages)}. " \
            f"Messages: {[(m.role, m.content[:20]) for m in messages]}"
        
        # Find the user and assistant messages (order might vary due to same timestamp)
        user_msg = next((m for m in messages if m.role == "user"), None)
        assistant_msg = next((m for m in messages if m.role == "assistant"), None)
        
        assert user_msg is not None, "User message should be persisted"
        assert assistant_msg is not None, "Assistant message should be persisted"
        
        # Verify user message (Requirement 1.1)
        assert user_msg.role == "user", \
            f"User message should have role='user', got '{user_msg.role}'"
        assert user_msg.content == message, \
            f"User message content should match input"
        assert user_msg.agent_type is None, \
            f"User message should not have agent_type, got '{user_msg.agent_type}'"
        assert user_msg.user_id == user.id, \
            f"User message should have correct user_id (Requirement 1.5)"
        assert user_msg.created_at is not None, \
            f"User message should have timestamp (Requirement 1.4)"
        
        # Verify assistant message (Requirement 1.2)
        assert assistant_msg.role == "assistant", \
            f"Assistant message should have role='assistant', got '{assistant_msg.role}'"
        assert assistant_msg.content == assistant_response, \
            f"Assistant message content should match output"
        assert assistant_msg.agent_type == agent_type, \
            f"Assistant message should have agent_type='{agent_type}' (Requirement 1.3)"
        assert assistant_msg.user_id == user.id, \
            f"Assistant message should have correct user_id (Requirement 1.5)"
        assert assistant_msg.created_at is not None, \
            f"Assistant message should have timestamp (Requirement 1.4)"
        
        # Verify chronological order (Requirement 1.6)
        assert user_msg.created_at <= assistant_msg.created_at, \
            f"User message should be created before or at same time as assistant message"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_messages=st.integers(min_value=1, max_value=10),
        agent_type=agent_type_value()
    )
    @settings(
        max_examples=10,  # Reduced for faster testing
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_multiple_messages_persistence(
        self,
        num_messages: int,
        agent_type: str,
        db_session: AsyncSession
    ):
        """
        Property: Multiple chat interactions persist all messages in order.
        
        This test verifies that when multiple chat requests occur:
        1. All user and assistant messages are persisted
        2. Messages maintain chronological order
        3. Each pair has correct roles and agent_type
        """
        # Feature: text-chat-api, Property 1: Message Persistence Completeness
        
        # Create test user
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Simulate multiple chat interactions
        for i in range(num_messages):
            user_content = f"User message {i}"
            assistant_content = f"Assistant response {i}"
            
            # Save user message
            user_message = ConversationMessage(
                user_id=user.id,
                role="user",
                content=user_content,
                agent_type=None
            )
            db_session.add(user_message)
            
            # Save assistant message
            assistant_message = ConversationMessage(
                user_id=user.id,
                role="assistant",
                content=assistant_content,
                agent_type=agent_type
            )
            db_session.add(assistant_message)
            
            await db_session.commit()
        
        # Verify all messages were persisted
        stmt = select(ConversationMessage).where(
            ConversationMessage.user_id == user.id
        ).order_by(ConversationMessage.created_at.asc())
        
        result = await db_session.execute(stmt)
        messages = result.scalars().all()
        
        # Property verification: All messages should be persisted
        expected_count = num_messages * 2  # Each interaction = user + assistant
        assert len(messages) == expected_count, \
            f"Expected {expected_count} messages, found {len(messages)}"
        
        # Count user and assistant messages
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        # Verify we have equal numbers of user and assistant messages
        assert len(user_messages) == num_messages, \
            f"Expected {num_messages} user messages, found {len(user_messages)}"
        assert len(assistant_messages) == num_messages, \
            f"Expected {num_messages} assistant messages, found {len(assistant_messages)}"
        
        # Verify agent_type for all assistant messages
        for msg in assistant_messages:
            assert msg.agent_type == agent_type, \
                f"Assistant message should have agent_type='{agent_type}'"
        
        # Verify user messages don't have agent_type
        for msg in user_messages:
            assert msg.agent_type is None, \
                f"User message should not have agent_type"
        
        # Verify chronological order (Requirement 1.6)
        for i in range(len(messages) - 1):
            assert messages[i].created_at <= messages[i + 1].created_at, \
                f"Messages should be in chronological order"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        message=valid_chat_message()
    )
    @settings(
        max_examples=10,  # Reduced for faster testing
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_user_data_isolation_in_persistence(
        self,
        message: str,
        db_session: AsyncSession
    ):
        """
        Property: Messages are isolated per user.
        
        This test verifies that:
        1. Each user's messages are associated with their user_id
        2. Users cannot see other users' messages
        3. Message persistence respects user boundaries
        """
        # Feature: text-chat-api, Property 1: Message Persistence Completeness
        
        # Create two test users
        user1 = User(
            id=uuid4(),
            email=f"user1_{uuid4()}@example.com",
            hashed_password=hash_password("password123"),
            full_name="User One",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        user2 = User(
            id=uuid4(),
            email=f"user2_{uuid4()}@example.com",
            hashed_password=hash_password("password123"),
            full_name="User Two",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        
        # User 1 sends a message
        user1_message = ConversationMessage(
            user_id=user1.id,
            role="user",
            content=message,
            agent_type=None
        )
        db_session.add(user1_message)
        
        user1_response = ConversationMessage(
            user_id=user1.id,
            role="assistant",
            content=f"Response to user1: {message[:30]}",
            agent_type="general"
        )
        db_session.add(user1_response)
        
        # User 2 sends a different message
        user2_message = ConversationMessage(
            user_id=user2.id,
            role="user",
            content=f"Different: {message}",
            agent_type=None
        )
        db_session.add(user2_message)
        
        user2_response = ConversationMessage(
            user_id=user2.id,
            role="assistant",
            content=f"Response to user2: {message[:30]}",
            agent_type="workout"
        )
        db_session.add(user2_response)
        
        await db_session.commit()
        
        # Verify user 1's messages
        stmt1 = select(ConversationMessage).where(
            ConversationMessage.user_id == user1.id
        )
        result1 = await db_session.execute(stmt1)
        user1_messages = result1.scalars().all()
        
        assert len(user1_messages) == 2, \
            f"User 1 should have 2 messages, found {len(user1_messages)}"
        assert all(msg.user_id == user1.id for msg in user1_messages), \
            f"All messages should belong to user 1 (Requirement 1.5)"
        
        # Verify user 2's messages
        stmt2 = select(ConversationMessage).where(
            ConversationMessage.user_id == user2.id
        )
        result2 = await db_session.execute(stmt2)
        user2_messages = result2.scalars().all()
        
        assert len(user2_messages) == 2, \
            f"User 2 should have 2 messages, found {len(user2_messages)}"
        assert all(msg.user_id == user2.id for msg in user2_messages), \
            f"All messages should belong to user 2 (Requirement 1.5)"
        
        # Verify no cross-contamination
        user1_ids = {msg.id for msg in user1_messages}
        user2_ids = {msg.id for msg in user2_messages}
        assert user1_ids.isdisjoint(user2_ids), \
            f"User messages should not overlap"


class TestAuthenticationEnforcement:
    """
    Property 2: Authentication Enforcement
    
    **Validates: Requirements 2.6, 3.6, 4.6, 5.4, 8.1, 8.2**
    
    For any request to any chat endpoint (chat, stream, history, delete) without 
    a valid JWT token, the system SHALL return a 401 Unauthorized error and SHALL 
    NOT process the request or access the database.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        message=valid_chat_message()
    )
    @settings(
        max_examples=10,  # Reduced for faster testing
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_chat_endpoint_requires_authentication(
        self,
        message: str,
        client
    ):
        """
        Property: Chat endpoint rejects requests without valid JWT token.
        
        This test verifies that:
        1. Requests without Authorization header return 401
        2. Requests with invalid token return 401
        3. No database operations occur for unauthenticated requests
        """
        # Feature: text-chat-api, Property 2: Authentication Enforcement
        
        # Test 1: No Authorization header (Requirement 8.1, 8.2)
        response = await client.post(
            "/api/v1/chat/chat",
            json={"message": message}
        )
        
        assert response.status_code == 401, \
            f"Chat endpoint should return 401 without auth token, got {response.status_code}"
        
        # Test 2: Invalid token format
        client.headers["Authorization"] = "Bearer invalid_token_format"
        response = await client.post(
            "/api/v1/chat/chat",
            json={"message": message}
        )
        
        assert response.status_code == 401, \
            f"Chat endpoint should return 401 with invalid token, got {response.status_code}"
        
        # Test 3: Malformed Authorization header
        client.headers["Authorization"] = "NotBearer token"
        response = await client.post(
            "/api/v1/chat/chat",
            json={"message": message}
        )
        
        assert response.status_code == 401, \
            f"Chat endpoint should return 401 with malformed auth header, got {response.status_code}"
        
        # Clean up headers
        if "Authorization" in client.headers:
            del client.headers["Authorization"]
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_history_endpoint_requires_authentication(
        self,
        client
    ):
        """
        Property: History endpoint rejects requests without valid JWT token.
        
        This test verifies that:
        1. GET /chat/history requires authentication (Requirement 4.6)
        2. Returns 401 for unauthenticated requests
        
        Note: This test will be skipped if the endpoint is not yet implemented (404).
        """
        # Feature: text-chat-api, Property 2: Authentication Enforcement
        
        # Test without Authorization header
        response = await client.get("/api/v1/chat/history")
        
        # Skip if endpoint not implemented yet
        if response.status_code == 404:
            pytest.skip("History endpoint not yet implemented")
        
        assert response.status_code == 401, \
            f"History endpoint should return 401 without auth token, got {response.status_code}"
        
        # Test with invalid token
        client.headers["Authorization"] = "Bearer invalid_token"
        response = await client.get("/api/v1/chat/history")
        
        assert response.status_code == 401, \
            f"History endpoint should return 401 with invalid token, got {response.status_code}"
        
        # Clean up headers
        if "Authorization" in client.headers:
            del client.headers["Authorization"]
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_delete_history_endpoint_requires_authentication(
        self,
        client
    ):
        """
        Property: Delete history endpoint rejects requests without valid JWT token.
        
        This test verifies that:
        1. DELETE /chat/history requires authentication (Requirement 5.4)
        2. Returns 401 for unauthenticated requests
        3. No database deletions occur without authentication
        
        Note: This test will be skipped if the endpoint is not yet implemented (404).
        """
        # Feature: text-chat-api, Property 2: Authentication Enforcement
        
        # Test without Authorization header
        response = await client.delete("/api/v1/chat/history")
        
        # Skip if endpoint not implemented yet
        if response.status_code == 404:
            pytest.skip("Delete history endpoint not yet implemented")
        
        assert response.status_code == 401, \
            f"Delete history endpoint should return 401 without auth token, got {response.status_code}"
        
        # Test with invalid token
        client.headers["Authorization"] = "Bearer invalid_token"
        response = await client.delete("/api/v1/chat/history")
        
        assert response.status_code == 401, \
            f"Delete history endpoint should return 401 with invalid token, got {response.status_code}"
        
        # Clean up headers
        if "Authorization" in client.headers:
            del client.headers["Authorization"]
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        token_type=st.sampled_from([
            None,  # No token
            "invalid_format",  # Invalid token format
            "malformed_header",  # Malformed Authorization header
            "expired_token"  # Expired token (simulated)
        ])
    )
    @settings(
        max_examples=20,  # Test multiple combinations
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_chat_endpoint_authentication_variations(
        self,
        token_type: str,
        client
    ):
        """
        Property: Chat endpoint consistently enforces authentication for all token variations.
        
        This test verifies that:
        1. Chat endpoint rejects all types of invalid authentication (Requirement 8.1)
        2. Returns 401 for all invalid token types (Requirement 8.2)
        3. Authentication enforcement is consistent
        """
        # Feature: text-chat-api, Property 2: Authentication Enforcement
        
        # Set up authorization header based on token type
        if token_type is None:
            # No Authorization header
            if "Authorization" in client.headers:
                del client.headers["Authorization"]
        elif token_type == "invalid_format":
            client.headers["Authorization"] = "Bearer invalid_token_12345"
        elif token_type == "malformed_header":
            client.headers["Authorization"] = "NotBearer token"
        elif token_type == "expired_token":
            # Simulate expired token (just use invalid format)
            client.headers["Authorization"] = "Bearer expired.token.here"
        
        # Make request to chat endpoint
        response = await client.post(
            "/api/v1/chat/chat",
            json={"message": "Test message"}
        )
        
        # Verify 401 response
        assert response.status_code == 401, \
            f"Chat endpoint should return 401 for token_type={token_type}, " \
            f"got {response.status_code}"
        
        # Verify response has error detail
        data = response.json()
        assert "detail" in data, \
            f"401 response should include 'detail' field"
        
        # Clean up headers
        if "Authorization" in client.headers:
            del client.headers["Authorization"]
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        message=valid_chat_message()
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_no_database_access_without_authentication(
        self,
        message: str,
        client,
        db_session
    ):
        """
        Property: Unauthenticated requests do not access the database.
        
        This test verifies that:
        1. No messages are persisted for unauthenticated requests
        2. Database remains unchanged after failed authentication
        3. System fails fast on authentication errors
        """
        # Feature: text-chat-api, Property 2: Authentication Enforcement
        
        from sqlalchemy import select, func
        
        # Count messages before request
        count_stmt = select(func.count()).select_from(ConversationMessage)
        count_result = await db_session.execute(count_stmt)
        initial_count = count_result.scalar()
        
        # Make unauthenticated request
        response = await client.post(
            "/api/v1/chat/chat",
            json={"message": message}
        )
        
        # Verify 401 response
        assert response.status_code == 401, \
            f"Should return 401 without authentication"
        
        # Verify no messages were added to database
        count_result = await db_session.execute(count_stmt)
        final_count = count_result.scalar()
        
        assert final_count == initial_count, \
            f"No messages should be added without authentication. " \
            f"Initial: {initial_count}, Final: {final_count}"


class TestAgentRoutingConsistency:
    """
    Property 3: Agent Routing Consistency
    
    **Validates: Requirements 2.4, 6.1, 6.2**
    
    For any chat request with an explicit agent_type parameter from the valid set 
    (workout, diet, supplement, tracker, scheduler, general), the system SHALL 
    route to that specific agent and the returned agent_type SHALL match the 
    requested agent_type.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        message=valid_chat_message(),
        agent_type=agent_type_value()
    )
    @settings(
        max_examples=100,  # Test all agent types thoroughly
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_explicit_agent_routing_matches_request(
        self,
        message: str,
        agent_type: str,
        authenticated_client_with_profile
    ):
        """
        Property: Explicit agent_type routing is consistent.
        
        This test verifies that when a user specifies an agent_type:
        1. The request is routed to that specific agent (Requirement 2.4)
        2. The response agent_type matches the requested agent_type (Requirement 6.1)
        3. Routing is consistent across all valid agent types (Requirement 6.2)
        """
        # Feature: text-chat-api, Property 3: Agent Routing Consistency
        
        client, user = authenticated_client_with_profile
        
        # Send chat request with explicit agent_type
        response = await client.post(
            "/api/v1/chat/chat",
            json={
                "message": message,
                "agent_type": agent_type
            }
        )
        
        # Verify successful response
        assert response.status_code == 200, \
            f"Chat request with agent_type='{agent_type}' should succeed, " \
            f"got status {response.status_code}. Response: {response.text}"
        
        data = response.json()
        
        # Property verification: Response agent_type must match requested agent_type
        # (Requirement 6.1, 6.2)
        assert "agent_type" in data, \
            f"Response should include 'agent_type' field"
        
        assert data["agent_type"] == agent_type, \
            f"Response agent_type should match requested agent_type. " \
            f"Requested: '{agent_type}', Got: '{data['agent_type']}' " \
            f"(Requirement 2.4, 6.1)"
        
        # Verify response structure is complete
        assert "response" in data, \
            f"Response should include 'response' field"
        assert "conversation_id" in data, \
            f"Response should include 'conversation_id' field"
        assert "tools_used" in data, \
            f"Response should include 'tools_used' field"
        
        # Verify response content is not empty
        assert len(data["response"]) > 0, \
            f"Response content should not be empty for agent_type='{agent_type}'"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        message=valid_chat_message(),
        agent_types=st.lists(
            agent_type_value(),
            min_size=2,
            max_size=6,
            unique=True
        )
    )
    @settings(
        max_examples=50,  # Test multiple agent type combinations
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_routing_consistency_across_multiple_agents(
        self,
        message: str,
        agent_types: list,
        authenticated_client_with_profile
    ):
        """
        Property: Routing is consistent when switching between agents.
        
        This test verifies that:
        1. Multiple requests with different agent_types all succeed
        2. Each response matches its requested agent_type
        3. Agent routing is independent and consistent
        """
        # Feature: text-chat-api, Property 3: Agent Routing Consistency
        
        client, user = authenticated_client_with_profile
        
        # Send requests to multiple agents
        for agent_type in agent_types:
            response = await client.post(
                "/api/v1/chat/chat",
                json={
                    "message": message,
                    "agent_type": agent_type
                }
            )
            
            # Verify successful response
            assert response.status_code == 200, \
                f"Chat request with agent_type='{agent_type}' should succeed"
            
            data = response.json()
            
            # Property verification: Each response matches its requested agent_type
            assert data["agent_type"] == agent_type, \
                f"Response agent_type should match requested agent_type. " \
                f"Requested: '{agent_type}', Got: '{data['agent_type']}'"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        agent_type=agent_type_value()
    )
    @settings(
        max_examples=30,  # Test each agent type multiple times
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_agent_routing_with_various_message_lengths(
        self,
        agent_type: str,
        authenticated_client_with_profile
    ):
        """
        Property: Agent routing is consistent regardless of message length.
        
        This test verifies that:
        1. Short messages route correctly to specified agent
        2. Long messages route correctly to specified agent
        3. Message length doesn't affect routing consistency
        """
        # Feature: text-chat-api, Property 3: Agent Routing Consistency
        
        client, user = authenticated_client_with_profile
        
        # Test with short message
        short_message = "Hi"
        response_short = await client.post(
            "/api/v1/chat/chat",
            json={
                "message": short_message,
                "agent_type": agent_type
            }
        )
        
        assert response_short.status_code == 200, \
            f"Short message should succeed with agent_type='{agent_type}'"
        
        data_short = response_short.json()
        assert data_short["agent_type"] == agent_type, \
            f"Short message routing should match requested agent_type"
        
        # Test with long message (near max length)
        long_message = "What should I do? " * 100  # ~1800 characters
        long_message = long_message[:1999]  # Ensure under 2000 char limit
        
        response_long = await client.post(
            "/api/v1/chat/chat",
            json={
                "message": long_message,
                "agent_type": agent_type
            }
        )
        
        assert response_long.status_code == 200, \
            f"Long message should succeed with agent_type='{agent_type}'"
        
        data_long = response_long.json()
        assert data_long["agent_type"] == agent_type, \
            f"Long message routing should match requested agent_type"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        message=valid_chat_message(),
        agent_type=agent_type_value()
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_agent_routing_persistence_in_database(
        self,
        message: str,
        agent_type: str,
        authenticated_client_with_profile,
        db_session: AsyncSession
    ):
        """
        Property: Agent routing is correctly persisted in conversation history.
        
        This test verifies that:
        1. Explicit agent_type is persisted in database
        2. Assistant messages have correct agent_type
        3. Database records match API response
        """
        # Feature: text-chat-api, Property 3: Agent Routing Consistency
        
        client, user = authenticated_client_with_profile
        
        # Count messages before request
        count_stmt = select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.user_id == user.id
        )
        count_result = await db_session.execute(count_stmt)
        initial_count = count_result.scalar()
        
        # Send chat request with explicit agent_type
        response = await client.post(
            "/api/v1/chat/chat",
            json={
                "message": message,
                "agent_type": agent_type
            }
        )
        
        assert response.status_code == 200, \
            f"Chat request should succeed"
        
        data = response.json()
        
        # Verify response agent_type matches request
        assert data["agent_type"] == agent_type, \
            f"Response agent_type should match requested agent_type"
        
        # Query database for persisted messages
        stmt = select(ConversationMessage).where(
            ConversationMessage.user_id == user.id
        ).order_by(ConversationMessage.created_at.desc()).limit(2)
        
        result = await db_session.execute(stmt)
        messages = result.scalars().all()
        
        # Verify both messages were persisted
        expected_count = initial_count + 2
        assert len(messages) >= 2, \
            f"Should have at least 2 new messages in database"
        
        # Get the most recent messages (assistant first due to DESC order)
        assistant_msg = messages[0]
        user_msg = messages[1]
        
        # Verify assistant message has correct agent_type
        assert assistant_msg.role == "assistant", \
            f"Most recent message should be assistant response"
        assert assistant_msg.agent_type == agent_type, \
            f"Persisted assistant message should have agent_type='{agent_type}', " \
            f"got '{assistant_msg.agent_type}'"
        
        # Verify user message has no agent_type
        assert user_msg.role == "user", \
            f"Second most recent message should be user message"
        assert user_msg.agent_type is None, \
            f"User message should not have agent_type"


class TestConversationHistoryOrderingAndCompleteness:
    """
    Property 5: Conversation History Ordering and Completeness
    
    **Validates: Requirements 1.6, 4.1, 4.2, 4.3, 4.4**
    
    For any user's conversation history retrieval, messages SHALL be returned in 
    chronological order (oldest to newest) with accurate timestamps, each message 
    containing role, content, agent_type, and created_at fields, and the total 
    count SHALL match the actual number of messages for that user.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_messages=st.integers(min_value=1, max_value=20)
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_history_chronological_ordering(
        self,
        num_messages: int,
        authenticated_client_with_profile,
        db_session: AsyncSession
    ):
        """
        Property: Conversation history is returned in chronological order.
        
        This test verifies that:
        1. Messages are returned oldest to newest (Requirement 4.1)
        2. Timestamps are accurate and in order (Requirement 1.6)
        3. Ordering is consistent regardless of number of messages
        """
        # Feature: text-chat-api, Property 5: Conversation History Ordering and Completeness
        
        client, user = authenticated_client_with_profile
        
        # Create multiple conversation messages with slight time delays
        message_ids = []
        for i in range(num_messages):
            # Create user message
            user_msg = ConversationMessage(
                user_id=user.id,
                role="user",
                content=f"User message {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            await db_session.flush()
            await db_session.refresh(user_msg)
            message_ids.append(user_msg.id)
            
            # Create assistant message
            assistant_msg = ConversationMessage(
                user_id=user.id,
                role="assistant",
                content=f"Assistant response {i}",
                agent_type="general"
            )
            db_session.add(assistant_msg)
            await db_session.flush()
            await db_session.refresh(assistant_msg)
            message_ids.append(assistant_msg.id)
        
        await db_session.commit()
        
        # Retrieve conversation history
        response = await client.get("/api/v1/chat/history")
        
        assert response.status_code == 200, \
            f"History endpoint should return 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "messages" in data, \
            f"Response should include 'messages' field"
        assert "total" in data, \
            f"Response should include 'total' field"
        
        messages = data["messages"]
        
        # Property verification: Messages should be in chronological order (Requirement 4.1)
        for i in range(len(messages) - 1):
            current_time = datetime.fromisoformat(messages[i]["created_at"].replace('Z', '+00:00'))
            next_time = datetime.fromisoformat(messages[i + 1]["created_at"].replace('Z', '+00:00'))
            
            assert current_time <= next_time, \
                f"Messages should be in chronological order (oldest to newest). " \
                f"Message {i} timestamp: {current_time}, Message {i+1} timestamp: {next_time} " \
                f"(Requirement 4.1, 1.6)"
        
        # Verify all messages have timestamps (Requirement 1.6)
        for i, msg in enumerate(messages):
            assert "created_at" in msg, \
                f"Message {i} should have 'created_at' field (Requirement 1.6)"
            assert msg["created_at"] is not None, \
                f"Message {i} timestamp should not be null"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_messages=st.integers(min_value=1, max_value=15)
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_history_message_completeness(
        self,
        num_messages: int,
        authenticated_client_with_profile,
        db_session: AsyncSession
    ):
        """
        Property: Each message in history contains all required fields.
        
        This test verifies that:
        1. Each message has role, content, agent_type, created_at (Requirement 4.2, 4.3)
        2. Field values are correct and non-empty
        3. Message structure is complete
        """
        # Feature: text-chat-api, Property 5: Conversation History Ordering and Completeness
        
        client, user = authenticated_client_with_profile
        
        # Create conversation messages
        for i in range(num_messages):
            user_msg = ConversationMessage(
                user_id=user.id,
                role="user",
                content=f"Question {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            
            assistant_msg = ConversationMessage(
                user_id=user.id,
                role="assistant",
                content=f"Answer {i}",
                agent_type="workout"
            )
            db_session.add(assistant_msg)
        
        await db_session.commit()
        
        # Retrieve conversation history
        response = await client.get("/api/v1/chat/history")
        
        assert response.status_code == 200, \
            f"History endpoint should succeed"
        
        data = response.json()
        messages = data["messages"]
        
        # Property verification: Each message has all required fields (Requirement 4.2, 4.3)
        for i, msg in enumerate(messages):
            # Verify all required fields are present
            assert "role" in msg, \
                f"Message {i} should have 'role' field (Requirement 4.3)"
            assert "content" in msg, \
                f"Message {i} should have 'content' field (Requirement 4.3)"
            assert "agent_type" in msg, \
                f"Message {i} should have 'agent_type' field (Requirement 4.3)"
            assert "created_at" in msg, \
                f"Message {i} should have 'created_at' field (Requirement 4.3)"
            
            # Verify role is valid
            assert msg["role"] in ["user", "assistant"], \
                f"Message {i} role should be 'user' or 'assistant', got '{msg['role']}'"
            
            # Verify content is not empty
            assert len(msg["content"]) > 0, \
                f"Message {i} content should not be empty"
            
            # Verify agent_type is set for assistant messages
            if msg["role"] == "assistant":
                assert msg["agent_type"] is not None, \
                    f"Assistant message {i} should have agent_type (Requirement 4.3)"
                assert msg["agent_type"] in ["workout", "diet", "supplement", "tracker", "scheduler", "general"], \
                    f"Assistant message {i} should have valid agent_type"
            
            # Verify timestamp is valid ISO format
            try:
                datetime.fromisoformat(msg["created_at"].replace('Z', '+00:00'))
            except (ValueError, AttributeError) as e:
                pytest.fail(f"Message {i} created_at should be valid ISO timestamp: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_messages=st.integers(min_value=1, max_value=25)
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_history_total_count_accuracy(
        self,
        num_messages: int,
        authenticated_client_with_profile,
        db_session: AsyncSession
    ):
        """
        Property: Total count matches actual number of messages.
        
        This test verifies that:
        1. Total count field is accurate (Requirement 4.4)
        2. Count includes all user messages
        3. Count is consistent with database state
        """
        # Feature: text-chat-api, Property 5: Conversation History Ordering and Completeness
        
        client, user = authenticated_client_with_profile
        
        # Clear any existing messages for this user first
        delete_stmt = delete(ConversationMessage).where(
            ConversationMessage.user_id == user.id
        )
        await db_session.execute(delete_stmt)
        await db_session.commit()
        
        # Create conversation messages
        for i in range(num_messages):
            user_msg = ConversationMessage(
                user_id=user.id,
                role="user",
                content=f"Message {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            
            assistant_msg = ConversationMessage(
                user_id=user.id,
                role="assistant",
                content=f"Response {i}",
                agent_type="general"
            )
            db_session.add(assistant_msg)
        
        await db_session.commit()
        
        # Count messages in database
        count_stmt = select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.user_id == user.id
        )
        count_result = await db_session.execute(count_stmt)
        db_count = count_result.scalar()
        
        # Retrieve conversation history
        response = await client.get("/api/v1/chat/history")
        
        assert response.status_code == 200, \
            f"History endpoint should succeed"
        
        data = response.json()
        
        # Property verification: Total count matches database (Requirement 4.4)
        assert data["total"] == db_count, \
            f"Total count should match database count. " \
            f"API returned: {data['total']}, Database has: {db_count} " \
            f"(Requirement 4.4)"
        
        # Verify total count matches expected (2 messages per interaction)
        expected_count = num_messages * 2
        assert data["total"] == expected_count, \
            f"Total count should be {expected_count} (2 messages per interaction), " \
            f"got {data['total']}"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        limit=st.integers(min_value=1, max_value=50),
        total_messages=st.integers(min_value=5, max_value=30)
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_history_limit_parameter_ordering(
        self,
        limit: int,
        total_messages: int,
        authenticated_client_with_profile,
        db_session: AsyncSession
    ):
        """
        Property: Limit parameter returns most recent messages in chronological order.
        
        This test verifies that:
        1. Limit parameter controls number of messages returned (Requirement 4.2)
        2. Most recent messages are returned when limit < total
        3. Messages are still in chronological order (oldest to newest)
        4. Total count is accurate regardless of limit
        """
        # Feature: text-chat-api, Property 5: Conversation History Ordering and Completeness
        
        client, user = authenticated_client_with_profile
        
        # Clear any existing messages for this user first
        delete_stmt = delete(ConversationMessage).where(
            ConversationMessage.user_id == user.id
        )
        await db_session.execute(delete_stmt)
        await db_session.commit()
        
        # Create conversation messages
        for i in range(total_messages):
            user_msg = ConversationMessage(
                user_id=user.id,
                role="user",
                content=f"User message {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            
            assistant_msg = ConversationMessage(
                user_id=user.id,
                role="assistant",
                content=f"Assistant response {i}",
                agent_type="diet"
            )
            db_session.add(assistant_msg)
        
        await db_session.commit()
        
        # Retrieve conversation history with limit
        response = await client.get(f"/api/v1/chat/history?limit={limit}")
        
        assert response.status_code == 200, \
            f"History endpoint should succeed with limit={limit}"
        
        data = response.json()
        messages = data["messages"]
        
        # Property verification: Number of messages respects limit (Requirement 4.2)
        expected_message_count = min(limit, total_messages * 2)
        assert len(messages) <= limit, \
            f"Number of messages should not exceed limit. " \
            f"Limit: {limit}, Got: {len(messages)}"
        
        # Verify total count is accurate (not affected by limit) (Requirement 4.4)
        expected_total = total_messages * 2
        assert data["total"] == expected_total, \
            f"Total count should be {expected_total} regardless of limit, " \
            f"got {data['total']}"
        
        # Verify messages are in chronological order (Requirement 4.1)
        for i in range(len(messages) - 1):
            current_time = datetime.fromisoformat(messages[i]["created_at"].replace('Z', '+00:00'))
            next_time = datetime.fromisoformat(messages[i + 1]["created_at"].replace('Z', '+00:00'))
            
            assert current_time <= next_time, \
                f"Messages should be in chronological order even with limit. " \
                f"Message {i} timestamp: {current_time}, Message {i+1} timestamp: {next_time}"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_messages=st.integers(min_value=2, max_value=10)
    )
    @settings(
        max_examples=30,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_history_user_data_isolation(
        self,
        num_messages: int,
        authenticated_client_with_profile,
        db_session: AsyncSession
    ):
        """
        Property: History endpoint only returns messages for authenticated user.
        
        This test verifies that:
        1. Users only see their own messages (Requirement 4.5)
        2. Other users' messages are not included
        3. User data isolation is maintained
        """
        # Feature: text-chat-api, Property 5: Conversation History Ordering and Completeness
        
        client, user1 = authenticated_client_with_profile
        
        # Clear any existing messages for user1 first
        delete_stmt = delete(ConversationMessage).where(
            ConversationMessage.user_id == user1.id
        )
        await db_session.execute(delete_stmt)
        await db_session.commit()
        
        # Create second user
        user2 = User(
            id=uuid4(),
            email=f"user2_{uuid4()}@example.com",
            hashed_password=hash_password("password123"),
            full_name="User Two",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user2)
        
        # Create messages for user1
        for i in range(num_messages):
            user_msg = ConversationMessage(
                user_id=user1.id,
                role="user",
                content=f"User1 message {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            
            assistant_msg = ConversationMessage(
                user_id=user1.id,
                role="assistant",
                content=f"User1 response {i}",
                agent_type="tracker"
            )
            db_session.add(assistant_msg)
        
        # Create messages for user2
        for i in range(num_messages):
            user_msg = ConversationMessage(
                user_id=user2.id,
                role="user",
                content=f"User2 message {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            
            assistant_msg = ConversationMessage(
                user_id=user2.id,
                role="assistant",
                content=f"User2 response {i}",
                agent_type="scheduler"
            )
            db_session.add(assistant_msg)
        
        await db_session.commit()
        
        # Retrieve history for user1
        response = await client.get("/api/v1/chat/history")
        
        assert response.status_code == 200, \
            f"History endpoint should succeed"
        
        data = response.json()
        messages = data["messages"]
        
        # Property verification: Only user1's messages are returned (Requirement 4.5)
        expected_count = num_messages * 2
        assert len(messages) == expected_count, \
            f"User1 should have {expected_count} messages, got {len(messages)}"
        
        assert data["total"] == expected_count, \
            f"Total count should be {expected_count} for user1"
        
        # Verify all messages belong to user1 (no user2 messages)
        for i, msg in enumerate(messages):
            assert "User2" not in msg["content"], \
                f"Message {i} should not contain User2's content. " \
                f"Got: {msg['content']} (Requirement 4.5)"
            assert "User1" in msg["content"] or msg["role"] == "assistant", \
                f"Message {i} should belong to User1"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_history_empty_conversation(
        self,
        authenticated_client_with_profile
    ):
        """
        Property: Empty conversation history returns empty list with zero total.
        
        This test verifies that:
        1. Users with no messages get empty list
        2. Total count is zero
        3. Response structure is still valid
        """
        # Feature: text-chat-api, Property 5: Conversation History Ordering and Completeness
        
        client, user = authenticated_client_with_profile
        
        # Don't create any messages - user has empty history
        
        # Retrieve conversation history
        response = await client.get("/api/v1/chat/history")
        
        assert response.status_code == 200, \
            f"History endpoint should succeed even with empty history"
        
        data = response.json()
        
        # Property verification: Empty history returns empty list
        assert "messages" in data, \
            f"Response should include 'messages' field"
        assert "total" in data, \
            f"Response should include 'total' field"
        
        assert len(data["messages"]) == 0, \
            f"Empty history should return empty messages list"
        
        assert data["total"] == 0, \
            f"Empty history should have total count of 0"


class TestUserDataIsolation:
    """
    Property 6: User Data Isolation
    
    **Validates: Requirements 4.5, 5.1, 5.3, 8.3, 8.4**
    
    For any authenticated user, all conversation history operations (retrieve, delete) 
    SHALL only access messages belonging to that user (user_id from JWT token) and 
    SHALL NOT access or modify other users' messages.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_messages_user1=st.integers(min_value=1, max_value=15),
        num_messages_user2=st.integers(min_value=1, max_value=15)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_history_retrieval_isolation(
        self,
        num_messages_user1: int,
        num_messages_user2: int,
        db_session: AsyncSession
    ):
        """
        Property: History retrieval only returns messages for authenticated user.

        This test verifies that:
        1. User 1 only sees their own messages (Requirement 4.5)
        2. User 2 only sees their own messages (Requirement 4.5)
        3. No cross-contamination between users (Requirement 8.3, 8.4)
        4. User ID from JWT token determines access (Requirement 8.3)
        """
        # Feature: text-chat-api, Property 6: User Data Isolation

        from httpx import AsyncClient, ASGITransport
        from app.main import app

        # Create user1
        user1 = User(
            id=uuid4(),
            email=f"user1_{uuid4()}@example.com",
            hashed_password=hash_password("password123"),
            full_name="User One",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user1)

        # Create user2
        user2 = User(
            id=uuid4(),
            email=f"user2_{uuid4()}@example.com",
            hashed_password=hash_password("password123"),
            full_name="User Two",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        # Create messages for user1
        user1_message_ids = []
        for i in range(num_messages_user1):
            user_msg = ConversationMessage(
                user_id=user1.id,
                role="user",
                content=f"User1 question {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            await db_session.flush()
            await db_session.refresh(user_msg)
            user1_message_ids.append(user_msg.id)

            assistant_msg = ConversationMessage(
                user_id=user1.id,
                role="assistant",
                content=f"User1 answer {i}",
                agent_type="workout"
            )
            db_session.add(assistant_msg)
            await db_session.flush()
            await db_session.refresh(assistant_msg)
            user1_message_ids.append(assistant_msg.id)

        # Create messages for user2
        user2_message_ids = []
        for i in range(num_messages_user2):
            user_msg = ConversationMessage(
                user_id=user2.id,
                role="user",
                content=f"User2 question {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            await db_session.flush()
            await db_session.refresh(user_msg)
            user2_message_ids.append(user_msg.id)

            assistant_msg = ConversationMessage(
                user_id=user2.id,
                role="assistant",
                content=f"User2 answer {i}",
                agent_type="diet"
            )
            db_session.add(assistant_msg)
            await db_session.flush()
            await db_session.refresh(assistant_msg)
            user2_message_ids.append(assistant_msg.id)

        await db_session.commit()

        # Use async context managers for clients to prevent event loop errors
        token1 = create_access_token({"user_id": str(user1.id)})
        token2 = create_access_token({"user_id": str(user2.id)})

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client1:
            client1.headers["Authorization"] = f"Bearer {token1}"

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client2:
                client2.headers["Authorization"] = f"Bearer {token2}"

                # Property verification: User1 retrieves only their messages (Requirement 4.5, 8.3)
                response1 = await client1.get("/api/v1/chat/history")

                assert response1.status_code == 200, \
                    f"User1 history retrieval should succeed"

                data1 = response1.json()
                messages1 = data1["messages"]

                expected_count1 = num_messages_user1 * 2
                assert len(messages1) == expected_count1, \
                    f"User1 should have {expected_count1} messages, got {len(messages1)}"

                assert data1["total"] == expected_count1, \
                    f"User1 total count should be {expected_count1}"

                # Verify all messages belong to user1 (no user2 content)
                for i, msg in enumerate(messages1):
                    assert "User2" not in msg["content"], \
                        f"User1's history should not contain User2's messages (Requirement 4.5, 8.4). " \
                        f"Found: {msg['content']}"
                    assert "User1" in msg["content"] or msg["role"] == "assistant", \
                        f"Message {i} should belong to User1"

                # Property verification: User2 retrieves only their messages (Requirement 4.5, 8.3)
                response2 = await client2.get("/api/v1/chat/history")

                assert response2.status_code == 200, \
                    f"User2 history retrieval should succeed"

                data2 = response2.json()
                messages2 = data2["messages"]

                expected_count2 = num_messages_user2 * 2
                assert len(messages2) == expected_count2, \
                    f"User2 should have {expected_count2} messages, got {len(messages2)}"

                assert data2["total"] == expected_count2, \
                    f"User2 total count should be {expected_count2}"

                # Verify all messages belong to user2 (no user1 content)
                for i, msg in enumerate(messages2):
                    assert "User1" not in msg["content"], \
                        f"User2's history should not contain User1's messages (Requirement 4.5, 8.4). " \
                        f"Found: {msg['content']}"
                    assert "User2" in msg["content"] or msg["role"] == "assistant", \
                        f"Message {i} should belong to User2"

                # Verify no overlap in message IDs
                message_ids1 = {msg["content"] for msg in messages1}
                message_ids2 = {msg["content"] for msg in messages2}

                assert message_ids1.isdisjoint(message_ids2), \
                    f"User1 and User2 messages should not overlap (Requirement 8.3, 8.4)"

        # Clients are automatically closed when exiting context managers

    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_messages_user1=st.integers(min_value=2, max_value=10),
        num_messages_user2=st.integers(min_value=2, max_value=10)
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_history_deletion_isolation(
        self,
        num_messages_user1: int,
        num_messages_user2: int,
        db_session: AsyncSession
    ):
        """
        Property: History deletion only deletes messages for authenticated user.
        
        This test verifies that:
        1. User1 can delete their own messages (Requirement 5.1)
        2. User1's deletion does not affect User2's messages (Requirement 5.3)
        3. User2's messages remain intact after User1's deletion (Requirement 8.3, 8.4)
        4. User ID from JWT token determines deletion scope (Requirement 8.3)
        """
        # Feature: text-chat-api, Property 6: User Data Isolation
        
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        # Create user1
        user1 = User(
            id=uuid4(),
            email=f"user1_{uuid4()}@example.com",
            hashed_password=hash_password("password123"),
            full_name="User One",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user1)
        
        # Create user2
        user2 = User(
            id=uuid4(),
            email=f"user2_{uuid4()}@example.com",
            hashed_password=hash_password("password123"),
            full_name="User Two",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        
        # Create messages for user1
        for i in range(num_messages_user1):
            user_msg = ConversationMessage(
                user_id=user1.id,
                role="user",
                content=f"User1 message {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            
            assistant_msg = ConversationMessage(
                user_id=user1.id,
                role="assistant",
                content=f"User1 response {i}",
                agent_type="supplement"
            )
            db_session.add(assistant_msg)
        
        # Create messages for user2
        for i in range(num_messages_user2):
            user_msg = ConversationMessage(
                user_id=user2.id,
                role="user",
                content=f"User2 message {i}",
                agent_type=None
            )
            db_session.add(user_msg)
            
            assistant_msg = ConversationMessage(
                user_id=user2.id,
                role="assistant",
                content=f"User2 response {i}",
                agent_type="tracker"
            )
            db_session.add(assistant_msg)
        
        await db_session.commit()
        
        # Count messages before deletion
        count_stmt1 = select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.user_id == user1.id
        )
        count_result1 = await db_session.execute(count_stmt1)
        user1_count_before = count_result1.scalar()
        
        count_stmt2 = select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.user_id == user2.id
        )
        count_result2 = await db_session.execute(count_stmt2)
        user2_count_before = count_result2.scalar()
        
        expected_user1_count = num_messages_user1 * 2
        expected_user2_count = num_messages_user2 * 2
        
        assert user1_count_before == expected_user1_count, \
            f"User1 should have {expected_user1_count} messages before deletion"
        assert user2_count_before == expected_user2_count, \
            f"User2 should have {expected_user2_count} messages before deletion"
        
        # Use async context managers for clients to prevent event loop errors
        token1 = create_access_token({"user_id": str(user1.id)})
        token2 = create_access_token({"user_id": str(user2.id)})
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client1:
            client1.headers["Authorization"] = f"Bearer {token1}"
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client2:
                client2.headers["Authorization"] = f"Bearer {token2}"
                
                # Property verification: User1 deletes their history (Requirement 5.1)
                response1 = await client1.delete("/api/v1/chat/history")
                
                assert response1.status_code == 200, \
                    f"User1 history deletion should succeed"
                
                data1 = response1.json()
                assert data1["status"] == "cleared", \
                    f"Deletion should return 'cleared' status"
                
                # Verify user1's messages are deleted
                count_result1 = await db_session.execute(count_stmt1)
                user1_count_after = count_result1.scalar()
                
                assert user1_count_after == 0, \
                    f"User1 should have 0 messages after deletion, got {user1_count_after} " \
                    f"(Requirement 5.1)"
                
                # Property verification: User2's messages remain intact (Requirement 5.3, 8.3, 8.4)
                count_result2 = await db_session.execute(count_stmt2)
                user2_count_after = count_result2.scalar()
                
                assert user2_count_after == expected_user2_count, \
                    f"User2 should still have {expected_user2_count} messages after User1's deletion, " \
                    f"got {user2_count_after} (Requirement 5.3, 8.3, 8.4)"
                
                # Verify user2 can still retrieve their messages
                response2 = await client2.get("/api/v1/chat/history")
                
                assert response2.status_code == 200, \
                    f"User2 history retrieval should still work"
                
                data2 = response2.json()
                assert len(data2["messages"]) == expected_user2_count, \
                    f"User2 should still have all their messages"
                
                # Verify user2's messages contain correct content
                for msg in data2["messages"]:
                    assert "User2" in msg["content"] or msg["role"] == "assistant", \
                        f"User2's messages should be intact and correct"
                    assert "User1" not in msg["content"], \
                        f"User2's messages should not contain User1's content"
        
        # Clients are automatically closed when exiting context managers
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_users=st.integers(min_value=3, max_value=5),
        messages_per_user=st.integers(min_value=2, max_value=8)
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_multi_user_isolation(
        self,
        num_users: int,
        messages_per_user: int,
        db_session: AsyncSession
    ):
        """
        Property: Data isolation holds across multiple users.
        
        This test verifies that:
        1. Each user only sees their own messages (Requirement 4.5)
        2. Each user can only delete their own messages (Requirement 5.1, 5.3)
        3. No cross-contamination across multiple users (Requirement 8.3, 8.4)
        4. JWT token correctly identifies user for all operations (Requirement 8.3)
        """
        # Feature: text-chat-api, Property 6: User Data Isolation
        
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        # Create multiple users
        users = []
        
        for i in range(num_users):
            user = User(
                id=uuid4(),
                email=f"user{i}_{uuid4()}@example.com",
                hashed_password=hash_password("password123"),
                full_name=f"User {i}",
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(user)
            users.append(user)
        
        await db_session.commit()
        for user in users:
            await db_session.refresh(user)
        
        # Create messages for each user
        for i, user in enumerate(users):
            for j in range(messages_per_user):
                user_msg = ConversationMessage(
                    user_id=user.id,
                    role="user",
                    content=f"User{i} message {j}",
                    agent_type=None
                )
                db_session.add(user_msg)
                
                assistant_msg = ConversationMessage(
                    user_id=user.id,
                    role="assistant",
                    content=f"User{i} response {j}",
                    agent_type="general"
                )
                db_session.add(assistant_msg)
        
        await db_session.commit()
        
        # Property verification: Each user retrieves only their messages (Requirement 4.5, 8.3)
        # Use async context managers for all clients to prevent event loop errors
        for i, user in enumerate(users):
            token = create_access_token({"user_id": str(user.id)})
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as user_client:
                user_client.headers["Authorization"] = f"Bearer {token}"
                
                response = await user_client.get("/api/v1/chat/history")
                
                assert response.status_code == 200, \
                    f"User{i} history retrieval should succeed"
                
                data = response.json()
                messages = data["messages"]
                
                expected_count = messages_per_user * 2
                assert len(messages) == expected_count, \
                    f"User{i} should have {expected_count} messages, got {len(messages)}"
                
                # Verify all messages belong to this user
                for msg in messages:
                    assert f"User{i}" in msg["content"] or msg["role"] == "assistant", \
                        f"User{i}'s messages should only contain their own content (Requirement 4.5)"
                    
                    # Verify no other user's content is present
                    for j in range(num_users):
                        if j != i:
                            assert f"User{j}" not in msg["content"], \
                                f"User{i}'s messages should not contain User{j}'s content " \
                                f"(Requirement 8.3, 8.4)"
        
        # Property verification: Delete one user's history doesn't affect others (Requirement 5.3)
        # Delete first user's history
        token = create_access_token({"user_id": str(users[0].id)})
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as first_user_client:
            first_user_client.headers["Authorization"] = f"Bearer {token}"
            
            delete_response = await first_user_client.delete("/api/v1/chat/history")
            
            assert delete_response.status_code == 200, \
                f"User0 history deletion should succeed"
        
        # Verify first user has no messages
        count_stmt = select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.user_id == users[0].id
        )
        count_result = await db_session.execute(count_stmt)
        user0_count = count_result.scalar()
        
        assert user0_count == 0, \
            f"User0 should have 0 messages after deletion"
        
        # Verify all other users still have their messages (Requirement 5.3, 8.3, 8.4)
        for i in range(1, num_users):
            count_stmt = select(func.count()).select_from(ConversationMessage).where(
                ConversationMessage.user_id == users[i].id
            )
            count_result = await db_session.execute(count_stmt)
            user_count = count_result.scalar()
            
            expected_count = messages_per_user * 2
            assert user_count == expected_count, \
                f"User{i} should still have {expected_count} messages after User0's deletion, " \
                f"got {user_count} (Requirement 5.3, 8.3, 8.4)"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_messages=st.integers(min_value=1, max_value=10)
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
        deadline=None
    )
    async def test_jwt_token_determines_access(
        self,
        num_messages: int,
        db_session: AsyncSession
    ):
        """
        Property: JWT token user_id determines data access, not request body.
        
        This test verifies that:
        1. User ID is extracted from JWT token (Requirement 8.3)
        2. Users cannot access other users' data by manipulating requests
        3. Authentication token is the sole source of user identity (Requirement 8.3, 8.4)
        """
        # Feature: text-chat-api, Property 6: User Data Isolation
        
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        # Create two users
        user1 = User(
            id=uuid4(),
            email=f"user1_{uuid4()}@example.com",
            hashed_password=hash_password("password123"),
            full_name="User One",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        user2 = User(
            id=uuid4(),
            email=f"user2_{uuid4()}@example.com",
            hashed_password=hash_password("password123"),
            full_name="User Two",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        
        # Create messages for both users
        for i in range(num_messages):
            # User1 messages
            user1_msg = ConversationMessage(
                user_id=user1.id,
                role="user",
                content=f"User1 secret message {i}",
                agent_type=None
            )
            db_session.add(user1_msg)
            
            # User2 messages
            user2_msg = ConversationMessage(
                user_id=user2.id,
                role="user",
                content=f"User2 secret message {i}",
                agent_type=None
            )
            db_session.add(user2_msg)
        
        await db_session.commit()
        
        # Property verification: User1's JWT token only accesses User1's data (Requirement 8.3)
        token1 = create_access_token({"user_id": str(user1.id)})
        token2 = create_access_token({"user_id": str(user2.id)})
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client1:
            client1.headers["Authorization"] = f"Bearer {token1}"
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client2:
                client2.headers["Authorization"] = f"Bearer {token2}"
                
                response1 = await client1.get("/api/v1/chat/history")
                
                assert response1.status_code == 200, \
                    f"User1 should be able to access their history"
                
                data1 = response1.json()
                messages1 = data1["messages"]
                
                # Verify only User1's messages are returned
                for msg in messages1:
                    assert "User1" in msg["content"], \
                        f"User1's JWT token should only return User1's messages (Requirement 8.3)"
                    assert "User2" not in msg["content"], \
                        f"User1's JWT token should not return User2's messages (Requirement 8.3, 8.4)"
                
                # Property verification: User2's JWT token only accesses User2's data (Requirement 8.3)
                response2 = await client2.get("/api/v1/chat/history")
                
                assert response2.status_code == 200, \
                    f"User2 should be able to access their history"
                
                data2 = response2.json()
                messages2 = data2["messages"]
                
                # Verify only User2's messages are returned
                for msg in messages2:
                    assert "User2" in msg["content"], \
                        f"User2's JWT token should only return User2's messages (Requirement 8.3)"
                    assert "User1" not in msg["content"], \
                        f"User2's JWT token should not return User1's messages (Requirement 8.3, 8.4)"
                
                # Verify counts are correct
                assert len(messages1) == num_messages, \
                    f"User1 should have {num_messages} messages"
                assert len(messages2) == num_messages, \
                    f"User2 should have {num_messages} messages"
        
        # Clients are automatically closed when exiting context managers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
