"""
Chat endpoints for AI agent interaction.

This module provides REST API endpoints for:
- Sending messages to AI agents
- Creating and managing chat sessions
- Retrieving chat history with pagination
- Ending chat sessions
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse
)
from app.services.chat_service import ChatService


router = APIRouter()


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send message to AI agent",
    responses={
        200: {
            "description": "Message sent and response received",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "session_id": "223e4567-e89b-12d3-a456-426614174001",
                        "role": "assistant",
                        "content": "I can help you with your workout plan. What would you like to know?",
                        "agent_type": "workout_planning",
                        "created_at": "2026-01-30T10:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Session not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Chat session not found"
                    }
                }
            }
        },
        403: {
            "description": "Session belongs to different user",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authorized to access this session"
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "message"],
                                "msg": "ensure this value has at least 1 characters",
                                "type": "value_error.any_str.min_length"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def send_message(
    message_request: ChatMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ChatMessageResponse:
    """
    Send message to AI agent and receive response.
    
    Accepts a user message, routes it to the appropriate AI agent based on
    session type and context, stores both the user message and agent response,
    and returns the agent's reply. If no session_id is provided, creates or
    retrieves an active session of the specified type.
    
    **Request Body Example:**
    ```json
    {
        "message": "What exercises should I do today?",
        "session_type": "workout",
        "context_data": {
            "current_workout_day": 1
        }
    }
    ```
    
    Args:
        message_request: ChatMessageRequest with message content and optional session info
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        ChatMessageResponse with agent's reply including session_id
        
    Raises:
        HTTPException(404): If specified session_id not found
        HTTPException(403): If session belongs to different user
        HTTPException(422): If validation fails (handled by FastAPI)
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize chat service
    chat_service = ChatService(db)
    
    # Send message and get response
    response = await chat_service.send_message(current_user.id, message_request)
    
    # Return response
    return response


@router.post(
    "/session/start",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new chat session",
    responses={
        201: {
            "description": "Session created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "session_type": "workout",
                        "status": "active",
                        "started_at": "2026-01-30T10:00:00Z",
                        "ended_at": None,
                        "last_activity_at": "2026-01-30T10:00:00Z"
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "session_type"],
                                "msg": "value is not a valid enumeration member",
                                "type": "type_error.enum"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def start_session(
    session_create: ChatSessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ChatSessionResponse:
    """
    Create new chat session.
    
    Creates a new conversation context for the user with the specified session
    type and optional context data. Session types include: general, workout,
    meal, supplement, and tracking.
    
    **Request Body Example:**
    ```json
    {
        "session_type": "workout",
        "context_data": {
            "workout_plan_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    }
    ```
    
    Args:
        session_create: ChatSessionCreate with session type and optional context
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        ChatSessionResponse with new session details
        
    Raises:
        HTTPException(422): If validation fails (handled by FastAPI)
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize chat service
    chat_service = ChatService(db)
    
    # Create session
    session = await chat_service.create_session(current_user.id, session_create)
    
    # Return response
    return ChatSessionResponse(
        id=session.id,
        session_type=session.session_type,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        last_activity_at=session.last_activity_at
    )


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat history",
    responses={
        200: {
            "description": "Chat history retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "messages": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "session_id": "223e4567-e89b-12d3-a456-426614174001",
                                "role": "user",
                                "content": "What exercises should I do today?",
                                "agent_type": None,
                                "created_at": "2026-01-30T10:00:00Z"
                            },
                            {
                                "id": "323e4567-e89b-12d3-a456-426614174002",
                                "session_id": "223e4567-e89b-12d3-a456-426614174001",
                                "role": "assistant",
                                "content": "Today is Upper Body Push day. You'll be doing bench press, shoulder press, and tricep exercises.",
                                "agent_type": "workout_planning",
                                "created_at": "2026-01-30T10:00:05Z"
                            }
                        ],
                        "total": 2,
                        "limit": 50,
                        "offset": 0
                    }
                }
            }
        },
        404: {
            "description": "Session not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Chat session not found"
                    }
                }
            }
        }
    }
)
async def get_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    session_id: Optional[UUID] = Query(None, description="Optional session ID to filter messages"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip for pagination")
) -> ChatHistoryResponse:
    """
    Get chat history with pagination.
    
    Returns messages in chronological order (oldest to newest). If session_id
    is provided, returns messages for that session only. Otherwise, returns
    messages across all user's sessions. Supports pagination through limit
    and offset parameters.
    
    **Query Parameters:**
    - `session_id` (optional): Filter messages by session UUID
    - `limit` (default 50, max 100): Number of messages to return
    - `offset` (default 0): Number of messages to skip
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        session_id: Optional session ID to filter by (query parameter)
        limit: Maximum number of messages to return (default 50, max 100)
        offset: Number of messages to skip (default 0)
        
    Returns:
        ChatHistoryResponse with messages and pagination info
        
    Raises:
        HTTPException(404): If specified session_id not found
        HTTPException(403): If session belongs to different user
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize chat service
    chat_service = ChatService(db)
    
    # Get history
    history = await chat_service.get_history(
        user_id=current_user.id,
        session_id=session_id,
        limit=limit,
        offset=offset
    )
    
    # Return response
    return history


@router.delete(
    "/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="End chat session",
    responses={
        204: {
            "description": "Session ended successfully"
        },
        404: {
            "description": "Session not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Chat session not found"
                    }
                }
            }
        },
        403: {
            "description": "Session belongs to different user",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authorized to access this session"
                    }
                }
            }
        }
    }
)
async def end_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    """
    End chat session.
    
    Marks the specified chat session as completed and sets the ended_at
    timestamp. Validates that the session belongs to the authenticated user
    before ending it.
    
    Args:
        session_id: UUID of the session to end (path parameter)
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
        
    Returns:
        None (204 No Content response)
        
    Raises:
        HTTPException(404): If session not found
        HTTPException(403): If session belongs to different user
        HTTPException(401): If authentication fails (handled by dependency)
    """
    # Initialize chat service
    chat_service = ChatService(db)
    
    # End session
    await chat_service.end_session(current_user.id, session_id)
    
    # Return 204 No Content (no response body)
    return None
