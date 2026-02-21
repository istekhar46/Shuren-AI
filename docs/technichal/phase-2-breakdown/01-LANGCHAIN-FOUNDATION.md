# Sub-Doc 1: LangChain Foundation & Base Agent Framework

## Document Information
**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Ready for Implementation  
**Parent:** [00-PHASE-2-OVERVIEW.md](./00-PHASE-2-OVERVIEW.md)  
**Dependencies:** Phase 1 (Database, Models, Auth)

---

## Objective

Establish the foundational LangChain infrastructure including:
- Base agent class with LLM integration
- Agent context management
- Agent orchestrator for routing queries
- Multi-provider LLM support (Anthropic, OpenAI, Google)
- Database integration for context loading

---

## Prerequisites Verification

Before starting, verify Phase 1 is complete:

```bash
# 1. Database models exist
ls backend/app/models/user.py
ls backend/app/models/profile.py

# 2. Database session is async
grep "AsyncSession" backend/app/db/session.py

# 3. User profile can be queried
poetry run python -c "from app.models.profile import UserProfile; print('✓ Models OK')"

# 4. Redis is configured
grep "REDIS_URL" backend/.env
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Endpoint                      │
│                  (Text or Voice Path)                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  AgentOrchestrator    │
         │  - Load user context  │
         │  - Classify query     │
         │  - Route to agent     │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ┌─────────┐            ┌─────────┐
    │ Agent A │            │ Agent B │
    │ (Base)  │            │ (Base)  │
    └────┬────┘            └────┬────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  LangChain LLM   │
         │  (Anthropic/     │
         │   OpenAI/Google) │
         └──────────────────┘
```

---

## Implementation Steps

### Step 1: Install LangChain Dependencies

**File:** `backend/pyproject.toml`

Add to dependencies:
```toml
[tool.poetry.dependencies]
langchain = "^0.3.0"
langchain-core = "^0.3.0"
langchain-anthropic = "^0.3.0"
langchain-openai = "^0.3.0"
langchain-google-genai = "^2.0.0"
```

**Verification:**
```bash
cd backend
poetry install
poetry run python -c "import langchain; print(f'LangChain {langchain.__version__}')"
```

---

### Step 2: Create Agent Context Model

**File:** `backend/app/agents/context.py`

```python
"""Agent context models for LangChain agents"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class AgentContext(BaseModel):
    """Immutable context passed to all agents
    
    This context is loaded once per interaction and contains
    all necessary user data for agent decision-making.
    """
    
    # User Identity
    user_id: str = Field(..., description="User UUID")
    
    # Fitness Profile
    fitness_level: str = Field(..., description="beginner | intermediate | advanced")
    primary_goal: str = Field(..., description="fat_loss | muscle_gain | general_fitness")
    secondary_goal: Optional[str] = Field(None, description="Optional secondary goal")
    
    # Current State
    energy_level: str = Field(default="medium", description="low | medium | high")
    
    # Plans (cached from database)
    current_workout_plan: Dict = Field(default_factory=dict, description="Today's workout")
    current_meal_plan: Dict = Field(default_factory=dict, description="Today's meals")
    
    # Conversation History (last N messages)
    conversation_history: List[Dict] = Field(
        default_factory=list,
        description="Recent conversation messages"
    )
    
    # Metadata
    loaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True  # Immutable after creation


class AgentResponse(BaseModel):
    """Standardized agent response"""
    
    content: str = Field(..., description="Agent's response text")
    agent_type: str = Field(..., description="Which agent handled this")
    tools_used: List[str] = Field(default_factory=list, description="Tools called")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")
```

**Verification:**
```bash
poetry run python -c "from app.agents.context import AgentContext; print('✓ Context model OK')"
```

---

### Step 3: Create Base Agent Class

**File:** `backend/app/agents/base.py`

```python
"""Base agent class for all specialized agents"""
from abc import ABC, abstractmethod
from typing import List, AsyncIterator
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from .context import AgentContext, AgentResponse


class BaseAgent(ABC):
    """Base class for all specialized agents
    
    Provides:
    - LLM initialization with multi-provider support
    - Message formatting
    - Conversation history management
    - Abstract methods for specialization
    """
    
    def __init__(self, context: AgentContext, db_session: Optional[AsyncSession] = None):
        """Initialize agent with context
        
        Args:
            context: Immutable user context
            db_session: Optional database session for tools
        """
        self.context = context
        self.db = db_session
        self.llm = self._init_llm()
        self.classifier_llm = self._init_classifier_llm()
    
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
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _init_classifier_llm(self):
        """Initialize fast LLM for classification tasks"""
        # Always use Haiku for fast classification
        return ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.1,
            max_tokens=10
        )
    
    @abstractmethod
    async def process_text(self, query: str) -> AgentResponse:
        """Process text query with full capabilities
        
        Args:
            query: User's text query
            
        Returns:
            AgentResponse with detailed answer
        """
        pass
    
    @abstractmethod
    async def process_voice(self, query: str) -> str:
        """Process voice query with concise response
        
        Args:
            query: User's voice query (from STT)
            
        Returns:
            Concise string response (for TTS)
        """
        pass
    
    @abstractmethod
    async def stream_response(self, query: str) -> AsyncIterator[str]:
        """Stream response for text interactions
        
        Args:
            query: User's query
            
        Yields:
            Response chunks
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List:
        """Get LangChain tools for this agent
        
        Returns:
            List of @tool decorated functions
        """
        pass
    
    @abstractmethod
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """Get system prompt for this agent
        
        Args:
            voice_mode: Whether this is for voice interaction
            
        Returns:
            System prompt string
        """
        pass
    
    def _build_messages(self, query: str, voice_mode: bool = False) -> List:
        """Build message chain for LLM
        
        Args:
            query: Current user query
            voice_mode: Whether this is voice interaction
            
        Returns:
            List of LangChain messages
        """
        messages = [
            SystemMessage(content=self._system_prompt(voice_mode))
        ]
        
        # Add conversation history (limited for voice)
        history_limit = 5 if voice_mode else 10
        for msg in self.context.conversation_history[-history_limit:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        return messages
    
    def _format_chat_history(self) -> List:
        """Format conversation history for LangChain agents
        
        Returns:
            List of LangChain message objects
        """
        history = []
        for msg in self.context.conversation_history[-10:]:
            if msg["role"] == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history.append(AIMessage(content=msg["content"]))
        return history
```

**Verification:**
```bash
poetry run python -c "from app.agents.base import BaseAgent; print('✓ Base agent OK')"
```

---

### Step 4: Create Simple Test Agent

**File:** `backend/app/agents/test_agent.py`

```python
"""Simple test agent for verification"""
from typing import List, AsyncIterator
from langchain_core.tools import tool

from .base import BaseAgent
from .context import AgentContext, AgentResponse


class TestAgent(BaseAgent):
    """Simple agent for testing the framework"""
    
    async def process_text(self, query: str) -> AgentResponse:
        """Process text query"""
        messages = self._build_messages(query, voice_mode=False)
        result = await self.llm.ainvoke(messages)
        
        return AgentResponse(
            content=result.content,
            agent_type="test",
            tools_used=[],
            metadata={"model": self.llm.model_name}
        )
    
    async def process_voice(self, query: str) -> str:
        """Process voice query"""
        messages = self._build_messages(query, voice_mode=True)
        result = await self.llm.ainvoke(messages)
        return result.content
    
    async def stream_response(self, query: str) -> AsyncIterator[str]:
        """Stream response"""
        messages = self._build_messages(query, voice_mode=False)
        
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content
    
    def get_tools(self) -> List:
        """No tools for test agent"""
        return []
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """System prompt"""
        base = f"""You are a test fitness assistant.

User Context:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}

Just respond helpfully to test the system.
"""
        
        if voice_mode:
            base += "\nKeep responses under 30 seconds when spoken."
        
        return base
```

**Verification:**
```bash
poetry run python -c "from app.agents.test_agent import TestAgent; print('✓ Test agent OK')"
```

---

### Step 5: Create Context Loader Service

**File:** `backend/app/services/context_loader.py`

```python
"""Service for loading agent context from database"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from app.models.user import User
from app.models.profile import UserProfile
from app.agents.context import AgentContext

logger = logging.getLogger(__name__)


async def load_agent_context(
    db: AsyncSession,
    user_id: str,
    include_history: bool = True
) -> AgentContext:
    """Load complete agent context for a user
    
    Args:
        db: Database session
        user_id: User UUID
        include_history: Whether to load conversation history
        
    Returns:
        AgentContext with all user data
        
    Raises:
        ValueError: If user not found
    """
    
    # Load user profile
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalars().first()
    
    if not profile:
        raise ValueError(f"User profile not found: {user_id}")
    
    # Load current workout plan (simplified for now)
    current_workout = await _load_current_workout(db, user_id)
    
    # Load current meal plan (simplified for now)
    current_meal = await _load_current_meal(db, user_id)
    
    # Load conversation history if requested
    conversation_history = []
    if include_history:
        conversation_history = await _load_conversation_history(db, user_id, limit=10)
    
    # Build context
    context = AgentContext(
        user_id=str(user_id),
        fitness_level=profile.fitness_level or "beginner",
        primary_goal=profile.primary_goal or "general_fitness",
        secondary_goal=profile.secondary_goal,
        energy_level=profile.energy_level or "medium",
        current_workout_plan=current_workout,
        current_meal_plan=current_meal,
        conversation_history=conversation_history
    )
    
    logger.info(f"Loaded context for user {user_id}")
    return context


async def _load_current_workout(db: AsyncSession, user_id: str) -> dict:
    """Load today's workout plan"""
    # TODO: Implement actual workout loading in Sub-Doc 2
    return {
        "today": "Push Day",
        "exercises": ["Bench Press", "Shoulder Press", "Tricep Dips"]
    }


async def _load_current_meal(db: AsyncSession, user_id: str) -> dict:
    """Load today's meal plan"""
    # TODO: Implement actual meal loading in Sub-Doc 2
    return {
        "breakfast": "Oatmeal with berries",
        "lunch": "Chicken salad",
        "dinner": "Salmon with vegetables"
    }


async def _load_conversation_history(
    db: AsyncSession,
    user_id: str,
    limit: int = 10
) -> list:
    """Load recent conversation history"""
    # TODO: Implement conversation history table in Sub-Doc 3
    return []
```

**Verification:**
```bash
poetry run python -c "from app.services.context_loader import load_agent_context; print('✓ Context loader OK')"
```

---

### Step 6: Create Agent Orchestrator

**File:** `backend/app/services/agent_orchestrator.py`

```python
"""Agent orchestrator for routing queries to specialized agents"""
from enum import Enum
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.context import AgentContext, AgentResponse
from app.agents.test_agent import TestAgent
from .context_loader import load_agent_context

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Available agent types"""
    WORKOUT = "workout"
    DIET = "diet"
    SUPPLEMENT = "supplement"
    TRACKER = "tracker"
    SCHEDULER = "scheduler"
    GENERAL = "general"
    TEST = "test"  # For testing


class AgentOrchestrator:
    """Routes queries to appropriate specialized agents
    
    Responsibilities:
    - Load user context from database
    - Classify queries to determine agent type
    - Route to appropriate agent
    - Cache agents for voice mode
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        mode: str = "text"  # "text" | "voice"
    ):
        """Initialize orchestrator
        
        Args:
            db_session: Database session
            mode: Interaction mode (affects caching strategy)
        """
        self.db = db_session
        self.mode = mode
        
        # Cache for voice mode
        self._agent_cache = {} if mode == "voice" else None
        self._classification_cache = {}
        
        # Track last agent used
        self.last_agent_type: Optional[AgentType] = None
    
    async def route_query(
        self,
        user_id: str,
        query: str,
        agent_type: Optional[AgentType] = None,
        voice_mode: bool = False
    ) -> AgentResponse:
        """Route query to appropriate agent
        
        Args:
            user_id: User UUID
            query: User's query
            agent_type: Optional explicit agent type
            voice_mode: Whether this is voice interaction
            
        Returns:
            AgentResponse from the agent
        """
        
        # Load user context
        context = await load_agent_context(self.db, user_id)
        
        # Determine agent type if not specified
        if not agent_type:
            agent_type = await self._classify_query(query)
        
        self.last_agent_type = agent_type
        
        # Get agent
        agent = self._get_or_create_agent(agent_type, context)
        
        # Process based on mode
        if voice_mode or self.mode == "voice":
            response_text = await agent.process_voice(query)
            return AgentResponse(
                content=response_text,
                agent_type=agent_type.value,
                tools_used=[],
                metadata={"mode": "voice"}
            )
        else:
            return await agent.process_text(query)
    
    async def _classify_query(self, query: str) -> AgentType:
        """Classify query to determine agent type
        
        Args:
            query: User's query
            
        Returns:
            AgentType enum
        """
        
        # Check cache (voice mode only)
        if self.mode == "voice":
            cache_key = query[:50]
            if cache_key in self._classification_cache:
                return self._classification_cache[cache_key]
        
        # For now, always return TEST agent
        # TODO: Implement actual classification in Sub-Doc 2
        agent_type = AgentType.TEST
        
        # Cache for voice mode
        if self.mode == "voice":
            self._classification_cache[cache_key] = agent_type
        
        logger.info(f"Classified query as: {agent_type.value}")
        return agent_type
    
    def _get_or_create_agent(self, agent_type: AgentType, context: AgentContext):
        """Get cached agent or create new one
        
        Args:
            agent_type: Type of agent needed
            context: User context
            
        Returns:
            Agent instance
        """
        
        # For voice mode, cache agents
        if self._agent_cache is not None:
            if agent_type not in self._agent_cache:
                self._agent_cache[agent_type] = self._create_agent(agent_type, context)
            return self._agent_cache[agent_type]
        
        # For text mode, create fresh agent
        return self._create_agent(agent_type, context)
    
    def _create_agent(self, agent_type: AgentType, context: AgentContext):
        """Factory method to create specialized agents
        
        Args:
            agent_type: Type of agent to create
            context: User context
            
        Returns:
            Agent instance
        """
        
        # For now, only TEST agent exists
        # TODO: Add other agents in Sub-Doc 2
        agent_map = {
            AgentType.TEST: TestAgent,
            # AgentType.WORKOUT: WorkoutPlannerAgent,  # Sub-Doc 2
            # AgentType.DIET: DietPlannerAgent,        # Sub-Doc 2
            # ... etc
        }
        
        agent_class = agent_map.get(agent_type, TestAgent)
        return agent_class(context=context, db_session=self.db)
    
    async def warm_up(self):
        """Pre-warm LLM connections for voice mode"""
        if self.mode == "voice":
            # Make dummy call to establish connection
            try:
                test_agent = TestAgent(
                    context=AgentContext(
                        user_id="test",
                        fitness_level="beginner",
                        primary_goal="general_fitness"
                    )
                )
                await test_agent.llm.ainvoke([HumanMessage(content="hello")])
                logger.info("LLM connection warmed up")
            except Exception as e:
                logger.warning(f"Warm-up failed: {e}")
```

**Verification:**
```bash
poetry run python -c "from app.services.agent_orchestrator import AgentOrchestrator; print('✓ Orchestrator OK')"
```

---

### Step 7: Update Configuration

**File:** `backend/app/core/config.py`

Add LLM configuration:

```python
from enum import Enum

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"

class Settings(BaseSettings):
    # ... existing settings ...
    
    # LangChain LLM Configuration
    LLM_PROVIDER: LLMProvider = LLMProvider.ANTHROPIC
    LLM_MODEL: str = "claude-sonnet-4-5-20250929"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    
    # LLM API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Classifier Configuration
    CLASSIFIER_MODEL: str = "claude-haiku-4-5-20251001"
    CLASSIFIER_TEMPERATURE: float = 0.1
    
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
```

**File:** `backend/.env.example`

Add:
```bash
# LangChain LLM Configuration
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# LLM API Keys (provide one based on LLM_PROVIDER)
ANTHROPIC_API_KEY=sk-ant-xxx
# OPENAI_API_KEY=sk-xxx
# GOOGLE_API_KEY=xxx

# Classifier
CLASSIFIER_MODEL=claude-haiku-4-5-20251001
CLASSIFIER_TEMPERATURE=0.1
```

**Verification:**
```bash
poetry run python -c "from app.core.config import settings; settings.get_required_llm_api_key(); print('✓ Config OK')"
```

---

### Step 8: Create Integration Test

**File:** `backend/tests/test_langchain_foundation.py`

```python
"""Integration tests for LangChain foundation"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context import AgentContext
from app.agents.test_agent import TestAgent
from app.services.agent_orchestrator import AgentOrchestrator, AgentType
from app.services.context_loader import load_agent_context


@pytest.mark.asyncio
async def test_agent_context_creation():
    """Test creating agent context"""
    context = AgentContext(
        user_id="test-user-123",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        energy_level="high"
    )
    
    assert context.user_id == "test-user-123"
    assert context.fitness_level == "intermediate"
    assert context.primary_goal == "muscle_gain"


@pytest.mark.asyncio
async def test_test_agent_text_response():
    """Test agent can respond to text query"""
    context = AgentContext(
        user_id="test-user",
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    
    agent = TestAgent(context=context)
    response = await agent.process_text("What should I eat for breakfast?")
    
    assert isinstance(response.content, str)
    assert len(response.content) > 0
    assert response.agent_type == "test"


@pytest.mark.asyncio
async def test_test_agent_voice_response():
    """Test agent can respond to voice query"""
    context = AgentContext(
        user_id="test-user",
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    
    agent = TestAgent(context=context)
    response = await agent.process_voice("What's my workout today?")
    
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_context_loader(db_session: AsyncSession, test_user):
    """Test loading context from database"""
    context = await load_agent_context(db_session, str(test_user.id))
    
    assert context.user_id == str(test_user.id)
    assert context.fitness_level in ["beginner", "intermediate", "advanced"]
    assert context.primary_goal is not None


@pytest.mark.asyncio
async def test_agent_orchestrator_routing(db_session: AsyncSession, test_user):
    """Test orchestrator can route queries"""
    orchestrator = AgentOrchestrator(db_session=db_session, mode="text")
    
    response = await orchestrator.route_query(
        user_id=str(test_user.id),
        query="What should I do today?",
        agent_type=AgentType.TEST
    )
    
    assert isinstance(response.content, str)
    assert len(response.content) > 0
    assert orchestrator.last_agent_type == AgentType.TEST


@pytest.mark.asyncio
async def test_orchestrator_voice_mode(db_session: AsyncSession, test_user):
    """Test orchestrator in voice mode"""
    orchestrator = AgentOrchestrator(db_session=db_session, mode="voice")
    
    # Warm up
    await orchestrator.warm_up()
    
    # Query
    response = await orchestrator.route_query(
        user_id=str(test_user.id),
        query="Quick workout tip?",
        voice_mode=True
    )
    
    assert isinstance(response.content, str)
    assert response.metadata.get("mode") == "voice"
```

**Verification:**
```bash
poetry run pytest backend/tests/test_langchain_foundation.py -v
```

---

## Verification Checklist

After completing all steps, verify:

- [ ] LangChain dependencies installed
- [ ] `AgentContext` model created and importable
- [ ] `BaseAgent` class created with abstract methods
- [ ] `TestAgent` implemented and working
- [ ] Context loader can load user data from database
- [ ] `AgentOrchestrator` can route queries
- [ ] Configuration updated with LLM settings
- [ ] Integration tests pass
- [ ] Test agent responds to queries via orchestrator

**Final Test:**
```bash
# Run all foundation tests
poetry run pytest backend/tests/test_langchain_foundation.py -v

# Should see all tests passing
```

---

## What's Next?

Once this sub-doc is complete and verified:

1. **Move to Sub-Doc 2:** Implement the 6 specialized agents
2. **Each agent will:**
   - Extend `BaseAgent`
   - Implement domain-specific tools
   - Define specialized system prompts
   - Handle both text and voice modes

---

## Troubleshooting

### Issue: LangChain import errors
**Solution:** Ensure all dependencies installed: `poetry install`

### Issue: API key errors
**Solution:** Check `.env` file has correct API key for chosen provider

### Issue: Database connection errors
**Solution:** Verify Phase 1 database is running and migrated

### Issue: Test agent not responding
**Solution:** Check LLM API key is valid and has credits

---

## Success Criteria

Sub-Doc 1 is complete when:

✅ All verification steps pass  
✅ Integration tests pass  
✅ Test agent can respond to queries  
✅ Orchestrator can route to test agent  
✅ Context loads from database  
✅ Both text and voice modes work  

**Estimated Time:** 3-5 days

**Next:** [02-SPECIALIZED-AGENTS.md](./02-SPECIALIZED-AGENTS.md)
