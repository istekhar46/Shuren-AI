"""Chat API Pydantic schemas for text-based chat interactions"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """
    Schema for sending a chat message to the AI assistant.
    
    The message will be processed by the appropriate specialized agent,
    either through automatic classification or explicit agent_type selection.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Message content to send to the AI assistant (1-2000 characters)"
    )
    agent_type: Optional[str] = Field(
        None,
        description="Optional explicit agent type: workout, diet, supplement, tracker, scheduler, general"
    )
    
    @field_validator('agent_type')
    @classmethod
    def validate_agent_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate agent_type is one of the allowed values"""
        if v is not None:
            allowed_types = {'workout', 'diet', 'supplement', 'tracker', 'scheduler', 'general'}
            if v not in allowed_types:
                raise ValueError(
                    f"Invalid agent_type '{v}'. Must be one of: {', '.join(sorted(allowed_types))}"
                )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What exercises should I do today?",
                "agent_type": "workout"
            }
        }


class ChatResponse(BaseModel):
    """
    Schema for chat response from the AI assistant.
    
    Contains the agent's response along with metadata about which agent
    handled the request and what tools were used during processing.
    """
    response: str = Field(
        ...,
        description="The agent's response text"
    )
    agent_type: str = Field(
        ...,
        description="Type of agent that handled this request (workout, diet, supplement, tracker, scheduler, general)"
    )
    conversation_id: str = Field(
        ...,
        description="User ID serving as conversation identifier"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools/functions called by the agent during processing"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on your fitness level and goals, I recommend starting with...",
                "agent_type": "workout",
                "conversation_id": "user-123",
                "tools_used": ["get_workout_plan", "calculate_calories"]
            }
        }


class MessageDict(BaseModel):
    """
    Schema for a single message in conversation history.
    
    Represents either a user message or an assistant response with
    associated metadata.
    """
    role: str = Field(
        ...,
        description="Message role: 'user' or 'assistant'"
    )
    content: str = Field(
        ...,
        description="Message content text"
    )
    agent_type: Optional[str] = Field(
        None,
        description="Type of agent that generated this message (only for assistant messages)"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the message was created"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What should I eat for breakfast?",
                "agent_type": None,
                "created_at": "2026-02-06T10:30:00Z"
            }
        }


class ChatMessageResponse(BaseModel):
    """
    Schema for individual chat message response.
    
    Used for returning single message data in chat operations,
    particularly for session-based messaging and test mocking.
    """
    id: UUID = Field(..., description="Unique message identifier")
    session_id: UUID = Field(..., description="Chat session identifier")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content text")
    agent_type: Optional[str] = Field(
        None,
        description="Agent type for assistant messages"
    )
    created_at: datetime = Field(..., description="Message creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "session_id": "123e4567-e89b-12d3-a456-426614174001",
                "role": "assistant",
                "content": "Based on your fitness level, I recommend...",
                "agent_type": "workout",
                "created_at": "2026-02-06T10:30:00Z"
            }
        }


class ChatHistoryResponse(BaseModel):
    """
    Schema for chat history response.
    
    Contains a list of messages in chronological order along with
    the total count of messages in the user's conversation history.
    """
    messages: List[MessageDict] = Field(
        ...,
        description="List of messages in chronological order (oldest to newest)"
    )
    total: int = Field(
        ...,
        description="Total number of messages in the user's conversation history"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "content": "What should I eat for breakfast?",
                        "agent_type": None,
                        "created_at": "2026-02-06T10:30:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "Based on your meal plan, I recommend...",
                        "agent_type": "diet",
                        "created_at": "2026-02-06T10:30:05Z"
                    }
                ],
                "total": 42
            }
        }
