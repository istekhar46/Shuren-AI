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
    it('should call POST /chat/chat with message and agent_type', async () => {
      const mockChatResponse: ChatResponse = {
        response: 'Here is your workout plan for today.',
        agent_type: 'workout_planning',
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

      const result = await chatService.sendMessage(
        'What should I do today?',
        'workout_planning'
      );

      expect(api.post).toHaveBeenCalledWith('/chat/chat', {
        message: 'What should I do today?',
        agent_type: 'workout_planning',
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
        agent_type: undefined,
      });
      expect(result.agent_type).toBe('conversational_assistant');
    });

    it('should return conversation_id from response', async () => {
      const mockChatResponse: ChatResponse = {
        response: 'Your meal plan is ready.',
        agent_type: 'diet_planning',
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

      const result = await chatService.sendMessage(
        'Show me my meal plan',
        'diet_planning'
      );

      expect(result.conversation_id).toBe('conv-789');
      expect(result.tools_used).toEqual(['get_meal_plan', 'get_dishes']);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(
        chatService.sendMessage('Test message', 'workout_planning')
      ).rejects.toThrow('Network error');
      expect(api.post).toHaveBeenCalledWith('/chat/chat', {
        message: 'Test message',
        agent_type: 'workout_planning',
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
        agent_type: undefined,
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
        agent_type: undefined,
      });
      expect(result).toEqual(mockChatResponse);
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

    it('should create EventSource with correct URL and query params', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage(
        'Tell me about protein',
        'diet_planning',
        onChunk,
        onComplete,
        onError
      );

      expect(globalThis.EventSource).toHaveBeenCalledTimes(1);
      const calledUrl = (globalThis.EventSource as any).mock.calls[0][0];
      expect(calledUrl).toContain('/chat/stream');
      expect(calledUrl).toContain('message=Tell');
      expect(calledUrl).toContain('protein');
      expect(calledUrl).toContain('agent_type=diet_planning');
      expect(calledUrl).toContain('token=test-token-123');
    });

    it('should handle chunk messages correctly', () => {
      const onChunk = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      chatService.streamMessage(
        'Test message',
        'workout_planning',
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
        'diet_planning',
        onChunk,
        onComplete,
        onError
      );

      // Simulate completion
      const doneEvent = {
        data: JSON.stringify({ done: true, agent_type: 'diet_planning' }),
      };
      mockEventSource.onmessage(doneEvent);

      expect(onComplete).toHaveBeenCalledWith('diet_planning');
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
        'workout_planning',
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
        'diet_planning',
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
        'workout_planning',
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

      chatService.streamMessage('Test message', undefined, onChunk, onComplete, onError);

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
        'diet_planning',
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
        'workout_planning',
        onChunk,
        onComplete,
        onError
      );

      expect(eventSource).toBe(mockEventSource);
      expect(eventSource.close).toBeDefined();
    });
  });
});
