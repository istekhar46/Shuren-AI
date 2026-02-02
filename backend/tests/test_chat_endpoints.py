"""
Tests for chat endpoints.

Validates chat message sending, session management, history retrieval,
and session ending functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.chat import router
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatMessageResponse, ChatHistoryResponse


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
def mock_chat_session(mock_user):
    """Create a mock chat session."""
    return ChatSession(
        id=uuid4(),
        user_id=mock_user.id,
        session_type='general',
        status='active',
        context_data={},
        started_at=datetime.now(),
        last_activity_at=datetime.now()
    )


@pytest.fixture
def mock_chat_message(mock_chat_session):
    """Create a mock chat message."""
    return ChatMessage(
        id=uuid4(),
        session_id=mock_chat_session.id,
        role='assistant',
        content='Test response',
        agent_type='conversational',
        message_metadata={},
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


class TestSendMessage:
    """Tests for POST /api/v1/chat/message endpoint."""
    
    def test_send_message_success(self, client, mock_db, mock_chat_message):
        """Test successful message sending."""
        mock_response = ChatMessageResponse(
            id=mock_chat_message.id,
            session_id=mock_chat_message.session_id,
            role=mock_chat_message.role,
            content=mock_chat_message.content,
            agent_type=mock_chat_message.agent_type,
            created_at=mock_chat_message.created_at
        )
        
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.send_message = AsyncMock(return_value=mock_response)
            
            response = client.post(
                "/api/v1/chat/message",
                json={
                    "message": "Hello, how can I improve my workout?",
                    "session_type": "workout"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "Test response"
            assert data["role"] == "assistant"
            assert "session_id" in data
    
    def test_send_message_with_session_id(self, client, mock_db, mock_chat_message):
        """Test sending message to existing session."""
        session_id = uuid4()
        mock_response = ChatMessageResponse(
            id=mock_chat_message.id,
            session_id=session_id,
            role=mock_chat_message.role,
            content=mock_chat_message.content,
            agent_type=mock_chat_message.agent_type,
            created_at=mock_chat_message.created_at
        )
        
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.send_message = AsyncMock(return_value=mock_response)
            
            response = client.post(
                "/api/v1/chat/message",
                json={
                    "message": "Follow-up question",
                    "session_id": str(session_id)
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == str(session_id)
    
    def test_send_message_validation_error(self, client, mock_db):
        """Test message validation (empty message)."""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": ""
            }
        )
        
        assert response.status_code == 422


class TestCreateChatSession:
    """Tests for POST /api/v1/chat/sessions endpoint."""
    
    def test_create_session_success(self, client, mock_db, mock_chat_session):
        """Test successful session creation with request body."""
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.create_session = AsyncMock(return_value=mock_chat_session)
            
            response = client.post(
                "/api/v1/chat/sessions",
                json={
                    "session_type": "workout",
                    "context_data": {"goal": "strength"}
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["session_type"] == "general"
            assert data["status"] == "active"
            assert "id" in data
            assert "started_at" in data
            assert "last_activity_at" in data
            assert data["ended_at"] is None
    
    def test_create_session_no_body(self, client, mock_db, mock_chat_session):
        """Test session creation without request body defaults to 'general' type."""
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.create_session = AsyncMock(return_value=mock_chat_session)
            
            response = client.post("/api/v1/chat/sessions")
            
            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["status"] == "active"
            # Verify the service was called with default "general" type
            mock_service.create_session.assert_called_once()
            call_args = mock_service.create_session.call_args
            assert call_args[0][1].session_type == "general"
    
    def test_create_session_with_context_data(self, client, mock_db, mock_chat_session):
        """Test session creation with context data."""
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.create_session = AsyncMock(return_value=mock_chat_session)
            
            response = client.post(
                "/api/v1/chat/sessions",
                json={
                    "session_type": "meal",
                    "context_data": {"meal_plan_id": "123e4567-e89b-12d3-a456-426614174000"}
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "id" in data


class TestStartSession:
    """Tests for POST /api/v1/chat/session/start endpoint."""
    
    def test_start_session_success(self, client, mock_db, mock_chat_session):
        """Test successful session creation."""
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.create_session = AsyncMock(return_value=mock_chat_session)
            
            response = client.post(
                "/api/v1/chat/session/start",
                json={
                    "session_type": "workout",
                    "context_data": {"goal": "strength"}
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["session_type"] == "general"
            assert data["status"] == "active"
            assert "id" in data
            assert "started_at" in data
    
    def test_start_session_default_type(self, client, mock_db, mock_chat_session):
        """Test session creation with default type."""
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.create_session = AsyncMock(return_value=mock_chat_session)
            
            response = client.post(
                "/api/v1/chat/session/start",
                json={}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "id" in data


class TestGetHistory:
    """Tests for GET /api/v1/chat/history endpoint."""
    
    def test_get_history_success(self, client, mock_db, mock_chat_message):
        """Test successful history retrieval."""
        mock_response = ChatMessageResponse(
            id=mock_chat_message.id,
            session_id=mock_chat_message.session_id,
            role=mock_chat_message.role,
            content=mock_chat_message.content,
            agent_type=mock_chat_message.agent_type,
            created_at=mock_chat_message.created_at
        )
        
        mock_history = ChatHistoryResponse(
            messages=[mock_response],
            total=1,
            limit=50,
            offset=0
        )
        
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_history = AsyncMock(return_value=mock_history)
            
            response = client.get("/api/v1/chat/history")
            
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            assert len(data["messages"]) == 1
            assert data["total"] == 1
            assert data["limit"] == 50
            assert data["offset"] == 0
    
    def test_get_history_with_session_filter(self, client, mock_db, mock_chat_message):
        """Test history retrieval filtered by session."""
        session_id = uuid4()
        mock_response = ChatMessageResponse(
            id=mock_chat_message.id,
            session_id=session_id,
            role=mock_chat_message.role,
            content=mock_chat_message.content,
            agent_type=mock_chat_message.agent_type,
            created_at=mock_chat_message.created_at
        )
        
        mock_history = ChatHistoryResponse(
            messages=[mock_response],
            total=1,
            limit=50,
            offset=0
        )
        
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_history = AsyncMock(return_value=mock_history)
            
            response = client.get(f"/api/v1/chat/history?session_id={session_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["messages"]) == 1
    
    def test_get_history_with_pagination(self, client, mock_db):
        """Test history retrieval with pagination."""
        mock_history = ChatHistoryResponse(
            messages=[],
            total=100,
            limit=10,
            offset=20
        )
        
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_history = AsyncMock(return_value=mock_history)
            
            response = client.get("/api/v1/chat/history?limit=10&offset=20")
            
            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 10
            assert data["offset"] == 20
            assert data["total"] == 100


class TestEndSession:
    """Tests for DELETE /api/v1/chat/session/{session_id} endpoint."""
    
    def test_end_session_success(self, client, mock_db):
        """Test successful session ending."""
        session_id = uuid4()
        
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.end_session = AsyncMock(return_value=None)
            
            response = client.delete(f"/api/v1/chat/session/{session_id}")
            
            assert response.status_code == 204
            assert response.content == b''
    
    def test_end_session_not_found(self, client, mock_db):
        """Test ending non-existent session returns 404."""
        from fastapi import HTTPException
        
        session_id = uuid4()
        
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.end_session = AsyncMock(
                side_effect=HTTPException(status_code=404, detail="Chat session not found")
            )
            
            response = client.delete(f"/api/v1/chat/session/{session_id}")
            
            assert response.status_code == 404
    
    def test_end_session_unauthorized(self, client, mock_db):
        """Test ending another user's session returns 403."""
        from fastapi import HTTPException
        
        session_id = uuid4()
        
        with patch('app.api.v1.endpoints.chat.ChatService') as MockService:
            mock_service = MockService.return_value
            mock_service.end_session = AsyncMock(
                side_effect=HTTPException(
                    status_code=403,
                    detail="Not authorized to access this chat session"
                )
            )
            
            response = client.delete(f"/api/v1/chat/session/{session_id}")
            
            assert response.status_code == 403
