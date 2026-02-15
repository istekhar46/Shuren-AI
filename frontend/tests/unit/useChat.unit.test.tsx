import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { useChat } from '../../src/hooks/useChat';
import { chatService } from '../../src/services/chatService';
import { AxiosError } from 'axios';
import type { ReactNode } from 'react';

// Mock the chat service
vi.mock('../../src/services/chatService', () => ({
  chatService: {
    sendMessage: vi.fn(),
    getHistory: vi.fn(),
  },
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: vi.fn(),
  };
});

describe('useChat Hook Unit Tests', () => {
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);
    vi.mocked(chatService.getHistory).mockResolvedValue({
      messages: [],
      total: 0,
    });
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <MemoryRouter>{children}</MemoryRouter>
  );

  describe('403 Error Handling', () => {
    it('should redirect to /onboarding on 403 error with ONBOARDING_REQUIRED code', async () => {
      const mockError = new AxiosError(
        'Request failed with status code 403',
        '403',
        undefined,
        undefined,
        {
          status: 403,
          statusText: 'Forbidden',
          data: {
            detail: {
              error_code: 'ONBOARDING_REQUIRED',
              message: 'Complete onboarding to access this feature',
              redirect: '/onboarding',
            },
          },
          headers: {},
          config: {} as any,
        }
      );

      vi.mocked(chatService.sendMessage).mockRejectedValue(mockError);

      const { result } = renderHook(() => useChat(), { wrapper });

      // Wait for initial history load
      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      // Send a message
      await result.current.sendMessage('Test message');

      // Wait for error handling
      await waitFor(() => {
        expect(result.current.error).toBe('Complete onboarding to access this feature');
      });

      // Verify navigation was called
      expect(mockNavigate).toHaveBeenCalledWith('/onboarding');
    });

    it('should display error message from backend on 403 with ONBOARDING_REQUIRED', async () => {
      const mockError = new AxiosError(
        'Request failed with status code 403',
        '403',
        undefined,
        undefined,
        {
          status: 403,
          statusText: 'Forbidden',
          data: {
            detail: {
              error_code: 'ONBOARDING_REQUIRED',
              message: 'Complete onboarding to access this feature',
              redirect: '/onboarding',
            },
          },
          headers: {},
          config: {} as any,
        }
      );

      vi.mocked(chatService.sendMessage).mockRejectedValue(mockError);

      const { result } = renderHook(() => useChat(), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      await result.current.sendMessage('Test message');

      await waitFor(() => {
        expect(result.current.error).toBe('Complete onboarding to access this feature');
      });
    });

    it('should use default error message if backend message is missing', async () => {
      const mockError = new AxiosError(
        'Request failed with status code 403',
        '403',
        undefined,
        undefined,
        {
          status: 403,
          statusText: 'Forbidden',
          data: {
            detail: {
              error_code: 'ONBOARDING_REQUIRED',
              redirect: '/onboarding',
            },
          },
          headers: {},
          config: {} as any,
        }
      );

      vi.mocked(chatService.sendMessage).mockRejectedValue(mockError);

      const { result } = renderHook(() => useChat(), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      await result.current.sendMessage('Test message');

      await waitFor(() => {
        expect(result.current.error).toBe('Complete onboarding to access this feature');
      });

      expect(mockNavigate).toHaveBeenCalledWith('/onboarding');
    });

    it('should remove optimistic user message on 403 error', async () => {
      const mockError = new AxiosError(
        'Request failed with status code 403',
        '403',
        undefined,
        undefined,
        {
          status: 403,
          statusText: 'Forbidden',
          data: {
            detail: {
              error_code: 'ONBOARDING_REQUIRED',
              message: 'Complete onboarding to access this feature',
              redirect: '/onboarding',
            },
          },
          headers: {},
          config: {} as any,
        }
      );

      vi.mocked(chatService.sendMessage).mockRejectedValue(mockError);

      const { result } = renderHook(() => useChat(), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      // Send message - should add optimistic message then remove it
      await result.current.sendMessage('Test message');

      await waitFor(() => {
        expect(result.current.error).toBe('Complete onboarding to access this feature');
      });

      // Verify optimistic message was removed
      expect(result.current.messages).toEqual([]);
    });

    it('should not redirect on 403 error without ONBOARDING_REQUIRED code', async () => {
      const mockError = new AxiosError(
        'Request failed with status code 403',
        '403',
        undefined,
        undefined,
        {
          status: 403,
          statusText: 'Forbidden',
          data: {
            detail: {
              error_code: 'FORBIDDEN',
              message: 'Access denied',
            },
          },
          headers: {},
          config: {} as any,
        }
      );

      vi.mocked(chatService.sendMessage).mockRejectedValue(mockError);

      const { result } = renderHook(() => useChat(), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      await result.current.sendMessage('Test message');

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      // Should not navigate for other 403 errors
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('should handle non-403 errors normally', async () => {
      const mockError = new Error('Network error');

      vi.mocked(chatService.sendMessage).mockRejectedValue(mockError);

      const { result } = renderHook(() => useChat(), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      await result.current.sendMessage('Test message');

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });

      // Should not navigate for non-403 errors
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Agent Selector Removal', () => {
    it('should send message without agent type parameter', async () => {
      const mockResponse = {
        message: 'Response from agent',
        agentType: 'general_assistant',
        conversationId: 'conv-123',
        timestamp: '2024-01-01T10:00:00Z',
      };

      vi.mocked(chatService.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat(), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      await result.current.sendMessage('Test message');

      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
      });

      // Verify sendMessage was called with message and undefined for agentType
      expect(chatService.sendMessage).toHaveBeenCalledWith('Test message', undefined);
    });
  });

  describe('General Functionality', () => {
    it('should load chat history on mount', async () => {
      const mockHistory = {
        messages: [
          {
            id: '1',
            role: 'user' as const,
            content: 'Previous message',
            timestamp: '2024-01-01T09:00:00Z',
          },
        ],
        total: 1,
      };

      vi.mocked(chatService.getHistory).mockResolvedValue(mockHistory);

      const { result } = renderHook(() => useChat(), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual(mockHistory.messages);
      });
    });

    it('should add user and agent messages on successful send', async () => {
      const mockResponse = {
        message: 'Agent response',
        agentType: 'general_assistant',
        conversationId: 'conv-123',
        timestamp: '2024-01-01T10:00:00Z',
      };

      vi.mocked(chatService.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat(), { wrapper });

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      await result.current.sendMessage('Hello');

      await waitFor(() => {
        expect(result.current.messages.length).toBe(2);
      });

      // Check user message
      expect(result.current.messages[0].role).toBe('user');
      expect(result.current.messages[0].content).toBe('Hello');

      // Check agent message
      expect(result.current.messages[1].role).toBe('assistant');
      expect(result.current.messages[1].content).toBe('Agent response');
    });

    it('should clear messages and conversation', () => {
      const { result } = renderHook(() => useChat(), { wrapper });

      result.current.clearMessages();

      expect(result.current.messages).toEqual([]);
      expect(result.current.conversationId).toBeNull();
      expect(result.current.error).toBeNull();
    });
  });
});
