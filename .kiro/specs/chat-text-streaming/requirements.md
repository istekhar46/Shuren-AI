# Requirements Document

## Introduction

This document specifies the requirements for implementing real-time text streaming in the Shuren chat interface. The feature will replace the current loading indicator with incremental text display as AI responses are generated, providing better user experience and perceived performance. The system will leverage existing backend SSE infrastructure and LangChain streaming capabilities.

## Glossary

- **SSE (Server-Sent Events)**: HTTP-based protocol for server-to-client streaming
- **Chat_Service**: Frontend service handling chat API communication
- **Agent**: Backend AI component that generates responses
- **Message_List**: React component displaying conversation messages
- **Streaming_Response**: FastAPI response type for SSE delivery
- **LangChain**: AI framework providing LLM streaming capabilities
- **EventSource**: Browser API for consuming SSE streams
- **Chat_Hook**: React hook managing chat state and operations
- **Loading_Indicator**: Current UI component showing "Agent is typing..."
- **Onboarding_Chat**: Specialized chat flow during user onboarding
- **Regular_Chat**: Standard chat interface for general queries

## Requirements

### Requirement 1: Backend Streaming Endpoint

**User Story:** As a backend system, I want to provide streaming endpoints for both regular and onboarding chat, so that frontend clients can receive incremental response chunks.

#### Acceptance Criteria

1. WHEN a client requests `/api/v1/chat/stream`, THE Backend SHALL stream response chunks using Server-Sent Events
2. WHEN a client requests `/api/v1/chat/onboarding-stream`, THE Backend SHALL stream onboarding-specific responses using Server-Sent Events
3. WHEN streaming a response, THE Backend SHALL use LangChain's `astream()` method to generate chunks
4. WHEN a chunk is generated, THE Backend SHALL format it as `data: {"chunk": "text"}\n\n`
5. WHEN streaming completes, THE Backend SHALL send `data: {"done": true, "agent_type": "agent_name"}\n\n`
6. WHEN streaming completes, THE Backend SHALL save the complete response to the database
7. WHEN authentication fails, THE Backend SHALL return HTTP 401 before starting the stream
8. WHEN an error occurs during streaming, THE Backend SHALL send `data: {"error": "message"}\n\n` and close the stream

### Requirement 2: Frontend Streaming Service

**User Story:** As a frontend developer, I want a service that handles SSE connections and parses streaming responses, so that components can easily consume real-time data.

#### Acceptance Criteria

1. WHEN `streamMessage()` is called, THE Chat_Service SHALL create an EventSource connection to the streaming endpoint
2. WHEN creating the connection, THE Chat_Service SHALL include the authentication token as a query parameter
3. WHEN a message event is received, THE Chat_Service SHALL parse the JSON payload
4. WHEN a chunk is received, THE Chat_Service SHALL invoke the provided callback with the chunk text
5. WHEN a completion event is received, THE Chat_Service SHALL invoke the completion callback
6. WHEN an error event is received, THE Chat_Service SHALL invoke the error callback and close the connection
7. WHEN the connection is closed, THE Chat_Service SHALL clean up the EventSource instance
8. THE Chat_Service SHALL provide a method to cancel active streaming connections

### Requirement 3: Chat State Management

**User Story:** As a chat interface, I want to manage streaming message state, so that I can display incremental updates as they arrive.

#### Acceptance Criteria

1. WHEN a user sends a message, THE Chat_Hook SHALL immediately add the user message to the conversation
2. WHEN streaming starts, THE Chat_Hook SHALL create a placeholder assistant message with empty content
3. WHEN a chunk arrives, THE Chat_Hook SHALL append the chunk to the placeholder message content
4. WHEN streaming completes, THE Chat_Hook SHALL mark the message as finalized
5. WHEN streaming fails, THE Chat_Hook SHALL mark the message with an error state
6. WHEN a streaming message exists, THE Chat_Hook SHALL prevent sending new messages until completion
7. THE Chat_Hook SHALL maintain conversation history with both user and assistant messages

### Requirement 4: Message Display

**User Story:** As a user, I want to see the AI response being typed in real-time, so that I have immediate feedback and better perceived performance.

#### Acceptance Criteria

1. WHEN a streaming message is displayed, THE Message_List SHALL render the current accumulated text
2. WHEN new chunks arrive, THE Message_List SHALL update the display without flickering
3. WHEN a message is streaming, THE Message_List SHALL display a typing indicator (cursor or animation)
4. WHEN streaming completes, THE Message_List SHALL remove the typing indicator
5. WHEN new content is added, THE Message_List SHALL auto-scroll to keep the latest text visible
6. THE Message_List SHALL distinguish between finalized and streaming messages visually

### Requirement 5: Onboarding Chat Integration

**User Story:** As a user completing onboarding, I want to see streaming responses during the onboarding chat, so that I have the same real-time experience as regular chat.

#### Acceptance Criteria

1. WHEN using onboarding chat, THE Onboarding_Chat_Page SHALL use the streaming endpoint
2. WHEN onboarding streaming starts, THE System SHALL use `/api/v1/chat/onboarding-stream`
3. WHEN onboarding responses stream, THE System SHALL maintain onboarding state consistency
4. WHEN onboarding streaming completes, THE System SHALL update onboarding progress if applicable
5. THE Onboarding_Chat_Page SHALL display streaming messages identically to regular chat

### Requirement 6: Error Handling

**User Story:** As a user, I want graceful error handling during streaming, so that I can retry or understand what went wrong.

#### Acceptance Criteria

1. WHEN a network error occurs during streaming, THE System SHALL display an error message
2. WHEN streaming fails, THE System SHALL provide a retry button
3. WHEN authentication expires during streaming, THE System SHALL prompt for re-authentication
4. WHEN the server sends an error event, THE System SHALL display the error message to the user
5. IF streaming is interrupted, THEN THE System SHALL preserve any partial response received
6. WHEN an error occurs, THE System SHALL log the error details for debugging

### Requirement 7: Connection Management

**User Story:** As a system, I want to properly manage streaming connections, so that resources are not leaked and users can navigate freely.

#### Acceptance Criteria

1. WHEN a user navigates away from chat, THE System SHALL cancel any active streaming connection
2. WHEN a component unmounts, THE System SHALL close the EventSource connection
3. WHEN multiple messages are sent rapidly, THE System SHALL queue them and process sequentially
4. WHEN a streaming connection is idle for 60 seconds, THE System SHALL close it and show a timeout error
5. THE System SHALL limit to one active streaming connection per chat session

### Requirement 8: Accessibility

**User Story:** As a user with assistive technology, I want streaming messages to be accessible, so that I can follow the conversation in real-time.

#### Acceptance Criteria

1. WHEN a streaming message updates, THE System SHALL use ARIA live regions to announce changes
2. WHEN streaming completes, THE System SHALL announce completion to screen readers
3. WHEN a typing indicator is shown, THE System SHALL provide appropriate ARIA labels
4. THE System SHALL ensure keyboard navigation works during streaming
5. THE System SHALL maintain focus management during streaming updates

### Requirement 9: Performance

**User Story:** As a user, I want smooth streaming performance, so that the interface remains responsive during AI responses.

#### Acceptance Criteria

1. WHEN chunks arrive rapidly, THE System SHALL batch updates to avoid excessive re-renders
2. WHEN displaying long messages, THE System SHALL maintain 60fps scroll performance
3. WHEN streaming multiple chunks, THE System SHALL debounce scroll updates to every 100ms
4. THE System SHALL render streaming text without blocking the main thread
5. WHEN streaming completes, THE System SHALL finalize the message in under 50ms

### Requirement 10: Backward Compatibility

**User Story:** As a developer, I want to maintain the non-streaming endpoint, so that we can fall back if streaming fails or for testing purposes.

#### Acceptance Criteria

1. THE Backend SHALL maintain the existing `/api/v1/chat` non-streaming endpoint
2. WHEN streaming is not supported by the client, THE System SHALL fall back to non-streaming
3. WHEN a feature flag disables streaming, THE System SHALL use the non-streaming endpoint
4. THE System SHALL allow configuration to prefer streaming or non-streaming mode
5. WHEN testing, THE System SHALL support both streaming and non-streaming modes
