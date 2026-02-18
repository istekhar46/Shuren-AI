"""
Unit tests for onboarding agent API endpoints.

This module tests the new agent-based onboarding endpoints:
- POST /api/v1/onboarding/chat: Chat with current onboarding agent
- GET /api/v1/onboarding/current-agent: Get current agent info

Tests cover:
- Authentication requirement (401 without token)
- Validation errors (422 for invalid requests)
- Not found errors (404 for missing state)
- Successful responses (200 with correct data)

Validates Requirements 6.5, 6.6, 7.6
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import datetime, timezone

from app.models.user import User
from app.models.onboarding import OnboardingState
from app.core.security import create_access_token
from app.schemas.onboarding import AgentResponse


@pytest.mark.asyncio
@pytest.mark.unit
class TestChatEndpointAuthentication:
    """Tests for chat endpoint authentication."""
    
    async def test_chat_requires_authentication(self, client: AsyncClient):
        """Test that chat endpoint returns 401 without authentication."""
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "Hello"}
        )
        assert response.status_code == 401
    
    async def test_chat_with_invalid_token(self, client: AsyncClient):
        """Test that chat endpoint returns 401 with invalid token."""
        client.headers["Authorization"] = "Bearer invalid_token_here"
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "Hello"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.unit
class TestChatEndpointValidation:
    """Tests for chat endpoint request validation."""
    
    async def test_chat_empty_message_fails(self, authenticated_client):
        """Test that empty message returns 422 validation error."""
        client, user = authenticated_client
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": ""}
        )
        assert response.status_code == 422
    
    async def test_chat_missing_message_fails(self, authenticated_client):
        """Test that missing message field returns 422 validation error."""
        client, user = authenticated_client
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={}
        )
        assert response.status_code == 422
    
    async def test_chat_message_too_long_fails(self, authenticated_client):
        """Test that message exceeding max length returns 422."""
        client, user = authenticated_client
        long_message = "a" * 2001
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": long_message}
        )
        assert response.status_code == 422
    
    async def test_chat_invalid_step_fails(self, authenticated_client):
        """Test that invalid step number returns 422."""
        client, user = authenticated_client
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "Hello", "step": 10}
        )
        assert response.status_code == 422
    
    async def test_chat_negative_step_fails(self, authenticated_client):
        """Test that negative step number returns 422."""
        client, user = authenticated_client
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "Hello", "step": -1}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.unit
class TestChatEndpointNotFound:
    """Tests for chat endpoint not found errors."""
    
    async def test_chat_without_onboarding_state_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that chat returns 404 when onboarding state doesn't exist."""
        # Create user without onboarding state
        user = User(
            id=uuid4(),
            email="nostate@example.com",
            hashed_password="hashed",
            full_name="No State User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        
        # Create token
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Try to chat
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "Hello"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.unit
class TestChatEndpointSuccess:
    """Tests for successful chat endpoint responses."""
    
    @patch('app.agents.onboarding.base.BaseOnboardingAgent._init_llm')
    async def test_chat_with_valid_message_succeeds(self, mock_init_llm, authenticated_client):
        """Test that valid chat message returns 200 with agent response."""
        # Mock LLM initialization to avoid API key requirement
        mock_init_llm.return_value = None
        
        client, user = authenticated_client
        
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "I workout 3 times a week"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "agent_type" in data
        assert "current_step" in data
        assert "step_complete" in data
        assert "next_action" in data
        
        # Verify data types
        assert isinstance(data["message"], str)
        assert isinstance(data["agent_type"], str)
        assert isinstance(data["current_step"], int)
        assert isinstance(data["step_complete"], bool)
        assert isinstance(data["next_action"], str)
    
    @patch('app.agents.onboarding.base.BaseOnboardingAgent._init_llm')
    async def test_chat_with_step_parameter_succeeds(self, mock_init_llm, authenticated_client):
        """Test that chat with optional step parameter succeeds."""
        mock_init_llm.return_value = None
        
        client, user = authenticated_client
        
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "Hello", "step": 0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == 0
    
    @patch('app.agents.onboarding.base.BaseOnboardingAgent._init_llm')
    async def test_chat_updates_conversation_history(
        self,
        mock_init_llm,
        authenticated_client,
        db_session: AsyncSession
    ):
        """Test that chat appends to conversation history."""
        mock_init_llm.return_value = None
        
        client, user = authenticated_client
        
        # Get initial conversation history
        from sqlalchemy import select
        stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
        result = await db_session.execute(stmt)
        state_before = result.scalars().first()
        initial_history_length = len(state_before.conversation_history or [])
        
        # Send message
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "Test message"}
        )
        
        assert response.status_code == 200
        
        # Refresh state and check conversation history
        await db_session.refresh(state_before)
        new_history_length = len(state_before.conversation_history or [])
        
        # Should have added 2 messages (user + assistant)
        assert new_history_length == initial_history_length + 2
        
        # Verify message structure
        history = state_before.conversation_history
        user_message = history[-2]
        agent_message = history[-1]
        
        assert user_message["role"] == "user"
        assert user_message["content"] == "Test message"
        assert "timestamp" in user_message
        
        assert agent_message["role"] == "assistant"
        assert "content" in agent_message
        assert "timestamp" in agent_message
        assert "agent_type" in agent_message
    
    @patch('app.agents.onboarding.base.BaseOnboardingAgent._init_llm')
    async def test_chat_returns_correct_agent_type(self, mock_init_llm, authenticated_client):
        """Test that chat returns correct agent type for current step."""
        mock_init_llm.return_value = None
        
        client, user = authenticated_client
        
        response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Step 0 should map to fitness_assessment agent
        assert data["agent_type"] == "fitness_assessment"
        assert data["current_step"] == 0


@pytest.mark.asyncio
@pytest.mark.unit
class TestCurrentAgentEndpointAuthentication:
    """Tests for current-agent endpoint authentication."""
    
    async def test_current_agent_requires_authentication(self, client: AsyncClient):
        """Test that current-agent endpoint returns 401 without authentication."""
        response = await client.get("/api/v1/onboarding/current-agent")
        assert response.status_code == 401
    
    async def test_current_agent_with_invalid_token(self, client: AsyncClient):
        """Test that current-agent endpoint returns 401 with invalid token."""
        client.headers["Authorization"] = "Bearer invalid_token_here"
        response = await client.get("/api/v1/onboarding/current-agent")
        assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.unit
class TestCurrentAgentEndpointNotFound:
    """Tests for current-agent endpoint not found errors."""
    
    async def test_current_agent_without_onboarding_state_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that current-agent returns 404 when onboarding state doesn't exist."""
        # Create user without onboarding state
        user = User(
            id=uuid4(),
            email="nostate2@example.com",
            hashed_password="hashed",
            full_name="No State User 2",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        
        # Create token
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Try to get current agent
        response = await client.get("/api/v1/onboarding/current-agent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.unit
class TestCurrentAgentEndpointSuccess:
    """Tests for successful current-agent endpoint responses."""
    
    async def test_current_agent_returns_correct_data(self, authenticated_client):
        """Test that current-agent returns correct agent info."""
        client, user = authenticated_client
        
        response = await client.get("/api/v1/onboarding/current-agent")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "agent_type" in data
        assert "current_step" in data
        assert "agent_description" in data
        assert "context_summary" in data
        
        # Verify data types
        assert isinstance(data["agent_type"], str)
        assert isinstance(data["current_step"], int)
        assert isinstance(data["agent_description"], str)
        assert isinstance(data["context_summary"], dict)
    
    async def test_current_agent_returns_correct_agent_for_step_0(
        self,
        authenticated_client
    ):
        """Test that step 0 returns fitness_assessment agent."""
        client, user = authenticated_client
        
        response = await client.get("/api/v1/onboarding/current-agent")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["agent_type"] == "fitness_assessment"
        assert data["current_step"] == 0
        assert "fitness" in data["agent_description"].lower()
    
    async def test_current_agent_returns_correct_agent_for_step_3(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that step 3 returns goal_setting agent."""
        # Create user with step 3
        user = User(
            id=uuid4(),
            email="step3@example.com",
            hashed_password="hashed",
            full_name="Step 3 User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=3,
            is_complete=False,
            step_data={},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Create token
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        response = await client.get("/api/v1/onboarding/current-agent")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["agent_type"] == "goal_setting"
        assert data["current_step"] == 3
        assert "goal" in data["agent_description"].lower()
    
    async def test_current_agent_includes_context_summary(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that current-agent includes context summary."""
        # Create user with agent context
        user = User(
            id=uuid4(),
            email="context@example.com",
            hashed_password="hashed",
            full_name="Context User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        agent_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "experience_years": 2
            }
        }
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=1,
            is_complete=False,
            step_data={},
            agent_context=agent_context,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Create token
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        response = await client.get("/api/v1/onboarding/current-agent")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["context_summary"] == agent_context
        assert "fitness_assessment" in data["context_summary"]


@pytest.mark.asyncio
@pytest.mark.unit
class TestEndpointIntegration:
    """Integration tests for endpoint interactions."""
    
    @patch('app.agents.onboarding.base.BaseOnboardingAgent._init_llm')
    async def test_chat_then_get_current_agent(self, mock_init_llm, authenticated_client):
        """Test that chat and current-agent endpoints work together."""
        mock_init_llm.return_value = None
        
        client, user = authenticated_client
        
        # Send chat message
        chat_response = await client.post(
            "/api/v1/onboarding/chat",
            json={"message": "Hello"}
        )
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        
        # Get current agent
        agent_response = await client.get("/api/v1/onboarding/current-agent")
        assert agent_response.status_code == 200
        agent_data = agent_response.json()
        
        # Verify consistency
        assert chat_data["agent_type"] == agent_data["agent_type"]
        assert chat_data["current_step"] == agent_data["current_step"]
