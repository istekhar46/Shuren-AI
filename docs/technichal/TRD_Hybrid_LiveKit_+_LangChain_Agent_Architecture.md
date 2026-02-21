# Technical Requirements Document: Hybrid LiveKit + LangChain Agent Architecture

## Document Information

**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Final  
**Based On:** Official LiveKit Agents v1.3+ and LangChain v0.3+ Documentation

---

## Executive Summary

This document specifies a production-ready hybrid architecture that combines **LiveKit Agents** for voice interaction handling with **LangChain** for agent orchestration and complex reasoning. The architecture separates concerns: LiveKit manages the real-time voice pipeline (STT→TTS), while LangChain handles business logic, specialized agent routing, and database interactions.

### Architecture Philosophy

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                        │
│              (iOS/Android/Web with LiveKit SDK)              │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    WebRTC       FastAPI      WebRTC
    (Voice)       (Text)      (Data)
         │           │           │
         ▼           ▼           ▼
┌────────────────────────────────────────────────────────────┐
│              LIVEKIT SERVER                                 │
│  (WebRTC SFU - Handles Media Routing)                      │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ├─── Job Dispatch
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────────┐
│ LIVEKIT AGENT  │    │   FASTAPI BACKEND   │
│    WORKERS      │    │  (Text Endpoints)   │
│ (Voice Path)    │    │   (Text Path)       │
└────────┬────────┘    └──────────┬──────────┘
         │                        │
         │                        │
         └────────┬───────────────┘
                  │
         ┌────────▼────────┐
         │  LANGCHAIN      │
         │  ORCHESTRATOR   │
         │  (Shared Core)  │
         └────────┬────────┘
                  │
      ┌───────────┼────────────┐
      │           │            │
      ▼           ▼            ▼
   [Agent     [Agent       [Agent
   Workout]   Diet]        General]
```

**Key Principle:** LiveKit handles "how to communicate" (voice/STT/TTS), LangChain handles "what to say and do" (reasoning/tools/database).

---

## 1. Core Requirements

### Requirement 1.1: Dual-Path Architecture

**Requirement:** THE System SHALL implement two distinct interaction paths: Voice Path (via LiveKit) and Text Path (via FastAPI).

#### Acceptance Criteria

1. WHEN a user initiates a voice session, THE System SHALL create a LiveKit room and dispatch a LiveKit Agent worker
2. WHEN a user sends a text message, THE System SHALL route the request through FastAPI to the LangChain AgentOrchestrator
3. BOTH paths SHALL share the same underlying LangChain AgentOrchestrator and specialized agents
4. THE Voice Path SHALL achieve <2 second end-to-end latency (95th percentile)
5. THE Text Path SHALL achieve <3 second response time (95th percentile)
6. THE System SHALL maintain conversation history consistency across both paths for the same user

### Requirement 1.2: LiveKit Agent Framework Integration

**Requirement:** THE System SHALL use LiveKit Agents Python SDK v1.3+ as the voice interaction layer.

#### Acceptance Criteria

1. THE System SHALL use `livekit.agents.Agent` class for voice agent implementation
2. THE System SHALL implement the `entrypoint` function pattern as specified in LiveKit documentation
3. WHEN a voice session starts, THE System SHALL connect to the LiveKit room using `JobContext.connect()`
4. THE System SHALL use `@function_tool` decorator for LiveKit-compatible tool definitions
5. THE System SHALL NOT use deprecated v0.x patterns (no `VoicePipelineAgent`, no `@llm.ai_callable`)
6. THE System SHALL properly handle `JobContext` lifecycle including connection, room events, and shutdown
7. THE System SHALL register with LiveKit Server as an agent worker process using `WorkerOptions`

### Requirement 1.3: LangChain Integration

**Requirement:** THE System SHALL use LangChain v0.3+ for agent orchestration, tool management, and LLM interactions.

#### Acceptance Criteria

1. THE System SHALL use LangChain's standardized `ChatModel` interface (e.g., `ChatAnthropic`, `ChatOpenAI`)
2. THE System SHALL support multiple LLM providers via LangChain's provider-agnostic interface
3. THE System SHALL use LangChain's `@tool` decorator for database interaction tools
4. THE System SHALL implement conversation history using LangChain message types (`HumanMessage`, `AIMessage`, `SystemMessage`)
5. THE System SHALL use LangChain's async methods (`ainvoke`, `astream`) for non-blocking operations
6. THE System SHALL NOT use LiveKit's LLM plugins for the orchestration layer (use only for STT/TTS)

---

## 2. Voice Path Implementation (LiveKit Agents)

### Requirement 2.1: LiveKit Agent Worker Architecture

**Requirement:** THE System SHALL implement LiveKit Agent workers that delegate reasoning to LangChain while handling voice I/O locally.

#### LiveKit Agent Worker Structure

```python
# livekit_agents/voice_agent_worker.py
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, Agent, function_tool, RunContext
from livekit.plugins import deepgram, openai, cartesia
import asyncio

class FitnessVoiceAgent(Agent):
    """Voice agent that delegates to LangChain for reasoning"""
    
    def __init__(self, user_id: str, agent_type: str):
        # Voice-specific configuration
        super().__init__(
            instructions=self._get_base_instructions(agent_type)
        )
        self.user_id = user_id
        self.agent_type = agent_type
        
        # LangChain orchestrator (initialized later)
        self.orchestrator = None
        self.user_context = None
    
    async def initialize_orchestrator(self):
        """Pre-load LangChain orchestrator with user context"""
        # This happens ONCE at session start
        async with get_db_session() as db:
            # Load user context from database
            self.user_context = await load_agent_context(db, self.user_id)
            
            # Initialize LangChain orchestrator with context
            self.orchestrator = AgentOrchestrator(
                user_context=self.user_context,
                mode="voice"  # Optimized mode for voice
            )
            
            # Pre-warm LLM connection
            await self.orchestrator.warm_up()
    
    @function_tool()
    async def get_todays_workout(
        self,
        context: RunContext
    ) -> str:
        """Get user's workout plan for today.
        
        This tool retrieves the current workout from cached context,
        avoiding database queries during voice interaction.
        """
        # Use pre-loaded context (no DB hit)
        workout = self.user_context.current_workout_plan.get("today")
        return json.dumps(workout)
    
    @function_tool()
    async def log_workout_set(
        self,
        context: RunContext,
        exercise: str,
        reps: int,
        weight: float
    ) -> str:
        """Log a completed workout set.
        
        Args:
            exercise: Name of the exercise performed
            reps: Number of repetitions completed
            weight: Weight used in pounds or kilograms
        """
        # Queue for async processing (non-blocking)
        await self._queue_log({
            "type": "workout_set",
            "exercise": exercise,
            "reps": reps,
            "weight": weight,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Return immediately
        return f"Logged {reps} reps of {exercise} at {weight} pounds"
    
    @function_tool()
    async def ask_specialist_agent(
        self,
        context: RunContext,
        query: str,
        specialist: str  # "workout" | "diet" | "supplement"
    ) -> str:
        """Delegate complex queries to LangChain specialist agents.
        
        Args:
            query: The user's question or request
            specialist: Which specialist agent to consult
        """
        # Call LangChain orchestrator
        response = await self.orchestrator.route_query(
            query=query,
            agent_type=AgentType(specialist),
            voice_mode=True  # Use optimized voice mode
        )
        
        return response
    
    async def _queue_log(self, log_data: dict):
        """Queue log entry for background processing"""
        # Non-blocking: write happens after voice response
        if not hasattr(self, '_log_queue'):
            self._log_queue = asyncio.Queue()
            # Start background worker
            asyncio.create_task(self._log_worker())
        
        await self._log_queue.put(log_data)
    
    async def _log_worker(self):
        """Background worker that flushes logs to database"""
        while True:
            try:
                log_entry = await self._log_queue.get()
                async with get_db_session() as db:
                    await write_workout_log(db, self.user_id, log_entry)
                self._log_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Log worker error: {e}")
    
    def _get_base_instructions(self, agent_type: str) -> str:
        """Get base instructions for the agent"""
        base = f"""You are a helpful fitness coach assistant.
        
Your role is to:
- Answer quick questions about workouts and meals
- Log workout progress
- Provide motivation and encouragement

For complex queries, use the ask_specialist_agent tool.

Keep responses conversational and under 30 seconds when spoken.
"""
        return base


async def entrypoint(ctx: JobContext):
    """Main entrypoint for LiveKit agent worker"""
    
    # Extract metadata from room
    metadata = json.loads(ctx.room.metadata or "{}")
    user_id = metadata.get("user_id")
    agent_type = metadata.get("agent_type", "general")
    
    if not user_id:
        logger.error("No user_id in room metadata")
        return
    
    # Create agent
    agent = FitnessVoiceAgent(user_id=user_id, agent_type=agent_type)
    
    # Pre-load orchestrator BEFORE connecting
    await agent.initialize_orchestrator()
    
    # Now connect to room
    await ctx.connect()
    
    # Start agent session
    from livekit.agents.voice import AgentSession
    
    session = AgentSession(
        # STT Configuration
        stt=deepgram.STT(
            model="nova-2-general",
            language="en-US"
        ),
        
        # TTS Configuration  
        tts=cartesia.TTS(
            model="sonic-english",
            voice_id="fitness-coach-male",
            sample_rate=24000,
            speed=1.1  # Slightly faster for efficiency
        ),
        
        # LLM Configuration (for function calling only)
        llm=openai.LLM(
            model="gpt-4o",
            temperature=0.7
        )
    )
    
    await session.start(room=ctx.room, agent=agent)
    
    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user warmly and ask how you can help with their fitness today."
    )


if __name__ == "__main__":
    # Run the agent worker
    agents.cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            num_idle_workers=2,  # Pre-warm workers
            worker_type=agents.WorkerType.ROOM
        )
    )
```

#### Acceptance Criteria

1. THE LiveKit Agent SHALL define tools using `@function_tool()` decorator as per LiveKit v1.x specification
2. THE LiveKit Agent SHALL implement `async def entrypoint(ctx: JobContext)` as the entry point
3. THE LiveKit Agent SHALL pre-load LangChain orchestrator BEFORE connecting to the room
4. THE LiveKit Agent SHALL use `AgentSession` class (not deprecated `VoicePipelineAgent`)
5. THE LiveKit Agent SHALL implement async logging that doesn't block voice responses
6. THE LiveKit Agent SHALL provide simple tools that use cached data (no DB queries in voice path)
7. THE LiveKit Agent SHALL delegate complex reasoning to LangChain via `ask_specialist_agent` tool
8. THE LiveKit Agent SHALL properly cleanup resources on disconnect

### Requirement 2.2: LiveKit-to-LangChain Bridge

**Requirement:** THE System SHALL provide a clean interface between LiveKit tools and LangChain orchestration.

#### Bridge Implementation

```python
# services/langchain_orchestrator.py (Voice-Optimized Mode)
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from enum import Enum

class AgentType(str, Enum):
    WORKOUT = "workout"
    DIET = "diet"
    SUPPLEMENT = "supplement"
    TRACKER = "tracker"
    SCHEDULER = "scheduler"
    GENERAL = "general"

class AgentOrchestrator:
    """LangChain-based orchestrator with voice optimization"""
    
    def __init__(
        self,
        user_context: AgentContext,
        mode: str = "text"  # "text" | "voice"
    ):
        self.user_context = user_context
        self.mode = mode
        
        # In-memory cache for voice mode
        self._agent_cache = {} if mode == "voice" else None
        self._classification_cache = {}
        
        # LangChain LLM for classification
        self.classifier_llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",  # Fast model
            temperature=0.1,
            max_tokens=10  # Just need agent type
        )
    
    async def route_query(
        self,
        query: str,
        agent_type: AgentType | None = None,
        voice_mode: bool = False
    ) -> str:
        """Route query to appropriate agent
        
        Args:
            query: User's query
            agent_type: Optional explicit agent type
            voice_mode: Whether this is a voice interaction
        
        Returns:
            Agent's response as string
        """
        
        # Determine agent type if not specified
        if not agent_type:
            agent_type = await self._classify_query(query)
        
        # Get specialized agent
        agent = self._get_or_create_agent(agent_type)
        
        # Process with appropriate mode
        if voice_mode or self.mode == "voice":
            response = await agent.process_voice(
                query=query,
                context=self.user_context
            )
        else:
            response = await agent.process_text(
                query=query,
                context=self.user_context
            )
        
        return response
    
    async def _classify_query(self, query: str) -> AgentType:
        """Fast query classification using Haiku"""
        
        # Check cache (voice mode only)
        if self.mode == "voice":
            cache_key = query[:50]  # First 50 chars
            if cache_key in self._classification_cache:
                return self._classification_cache[cache_key]
        
        # Classify with LLM
        messages = [
            SystemMessage(content="""Classify this fitness query into ONE category:
- workout: Exercise plans, form, demonstrations
- diet: Meal plans, nutrition, recipes
- supplement: Supplement guidance
- tracker: Progress tracking
- scheduler: Schedule changes
- general: Motivation, casual

Respond with ONLY the category name."""),
            HumanMessage(content=query)
        ]
        
        result = await self.classifier_llm.ainvoke(messages)
        agent_type = AgentType(result.content.strip().lower())
        
        # Cache for voice mode
        if self.mode == "voice":
            self._classification_cache[cache_key] = agent_type
        
        return agent_type
    
    def _get_or_create_agent(self, agent_type: AgentType):
        """Get cached agent or create new one"""
        
        # For voice mode, cache agents in memory
        if self._agent_cache is not None:
            if agent_type not in self._agent_cache:
                self._agent_cache[agent_type] = self._create_agent(agent_type)
            return self._agent_cache[agent_type]
        
        # For text mode, create fresh agent each time
        return self._create_agent(agent_type)
    
    def _create_agent(self, agent_type: AgentType):
        """Factory method to create specialized agents"""
        from agents.workout_planner import WorkoutPlannerAgent
        from agents.diet_planner import DietPlannerAgent
        from agents.general_assistant import GeneralAssistantAgent
        
        agent_map = {
            AgentType.WORKOUT: WorkoutPlannerAgent,
            AgentType.DIET: DietPlannerAgent,
            AgentType.GENERAL: GeneralAssistantAgent,
            # ... other agents
        }
        
        agent_class = agent_map.get(agent_type, GeneralAssistantAgent)
        return agent_class(context=self.user_context)
    
    async def warm_up(self):
        """Pre-warm LLM connections"""
        # Make a dummy call to establish connection
        try:
            await self.classifier_llm.ainvoke([
                HumanMessage(content="hello")
            ])
        except Exception:
            pass  # Ignore errors, just warming up
```

#### Acceptance Criteria

1. THE AgentOrchestrator SHALL use LangChain's `ChatAnthropic` or equivalent for classification
2. THE AgentOrchestrator SHALL support both "voice" and "text" modes with different optimization strategies
3. WHEN in voice mode, THE AgentOrchestrator SHALL cache agent instances in memory
4. WHEN in voice mode, THE AgentOrchestrator SHALL cache query classifications
5. THE AgentOrchestrator SHALL use fast models (Claude Haiku, GPT-4o-mini) for classification
6. THE AgentOrchestrator SHALL provide async methods using LangChain's `ainvoke`
7. THE AgentOrchestrator SHALL support pre-warming of LLM connections

### Requirement 2.3: FastAPI Integration for Voice Sessions

**Requirement:** THE System SHALL provide FastAPI endpoints to create LiveKit voice sessions.

```python
# api/v1/endpoints/voice_sessions.py
from fastapi import APIRouter, Depends, HTTPException
from livekit import api
import secrets

router = APIRouter()

@router.post("/start-voice-session")
async def start_voice_session(
    agent_type: str = "general",  # workout | diet | general
    current_user: User = Depends(get_current_user),
    livekit_api: api.LiveKitAPI = Depends(get_livekit_api)
):
    """Create a LiveKit voice session for the user
    
    This endpoint:
    1. Creates a LiveKit room
    2. Generates access token for user
    3. Triggers agent worker dispatch
    4. Returns connection details to client
    """
    
    # Create unique room name
    room_name = f"fitness-voice-{current_user.id}-{secrets.token_hex(4)}"
    
    # Create room with metadata
    room = await livekit_api.room.create_room(
        api.CreateRoomRequest(
            name=room_name,
            metadata=json.dumps({
                "user_id": str(current_user.id),
                "agent_type": agent_type,
                "mode": "voice"
            }),
            empty_timeout=300,  # 5 minutes
            max_participants=2  # User + agent
        )
    )
    
    # Generate access token for user
    token = api.AccessToken(
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET
    )
    token.with_identity(str(current_user.id))
    token.with_name(current_user.email)
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True
    ))
    
    jwt_token = token.to_jwt()
    
    return {
        "room_name": room_name,
        "token": jwt_token,
        "livekit_url": settings.LIVEKIT_URL,
        "agent_type": agent_type
    }

@router.get("/session/{room_name}/status")
async def get_session_status(
    room_name: str,
    current_user: User = Depends(get_current_user),
    livekit_api: api.LiveKitAPI = Depends(get_livekit_api)
):
    """Get status of active voice session"""
    
    try:
        room = await livekit_api.room.get_room(room_name)
        
        return {
            "active": room.num_participants > 0,
            "participants": room.num_participants,
            "created_at": room.creation_time,
            "agent_connected": room.num_participants >= 2
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Room not found")

@router.delete("/session/{room_name}")
async def end_session(
    room_name: str,
    current_user: User = Depends(get_current_user),
    livekit_api: api.LiveKitAPI = Depends(get_livekit_api)
):
    """End a voice session"""
    
    await livekit_api.room.delete_room(room_name)
    
    return {"status": "ended"}
```

#### Acceptance Criteria

1. THE System SHALL create LiveKit rooms with user-specific metadata
2. THE System SHALL generate JWT access tokens using LiveKit's `api.AccessToken`
3. THE System SHALL include `user_id` and `agent_type` in room metadata for agent worker
4. THE System SHALL limit room lifetime with `empty_timeout` parameter
5. THE System SHALL support querying room status via LiveKit API
6. THE System SHALL support graceful session termination

---

## 3. Text Path Implementation (FastAPI + LangChain)

### Requirement 3.1: FastAPI Text Endpoints

**Requirement:** THE System SHALL provide REST API endpoints for text-based interactions that use the same LangChain orchestrator.

```python
# api/v1/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    agent_type: str | None = None  # Optional explicit routing

class ChatResponse(BaseModel):
    response: str
    agent_type: str
    conversation_id: str

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
    
    # Load user context
    context = await load_agent_context(db, current_user.id)
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(
        user_context=context,
        mode="text"
    )
    
    # Route query
    response = await orchestrator.route_query(
        query=request.message,
        agent_type=AgentType(request.agent_type) if request.agent_type else None,
        voice_mode=False
    )
    
    # Save conversation
    await save_conversation_message(
        db=db,
        user_id=current_user.id,
        role="user",
        content=request.message
    )
    await save_conversation_message(
        db=db,
        user_id=current_user.id,
        role="assistant",
        content=response
    )
    
    return ChatResponse(
        response=response,
        agent_type=orchestrator.last_agent_type.value,
        conversation_id=str(current_user.id)
    )

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Streaming chat endpoint for real-time text responses"""
    
    async def generate():
        # Load context
        context = await load_agent_context(db, current_user.id)
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(
            user_context=context,
            mode="text"
        )
        
        # Get agent
        agent_type = await orchestrator._classify_query(request.message)
        agent = orchestrator._get_or_create_agent(agent_type)
        
        # Stream response
        async for chunk in agent.stream_response(
            query=request.message,
            context=context
        ):
            yield f"data: {json.dumps({'chunk': chunk})}

"
        
        yield f"data: {json.dumps({'done': True})}

"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

#### Acceptance Criteria

1. THE System SHALL provide both synchronous and streaming chat endpoints
2. THE Text Path SHALL use the same `AgentOrchestrator` as the Voice Path
3. THE System SHALL save conversation history to database after each interaction
4. THE System SHALL support explicit agent type routing via `agent_type` parameter
5. THE System SHALL return the actual agent type that handled the request
6. WHEN streaming, THE System SHALL use Server-Sent Events (SSE) format
7. THE Text Path SHALL load fresh context from database on each request

---

## 4. LangChain Specialized Agents

### Requirement 4.1: Base Agent with LangChain Integration

**Requirement:** THE System SHALL implement specialized agents using LangChain for LLM interaction and tool management.

```python
# agents/base.py
from abc import ABC, abstractmethod
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import AsyncIterator

class AgentContext(BaseModel):
    """Immutable user context"""
    user_id: str
    fitness_level: str
    primary_goal: str
    secondary_goal: str | None
    energy_level: str
    current_workout_plan: dict
    current_meal_plan: dict
    conversation_history: list[dict] = []

class BaseAgent(ABC):
    """Base agent using LangChain for LLM interactions"""
    
    def __init__(self, context: AgentContext):
        self.context = context
        self.llm = self._init_llm()
    
    def _init_llm(self):
        """Initialize LangChain LLM based on configuration"""
        provider = settings.LLM_PROVIDER
        
        if provider == "anthropic":
            return ChatAnthropic(
                model=settings.LLM_MODEL,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
        elif provider == "openai":
            return ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
        elif provider == "google":
            return ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @abstractmethod
    async def process_text(self, query: str, context: AgentContext) -> str:
        """Process text query (full response)"""
        pass
    
    @abstractmethod
    async def process_voice(self, query: str, context: AgentContext) -> str:
        """Process voice query (concise response)"""
        pass
    
    @abstractmethod
    async def stream_response(
        self,
        query: str,
        context: AgentContext
    ) -> AsyncIterator[str]:
        """Stream response for text interactions"""
        pass
    
    @abstractmethod
    def get_tools(self) -> list:
        """Get LangChain tools for this agent"""
        pass
    
    def _build_messages(
        self,
        query: str,
        voice_mode: bool = False
    ) -> list:
        """Build message chain for LLM"""
        
        messages = [
            SystemMessage(content=self._system_prompt(voice_mode))
        ]
        
        # Add conversation history (last N messages)
        history_limit = 5 if voice_mode else 10
        for msg in self.context.conversation_history[-history_limit:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        return messages
    
    @abstractmethod
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """Get system prompt for this agent"""
        pass
```

### Requirement 4.2: Example Specialized Agent Implementation

```python
# agents/workout_planner.py
from .base import BaseAgent, AgentContext
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
import asyncio

class WorkoutPlannerAgent(BaseAgent):
    """Specialized agent for workout planning using LangChain"""
    
    def get_tools(self) -> list:
        """Define LangChain tools for workout planning"""
        
        @tool
        async def get_current_workout() -> str:
            """Get today's workout plan for the user"""
            # Query from cached context (voice mode) or database (text mode)
            workout = self.context.current_workout_plan.get("today")
            return json.dumps(workout)
        
        @tool
        async def show_exercise_demo(exercise_name: str) -> str:
            """Get demonstration GIF URL for an exercise
            
            Args:
                exercise_name: Name of the exercise
            """
            async with get_db_session() as db:
                stmt = select(Exercise).where(Exercise.name == exercise_name)
                result = await db.execute(stmt)
                exercise = result.scalars().first()
                if exercise:
                    return exercise.demo_gif_url
                return "Exercise not found"
        
        @tool
        async def suggest_workout_modification(
            reason: str,
            intensity_change: str  # "increase" | "decrease" | "maintain"
        ) -> str:
            """Suggest modifications to current workout based on user feedback
            
            Args:
                reason: Why modification is needed (e.g., "too tired", "feeling strong")
                intensity_change: Direction of intensity change
            """
            # Use LLM to generate smart modifications
            # This is a tool that calls another LLM - that's fine!
            prompt = f"""Given this workout: {self.context.current_workout_plan}
User feedback: {reason}
Intensity change: {intensity_change}

Suggest a modified workout plan."""
            
            messages = [
                SystemMessage(content="You are a workout modification expert"),
                HumanMessage(content=prompt)
            ]
            
            result = await self.llm.ainvoke(messages)
            return result.content
        
        return [get_current_workout, show_exercise_demo, suggest_workout_modification]
    
    async def process_voice(self, query: str, context: AgentContext) -> str:
        """Process voice query - concise response"""
        
        messages = self._build_messages(query, voice_mode=True)
        
        # For voice, we want quick responses without tools
        # Tools are called via LiveKit's @function_tool pattern instead
        result = await self.llm.ainvoke(messages)
        
        return result.content
    
    async def process_text(self, query: str, context: AgentContext) -> str:
        """Process text query - can use tools"""
        
        # Create agent with tool calling
        tools = self.get_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._system_prompt(voice_mode=False)),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            max_iterations=5,
            handle_parsing_errors=True
        )
        
        result = await agent_executor.ainvoke({
            "input": query,
            "chat_history": self._format_chat_history()
        })
        
        return result["output"]
    
    async def stream_response(
        self,
        query: str,
        context: AgentContext
    ) -> AsyncIterator[str]:
        """Stream response for text interactions"""
        
        messages = self._build_messages(query, voice_mode=False)
        
        # Use LangChain's streaming
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """Generate system prompt based on mode"""
        
        base_prompt = f"""You are a professional workout planning assistant.

User Profile:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}
- Energy Level: {self.context.energy_level}

Current Workout Plan:
{json.dumps(self.context.current_workout_plan, indent=2)}

Guidelines:
- Be motivating but realistic
- Reference their specific plan
- Adjust based on energy level
- Never give medical advice
"""
        
        if voice_mode:
            base_prompt += """
- Keep responses under 30 seconds when spoken
- Be conversational and concise
- Use simple language
"""
        else:
            base_prompt += """
- Provide detailed explanations when helpful
- Use tools to fetch specific data
- Format responses with markdown when appropriate
"""
        
        return base_prompt
    
    def _format_chat_history(self) -> list:
        """Format conversation history for LangChain"""
        history = []
        for msg in self.context.conversation_history[-10:]:
            if msg["role"] == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history.append(AIMessage(content=msg["content"]))
        return history
```

#### Acceptance Criteria

1. THE Specialized Agents SHALL use LangChain's `@tool` decorator for tool definitions
2. THE Specialized Agents SHALL support both `process_voice` and `process_text` methods
3. THE `process_text` method SHALL use LangChain's `AgentExecutor` for tool calling
4. THE `process_voice` method SHALL return concise responses without tool calling
5. THE Specialized Agents SHALL use LangChain's streaming via `astream` method
6. THE Tools SHALL use async database operations
7. THE Agents SHALL format conversation history using LangChain message types
8. THE System prompt SHALL adapt based on voice vs. text mode

---

## 5. Integration Points and Data Flow

### Requirement 5.1: Complete Flow Diagrams

#### Voice Interaction Flow

```
[User speaks in app]
      ↓
[App sends audio via WebRTC to LiveKit Server]
      ↓
[LiveKit Server routes to Agent Worker]
      ↓
[LiveKit Agent Worker receives audio]
      ↓
[Deepgram STT converts speech to text]
      ↓
[LiveKit Agent's @function_tool tools are available to LLM]
      ↓
IF simple query (e.g., "what's my workout?"):
    [Tool: get_todays_workout() - returns cached data]
    ↓
    [GPT-4o generates response]
    ↓
    [Cartesia TTS converts to speech]
    ↓
    [Audio sent to user via WebRTC]
    
ELSE IF complex query (e.g., "why is this exercise good?"):
    [Tool: ask_specialist_agent("workout", query)]
    ↓
    [LangChain AgentOrchestrator.route_query(voice_mode=True)]
    ↓
    [WorkoutPlannerAgent.process_voice()]
    ↓
    [Claude Sonnet generates response]
    ↓
    [Response returned to LiveKit Agent]
    ↓
    [Cartesia TTS converts to speech]
    ↓
    [Audio sent to user via WebRTC]

ELSE IF logging action (e.g., "I did 8 reps at 185"):
    [Tool: log_workout_set(exercise, reps, weight)]
    ↓
    [Queued for async processing - returns immediately]
    ↓
    [GPT-4o generates confirmation]
    ↓
    [Cartesia TTS converts to speech]
    ↓
    [Audio sent to user via WebRTC]
    ↓
    [Background worker writes to PostgreSQL]

Total Latency: 1.1-1.9 seconds for cached queries
               1.5-2.5 seconds for LangChain queries
```

#### Text Interaction Flow

```
[User types message in app]
      ↓
[POST /api/v1/chat with message]
      ↓
[FastAPI receives request]
      ↓
[Load AgentContext from PostgreSQL + Redis]
      ↓
[Create AgentOrchestrator(mode="text")]
      ↓
[AgentOrchestrator.route_query(voice_mode=False)]
      ↓
[LangChain classifier determines agent type]
      ↓
[Specialized Agent.process_text()]
      ↓
[LangChain AgentExecutor with tools]
      ↓
[Tools may query PostgreSQL]
      ↓
[Claude Sonnet generates detailed response]
      ↓
[Save conversation to PostgreSQL]
      ↓
[Return response to client]

Total Latency: 2.0-3.0 seconds
```

#### Acceptance Criteria

1. THE Voice Path SHALL achieve <2 second latency for cached queries
2. THE Voice Path SHALL achieve <2.5 second latency for LangChain-routed queries
3. THE Text Path SHALL achieve <3 second latency
4. THE System SHALL log all latencies for monitoring
5. THE System SHALL maintain data consistency between voice and text paths

---

## 6. Configuration and Environment

### Requirement 6.1: Environment Configuration

```python
# config.py
from pydantic_settings import BaseSettings
from enum import Enum

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Fitness AI"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 86400
    
    # LiveKit Configuration
    LIVEKIT_URL: str  # wss://your-project.livekit.cloud
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    LIVEKIT_WORKER_NUM_IDLE: int = 2
    
    # LangChain LLM Configuration
    LLM_PROVIDER: LLMProvider = LLMProvider.ANTHROPIC
    LLM_MODEL: str = "claude-sonnet-4-5-20250929"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    
    # LLM API Keys
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    
    # Classifier Configuration (for routing)
    CLASSIFIER_MODEL: str = "claude-haiku-4-5-20251001"
    CLASSIFIER_TEMPERATURE: float = 0.1
    
    # LiveKit STT/TTS Configuration
    DEEPGRAM_API_KEY: str
    CARTESIA_API_KEY: str
    
    # Voice optimization
    VOICE_CONTEXT_CACHE_TTL: int = 3600
    VOICE_MAX_RESPONSE_TOKENS: int = 150
    
    class Config:
        env_file = ".env"
    
    def get_required_llm_api_key(self) -> str:
        """Get API key for configured LLM provider"""
        if self.LLM_PROVIDER == LLMProvider.ANTHROPIC:
            if not self.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY required")
            return self.ANTHROPIC_API_KEY
        elif self.LLM_PROVIDER == LLMProvider.OPENAI:
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY required")
            return self.OPENAI_API_KEY
        elif self.LLM_PROVIDER == LLMProvider.GOOGLE:
            if not self.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY required")
            return self.GOOGLE_API_KEY

settings = Settings()
```

#### Example .env File

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/fitness
REDIS_URL=redis://localhost:6379

# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxx
LIVEKIT_API_SECRET=secretxxxx

# LangChain LLM (choose one provider)
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_API_KEY=sk-ant-xxx
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Classification
CLASSIFIER_MODEL=claude-haiku-4-5-20251001
CLASSIFIER_TEMPERATURE=0.1

# LiveKit Voice Services
DEEPGRAM_API_KEY=xxx
CARTESIA_API_KEY=xxx

# Voice Optimization
VOICE_CONTEXT_CACHE_TTL=3600
VOICE_MAX_RESPONSE_TOKENS=150
```

#### Acceptance Criteria

1. THE System SHALL validate required configuration at startup
2. THE System SHALL support all three LLM providers (Anthropic, OpenAI, Google)
3. THE System SHALL require appropriate API key based on `LLM_PROVIDER`
4. THE System SHALL support separate configuration for classifier model
5. THE System SHALL provide sensible defaults for optimization parameters

---

## 7. Deployment Architecture

### Requirement 7.1: Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  # FastAPI Backend
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/fitness
      - REDIS_URL=redis://redis:6379
      - LIVEKIT_URL=${LIVEKIT_URL}
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_MODEL=${LLM_MODEL}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
  
  # LiveKit Agent Worker
  livekit_agent:
    build:
      context: ./backend
      dockerfile: Dockerfile.agent
    environment:
      - LIVEKIT_URL=${LIVEKIT_URL}
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/fitness
      - REDIS_URL=redis://redis:6379
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_MODEL=${LLM_MODEL}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
      - CARTESIA_API_KEY=${CARTESIA_API_KEY}
    depends_on:
      - postgres
      - redis
    command: python livekit_agents/voice_agent_worker.py
    deploy:
      replicas: 2  # Run multiple agent workers
  
  # PostgreSQL
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: fitness
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  # Celery Worker (Background Tasks)
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.core.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/fitness
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  # Celery Beat (Scheduler)
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.core.celery_app beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
```

### Requirement 7.2: Agent Worker Dockerfile

```dockerfile
# Dockerfile.agent
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-agent.txt .
RUN pip install --no-cache-dir -r requirements-agent.txt

# Copy application code
COPY . .

# Run agent worker
CMD ["python", "livekit_agents/voice_agent_worker.py"]
```

### Requirements File for Agent

```txt
# requirements-agent.txt
# LiveKit Agents with required plugins
livekit-agents[deepgram,openai,cartesia]==1.3.12

# LangChain for orchestration
langchain==0.3.0
langchain-core==0.3.0
langchain-anthropic==0.3.0
langchain-openai==0.3.0
langchain-google-genai==2.0.0

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.30.0

# Redis
redis[hiredis]==5.0.0

# Utilities
pydantic==2.6.0
pydantic-settings==2.2.0
python-dotenv==1.0.0
```

#### Acceptance Criteria

1. THE System SHALL run LiveKit Agent workers in separate containers from FastAPI
2. THE System SHALL support horizontal scaling of agent workers via `replicas`
3. THE System SHALL share database and Redis access between all services
4. THE System SHALL include all required dependencies in agent worker image
5. THE System SHALL support environment-based configuration

---

## 8. Dependencies and Versions

### Requirement 8.1: Version Matrix

| Component | Version | Rationale |
|-----------|---------|-----------|
| LiveKit Agents | 1.3.12+ | Latest stable with v1.x architecture |
| LangChain | 0.3.0+ | Current stable version |
| LangChain Anthropic | 0.3.0+ | Provider integration |
| LangChain OpenAI | 0.3.0+ | Provider integration |
| LangChain Google | 2.0.0+ | Provider integration |
| FastAPI | 0.115.0+ | Latest async features |
| Uvicorn | 0.32.0+ | ASGI server |
| SQLAlchemy | 2.0.25+ | Async ORM |
| Pydantic | 2.6.0+ | Data validation |
| PostgreSQL | 15+ | Production database |
| Redis | 7+ | Caching layer |
| Python | 3.11+ | Required for LiveKit Agents |

### Requirement 8.2: Plugin Compatibility

**LiveKit Plugins (for STT/TTS only):**
- `livekit-plugins-deepgram`: Speech-to-text
- `livekit-plugins-cartesia`: Text-to-speech
- `livekit-plugins-openai`: For OpenAI Realtime API (optional)

**LangChain Providers (for reasoning/orchestration):**
- Anthropic Claude (recommended)
- OpenAI GPT models
- Google Gemini

#### Acceptance Criteria

1. THE System SHALL use compatible versions as specified in the matrix
2. THE System SHALL NOT mix LiveKit's LLM plugins with LangChain's LLM integrations for orchestration
3. THE System SHALL use LiveKit plugins ONLY for STT/TTS
4. THE System SHALL use LangChain ONLY for agent orchestration and reasoning
5. THE System SHALL document version compatibility in requirements files

---

## 9. Testing Requirements

### Requirement 9.1: Integration Testing

```python
# tests/integration/test_voice_path.py
import pytest
from livekit import api
import asyncio

@pytest.mark.asyncio
async def test_voice_session_creation():
    """Test creating a voice session"""
    
    # Create room via API
    response = await client.post(
        "/api/v1/start-voice-session",
        json={"agent_type": "workout"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "room_name" in data
    assert "token" in data
    assert "livekit_url" in data

@pytest.mark.asyncio
async def test_langchain_orchestrator_routing():
    """Test that LangChain orchestrator routes correctly"""
    
    context = await load_agent_context(db, test_user_id)
    orchestrator = AgentOrchestrator(
        user_context=context,
        mode="voice"
    )
    
    # Test routing
    response = await orchestrator.route_query(
        "What's my workout today?",
        voice_mode=True
    )
    
    assert len(response) > 0
    assert orchestrator.last_agent_type == AgentType.WORKOUT

@pytest.mark.asyncio
async def test_livekit_to_langchain_bridge():
    """Test that LiveKit tools can call LangChain orchestrator"""
    
    # Create mock agent
    agent = FitnessVoiceAgent(
        user_id=test_user_id,
        agent_type="workout"
    )
    
    await agent.initialize_orchestrator()
    
    # Simulate tool call
    response = await agent.ask_specialist_agent(
        context=mock_run_context,
        query="Why is squatting good for me?",
        specialist="workout"
    )
    
    assert len(response) > 0
    assert "squat" in response.lower()
```

#### Acceptance Criteria

1. THE System SHALL have integration tests for voice session creation
2. THE System SHALL have integration tests for LangChain orchestrator
3. THE System SHALL have integration tests for LiveKit-to-LangChain bridge
4. THE System SHALL test latency requirements (voice <2s, text <3s)
5. THE System SHALL test conversation history persistence
6. THE System SHALL test error handling and graceful degradation

---

## 10. Monitoring and Observability

### Requirement 10.1: Metrics Collection

```python
# core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Voice path metrics
voice_session_total = Counter(
    'voice_sessions_total',
    'Total voice sessions created',
    ['agent_type']
)

voice_latency = Histogram(
    'voice_response_latency_seconds',
    'Voice response latency',
    ['component']  # stt, llm, tts, total
)

# Text path metrics
text_request_total = Counter(
    'text_requests_total',
    'Total text chat requests',
    ['agent_type']
)

text_latency = Histogram(
    'text_response_latency_seconds',
    'Text response latency',
    ['agent_type']
)

# LangChain metrics
langchain_calls = Counter(
    'langchain_llm_calls_total',
    'Total LangChain LLM calls',
    ['provider', 'model', 'agent_type']
)

langchain_tokens = Counter(
    'langchain_tokens_total',
    'Total tokens used',
    ['provider', 'model', 'type']  # type: prompt | completion
)

# LiveKit metrics
livekit_rooms_active = Gauge(
    'livekit_rooms_active',
    'Active LiveKit rooms'
)
```

#### Acceptance Criteria

1. THE System SHALL collect metrics for both voice and text paths
2. THE System SHALL track latency at component level (STT, LLM, TTS)
3. THE System SHALL track LangChain LLM calls and token usage
4. THE System SHALL track active LiveKit rooms
5. THE System SHALL expose metrics via Prometheus endpoint
6. THE System SHALL support integration with Grafana for visualization

---

## 11. Security Requirements

### Requirement 11.1: Authentication and Authorization

#### Acceptance Criteria

1. THE System SHALL validate JWT tokens for all API requests
2. THE System SHALL include user_id in LiveKit room metadata for agent authorization
3. THE System SHALL prevent agents from accessing data for different users
4. THE System SHALL encrypt API keys in environment variables
5. THE System SHALL use HTTPS/WSS for all external connections
6. THE System SHALL implement rate limiting (60 requests/minute per user)
7. THE System SHALL audit all tool calls that modify user data

---

## 12. Success Criteria

The hybrid architecture is considered successful when:

1. ✅ Voice interactions achieve <2 second latency (95th percentile)
2. ✅ Text interactions achieve <3 second latency (95th percentile)
3. ✅ Both paths share the same LangChain orchestrator and agents
4. ✅ LiveKit Agent workers successfully delegate to LangChain for complex reasoning
5. ✅ System maintains conversation history consistency across paths
6. ✅ All 6 specialized agents work in both voice and text modes
7. ✅ System handles 100+ concurrent users
8. ✅ Voice sessions are stable with <1% error rate
9. ✅ LangChain tool calling works reliably from LiveKit agents
10. ✅ System supports switching LLM providers via configuration

---

## Appendix A: Key Design Decisions

### Decision 1: Why Hybrid Architecture?

**Rationale:** LiveKit Agents excels at real-time voice processing (STT→TTS) but has limited agent orchestration capabilities. LangChain excels at agent orchestration and tool management but isn't optimized for real-time voice. Combining both gives best-of-both-worlds.

### Decision 2: Why Not Use LiveKit's LLM Plugins for Everything?

**Rationale:** LiveKit's LLM plugins (e.g., `livekit.plugins.openai.LLM`) are designed for simple function calling in voice context. They lack:
- Agent orchestration
- Multi-agent coordination
- Provider abstraction
- Complex tool ecosystems
- Conversation memory management

LangChain provides all of these, making it better suited for the orchestration layer.

### Decision 3: Voice Mode vs. Text Mode

**Rationale:** Voice requires different optimization:
- Shorter responses (30 seconds spoken)
- Faster routing (cached classifications)
- Simpler tool calls (cached data)
- Async logging (non-blocking)

Text allows:
- Detailed responses
- Complex tool calling
- Synchronous operations
- Full database queries

### Decision 4: Pre-loading Context

**Rationale:** Loading user context on every voice utterance adds 200-500ms latency. Pre-loading at session start and caching in memory reduces voice response time by 20-30%.

---

## Appendix B: Alternative Approaches Considered

### Alternative 1: LiveKit Only (No LangChain)

**Pros:**
- Simpler architecture
- One less framework

**Cons:**
- Limited agent orchestration
- Manual tool management
- No provider abstraction
- Difficult multi-agent coordination

**Verdict:** Rejected - insufficient for complex agent requirements

### Alternative 2: LangChain Only (No LiveKit)

**Pros:**
- Unified architecture
- Excellent agent capabilities

**Cons:**
- No native voice support
- Must build STT→TTS pipeline manually
- No WebRTC infrastructure
- Difficult real-time audio

**Verdict:** Rejected - voice is core requirement

### Alternative 3: Separate Stacks (LiveKit for Voice, LangChain for Text)

**Pros:**
- Complete separation
- Independent scaling

**Cons:**
- Code duplication
- Inconsistent behavior
- Double maintenance

**Verdict:** Rejected - violates DRY principle

---

## Document Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-02 | Initial document | Technical Team |

---

## References

1. [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
2. [LiveKit Python SDK Reference](https://docs.livekit.io/reference/python/livekit/agents/)
3. [LiveKit Tool Definition Guide](https://docs.livekit.io/agents/build/tools/)
4. [LangChain Documentation](https://python.langchain.com)
5. [LangChain Streaming Guide](https://python.langchain.com/docs/modules/model_io/chat/streaming/)
6. [LangChain Agent Documentation](https://python.langchain.com/docs/modules/agents/)