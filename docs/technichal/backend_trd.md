## FastAPI + LiveKit Architecture Analysis

### **Why This Stack Makes Sense**

**FastAPI Advantages for Your Project:**
1. **Async-first architecture** - Perfect for handling multiple concurrent agent interactions
2. **Automatic API documentation** - OpenAPI/Swagger out of the box
3. **Pydantic validation** - Type-safe data models align perfectly with your schema
4. **Performance** - Comparable to Node.js, faster than Django/Flask
5. **Python ecosystem** - Better for AI/ML integrations, data processing
6. **Simpler deployment** - Single language stack if you do data science later

**LiveKit Advantages:**
1. **Purpose-built for real-time agents** - Not adapting a generic solution
2. **Voice + Text in one platform** - Unified agent interface
3. **WebRTC infrastructure** - Low-latency, high-quality voice
4. **Agent framework included** - Built-in orchestration for AI agents
5. **Open source** - No vendor lock-in, self-hostable
6. **Production-ready** - Used by companies handling millions of concurrent sessions

---

## Revised Tech Stack Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                              │
│  (iOS/Android/Web)                                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌──────────────┐
│ REST API│  │GraphQL  │  │LiveKit Agent │
│         │  │(optional)│  │  Interface   │
└────┬────┘  └────┬────┘  └──────┬───────┘
     │            │               │
     └────────────┴───────────────┘
                  │
         ┌────────┴────────┐
         │   FastAPI Core  │
         │   Application   │
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────────┐
    ▼             ▼                 ▼
┌──────────┐  ┌─────────┐     ┌─────────────┐
│PostgreSQL│  │  Redis  │     │LiveKit Server│
└──────────┘  └─────────┘     └─────────────┘
```

---

## Complete Stack Specification

### **1. Backend Core**

```yaml
Framework: FastAPI 0.109+
Runtime: Python 3.11+
ASGI Server: Uvicorn with Gunicorn workers

Key Libraries:
  - fastapi[all]: Core framework
  - sqlalchemy 2.0+: ORM
  - alembic: Database migrations
  - pydantic 2.0+: Data validation
  - asyncpg: Async PostgreSQL driver
  - redis[hiredis]: Async Redis client
  - celery: Background tasks
  - python-jose[cryptography]: JWT tokens
```

**Project Structure:**
```
backend/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings (Pydantic BaseSettings)
│   ├── dependencies.py         # DI, auth, db sessions
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── onboarding.py
│   │   │   │   ├── profiles.py
│   │   │   │   ├── workouts.py
│   │   │   │   ├── meals.py
│   │   │   │   └── chat.py
│   │   │   └── router.py
│   │   └── deps.py
│   │
│   ├── agents/                 # Your 6 AI agents
│   │   ├── base.py            # Base agent class
│   │   ├── workout_planner.py
│   │   ├── diet_planner.py
│   │   ├── supplement_guide.py
│   │   ├── tracker.py
│   │   ├── scheduler.py
│   │   └── assistant.py
│   │
│   ├── livekit_agents/        # LiveKit integration
│   │   ├── voice_agent.py
│   │   ├── text_agent.py
│   │   └── agent_runner.py
│   │
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── profile.py
│   │   ├── meal_plan.py
│   │   └── workout.py
│   │
│   ├── schemas/               # Pydantic schemas
│   │   ├── user.py
│   │   ├── onboarding.py
│   │   └── responses.py
│   │
│   ├── services/              # Business logic
│   │   ├── onboarding_service.py
│   │   ├── profile_service.py
│   │   └── agent_orchestrator.py
│   │
│   ├── core/
│   │   ├── security.py        # Auth, encryption
│   │   ├── cache.py           # Redis utilities
│   │   |── events.py          # Event handlers
|   |   └── config.py          # Env improts and validation
│   │
│   └── db/
│       ├── base.py
│       ├── session.py
│       └── migrations/        # Alembic
│
├── tests/
├── alembic/
├── requirements.txt
└── docker-compose.yml
```

---

### **2. LiveKit Integration**

**LiveKit Components:**

```yaml
LiveKit Server: Self-hosted or Cloud
LiveKit Agents SDK: Python

Architecture:
  ┌──────────────────┐
  │  Client App      │
  │  (LiveKit Client)│
  └────────┬─────────┘
           │ WebRTC
           ▼
  ┌──────────────────┐
  │ LiveKit Server   │
  │ (SFU/Media)      │
  └────────┬─────────┘
           │ Webhooks/Events
           ▼
  ┌──────────────────┐
  │ FastAPI Backend  │
  │ + Agent Workers  │
  └──────────────────┘
```

**LiveKit Agent Implementation:**

```python
# livekit_agents/voice_agent.py
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import openai, deepgram, cartesia
import logging

class FitnessVoiceAgent:
    def __init__(
        self,
        user_context: dict,
        agent_type: str  # 'workout' | 'diet' | 'general'
    ):
        self.user_context = user_context
        self.agent_type = agent_type
        self.conversation_history = []
    
    async def run(self, ctx: JobContext):
        """Main agent entry point"""
        
        # Connect to room
        await ctx.connect()
        
        # Initialize STT (Speech-to-Text)
        stt = deepgram.STT(
            model="nova-2-general",
            language="en"
        )
        
        # Initialize LLM
        llm = openai.LLM(
            model="gpt-4-turbo",
            temperature=0.7
        )
        
        # Initialize TTS (Text-to-Speech)
        tts = cartesia.TTS(
            model="sonic-english",
            voice_id="fitness-coach-male"  # Custom voice
        )
        
        # Create agent with voice pipeline
        assistant = agents.VoiceAssistant(
            vad=ctx.vad,
            stt=stt,
            llm=llm,
            tts=tts,
            chat_ctx=self._build_chat_context(),
            fnc_ctx=self._build_function_context()
        )
        
        # Start the agent
        assistant.start(ctx.room)
        
        # Handle session
        await self._handle_session(ctx, assistant)
    
    def _build_chat_context(self):
        """Build LLM context from user profile"""
        
        system_prompt = f"""
You are a {self.agent_type} fitness coach assistant.

User Context:
- Fitness Level: {self.user_context['fitness_level']}
- Primary Goal: {self.user_context['primary_goal']}
- Current Energy: {self.user_context['energy_level']}

Guidelines:
- Be conversational and motivating
- Reference their specific workout/meal plan
- Never give medical advice
- Keep responses under 30 seconds when spoken
        """
        
        return agents.ChatContext(
            messages=[
                {"role": "system", "content": system_prompt}
            ]
        )
    
    def _build_function_context(self):
        """Define functions agent can call"""
        
        @agents.llm_function
        async def get_next_exercise():
            """Get the user's next scheduled exercise"""
            # Query your database
            return await self._fetch_next_exercise()
        
        @agents.llm_function
        async def get_current_meal():
            """Get details about the user's current meal"""
            return await self._fetch_current_meal()
        
        @agents.llm_function  
        async def log_workout_completion(exercise: str, sets: int):
            """Log that user completed a workout"""
            await self._log_workout(exercise, sets)
            return {"status": "logged"}
        
        return agents.FunctionContext(
            functions=[
                get_next_exercise,
                get_current_meal,
                log_workout_completion
            ]
        )
    
    async def _handle_session(self, ctx: JobContext, assistant):
        """Handle the conversation session"""
        
        # Wait for participant to join
        participant = await ctx.wait_for_participant()
        
        # Greet the user
        await assistant.say(
            f"Hey! Ready for your workout? "
            f"You're doing {self.user_context['workout_today']}"
        )
        
        # Listen and respond
        async for event in ctx.room.events():
            if isinstance(event, agents.TranscriptionReceived):
                # User spoke
                await self._handle_user_speech(event, assistant)
```

**Text Agent (Chat Interface):**

```python
# livekit_agents/text_agent.py
from livekit import agents
from typing import AsyncGenerator

class FitnessTextAgent:
    """Text-based chat agent (similar to voice but no STT/TTS)"""
    
    async def run(self, ctx: JobContext):
        """Handle text chat"""
        
        llm = openai.LLM(model="gpt-4-turbo")
        
        agent = agents.AssistantLLM(
            llm=llm,
            chat_ctx=self._build_chat_context(),
            fnc_ctx=self._build_function_context()
        )
        
        # Listen for text messages
        async for msg in ctx.room.messages():
            response = await agent.chat(msg.content)
            await ctx.room.send_message(response)
```

**Agent Worker (Background Process):**

```python
# livekit_agents/agent_runner.py
from livekit.agents import Worker, WorkerOptions
from .voice_agent import FitnessVoiceAgent
from .text_agent import FitnessTextAgent

async def entrypoint(ctx: JobContext):
    """Main entry point for LiveKit agent worker"""
    
    # Get user context from room metadata
    room_metadata = ctx.room.metadata
    user_id = room_metadata.get("user_id")
    agent_type = room_metadata.get("agent_type", "general")
    
    # Fetch user context from database
    async with get_db_session() as db:
        user_context = await fetch_user_context(db, user_id)
    
    # Determine if voice or text
    if room_metadata.get("mode") == "voice":
        agent = FitnessVoiceAgent(user_context, agent_type)
    else:
        agent = FitnessTextAgent(user_context, agent_type)
    
    await agent.run(ctx)

# Run the worker
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            num_idle_workers=2,  # Pre-warm workers
        )
    )
```

---

### **3. FastAPI Integration with LiveKit**

```python
# api/v1/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException
from livekit import api
import secrets

router = APIRouter()

@router.post("/start-voice-session")
async def start_voice_session(
    agent_type: str,  # 'workout' | 'diet' | 'general'
    current_user: User = Depends(get_current_user),
    livekit_client: api.LiveKitAPI = Depends(get_livekit_client)
):
    """Start a voice coaching session"""
    
    # Create LiveKit room
    room_name = f"fitness-{current_user.id}-{secrets.token_hex(4)}"
    
    room = await livekit_client.room.create_room(
        api.CreateRoomRequest(
            name=room_name,
            metadata=json.dumps({
                "user_id": str(current_user.id),
                "agent_type": agent_type,
                "mode": "voice"
            })
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
        can_subscribe=True
    ))
    
    jwt_token = token.to_jwt()
    
    return {
        "room_name": room_name,
        "token": jwt_token,
        "livekit_url": settings.LIVEKIT_URL
    }

@router.post("/start-text-session")
async def start_text_session(
    agent_type: str,
    current_user: User = Depends(get_current_user),
    livekit_client: api.LiveKitAPI = Depends(get_livekit_client)
):
    """Start a text chat session"""
    # Similar to voice but with mode='text'
    pass

@router.get("/session/{room_name}/status")
async def get_session_status(
    room_name: str,
    current_user: User = Depends(get_current_user),
    livekit_client: api.LiveKitAPI = Depends(get_livekit_client)
):
    """Get status of active session"""
    
    room = await livekit_client.room.get_room(room_name)
    
    return {
        "active": room.num_participants > 0,
        "duration_seconds": room.creation_time,
        "agent_connected": room.num_participants >= 2
    }
```

---

### **4. Database Layer**

**SQLAlchemy Models (Async):**

```python
# models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_auth_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    account_status = Column(String(50), nullable=False, default='active')
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    onboarding_state = relationship("OnboardingState", back_populates="user", uselist=False)
    meal_plan = relationship("MealPlan", back_populates="user", uselist=False)
```

**Async Database Session:**

```python
# db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

### **5. Agent Orchestration**

**Base Agent Class:**

```python
# agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel

class AgentContext(BaseModel):
    """Shared context for all agents"""
    user_id: str
    fitness_level: str
    primary_goal: str
    secondary_goal: str | None
    energy_level: str
    current_meal_plan: Dict
    current_workout_plan: Dict
    conversation_history: List[Dict] = []

class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, context: AgentContext, db_session: AsyncSession):
        self.context = context
        self.db = db_session
        self.llm = self._init_llm()
    
    @abstractmethod
    async def process(self, query: str) -> str:
        """Process user query and return response"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """Return agent-specific tools/functions"""
        pass
    
    def _init_llm(self):
        """Initialize LLM with agent-specific config"""
        from langchain_anthropic import ChatAnthropic
        
        return ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0.7,
            max_tokens=1024
        )
```

**Workout Planning Agent:**

```python
# agents/workout_planner.py
from .base import BaseAgent
from langchain.tools import tool

class WorkoutPlannerAgent(BaseAgent):
    """Specialized agent for workout planning and guidance"""
    
    async def process(self, query: str) -> str:
        """Handle workout-related queries"""
        
        # Build prompt with user context
        prompt = self._build_prompt(query)
        
        # Call LLM with tools
        from langchain.agents import create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate
        
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.get_tools(),
            prompt=ChatPromptTemplate.from_messages([
                ("system", self._system_prompt()),
                ("user", "{input}"),
                ("assistant", "{agent_scratchpad}")
            ])
        )
        
        result = await agent.ainvoke({"input": query})
        return result["output"]
    
    def get_tools(self) -> List:
        """Workout-specific tools"""
        
        @tool
        async def get_current_workout():
            """Get today's workout plan for the user"""
            # Query database
            stmt = select(WorkoutSchedule).where(
                WorkoutSchedule.user_id == self.context.user_id
            )
            result = await self.db.execute(stmt)
            return result.scalars().first()
        
        @tool
        async def show_exercise_demo(exercise_name: str):
            """Get GIF demonstration for an exercise"""
            # Query exercise database
            stmt = select(Exercise).where(
                Exercise.name == exercise_name
            )
            result = await self.db.execute(stmt)
            exercise = result.scalars().first()
            return exercise.demo_gif_url if exercise else None
        
        @tool
        async def log_set_completion(exercise: str, reps: int, weight: float):
            """Log a completed set"""
            # Insert into workout_logs table
            log = WorkoutLog(
                user_id=self.context.user_id,
                exercise=exercise,
                reps=reps,
                weight_kg=weight,
                logged_at=datetime.utcnow()
            )
            self.db.add(log)
            await self.db.commit()
            return {"status": "logged"}
        
        return [get_current_workout, show_exercise_demo, log_set_completion]
    
    def _system_prompt(self) -> str:
        return f"""
You are a workout planning assistant for a fitness app.

User Context:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}
- Energy Level: {self.context.energy_level}

Current Workout Plan:
{json.dumps(self.context.current_workout_plan, indent=2)}

Guidelines:
- Be motivating but realistic
- Reference their specific workout plan
- Suggest modifications if energy is low
- Never give medical advice
- Use available tools to fetch data or log progress
        """
```

**Agent Orchestrator:**

```python
# services/agent_orchestrator.py
from enum import Enum

class AgentType(str, Enum):
    WORKOUT = "workout"
    DIET = "diet"
    SUPPLEMENT = "supplement"
    TRACKER = "tracker"
    SCHEDULER = "scheduler"
    GENERAL = "general"

class AgentOrchestrator:
    """Routes queries to appropriate agent"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.agents = {}
    
    async def route_query(
        self,
        user_id: str,
        query: str,
        agent_type: AgentType | None = None
    ) -> str:
        """Route query to appropriate agent"""
        
        # Load user context
        context = await self._load_context(user_id)
        
        # Determine agent if not specified
        if not agent_type:
            agent_type = await self._classify_query(query)
        
        # Get or create agent
        agent = await self._get_agent(agent_type, context)
        
        # Process query
        response = await agent.process(query)
        
        # Update conversation history
        await self._update_history(user_id, query, response)
        
        return response
    
    async def _classify_query(self, query: str) -> AgentType:
        """Use LLM to classify which agent should handle query"""
        
        classifier_prompt = f"""
Classify this user query into one category:
- workout: Exercise plans, form, demonstrations
- diet: Meal plans, nutrition, cooking
- supplement: Supplement guidance
- tracker: Progress tracking, missed sessions
- scheduler: Timing, reminders, schedule changes
- general: Motivation, casual conversation

Query: {query}

Respond with only the category name.
        """
        
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-haiku-4-5-20250514")  # Fast classifier
        
        result = await llm.ainvoke(classifier_prompt)
        return AgentType(result.content.strip().lower())
    
    async def _load_context(self, user_id: str) -> AgentContext:
        """Load user profile and create agent context"""
        
        # Fetch from database
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalars().first()
        
        # Build context object
        return AgentContext(
            user_id=user_id,
            fitness_level=profile.fitness_level,
            primary_goal=profile.primary_goal,
            secondary_goal=profile.secondary_goal,
            energy_level=profile.energy_level,
            current_meal_plan=await self._get_meal_plan(user_id),
            current_workout_plan=await self._get_workout_plan(user_id)
        )
```

---

### **6. Background Tasks & Scheduling**

**Celery Configuration:**

```python
# core/celery_app.py
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "fitness_app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    'send-workout-reminders': {
        'task': 'app.tasks.send_workout_reminders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'send-meal-reminders': {
        'task': 'app.tasks.send_meal_reminders',
        'schedule': crontab(minute='*/30'),
    },
    'send-hydration-reminders': {
        'task': 'app.tasks.send_hydration_reminders',
        'schedule': crontab(hour='*/1'),  # Hourly
    },
    'recalculate-adaptive-plans': {
        'task': 'app.tasks.recalculate_plans',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

**Task Definitions:**

```python
# tasks/notifications.py
from app.core.celery_app import celery_app
from datetime import datetime, time
import pytz

@celery_app.task
async def send_workout_reminders():
    """Send workout reminders to users based on their schedule"""
    
    current_time = datetime.utcnow().time()
    
    async with get_db_session() as db:
        # Find users who have workouts scheduled soon
        stmt = select(User, WorkoutSchedule).join(WorkoutSchedule).where(
            WorkoutSchedule.workout_reminder_enabled == True,
            # Complex time matching logic here
        )
        
        results = await db.execute(stmt)
        
        for user, schedule in results:
            await send_push_notification(
                user_id=user.id,
                title="Workout Time!",
                body=f"Your {schedule.workout_type} is scheduled now",
                data={"type": "workout_reminder"}
            )

@celery_app.task
async def recalculate_plans():
    """Daily recalculation of adaptive plans based on user adherence"""
    
    async with get_db_session() as db:
        # Get users with recent missed sessions
        users = await get_users_needing_recalculation(db)
        
        for user in users:
            await recalculate_user_plan(db, user)
```

---

### **7. Configuration Management**

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Fitness AI"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 86400  # 24 hours
    
    # LiveKit
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    
    # AI/LLM
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str  # For LiveKit voice
    
    # Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Push Notifications
    FCM_CREDENTIALS_PATH: str
    
    # Storage
    S3_BUCKET: str
    S3_REGION: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

---

### **8. Deployment Architecture**

```yaml
# docker-compose.yml
version: '3.8'

services:
  # FastAPI backend
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/fitness
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
  
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
  
  # Celery worker (background tasks)
  celery_worker:
    build: ./backend
    command: celery -A app.core.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/fitness
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  # Celery beat (scheduler)
  celery_beat:
    build: ./backend
    command: celery -A app.core.celery_app beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
  
  # LiveKit server (self-hosted option)
  livekit:
    image: livekit/livekit-server:latest
    command: --dev
    ports:
      - "7880:7880"  # HTTP
      - "7881:7881"  # HTTPS
      - "50000-50100:50000-50100/udp"  # WebRTC
    volumes:
      - ./livekit.yaml:/livekit.yaml
  
  # LiveKit agent worker
  livekit_agent:
    build:
      context: ./backend
      dockerfile: Dockerfile.agent
    environment:
      - LIVEKIT_URL=ws://livekit:7880
      - LIVEKIT_API_KEY=your_key
      - LIVEKIT_API_SECRET=your_secret
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/fitness
    depends_on:
      - livekit
      - postgres

volumes:
  postgres_data:
  redis_data:
```

---

### **9. Cost Estimation (10K Active Users)**

```yaml
Self-Hosted Option (DigitalOcean/Hetzner):
  Compute:
    - API Server (4 vCPU, 8GB): $80/month
    - Celery Workers (2x2vCPU): $60/month
    - LiveKit Server (8 vCPU, 16GB): $160/month
    - Agent Workers (2x4vCPU): $120/month
  
  Database:
    - Managed PostgreSQL (4GB): $60/month
    - Redis (2GB): $20/month
  
  Storage:
    - S3/Spaces (100GB): $20/month
  
  LLM Costs:
    - Claude API (~1M tokens/day): $300/month
    - Deepgram STT (~1000 hrs/month): $100/month
    - Cartesia TTS (~1000 hrs/month): $150/month
  
  Total: ~$1,070/month

AWS Option:
  - ECS Fargate: $250/month
  - RDS PostgreSQL: $150/month
  - ElastiCache: $50/month
  - S3: $30/month
  - LLM Costs: $550/month
  
  Total: ~$1,030/month
```

---

### **10. Development Roadmap**

**Phase 1: Foundation**
- [ ] FastAPI project setup
- [ ] Database schema implementation
- [ ] Auth system (JWT)
- [ ] Onboarding API endpoints
- [ ] Basic CRUD operations

**Phase 2: AI Integration**
- [ ] LangChain agent setup
- [ ] Implement 6 specialized agents
- [ ] Agent orchestration logic
- [ ] Testing with mock data

**Phase 3: LiveKit Integration**
- [ ] LiveKit server setup
- [ ] Voice agent implementation
- [ ] Text agent implementation
- [ ] Client SDK integration
- [ ] End-to-end voice testing

**Phase 4: Background Jobs**
- [ ] Celery setup
- [ ] Notification system
- [ ] Scheduled reminders
- [ ] Adaptive recalculation

**Phase 5: Testing & Launch**
- [ ] Load testing
- [ ] Security audit
- [ ] Beta user testing
- [ ] Production deployment

---