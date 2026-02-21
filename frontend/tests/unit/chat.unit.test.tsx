import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AgentSelector } from '../../src/components/chat/AgentSelector';
import { MessageInput } from '../../src/components/chat/MessageInput';
import { MessageList } from '../../src/components/chat/MessageList';
import { ChatPage } from '../../src/pages/ChatPage';
import * as useChatModule from '../../src/hooks/useChat';
import type { AgentType, ChatMessage } from '../../src/types';

// Mock the chat service
vi.mock('../../src/services/chatService', () => ({
  chatService: {
    sendMessage: vi.fn(),
    getHistory: vi.fn(),
  },
}));

// Mock the useChat hook for ChatPage tests
vi.mock('../../src/hooks/useChat');

describe('Chat Components Unit Tests', () => {
  describe('AgentSelector', () => {
    it('should render with default value', () => {
      const onChange = vi.fn();
      render(<AgentSelector value="general_assistant" onChange={onChange} />);

      const select = screen.getByLabelText('Select AI Agent');
      expect(select).toBeInTheDocument();
      expect(select).toHaveValue('general_assistant');
    });

    it('should call onChange when agent is selected', async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      render(<AgentSelector value="general_assistant" onChange={onChange} />);

      const select = screen.getByLabelText('Select AI Agent');
      await user.selectOptions(select, 'workout_planning');

      expect(onChange).toHaveBeenCalledWith('workout_planning');
    });

    it('should display all agent options', () => {
      const onChange = vi.fn();
      render(<AgentSelector value="general_assistant" onChange={onChange} />);

      const options = screen.getAllByRole('option');
      expect(options).toHaveLength(6);

      // Check that all expected options are present by their values
      expect(screen.getByRole('option', { name: /General Assistant/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Workout Planning/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Diet Planning/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Supplement Guidance/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Tracking & Adjustment/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Scheduling & Reminder/i })).toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      const onChange = vi.fn();
      render(<AgentSelector value="general_assistant" onChange={onChange} disabled />);

      const select = screen.getByLabelText('Select AI Agent');
      expect(select).toBeDisabled();
    });

    it('should not call onChange when disabled', async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      render(<AgentSelector value="general_assistant" onChange={onChange} disabled />);

      const select = screen.getByLabelText('Select AI Agent');
      
      // Attempt to change selection
      await user.click(select);
      
      expect(onChange).not.toHaveBeenCalled();
    });
  });

  describe('MessageInput', () => {
    it('should render textarea and send button', () => {
      const onSend = vi.fn();
      render(<MessageInput onSend={onSend} />);

      expect(screen.getByPlaceholderText(/Type your message/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    it('should call onSend when send button is clicked', async () => {
      const onSend = vi.fn();
      const user = userEvent.setup();
      render(<MessageInput onSend={onSend} />);

      const textarea = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(textarea, 'Hello, agent!');
      await user.click(sendButton);

      expect(onSend).toHaveBeenCalledWith('Hello, agent!');
    });

    it('should clear input after sending message', async () => {
      const onSend = vi.fn();
      const user = userEvent.setup();
      render(<MessageInput onSend={onSend} />);

      const textarea = screen.getByPlaceholderText(/Type your message/i) as HTMLTextAreaElement;

      await user.type(textarea, 'Test message');
      await user.click(screen.getByRole('button', { name: /send/i }));

      expect(textarea.value).toBe('');
    });

    it('should send message on Enter key press', async () => {
      const onSend = vi.fn();
      const user = userEvent.setup();
      render(<MessageInput onSend={onSend} />);

      const textarea = screen.getByPlaceholderText(/Type your message/i);

      await user.type(textarea, 'Test message{Enter}');

      expect(onSend).toHaveBeenCalledWith('Test message');
    });

    it('should not send message on Shift+Enter', async () => {
      const onSend = vi.fn();
      const user = userEvent.setup();
      render(<MessageInput onSend={onSend} />);

      const textarea = screen.getByPlaceholderText(/Type your message/i);

      await user.type(textarea, 'Line 1{Shift>}{Enter}{/Shift}Line 2');

      expect(onSend).not.toHaveBeenCalled();
    });

    it('should not send empty or whitespace-only messages', async () => {
      const onSend = vi.fn();
      const user = userEvent.setup();
      render(<MessageInput onSend={onSend} />);

      const sendButton = screen.getByRole('button', { name: /send/i });

      // Try to send empty message
      await user.click(sendButton);
      expect(onSend).not.toHaveBeenCalled();

      // Try to send whitespace-only message
      const textarea = screen.getByPlaceholderText(/Type your message/i);
      await user.type(textarea, '   ');
      await user.click(sendButton);
      expect(onSend).not.toHaveBeenCalled();
    });

    it('should disable input and button when disabled prop is true', () => {
      const onSend = vi.fn();
      render(<MessageInput onSend={onSend} disabled />);

      const textarea = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      expect(textarea).toBeDisabled();
      expect(sendButton).toBeDisabled();
    });

    it('should not send message when disabled', async () => {
      const onSend = vi.fn();
      const user = userEvent.setup();
      render(<MessageInput onSend={onSend} disabled />);

      const textarea = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      // Try to type (should not work)
      await user.type(textarea, 'Test');
      await user.click(sendButton);

      expect(onSend).not.toHaveBeenCalled();
    });
  });

  describe('MessageList', () => {
    const mockMessages: ChatMessage[] = [
      {
        id: '1',
        role: 'user',
        content: 'Hello, how are you?',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
      },
      {
        id: '2',
        role: 'assistant',
        content: 'I am doing well, thank you!',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:05Z',
      },
      {
        id: '3',
        role: 'user',
        content: 'Can you help me with my workout?',
        agentType: 'workout_planning',
        timestamp: '2024-01-01T10:01:00Z',
      },
    ];

    beforeEach(() => {
      // Mock scrollIntoView
      Element.prototype.scrollIntoView = vi.fn();
      // Mock setTimeout for debouncing tests
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should display empty state when no messages', () => {
      render(<MessageList messages={[]} />);

      expect(screen.getByText(/No messages yet/i)).toBeInTheDocument();
    });

    it('should render all messages', () => {
      render(<MessageList messages={mockMessages} />);

      expect(screen.getByText('Hello, how are you?')).toBeInTheDocument();
      expect(screen.getByText('I am doing well, thank you!')).toBeInTheDocument();
      expect(screen.getByText('Can you help me with my workout?')).toBeInTheDocument();
    });

    it('should display user messages on the right', () => {
      render(<MessageList messages={[mockMessages[0]]} />);

      const messageContainer = screen.getByText('Hello, how are you?').closest('div');
      expect(messageContainer?.parentElement).toHaveClass('justify-end');
    });

    it('should display agent messages on the left', () => {
      render(<MessageList messages={[mockMessages[1]]} />);

      const messageContainer = screen.getByText('I am doing well, thank you!').closest('div');
      expect(messageContainer?.parentElement).toHaveClass('justify-start');
    });

    it('should display message timestamps', () => {
      render(<MessageList messages={[mockMessages[0]]} />);

      // Check that timestamp is rendered (format may vary by locale)
      const timeElements = screen.getAllByText(/\d{1,2}:\d{2}/);
      expect(timeElements.length).toBeGreaterThan(0);
    });

    it('should display sender labels', () => {
      render(<MessageList messages={mockMessages} />);

      const youLabels = screen.getAllByText('You');
      const agentLabels = screen.getAllByText('Agent');

      expect(youLabels).toHaveLength(2); // Two user messages
      expect(agentLabels).toHaveLength(1); // One agent message
    });

    it('should apply correct styling to user messages', () => {
      render(<MessageList messages={[mockMessages[0]]} />);

      const messageDiv = screen.getByText('Hello, how are you?').closest('div');
      expect(messageDiv).toHaveClass('bg-blue-500', 'text-white');
    });

    it('should apply correct styling to agent messages', () => {
      render(<MessageList messages={[mockMessages[1]]} />);

      const messageDiv = screen.getByText('I am doing well, thank you!').closest('div');
      expect(messageDiv).toHaveClass('bg-gray-200', 'text-gray-900');
    });

    // New tests for streaming functionality - Requirement 4.3
    it('should show typing indicator when isStreaming is true', () => {
      const streamingMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'This is a streaming',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        isStreaming: true,
      };

      render(<MessageList messages={[streamingMessage]} />);

      const typingIndicator = screen.getByLabelText('typing');
      expect(typingIndicator).toBeInTheDocument();
      expect(typingIndicator).toHaveClass('typing-cursor');
    });

    // Requirement 4.4
    it('should hide typing indicator when isStreaming is false', () => {
      const finalizedMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'This is a complete message',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        isStreaming: false,
      };

      render(<MessageList messages={[finalizedMessage]} />);

      const typingIndicator = screen.queryByLabelText('typing');
      expect(typingIndicator).not.toBeInTheDocument();
    });

    // Requirement 4.6
    it('should apply different styling for streaming vs finalized messages', () => {
      const streamingMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'Streaming...',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        isStreaming: true,
      };

      const finalizedMessage: ChatMessage = {
        id: '2',
        role: 'assistant',
        content: 'Complete',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:05Z',
        isStreaming: false,
      };

      render(<MessageList messages={[streamingMessage, finalizedMessage]} />);

      const streamingDiv = screen.getByText('Streaming...').closest('div');
      const finalizedDiv = screen.getByText('Complete').closest('div');

      expect(streamingDiv).toHaveClass('bg-gray-100');
      expect(finalizedDiv).toHaveClass('bg-gray-200');
    });

    // Requirement 4.6
    it('should add data-streaming attribute for testing', () => {
      const streamingMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'Streaming...',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        isStreaming: true,
      };

      render(<MessageList messages={[streamingMessage]} />);

      const messageDiv = screen.getByText('Streaming...').closest('div');
      expect(messageDiv).toHaveAttribute('data-streaming', 'true');
    });

    // Requirement 4.5
    it('should trigger auto-scroll on content update with debouncing', () => {
      const scrollIntoViewMock = vi.fn();
      Element.prototype.scrollIntoView = scrollIntoViewMock;

      const { rerender } = render(<MessageList messages={[mockMessages[0]]} />);

      // Add more messages
      rerender(<MessageList messages={[mockMessages[0], mockMessages[1]]} />);

      // Scroll should not be called immediately (debounced)
      expect(scrollIntoViewMock).not.toHaveBeenCalled();

      // Fast-forward time by 100ms (debounce delay)
      vi.advanceTimersByTime(100);

      // Now scroll should be called
      waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalled();
      });
    });

    // Requirement 9.3
    it('should debounce scroll updates to 100ms', () => {
      const scrollIntoViewMock = vi.fn();
      Element.prototype.scrollIntoView = scrollIntoViewMock;

      const { rerender } = render(<MessageList messages={[mockMessages[0]]} />);

      // Rapidly update messages (simulating streaming chunks)
      rerender(<MessageList messages={[mockMessages[0], mockMessages[1]]} />);
      vi.advanceTimersByTime(50);
      
      rerender(<MessageList messages={[...mockMessages]} />);
      vi.advanceTimersByTime(50);

      // Should only call scroll once after debounce period
      waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalledTimes(1);
      });
    });

    // Requirements 8.1, 8.2, 8.3
    it('should have ARIA live region for accessibility', () => {
      const streamingMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'Streaming...',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        isStreaming: true,
      };

      render(<MessageList messages={[streamingMessage]} />);

      const liveRegion = screen.getByText('Assistant is responding');
      expect(liveRegion).toBeInTheDocument();
      expect(liveRegion.parentElement).toHaveAttribute('aria-live', 'polite');
      expect(liveRegion.parentElement).toHaveAttribute('aria-atomic', 'false');
    });

    // Requirement 8.2
    it('should announce streaming completion via ARIA', () => {
      const streamingMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'Streaming...',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        isStreaming: true,
      };

      const { rerender } = render(<MessageList messages={[streamingMessage]} />);

      expect(screen.getByText('Assistant is responding')).toBeInTheDocument();

      // Update to finalized message
      const finalizedMessage = { ...streamingMessage, isStreaming: false };
      rerender(<MessageList messages={[finalizedMessage]} />);

      expect(screen.queryByText('Assistant is responding')).not.toBeInTheDocument();
    });

    // Requirement 6.1
    it('should display error message when message has error property', () => {
      const errorMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'Partial response',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        error: 'Connection lost',
      };

      render(<MessageList messages={[errorMessage]} />);

      expect(screen.getByText('Connection lost')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    // Requirement 6.2
    it('should render retry button for failed messages', () => {
      const errorMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'Partial response',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        error: 'Network error',
      };

      const onRetry = vi.fn();
      render(<MessageList messages={[errorMessage]} onRetry={onRetry} />);

      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();
    });

    // Requirement 6.4
    it('should call onRetry when retry button is clicked', async () => {
      const errorMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'Partial response',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        error: 'Network error',
      };

      const onRetry = vi.fn();
      const user = userEvent.setup({ delay: null });
      render(<MessageList messages={[errorMessage]} onRetry={onRetry} />);

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('should not render retry button when onRetry is not provided', () => {
      const errorMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'Partial response',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        error: 'Network error',
      };

      render(<MessageList messages={[errorMessage]} />);

      expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
    });

    // Requirement 4.1
    it('should render streaming messages with accumulated text', () => {
      const streamingMessage: ChatMessage = {
        id: '1',
        role: 'assistant',
        content: 'This is accumulating text from multiple chunks',
        agentType: 'general_assistant',
        timestamp: '2024-01-01T10:00:00Z',
        isStreaming: true,
      };

      render(<MessageList messages={[streamingMessage]} />);

      expect(screen.getByText(/This is accumulating text from multiple chunks/)).toBeInTheDocument();
      expect(screen.getByLabelText('typing')).toBeInTheDocument();
    });
  });

  describe('ChatPage Integration', () => {
    beforeEach(() => {
      // Reset mocks before each test
      vi.clearAllMocks();
      // Mock scrollIntoView
      Element.prototype.scrollIntoView = vi.fn();
    });

    it('should render all chat components', () => {
      const mockUseChat = {
        messages: [],
        error: null,
        isStreaming: false,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
        retryLastMessage: vi.fn(),
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      expect(screen.getByText('AI Chat')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Type a message/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
      // Agent selector should not be present
      expect(screen.queryByLabelText('Select AI Agent')).not.toBeInTheDocument();
    });

    it('should send message without agent type', async () => {
      const mockSendMessage = vi.fn();
      const mockUseChat = {
        messages: [],
        error: null,
        isStreaming: false,
        sendMessage: mockSendMessage,
        clearMessages: vi.fn(),
        conversationId: null,
        retryLastMessage: vi.fn(),
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      // Type and send message (no agent selection needed)
      const textarea = screen.getByPlaceholderText(/Type a message/i);
      await user.type(textarea, 'Create a workout plan');
      await user.click(screen.getByRole('button', { name: /send/i }));

      // Should be called without agent type parameter
      expect(mockSendMessage).toHaveBeenCalledWith('Create a workout plan');
    });

    it('should display error message when error occurs', () => {
      const mockUseChat = {
        messages: [],
        error: 'Failed to send message',
        isStreaming: false,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
        retryLastMessage: vi.fn(),
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Failed to send message')).toBeInTheDocument();
    });

    it('should dismiss error message when close button is clicked', async () => {
      const mockUseChat = {
        messages: [],
        error: 'Failed to send message',
        isStreaming: false,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
        retryLastMessage: vi.fn(),
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Failed to send message')).toBeInTheDocument();

      const dismissButton = screen.getByLabelText('Dismiss error');
      await user.click(dismissButton);

      expect(screen.queryByText('Failed to send message')).not.toBeInTheDocument();
    });

    it('should disable input when streaming', () => {
      const mockUseChat = {
        messages: [],
        error: null,
        isStreaming: true,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
        retryLastMessage: vi.fn(),
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      const textarea = screen.getByPlaceholderText(/Waiting for response/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      expect(textarea).toBeDisabled();
      expect(sendButton).toBeDisabled();
    });

    it('should show appropriate placeholder when streaming', () => {
      const mockUseChat = {
        messages: [],
        error: null,
        isStreaming: true,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
        retryLastMessage: vi.fn(),
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText(/Waiting for response/i)).toBeInTheDocument();
    });

    it('should clear messages when clear button is clicked', async () => {
      const mockClearMessages = vi.fn();
      const mockUseChat = {
        messages: [
          {
            id: '1',
            role: 'user' as const,
            content: 'Test message',
            agentType: 'general_assistant' as AgentType,
            timestamp: '2024-01-01T10:00:00Z',
          },
        ],
        error: null,
        isStreaming: false,
        sendMessage: vi.fn(),
        clearMessages: mockClearMessages,
        conversationId: null,
        retryLastMessage: vi.fn(),
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      const clearButton = screen.getByRole('button', { name: /clear chat/i });
      await user.click(clearButton);

      expect(mockClearMessages).toHaveBeenCalled();
    });

    it('should disable clear button when no messages', () => {
      const mockUseChat = {
        messages: [],
        error: null,
        isStreaming: false,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
        retryLastMessage: vi.fn(),
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      const clearButton = screen.getByRole('button', { name: /clear chat/i });
      expect(clearButton).toBeDisabled();
    });

    it('should disable clear button when streaming', () => {
      const mockUseChat = {
        messages: [
          {
            id: '1',
            role: 'user' as const,
            content: 'Test message',
            agentType: 'general_assistant' as AgentType,
            timestamp: '2024-01-01T10:00:00Z',
          },
        ],
        error: null,
        isStreaming: true,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
        retryLastMessage: vi.fn(),
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      const clearButton = screen.getByRole('button', { name: /clear chat/i });
      expect(clearButton).toBeDisabled();
    });
  });
});
