import { describe, it, expect, vi, beforeEach } from 'vitest';
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
        loading: false,
        error: null,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      expect(screen.getByText('AI Chat')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Type your message/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
      // Agent selector should not be present
      expect(screen.queryByLabelText('Select AI Agent')).not.toBeInTheDocument();
    });

    it('should send message without agent type', async () => {
      const mockSendMessage = vi.fn();
      const mockUseChat = {
        messages: [],
        loading: false,
        error: null,
        sendMessage: mockSendMessage,
        clearMessages: vi.fn(),
        conversationId: null,
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      // Type and send message (no agent selection needed)
      const textarea = screen.getByPlaceholderText(/Type your message/i);
      await user.type(textarea, 'Create a workout plan');
      await user.click(screen.getByRole('button', { name: /send/i }));

      // Should be called without agent type parameter
      expect(mockSendMessage).toHaveBeenCalledWith('Create a workout plan');
    });

    it('should display error message when error occurs', () => {
      const mockUseChat = {
        messages: [],
        loading: false,
        error: 'Failed to send message',
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
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
        loading: false,
        error: 'Failed to send message',
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
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

    it('should disable input when loading', () => {
      const mockUseChat = {
        messages: [],
        loading: true,
        error: null,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      const textarea = screen.getByPlaceholderText(/Type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      expect(textarea).toBeDisabled();
      expect(sendButton).toBeDisabled();
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
        loading: false,
        error: null,
        sendMessage: vi.fn(),
        clearMessages: mockClearMessages,
        conversationId: null,
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
        loading: false,
        error: null,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
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

    it('should display loading indicator when loading', () => {
      const mockUseChat = {
        messages: [],
        loading: true,
        error: null,
        sendMessage: vi.fn(),
        clearMessages: vi.fn(),
        conversationId: null,
      };

      vi.mocked(useChatModule.useChat).mockReturnValue(mockUseChat);

      render(
        <MemoryRouter>
          <ChatPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/thinking/i)).toBeInTheDocument();
    });
  });
});
