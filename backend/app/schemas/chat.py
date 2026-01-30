"""Chat Pydantic schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """
    Schema for sending a chat message.
    
    Used to send a message to an AI agent. Can optionally specify a session
    to continue an existing conversation, or create a new session.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message content to send to the AI agent (1-5000 characters)"
    )
    session_id: Optional[UUID] = Field(
        None,
        description="Optional session ID to continue existing conversation. If not provided, creates or retrieves active session."
    )
    session_type: Optional[str] = Field(
        default='general',
        description="Session type: general, workout, meal, supplement, tracking. Used when creating new session."
    )
    context_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional context data for the session (e.g., current workout day, meal plan ID)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What exercises should I do today?",
                "session_type": "workout",
                "context_data": {
                    "current_workout_day": 1
                }
            }
        }


class ChatSessionCreate(BaseModel):
    """
    Schema for creating a new chat session.
    
    Used to explicitly create a new conversation context with the AI agent.
    Session type determines which specialized agent will handle the conversation.
    """
    session_type: str = Field(
        default='general',
        description="Session type: general, workout, meal, supplement, tracking. Determines which AI agent handles the conversation."
    )
    context_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional context data to initialize the session (e.g., workout_plan_id, meal_plan_id)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_type": "workout",
                "context_data": {
                    "workout_plan_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }


class ChatMessageResponse(BaseModel):
    """
    Schema for chat message response.
    
    Represents a single message in a conversation, either from the user
    or from the AI agent.
    """
    id: UUID = Field(..., description="Unique identifier for this message")
    session_id: UUID = Field(..., description="Session this message belongs to")
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content text")
    agent_type: Optional[str] = Field(
        None,
        description="Type of AI agent that generated this message (for assistant messages): workout_planning, diet_planning, supplement_guidance, tracking_adjustment, scheduling_reminder, conversational"
    )
    created_at: datetime = Field(..., description="Timestamp when the message was created")
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """
    Schema for chat session response.
    
    Represents a conversation context between the user and AI agent,
    including session metadata and status.
    """
    id: UUID = Field(..., description="Unique identifier for this session")
    session_type: str = Field(..., description="Session type: general, workout, meal, supplement, tracking")
    status: str = Field(..., description="Session status: active, completed, abandoned")
    started_at: datetime = Field(..., description="Timestamp when the session was started")
    ended_at: Optional[datetime] = Field(None, description="Timestamp when the session was ended (null if still active)")
    last_activity_at: datetime = Field(..., description="Timestamp of last message in this session")
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """
    Schema for chat history response with pagination.
    
    Contains a list of messages with pagination metadata. Messages are
    returned in chronological order (oldest to newest).
    """
    messages: List[ChatMessageResponse] = Field(..., description="List of messages in chronological order")
    total: int = Field(..., description="Total number of messages available (across all pages)")
    limit: int = Field(..., description="Maximum number of messages returned in this response")
    offset: int = Field(..., description="Number of messages skipped (for pagination)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [],
                "total": 42,
                "limit": 50,
                "offset": 0
            }
        }
