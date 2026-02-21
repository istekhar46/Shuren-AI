# Design Document: Onboarding Conversation Memory

## Overview

This design implements conversation memory for onboarding agents by aligning their architecture with the established BaseAgent pattern. The solution creates an OnboardingAgentContext class (similar to AgentContext), updates BaseOnboardingAgent to use this context, and ensures conversation history is loaded and utilized throughout the onboarding flow.

The key architectural change is moving from a plain dict-based context to a structured Pydantic model that includes conversation_history, matching the pattern used by post-onboarding agents. This ensures consistency across all agent types and enables natural, context-aware conversations during onboarding.

## Architecture

### Current Architecture

**Post-Onboarding Agents (BaseAgent)**:
- Use AgentContext (Pydantic model) with conversation_history field
- Have _build_messages() helper method for consistent message construction
- Load conversation history from ConversationMessage table
- Maintain context across multiple messages

**Onboarding Agents (BaseOnboardingAgent)**:
- Use plain dict for context (no conversation_history)
- Manually construct prompts in each agent's stream_response method
- Accept conversation_history parameter but don't load it automatically
- Lose context between messages

### Target Architecture

**Unified Pattern**:
- Both BaseAgent and BaseOnboardingAgent use structured context models
- Both have _build_messages() helper for consistent message construction
- Both load conversation history automatically
- Both maintain context across messages

### Architectural Alignment

```
BaseAgent                          BaseOnboardingAgent
├── AgentContext                   ├── OnboardingAgentContext
│   ├── user_id                    │   ├── user_id
│   ├── conversation_history       │   ├── conversation_history
│   ├── fitness_level              │   ├── agent_context (dict)
│   └── ...                        │   └── loaded_at
├── _build_messages()              ├── _build_messages()
├── _format_chat_history()         └── (uses same pattern)
└── process_text/voice             
```

## Components and Interfaces

### 1. OnboardingAgentContext (New)

**Location**: `backend/app/agents/context.py`

**Purpose**: Immutable Pydantic model containing all data needed for onboarding agent interactions, including conversation history.

**Interface**:
```python
class OnboardingAgentContext(BaseModel):
    """
    Immutable context for onboarding agents.
    
    Attributes:
        user_id: Unique identifier for the user
        conversation_history: Recent conversation messages
        agent_context: Data collected by previous agents
        loaded_at: Timestamp when context was loaded
    """
    user_id: str
    conversation_history: List[Dict] = Field(default_factory=list)
    agent_context: Dict = Field(default_factory=dict)
    loaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True  # Immutable
```

**Design Rationale**:
- Matches AgentContext structure for consistency
- Includes conversation_history for memory
- Includes agent_context for onboarding state data
- Immutable to prevent accidental modifications

### 2. BaseOnboardingAgent Updates

**Location**: `backend/app/agents/onboarding/base.py`

**Changes**:
1. Constructor accepts OnboardingAgentContext
2. Add _build_messages() helper method

**New Interface**:
```python
class BaseOnboardingAgent(ABC):
    def __init__(self, db: AsyncSession, context: OnboardingAgentContext):
        self.db = db
        self.context = context  # Now OnboardingAgentContext
        self.llm = self._init_llm()
    
    def _build_messages(self, message: str) -> List:
        """
        Build message chain for LLM including system prompt, history, and current query.
        
        Args:
            message: Current user message
            
        Returns:
            List of LangChain messages (SystemMessage, HumanMessage, AIMessage)
        """
        messages = [SystemMessage(content=self.get_system_prompt())]
        
        # Add conversation history (limit to last 15 messages)
        for msg in self.context.conversation_history[-15:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=message))
        
        return messages
```

**Design Rationale**:
- _build_messages() centralizes message construction logic
- Limits history to 15 messages to prevent token overflow
- Uses LangChain message types for consistency with BaseAgent
- System prompt comes from get_system_prompt() (agent-specific)

### 3. OnboardingAgentOrchestrator Updates

**Location**: `backend/app/services/onboarding_orchestrator.py`

**Changes**:
1. Load conversation history from ConversationMessage table
2. Create OnboardingAgentContext instead of plain dict
3. Pass structured context to agent constructor

**New Method**:
```python
async def _load_conversation_history(self, user_id: UUID) -> List[Dict]:
    """
    Load recent conversation history for user.
    
    Args:
        user_id: UUID of the user
        
    Returns:
        List of messages in format [{"role": "user"|"assistant", "content": "..."}]
    """
    from app.models.conversation import ConversationMessage
    
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.user_id == user_id)
        .order_by(ConversationMessage.created_at.asc())
        .limit(20)  # Limit to last 20 messages
    )
    
    result = await self.db.execute(stmt)
    messages = result.scalars().all()
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

async def _create_agent(
    self,
    agent_type: OnboardingAgentType,
    context_dict: dict,
    user_id: UUID
) -> BaseOnboardingAgent:
    """
    Factory method to create agent instance with conversation history.
    
    Args:
        agent_type: Type of agent to create
        context_dict: Agent context from database
        user_id: UUID of the user
        
    Returns:
        Instance of the appropriate agent class
    """
    # Load conversation history
    conversation_history = await self._load_conversation_history(user_id)
    
    # Create OnboardingAgentContext
    context = OnboardingAgentContext(
        user_id=str(user_id),
        conversation_history=conversation_history,
        agent_context=context_dict
    )
    
    # Instantiate agent
    agent_classes = {
        OnboardingAgentType.FITNESS_ASSESSMENT: FitnessAssessmentAgent,
        OnboardingAgentType.GOAL_SETTING: GoalSettingAgent,
        OnboardingAgentType.WORKOUT_PLANNING: WorkoutPlanningAgent,
        OnboardingAgentType.DIET_PLANNING: DietPlanningAgent,
        OnboardingAgentType.SCHEDULING: SchedulingAgent,
    }
    
    agent_class = agent_classes[agent_type]
    return agent_class(self.db, context)
```

**Design Rationale**:
- Loads last 20 messages from database (orchestrator level)
- BaseOnboardingAgent._build_messages() further limits to 15 (agent level)
- Two-tier limiting prevents token overflow while maintaining flexibility
- Conversation history loaded once per agent creation (efficient)

### 4. Individual Agent Updates

**Location**: All 5 agents in `backend/app/agents/onboarding/`

**Changes**:
Each agent's stream_response method will be updated to use _build_messages():

**Before**:
```python
async def stream_response(self, message: str, conversation_history: list = None):
    messages = [("system", self.get_system_prompt())]
    
    if conversation_history:
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(("ai", msg["content"]))
    
    messages.append(("human", "{input}"))
    prompt = ChatPromptTemplate.from_messages(messages)
    formatted_messages = prompt.format_messages(input=message)
    
    async for chunk in self.llm.astream(formatted_messages):
        if hasattr(chunk, 'content') and chunk.content:
            yield chunk.content
```

**After**:
```python
async def stream_response(self, message: str):
    # Build messages using helper (includes system prompt + history + current message)
    messages = self._build_messages(message)
    
    # Stream response chunks from LLM
    async for chunk in self.llm.astream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            yield chunk.content
```

**Design Rationale**:
- Removes duplicate message construction logic
- Simpler, more maintainable code
- Consistent with BaseAgent pattern

## Data Models

### OnboardingAgentContext

```python
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "conversation_history": [
        {"role": "user", "content": "I'm a beginner"},
        {"role": "assistant", "content": "Great! Let's assess your fitness level..."},
        {"role": "user", "content": "I can do 10 pushups"},
        {"role": "assistant", "content": "That's a good starting point..."}
    ],
    "agent_context": {
        "fitness_assessment": {
            "fitness_level": "beginner",
            "limitations": ["lower_back_pain"],
            "completed_at": "2026-02-04T12:00:00Z"
        },
        "goal_setting": {
            "primary_goal": "fat_loss",
            "target_weight_kg": 75.0,
            "completed_at": "2026-02-04T12:15:00Z"
        }
    },
    "loaded_at": "2026-02-04T12:30:00Z"
}
```

### Conversation History Format

```python
[
    {"role": "user", "content": "message text"},
    {"role": "assistant", "content": "response text"}
]
```

This format matches:
- ConversationMessage table structure
- BaseAgent conversation_history format
- LangChain message conversion expectations

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Message Structure Invariant

*For any* user message and agent context, when _build_messages() is called, the returned list should have a SystemMessage as the first element and a HumanMessage with the user's message content as the last element.

**Validates: Requirements 3.3, 3.6**

### Property 2: Conversation History Inclusion with Limiting

*For any* OnboardingAgentContext with conversation history, when _build_messages() is called, the returned list should include messages from the conversation history (up to the last 15 messages) between the system prompt and the current user message.

**Validates: Requirements 3.4, 3.5**

### Property 3: History Format Conversion

*For any* valid conversation history in dict format [{"role": "user"|"assistant", "content": "..."}], when _build_messages() processes it, each dict should be converted to the corresponding LangChain message type (HumanMessage for "user", AIMessage for "assistant") with the same content.

**Validates: Requirements 3.7**

### Property 4: Orchestrator Message Loading with Ordering and Limiting

*For any* user with conversation messages in the database, when OnboardingAgentOrchestrator loads conversation history, it should return at most the last 20 messages ordered by created_at ascending.

**Validates: Requirements 4.2, 4.3, 6.1**

### Property 5: Orchestrator Format Transformation

*For any* set of ConversationMessage objects loaded from the database, when OnboardingAgentOrchestrator formats them, each message should be transformed to a dict with "role" and "content" keys matching the original message's role and content fields.

**Validates: Requirements 4.4**

### Property 6: History Limiting Preserves Recency

*For any* conversation history exceeding the limit (15 for _build_messages, 20 for orchestrator), when the system applies the limit, only the most recent messages should be included, and their relative order (oldest to newest) should be preserved.

**Validates: Requirements 6.2, 6.3, 6.4**

### Property 7: Message Content Preservation

*For any* message in the conversation history, when the system processes it through loading, formatting, and message building, the message content should never be truncated or modified, regardless of message length.

**Validates: Requirements 6.5**

## Error Handling

### Invalid Context Creation

**Scenario**: OnboardingAgentContext created with invalid data

**Handling**:
- Pydantic validation will raise ValidationError for invalid types
- Missing required fields will raise ValidationError
- Caller should catch ValidationError and handle appropriately

**Example**:
```python
try:
    context = OnboardingAgentContext(
        user_id=123,  # Invalid: should be str
        conversation_history="not a list"  # Invalid: should be List[Dict]
    )
except ValidationError as e:
    logger.error(f"Invalid context data: {e}")
    # Handle error appropriately
```

### Database Query Failures

**Scenario**: OnboardingAgentOrchestrator fails to load conversation history

**Handling**:
- Database errors should be caught and logged
- Return empty conversation history as fallback
- Agent can still function without history (degraded experience)

**Example**:
```python
async def _load_conversation_history(self, user_id: UUID) -> List[Dict]:
    try:
        # Query database
        ...
    except Exception as e:
        logger.error(f"Failed to load conversation history for {user_id}: {e}")
        return []  # Fallback to empty history
```

### Message Building Failures

**Scenario**: _build_messages() receives malformed conversation history

**Handling**:
- Skip malformed messages with warning log
- Continue processing valid messages
- Ensure system prompt and current message are always included

**Example**:
```python
def _build_messages(self, message: str) -> List:
    messages = [SystemMessage(content=self.get_system_prompt())]
    
    for msg in self.context.conversation_history[-15:]:
        try:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        except (KeyError, TypeError) as e:
            logger.warning(f"Skipping malformed message: {e}")
            continue
    
    messages.append(HumanMessage(content=message))
    return messages
```

### Agent Instantiation Failures

**Scenario**: Agent constructor fails with new context type

**Handling**:
- Catch TypeError or AttributeError during agent creation
- Log error with full context for debugging
- Raise ValueError with clear message for caller

**Example**:
```python
async def _create_agent(self, agent_type, context_dict, user_id):
    try:
        conversation_history = await self._load_conversation_history(user_id)
        context = OnboardingAgentContext(
            user_id=str(user_id),
            conversation_history=conversation_history,
            agent_context=context_dict
        )
        agent_class = agent_classes[agent_type]
        return agent_class(self.db, context)
    except Exception as e:
        logger.error(f"Failed to create agent {agent_type} for {user_id}: {e}")
        raise ValueError(f"Agent creation failed: {e}")
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests**: Verify specific examples, edge cases, and integration points
- OnboardingAgentContext creation with valid data
- OnboardingAgentContext immutability (frozen=True)
- BaseOnboardingAgent constructor accepts new context type
- Orchestrator loads conversation history from database
- Each agent's stream_response uses _build_messages
- Empty conversation history edge case
- save_context continues to work

**Property-Based Tests**: Verify universal properties across all inputs
- Message structure invariant (Property 1)
- Conversation history inclusion with limiting (Property 2)
- History format conversion (Property 3)
- Orchestrator message loading with ordering and limiting (Property 4)
- Orchestrator format transformation (Property 5)
- History limiting preserves recency (Property 6)
- Message content preservation (Property 7)

### Property-Based Testing Configuration

**Library**: Hypothesis (Python property-based testing library)

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Tag format: `# Feature: onboarding-conversation-memory, Property N: [property text]`

**Example Property Test**:
```python
from hypothesis import given, strategies as st
import pytest

@given(
    user_message=st.text(min_size=1),
    history_size=st.integers(min_value=0, max_value=50)
)
@pytest.mark.property
async def test_property_1_message_structure_invariant(
    user_message: str,
    history_size: int,
    mock_agent_context
):
    """
    Feature: onboarding-conversation-memory, Property 1: Message Structure Invariant
    
    For any user message and agent context, when _build_messages() is called,
    the returned list should have a SystemMessage as the first element and a
    HumanMessage with the user's message content as the last element.
    """
    # Create context with random history
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg{i}"}
        for i in range(history_size)
    ]
    context = OnboardingAgentContext(
        user_id="test-user",
        conversation_history=history,
        agent_context={}
    )
    
    # Create agent and build messages
    agent = FitnessAssessmentAgent(mock_db, context)
    messages = agent._build_messages(user_message)
    
    # Verify structure
    assert len(messages) >= 2
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[-1], HumanMessage)
    assert messages[-1].content == user_message
```

### Unit Test Examples

**Test OnboardingAgentContext Creation**:
```python
def test_onboarding_agent_context_creation():
    """Test creating OnboardingAgentContext with valid data."""
    context = OnboardingAgentContext(
        user_id="test-user-123",
        conversation_history=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ],
        agent_context={"fitness_assessment": {"fitness_level": "beginner"}}
    )
    
    assert context.user_id == "test-user-123"
    assert len(context.conversation_history) == 2
    assert context.agent_context["fitness_assessment"]["fitness_level"] == "beginner"
    assert isinstance(context.loaded_at, datetime)
```

**Test Context Immutability**:
```python
def test_onboarding_agent_context_immutable():
    """Test that OnboardingAgentContext is immutable."""
    context = OnboardingAgentContext(
        user_id="test-user",
        conversation_history=[],
        agent_context={}
    )
    
    with pytest.raises(ValidationError):
        context.user_id = "new-user"
```

**Test Orchestrator Loads History**:
```python
async def test_orchestrator_loads_conversation_history(db_session, test_user):
    """Test that orchestrator loads conversation history from database."""
    # Create conversation messages
    for i in range(5):
        msg = ConversationMessage(
            user_id=test_user.id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}"
        )
        db_session.add(msg)
    await db_session.commit()
    
    # Create orchestrator and get agent
    orchestrator = OnboardingAgentOrchestrator(db_session)
    agent = await orchestrator.get_current_agent(test_user.id)
    
    # Verify conversation history loaded
    assert len(agent.context.conversation_history) == 5
    assert agent.context.conversation_history[0]["content"] == "Message 0"
```

**Test Agent Uses _build_messages**:
```python
async def test_fitness_assessment_agent_uses_build_messages(mock_db):
    """Test that FitnessAssessmentAgent uses _build_messages in stream_response."""
    context = OnboardingAgentContext(
        user_id="test-user",
        conversation_history=[
            {"role": "user", "content": "I'm a beginner"}
        ],
        agent_context={}
    )
    
    agent = FitnessAssessmentAgent(mock_db, context)
    
    # Mock _build_messages to verify it's called
    original_build = agent._build_messages
    call_count = 0
    
    def mock_build(message):
        nonlocal call_count
        call_count += 1
        return original_build(message)
    
    agent._build_messages = mock_build
    
    # Call stream_response
    chunks = []
    async for chunk in agent.stream_response("How many pushups can you do?"):
        chunks.append(chunk)
    
    # Verify _build_messages was called
    assert call_count == 1
```

### Test Coverage Goals

- Unit test coverage: 90%+ for new code
- Property test coverage: All 7 correctness properties implemented
- Integration test coverage: All 5 agents tested with new context
- All existing tests pass without modification

### Testing Execution

```bash
# Run all tests
poetry run pytest

# Run only property-based tests
poetry run pytest -m property

# Run only onboarding agent tests
poetry run pytest tests/test_onboarding_agents.py

# Run with coverage
poetry run pytest --cov=app/agents/onboarding --cov-report=html
```

## Implementation Notes

### Migration Path

1. **Phase 1**: Create OnboardingAgentContext
2. **Phase 2**: Update BaseOnboardingAgent to use OnboardingAgentContext
3. **Phase 3**: Update OnboardingAgentOrchestrator to create OnboardingAgentContext
4. **Phase 4**: Update all 5 agents to use _build_messages
5. **Phase 5**: Validation and testing

### Performance Considerations

**Database Query Optimization**:
- Limit conversation history query to 20 messages (prevents large result sets)
- Use index on (user_id, created_at) for fast queries
- Query executed once per agent creation (not per message)

**Memory Usage**:
- OnboardingAgentContext is immutable (can be safely shared)
- Conversation history limited to 20 messages in memory
- Each message ~100-500 bytes, total ~10-50KB per context

**Token Usage**:
- 15 message limit in _build_messages prevents token overflow
- Average message ~50-200 tokens
- Total history ~750-3000 tokens (well within limits)

### Backward Compatibility Strategy

**No Backward Compatibility Required**: This is a clean implementation following the official BaseAgent pattern. All onboarding agents will be updated to use the new context structure.

**Graceful Degradation**:
- If conversation history fails to load, agent works with empty history
- If context creation fails, log error and raise clear exception
- Existing agent tools continue to work without modification

## Dependencies

**Existing Dependencies** (no new dependencies required):
- `pydantic`: For OnboardingAgentContext model
- `sqlalchemy`: For database queries
- `langchain-core`: For message types (SystemMessage, HumanMessage, AIMessage)

**Testing Dependencies**:
- `hypothesis`: For property-based testing (already in dev dependencies)
- `pytest`: For unit tests (already in dev dependencies)
- `pytest-asyncio`: For async tests (already in dev dependencies)

## Rollout Plan

### Phase 1: Foundation
- Create OnboardingAgentContext in context.py
- Add _build_messages to BaseOnboardingAgent
- Update BaseOnboardingAgent constructor to accept OnboardingAgentContext
- Write unit tests for new components

### Phase 2: Orchestrator Update
- Update OnboardingAgentOrchestrator to load conversation history
- Update OnboardingAgentOrchestrator to create OnboardingAgentContext
- Write integration tests for orchestrator

### Phase 3: Agent Updates
- Update FitnessAssessmentAgent to use _build_messages
- Update GoalSettingAgent to use _build_messages
- Update WorkoutPlanningAgent to use _build_messages
- Update DietPlanningAgent to use _build_messages
- Update SchedulingAgent to use _build_messages
- Write property-based tests for each agent

### Phase 4: Validation
- Run full test suite
- Manual testing of onboarding flow
- Verify conversation memory works end-to-end
- Performance testing with large conversation histories

### Phase 5: Cleanup
- Update documentation
- Add docstrings to new methods
