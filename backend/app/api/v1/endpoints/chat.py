"""
Chat endpoints for text-based AI assistant interactions.

This module provides REST API endpoints for:
- Synchronous chat with AI agents
- Streaming chat with Server-Sent Events
- Conversation history retrieval
- Conversation history deletion
"""

import json
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.conversation import ConversationMessage
from app.models.user import User
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse, MessageDict
from app.services.agent_orchestrator import AgentOrchestrator, AgentType
from app.services.chat_service import ChatService
from app.services.context_loader import load_agent_context


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ChatResponse:
    """
    Send a message to the AI assistant and receive a complete response.
    
    This endpoint processes user messages through the agent orchestration system,
    which automatically routes queries to the appropriate specialized agent or
    uses an explicitly specified agent type.
    
    The conversation is persisted to the database for context continuity and
    history retrieval.
    
    Args:
        request: ChatRequest with message and optional agent_type
        current_user: Authenticated user from JWT token
        db: Database session from dependency injection
        
    Returns:
        ChatResponse with agent's response, agent_type, conversation_id, and tools_used
        
    Raises:
        HTTPException(401): If user is not authenticated (handled by dependency)
        HTTPException(422): If validation fails (handled by FastAPI/Pydantic)
        HTTPException(400): If agent_type is invalid
        HTTPException(500): If agent processing fails
    """
    start_time = time.time()
    user_id = str(current_user.id)
    
    try:
        # Parse optional agent_type from request
        agent_type = None
        if request.agent_type:
            try:
                agent_type = AgentType(request.agent_type)
            except ValueError:
                logger.info(
                    f"Invalid agent_type '{request.agent_type}' provided by user {user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid agent_type '{request.agent_type}'. "
                           f"Must be one of: workout, diet, supplement, tracker, scheduler, general"
                )
        
        # Load user context
        try:
            context = await load_agent_context(
                db=db,
                user_id=user_id,
                include_history=True
            )
        except ValueError as e:
            logger.error(f"Context loading failed for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load user context"
            )
        
        # Initialize AgentOrchestrator in text mode
        orchestrator = AgentOrchestrator(db_session=db, mode="text")
        
        # Call orchestrator.route_query() with user context
        try:
            response = await orchestrator.route_query(
                user_id=user_id,
                query=request.message,
                agent_type=agent_type,
                voice_mode=False
            )
        except Exception as e:
            logger.error(
                f"Agent processing failed for user {user_id}, "
                f"query: {request.message[:50]}, error: {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process message"
            )
        
        # Save user message to database (role="user")
        user_message = ConversationMessage(
            user_id=current_user.id,
            role="user",
            content=request.message,
            agent_type=None
        )
        db.add(user_message)
        
        # Save assistant response to database (role="assistant", agent_type from response)
        assistant_message = ConversationMessage(
            user_id=current_user.id,
            role="assistant",
            content=response.content,
            agent_type=response.agent_type
        )
        db.add(assistant_message)
        
        # Commit transaction
        await db.commit()
        
        # Calculate response time
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Log successful request
        logger.info(
            f"Chat processed: user={user_id}, agent={response.agent_type}, "
            f"time={elapsed_ms}ms"
        )
        
        # Return ChatResponse
        return ChatResponse(
            response=response.content,
            agent_type=response.agent_type,
            conversation_id=user_id,
            tools_used=response.tools_used
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (401, 400, 500)
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.error(
            f"Unexpected error in chat endpoint for user {user_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/stream", status_code=status.HTTP_200_OK)
async def chat_stream(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> StreamingResponse:
    """
    Send a message to the AI assistant and receive a streaming response.
    
    This endpoint processes user messages through the agent orchestration system
    and streams the response in real-time using Server-Sent Events (SSE). This
    provides a better user experience by showing text as it's generated rather
    than waiting for the complete response.
    
    The conversation is persisted to the database after streaming completes.
    
    Args:
        request: ChatRequest with message and optional agent_type
        current_user: Authenticated user from JWT token
        db: Database session from dependency injection
        
    Returns:
        StreamingResponse: SSE stream with response chunks and completion event
        
    Raises:
        HTTPException(401): If user is not authenticated (handled by dependency)
        HTTPException(422): If validation fails (handled by FastAPI/Pydantic)
        HTTPException(400): If agent_type is invalid
        Error events in stream: If agent processing fails
    """
    user_id = str(current_user.id)
    
    async def generate():
        """Async generator function for SSE streaming"""
        start_time = time.time()
        full_response = ""
        agent_type_value = None
        
        try:
            # Parse optional agent_type from request
            agent_type = None
            if request.agent_type:
                try:
                    agent_type = AgentType(request.agent_type)
                except ValueError:
                    logger.info(
                        f"Invalid agent_type '{request.agent_type}' provided by user {user_id}"
                    )
                    yield f"data: {json.dumps({'error': f'Invalid agent_type. Must be one of: workout, diet, supplement, tracker, scheduler, general'})}\n\n"
                    return
            
            # Load user context
            try:
                context = await load_agent_context(
                    db=db,
                    user_id=user_id,
                    include_history=True
                )
            except ValueError as e:
                logger.error(f"Context loading failed for user {user_id}: {e}")
                yield f"data: {json.dumps({'error': 'Failed to load user context'})}\n\n"
                return
            
            # Initialize AgentOrchestrator in text mode
            orchestrator = AgentOrchestrator(db_session=db, mode="text")
            
            # Classify query if agent_type not provided
            if agent_type is None:
                try:
                    agent_type = await orchestrator._classify_query(request.message)
                except Exception as e:
                    logger.error(f"Query classification failed for user {user_id}: {e}")
                    yield f"data: {json.dumps({'error': 'Failed to classify query'})}\n\n"
                    return
            
            agent_type_value = agent_type.value
            
            # Get or create agent instance
            agent = orchestrator._get_or_create_agent(agent_type, context)
            
            # Stream response chunks via agent.stream_response()
            try:
                async for chunk in agent.stream_response(request.message):
                    full_response += chunk
                    # Send each chunk as SSE data event with JSON payload
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Send final event with "done: true" and agent_type
                yield f"data: {json.dumps({'done': True, 'agent_type': agent_type_value})}\n\n"
                
            except Exception as e:
                logger.error(
                    f"Agent streaming failed for user {user_id}, "
                    f"query: {request.message[:50]}, error: {e}",
                    exc_info=True
                )
                yield f"data: {json.dumps({'error': 'Failed to process message'})}\n\n"
                return
            
            # Save user message and complete assistant response after streaming
            try:
                user_message = ConversationMessage(
                    user_id=current_user.id,
                    role="user",
                    content=request.message,
                    agent_type=None
                )
                db.add(user_message)
                
                assistant_message = ConversationMessage(
                    user_id=current_user.id,
                    role="assistant",
                    content=full_response,
                    agent_type=agent_type_value
                )
                db.add(assistant_message)
                
                # Commit transaction
                await db.commit()
                
            except Exception as e:
                logger.error(
                    f"Failed to save conversation for user {user_id}: {e}",
                    exc_info=True
                )
                # Don't send error to client since streaming already completed
            
            # Calculate response time
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Add logging for streaming requests
            logger.info(
                f"Chat stream processed: user={user_id}, agent={agent_type_value}, "
                f"time={elapsed_ms}ms, chunks={len(full_response)}"
            )
            
        except Exception as e:
            # Handle errors with error events in stream
            logger.error(
                f"Unexpected error in streaming endpoint for user {user_id}: {e}",
                exc_info=True
            )
            yield f"data: {json.dumps({'error': 'An unexpected error occurred'})}\n\n"
    
    # Return StreamingResponse with media_type="text/event-stream"
    return StreamingResponse(generate(), media_type="text/event-stream")



@router.get("/history", response_model=ChatHistoryResponse, status_code=status.HTTP_200_OK)
async def get_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of messages to return")
) -> ChatHistoryResponse:
    """
    Retrieve conversation history for the authenticated user.
    
    Returns messages in chronological order (oldest to newest) with metadata
    including role, content, agent_type, and timestamp. The limit parameter
    controls how many recent messages to return.
    
    Args:
        current_user: Authenticated user from JWT token
        db: Database session from dependency injection
        limit: Maximum number of messages to return (default 50, max 200)
        
    Returns:
        ChatHistoryResponse with messages list and total count
        
    Raises:
        HTTPException(401): If user is not authenticated (handled by dependency)
    """
    user_id = current_user.id
    
    try:
        # Get total count of user's messages
        count_stmt = select(func.count()).select_from(ConversationMessage).where(
            ConversationMessage.user_id == user_id
        )
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar() or 0
        
        # Query ConversationMessage table filtered by user_id
        # Order by created_at DESC, apply limit
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.user_id == user_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        # Reverse messages to chronological order (oldest to newest)
        messages = list(reversed(messages))
        
        # Format messages with role, content, agent_type, created_at
        formatted_messages = [
            MessageDict(
                role=msg.role,
                content=msg.content,
                agent_type=msg.agent_type,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
        # Return ChatHistoryResponse with messages and total
        return ChatHistoryResponse(
            messages=formatted_messages,
            total=total_count
        )
        
    except Exception as e:
        logger.error(
            f"Failed to retrieve chat history for user {user_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )


@router.delete("/history", status_code=status.HTTP_200_OK)
async def delete_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """
    Delete all conversation history for the authenticated user.
    
    This permanently removes all conversation messages (both user and assistant)
    for the authenticated user. This operation cannot be undone.
    
    Args:
        current_user: Authenticated user from JWT token
        db: Database session from dependency injection
        
    Returns:
        Success status dictionary: {"status": "cleared"}
        
    Raises:
        HTTPException(401): If user is not authenticated (handled by dependency)
    """
    user_id = current_user.id
    
    try:
        # Delete all ConversationMessage records for user_id
        stmt = delete(ConversationMessage).where(
            ConversationMessage.user_id == user_id
        )
        
        await db.execute(stmt)
        
        # Commit transaction
        await db.commit()
        
        logger.info(f"Chat history cleared for user {user_id}")
        
        # Return success status
        return {"status": "cleared"}
        
    except Exception as e:
        logger.error(
            f"Failed to delete chat history for user {user_id}: {e}",
            exc_info=True
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation history"
        )
