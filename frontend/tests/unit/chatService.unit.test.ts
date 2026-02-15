import { describe, it, expect, vi, beforeEach } from 'vitest';
import { chatService } from '../../src/services/chatService';
import api from '../../src/services/api';
import type { ChatResponse, ChatHistoryResponse } from '../../src/types/api';

// Mock the api module
vi.mock('../../src/services/api');

describe('chatService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('sendMessage', () => {
    it('should call POST /chat/chat with message only (no agent_type)', async () => {
      const mockChatResponse: ChatResponse = {
        response: 'Here is your workout plan for today.',
        agent_type: 'conversational_assistant',
        conversation_id: 'conv-123',
        tools_used: ['get_workout_plan'],
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await chatService.sendMessage('What should I do today?');

      expect(api.post).toHaveBeenCalledWith('/chat/chat', {
        message: 'What should I do today?',
      });
      expect(api.post).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockChatResponse);
      expect(result.conversation_id).toBe('conv-123');
    });

    it('should send message without agent_type when not specified', async () => {
      const mockChatResponse: ChatResponse = {
        response: 'I can help you with that.',
        agent_type: 'conversational_assistant',
        conversation_id: 'conv-456',
        tools_used: [],
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await chatService.sendMessage('Hello');

      expect(api.post).toHaveBeenCalledWith('/chat/chat', {
        message: 'Hello',
      });
      expect(result.agent_type).toBe('conversational_assistant');
    });

    it('should return conversation_id from response', async () => {
      const mockChatResponse: ChatResponse = {
        response: 'Your meal plan is ready.',
        agent_type: 'conversational_assistant',
        conversation_id: 'conv-789',
        tools_used: ['get_meal_plan', 'get_dishes'],
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await chatService.sendMessage('Show me my meal plan');

      expect(result.conversation_id).toBe('conv-789');
      expect(result.tools_used).toEqual(['get_meal_plan', 'get_dishes']);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(
        chatService.sendMessage('Test message')
      ).rejects.toThrow('Network error');
      expect(api.post).toHaveBeenCalledWith('/chat/chat', {
        message: 'Test message',
      });
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(chatService.sendMessage('Test message')).rejects.toThrow();
      expect(api.post).toHaveBeenCalledWith('/chat/chat', {
        message: 'Test message',
      });
    });

    it('should handle empty message', async () => {
      const mockChatResponse: ChatResponse = {
        response: 'Please provide a message.',
        agent_type: 'conversational_assistant',
        conversation_id: 'conv-empty',
        tools_used: [],
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await chatService.sendMessage('');

      expect(api.post).toHaveBeenCalledWith('/chat/chat', {
        message: '',
      });
      expect(result).toEqual(mockChatResponse);
    });

    it('should throw structured error for 403 with ONBOARDING_REQUIRED', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            detail: {
              error_code: 'ONBOARDING_REQUIRED',
              message: 'Complete onboarding to access chat',
              redirect: '/onboarding',
            },
          },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      try {
        await chatService.sendMessage('Test message');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.status).toBe(403);
        expect(error.code).toBe('ONBOARDING_REQUIRED');
        expect(error.message).toBe('Complete onboarding to access chat');
        expect(error.redirect).toBe('/onboarding');
      }
    });

    it('should throw structured error for 403 without error_code', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            detail: {
              message: 'Access forbidden',
            },
          },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      try {
        await chatService.sendMessage('Test message');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.status).toBe(403);
        expect(error.code).toBeUndefined();
        expect(error.message).toBe('Access forbidden');
      }
    });

    it('should throw structured error for 403 with all error details', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            detail: {
              error_code: 'ONBOARDING_REQUIRED',
              message: 'You must complete onboarding first',
              redirect: '/onboarding',
            },
          },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      try {
        await chatService.sendMessage('Test message');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error).toHaveProperty('status', 403);
        expect(error).toHaveProperty('code', 'ONBOARDING_REQUIRED');
        expect(error).toHaveProperty('message', 'You must complete onboarding first');
        expect(error).toHaveProperty('redirect', '/onboarding');
      }
    });

    it('should use default message when detail.message is missing', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            detail: {
              error_code: 'FORBIDDEN',
            },
          },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      try {
        await chatService.sendMessage('Test message');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.status).toBe(403);
        expect(error.code).toBe('FORBIDDEN');
        expect(error.message).toBe('Access forbidden');
        expect(error.redirect).toBeUndefined();
      }
    });

    it('should handle 403 error with empty detail object', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            detail: {},
          },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      try {
        await chatService.sendMessage('Test message');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.status).toBe(403);
        expect(error.code).toBeUndefined();
        expect(error.message).toBe('Access forbidden');
        expect(error.redirect).toBeUndefined();
      }
    });

    it('should handle 403 error without detail object', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {},
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      try {
        await chatService.sendMessage('Test message');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.status).toBe(403);
        expect(error.code).toBeUndefined();
        expect(error.message).toBe('Access forbidden');
        expect(error.redirect).toBeUndefined();
      }
    });

    it('should preserve redirect URL in structured error', async () => {
      const mockError = {
        response: {
          status: 403,
          data: {
            detail: {
              error_code: 'ONBOARDING_REQUIRED',
              message: 'Complete onboarding to continue',
              redirect: '/onboarding?from=chat',
            },
          },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      try {
        await chatService.sendMessage('Test message');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.redirect).toBe('/onboarding?from=chat');
      }
    });

    it('should not modify non-403 errors', async () => {
      const mockError = {
        response: {
          status: 500,
          data: {
            detail: 'Internal server error',
          },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      try {
        await chatService.sendMessage('Test message');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        // Non-403 errors should be thrown as-is
        expect(error.response.status).toBe(500);
        expect(error.response.data.detail).toBe('Internal server error');
        // Should not have structured error properties
        expect(error.status).toBeUndefined();
        expect(error.code).toBeUndefined();
      }
    });

    it('should not modify network errors without response', async () => {
      const mockError = new Error('Network connection failed');
      vi.mocked(api.post).mockRejectedValue(mockError);

      try {
        await chatService.sendMessage('Test message');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        // Network errors should be thrown as-is
        expect(error.message).toBe('Network connection failed');
        expect(error.status).toBeUndefined();
        expect(error.code).toBeUndefined();
      }
    });
  });

  describe('getHistory', () => {
    it('should call GET /chat/history with limit parameter', async () => {
      const mockHistoryResponse: ChatHistoryResponse = {
        messages: [
          {
            role: 'user',
            content: 'What should I eat?',
            agent_type: null,
            created_at: '2024-01-15T10:00:00Z',
          },
          {
            role: 'assistant',
            content: 'Here are some meal suggestions.',
            agent_type: 'diet_planning',
            created_at: '2024-01-15T10:00:05Z',
          },
        ],
        total: 2,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockHistoryResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await chatService.getHistory(20);

      expect(api.get).toHaveBeenCalledWith('/chat/history', {
        params: { limit: 20 },
      });
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockHistoryResponse);
      expect(result.messages).toHaveLength(2);
      expect(result.total).toBe(2);
    });

    it('should use default limit of 50 when not specified', async () => {
      const mockHistoryResponse: ChatHistoryResponse = {
        messages: [],
        total: 0,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockHistoryResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await chatService.getHistory();

      expect(api.get).toHaveBeenCalledWith('/chat/history', {
        params: { limit: 50 },
      });
      expect(result.messages).toHaveLength(0);
    });

    it('should return empty history when no messages exist', async () => {
      const mockHistoryResponse: ChatHistoryResponse = {
        messages: [],
        total: 0,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockHistoryResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await chatService.getHistory(10);

      expect(result.messages).toEqual([]);
      expect(result.total).toBe(0);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(chatService.getHistory(10)).rejects.toThrow('Network error');
      expect(api.get).toHaveBeenCalledWith('/chat/history', {
        params: { limit: 10 },
      });
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(chatService.getHistory()).rejects.toThrow();
      expect(api.get).toHaveBeenCalledWith('/chat/history', {
        params: { limit: 50 },
      });
    });

    it('should handle large history with pagination', async () => {
      const mockHistoryResponse: ChatHistoryResponse = {
        messages: Array(100)
          .fill(null)
          .map((_, i) => ({
            role: i % 2 === 0 ? 'user' : 'assistant',
            content: `Message ${i}`,
            agent_type: i % 2 === 0 ? null : 'conversational_assistant',
            created_at: `2024-01-15T10:${String(i).padStart(2, '0')}:00Z`,
          })),
        total: 500,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockHistoryResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await chatService.getHistory(100);

      expect(result.messages).toHaveLength(100);
      expect(result.total).toBe(500);
    });
  });

  describe('clearHistory', () => {
    it('should call DELETE /chat/history and return success status', async () => {
      const mockResponse = { status: 'success' };

      vi.mocked(api.delete).mockResolvedValue({
        data: mockResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await chatService.clearHistory();

      expect(api.delete).toHaveBeenCalledWith('/chat/history');
      expect(api.delete).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockResponse);
      expect(result.status).toBe('success');
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.delete).mockRejectedValue(mockError);

      await expect(chatService.clearHistory()).rejects.toThrow('Network error');
      expect(api.delete).toHaveBeenCalledWith('/chat/history');
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.delete).mockRejectedValue(mockError);

      await expect(chatService.clearHistory()).rejects.toThrow();
      expect(api.delete).toHaveBeenCalledWith('/chat/history');
    });

    it('should throw error when server error occurs (500)', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };
      vi.mocked(api.delete).mockRejectedValue(mockError);

      await expect(chatService.clearHistory()).rejects.toThrow();
      expect(api.delete).toHaveBeenCalledWith('/chat/history');
    });
  });

  describe('streamMessage', () => {
    let mockEventSource: any;

    beforeEach(() => {
      // Mock EventSource as a constructor function
      mockEventSource = {
        onmessage: null,
        onerror: null,
        close: vi.fn(),
      };
      
      // Create a proper constructor mock
      (globalThis as any).EventSource = vi.fn(function (this: any, url: string) {
        return mockEventSource;
      });
      
      localStorage.setItem('auth_token', 'test-token-123');
    });

    it('should create EventSource with correct URL and query params (no agent_type)', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage(
        'Tell me about protein',
        onChunk,
        onComplete,
        onError
      );

      expect(globalThis.EventSource).toHaveBeenCalledTimes(1);
      const calledUrl = (globalThis.EventSource as any).mock.calls[0][0];
      expect(calledUrl).toContain('/chat/stream');
      expect(calledUrl).toContain('message=Tell');
      expect(calledUrl).toContain('protein');
      expect(calledUrl).not.toContain('agent_type=');
      expect(calledUrl).toContain('token=test-token-123');
    });

    it('should handle chunk messages correctly', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage(
        'Test message',
        onChunk,
        onComplete,
        onError
      );

      // Simulate receiving a chunk
      const chunkEvent = {
        data: JSON.stringify({ chunk: 'Here is your workout' }),
      };
      mockEventSource.onmessage(chunkEvent);

      expect(onChunk).toHaveBeenCalledWith('Here is your workout');
      expect(onChunk).toHaveBeenCalledTimes(1);
      expect(onComplete).not.toHaveBeenCalled();
      expect(onError).not.toHaveBeenCalled();
    });

    it('should handle completion message correctly', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage(
        'Test message',
        onChunk,
        onComplete,
        onError
      );

      // Simulate completion
      const doneEvent = {
        data: JSON.stringify({ done: true, agent_type: 'conversational_assistant' }),
      };
      mockEventSource.onmessage(doneEvent);

      expect(onComplete).toHaveBeenCalledWith('conversational_assistant');
      expect(onComplete).toHaveBeenCalledTimes(1);
      expect(mockEventSource.close).toHaveBeenCalled();
      expect(onChunk).not.toHaveBeenCalled();
    });

    it('should handle error messages from stream', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage(
        'Test message',
        onChunk,
        onComplete,
        onError
      );

      // Simulate error in stream data
      const errorEvent = {
        data: JSON.stringify({ error: 'Agent not available' }),
      };
      mockEventSource.onmessage(errorEvent);

      expect(onError).toHaveBeenCalledWith(new Error('Agent not available'));
      expect(onError).toHaveBeenCalledTimes(1);
      expect(mockEventSource.close).toHaveBeenCalled();
      expect(onChunk).not.toHaveBeenCalled();
      expect(onComplete).not.toHaveBeenCalled();
    });

    it('should handle malformed JSON in stream', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage(
        'Test message',
        onChunk,
        onComplete,
        onError
      );

      // Simulate malformed JSON
      const malformedEvent = {
        data: 'not valid json',
      };
      mockEventSource.onmessage(malformedEvent);

      expect(onError).toHaveBeenCalledWith(new Error('Failed to parse stream data'));
      expect(mockEventSource.close).toHaveBeenCalled();
    });

    it('should handle EventSource connection errors', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage(
        'Test message',
        onChunk,
        onComplete,
        onError
      );

      // Simulate connection error
      mockEventSource.onerror();

      expect(onError).toHaveBeenCalledWith(new Error('Stream connection failed'));
      expect(mockEventSource.close).toHaveBeenCalled();
    });

    it('should work without agent_type', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage('Test message', onChunk, onComplete, onError);

      const calledUrl = (globalThis.EventSource as any).mock.calls[0][0];
      expect(calledUrl).toContain('message=Test');
      expect(calledUrl).toContain('message');
      expect(calledUrl).not.toContain('agent_type=');
    });

    it('should work without auth token', () => {
      localStorage.clear();

      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage(
        'Test message',
        onChunk,
        onComplete,
        onError
      );

      const calledUrl = (globalThis.EventSource as any).mock.calls[0][0];
      expect(calledUrl).not.toContain('token=');
    });

    it('should return EventSource instance', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      const eventSource = chatService.streamMessage(
        'Test message',
        onChunk,
        onComplete,
        onError
      );

      expect(eventSource).toBe(mockEventSource);
      expect(eventSource.close).toBeDefined();
    });
  });
});
