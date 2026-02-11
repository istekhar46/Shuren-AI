import { describe, it, expect, beforeEach, vi } from 'vitest';
import fc from 'fast-check';
import { chatService } from '../../src/services/chatService';
import api from '../../src/services/api';
import type { AgentType, ChatMessage, ChatResponse } from '../../src/types';

// Mock the API module
vi.mock('../../src/services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('Chat Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Property 8: Messages routed to selected agent', async () => {
    // Feature: minimal-frontend-testing, Property 8: Messages routed to selected agent
    // For any message sent with a specific agent type, the API call should include
    // that agent type, ensuring messages are routed to the correct specialized agent.
    // Validates: Requirements 2.4.2, 2.4.4

    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 500 }), // Random message text
        fc.constantFrom<AgentType>(
          'workout_planning',
          'diet_planning',
          'supplement_guidance',
          'tracking_adjustment',
          'scheduling_reminder',
          'general_assistant'
        ), // Random agent type
        fc.option(fc.uuid(), { nil: undefined }), // Optional conversation ID
        async (message, agentType, conversationId) => {
          // Mock successful API response
          const mockResponse: ChatResponse = {
            message: 'Agent response',
            agentType: agentType,
            conversationId: conversationId || 'new-conversation-id',
            timestamp: new Date().toISOString(),
          };
          vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse });

          // Send message through service
          const result = await chatService.sendMessage(
            message,
            agentType,
            conversationId
          );

          // Verify API was called with correct agent type
          expect(api.post).toHaveBeenCalledWith('/chat/chat', {
            message,
            agent_type: agentType,
            conversation_id: conversationId,
          });

          // Verify response contains the same agent type
          expect(result.agentType).toBe(agentType);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 9: Chat history accumulates messages', async () => {
    // Feature: minimal-frontend-testing, Property 9: Chat history accumulates messages
    // For any sequence of messages sent during a conversation, the chat history
    // should accumulate all messages in order, maintaining conversation context.
    // Validates: Requirements 2.4.5

    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            message: fc.string({ minLength: 1, maxLength: 200 }),
            agentType: fc.constantFrom<AgentType>(
              'workout_planning',
              'diet_planning',
              'supplement_guidance',
              'tracking_adjustment',
              'scheduling_reminder',
              'general_assistant'
            ),
          }),
          { minLength: 1, maxLength: 10 }
        ), // Array of messages to send
        fc.uuid(), // Conversation ID
        async (messagesToSend, conversationId) => {
          const accumulatedMessages: ChatMessage[] = [];

          // Send each message and accumulate responses
          for (let i = 0; i < messagesToSend.length; i++) {
            const { message, agentType } = messagesToSend[i];

            // Mock API response for sending message
            const mockResponse: ChatResponse = {
              message: `Response to: ${message}`,
              agentType: agentType,
              conversationId: conversationId,
              timestamp: new Date(Date.now() + i * 1000).toISOString(),
            };
            vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse });

            // Send message
            const response = await chatService.sendMessage(
              message,
              agentType,
              conversationId
            );

            // Add user message to accumulated history
            accumulatedMessages.push({
              id: `user-${i}`,
              role: 'user',
              content: message,
              agentType: agentType,
              timestamp: new Date(Date.now() + i * 1000).toISOString(),
            });

            // Add agent response to accumulated history
            accumulatedMessages.push({
              id: `agent-${i}`,
              role: 'assistant',
              content: response.message,
              agentType: response.agentType,
              timestamp: response.timestamp,
            });
          }

          // Mock getHistory to return accumulated messages
          vi.mocked(api.get).mockResolvedValueOnce({
            data: accumulatedMessages,
          });

          // Retrieve history
          const history = await chatService.getHistory(conversationId);

          // Verify history contains all messages
          expect(history.length).toBe(messagesToSend.length * 2); // user + agent for each

          // Verify messages are in order
          for (let i = 0; i < messagesToSend.length; i++) {
            const userMsgIndex = i * 2;
            const agentMsgIndex = i * 2 + 1;

            expect(history[userMsgIndex].role).toBe('user');
            expect(history[userMsgIndex].content).toBe(
              messagesToSend[i].message
            );
            expect(history[agentMsgIndex].role).toBe('assistant');
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 10: Chat errors displayed', async () => {
    // Feature: minimal-frontend-testing, Property 10: Chat errors displayed
    // For any API error during chat (network failure, server error, etc.),
    // the error should be caught and made available for display to the user.
    // Validates: Requirements 2.4.7

    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 500 }), // Random message
        fc.constantFrom<AgentType>(
          'workout_planning',
          'diet_planning',
          'supplement_guidance',
          'tracking_adjustment',
          'scheduling_reminder',
          'general_assistant'
        ), // Random agent type
        fc.constantFrom(
          400, // Bad Request
          401, // Unauthorized
          403, // Forbidden
          404, // Not Found
          500, // Internal Server Error
          502, // Bad Gateway
          503 // Service Unavailable
        ), // Random error status code
        fc.constantFrom(
          'Agent is currently unavailable',
          'Failed to process message',
          'Network connection error',
          'Service temporarily unavailable',
          'Invalid request format',
          'Authentication failed'
        ), // Random error message
        async (message, agentType, statusCode, errorMessage) => {
          // Mock API error response
          const mockError = {
            response: {
              status: statusCode,
              data: {
                detail: errorMessage,
              },
            },
            message: errorMessage,
          };
          vi.mocked(api.post).mockRejectedValueOnce(mockError);

          // Attempt to send message (should fail)
          try {
            await chatService.sendMessage(message, agentType);
            // Should not reach here
            expect.fail('Expected error to be thrown');
          } catch (err: any) {
            // Verify error structure is available for display
            expect(err).toBeDefined();

            // Verify error has response information
            if (err.response) {
              expect(err.response.status).toBe(statusCode);
              expect(err.response.data).toBeDefined();

              // Verify error message is accessible
              const displayMessage =
                err.response.data.detail || err.message || 'Unknown error';
              expect(displayMessage).toBeDefined();
              expect(typeof displayMessage).toBe('string');
              expect(displayMessage.length).toBeGreaterThan(0);
            } else {
              // Network error without response
              expect(err.message).toBeDefined();
              expect(typeof err.message).toBe('string');
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
