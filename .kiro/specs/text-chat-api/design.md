# Design Document: Text Chat API Integration

## Overview

The Text Chat API Integration provides REST API endpoints for text-based interactions with the Shuren AI fitness assistant. This feature enables users to communicate with specialized AI agents through both synchronous and streaming interfaces, with full conversation history persistence.

This design builds upon the existing LangChain Foundation (Sub-Doc 1) and Specialized Agents (Sub-Doc 2) infrastructure, adding the HTTP interface layer that allows client applications to interact with the agent orchestration system.

### Key Design Goals

1. **Seamless Integration**: Leverage existing AgentOrchestrator and specialized agents without modification
2. **Performance**: Meet latency targets (< 3s for synchronous, < 1s for first streaming chunk)
3. **Persistence**: Store all conversations for context continuity and user review
4. **Flexibility**: Support both automatic agent routing and explicit agent selection
5. **Real-time Experience**: Provide streaming responses for immediate user feedback

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Application                      │
│                  (iOS/Android/Web Frontend)                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/HTTPS
                         │ JWT Authentication
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Chat Endpoints (chat.py)                    │  │
│  │  • POST /api/v1/chat/chat (synchronous)              │  │
│  │  • POST /api/v1/chat/stream (SSE streaming)          │  │
│  │  • GET /api/v1/chat/history                          │  │
│  │  • DELETE /api/v1/chat/history                       │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │         Agent Orchestrator Service                    │  │
│  │  • Query classification                               │  │
│  │  • Agent routing                                      │  │
│  │  • Context loading                                    │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │         Specialized Agents (6 agents)                 │  │
│  │  • Workout Planner                                    │  │
│  │  • Diet Planner                                       │  │
│  │  • Supplement Guide                                   │  │
│  │  • Tracker                                            │  │
│  │  • Scheduler                                          │  │
│  │  • General Assistant                                  │  │
│  └──────────────────────┬───────────────────────────────┘  │
└─────────────────────────┼────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                        │
│  • conversation_messages (new table)                         │
│  • users, user_profiles, preferences (existing)              │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

#### Synchronous Chat Flow

1. Client sends POST request to `/api/v1/chat/chat` with JWT token and message
2. FastAPI validates JWT and extracts user ID
3. Chat endpoint loads user context via `context_loader.load_agent_context()`
4. Chat endpoint calls `AgentOrchestrator.route_query()` with user context
5. AgentOrchestrator classifies query (if agent_type not specified)
6. AgentOrchestrator routes to appropriate specialized agent
7. Agent processes query using LLM and returns AgentResponse
8. Chat endpoint saves user message and assistant response to database
9. Chat endpoint returns response to client

#### Streaming Chat Flow

1. Client sends POST request to `/api/v1/chat/stream` with JWT token and message
2. FastAPI validates JWT and extracts user ID
3. Chat endpoint establishes Server-Sent Events (SSE) connection
4. Chat endpoint loads user context and gets appropriate agent
5. Agent streams response chunks via `stream_response()` method
6. Each chunk is sent to client as SSE data event
7. After streaming completes, full conversation is saved to database
8. Final SSE event sent with "done: true" and agent_type

## Components and Interfaces

### 1. Database Model: ConversationMessage

**Purpose**: Persist all chat messages for conversation history and context continuity.

**Schema**:
```python
class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    
    id: UUID                    # Primary key
    user_id: UUID               # Foreign key to users table
    role: str                   # "user" or "assistant"
    content: Text               # Message content
    agent_type: str             # Which agent handled this (nullable for user messages)
    created_at: DateTime        # Timestamp
    
    # Indexes
    idx_user_created: (user_id, created_at)  # For efficient history queries
```

**Design Decisions**:
- Simple flat structure for fast queries
- Composite index on (user_id, created_at) for efficient history retrieval
- No foreign key to agents table (agents are code-level, not database entities)
- No conversation_id grouping (all messages for a user form one continuous conversation)
- Text field for content (supports long messages and responses)

### 2. Pydantic Schemas

**ChatRequest**:
```python
class ChatRequest(BaseModel):
    message: str                    # 1-2000 characters
    agent_type: Optional[str]       # Optional explicit routing
```

**ChatResponse**:
```python
class ChatResponse(BaseModel):
    response: str                   # Agent's response text
    agent_type: str                 # Which agent handled this
    conversation_id: str            # User ID (for client reference)
    tools_used: list                # Tools/functions called by agent
```

**ChatHistoryResponse**:
```python
class ChatHistoryResponse(BaseModel):
    messages: list                  # List of message dicts
    total: int                      # Total message count
```

**Message Dict Format**:
```python
{
    "role": "user" | "assistant",
    "content": str,
    "agent_type": str,
    "created_at": ISO8601 timestamp
}
```

### 3. Chat Endpoints

**POST /api/v1/chat/chat** (Synchronous)

- **Authentication**: Required (JWT Bearer token)
- **Request Body**: ChatRequest
- **Response**: ChatResponse (200 OK)
- **Error Responses**:
  - 401: Unauthorized (invalid/missing token)
  - 422: Validation Error (invalid message format)
  - 400: Bad Request (invalid agent_type)
  - 500: Internal Server Error (processing failure)

**POST /api/v1/chat/stream** (Streaming)

- **Authentication**: Required (JWT Bearer token)
- **Request Body**: ChatRequest
- **Response**: Server-Sent Events stream
- **Event Format**:
  ```
  data: {"chunk": "response text"}
  
  data: {"done": true, "agent_type": "workout"}
  
  ```
- **Error Responses**:
  - 401: Unauthorized
  - 422: Validation Error
  - Error events in stream: `data: {"error": "message"}`

**GET /api/v1/chat/history**

- **Authentication**: Required (JWT Bearer token)
- **Query Parameters**: 
  - `limit` (optional, default 50, max 200)
- **Response**: ChatHistoryResponse (200 OK)
- **Error Responses**:
  - 401: Unauthorized

**DELETE /api/v1/chat/history**

- **Authentication**: Required (JWT Bearer token)
- **Response**: `{"status": "cleared"}` (200 OK)
- **Error Responses**:
  - 401: Unauthorized

### 4. Context Loader Updates

**Updated Function**: `_load_conversation_history()`

```python
async def _load_conversation_history(
    db: AsyncSession,
    user_id: str,
    limit: int = 10
) -> list:
    """Load recent conversation history from database"""
    
    # Query conversation_messages table
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.user_id == user_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    # Reverse to chronological order and format
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "agent_type": msg.agent_type
        }
        for msg in reversed(messages)
    ]
```

**Integration**: This function is already called by `load_agent_context()`, so no changes needed to the context loader interface.

### 5. Agent Orchestrator Integration

The chat endpoints use the existing `AgentOrchestrator` without modification:

```python
# Initialize orchestrator
orchestrator = AgentOrchestrator(db_session=db, mode="text")

# Route query (with optional explicit agent type)
response = await orchestrator.route_query(
    user_id=str(current_user.id),
    query=request.message,
    agent_type=agent_type,  # None for automatic classification
    voice_mode=False
)
```

**Key Points**:
- Mode is always "text" (not "voice") for chat API
- AgentOrchestrator handles classification if agent_type is None
- Returns AgentResponse with content, agent_type, and tools_used

### 6. Streaming Implementation

**Approach**: Use FastAPI's `StreamingResponse` with Server-Sent Events (SSE)

```python
async def generate():
    """Async generator for SSE streaming"""
    try:
        # Get agent and stream response
        async for chunk in agent.stream_response(query):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Send completion event
        yield f"data: {json.dumps({'done': True, 'agent_type': agent_type.value})}\n\n"
        
        # Save conversation after streaming
        # ... save to database ...
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

return StreamingResponse(generate(), media_type="text/event-stream")
```

**Design Decisions**:
- SSE chosen over WebSockets for simplicity (unidirectional, HTTP-based)
- Each chunk sent as separate data event
- Final event signals completion with agent_type
- Conversation saved after streaming completes (not during)
- Error events sent in-stream rather than closing connection

## Data Models

### Database Schema

**New Table: conversation_messages**

```sql
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    agent_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_created ON conversation_messages(user_id, created_at);
```

**Rationale**:
- UUID primary key for consistency with other tables
- Foreign key to users ensures referential integrity
- CHECK constraint on role ensures data validity
- Composite index optimizes history queries (user_id + created_at DESC)
- agent_type nullable (user messages don't have agent_type)
- No soft delete (deleted_at) - history deletion is hard delete

### Message Flow Data

**User Message Storage**:
```python
user_msg = ConversationMessage(
    user_id=current_user.id,
    role="user",
    content=request.message,
    agent_type=None  # Set after agent processes
)
```

**Assistant Message Storage**:
```python
assistant_msg = ConversationMessage(
    user_id=current_user.id,
    role="assistant",
    content=response.content,
    agent_type=response.agent_type
)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Message Persistence Completeness

*For any* successful chat interaction (synchronous or streaming), both the user message and assistant response SHALL be persisted to the database with correct role ("user" or "assistant"), content matching the input/output, agent_type populated for assistant messages, timestamp present, and user_id matching the authenticated user.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 3.5**

### Property 2: Authentication Enforcement

*For any* request to any chat endpoint (chat, stream, history, delete) without a valid JWT token, the system SHALL return a 401 Unauthorized error and SHALL NOT process the request or access the database.

**Validates: Requirements 2.6, 3.6, 4.6, 5.4, 8.1, 8.2**

### Property 3: Agent Routing Consistency

*For any* chat request with an explicit agent_type parameter from the valid set (workout, diet, supplement, tracker, scheduler, general), the system SHALL route to that specific agent and the returned agent_type SHALL match the requested agent_type.

**Validates: Requirements 2.4, 6.1, 6.2**

### Property 4: Automatic Classification

*For any* chat request without an explicit agent_type parameter, the system SHALL use the Agent_Orchestrator to classify the query and route to an appropriate agent, returning a valid agent_type in the response.

**Validates: Requirements 2.3, 6.4**

### Property 5: Conversation History Ordering and Completeness

*For any* user's conversation history retrieval, messages SHALL be returned in chronological order (oldest to newest) with accurate timestamps, each message containing role, content, agent_type, and created_at fields, and the total count SHALL match the actual number of messages for that user.

**Validates: Requirements 1.6, 4.1, 4.2, 4.3, 4.4**

### Property 6: User Data Isolation

*For any* authenticated user, all conversation history operations (retrieve, delete) SHALL only access messages belonging to that user (user_id from JWT token) and SHALL NOT access or modify other users' messages.

**Validates: Requirements 4.5, 5.1, 5.3, 8.3, 8.4**

### Property 7: Streaming Response Format

*For any* streaming chat request, the response SHALL use Server-Sent Events format, deliver the first chunk within 1 second, stream each chunk as a JSON data event, and send a final event with "done: true" and the agent_type upon completion.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 8: Context Loading Integration

*For any* chat request (synchronous or streaming), the system SHALL load complete user context including fitness level, goals, energy level, workout plan, meal plan, and conversation history before agent processing begins, and SHALL pass this context to the Agent_Orchestrator.

**Validates: Requirements 2.2, 7.1, 7.2, 7.4**

### Property 9: Response Structure Completeness

*For any* successful synchronous chat request, the response SHALL contain response content, agent_type, conversation_id, and tools_used fields with appropriate values.

**Validates: Requirements 2.5**

### Property 10: Validation Error Handling

*For any* chat request with invalid input (empty message, message > 2000 characters, invalid agent_type), the system SHALL return appropriate error status (422 for validation, 400 for bad request) with descriptive message and SHALL NOT persist any messages to the database.

**Validates: Requirements 2.7, 6.3**

### Property 11: Performance Targets

*For any* synchronous chat request with a valid message, the system SHALL return a complete response within 3 seconds at the 95th percentile, and for streaming requests, SHALL deliver the first chunk within 1 second.

**Validates: Requirements 2.1, 3.2**

### Property 12: Deletion Completeness

*For any* authenticated user's delete history request, the system SHALL delete all conversation messages belonging to that user, return a success status, and subsequent history queries SHALL return zero messages.

**Validates: Requirements 5.1, 5.2**

### Property 13: Logging Completeness

*For any* chat interaction, the system SHALL log successful requests at INFO level with user_id, agent_type, and response_time, and SHALL log errors at ERROR level with user_id, query excerpt, and error details without exposing internal implementation details in the error response.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

## Error Handling

### Error Categories

**1. Authentication Errors (401)**
- Missing JWT token
- Invalid JWT token (expired, malformed, invalid signature)
- User not found or deleted

**Handling**: Return 401 with generic message, log at WARNING level

**2. Validation Errors (422)**
- Empty message
- Message exceeds 2000 characters
- Missing required fields

**Handling**: Return 422 with field-specific errors (FastAPI automatic), no logging needed

**3. Bad Request Errors (400)**
- Invalid agent_type value

**Handling**: Return 400 with descriptive message, log at INFO level

**4. Processing Errors (500)**
- Agent processing failure
- Database connection failure
- LLM API failure
- Context loading failure

**Handling**: Return 500 with generic message, log at ERROR level with full context

### Error Response Format

```python
{
    "detail": "Human-readable error message"
}
```

For validation errors (422):
```python
{
    "detail": [
        {
            "loc": ["body", "message"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

### Logging Strategy

**INFO Level**:
- Successful chat interactions (user_id, agent_type, response_time)
- Invalid agent_type requests

**WARNING Level**:
- Authentication failures
- Rate limiting (future)

**ERROR Level**:
- Agent processing failures
- Database errors
- LLM API errors
- Unexpected exceptions

**Log Format**:
```python
logger.info(f"Chat processed: user={user_id}, agent={agent_type}, time={elapsed}ms")
logger.error(f"Chat error: user={user_id}, query={query[:50]}, error={e}", exc_info=True)
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Together, these provide comprehensive coverage where unit tests catch concrete bugs and property tests verify general correctness.

### Unit Testing

**Test Categories**:

1. **Endpoint Tests** (`test_chat_endpoints.py`)
   - Test synchronous chat with valid message
   - Test chat with explicit agent type
   - Test streaming chat endpoint
   - Test conversation history retrieval
   - Test conversation history deletion
   - Test authentication failures (missing/invalid token)
   - Test validation errors (empty message, too long)
   - Test invalid agent_type error

2. **Integration Tests**
   - Test end-to-end flow with real database
   - Test context loading integration
   - Test agent orchestrator integration
   - Test message persistence after chat
   - Test streaming with database save

3. **Edge Cases**
   - Empty conversation history
   - Very long messages (near 2000 char limit)
   - Special characters in messages
   - Concurrent requests from same user
   - Database connection failures

**Example Unit Test**:
```python
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
```

### Property-Based Testing

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**: Minimum 100 iterations per property test

**Property Test Tags**: Each test must include a comment referencing the design property:
```python
# Feature: text-chat-api, Property 1: Message Persistence Completeness
```

**Property Tests**:

1. **Property 1: Message Persistence Completeness**
   - Generate random valid messages
   - Send via chat endpoint
   - Verify both user and assistant messages in database
   - Verify correct role, content, agent_type

2. **Property 2: Authentication Enforcement**
   - Generate random invalid/missing tokens
   - Attempt requests to all endpoints
   - Verify all return 401
   - Verify no database access

3. **Property 3: Agent Routing Consistency**
   - Generate random messages with explicit agent_types
   - Verify response agent_type matches request
   - Verify correct agent handled the request

4. **Property 5: User Data Isolation**
   - Create multiple users with conversations
   - Verify each user only sees their own messages
   - Verify delete only affects own messages

5. **Property 9: Validation Error Handling**
   - Generate invalid inputs (empty, too long, invalid agent_type)
   - Verify appropriate error codes
   - Verify no messages persisted

**Example Property Test**:
```python
from hypothesis import given, strategies as st

# Feature: text-chat-api, Property 1: Message Persistence Completeness
@given(message=st.text(min_size=1, max_size=2000))
@pytest.mark.asyncio
async def test_message_persistence_property(
    message: str,
    authenticated_client,
    db_session
):
    """Property: All successful chats persist both user and assistant messages"""
    client, user = authenticated_client
    
    # Send message
    response = await client.post(
        "/api/v1/chat/chat",
        json={"message": message}
    )
    
    if response.status_code == 200:
        # Verify messages in database
        from app.models.conversation import ConversationMessage
        stmt = select(ConversationMessage).where(
            ConversationMessage.user_id == user.id
        ).order_by(ConversationMessage.created_at.desc()).limit(2)
        
        result = await db_session.execute(stmt)
        messages = result.scalars().all()
        
        assert len(messages) == 2
        assert messages[1].role == "user"
        assert messages[1].content == message
        assert messages[0].role == "assistant"
        assert messages[0].agent_type is not None
```

### Performance Testing

**Latency Targets**:
- Synchronous chat: < 3 seconds (95th percentile)
- Streaming first chunk: < 1 second

**Performance Tests**:
```python
@pytest.mark.asyncio
async def test_chat_latency(authenticated_client):
    """Test chat response time meets target"""
    client, user = authenticated_client
    
    start = time.time()
    response = await client.post(
        "/api/v1/chat/chat",
        json={"message": "Quick question"}
    )
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 3.0  # 3 second target
```

### Test Fixtures

**Required Fixtures** (add to `conftest.py`):
- `authenticated_client`: HTTP client with JWT token
- `test_user`: User with completed onboarding
- `conversation_history`: User with existing messages
- `multiple_users`: Multiple users for isolation testing

### Test Coverage Goals

- **Line Coverage**: > 80% for chat endpoints and related code
- **Branch Coverage**: > 75% for error handling paths
- **Integration Coverage**: All endpoints tested end-to-end

## Performance Considerations

### Latency Optimization

**Target Latencies**:
- Synchronous chat: < 3 seconds (95th percentile)
- Streaming first chunk: < 1 second

**Optimization Strategies**:

1. **Context Loading**:
   - Use selectinload for eager loading of relationships
   - Limit conversation history to last 10 messages
   - Cache user profiles in Redis (future enhancement)

2. **Agent Processing**:
   - Use text mode (no caching) for fresh responses
   - Limit LLM max_tokens to 4096
   - Use fast classifier model (Claude Haiku) for routing

3. **Database Operations**:
   - Use composite index on (user_id, created_at) for history queries
   - Batch insert user and assistant messages in single transaction
   - Use connection pooling (already configured in session.py)

4. **Streaming**:
   - Stream chunks immediately without buffering
   - Save to database after streaming completes (not during)
   - Use async generators for memory efficiency

### Scalability Considerations

**Current Design** (Phase 2):
- Single FastAPI instance
- Direct database connections
- No caching layer

**Future Enhancements** (Phase 3+):
- Redis caching for user contexts (24h TTL)
- Message queue for async message persistence
- Horizontal scaling with load balancer
- Rate limiting per user

### Database Performance

**Query Optimization**:
- Composite index on (user_id, created_at) for O(log n) history queries
- Limit queries to prevent full table scans
- Use EXPLAIN ANALYZE to verify query plans

**Connection Management**:
- Connection pool size: 5 (configured in session.py)
- Max overflow: 10
- Pool pre-ping enabled for connection health checks

## Security Considerations

### Authentication

- All endpoints require valid JWT Bearer token
- JWT validation handled by `get_current_user` dependency
- Token expiration: 24 hours (configurable)
- No refresh tokens in Phase 2 (add in Phase 3)

### Authorization

- Users can only access their own conversation data
- User ID extracted from JWT token (not request body)
- Database queries filtered by user_id from token

### Input Validation

- Message length: 1-2000 characters (Pydantic validation)
- Agent type: Must be valid AgentType enum value
- SQL injection: Prevented by SQLAlchemy parameterized queries
- XSS: Not applicable (API only, no HTML rendering)

### Data Privacy

- Conversation messages contain sensitive health/fitness data
- No encryption at rest in Phase 2 (add in Phase 3 if required)
- Encryption in transit via HTTPS (production requirement)
- No PII in logs (user_id only, not email/name)

### Rate Limiting

- Not implemented in Phase 2
- Future: 100 requests per minute per user
- Future: 10 streaming connections per user

## Deployment Considerations

### Database Migration

**Migration Steps**:
1. Create migration: `poetry run alembic revision --autogenerate -m "add conversation messages"`
2. Review generated migration
3. Apply migration: `poetry run alembic upgrade head`
4. Verify table and index creation

**Rollback Plan**:
- Migration is reversible (drop table)
- No data loss risk (new table)

### API Versioning

- All endpoints under `/api/v1/chat/`
- Future breaking changes require `/api/v2/`
- Maintain v1 for backward compatibility

### Monitoring

**Metrics to Track**:
- Request count per endpoint
- Response time (p50, p95, p99)
- Error rate by status code
- Agent type distribution
- Message count per user

**Logging**:
- All requests logged at INFO level
- Errors logged at ERROR level with full context
- Performance metrics logged for monitoring

### Documentation

- OpenAPI/Swagger docs auto-generated by FastAPI
- Available at `/docs` endpoint
- Includes request/response schemas, authentication, error codes

## Dependencies

### External Dependencies

**Existing** (no new dependencies required):
- FastAPI: Web framework
- SQLAlchemy: ORM and database operations
- Pydantic: Schema validation
- asyncpg: Async PostgreSQL driver
- LangChain: Agent framework (already integrated)

**Testing**:
- pytest: Test framework
- pytest-asyncio: Async test support
- httpx: Async HTTP client for testing
- hypothesis: Property-based testing

### Internal Dependencies

**Required** (already implemented):
- Sub-Doc 1: LangChain Foundation
  - AgentOrchestrator
  - AgentContext, AgentResponse
  - BaseAgent
- Sub-Doc 2: Specialized Agents
  - All 6 specialized agents
  - Agent tools and prompts
- Phase 1: Core Infrastructure
  - User authentication (JWT)
  - Database models and session
  - FastAPI application setup

### Configuration

**Environment Variables** (add to .env):
```bash
# No new environment variables required
# Uses existing LLM and database configuration
```

## Future Enhancements

### Phase 3 Enhancements

1. **Redis Caching**:
   - Cache user contexts (24h TTL)
   - Cache conversation history (1h TTL)
   - Invalidate on profile updates

2. **Rate Limiting**:
   - Per-user request limits
   - Per-user streaming connection limits
   - Redis-based rate limiting

3. **Message Queue**:
   - Async message persistence via Celery
   - Reduce endpoint latency
   - Improve scalability

4. **Advanced Features**:
   - Message reactions/feedback
   - Conversation branching
   - Message editing/deletion
   - Export conversation history

5. **Analytics**:
   - User engagement metrics
   - Agent performance tracking
   - Popular query patterns
   - Response quality metrics

### Potential Optimizations

1. **Streaming Improvements**:
   - WebSocket support for bidirectional communication
   - Typing indicators
   - Read receipts

2. **Context Enhancements**:
   - Semantic search over conversation history
   - Conversation summarization
   - Context window management

3. **Performance**:
   - Response caching for common queries
   - Predictive context pre-loading
   - Connection pooling optimization
