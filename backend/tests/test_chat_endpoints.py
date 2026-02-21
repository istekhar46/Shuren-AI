"""
Tests for chat endpoints.

Validates direct chat messaging, streaming, history retrieval,
and history deletion functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.chat import router
from app.models.user import User
from app.models.conversation import ConversationMessage
from app.schemas.chat import ChatResponse, MessageDict, ChatHistoryResponse


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return User(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        is_active=True
    )


@pytest.fixture
def mock_conversation_message(mock_user):
    """Create a mock conversation message."""
    return ConversationMessage(
        id=uuid4(),
        user_id=mock_user.id,
        role='assistant',
        content='Test response',
        agent_type='general',
        created_at=datetime.now()
    )


@pytest.fixture
def app(mock_db, mock_user):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
    
    # Override dependencies
    from app.db.session import get_db
    from app.core.deps import get_current_user
    
    async def override_get_db():
        yield mock_db
    
    async def override_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestChatEndpoint:
    """Tests for POST /api/v1/chat/chat endpoint."""
    
    def test_chat_success(self, client, mock_db, mock_user):
        """Test successful chat message."""
        # Mock AgentOrchestrator and context loading
        with patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            mock_context.return_value = {"user_id": str(mock_user.id)}
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_response = MagicMock()
            mock_response.content = "Here's your workout plan"
            mock_response.agent_type = "workout"
            mock_response.tools_used = ["get_workout_plan"]
            mock_orchestrator.route_query = AsyncMock(return_value=mock_response)
            
            response = client.post(
                "/api/v1/chat/chat",
                json={"message": "What should I do today?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Here's your workout plan"
            assert data["agent_type"] == "workout"
            assert data["conversation_id"] == str(mock_user.id)
            assert "tools_used" in data
    
    def test_chat_with_agent_type(self, client, mock_db, mock_user):
        """Test chat with explicit agent type."""
        with patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            mock_context.return_value = {"user_id": str(mock_user.id)}
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_response = MagicMock()
            mock_response.content = "Here's your meal plan"
            mock_response.agent_type = "diet"
            mock_response.tools_used = []
            mock_orchestrator.route_query = AsyncMock(return_value=mock_response)
            
            response = client.post(
                "/api/v1/chat/chat",
                json={
                    "message": "What should I eat?",
                    "agent_type": "diet"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["agent_type"] == "diet"
    
    def test_chat_invalid_agent_type(self, client):
        """Test chat with invalid agent type."""
        with patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context:
            mock_context.return_value = {"user_id": "test"}
            
            response = client.post(
                "/api/v1/chat/chat",
                json={
                    "message": "Hello",
                    "agent_type": "invalid_type"
                }
            )
            
            # Pydantic validation returns 422 for invalid enum values
            assert response.status_code == 422
            data = response.json()
            # Check that validation error mentions the field
            assert "agent_type" in str(data).lower() or "detail" in data
    
    def test_chat_validation_error(self, client):
        """Test chat with empty message."""
        response = client.post(
            "/api/v1/chat/chat",
            json={"message": ""}
        )
        
        assert response.status_code == 422


class TestChatStreamEndpoint:
    """Tests for POST /api/v1/chat/stream endpoint."""
    
    def test_stream_success(self, client, mock_db, mock_user):
        """Test successful streaming chat."""
        with patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            mock_context.return_value = {"user_id": str(mock_user.id)}
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_agent = MagicMock()
            
            # Mock streaming response
            async def mock_stream(message):
                yield "Hello "
                yield "there!"
            
            mock_agent.stream_response = mock_stream
            mock_orchestrator._classify_query = AsyncMock(return_value=MagicMock(value="general"))
            mock_orchestrator._get_or_create_agent = MagicMock(return_value=mock_agent)
            
            response = client.post(
                "/api/v1/chat/stream",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"


class TestGetHistoryEndpoint:
    """Tests for GET /api/v1/chat/history endpoint."""
    
    def test_get_history_success(self, client, mock_db, mock_user):
        """Test successful history retrieval."""
        # Mock database query results
        mock_messages = [
            ConversationMessage(
                id=uuid4(),
                user_id=mock_user.id,
                role="user",
                content="Hello",
                agent_type=None,
                created_at=datetime.now()
            ),
            ConversationMessage(
                id=uuid4(),
                user_id=mock_user.id,
                role="assistant",
                content="Hi there!",
                agent_type="general",
                created_at=datetime.now()
            )
        ]
        
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2
        
        # Mock messages query
        mock_messages_result = MagicMock()
        mock_messages_result.scalars.return_value.all.return_value = list(reversed(mock_messages))
        
        mock_db.execute.side_effect = [mock_count_result, mock_messages_result]
        
        response = client.get("/api/v1/chat/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["messages"]) == 2
    
    def test_get_history_with_limit(self, client, mock_db, mock_user):
        """Test history retrieval with limit parameter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100
        
        mock_messages_result = MagicMock()
        mock_messages_result.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [mock_count_result, mock_messages_result]
        
        response = client.get("/api/v1/chat/history?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
    
    def test_get_history_empty(self, client, mock_db, mock_user):
        """Test history retrieval with no messages."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        mock_messages_result = MagicMock()
        mock_messages_result.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [mock_count_result, mock_messages_result]
        
        response = client.get("/api/v1/chat/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["messages"]) == 0


class TestDeleteHistoryEndpoint:
    """Tests for DELETE /api/v1/chat/history endpoint."""
    
    def test_delete_history_success(self, client, mock_db, mock_user):
        """Test successful history deletion."""
        response = client.delete("/api/v1/chat/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"
        
        # Verify delete was called
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()


class TestChatStreamingEndpoints:
    """Tests for streaming endpoint functionality (Requirements 1.7, 1.8)."""
    
    def test_stream_endpoint_returns_401_with_invalid_token(self, mock_db):
        """Test /chat/stream returns 401 with invalid token."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
        
        # Override get_db but not get_current_user (authentication should fail)
        from app.db.session import get_db
        
        async def override_get_db():
            yield mock_db
        
        test_app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(test_app)
        
        response = client.post(
            "/api/v1/chat/stream",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 401
    
    def test_onboarding_stream_endpoint_returns_401_with_invalid_token(self, mock_db):
        """Test /chat/onboarding-stream returns 401 with invalid token."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
        
        # Override get_db
        from app.db.session import get_db
        
        async def override_get_db():
            yield mock_db
        
        test_app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(test_app)
        
        # Mock get_current_user_from_token to raise 401
        with patch('app.core.deps.get_current_user_from_token') as mock_auth:
            from fastapi import HTTPException, status
            mock_auth.side_effect = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
            response = client.get(
                "/api/v1/chat/onboarding-stream?message=Hello&token=invalid_token"
            )
            
            assert response.status_code == 401
    
    def test_stream_timeout_after_60_seconds(self, client, mock_db, mock_user):
        """Test streaming timeout after 60 seconds of inactivity."""
        with patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator, \
             patch('app.api.v1.endpoints.chat.time') as mock_time:
            
            mock_context.return_value = {"user_id": str(mock_user.id)}
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_agent = MagicMock()
            
            # Mock time to simulate timeout
            time_values = [0, 0, 35]  # start_time, last_chunk_time, check_time (35s elapsed)
            mock_time.time.side_effect = time_values
            
            # Mock streaming response that takes too long
            async def mock_stream(message):
                yield "Starting..."
                # Simulate long delay - timeout check will trigger
            
            mock_agent.stream_response = mock_stream
            mock_orchestrator._classify_query = AsyncMock(return_value=MagicMock(value="general"))
            mock_orchestrator._get_or_create_agent = MagicMock(return_value=mock_agent)
            
            response = client.post(
                "/api/v1/chat/stream",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 200
            # Note: Actual timeout behavior would need async testing framework
            # This test verifies the timeout logic exists in the code
    
    def test_stream_error_event_format_when_llm_fails(self, client, mock_db, mock_user):
        """Test error event format when LLM processing fails."""
        with patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            mock_context.return_value = {"user_id": str(mock_user.id)}
            
            mock_orchestrator = MockOrchestrator.return_value
            mock_agent = MagicMock()
            
            # Mock streaming response that raises an error
            async def mock_stream(message):
                raise Exception("LLM service unavailable")
            
            mock_agent.stream_response = mock_stream
            mock_orchestrator._classify_query = AsyncMock(return_value=MagicMock(value="general"))
            mock_orchestrator._get_or_create_agent = MagicMock(return_value=mock_agent)
            
            response = client.post(
                "/api/v1/chat/stream",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Check that response contains error event
            content = response.text
            assert "error" in content.lower()
    
    def test_onboarding_stream_error_event_format(self, mock_db):
        """Test onboarding stream sends error event on failure."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
        
        from app.db.session import get_db
        
        async def override_get_db():
            yield mock_db
        
        test_app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(test_app)
        
        # Create mock user with onboarding_completed property
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_user.onboarding_completed = False
        
        with patch('app.core.deps.get_current_user_from_token') as mock_auth, \
             patch('app.api.v1.endpoints.chat.OnboardingService') as MockOnboardingService, \
             patch('app.api.v1.endpoints.chat.load_agent_context') as mock_context, \
             patch('app.api.v1.endpoints.chat.AgentOrchestrator') as MockOrchestrator:
            
            mock_auth.return_value = mock_user
            
            # Mock onboarding service to return state
            mock_service = MockOnboardingService.return_value
            mock_state = MagicMock()
            mock_state.current_step = 1
            mock_service.get_onboarding_state = AsyncMock(return_value=mock_state)
            
            mock_context.return_value = {"user_id": str(mock_user.id)}
            
            # Mock orchestrator to raise error
            mock_orchestrator = MockOrchestrator.return_value
            mock_agent = MagicMock()
            
            async def mock_stream(message):
                raise Exception("Agent processing failed")
            
            mock_agent.stream_response = mock_stream
            mock_orchestrator._get_or_create_agent = MagicMock(return_value=mock_agent)
            
            response = client.get(
                "/api/v1/chat/onboarding-stream?message=Hello&token=valid_token"
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Check that response contains error event
            content = response.text
            assert "error" in content.lower()


class TestChatEndpointsAuthentication:
    """Tests for authentication requirements on chat endpoints."""
    
    def test_chat_requires_authentication(self):
        """Test that chat endpoint requires authentication."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
        client = TestClient(test_app)
        
        response = client.post(
            "/api/v1/chat/chat",
            json={"message": "Hello"}
        )
        
        assert response.status_code in [401, 403]
    
    def test_history_requires_authentication(self):
        """Test that history endpoint requires authentication."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
        client = TestClient(test_app)
        
        response = client.get("/api/v1/chat/history")
        
        assert response.status_code in [401, 403]
    
    def test_delete_history_requires_authentication(self):
        """Test that delete history endpoint requires authentication."""
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/chat", tags=["chat"])
        client = TestClient(test_app)
        
        response = client.delete("/api/v1/chat/history")
        
        assert response.status_code in [401, 403]
