# Implementation Plan: Chat Text Streaming

## Overview

This implementation plan breaks down the chat text streaming feature into incremental coding tasks. The approach follows a backend-first strategy, implementing streaming endpoints and agent integration, then moving to frontend service layer, state management, and finally UI components. Each task builds on previous work and includes testing to validate functionality early.

## Tasks

- [x] 1. Backend: Implement streaming endpoint infrastructure
  - [x] 1.1 Add `/chat/onboarding-stream` endpoint to `backend/app/api/v1/endpoints/chat.py`
    - Create new GET endpoint with FastAPI StreamingResponse
    - Accept `message` and `token` as query parameters
    - Implement SSE event generator with proper headers (Cache-Control, Connection, X-Accel-Buffering)
    - Use existing authentication via `get_current_user_from_token` dependency
    - _Requirements: 1.1, 1.2, 1.7_

  - [x] 1.2 Enhance existing `/chat/stream` endpoint
    - Verify SSE headers are correctly set
    - Ensure error handling sends error events before closing stream
    - Add timeout handling (30 seconds of no chunks)
    - _Requirements: 1.1, 1.7, 1.8_

  - [x]* 1.3 Write unit tests for streaming endpoints
    - Test 401 response with invalid token
    - Test timeout after 60 seconds
    - Test error event format when LLM fails
    - _Requirements: 1.7, 1.8_

- [x] 2. Backend: Implement agent streaming methods
  - [x] 2.1 Add `stream_onboarding_response()` to `AgentOrchestrator`
    - Load onboarding state from database
    - Build onboarding-specific prompt with context
    - Stream response using conversational agent
    - Update onboarding progress after completion
    - _Requirements: 1.3, 5.3, 5.4_

  - [x] 2.2 Verify `BaseAgent.stream_response()` uses LangChain `astream()`
    - Ensure all agents inherit correct streaming implementation
    - Verify chunks are yielded as they arrive
    - Store full response for database save
    - _Requirements: 1.3_

  - [x] 2.3 Add database persistence after streaming
    - Save complete conversation to database after stream completes
    - Use separate async session to avoid blocking
    - Implement retry logic for save failures (Celery task)
    - _Requirements: 1.6_

  - [x]* 2.4 Write property test for SSE format compliance
    - **Property 1: SSE Format Compliance**
    - **Validates: Requirements 1.1, 1.2, 1.4, 1.5, 1.8**
    - Generate random messages and verify all events follow SSE spec
    - Test chunk events, completion events, and error events

  - [x]* 2.5 Write property test for streaming persistence
    - **Property 2: Streaming Persistence Round-Trip**
    - **Validates: Requirements 1.6**
    - Stream random messages and verify database contains complete response

- [ ] 3. Checkpoint - Backend streaming functional
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Frontend: Implement chat service streaming
  - [x] 4.1 Enhance `streamMessage()` in `frontend/src/services/chatService.ts`
    - Create EventSource connection with authentication token in query param
    - Implement `onmessage` handler to parse JSON and route to callbacks
    - Implement `onerror` handler to trigger error callback
    - Add connection cleanup on close
    - Return cancellation function
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 4.2 Add `cancelStream()` method to ChatService
    - Close active EventSource connection
    - Set activeStream to null
    - _Requirements: 2.8_

  - [x]* 4.3 Write unit tests for ChatService
    - Test EventSource created with correct URL and token
    - Test chunk callback invoked with correct data
    - Test completion callback invoked
    - Test error callback invoked and connection closed
    - Test cancellation closes connection
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x]* 4.4 Write property test for callback routing
    - **Property 5: Callback Routing Correctness**
    - **Validates: Requirements 2.4, 2.5, 2.6**
    - Generate random SSE events and verify correct callbacks invoked

- [ ] 5. Frontend: Implement chat state management
  - [ ] 5.1 Update `useChat` hook in `frontend/src/hooks/useChat.ts`
    - Add immediate user message to state on send
    - Create placeholder assistant message with `isStreaming: true`
    - Implement `onChunk` callback to append chunks to placeholder
    - Implement `onComplete` callback to set `isStreaming: false`
    - Implement `onError` callback to set error state
    - Prevent sending new messages while streaming
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ] 5.2 Add `retryLastMessage()` method to useChat
    - Find last user message in history
    - Remove failed assistant message
    - Resend user message
    - _Requirements: 6.2_

  - [ ] 5.3 Add cleanup effect for component unmount
    - Cancel active stream on unmount
    - Use useEffect cleanup function
    - _Requirements: 7.1, 7.2_

  - [ ]* 5.4 Write unit tests for useChat hook
    - Test user message added immediately
    - Test placeholder created on stream start
    - Test chunks appended correctly
    - Test message finalized on completion
    - Test error state set on failure
    - Test concurrent sends blocked
    - Test cleanup on unmount
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.1, 7.2_

  - [ ]* 5.5 Write property test for content accumulation
    - **Property 9: Content Accumulation Invariant**
    - **Validates: Requirements 3.3, 4.1**
    - Generate random chunk sequences and verify final content equals concatenation

  - [ ]* 5.6 Write property test for conversation history
    - **Property 13: Conversation History Preservation**
    - **Validates: Requirements 3.7**
    - Send random sequences of messages and verify all preserved in order

- [ ] 6. Frontend: Implement message display components
  - [ ] 6.1 Update `MessageList` component in `frontend/src/components/MessageList.tsx`
    - Render streaming messages with current accumulated text
    - Show typing indicator (cursor) when `isStreaming` is true
    - Hide typing indicator when `isStreaming` is false
    - Add ARIA live region for accessibility announcements
    - Add ARIA labels to typing indicator
    - _Requirements: 4.1, 4.3, 4.4, 8.1, 8.2, 8.3_

  - [ ] 6.2 Implement auto-scroll with debouncing
    - Use useRef for scroll target
    - Debounce scroll updates to 100ms
    - Use requestAnimationFrame for smooth scrolling
    - _Requirements: 4.5, 9.3_

  - [ ] 6.3 Add visual distinction for streaming vs finalized messages
    - Apply different CSS classes based on `isStreaming` state
    - Add data attributes for testing
    - _Requirements: 4.6_

  - [ ] 6.4 Add error display and retry button
    - Show error message when message has error property
    - Render retry button for failed messages
    - Wire retry button to `retryLastMessage()` from useChat
    - _Requirements: 6.1, 6.2, 6.4_

  - [ ]* 6.5 Write unit tests for MessageList
    - Test typing indicator shown when isStreaming is true
    - Test typing indicator hidden when isStreaming is false
    - Test auto-scroll triggered on content update
    - Test ARIA live region announces streaming
    - Test error message displayed
    - Test retry button rendered for failed messages
    - _Requirements: 4.3, 4.4, 4.5, 6.1, 6.2, 8.1, 8.2, 8.3_

- [ ] 7. Checkpoint - Frontend streaming functional
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Frontend: Update chat pages
  - [ ] 8.1 Update `ChatPage` in `frontend/src/pages/ChatPage.tsx`
    - Replace LoadingIndicator with streaming from useChat
    - Pass `isOnboarding: false` to useChat
    - Update input placeholder based on streaming state
    - Disable input while streaming
    - _Requirements: 3.1, 3.6_

  - [ ] 8.2 Update `OnboardingChatPage` in `frontend/src/pages/OnboardingChatPage.tsx`
    - Replace LoadingIndicator with streaming from useChat
    - Pass `isOnboarding: true` to useChat
    - Ensure UI matches regular chat (same MessageList component)
    - Update input placeholder based on streaming state
    - _Requirements: 5.1, 5.2, 5.5_

  - [ ]* 8.3 Write integration tests for chat pages
    - Test complete streaming flow in ChatPage
    - Test complete streaming flow in OnboardingChatPage
    - Test UI consistency between both pages
    - _Requirements: 5.5_

- [ ] 9. Backend: Add monitoring and logging
  - [ ] 9.1 Add structured logging to streaming endpoints
    - Log stream start with user_id and message_id
    - Log stream completion with duration and chunk count
    - Log all errors with full context
    - Log cleanup events
    - _Requirements: 6.6_

  - [ ] 9.2 Add metrics tracking
    - Track streaming session duration (avg, p95, p99)
    - Track chunks per session
    - Track error rate by error type
    - Track database save success rate
    - _Requirements: 6.6_

  - [ ]* 9.3 Write property test for error logging
    - **Property 23: Error Logging**
    - **Validates: Requirements 6.6**
    - Trigger random errors and verify all are logged

- [ ] 10. Frontend: Add performance optimizations
  - [ ] 10.1 Implement render batching for rapid chunks
    - Use React 18 automatic batching
    - Verify multiple setState calls in same event are batched
    - Add manual batching if needed for older React versions
    - _Requirements: 9.1_

  - [ ] 10.2 Add memory management for long conversations
    - Limit message history to last 50 messages
    - Clear old messages when limit exceeded
    - Preserve conversation in backend
    - _Requirements: 9.1_

  - [ ]* 10.3 Write property test for render batching
    - **Property 30: Render Batching**
    - **Validates: Requirements 9.1**
    - Send rapid chunks and verify re-renders are batched

- [ ] 11. Security and validation
  - [ ] 11.1 Add content sanitization
    - Install DOMPurify library
    - Sanitize all streamed content before display
    - Prevent XSS attacks
    - _Requirements: 1.8, 6.1_

  - [ ] 11.2 Implement rate limiting
    - Limit to 10 concurrent streams per user
    - Limit to 100 messages per hour per user
    - Return 429 status when limits exceeded
    - _Requirements: 7.5_

  - [ ]* 11.3 Write unit tests for security measures
    - Test content sanitization removes malicious scripts
    - Test rate limiting blocks excessive requests
    - Test concurrent connection limit enforced
    - _Requirements: 7.5_

- [ ] 12. Accessibility enhancements
  - [ ] 12.1 Ensure keyboard navigation during streaming
    - Test tab navigation works during streaming
    - Test arrow key navigation works
    - Test enter key works for sending messages
    - _Requirements: 8.4_

  - [ ] 12.2 Implement focus management
    - Preserve focus during streaming updates
    - Don't steal focus when chunks arrive
    - Maintain focus on input after sending
    - _Requirements: 8.5_

  - [ ]* 12.3 Write accessibility tests
    - Test ARIA live regions announce correctly
    - Test keyboard navigation preserved
    - Test focus management stable
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 12.4 Write property test for accessibility compliance
    - **Property 27: Accessibility Compliance**
    - **Validates: Requirements 8.1, 8.2, 8.3**
    - Verify ARIA attributes present for all streaming states

- [ ] 13. Backward compatibility and feature flag
  - [ ] 13.1 Add feature flag for streaming
    - Add `ENABLE_STREAMING` config variable
    - Default to false for gradual rollout
    - Frontend checks flag and falls back to non-streaming if disabled
    - _Requirements: 10.3, 10.4_

  - [ ] 13.2 Implement fallback to non-streaming
    - Detect if EventSource is not supported
    - Fall back to existing `sendMessage()` method
    - Show loading indicator instead of streaming
    - _Requirements: 10.2_

  - [ ]* 13.3 Write tests for backward compatibility
    - Test non-streaming endpoint still works
    - Test fallback when EventSource unavailable
    - Test feature flag toggles behavior
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 14. Final checkpoint - Complete feature validation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Documentation and deployment preparation
  - [ ] 15.1 Update API documentation
    - Document `/chat/stream` endpoint
    - Document `/chat/onboarding-stream` endpoint
    - Include SSE event format examples
    - Add authentication requirements
    - _Requirements: 1.1, 1.2_

  - [ ] 15.2 Add nginx configuration for SSE
    - Disable buffering for streaming endpoints
    - Set appropriate headers
    - Document configuration in deployment guide
    - _Requirements: 1.1, 1.2_

  - [ ] 15.3 Create migration guide
    - Document feature flag rollout plan
    - Document monitoring metrics to watch
    - Document rollback procedure
    - _Requirements: 10.3, 10.4_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- Backend tasks use Python with FastAPI, LangChain, and pytest
- Frontend tasks use TypeScript with React, EventSource API, and Jest
- All streaming uses official APIs: FastAPI StreamingResponse, LangChain astream(), EventSource
