# Sub-Doc 5: LiveKit Voice Agent Implementation

## Document Information
**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Ready for Implementation  
**Parent:** [00-PHASE-2-OVERVIEW.md](./00-PHASE-2-OVERVIEW.md)  
**Dependencies:** Sub-Doc 1, 2 (Agents), Sub-Doc 4 (LiveKit Infrastructure)

---

## Objective

Implement LiveKit voice agent worker that:
- Connects to LiveKit rooms
- Handles STT (Speech-to-Text) via Deepgram
- Handles TTS (Text-to-Speech) via Cartesia
- Bridges to LangChain orchestrator for reasoning
- Provides function tools for quick queries
- Achieves <2 second latency

---

## Prerequisites Verification

```bash
# Verify dependencies
python -c "from app.services.agent_orchestrator import AgentOrchestrator; print('✓')"
python -c "from app.core.livekit_client import get_livekit_api; print('✓')"
poetry run pytest backend/tests/test_voice_sessions.py -v
```

---

## Architecture

```
[User speaks] → [LiveKit Server] → [Voice Agent Worker]
                                          ↓
                                    [Deepgram STT]
                                          ↓
                                    [Function Tools]
                                          ↓
                              ┌───────────┴───────────┐
                              │                       │
                         [Quick Tool]          [LangChain Agent]
                         (cached data)         (complex reasoning)
                              │                       │
                              └───────────┬───────────┘
                                          ↓
                                    [GPT-4o/Claude]
                                          ↓
                                    [Cartesia TTS]
                                          ↓
                                    [Audio Response]
```

---

## Implementation Steps

### Step 1: Install LiveKit Agents SDK

**File:** `backend/requirements-agent.txt`

```txt
# LiveKit Agents with plugins
livekit-agents[deepgram,openai,cartesia]==1.3.12

# LangChain (shared with main app)
langchain==0.3.0
langchain-core==0.3.0
langchain-anthropic==0.3.0

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

```bash
poetry add livekit-agents[deepgram,openai,cartesia]
```

---

### Step 2: Update Configuration

**File:** `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing ...
    
    # LiveKit Voice Services
    DEEPGRAM_API_KEY: str = Field(..., description="Deepgram STT API key")
    CARTESIA_API_KEY: str = Field(..., description="Cartesia TTS API key")
    
    # Voice Optimization
    VOICE_CONTEXT_CACHE_TTL: int = Field(default=3600, description="Context cache TTL in seconds")
    VOICE_MAX_RESPONSE_TOKENS: int = Field(default=150, description="Max tokens for voice responses")
```

**File:** `backend/.env.example`

```bash
# LiveKit Voice Services
DEEPGRAM_API_KEY=xxx
CARTESIA_API_KEY=xxx

# Voice Optimization
VOICE_CONTEXT_CACHE_TTL=3600
VOICE_MAX_RESPONSE_TOKENS=150
```

---

### Step 3: Create Voice Agent Worker

**File:** `backend/app/livekit_agents/voice_agent_worker.py`

```python
"""LiveKit voice agent worker"""
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, Agent, function_tool, RunContext
from livekit.plugins import deepgram, openai, cartesia
import asyncio
import json
import logging

from app.core.config import settings
from app.services.agent_orchestrator import AgentOrchestrator, AgentType
from app.services.context_loader import load_agent_context
from app.db.session import async_session_maker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FitnessVoiceAgent(Agent):
    """Voice agent that delegates to LangChain for reasoning"""
    
    def __init__(self, user_id: str, agent_type: str):
        super().__init__(
            instructions=self._get_base_instructions(agent_type)
        )
        self.user_id = user_id
        self.agent_type = agent_type
        
        # LangChain orchestrator (initialized later)
        self.orchestrator = None
        self.user_context = None
        
        # Log queue for async processing
        self._log_queue = asyncio.Queue()
        self._log_worker_task = None
    
    async def initialize_orchestrator(self):
        """Pre-load LangChain orchestrator with user context"""
        async with async_session_maker() as db:
            # Load user context from database
            self.user_context = await load_agent_context(db, self.user_id)
            
            # Initialize LangChain orchestrator with context
            self.orchestrator = AgentOrchestrator(
                db_session=db,
                mode="voice"
            )
            
            # Pre-warm LLM connection
            await self.orchestrator.warm_up()
            
        logger.info(f"Initialized orchestrator for user {self.user_id}")
    
    @function_tool()
    async def get_todays_workout(self, context: RunContext) -> str:
        """Get user's workout plan for today.
        
        This tool retrieves the current workout from cached context,
        avoiding database queries during voice interaction.
        """
        if not self.user_context:
            return "Context not loaded"
        
        workout = self.user_context.current_workout_plan.get("today", "No workout scheduled")
        exercises = self.user_context.current_workout_plan.get("exercises", [])
        
        return f"Today's workout: {workout}. Exercises: {', '.join(exercises)}"
    
    @function_tool()
    async def get_todays_meals(self, context: RunContext) -> str:
        """Get user's meal plan for today."""
        if not self.user_context:
            return "Context not loaded"
        
        meals = self.user_context.current_meal_plan
        return json.dumps(meals)
    
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
        await self._log_queue.put({
            "type": "workout_set",
            "exercise": exercise,
            "reps": reps,
            "weight": weight,
            "timestamp": datetime.utcnow().isoformat()
        })
        
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
        if not self.orchestrator:
            return "Orchestrator not initialized"
        
        try:
            # Call LangChain orchestrator
            async with async_session_maker() as db:
                self.orchestrator.db = db
                response = await self.orchestrator.route_query(
                    user_id=self.user_id,
                    query=query,
                    agent_type=AgentType(specialist),
                    voice_mode=True
                )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Specialist agent error: {e}")
            return "I'm having trouble processing that. Can you rephrase?"
    
    async def start_log_worker(self):
        """Start background worker for logging"""
        self._log_worker_task = asyncio.create_task(self._log_worker())
    
    async def _log_worker(self):
        """Background worker that flushes logs to database"""
        while True:
            try:
                log_entry = await self._log_queue.get()
                
                async with async_session_maker() as db:
                    # Write to database
                    from app.models.workout import WorkoutLog
                    log = WorkoutLog(
                        user_id=self.user_id,
                        exercise=log_entry["exercise"],
                        reps=log_entry["reps"],
                        weight_kg=log_entry["weight"],
                        logged_at=datetime.fromisoformat(log_entry["timestamp"])
                    )
                    db.add(log)
                    await db.commit()
                    
                self._log_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Log worker error: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._log_worker_task:
            self._log_worker_task.cancel()
            try:
                await self._log_worker_task
            except asyncio.CancelledError:
                pass
    
    def _get_base_instructions(self, agent_type: str) -> str:
        """Get base instructions for the agent"""
        return f"""You are a helpful fitness coach assistant specializing in {agent_type}.

Your role is to:
- Answer quick questions about workouts and meals
- Log workout progress
- Provide motivation and encouragement

For complex queries, use the ask_specialist_agent tool.

Keep responses conversational and under 30 seconds when spoken.
"""


async def entrypoint(ctx: JobContext):
    """Main entrypoint for LiveKit agent worker"""
    
    # Extract metadata from room
    metadata = json.loads(ctx.room.metadata or "{}")
    user_id = metadata.get("user_id")
    agent_type = metadata.get("agent_type", "general")
    
    if not user_id:
        logger.error("No user_id in room metadata")
        return
    
    logger.info(f"Starting voice agent for user {user_id}, type {agent_type}")
    
    # Create agent
    agent = FitnessVoiceAgent(user_id=user_id, agent_type=agent_type)
    
    # Pre-load orchestrator BEFORE connecting
    await agent.initialize_orchestrator()
    
    # Start log worker
    await agent.start_log_worker()
    
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
        instructions=f"Greet the user warmly and ask how you can help with their {agent_type} today."
    )
    
    # Wait for session to end
    await session.wait_for_completion()
    
    # Cleanup
    await agent.cleanup()
    
    logger.info(f"Voice agent session ended for user {user_id}")


if __name__ == "__main__":
    # Run the agent worker
    agents.cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            num_idle_workers=settings.LIVEKIT_WORKER_NUM_IDLE,
            worker_type=agents.WorkerType.ROOM
        )
    )
```

---

### Step 4: Create Agent Dockerfile

**File:** `backend/Dockerfile.agent`

```dockerfile
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
CMD ["python", "app/livekit_agents/voice_agent_worker.py"]
```

---

### Step 5: Update Docker Compose

**File:** `docker-compose.yml`

```yaml
services:
  # ... existing services ...
  
  # LiveKit agent worker
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
    deploy:
      replicas: 2  # Run multiple agent workers
```

---

### Step 6: Create Integration Test

**File:** `backend/tests/test_voice_agent_integration.py`

```python
"""Integration tests for voice agent"""
import pytest
from unittest.mock import Mock, AsyncMock
from app.livekit_agents.voice_agent_worker import FitnessVoiceAgent


@pytest.mark.asyncio
async def test_voice_agent_initialization(test_user):
    """Test voice agent can initialize"""
    agent = FitnessVoiceAgent(
        user_id=str(test_user.id),
        agent_type="workout"
    )
    
    await agent.initialize_orchestrator()
    
    assert agent.orchestrator is not None
    assert agent.user_context is not None
    assert agent.user_context.user_id == str(test_user.id)


@pytest.mark.asyncio
async def test_get_todays_workout_tool(test_user):
    """Test workout tool returns cached data"""
    agent = FitnessVoiceAgent(
        user_id=str(test_user.id),
        agent_type="workout"
    )
    
    await agent.initialize_orchestrator()
    
    # Mock context
    mock_context = Mock()
    result = await agent.get_todays_workout(mock_context)
    
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_log_workout_set_tool(test_user):
    """Test logging tool queues data"""
    agent = FitnessVoiceAgent(
        user_id=str(test_user.id),
        agent_type="workout"
    )
    
    await agent.start_log_worker()
    
    mock_context = Mock()
    result = await agent.log_workout_set(
        mock_context,
        exercise="Bench Press",
        reps=10,
        weight=185.0
    )
    
    assert "Logged" in result
    assert "Bench Press" in result
    
    await agent.cleanup()


@pytest.mark.asyncio
async def test_ask_specialist_agent_tool(test_user):
    """Test specialist agent delegation"""
    agent = FitnessVoiceAgent(
        user_id=str(test_user.id),
        agent_type="general"
    )
    
    await agent.initialize_orchestrator()
    
    mock_context = Mock()
    result = await agent.ask_specialist_agent(
        mock_context,
        query="What's the best form for squats?",
        specialist="workout"
    )
    
    assert isinstance(result, str)
    assert len(result) > 0
```

---

## Running the Voice Agent Worker

### Development

```bash
# Set environment variables
export LIVEKIT_URL=wss://your-project.livekit.cloud
export LIVEKIT_API_KEY=APIxxxxxx
export LIVEKIT_API_SECRET=secretxxxx
export DEEPGRAM_API_KEY=xxx
export CARTESIA_API_KEY=xxx

# Run worker
poetry run python backend/app/livekit_agents/voice_agent_worker.py
```

### Production (Docker)

```bash
docker-compose up -d livekit_agent
docker-compose logs -f livekit_agent
```

---

## Verification Checklist

- [ ] LiveKit Agents SDK installed
- [ ] Voice agent worker implemented
- [ ] Function tools defined
- [ ] LangChain bridge working
- [ ] Dockerfile created
- [ ] Docker Compose updated
- [ ] Tests pass
- [ ] Worker connects to LiveKit
- [ ] Agent responds to voice

**Manual Test:**
1. Start voice agent worker
2. Create voice session via API
3. Connect with LiveKit client
4. Speak to agent
5. Verify response

---

## Success Criteria

✅ Voice agent worker runs  
✅ Connects to LiveKit rooms  
✅ STT/TTS working  
✅ Function tools callable  
✅ LangChain delegation works  
✅ Tests pass  
✅ Latency <2 seconds  

**Estimated Time:** 5-7 days

**Next:** [06-VOICE-OPTIMIZATION.md](./06-VOICE-OPTIMIZATION.md)
