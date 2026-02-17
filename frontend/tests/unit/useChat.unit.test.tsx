import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { useChat } from '../../src/hooks/useChat';
import { chatService } from '../../src/services/chatService';
import type { ReactNode } from 'react';

// Mock the chat service
vi.mock('../../src/services/chatService', () => ({
  chatService: {
    sendMessage: vi.fn(),
    getHistory: vi.fn(),
    streamMessage: vi.fn(),
    cancelStream: vi.fn(),
  },
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: vi.fn(() => vi.fn()),
  };
});

describe('useChat Hook Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(chatService.getHistory).mockResolvedValue({
      messages: [],
      total: 0,
    });
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <MemoryRouter>{children}</MemoryRouter>
  );

  describe('Streaming Functionality', () => {
    it('should add user message immediately on send', async () => {
      const mockCancel = vi.fn();
      vi.mocked(chatService.streamMessage).mockReturnValue(mockCancel);

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('Hello');
      });

      // User message should be added immediately (Requirement 3.1)
      await waitFor(() => {
        expect(result.current.messages.length).toBe(2); // user + placeholder
        expect(result.current.messages[0].role).toBe('user');
        expect(result.current.messages[0].content).toBe('Hello');
      });
    });

    it('should create placeholder assistant message with isStreaming: true', async () => {
      const mockCancel = vi.fn();
      vi.mocked(chatService.streamMessage).mockReturnValue(mockCancel);

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('Test');
      });

      // Placeholder should be created with isStreaming: true (Requirement 3.2)
      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
        const assistantMsg = result.current.messages[1];
        expect(assistantMsg.role).toBe('assistant');
        expect(assistantMsg.content).toBe('');
        expect(assistantMsg.isStreaming).toBe(true);
      });
    });

    it('should append chunks to placeholder message correctly', async () => {
      let onChunkCallback: ((chunk: string) => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
        onChunkCallback = callbacks.onChunk;
        return vi.fn();
      });

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('Test');
      });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
      });

      // Simulate receiving chunks (Requirement 3.3)
      act(() => {
        onChunkCallback?.('Hello ');
      });

      await waitFor(() => {
        expect(result.current.messages[1].content).toBe('Hello ');
      });

      act(() => {
        onChunkCallback?.('world');
      });

      await waitFor(() => {
        expect(result.current.messages[1].content).toBe('Hello world');
      });

      act(() => {
        onChunkCallback?.('!');
      });

      await waitFor(() => {
        expect(result.current.messages[1].content).toBe('Hello world!');
      });
    });

    it('should set isStreaming: false on completion', async () => {
      let onCompleteCallback: ((agentType?: string) => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
        onCompleteCallback = callbacks.onComplete;
        return vi.fn();
      });

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('Test');
      });

      await waitFor(() => {
        expect(result.current.messages[1].isStreaming).toBe(true);
      });

      // Simulate completion (Requirement 3.4)
      act(() => {
        onCompleteCallback?.('general_assistant');
      });

      await waitFor(() => {
        expect(result.current.messages[1].isStreaming).toBe(false);
        expect(result.current.isStreaming).toBe(false);
      });
    });

    it('should set error state on streaming failure', async () => {
      let onErrorCallback: ((error: string) => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
        onErrorCallback = callbacks.onError;
        return vi.fn();
      });

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('Test');
      });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
      });

      // Simulate error (Requirement 3.5)
      act(() => {
        onErrorCallback?.('Connection error');
      });

      await waitFor(() => {
        expect(result.current.messages[1].error).toBe('Connection error');
        expect(result.current.messages[1].isStreaming).toBe(false);
        expect(result.current.error).toBe('Connection error');
        expect(result.current.isStreaming).toBe(false);
      });
    });

    it('should prevent sending new messages while streaming', async () => {
      const mockCancel = vi.fn();
      vi.mocked(chatService.streamMessage).mockReturnValue(mockCancel);

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      // Send first message
      act(() => {
        result.current.sendMessage('First message');
      });

      await waitFor(() => {
        expect(result.current.isStreaming).toBe(true);
      });

      const messageCountAfterFirst = result.current.messages.length;

      // Try to send second message while streaming (Requirement 3.6)
      act(() => {
        result.current.sendMessage('Second message');
      });

      // Message count should not increase
      await waitFor(() => {
        expect(result.current.messages.length).toBe(messageCountAfterFirst);
      });

      // streamMessage should only be called once
      expect(chatService.streamMessage).toHaveBeenCalledTimes(1);
    });

    it('should pass isOnboarding parameter to streamMessage', async () => {
      const mockCancel = vi.fn();
      vi.mocked(chatService.streamMessage).mockReturnValue(mockCancel);

      const { result } = renderHook(() => useChat(true), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('Test');
      });

      await waitFor(() => {
        expect(chatService.streamMessage).toHaveBeenCalledWith(
          'Test',
          expect.any(Object),
          true // isOnboarding
        );
      });
    });
  });

  describe('Retry Functionality', () => {
    it('should retry last message on retryLastMessage call', async () => {
      let onErrorCallback: ((error: string) => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
        onErrorCallback = callbacks.onError;
        return vi.fn();
      });

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      // Send message that will fail
      act(() => {
        result.current.sendMessage('Test message');
      });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
      });

      // Simulate error
      act(() => {
        onErrorCallback?.('Network error');
      });

      await waitFor(() => {
        expect(result.current.messages[1].error).toBe('Network error');
      });

      // Clear the mock to track new calls
      vi.mocked(chatService.streamMessage).mockClear();

      // Retry (Requirement 6.2)
      act(() => {
        result.current.retryLastMessage();
      });

      await waitFor(() => {
        // Should remove failed message and resend
        expect(chatService.streamMessage).toHaveBeenCalledWith(
          'Test message',
          expect.any(Object),
          false
        );
      });
    });

    it('should find last user message correctly', async () => {
      let onChunkCallback: ((chunk: string) => void) | null = null;
      let onCompleteCallback: ((agentType?: string) => void) | null = null;
      let onErrorCallback: ((error: string) => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
        onChunkCallback = callbacks.onChunk;
        onCompleteCallback = callbacks.onComplete;
        onErrorCallback = callbacks.onError;
        return vi.fn();
      });

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      // Send first message
      act(() => {
        result.current.sendMessage('First');
      });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
      });

      // Complete first message
      act(() => {
        onChunkCallback?.('Response 1');
        onCompleteCallback?.();
      });

      await waitFor(() => {
        expect(result.current.isStreaming).toBe(false);
      });

      // Send second message
      act(() => {
        result.current.sendMessage('Second');
      });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(4);
      });

      // Fail second message
      act(() => {
        onErrorCallback?.('Error');
      });

      await waitFor(() => {
        expect(result.current.messages[3].error).toBe('Error');
      });

      vi.mocked(chatService.streamMessage).mockClear();

      // Retry should use "Second" (last user message)
      act(() => {
        result.current.retryLastMessage();
      });

      await waitFor(() => {
        expect(chatService.streamMessage).toHaveBeenCalledWith(
          'Second',
          expect.any(Object),
          false
        );
      });
    });
  });

  describe('Cleanup on Unmount', () => {
    it('should cancel active stream on unmount', async () => {
      const mockCancel = vi.fn();
      vi.mocked(chatService.streamMessage).mockReturnValue(mockCancel);

      const { result, unmount } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('Test');
      });

      await waitFor(() => {
        expect(result.current.isStreaming).toBe(true);
      });

      // Unmount component (Requirements 7.1, 7.2)
      unmount();

      // Cancel function should be called
      expect(mockCancel).toHaveBeenCalled();
    });

    it('should not error if no active stream on unmount', () => {
      const { unmount } = renderHook(() => useChat(false), { wrapper });

      // Should not throw error
      expect(() => unmount()).not.toThrow();
    });
  });

  describe('Edge Cases', () => {
    it('should not send empty messages', async () => {
      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('');
      });

      act(() => {
        result.current.sendMessage('   ');
      });

      // No messages should be sent
      expect(chatService.streamMessage).not.toHaveBeenCalled();
      expect(result.current.messages.length).toBe(0);
    });

    it('should handle rapid chunk updates', async () => {
      let onChunkCallback: ((chunk: string) => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
        onChunkCallback = callbacks.onChunk;
        return vi.fn();
      });

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('Test');
      });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
      });

      // Send many chunks rapidly
      act(() => {
        for (let i = 0; i < 100; i++) {
          onChunkCallback?.(`${i} `);
        }
      });

      await waitFor(() => {
        const content = result.current.messages[1].content;
        expect(content).toContain('0 ');
        expect(content).toContain('99 ');
      });
    });

    it('should preserve message history during streaming', async () => {
      let onChunkCallback: ((chunk: string) => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
        onChunkCallback = callbacks.onChunk;
        return vi.fn();
      });

      // Mock history with existing messages
      vi.mocked(chatService.getHistory).mockResolvedValue({
        messages: [
          {
            role: 'user',
            content: 'Previous message',
            agent_type: 'general_assistant',
            created_at: '2024-01-01T09:00:00Z',
          },
        ],
        total: 1,
      });

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(1);
      });

      act(() => {
        result.current.sendMessage('New message');
      });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(3); // history + user + assistant
      });

      act(() => {
        onChunkCallback?.('Response');
      });

      await waitFor(() => {
        // All messages should be preserved
        expect(result.current.messages.length).toBe(3);
        expect(result.current.messages[0].content).toBe('Previous message');
        expect(result.current.messages[1].content).toBe('New message');
        expect(result.current.messages[2].content).toBe('Response');
      });
    });
  });

  describe('Clear Messages', () => {
    it('should clear all messages and reset state', async () => {
      let onChunkCallback: ((chunk: string) => void) | null = null;
      let onCompleteCallback: ((agentType?: string) => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
        onChunkCallback = callbacks.onChunk;
        onCompleteCallback = callbacks.onComplete;
        return vi.fn();
      });

      const { result } = renderHook(() => useChat(false), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      act(() => {
        result.current.sendMessage('Test');
      });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
      });

      act(() => {
        onChunkCallback?.('Response');
        onCompleteCallback?.();
      });

      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
      });

      act(() => {
        result.current.clearMessages();
      });

      expect(result.current.messages).toEqual([]);
      expect(result.current.conversationId).toBeNull();
      expect(result.current.error).toBeNull();
    });
  });
});
