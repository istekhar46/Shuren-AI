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

    it('should create EventSource with correct URL and token for regular chat', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Tell me about protein', callbacks, false);

      expect(globalThis.EventSource).toHaveBeenCalledTimes(1);
      const calledUrl = (globalThis.EventSource as any).mock.calls[0][0];
      expect(calledUrl).toContain('/chat/stream');
      expect(calledUrl).toContain('message=Tell');
      expect(calledUrl).toContain('protein');
      expect(calledUrl).toContain('token=test-token-123');
    });

    it('should create EventSource with onboarding endpoint when isOnboarding is true', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Tell me about protein', callbacks, true);

      expect(globalThis.EventSource).toHaveBeenCalledTimes(1);
      const calledUrl = (globalThis.EventSource as any).mock.calls[0][0];
      expect(calledUrl).toContain('/chat/onboarding-stream');
      expect(calledUrl).toContain('message=Tell');
      expect(calledUrl).toContain('token=test-token-123');
    });

    it('should handle chunk messages correctly', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);

      // Simulate receiving a chunk
      const chunkEvent = {
        data: JSON.stringify({ chunk: 'Here is your workout' }),
      };
      mockEventSource.onmessage(chunkEvent);

      expect(callbacks.onChunk).toHaveBeenCalledWith('Here is your workout');
      expect(callbacks.onChunk).toHaveBeenCalledTimes(1);
      expect(callbacks.onComplete).not.toHaveBeenCalled();
      expect(callbacks.onError).not.toHaveBeenCalled();
    });

    it('should handle completion message correctly', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);

      // Simulate completion
      const doneEvent = {
        data: JSON.stringify({ done: true, agent_type: 'conversational_assistant' }),
      };
      mockEventSource.onmessage(doneEvent);

      expect(callbacks.onComplete).toHaveBeenCalledWith('conversational_assistant');
      expect(callbacks.onComplete).toHaveBeenCalledTimes(1);
      expect(mockEventSource.close).toHaveBeenCalled();
      expect(callbacks.onChunk).not.toHaveBeenCalled();
    });

    it('should handle error messages from stream', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);

      // Simulate error in stream data
      const errorEvent = {
        data: JSON.stringify({ error: 'Agent not available' }),
      };
      mockEventSource.onmessage(errorEvent);

      expect(callbacks.onError).toHaveBeenCalledWith('Agent not available');
      expect(callbacks.onError).toHaveBeenCalledTimes(1);
      expect(mockEventSource.close).toHaveBeenCalled();
      expect(callbacks.onChunk).not.toHaveBeenCalled();
      expect(callbacks.onComplete).not.toHaveBeenCalled();
    });

    it('should handle malformed JSON in stream', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);

      // Simulate malformed JSON
      const malformedEvent = {
        data: 'not valid json',
      };
      mockEventSource.onmessage(malformedEvent);

      expect(callbacks.onError).toHaveBeenCalledWith('Failed to parse response');
      expect(mockEventSource.close).toHaveBeenCalled();
    });

    it('should handle EventSource connection errors', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);

      // Simulate connection error
      mockEventSource.onerror();

      expect(callbacks.onError).toHaveBeenCalledWith('Connection error');
      expect(mockEventSource.close).toHaveBeenCalled();
    });

    it('should work without auth token', () => {
      localStorage.clear();

      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);

      const calledUrl = (globalThis.EventSource as any).mock.calls[0][0];
      expect(calledUrl).not.toContain('token=');
    });

    it('should return cancellation function', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      const cancelFn = chatService.streamMessage('Test message', callbacks);

      expect(typeof cancelFn).toBe('function');
      
      // Call cancellation function
      cancelFn();
      
      expect(mockEventSource.close).toHaveBeenCalled();
    });

    it('should handle cancellation via returned function', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      const cancelFn = chatService.streamMessage('Test message', callbacks);
      
      // Cancel the stream
      cancelFn();

      expect(mockEventSource.close).toHaveBeenCalledTimes(1);
    });

    it('should handle multiple chunk messages', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);

      // Simulate multiple chunks
      mockEventSource.onmessage({ data: JSON.stringify({ chunk: 'First ' }) });
      mockEventSource.onmessage({ data: JSON.stringify({ chunk: 'second ' }) });
      mockEventSource.onmessage({ data: JSON.stringify({ chunk: 'third' }) });

      expect(callbacks.onChunk).toHaveBeenCalledTimes(3);
      expect(callbacks.onChunk).toHaveBeenNthCalledWith(1, 'First ');
      expect(callbacks.onChunk).toHaveBeenNthCalledWith(2, 'second ');
      expect(callbacks.onChunk).toHaveBeenNthCalledWith(3, 'third');
    });

    it('should close connection on error and set activeStream to null', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);

      // Simulate error
      const errorEvent = {
        data: JSON.stringify({ error: 'Test error' }),
      };
      mockEventSource.onmessage(errorEvent);

      expect(mockEventSource.close).toHaveBeenCalled();
      expect(callbacks.onError).toHaveBeenCalledWith('Test error');
    });

    it('should close connection on completion and set activeStream to null', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);

      // Simulate completion
      const doneEvent = {
        data: JSON.stringify({ done: true, agent_type: 'test_agent' }),
      };
      mockEventSource.onmessage(doneEvent);

      expect(mockEventSource.close).toHaveBeenCalled();
      expect(callbacks.onComplete).toHaveBeenCalledWith('test_agent');
    });
  });

  describe('cancelStream', () => {
    let mockEventSource: any;

    beforeEach(() => {
      mockEventSource = {
        onmessage: null,
        onerror: null,
        close: vi.fn(),
      };
      
      (globalThis as any).EventSource = vi.fn(function (this: any, url: string) {
        return mockEventSource;
      });
      
      localStorage.setItem('auth_token', 'test-token-123');
    });

    it('should close active stream when called', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      // Start a stream
      chatService.streamMessage('Test message', callbacks);

      // Cancel the stream
      chatService.cancelStream();

      expect(mockEventSource.close).toHaveBeenCalled();
    });

    it('should be safe to call when no stream is active', () => {
      // Should not throw error
      expect(() => chatService.cancelStream()).not.toThrow();
    });

    it('should be safe to call multiple times', () => {
      const callbacks = {
        onChunk: vi.fn(),
        onComplete: vi.fn(),
        onError: vi.fn(),
      };

      chatService.streamMessage('Test message', callbacks);
      
      chatService.cancelStream();
      chatService.cancelStream();
      chatService.cancelStream();

      // Should only close once (subsequent calls do nothing)
      expect(mockEventSource.close).toHaveBeenCalledTimes(1);
    });
  });
});
