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
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    MessageDict,
    OnboardingChatRequest,
    OnboardingChatResponse
)
from app.services.agent_orchestrator import AgentOrchestrator, AgentType
from app.services.chat_service import ChatService
from app.services.context_loader import load_agent_context
from app.services.onboarding_service import OnboardingService, STATE_TO_AGENT_MAP
from app.core.metrics import get_metrics_tracker


router = APIRouter()
logger = logging.getLogger(__name__)
metrics_tracker = get_metrics_tracker()


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ChatResponse:
    """
    Send a message to the AI assistant and receive a complete response.
    
    This endpoint processes user messages through the agent orchestration system.
    Only available to users who have completed onboarding. All queries are routed
    to the general agent for completed users.
    
    The conversation is persisted to the database for context continuity and
    history retrieval.
    
    Args:
        request: ChatRequest with message and optional agent_type
        current_user: Authenticated user from JWT token
        db: Database session from dependency injection
        
    Returns:
        ChatResponse with agent's response, agent_type, conversation_id, and tools_used
        
    Raises:
        HTTPException(403): If user has not completed onboarding or requests non-general agent
        HTTPException(401): If user is not authenticated (handled by dependency)
        HTTPException(422): If validation fails (handled by FastAPI/Pydantic)
        HTTPException(500): If agent processing fails
    """
    start_time = time.time()
    user_id = str(current_user.id)
    
    try:
        # Check onboarding status - must be completed to access chat
        if not current_user.onboarding_completed:
            # Get onboarding progress for helpful error message
            from app.services.onboarding_service import OnboardingService
            onboarding_service = OnboardingService(db)
            try:
                progress = await onboarding_service.get_progress(current_user.id)
                onboarding_progress = {
                    "current_state": progress.current_state,
                    "completion_percentage": progress.completion_percentage
                }
            except Exception:
                onboarding_progress = None
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Complete onboarding to access this feature",
                    "error_code": "ONBOARDING_REQUIRED",
                    "redirect": "/onboarding",
                    "onboarding_progress": onboarding_progress
                }
            )
        
        # If explicit agent_type provided, reject if not "general"
        if request.agent_type and request.agent_type != "general":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Only general agent available after onboarding",
                    "error_code": "AGENT_NOT_ALLOWED",
                    "requested_agent": request.agent_type,
                    "allowed_agent": "general"
                }
            )
        
        # Force general agent for all completed users
        agent_type = AgentType.GENERAL
        
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
        
        # Call orchestrator.route_query() with onboarding_mode=False
        try:
            response = await orchestrator.route_query(
                user_id=user_id,
                query=request.message,
                agent_type=agent_type,
                voice_mode=False,
                onboarding_mode=False
            )
        except ValueError as e:
            # Handle access control errors from orchestrator
            logger.error(f"Orchestrator error for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
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
        # Re-raise HTTP exceptions (401, 403, 500)
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


@router.post("/onboarding", response_model=OnboardingChatResponse, status_code=status.HTTP_200_OK)
async def chat_onboarding(
    request: OnboardingChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingChatResponse:
    """
    Handle chat-based onboarding with specialized agent routing.
    
    This endpoint processes user messages during onboarding, routing them
    to the appropriate specialized agent based on the current onboarding state.
    The agent can save onboarding data via function tools, advancing the state.
    
    Args:
        request: OnboardingChatRequest with message and current_state
        current_user: Authenticated user from JWT token
        db: Database session from dependency injection
        
    Returns:
        OnboardingChatResponse with agent's response, agent_type, state_updated flag,
        new_state (if updated), and progress information
        
    Raises:
        HTTPException(403): If user has already completed onboarding
        HTTPException(400): If current_state doesn't match backend state
        HTTPException(401): If authentication fails (handled by dependency)
        HTTPException(500): If agent processing fails
    """
    start_time = time.time()
    user_id = str(current_user.id)
    
    try:
        # 1. Verify user is not onboarding_completed
        if current_user.onboarding_completed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Onboarding already completed"
            )
        
        # 2. Load onboarding state
        onboarding_service = OnboardingService(db)
        state = await onboarding_service.get_onboarding_state(current_user.id)
        
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding state not found"
            )
        
        # NEW: Store initial state for comparison
        initial_step = state.current_step
        
        # 3. Verify current_state matches
        if state.current_step != request.current_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"State mismatch. Current: {state.current_step}, Requested: {request.current_state}"
            )
        
        # 4. Route to appropriate agent based on current_state
        agent_type = STATE_TO_AGENT_MAP.get(request.current_state)
        if not agent_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state number: {request.current_state}"
            )
        
        # 5. Initialize AgentOrchestrator in text mode
        orchestrator = AgentOrchestrator(db_session=db, mode="text")
        
        # 6. Process query with agent in onboarding mode
        try:
            agent_response = await orchestrator.route_query(
                user_id=user_id,
                query=request.message,
                agent_type=agent_type,
                voice_mode=False,
                onboarding_mode=True
            )
        except ValueError as e:
            # Handle access control errors from orchestrator
            logger.error(f"Orchestrator error for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
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
        
        # 7. Check if state was updated (agent called save function)
        updated_state = await onboarding_service.get_onboarding_state(current_user.id)
        state_updated = updated_state.current_step > initial_step
        
        # 8. Get progress
        progress = await onboarding_service.get_progress(current_user.id)
        
        # 9. Save conversation messages
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
            content=agent_response.content,
            agent_type=agent_response.agent_type
        )
        db.add(assistant_message)
        
        await db.commit()
        
        # Calculate response time
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Log successful request
        logger.info(
            f"Onboarding chat processed: user={user_id}, agent={agent_response.agent_type}, "
            f"initial_state={initial_step}, final_state={updated_state.current_step}, "
            f"state_updated={state_updated}, time={elapsed_ms}ms"
        )
        
        return OnboardingChatResponse(
            response=agent_response.content,
            agent_type=agent_response.agent_type,
            state_updated=state_updated,
            new_state=updated_state.current_step if state_updated else None,
            progress={
                "current_state": progress.current_state,
                "total_states": progress.total_states,
                "completed_states": progress.completed_states,
                "completion_percentage": progress.completion_percentage,
                "is_complete": progress.is_complete,
                "can_complete": progress.can_complete
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.error(
            f"Unexpected error in onboarding chat endpoint for user {user_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/onboarding-stream", status_code=status.HTTP_200_OK)
async def chat_onboarding_stream(
    message: str = Query(..., description="User message to send to onboarding agent"),
    token: str = Query(..., description="JWT authentication token")
) -> StreamingResponse:
    """
    Stream onboarding chat responses using Server-Sent Events (SSE).
    
    This endpoint processes user messages during onboarding and streams the response
    in real-time. It routes messages to the appropriate specialized agent based on
    the current onboarding state. The agent can save onboarding data via function
    tools, advancing the state.
    
    EventSource API limitation: Cannot send custom headers, so authentication token
    must be passed as a query parameter instead of Authorization header.
    
    NOTE: Database session is managed manually within the generator to keep it alive
    during the entire streaming operation. This is required because FastAPI's
    dependency injection closes sessions after the endpoint returns, but
    StreamingResponse generators continue running after that point.
    
    Args:
        message: User message to send to onboarding agent
        token: JWT authentication token (query parameter)
        
    Returns:
        StreamingResponse: SSE stream with response chunks and completion event
        
    Raises:
        HTTPException(401): If authentication fails
        HTTPException(403): If user has already completed onboarding
        HTTPException(500): If agent processing fails (sent as error event in stream)
    """
    from app.core.deps import get_current_user_from_token
    import uuid
    
    # Generate unique message ID for tracking
    message_id = str(uuid.uuid4())
    
    # Create database session for authentication
    # This session is only for auth and will be closed before streaming
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as auth_db:
        # Authenticate user from token query parameter
        try:
            current_user = await get_current_user_from_token(token, auth_db)
        except HTTPException:
            # Re-raise authentication errors
            raise
    
    user_id = str(current_user.id)
    
    # Check if user has already completed onboarding
    if current_user.onboarding_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Onboarding already completed"
        )
    
    async def generate():
        """Async generator function for SSE streaming with managed database session"""
        # Create a new database session that will live for the entire streaming operation
        # This is the official pattern for StreamingResponse with database dependencies
        async with AsyncSessionLocal() as db:
            start_time = time.time()
            full_response = ""
            agent_type_value = None
            initial_step = None
            chunk_count = 0
            error_occurred = False
            
            # Start metrics tracking
            session_metrics = metrics_tracker.start_session(user_id, message_id)
            
            try:
                # Log stream start with user_id and message_id
                logger.info(
                    "Onboarding stream started",
                    extra={
                        "event": "stream_start",
                        "user_id": user_id,
                        "message_id": message_id,
                        "message_preview": message[:100] if len(message) > 100 else message,
                        "message_length": len(message)
                    }
                )
                # Load onboarding state
                onboarding_service = OnboardingService(db)
                state = await onboarding_service.get_onboarding_state(current_user.id)
                
                if not state:
                    error_msg = 'Onboarding state not found'
                    error_type = "state_not_found"
                    logger.error(
                        "Onboarding state not found",
                        extra={
                            "event": "stream_error",
                            "user_id": user_id,
                            "message_id": message_id,
                            "error_type": error_type
                        }
                    )
                    error_occurred = True
                    
                    # Complete metrics tracking with error
                    metrics_tracker.complete_session(
                        message_id=message_id,
                        agent_type="unknown",
                        chunk_count=chunk_count,
                        response_length=len(full_response),
                        error_type=error_type
                    )
                    
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    return
                
                initial_step = state.current_step
                
                # Route to appropriate agent based on current_state
                agent_type = STATE_TO_AGENT_MAP.get(state.current_step)
                if not agent_type:
                    error_msg = f'Invalid state number: {state.current_step}'
                    error_type = "invalid_state"
                    logger.error(
                        "Invalid onboarding state",
                        extra={
                            "event": "stream_error",
                            "user_id": user_id,
                            "message_id": message_id,
                            "error_type": error_type,
                            "state": state.current_step
                        }
                    )
                    error_occurred = True
                    
                    # Complete metrics tracking with error
                    metrics_tracker.complete_session(
                        message_id=message_id,
                        agent_type="unknown",
                        chunk_count=chunk_count,
                        response_length=len(full_response),
                        error_type=error_type
                    )
                    
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    return
                
                agent_type_value = agent_type.value
                
                # Load user context (onboarding mode)
                try:
                    context = await load_agent_context(
                        db=db,
                        user_id=user_id,
                        include_history=True,
                        onboarding_mode=True
                    )
                except ValueError as e:
                    error_msg = 'Failed to load user context'
                    logger.error(
                        "Context loading failed",
                        extra={
                            "event": "stream_error",
                            "user_id": user_id,
                            "message_id": message_id,
                            "error_type": "context_load_failed",
                            "error_message": str(e)
                        }
                    )
                    error_occurred = True
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    return
                
                # Initialize AgentOrchestrator in text mode
                orchestrator = AgentOrchestrator(db_session=db, mode="text")
                
                # Get or create agent instance
                agent = orchestrator._get_or_create_agent(agent_type, context)
                
                # Stream response chunks via agent.stream_response()
                # Note: Agent tools may be called during streaming and need db_session
                try:
                    async for chunk in agent.stream_response(message):
                        full_response += chunk
                        chunk_count += 1
                        # Send each chunk as SSE data event with JSON payload
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    
                    # Check if state was updated (agent called save function)
                    updated_state = await onboarding_service.get_onboarding_state(current_user.id)
                    state_updated = updated_state.current_step > initial_step
                    
                    # Get progress
                    progress = await onboarding_service.get_progress(current_user.id)
                    
                    # Send final event with "done: true", agent_type, and progress info
                    yield f"data: {json.dumps({
                        'done': True,
                        'agent_type': agent_type_value,
                        'state_updated': state_updated,
                        'new_state': updated_state.current_step if state_updated else None,
                        'progress': {
                            'current_state': progress.current_state,
                            'total_states': progress.total_states,
                            'completed_states': progress.completed_states,
                            'completion_percentage': progress.completion_percentage,
                            'is_complete': progress.is_complete,
                            'can_complete': progress.can_complete
                        }
                    })}\n\n"
                    
                except Exception as e:
                    error_msg = 'Failed to process message'
                    logger.error(
                        "Agent streaming failed",
                        extra={
                            "event": "stream_error",
                            "user_id": user_id,
                            "message_id": message_id,
                            "error_type": "agent_streaming_failed",
                            "error_message": str(e),
                            "agent_type": agent_type_value,
                            "chunks_sent": chunk_count
                        },
                        exc_info=True
                    )
                    error_occurred = True
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    return
                
                # Save user message and complete assistant response after streaming
                try:
                    user_message = ConversationMessage(
                        user_id=current_user.id,
                        role="user",
                        content=message,
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
                        "Failed to save conversation",
                        extra={
                            "event": "database_save_failed",
                            "user_id": user_id,
                            "message_id": message_id,
                            "error_type": "conversation_save_failed",
                            "error_message": str(e)
                        },
                        exc_info=True
                    )
                    # Mark database save failure in metrics
                    metrics_tracker.mark_database_save_failed(message_id)
                    # Don't send error to client since streaming already completed
                
                # Calculate response time and metrics
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                # Complete metrics tracking
                metrics_tracker.complete_session(
                    message_id=message_id,
                    agent_type=agent_type_value,
                    chunk_count=chunk_count,
                    response_length=len(full_response),
                    error_type=None
                )
                
                # Log stream completion with duration and chunk count
                logger.info(
                    "Onboarding stream completed",
                    extra={
                        "event": "stream_complete",
                        "user_id": user_id,
                        "message_id": message_id,
                        "agent_type": agent_type_value,
                        "initial_state": initial_step,
                        "final_state": updated_state.current_step,
                        "state_updated": state_updated,
                        "duration_ms": elapsed_ms,
                        "chunk_count": chunk_count,
                        "response_length": len(full_response)
                    }
                )
                
            except Exception as e:
                # Handle errors with error events in stream
                logger.error(
                    "Unexpected error in onboarding streaming",
                    extra={
                        "event": "stream_error",
                        "user_id": user_id,
                        "message_id": message_id,
                        "error_type": "unexpected_error",
                        "error_message": str(e)
                    },
                    exc_info=True
                )
                error_occurred = True
                
                # Complete metrics tracking with error
                if agent_type_value:
                    metrics_tracker.complete_session(
                        message_id=message_id,
                        agent_type=agent_type_value or "unknown",
                        chunk_count=chunk_count,
                        response_length=len(full_response),
                        error_type="unexpected_error"
                    )
                
                yield f"data: {json.dumps({'error': 'An unexpected error occurred'})}\n\n"
            finally:
                # Log cleanup event
                if error_occurred:
                    logger.info(
                        "Onboarding stream cleanup after error",
                        extra={
                            "event": "stream_cleanup",
                            "user_id": user_id,
                            "message_id": message_id,
                            "duration_ms": int((time.time() - start_time) * 1000),
                            "chunks_sent": chunk_count,
                            "error": True
                        }
                    )
    
    # Return StreamingResponse with SSE headers
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
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
    import uuid
    
    user_id = str(current_user.id)
    # Generate unique message ID for tracking
    message_id = str(uuid.uuid4())
    
    async def generate():
        """Async generator function for SSE streaming"""
        start_time = time.time()
        full_response = ""
        agent_type_value = None
        last_chunk_time = time.time()
        chunk_count = 0
        error_occurred = False
        
        # Start metrics tracking
        session_metrics = metrics_tracker.start_session(user_id, message_id)
        
        try:
            # Log stream start with user_id and message_id
            logger.info(
                "Chat stream started",
                extra={
                    "event": "stream_start",
                    "user_id": user_id,
                    "message_id": message_id,
                    "message_preview": request.message[:100] if len(request.message) > 100 else request.message,
                    "message_length": len(request.message),
                    "requested_agent_type": request.agent_type
                }
            )
            # Parse optional agent_type from request
            agent_type = None
            if request.agent_type:
                try:
                    agent_type = AgentType(request.agent_type)
                except ValueError:
                    error_msg = f'Invalid agent_type. Must be one of: workout, diet, supplement, tracker, scheduler, general'
                    logger.error(
                        "Invalid agent_type provided",
                        extra={
                            "event": "stream_error",
                            "user_id": user_id,
                            "message_id": message_id,
                            "error_type": "invalid_agent_type",
                            "requested_agent_type": request.agent_type
                        }
                    )
                    error_occurred = True
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    return
            
            # Load user context
            try:
                context = await load_agent_context(
                    db=db,
                    user_id=user_id,
                    include_history=True
                )
            except ValueError as e:
                error_msg = 'Failed to load user context'
                logger.error(
                    "Context loading failed",
                    extra={
                        "event": "stream_error",
                        "user_id": user_id,
                        "message_id": message_id,
                        "error_type": "context_load_failed",
                        "error_message": str(e)
                    }
                )
                error_occurred = True
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                return
            
            # Initialize AgentOrchestrator in text mode
            orchestrator = AgentOrchestrator(db_session=db, mode="text")
            
            # Classify query if agent_type not provided
            if agent_type is None:
                try:
                    agent_type = await orchestrator._classify_query(request.message)
                except Exception as e:
                    error_msg = 'Failed to classify query'
                    logger.error(
                        "Query classification failed",
                        extra={
                            "event": "stream_error",
                            "user_id": user_id,
                            "message_id": message_id,
                            "error_type": "classification_failed",
                            "error_message": str(e)
                        }
                    )
                    error_occurred = True
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    return
            
            agent_type_value = agent_type.value
            
            # Get or create agent instance
            agent = orchestrator._get_or_create_agent(agent_type, context)
            
            # Stream response chunks via agent.stream_response()
            try:
                async for chunk in agent.stream_response(request.message):
                    full_response += chunk
                    chunk_count += 1
                    last_chunk_time = time.time()
                    
                    # Send each chunk as SSE data event with JSON payload
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    
                    # Check for timeout (30 seconds of no chunks)
                    if time.time() - last_chunk_time > 30:
                        error_msg = 'Stream timeout - no response from AI'
                        logger.warning(
                            "Stream timeout",
                            extra={
                                "event": "stream_timeout",
                                "user_id": user_id,
                                "message_id": message_id,
                                "timeout_seconds": 30,
                                "chunks_sent": chunk_count
                            }
                        )
                        error_occurred = True
                        yield f"data: {json.dumps({'error': error_msg})}\n\n"
                        return
                
                # Send final event with "done: true" and agent_type
                yield f"data: {json.dumps({'done': True, 'agent_type': agent_type_value})}\n\n"
                
            except Exception as e:
                error_msg = 'Failed to process message'
                logger.error(
                    "Agent streaming failed",
                    extra={
                        "event": "stream_error",
                        "user_id": user_id,
                        "message_id": message_id,
                        "error_type": "agent_streaming_failed",
                        "error_message": str(e),
                        "agent_type": agent_type_value,
                        "chunks_sent": chunk_count
                    },
                    exc_info=True
                )
                error_occurred = True
                # Send error event before closing stream
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
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
                    "Failed to save conversation",
                    extra={
                        "event": "database_save_failed",
                        "user_id": user_id,
                        "message_id": message_id,
                        "error_type": "conversation_save_failed",
                        "error_message": str(e)
                    },
                    exc_info=True
                )
                # Mark database save failure in metrics
                metrics_tracker.mark_database_save_failed(message_id)
                # Don't send error to client since streaming already completed
            
            # Calculate response time and metrics
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Complete metrics tracking
            metrics_tracker.complete_session(
                message_id=message_id,
                agent_type=agent_type_value,
                chunk_count=chunk_count,
                response_length=len(full_response),
                error_type=None
            )
            
            # Log stream completion with duration and chunk count
            logger.info(
                "Chat stream completed",
                extra={
                    "event": "stream_complete",
                    "user_id": user_id,
                    "message_id": message_id,
                    "agent_type": agent_type_value,
                    "duration_ms": elapsed_ms,
                    "chunk_count": chunk_count,
                    "response_length": len(full_response)
                }
            )
            
        except Exception as e:
            # Handle errors with error events in stream
            logger.error(
                "Unexpected error in streaming",
                extra={
                    "event": "stream_error",
                    "user_id": user_id,
                    "message_id": message_id,
                    "error_type": "unexpected_error",
                    "error_message": str(e)
                },
                exc_info=True
            )
            error_occurred = True
            
            # Complete metrics tracking with error
            if agent_type_value:
                metrics_tracker.complete_session(
                    message_id=message_id,
                    agent_type=agent_type_value or "unknown",
                    chunk_count=chunk_count,
                    response_length=len(full_response),
                    error_type="unexpected_error"
                )
            
            # Send error event before closing stream
            yield f"data: {json.dumps({'error': 'An unexpected error occurred'})}\n\n"
        finally:
            # Log cleanup event
            if error_occurred:
                logger.info(
                    "Chat stream cleanup after error",
                    extra={
                        "event": "stream_cleanup",
                        "user_id": user_id,
                        "message_id": message_id,
                        "duration_ms": int((time.time() - start_time) * 1000),
                        "chunks_sent": chunk_count,
                        "error": True
                    }
                )
    
    # Return StreamingResponse with proper SSE headers
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )



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
