# Implementation Plan: Text Chat API Integration

## Overview

This implementation plan breaks down the Text Chat API Integration feature into discrete coding tasks. The feature adds REST API endpoints for text-based chat interactions with AI fitness agents, building upon the existing LangChain Foundation and Specialized Agents infrastructure.

The implementation follows this sequence:
1. Create database model and migration
2. Update context loader for conversation history
3. Create Pydantic schemas for API validation
4. Implement chat endpoints (synchronous, streaming, history)
5. Register router and integrate with FastAPI app
6. Write comprehensive tests

## Tasks

- [x] 1. Create conversation history database model and migration
  - Create `backend/app/models/conversation.py` with ConversationMessage model
  - Define table schema: id (UUID), user_id (FK), role, content, agent_type, created_at
  - Add composite index on (user_id, created_at) for efficient queries
  - Generate Alembic migration: `poetry run alembic revision --autogenerate -m "add conversation messages"`
  - Review and apply migration: `poetry run alembic upgrade head`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 2. Update context loader to fetch conversation history
  - [x] 2.1 Implement `_load_conversation_history()` function in `backend/app/services/context_loader.py`
    - Query ConversationMessage table filtered by user_id
    - Order by created_at DESC, limit to 10 messages
    - Reverse to chronological order
    - Return list of dicts with role, content, agent_type
    - _Requirements: 1.6, 7.2_
  
  - [ ]* 2.2 Write property test for conversation history loading
    - **Property 8: Context Loading Integration**
    - **Validates: Requirements 2.2, 7.1, 7.2, 7.4**

- [x] 3. Create Pydantic schemas for chat API
  - Create `backend/app/schemas/chat.py` with ChatRequest, ChatResponse, ChatHistoryResponse models
  - ChatRequest: message (1-2000 chars), optional agent_type
  - ChatResponse: response, agent_type, conversation_id, tools_used
  - ChatHistoryResponse: messages list, total count
  - Add validation rules and field descriptions
  - _Requirements: 2.7, 6.3_

- [x] 4. Implement synchronous chat endpoint
  - [x] 4.1 Create `backend/app/api/v1/endpoints/chat.py` with POST /chat endpoint
    - Add JWT authentication dependency (get_current_user)
    - Load user context via context_loader.load_agent_context()
    - Initialize AgentOrchestrator in text mode
    - Parse optional agent_type from request
    - Call orchestrator.route_query() with user context
    - Save user message to database (role="user")
    - Save assistant response to database (role="assistant", agent_type from response)
    - Commit transaction
    - Return ChatResponse with response content, agent_type, conversation_id, tools_used
    - Add error handling for 401, 422, 400, 500
    - Add logging for successful requests and errors
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [x] 4.2 Write property test for message persistence
    - **Property 1: Message Persistence Completeness**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 3.5**
  
  - [x] 4.3 Write property test for authentication enforcement
    - **Property 2: Authentication Enforcement**
    - **Validates: Requirements 2.6, 3.6, 4.6, 5.4, 8.1, 8.2**
  
  - [x] 4.4 Write property test for agent routing consistency
    - **Property 3: Agent Routing Consistency**
    - **Validates: Requirements 2.4, 6.1, 6.2**
  
  - [ ]* 4.5 Write property test for automatic classification
    - **Property 4: Automatic Classification**
    - **Validates: Requirements 2.3, 6.4**
  
  - [ ]* 4.6 Write property test for response structure
    - **Property 9: Response Structure Completeness**
    - **Validates: Requirements 2.5**
  
  - [ ]* 4.7 Write property test for validation error handling
    - **Property 10: Validation Error Handling**
    - **Validates: Requirements 2.7, 6.3**
  
  - [ ]* 4.8 Write unit tests for synchronous chat endpoint
    - Test successful chat with valid message
    - Test chat with explicit agent type
    - Test authentication failure (missing/invalid token)
    - Test validation errors (empty message, too long)
    - Test invalid agent_type error (400)
    - Test agent processing failure (500)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

- [x] 5. Checkpoint - Ensure synchronous chat endpoint works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement streaming chat endpoint
  - [x] 6.1 Add POST /chat/stream endpoint to `backend/app/api/v1/endpoints/chat.py`
    - Add JWT authentication dependency
    - Create async generator function for SSE streaming
    - Load user context and get appropriate agent
    - Stream response chunks via agent.stream_response()
    - Send each chunk as SSE data event with JSON payload
    - Send final event with "done: true" and agent_type
    - Save user message and complete assistant response after streaming
    - Handle errors with error events in stream
    - Add logging for streaming requests
    - Return StreamingResponse with media_type="text/event-stream"
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [ ]* 6.2 Write property test for streaming response format
    - **Property 7: Streaming Response Format**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
  
  - [ ]* 6.3 Write property test for streaming performance
    - **Property 11: Performance Targets (streaming)**
    - **Validates: Requirements 3.2**
  
  - [ ]* 6.4 Write unit tests for streaming endpoint
    - Test streaming with valid message
    - Test streaming chunk format (SSE)
    - Test final completion event
    - Test message persistence after streaming
    - Test authentication failure
    - Test streaming error handling
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 7. Implement conversation history endpoints
  - [x] 7.1 Add GET /chat/history endpoint to `backend/app/api/v1/endpoints/chat.py`
    - Add JWT authentication dependency
    - Accept optional limit query parameter (default 50, max 200)
    - Query ConversationMessage table filtered by user_id
    - Order by created_at DESC, apply limit
    - Get total count of user's messages
    - Reverse messages to chronological order
    - Format messages with role, content, agent_type, created_at
    - Return ChatHistoryResponse with messages and total
    - Add error handling for 401
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [x] 7.2 Add DELETE /chat/history endpoint to `backend/app/api/v1/endpoints/chat.py`
    - Add JWT authentication dependency
    - Delete all ConversationMessage records for user_id
    - Commit transaction
    - Return success status {"status": "cleared"}
    - Add error handling for 401
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [x] 7.3 Write property test for conversation history ordering
    - **Property 5: Conversation History Ordering and Completeness**
    - **Validates: Requirements 1.6, 4.1, 4.2, 4.3, 4.4**
  
  - [x] 7.4 Write property test for user data isolation
    - **Property 6: User Data Isolation**
    - **Validates: Requirements 4.5, 5.1, 5.3, 8.3, 8.4**
  
  - [ ]* 7.5 Write property test for deletion completeness
    - **Property 12: Deletion Completeness**
    - **Validates: Requirements 5.1, 5.2**
  
  - [ ]* 7.6 Write unit tests for history endpoints
    - Test get history with messages
    - Test get history with limit parameter
    - Test get history with empty history
    - Test delete history
    - Test authentication failures
    - Test user data isolation (multiple users)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4_

- [x] 8. Register chat router in FastAPI application
  - Update `backend/app/api/v1/__init__.py` to import and include chat router
  - Add router with prefix="/chat" and tags=["chat"]
  - Verify all endpoints appear in OpenAPI/Swagger docs at /docs
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 9. Checkpoint - Ensure all endpoints work end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 10. Write integration tests for complete chat flows
  - [ ]* 10.1 Write integration test for complete synchronous chat flow
    - Test full flow: authenticate → send message → verify response → check database
    - Test context loading integration
    - Test agent orchestrator integration
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.1, 7.2, 7.4_
  
  - [ ]* 10.2 Write integration test for complete streaming flow
    - Test full flow: authenticate → stream message → verify chunks → check database
    - Test SSE format and completion
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ]* 10.3 Write integration test for conversation continuity
    - Send multiple messages
    - Verify conversation history grows
    - Verify history retrieval shows all messages
    - Verify deletion clears all messages
    - _Requirements: 1.6, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2_

- [ ]* 11. Write property test for logging completeness
  - **Property 13: Logging Completeness**
  - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

- [ ]* 12. Write property test for performance targets
  - **Property 11: Performance Targets (synchronous)**
  - **Validates: Requirements 2.1**

- [ ] 13. Final checkpoint - Verify all requirements met
  - Run full test suite: `poetry run pytest backend/tests/test_chat_endpoints.py -v`
  - Verify all tests pass
  - Check OpenAPI docs at http://localhost:8000/docs
  - Verify all 4 endpoints documented with schemas
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- All database operations use async SQLAlchemy sessions
- All endpoints require JWT authentication via get_current_user dependency
- Streaming uses Server-Sent Events (SSE) for simplicity over WebSockets
- Conversation history is stored in a new conversation_messages table
- Context loader is updated to fetch conversation history from database
- Agent orchestrator is used in "text" mode (not "voice")
