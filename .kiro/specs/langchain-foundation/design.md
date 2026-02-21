# LangChain Foundation & Base Agent Framework - Design

## Design Information
**Feature:** LangChain Foundation & Base Agent Framework  
**Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** February 4, 2026

---

## Architecture Overview

### System Context

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

### Component Responsibilities

**AgentContext:**
- Immutable data container
- Holds all user data needed for agent decisions
- Loaded once per interaction
- Cached in voice mode

**BaseAgent:**
- Abstract base class for all agents
- Manages LLM initialization
- Provides message formatting
- Defines interface for specialized agents

**AgentOrchestrator:**
- Routes queries to appropriate agents
- Loads user context from database
- Classifies queries (placeholder in this spec)
- Caches agents and classifications in voice mode

**Context Loader:**
- Loads user profile from database
- Assembles complete AgentContext
- Handles missing data gracefully

---

## Data Models

### AgentContext

```python
class AgentContext(BaseModel):
    """Immutable context passed to all agents"""
    
    # User Identity
    user_id: str
    
    # Fitness Profile
    fitness_level: str  # "beginner" | "intermediate" | "advanced"
    primary_goal: str   # "fat_loss" | "muscle_gain" | "general_fitness"
    secondary_goal: Optional[str]
    
    # Current State
    energy_level: str = "medium"  # "low" | "medium" | "high"
    
    # Plans (cached from database)
    current_workout_plan: Dict = {}
    current_meal_plan: Dict = {}
    
    # Conversation History
    conversation_history: List[Dict] = []
    
    # Metadata
    loaded_at: datetime
    
    class Config:
        frozen = True  # Immutable
```

**Design Decisions:**
- Immutable to prevent accidental modifications
- All data loaded upfront to avoid mid-interaction queries
- Conversation history limited to last N messages
- Timestamps for cache invalidation

### AgentResponse

```python
class AgentResponse(BaseModel):
    """Standardized agent response"""
    
    content: str              # Agent's response text
    agent_type: str           # Which agent handled this
    tools_used: List[str]     # Tools called during processing
    metadata: Dict            # Additional metadata
```

**Design Decisions:**
- Standardized format for all agents
- Tracks which agent responded
- Records tool usage for debugging
- Extensible metadata field

---

## Component Design

### 1. BaseAgent Abstract Class

**Purpose:** Provide common functionality for all specialized agents

**Key Methods:**

```python
class BaseAgent(ABC):
    def __init__(self, context: AgentContext, db_session: Optional[AsyncSession])
    
    # Abstract methods (must be implemented by subclasses)
    @abstractmethod
    async def process_text(self, query: str) -> AgentResponse
    
    @abstractmethod
    async def process_voice(self, query: str) -> str
    
    @abstractmethod
    async def stream_response(self, query: str) -> AsyncIterator[str]
    
    @abstractmethod
    def get_tools(self) -> List
    
    @abstractmethod
    def _system_prompt(self, voice_mode: bool) -> str
    
    # Concrete methods (provided by base class)
    def _init_llm(self)
    def _init_classifier_llm(self)
    def _build_messages(self, query: str, voice_mode: bool) -> List
    def _format_chat_history(self) -> List
```

**Design Decisions:**
- Abstract methods force consistent interface
- Concrete methods provide shared functionality
- Separate LLM for classification (fast model)
- Voice mode affects message history limit (5 vs 10)

### 2. TestAgent Implementation

**Purpose:** Validate the base agent framework

**Implementation:**
- Extends BaseAgent
- Minimal system prompt
- No tools
- Simple pass-through to LLM

**Design Decisions:**
- Intentionally simple for testing
- No complex logic
- Validates framework only

### 3. Context Loader Service

**Purpose:** Load user data from database into AgentContext

**Flow:**
```
load_agent_context(db, user_id)
    ↓
Query UserProfile
    ↓
Load workout plan (placeholder)
    ↓
Load meal plan (placeholder)
    ↓
Load conversation history (placeholder)
    ↓
Build AgentContext
    ↓
Return context
```

**Design Decisions:**
- Single function, not a class
- Async for database operations
- Placeholder functions for future implementation
- Raises ValueError if user not found

### 4. Agent Orchestrator

**Purpose:** Route queries to appropriate agents

**State Management:**
```python
class AgentOrchestrator:
    db_session: AsyncSession
    mode: str  # "text" | "voice"
    _agent_cache: Optional[Dict]  # Only in voice mode
    _classification_cache: Dict
    last_agent_type: Optional[AgentType]
```

**Key Methods:**

```python
async def route_query(
    user_id: str,
    query: str,
    agent_type: Optional[AgentType],
    voice_mode: bool
) -> AgentResponse

async def _classify_query(query: str) -> AgentType

def _get_or_create_agent(agent_type: AgentType, context: AgentContext)

def _create_agent(agent_type: AgentType, context: AgentContext)

async def warm_up()
```

**Design Decisions:**
- Mode affects caching strategy
- Voice mode caches agents for performance
- Classification cached in voice mode
- Factory pattern for agent creation
- Warm-up for LLM connection pre-establishment

---

## LLM Provider Support

### Configuration

```python
class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"

class Settings(BaseSettings):
    LLM_PROVIDER: LLMProvider = LLMProvider.ANTHROPIC
    LLM_MODEL: str = "claude-sonnet-4-5-20250929"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    
    ANTHROPIC_API_KEY: Optional[str]
    OPENAI_API_KEY: Optional[str]
    GOOGLE_API_KEY: Optional[str]
    
    CLASSIFIER_MODEL: str = "claude-haiku-4-5-20251001"
    CLASSIFIER_TEMPERATURE: float = 0.1
```

### Provider Initialization

```python
def _init_llm(self):
    provider = settings.LLM_PROVIDER
    
    if provider == "anthropic":
        return ChatAnthropic(
            model=settings.LLM_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )
    elif provider == "openai":
        return ChatOpenAI(...)
    elif provider == "google":
        return ChatGoogleGenerativeAI(...)
```

**Design Decisions:**
- Single provider active at a time
- Classifier always uses Claude Haiku (fast)
- API keys validated at startup
- Provider-specific parameters handled

---

## Message Flow

### Text Mode Flow

```
User Query
    ↓
AgentOrchestrator.route_query()
    ↓
load_agent_context(db, user_id)
    ↓
_classify_query(query)  # Returns AgentType.TEST
    ↓
_get_or_create_agent(TEST, context)
    ↓
agent.process_text(query)
    ↓
_build_messages(query, voice_mode=False)
    ↓
llm.ainvoke(messages)
    ↓
Return AgentResponse
```

### Voice Mode Flow

```
User Query
    ↓
AgentOrchestrator.route_query(voice_mode=True)
    ↓
load_agent_context(db, user_id)
    ↓
Check _classification_cache
    ↓
_get_or_create_agent(cached_type, context)
    ↓
Check _agent_cache
    ↓
agent.process_voice(query)
    ↓
_build_messages(query, voice_mode=True)  # Limited history
    ↓
llm.ainvoke(messages)
    ↓
Return string response
```

**Design Decisions:**
- Voice mode uses caching for performance
- Voice mode limits conversation history (5 vs 10)
- Voice mode returns string, not AgentResponse
- Classification cached by first 50 chars of query

---

## Performance Considerations

### Voice Mode Optimizations

1. **Agent Caching**
   - Agents cached in memory
   - Avoids re-initialization overhead
   - Cache key: AgentType

2. **Classification Caching**
   - Classifications cached by query prefix
   - Cache key: First 50 characters
   - Reduces LLM calls

3. **Context Loading**
   - Context loaded once per interaction
   - Cached data (workout/meal plans)
   - No mid-interaction database queries

4. **Fast Classifier**
   - Always uses Claude Haiku
   - Temperature 0.1 for consistency
   - Max 10 tokens output

### Text Mode Behavior

- No caching (fresh agents each time)
- Full conversation history (10 messages)
- Detailed AgentResponse with metadata
- Supports streaming

---

## Error Handling

### User Not Found
```python
if not profile:
    raise ValueError(f"User profile not found: {user_id}")
```

### Invalid LLM Provider
```python
if provider not in ["anthropic", "openai", "google"]:
    raise ValueError(f"Unsupported LLM provider: {provider}")
```

### Missing API Key
```python
if self.LLM_PROVIDER == LLMProvider.ANTHROPIC:
    if not self.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY required")
```

### Warm-up Failure
```python
try:
    await test_agent.llm.ainvoke([HumanMessage(content="hello")])
except Exception as e:
    logger.warning(f"Warm-up failed: {e}")
    # Continue anyway - not critical
```

**Design Decisions:**
- Fail fast for configuration errors
- Graceful degradation for warm-up
- Detailed error messages
- Logging for all errors

---

## Testing Strategy

### Unit Tests

1. **AgentContext Creation**
   - Test immutability
   - Test default values
   - Test validation

2. **BaseAgent Initialization**
   - Test LLM provider selection
   - Test message building
   - Test history formatting

3. **TestAgent Responses**
   - Test text mode
   - Test voice mode
   - Test streaming

### Integration Tests

1. **Context Loader**
   - Test with real database
   - Test missing user
   - Test data assembly

2. **Orchestrator Routing**
   - Test text mode
   - Test voice mode
   - Test caching behavior
   - Test warm-up

### Test Fixtures

```python
@pytest.fixture
async def test_user(db_session):
    """Create test user with profile"""
    # Create user and profile
    # Return user object

@pytest.fixture
def agent_context():
    """Create test AgentContext"""
    return AgentContext(
        user_id="test-user",
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
```

---

## Implementation Order

1. **Step 1:** Install dependencies
2. **Step 2:** Create AgentContext and AgentResponse models
3. **Step 3:** Create BaseAgent abstract class
4. **Step 4:** Create TestAgent implementation
5. **Step 5:** Create context_loader service
6. **Step 6:** Create AgentOrchestrator
7. **Step 7:** Update configuration
8. **Step 8:** Create integration tests

**Rationale:** Bottom-up approach - build foundation first, then orchestration

---

## Future Enhancements (Out of Scope)

The following will be added in later sub-docs:

1. **Sub-Doc 2:**
   - Actual query classification logic
   - Specialized agent implementations
   - Domain-specific tools

2. **Sub-Doc 3:**
   - Conversation history persistence
   - Conversation history loading

3. **Sub-Doc 6:**
   - Redis-based context caching
   - Performance metrics
   - Advanced error handling

---

## Security Considerations

1. **API Keys**
   - Stored in environment variables
   - Never logged or exposed
   - Validated at startup

2. **User Data**
   - Context is immutable
   - No data leakage between users
   - Database queries use user_id filter

3. **Input Validation**
   - Pydantic validates all inputs
   - Query length limits (handled by LLM)
   - User ID format validation

---

## Monitoring and Logging

### Logging Points

```python
logger.info(f"Loaded context for user {user_id}")
logger.info(f"Classified query as: {agent_type.value}")
logger.info("LLM connection warmed up")
logger.warning(f"Warm-up failed: {e}")
logger.error(f"Context load error: {e}", exc_info=True)
```

### Metrics (Future)

- Context load time
- Classification time
- Agent response time
- Cache hit rate

---

## Configuration Reference

### Environment Variables

```bash
# LLM Provider
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=xxx

# Classifier
CLASSIFIER_MODEL=claude-haiku-4-5-20251001
CLASSIFIER_TEMPERATURE=0.1
```

### Defaults

- LLM_PROVIDER: anthropic
- LLM_TEMPERATURE: 0.7
- LLM_MAX_TOKENS: 4096
- CLASSIFIER_TEMPERATURE: 0.1
- CLASSIFIER_MAX_TOKENS: 10

---

## Acceptance Criteria Summary

✅ AgentContext model is immutable and contains all required fields  
✅ BaseAgent provides proper abstraction with all required methods  
✅ TestAgent validates the framework  
✅ Context loader retrieves data from database  
✅ AgentOrchestrator routes queries correctly  
✅ Multi-provider LLM support works  
✅ Voice mode uses caching for performance  
✅ Text mode provides full functionality  
✅ All integration tests pass  
✅ Configuration is complete and validated  

---

## References

- [requirements.md](./requirements.md) - Requirements document
- [01-LANGCHAIN-FOUNDATION.md](../../../docs/technichal/phase-2-breakdown/01-LANGCHAIN-FOUNDATION.md) - Source document
- [LangChain Documentation](https://python.langchain.com)
