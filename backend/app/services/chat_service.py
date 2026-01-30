"""Chat service for managing chat sessions and messages."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)


class ChatService:
    """Service for managing chat sessions and messages.
    
    Handles chat session lifecycle, message storage and retrieval,
    and routing to AI agents (placeholder for future integration).
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize chat service.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def create_session(
        self,
        user_id: UUID,
        create: ChatSessionCreate
    ) -> ChatSession:
        """Create new chat session.
        
        Creates a new conversation context for the user with specified
        session type and optional context data.
        
        Args:
            user_id: User's unique identifier
            create: Session creation parameters
            
        Returns:
            Created ChatSession
        """
        session = ChatSession(
            user_id=user_id,
            session_type=create.session_type,
            context_data=create.context_data or {},
            status='active',
            started_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow()
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def get_or_create_session(
        self,
        user_id: UUID,
        session_type: str,
        session_id: Optional[UUID] = None
    ) -> ChatSession:
        """Get existing session or create new one.
        
        If session_id is provided, retrieves that session (verifying ownership).
        Otherwise, looks for an active session of the specified type, or creates
        a new one if none exists.
        
        Args:
            user_id: User's unique identifier
            session_type: Type of session (general, workout, meal, etc.)
            session_id: Optional specific session ID to retrieve
            
        Returns:
            Existing or newly created ChatSession
            
        Raises:
            HTTPException: 404 if specified session_id not found
            HTTPException: 403 if session belongs to different user
        """
        # If session_id provided, retrieve that specific session
        if session_id:
            result = await self.db.execute(
                select(ChatSession)
                .where(
                    ChatSession.id == session_id,
                    ChatSession.deleted_at.is_(None)
                )
            )
            session = result.scalar_one_or_none()
            
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="Chat session not found"
                )
            
            # Verify ownership
            if session.user_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access this chat session"
                )
            
            # Update last activity
            session.last_activity_at = datetime.utcnow()
            await self.db.commit()
            
            return session
        
        # Look for active session of this type
        result = await self.db.execute(
            select(ChatSession)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.session_type == session_type,
                ChatSession.status == 'active',
                ChatSession.deleted_at.is_(None)
            )
            .order_by(ChatSession.last_activity_at.desc())
            .limit(1)
        )
        session = result.scalar_one_or_none()
        
        if session:
            # Update last activity
            session.last_activity_at = datetime.utcnow()
            await self.db.commit()
            return session
        
        # Create new session
        create_data = ChatSessionCreate(
            session_type=session_type,
            context_data={}
        )
        return await self.create_session(user_id, create_data)
    
    async def end_session(self, user_id: UUID, session_id: UUID) -> None:
        """End chat session by marking it as completed.
        
        Updates session status to 'completed' and sets ended_at timestamp.
        Validates user ownership before ending session.
        
        Args:
            user_id: User's unique identifier
            session_id: Session ID to end
            
        Raises:
            HTTPException: 404 if session not found
            HTTPException: 403 if session belongs to different user
        """
        result = await self.db.execute(
            select(ChatSession)
            .where(
                ChatSession.id == session_id,
                ChatSession.deleted_at.is_(None)
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )
        
        # Verify ownership
        if session.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this chat session"
            )
        
        # Update session status
        session.status = 'completed'
        session.ended_at = datetime.utcnow()
        session.last_activity_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def send_message(
        self,
        user_id: UUID,
        request: ChatMessageRequest
    ) -> ChatMessageResponse:
        """Send message to AI agent and receive response.
        
        Stores user message, routes to appropriate AI agent (placeholder),
        stores agent response, and returns the response message.
        Updates session last_activity_at timestamp.
        
        Args:
            user_id: User's unique identifier
            request: Message request with content and optional session info
            
        Returns:
            ChatMessageResponse with agent's reply
            
        Raises:
            HTTPException: 404 if session not found
            HTTPException: 403 if session belongs to different user
        """
        # Get or create session
        session = await self.get_or_create_session(
            user_id=user_id,
            session_type=request.session_type or 'general',
            session_id=request.session_id
        )
        
        # Store user message
        user_message = ChatMessage(
            session_id=session.id,
            role='user',
            content=request.message,
            agent_type=None,
            message_metadata=request.context_data or {}
        )
        self.db.add(user_message)
        
        # Route to AI agent and get response (placeholder)
        agent_response_content = await self.route_to_agent(
            message=request.message,
            context={
                'session_type': session.session_type,
                'session_context': session.context_data,
                'message_context': request.context_data or {}
            }
        )
        
        # Store agent response
        agent_message = ChatMessage(
            session_id=session.id,
            role='assistant',
            content=agent_response_content,
            agent_type='conversational',  # Default agent type
            message_metadata={}
        )
        self.db.add(agent_message)
        
        # Update session activity
        session.last_activity_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(agent_message)
        
        # Return agent message as response
        return ChatMessageResponse(
            id=agent_message.id,
            session_id=agent_message.session_id,
            role=agent_message.role,
            content=agent_message.content,
            agent_type=agent_message.agent_type,
            created_at=agent_message.created_at
        )
    
    async def get_history(
        self,
        user_id: UUID,
        session_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> ChatHistoryResponse:
        """Retrieve chat history with pagination.
        
        Returns messages in chronological order (oldest to newest).
        If session_id provided, returns messages for that session only.
        Otherwise, returns messages across all user's sessions.
        
        Args:
            user_id: User's unique identifier
            session_id: Optional session ID to filter by
            limit: Maximum number of messages to return (default 50)
            offset: Number of messages to skip (default 0)
            
        Returns:
            ChatHistoryResponse with messages and pagination info
            
        Raises:
            HTTPException: 404 if specified session not found
            HTTPException: 403 if session belongs to different user
        """
        # Build base query
        query = (
            select(ChatMessage)
            .join(ChatSession)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.deleted_at.is_(None),
                ChatMessage.deleted_at.is_(None)
            )
        )
        
        # Filter by session if provided
        if session_id:
            # Verify session exists and belongs to user
            session_result = await self.db.execute(
                select(ChatSession)
                .where(
                    ChatSession.id == session_id,
                    ChatSession.deleted_at.is_(None)
                )
            )
            session = session_result.scalar_one_or_none()
            
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="Chat session not found"
                )
            
            if session.user_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access this chat session"
                )
            
            query = query.where(ChatMessage.session_id == session_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get messages with pagination, ordered chronologically
        query = (
            query
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(query)
        messages = result.scalars().all()
        
        # Convert to response models
        message_responses = [
            ChatMessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                agent_type=msg.agent_type,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
        return ChatHistoryResponse(
            messages=message_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    
    async def route_to_agent(self, message: str, context: dict) -> str:
        """Route message to appropriate AI agent and get response.
        
        PLACEHOLDER: This method currently returns a simple placeholder response.
        
        TODO: Integrate with LiveKit agents for actual AI-powered responses.
        Future implementation will:
        - Analyze message content and context to determine appropriate agent
        - Route to one of six specialized agents:
          * Workout Planning Agent
          * Diet Planning Agent
          * Supplement Guidance Agent
          * Tracking & Adjustment Agent
          * Scheduling & Reminder Agent
          * Conversational General Assistant
        - Handle agent responses and format for chat interface
        - Support both text and voice modalities through LiveKit
        
        Args:
            message: User's message content
            context: Context data including session type and metadata
            
        Returns:
            Agent's response as string
        """
        # Placeholder response based on session type
        session_type = context.get('session_type', 'general')
        
        if session_type == 'workout':
            return (
                "I'm your workout planning assistant. I can help you with exercise "
                "selection, form tips, and workout adjustments. How can I assist you today?"
            )
        elif session_type == 'meal':
            return (
                "I'm your nutrition assistant. I can help you with meal planning, "
                "macro tracking, and dietary questions. What would you like to know?"
            )
        elif session_type == 'supplement':
            return (
                "I'm your supplement guidance assistant. I can provide information "
                "about supplements (not medical advice). How can I help?"
            )
        elif session_type == 'tracking':
            return (
                "I'm your tracking assistant. I can help you log workouts, track "
                "progress, and adjust your plan. What would you like to track?"
            )
        else:
            return (
                f"Thanks for your message: '{message}'. I'm a placeholder response. "
                "In the future, I'll be powered by AI agents through LiveKit integration."
            )


