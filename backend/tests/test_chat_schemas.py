"""
Unit tests for chat schemas.

Validates Pydantic schema definitions for chat-related data structures.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.schemas.chat import ChatMessageResponse


class TestChatMessageResponse:
    """Test ChatMessageResponse schema validation and serialization."""
    
    def test_schema_validation_with_valid_data(self):
        """Test ChatMessageResponse validates correctly with all required fields."""
        message_id = uuid4()
        session_id = uuid4()
        created_at = datetime.now()
        
        data = {
            "id": message_id,
            "session_id": session_id,
            "role": "assistant",
            "content": "Test response content",
            "agent_type": "workout",
            "created_at": created_at
        }
        
        response = ChatMessageResponse(**data)
        
        assert response.id == message_id
        assert response.session_id == session_id
        assert response.role == "assistant"
        assert response.content == "Test response content"
        assert response.agent_type == "workout"
        assert response.created_at == created_at
    
    def test_schema_with_optional_agent_type_none(self):
        """Test ChatMessageResponse accepts None for optional agent_type field."""
        message_id = uuid4()
        session_id = uuid4()
        created_at = datetime.now()
        
        data = {
            "id": message_id,
            "session_id": session_id,
            "role": "user",
            "content": "User message content",
            "agent_type": None,
            "created_at": created_at
        }
        
        response = ChatMessageResponse(**data)
        
        assert response.role == "user"
        assert response.agent_type is None
    
    def test_schema_serialization_from_orm_model(self):
        """Test ChatMessageResponse can serialize from ORM model with from_attributes."""
        # Create a mock ORM object
        class MockMessage:
            def __init__(self):
                self.id = uuid4()
                self.session_id = uuid4()
                self.role = "assistant"
                self.content = "ORM message content"
                self.agent_type = "diet"
                self.created_at = datetime.now()
        
        mock_message = MockMessage()
        
        # Should work with from_attributes = True in Config
        response = ChatMessageResponse.model_validate(mock_message)
        
        assert response.id == mock_message.id
        assert response.session_id == mock_message.session_id
        assert response.role == mock_message.role
        assert response.content == mock_message.content
        assert response.agent_type == mock_message.agent_type
        assert response.created_at == mock_message.created_at
