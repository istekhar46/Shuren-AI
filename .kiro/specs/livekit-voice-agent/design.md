# Design Document

## Overview

The LiveKit Voice Agent system enables real-time voice interactions between users and AI fitness coaches through LiveKit's infrastructure. The system integrates Speech-to-Text (Deepgram), Text-to-Speech (Cartesia), and the existing LangChain agent orchestrator to provide natural, low-latency voice coaching experiences.

The voice agent architecture follows a hybrid approach where quick queries (workout/meal lookups, logging) are handled by function tools with cached data, while complex reasoning queries are delegated to the LangChain orchestrator and specialized agents. This design achieves the <2 second latency requirement for voice responses.

### Key Design Principles

1. **Pre-loading for Performance**: User context and orchestrator are loaded before connecting to LiveKit rooms to minimize latency
2. **Function Tools for Speed**: Quick data retrieval uses cached context without database queries
3. **Async Logging**: Workout logs are queued and persisted asynchronously to avoid blocking voice interactions
4. **Specialist Delegation**: Complex queries route to LangChain orchestrator for expert handling
5. **Multi-Provider Support**: Configurable LLM provider (OpenAI, Anthropic, Google) for function calling

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Device                              │
│                    (Mobile/Web Client)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ WebRTC
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      LiveKit Server                              │
│                   (Room Management)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │ Room Events
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Voice Agent Worker                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FitnessVoiceAgent                           │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Pre-loaded Context:                               │ │  │
│  │  │  - User Profile                                    │ │  │
│  │  │  - Workout Plan                                    │ │  │
│  │  │  - Meal Plan                                       │ │  │
│  │  │  - Agent Orchestrator                              │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Function Tools:                                   │ │  │
│  │  │  - get_todays_workout()                            │ │  │
│  │  │  - get_todays_meals()                              │ │  │
│  │  │  - log_workout_set()                               │ │  │
│  │  │  - ask_specialist_agent()                          │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Background Log Worker                             │ │  │
│  │  │  (Async Queue Processing)                          │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Agent Session                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │ Deepgram │  │ Cartesia │  │ GPT-4o/  │              │  │
│  │  │   STT    │  │   TTS    │  │ Claude/  │              │  │
│  │  │          │  │          │  │ Gemini   │              │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                  LangChain Orchestrator                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Specialized Agents:                                     │  │
│  │  - Workout Planner                                       │  │
│  │  - Diet Planner                                          │  │
│  │  - Supplement Guide                                      │  │
│  │  - Tracker                                               │  │
│  │  - Scheduler                                             │  │
│  │  - General Assistant                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL + Redis                            │
│              (User Data + Workout Logs)                          │
└─────────────────────────────────────────────────────────────────┘
```

### Interaction Flow

**Quick Query Flow (Function Tools)**:
1. User speaks → LiveKit Server → Voice Agent Worker
2. Deepgram STT converts speech to text
3. GPT-4o/Claude/Gemini determines function tool to call
4. Function tool retrieves data from cached context (no DB query)
5. Response generated immediately
6. Cartesia TTS converts response to speech
7. Audio streamed back to user

**Complex Query Flow (Specialist Delegation)**:
1. User speaks → LiveKit Server → Voice Agent Worker
2. Deepgram STT converts speech to text
3. GPT-4o/Claude/Gemini calls ask_specialist_agent tool
4. Tool routes query to LangChain orchestrator
5. Orchestrator classifies and routes to specialized agent
6. Specialized agent processes with full context and tools
7. Response returned to voice agent
8. Cartesia TTS converts response to speech
9. Audio streamed back to user

**Logging Flow (Async)**:
1. User logs workout set via voice
2. log_workout_set tool queues entry
3. Immediate confirmation returned to user
4. Background log worker processes queue
5. Entry persisted to database asynchronously

## Components and Interfaces

### 1. FitnessVoiceAgent Class

The core voice agent class that manages voice interactions and delegates to LangChain.

**Responsibilities**:
- Maintain pre-loaded user context and orchestrator
- Provide function tools for quick queries
- Delegate complex queries to LangChain orchestrator
- Manage background logging worker
- Generate base instructions for LLM

**Interface**:
```python
class FitnessVoiceAgent(Agent):
    def __init__(self, user_id: str, agent_type: str)
    async def initialize_orchestrator() -> None
    async def start_log_worker() -> None
    async def cleanup() -> None
    
    # Function Tools
    @function_tool()
    async def get_todays_workout(context: RunContext) -> str
    
    @function_tool()
    async def get_todays_meals(context: RunContext) -> str
    
    @function_tool()
    async def log_workout_set(
        context: RunContext,
        exercise: str,
        reps: int,
        weight: float
    ) -> str
    
    @function_tool()
    async def ask_specialist_agent(
        context: RunContext,
        query: str,
        specialist: str
    ) -> str
    
    # Internal Methods
    async def _log_worker() -> None
    def _get_base_instructions(agent_type: str) -> str
```

**Attributes**:
- `user_id`: User's unique identifier
- `agent_type`: Type of agent (workout, diet, general, etc.)
- `orchestrator`: LangChain AgentOrchestrator instance
- `user_context`: Pre-loaded AgentContext with user data
- `_log_queue`: Async queue for workout logs
- `_log_worker_task`: Background task for log processing

### 2. Agent Session Configuration

The LiveKit agent session that connects STT, TTS, and LLM.

**Components**:
- **STT (Deepgram)**: Speech-to-Text with nova-2-general model
- **TTS (Cartesia)**: Text-to-Speech with sonic-english model
- **LLM (Configurable)**: OpenAI GPT-4o, Anthropic Claude, or Google Gemini for function calling

**Configuration**:
```python
session = AgentSession(
    stt=deepgram.STT(
        model="nova-2-general",
        language="en-US"
    ),
    tts=cartesia.TTS(
        model="sonic-english",
        voice_id="fitness-coach-male",
        sample_rate=24000,
        speed=1.1
    ),
    llm=_get_configured_llm()  # Based on LLM_PROVIDER setting
)
```

### 3. Agent Worker Entrypoint

The main entrypoint function that handles room connections.

**Responsibilities**:
- Extract user metadata from room
- Create FitnessVoiceAgent instance
- Pre-load orchestrator and context
- Start background log worker
- Connect to LiveKit room
- Start agent session
- Handle session completion and cleanup

**Interface**:
```python
async def entrypoint(ctx: JobContext) -> None
```

**Flow**:
1. Extract user_id and agent_type from room metadata
2. Create FitnessVoiceAgent instance
3. Call `initialize_orchestrator()` to pre-load context
4. Call `start_log_worker()` to start background logging
5. Connect to LiveKit room
6. Create and start AgentSession
7. Generate initial greeting
8. Wait for session completion
9. Call `cleanup()` to release resources

### 4. Background Log Worker

An async task that processes workout logs from a queue.

**Responsibilities**:
- Monitor log queue for new entries
- Persist entries to database asynchronously
- Handle errors gracefully without blocking
- Support graceful shutdown

**Implementation**:
```python
async def _log_worker(self):
    while True:
        try:
            log_entry = await self._log_queue.get()
            
            async with async_session_maker() as db:
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
```

### 5. Function Tools

Quick data retrieval and action tools exposed to the LLM.

#### get_todays_workout

Returns today's workout from cached context.

**Input**: None (uses context)
**Output**: String describing today's workout and exercises
**Latency**: <50ms (no database query)

#### get_todays_meals

Returns today's meal plan from cached context.

**Input**: None (uses context)
**Output**: JSON string with meal plan
**Latency**: <50ms (no database query)

#### log_workout_set

Queues a workout set for async logging.

**Input**:
- `exercise`: Exercise name (string)
- `reps`: Number of repetitions (int)
- `weight`: Weight used (float)

**Output**: Confirmation message (string)
**Latency**: <10ms (queue operation only)

#### ask_specialist_agent

Delegates complex queries to LangChain orchestrator.

**Input**:
- `query`: User's question (string)
- `specialist`: Agent type (workout, diet, supplement)

**Output**: Response from specialized agent (string)
**Latency**: <2s (includes LLM call and database queries)

### 6. Configuration Management

Voice service configuration in `app/core/config.py`.

**New Settings**:
```python
class Settings(BaseSettings):
    # LiveKit Voice Services
    DEEPGRAM_API_KEY: str
    CARTESIA_API_KEY: str
    
    # Voice Optimization
    VOICE_CONTEXT_CACHE_TTL: int = 3600
    VOICE_MAX_RESPONSE_TOKENS: int = 150
    
    # LLM Provider for Voice
    VOICE_LLM_PROVIDER: str = "openai"  # openai, anthropic, google
```

### 7. LLM Provider Selection

The voice agent supports multiple LLM providers for function calling.

**Provider Configuration**:
```python
def _get_configured_llm():
    """Get LLM based on VOICE_LLM_PROVIDER setting"""
    provider = settings.VOICE_LLM_PROVIDER
    
    if provider == "openai":
        return openai.LLM(
            model="gpt-4o",
            temperature=0.7
        )
    elif provider == "anthropic":
        # Note: LiveKit Agents SDK may not have native Anthropic plugin
        # May need to use OpenAI-compatible endpoint or custom integration
        return openai.LLM(
            model="claude-3-5-sonnet-20241022",
            base_url="https://api.anthropic.com/v1",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.7
        )
    elif provider == "google":
        # Note: LiveKit Agents SDK may not have native Google plugin
        # May need to use OpenAI-compatible endpoint or custom integration
        return openai.LLM(
            model="gemini-1.5-pro",
            base_url="https://generativelanguage.googleapis.com/v1beta",
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.7
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
```

**Note**: The LiveKit Agents SDK primarily supports OpenAI's function calling format. For Anthropic and Google providers, we may need to:
1. Use OpenAI-compatible endpoints if available
2. Implement custom LLM adapters
3. Default to OpenAI for voice interactions while using other providers for text

## Data Models

### WorkoutLog Model

Stores workout set logs from voice interactions.

**Schema**:
```python
class WorkoutLog(Base):
    __tablename__ = "workout_logs"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exercise: str = Column(String(255), nullable=False)
    reps: int = Column(Integer, nullable=False)
    weight_kg: float = Column(Float, nullable=False)
    logged_at: datetime = Column(DateTime(timezone=True), nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
```

**Indexes**:
- `user_id` (for querying user's logs)
- `logged_at` (for time-based queries)

### Room Metadata Format

LiveKit room metadata contains user information for agent initialization.

**Format**:
```json
{
  "user_id": "uuid-string",
  "agent_type": "workout|diet|supplement|general",
  "session_type": "voice",
  "created_at": "2026-02-02T10:30:00Z"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified the following testable properties and examples. Here's the reflection to eliminate redundancy:

**Redundancy Analysis**:
1. Properties 4.2, 4.3, 4.4 (context loading includes workout, meal, preferences) can be combined into a single comprehensive property about complete context loading
2. Properties 5.2 and 5.4 (tools use cached data) can be combined into a single property about all quick tools using cached data
3. Properties 6.3 and 6.4 (queuing and immediate return) are related but test different aspects - keep both
4. Properties 7.3 and 7.4 (queue retrieval and database write) can be combined into a single property about log persistence
5. Properties 8.3 and 8.5 (routing to orchestrator and returning response) can be combined into a single property about delegation flow
6. Properties 9.1 and 9.2 (extracting user_id and agent_type) can be combined into a single property about metadata extraction
7. Properties 19.1, 19.5, 19.6 (error logging, session logging, tool logging) can be combined into a single property about comprehensive logging
8. Property 3.5 and 20.2 (instructions vary by agent type) are duplicates - keep one

**Final Property Set** (after eliminating redundancy):
- Property 1: Context loading completeness (combines 4.2, 4.3, 4.4)
- Property 2: Quick tools use cached data (combines 5.2, 5.4)
- Property 3: Workout logging queues immediately (6.3)
- Property 4: Workout logging returns immediately (6.4)
- Property 5: Queued logs are persisted (combines 7.3, 7.4)
- Property 6: Log worker handles errors gracefully (7.6)
- Property 7: Specialist delegation flow (combines 8.3, 8.5)
- Property 8: All specialist types supported (8.4)
- Property 9: Orchestrator errors return friendly messages (8.6, 19.3)
- Property 10: Room metadata extraction (combines 9.1, 9.2)
- Property 11: Greetings vary by agent type (9.7)
- Property 12: LLM provider selection works for all providers (12.1)
- Property 13: Function tools are callable by LLM (12.7)
- Property 14: Instructions vary by agent type (combines 3.5, 20.2)
- Property 15: Comprehensive logging (combines 19.1, 19.4, 19.5, 19.6)

### Correctness Properties

Property 1: Context Loading Completeness
*For any* user with a profile, when the voice agent initializes, the loaded context should include the user's workout plan, meal plan, and preferences
**Validates: Requirements 4.2, 4.3, 4.4**

Property 2: Quick Tools Use Cached Data
*For any* user context, when get_todays_workout or get_todays_meals is called, the response should come from the cached context without making database queries
**Validates: Requirements 5.2, 5.4**

Property 3: Workout Logging Queues Immediately
*For any* workout set (exercise, reps, weight), when log_workout_set is called, the entry should be added to the async queue
**Validates: Requirements 6.3**

Property 4: Workout Logging Returns Immediately
*For any* workout set, when log_workout_set is called, a confirmation message should be returned without waiting for database persistence
**Validates: Requirements 6.4**

Property 5: Queued Logs Are Persisted
*For any* workout log entry in the queue, the log worker should retrieve it and persist it to the database
**Validates: Requirements 7.3, 7.4**

Property 6: Log Worker Handles Errors Gracefully
*For any* error during log processing, the log worker should log the error and continue processing subsequent entries
**Validates: Requirements 7.6**

Property 7: Specialist Delegation Flow
*For any* query and specialist type, when ask_specialist_agent is called, the query should be routed to the orchestrator and the orchestrator's response should be returned
**Validates: Requirements 8.3, 8.5**

Property 8: All Specialist Types Supported
*For any* specialist type (workout, diet, supplement), the ask_specialist_agent tool should successfully route to that specialist
**Validates: Requirements 8.4**

Property 9: Orchestrator Errors Return Friendly Messages
*For any* orchestrator failure, the system should return a user-friendly error message asking the user to rephrase
**Validates: Requirements 8.6, 19.3**

Property 10: Room Metadata Extraction
*For any* room with valid metadata, the system should successfully extract both user_id and agent_type
**Validates: Requirements 9.1, 9.2**

Property 11: Greetings Vary By Agent Type
*For any* agent type, the initial greeting should be appropriate to that agent type
**Validates: Requirements 9.7**

Property 12: LLM Provider Selection
*For any* supported LLM provider (openai, anthropic, google), the system should successfully configure and initialize that provider
**Validates: Requirements 12.1**

Property 13: Function Tools Are Callable By LLM
*For any* registered function tool, when the LLM calls it, the system should execute the tool and return results
**Validates: Requirements 12.7**

Property 14: Instructions Vary By Agent Type
*For any* agent type, the base instructions should be tailored to that agent type's domain
**Validates: Requirements 3.5, 20.2**

Property 15: Comprehensive Logging
*For any* agent session, error, or tool invocation, the system should log the event with appropriate context
**Validates: Requirements 19.1, 19.4, 19.5, 19.6**

## Error Handling

### Error Categories

**1. Initialization Errors**
- Missing user_id in room metadata → Log error, abort connection
- User profile not found → Log error, abort connection
- LLM provider configuration invalid → Raise ValueError with clear message
- Database connection failure → Log error, retry with exponential backoff

**2. Runtime Errors**
- Function tool execution failure → Log error, return error message to user
- Orchestrator delegation failure → Return friendly "please rephrase" message
- STT/TTS service failure → Log error, attempt reconnection
- Database write failure in log worker → Log error, continue processing queue

**3. Cleanup Errors**
- Log worker cancellation timeout → Force terminate after 5 seconds
- Database session cleanup failure → Log warning, continue shutdown

### Error Handling Patterns

**Graceful Degradation**:
- If orchestrator fails, voice agent can still handle quick queries via function tools
- If log worker fails, user still receives confirmation (logs queued for retry)
- If one specialist agent fails, other specialists remain available

**User-Friendly Messages**:
- Technical errors are logged but not exposed to users
- Users receive conversational error messages: "I'm having trouble with that. Can you rephrase?"
- System maintains conversational tone even during errors

**Retry Strategies**:
- Database operations: 3 retries with exponential backoff
- LLM calls: 2 retries with 1-second delay
- Log worker: Continuous processing with error logging (no retry limit)

## Testing Strategy

### Dual Testing Approach

The voice agent requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of function tool calls
- Configuration loading and validation
- Initialization sequences
- Cleanup procedures
- Error handling for specific scenarios
- Integration with LiveKit SDK

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Context loading completeness across all users
- Tool behavior across all valid inputs
- Delegation flow across all query types
- Error handling across all error types
- Logging behavior across all events

### Property-Based Testing Configuration

All property-based tests should:
- Run minimum 100 iterations (due to randomization)
- Reference the design document property number
- Use tag format: **Feature: livekit-voice-agent, Property {number}: {property_text}**

Example property test:
```python
@given(
    user_id=st.uuids(),
    agent_type=st.sampled_from(["workout", "diet", "supplement", "general"])
)
async def test_property_14_instructions_vary_by_agent_type(user_id, agent_type):
    """
    Feature: livekit-voice-agent, Property 14: Instructions vary by agent type
    
    For any agent type, the base instructions should be tailored to that 
    agent type's domain.
    """
    agent = FitnessVoiceAgent(user_id=str(user_id), agent_type=agent_type)
    instructions = agent._get_base_instructions(agent_type)
    
    # Verify instructions mention the agent type
    assert agent_type in instructions.lower()
    
    # Verify instructions are non-empty
    assert len(instructions) > 50
```

### Test Organization

```
backend/tests/
├── test_voice_agent_unit.py           # Unit tests for voice agent
├── test_voice_agent_properties.py     # Property-based tests
├── test_voice_agent_integration.py    # Integration tests with LiveKit
├── test_voice_agent_tools.py          # Function tool tests
└── test_voice_agent_logging.py        # Log worker tests
```

### Integration Testing

Integration tests should verify:
1. Voice agent can connect to LiveKit rooms
2. STT/TTS services are properly configured
3. Function tools are callable from LLM
4. Orchestrator delegation works end-to-end
5. Log worker persists data to database
6. Cleanup releases all resources

### Performance Testing

Performance tests should verify:
- Function tool responses < 100ms
- Specialist delegation < 2s
- Overall voice response < 2s (95th percentile)
- Log worker processes entries within 1s

### Mocking Strategy

**Mock External Services**:
- LiveKit SDK (room connections, sessions)
- Deepgram STT (speech transcription)
- Cartesia TTS (speech synthesis)
- LLM providers (function calling)

**Use Real Services**:
- PostgreSQL database (with test database)
- Redis cache (with test instance)
- Agent orchestrator (integration tests)
- Context loader (integration tests)

### Test Fixtures

Required fixtures:
- `test_user`: User with complete profile
- `test_context`: Pre-loaded AgentContext
- `mock_livekit_room`: Mocked LiveKit room
- `mock_stt`: Mocked Deepgram STT
- `mock_tts`: Mocked Cartesia TTS
- `mock_llm`: Mocked LLM for function calling
- `voice_agent`: FitnessVoiceAgent instance
- `log_worker_queue`: Async queue for testing

## Deployment Considerations

### Container Configuration

The voice agent runs as a separate container from the main FastAPI application:

**Dockerfile.agent**:
- Base: Python 3.11-slim
- Dependencies: requirements-agent.txt
- Entrypoint: voice_agent_worker.py

**Resource Requirements**:
- CPU: 1-2 cores per worker
- Memory: 512MB-1GB per worker
- Network: Low latency connection to LiveKit server

### Scaling Strategy

**Horizontal Scaling**:
- Run multiple agent worker replicas
- Each worker handles multiple concurrent sessions
- LiveKit automatically load balances across workers

**Configuration**:
```yaml
deploy:
  replicas: 2  # Start with 2 workers
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '1'
      memory: 512M
```

### Environment Variables

Required environment variables:
```bash
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxx
LIVEKIT_API_SECRET=secretxxxx

# Voice Services
DEEPGRAM_API_KEY=xxx
CARTESIA_API_KEY=xxx

# LLM Provider
VOICE_LLM_PROVIDER=openai  # or anthropic, google
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
GOOGLE_API_KEY=xxx

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/fitness
REDIS_URL=redis://redis:6379

# Voice Optimization
VOICE_CONTEXT_CACHE_TTL=3600
VOICE_MAX_RESPONSE_TOKENS=150
```

### Monitoring and Observability

**Metrics to Track**:
- Voice response latency (p50, p95, p99)
- Function tool call latency
- Specialist delegation latency
- Log worker queue depth
- Error rates by type
- Active session count

**Logging**:
- All agent sessions (start/end)
- All function tool invocations
- All errors with context
- Performance metrics

**Health Checks**:
- Worker process is running
- Database connection is healthy
- Redis connection is healthy
- LLM provider is reachable

### Production Readiness Checklist

- [ ] All environment variables configured
- [ ] Database migrations applied
- [ ] Redis cache available
- [ ] LiveKit server accessible
- [ ] Voice service API keys valid
- [ ] LLM provider API keys valid
- [ ] Container builds successfully
- [ ] Integration tests pass
- [ ] Performance tests meet latency requirements
- [ ] Monitoring and logging configured
- [ ] Error handling tested
- [ ] Cleanup procedures verified
- [ ] Multiple worker replicas deployed
- [ ] Health checks passing

## Security Considerations

### API Key Management

- All API keys stored in environment variables (never in code)
- API keys loaded via Pydantic Settings with validation
- API keys never logged or exposed in error messages
- Use secrets management service in production (AWS Secrets Manager, etc.)

### User Data Protection

- User context loaded only for authenticated users
- Room metadata validated before processing
- User_id validated as UUID format
- Database queries use parameterized statements
- No PII logged in error messages

### Network Security

- LiveKit connections use WSS (WebSocket Secure)
- All external API calls use HTTPS
- Database connections use SSL/TLS
- Redis connections use TLS (if configured)

### Input Validation

- Room metadata validated before use
- Function tool parameters validated
- User queries sanitized before LLM processing
- Database inputs validated by SQLAlchemy models

## Future Enhancements

### Phase 1 Enhancements (Post-MVP)

1. **Voice Activity Detection**: Detect when user stops speaking for faster responses
2. **Interrupt Handling**: Allow users to interrupt agent mid-response
3. **Multi-Language Support**: Support languages beyond English
4. **Voice Customization**: Allow users to select voice characteristics
5. **Emotion Detection**: Detect user emotion from voice tone

### Phase 2 Enhancements (Advanced Features)

1. **Streaming Responses**: Stream TTS audio as LLM generates text
2. **Context Persistence**: Save voice session context for follow-up sessions
3. **Voice Commands**: Support specific voice commands (e.g., "skip", "repeat")
4. **Background Noise Filtering**: Improve STT accuracy in noisy environments
5. **Multi-User Sessions**: Support group coaching sessions

### Performance Optimizations

1. **Context Caching**: Cache user context in Redis for faster loading
2. **LLM Response Caching**: Cache common responses to reduce LLM calls
3. **Parallel Tool Execution**: Execute multiple function tools in parallel
4. **Predictive Loading**: Pre-load likely next queries based on context
5. **Edge Deployment**: Deploy workers closer to users for lower latency

## References

- [LiveKit Agents SDK Documentation](https://docs.livekit.io/agents/)
- [Deepgram API Documentation](https://developers.deepgram.com/)
- [Cartesia API Documentation](https://docs.cartesia.ai/)
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
