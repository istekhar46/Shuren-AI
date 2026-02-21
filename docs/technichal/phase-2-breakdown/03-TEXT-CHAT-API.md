# Sub-Doc 3: Text Chat API Integration

## Document Information
**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Ready for Implementation  
**Parent:** [00-PHASE-2-OVERVIEW.md](./00-PHASE-2-OVERVIEW.md)  
**Dependencies:** Sub-Doc 1 (Foundation), Sub-Doc 2 (Specialized Agents)

---

## Objective

Implement REST API endpoints for text-based chat interactions:
- Synchronous chat endpoint
- Streaming chat endpoint (Server-Sent Events)
- Conversation history persistence
- Agent type selection

---

## Prerequisites Verification

```bash
# Verify dependencies
python -c "from app.services.agent_orchestrator import AgentOrchestrator; print('✓')"
python -c "from app.agents.workout_planner import WorkoutPlannerAgent; print('✓')"
poetry run pytest backend/tests/test_specialized_agents.py -v
```

---

## Implementation Steps

### Step 1: Create Conversation History Model

**File:** `backend/app/models/conversation.py`

```python
"""Conversation history model"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class ConversationMessage(Base):
    """Store conversation history"""
    __tablename__ = "conversation_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    agent_type = Column(String(50))  # Which agent handled this
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )
```

**Migration:**
```bash
poetry run alembic revision --autogenerate -m "add conversation messages"
poetry run alembic upgrade head
```

---

### Step 2: Update Context Loader

**File:** `backend/app/services/context_loader.py`

Update `_load_conversation_history`:

```python
async def _load_conversation_history(
    db: AsyncSession,
    user_id: str,
    limit: int = 10
) -> list:
    """Load recent conversation history"""
    from app.models.conversation import ConversationMessage
    
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.user_id == user_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    # Reverse to chronological order
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "agent_type": msg.agent_type
        }
        for msg in reversed(messages)
    ]
```

---

### Step 3: Create Chat Schemas

**File:** `backend/app/schemas/chat.py`

```python
"""Chat API schemas"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Request for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=2000)
    agent_type: Optional[str] = Field(None, description="Optional explicit agent routing")


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    response: str
    agent_type: str
    conversation_id: str
    tools_used: list = []


class ChatHistoryResponse(BaseModel):
    """Conversation history"""
    messages: list
    total: int
```

---

### Step 4: Create Chat Endpoints

**File:** `backend/app/api/v1/endpoints/chat.py`

```python
"""Chat API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.conversation import ConversationMessage
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse
from app.services.agent_orchestrator import AgentOrchestrator, AgentType

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a text message to the agent
    
    This endpoint:
    1. Loads user context
    2. Routes to appropriate LangChain agent
    3. Returns response
    4. Saves conversation history
    """
    
    try:
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(db_session=db, mode="text")
        
        # Parse agent type if provided
        agent_type = None
        if request.agent_type:
            try:
                agent_type = AgentType(request.agent_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid agent_type")
        
        # Route query
        response = await orchestrator.route_query(
            user_id=str(current_user.id),
            query=request.message,
            agent_type=agent_type,
            voice_mode=False
        )
        
        # Save user message
        user_msg = ConversationMessage(
            user_id=current_user.id,
            role="user",
            content=request.message,
            agent_type=response.agent_type
        )
        db.add(user_msg)
        
        # Save assistant response
        assistant_msg = ConversationMessage(
            user_id=current_user.id,
            role="assistant",
            content=response.content,
            agent_type=response.agent_type
        )
        db.add(assistant_msg)
        
        await db.commit()
        
        return ChatResponse(
            response=response.content,
            agent_type=response.agent_type,
            conversation_id=str(current_user.id),
            tools_used=response.tools_used
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat processing failed")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Streaming chat endpoint for real-time text responses"""
    
    async def generate():
        try:
            # Initialize orchestrator
            orchestrator = AgentOrchestrator(db_session=db, mode="text")
            
            # Parse agent type
            agent_type = None
            if request.agent_type:
                agent_type = AgentType(request.agent_type)
            
            # Load context and get agent
            from app.services.context_loader import load_agent_context
            context = await load_agent_context(db, str(current_user.id))
            
            if not agent_type:
                agent_type = await orchestrator._classify_query(request.message)
            
            agent = orchestrator._get_or_create_agent(agent_type, context)
            
            # Stream response
            full_response = ""
            async for chunk in agent.stream_response(request.message):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}

"
            
            yield f"data: {json.dumps({'done': True, 'agent_type': agent_type.value})}

"
            
            # Save conversation after streaming
            user_msg = ConversationMessage(
                user_id=current_user.id,
                role="user",
                content=request.message,
                agent_type=agent_type.value
            )
            db.add(user_msg)
            
            assistant_msg = ConversationMessage(
                user_id=current_user.id,
                role="assistant",
                content=full_response,
                agent_type=agent_type.value
            )
            db.add(assistant_msg)
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': 'Streaming failed'})}

"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history"""
    
    from sqlalchemy import select, func
    
    # Get messages
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.user_id == current_user.id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    # Get total count
    count_stmt = select(func.count()).select_from(ConversationMessage).where(
        ConversationMessage.user_id == current_user.id
    )
    total = await db.scalar(count_stmt)
    
    return ChatHistoryResponse(
        messages=[
            {
                "role": msg.role,
                "content": msg.content,
                "agent_type": msg.agent_type,
                "created_at": msg.created_at.isoformat()
            }
            for msg in reversed(messages)
        ],
        total=total
    )


@router.delete("/chat/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear conversation history"""
    
    from sqlalchemy import delete
    
    stmt = delete(ConversationMessage).where(
        ConversationMessage.user_id == current_user.id
    )
    
    await db.execute(stmt)
    await db.commit()
    
    return {"status": "cleared"}
```

---

### Step 5: Register Chat Router

**File:** `backend/app/api/v1/__init__.py`

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, profiles, chat  # Add chat

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])  # Add this
# ... other routers
```

---

### Step 6: Create Tests

**File:** `backend/tests/test_chat_endpoints.py`

```python
"""Tests for chat endpoints"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_endpoint(authenticated_client):
    """Test synchronous chat endpoint"""
    client, user = authenticated_client
    
    response = await client.post(
        "/api/v1/chat/chat",
        json={"message": "What's my workout today?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "agent_type" in data
    assert len(data["response"]) > 0


@pytest.mark.asyncio
async def test_chat_with_explicit_agent(authenticated_client):
    """Test chat with explicit agent type"""
    client, user = authenticated_client
    
    response = await client.post(
        "/api/v1/chat/chat",
        json={
            "message": "Give me a meal suggestion",
            "agent_type": "diet"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "diet"


@pytest.mark.asyncio
async def test_chat_history(authenticated_client):
    """Test conversation history"""
    client, user = authenticated_client
    
    # Send a message
    await client.post(
        "/api/v1/chat/chat",
        json={"message": "Hello"}
    )
    
    # Get history
    response = await client.get("/api/v1/chat/history")
    
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) >= 2  # User + assistant


@pytest.mark.asyncio
async def test_clear_history(authenticated_client):
    """Test clearing history"""
    client, user = authenticated_client
    
    # Send a message
    await client.post(
        "/api/v1/chat/chat",
        json={"message": "Test"}
    )
    
    # Clear history
    response = await client.delete("/api/v1/chat/history")
    assert response.status_code == 200
    
    # Verify cleared
    response = await client.get("/api/v1/chat/history")
    data = response.json()
    assert len(data["messages"]) == 0


@pytest.mark.asyncio
async def test_streaming_chat(authenticated_client):
    """Test streaming endpoint"""
    client, user = authenticated_client
    
    async with client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"message": "Quick tip?"}
    ) as response:
        assert response.status_code == 200
        
        chunks = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                chunks.append(line)
        
        assert len(chunks) > 0
```

---

## Verification Checklist

- [ ] Conversation model created and migrated
- [ ] Context loader updated
- [ ] Chat schemas defined
- [ ] Chat endpoints implemented
- [ ] Router registered
- [ ] Tests pass
- [ ] Streaming works
- [ ] History persists

**Final Test:**
```bash
poetry run pytest backend/tests/test_chat_endpoints.py -v
```

---

## API Documentation

After implementation, verify Swagger docs:

```bash
# Start server
poetry run uvicorn app.main:app --reload

# Visit http://localhost:8000/docs
# Should see:
# - POST /api/v1/chat/chat
# - POST /api/v1/chat/stream
# - GET /api/v1/chat/history
# - DELETE /api/v1/chat/history
```

---

## Success Criteria

✅ Chat endpoints working  
✅ Streaming functional  
✅ History persisted  
✅ All tests pass  
✅ API documented  

**Estimated Time:** 2-3 days

**Next:** [04-LIVEKIT-INFRASTRUCTURE.md](./04-LIVEKIT-INFRASTRUCTURE.md)
