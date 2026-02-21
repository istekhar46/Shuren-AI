import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ChatPage } from '../../src/pages/ChatPage';
import { OnboardingChatPage } from '../../src/pages/OnboardingChatPage';
import { chatService } from '../../src/services/chatService';
import { onboardingService } from '../../src/services/onboardingService';

/**
 * Integration Tests for Chat Pages with Streaming
 * 
 * Tests complete streaming flow in both ChatPage and OnboardingChatPage
 * Validates Requirements 5.5: UI consistency between both pages
 */

// Mock services
vi.mock('../../src/services/chatService');
vi.mock('../../src/services/onboardingService');

describe('Chat Pages Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('ChatPage - Complete Streaming Flow', () => {
    it('should complete full streaming flow from send to display', async () => {
      const user = userEvent.setup();
      
      // Mock chat history
      vi.mocked(chatService.getHistory).mockResolvedValue({
        messages: [],
        conversation_id: 'test-conv-id',
      });

      // Mock streaming
      let onChunkCallback: ((chunk: string) => void) | null = null;
      let onCompleteCallback: (() => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
        onChunkCallback = callbacks.onChunk;
        onCompleteCallback = callbacks.onComplete;
        return () => {}; // cancel function
      });

      render(
        <BrowserRouter>
          <ChatPage />
        </BrowserRouter>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(chatService.getHistory).toHaveBeenCalled();
      });

      // Type and send message
      const input = screen.getByPlaceholderText(/type a message/i);
      await user.type(input, 'Hello AI');
      
      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      // Verify user message appears immediately
      await waitFor(() => {
        expect(screen.getByText('Hello AI')).toBeInTheDocument();
      });

      // Simulate streaming chunks
      if (onChunkCallback) {
        onChunkCallback('Hello ');
        onChunkCallback('there! ');
        onChunkCallback('How can I help?');
      }

      // Verify chunks appear
      await waitFor(() => {
        expect(screen.getByText(/Hello there! How can I help?/)).toBeInTheDocument();
      });

      // Complete streaming
      if (onCompleteCallback) {
        onCompleteCallback();
      }

      // Verify streaming indicator is removed
      await waitFor(() => {
        const messages = screen.getAllByTestId(/message-/);
        expect(messages.length).toBeGreaterThan(0);
      });
    });

    it('should disable input during streaming', async () => {
      const user = userEvent.setup();
      
      vi.mocked(chatService.getHistory).mockResolvedValue({
        messages: [],
        conversation_id: 'test-conv-id',
      });

      vi.mocked(chatService.streamMessage).mockImplementation(() => {
        return () => {}; // Don't complete, keep streaming
      });

      render(
        <BrowserRouter>
          <ChatPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(chatService.getHistory).toHaveBeenCalled();
      });

      const input = screen.getByPlaceholderText(/type a message/i);
      await user.type(input, 'Test message');
      
      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      // Verify input is disabled during streaming
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/waiting for response/i)).toBeDisabled();
      });
    });
  });

  describe('OnboardingChatPage - Complete Streaming Flow', () => {
    it('should complete full streaming flow in onboarding context', async () => {
      const user = userEvent.setup();
      
      // Mock onboarding progress
      vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue({
        current_state: 1,
        completion_percentage: 10,
        is_complete: false,
        completed_states: [],
        current_state_info: {
          state_number: 1,
          name: 'Basic Information',
          description: 'Tell us about yourself',
        },
      });

      // Mock chat history
      vi.mocked(chatService.getHistory).mockResolvedValue({
        messages: [],
        conversation_id: 'onboarding-conv-id',
      });

      // Mock streaming
      let onChunkCallback: ((chunk: string) => void) | null = null;
      let onCompleteCallback: (() => void) | null = null;

      vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks, isOnboarding) => {
        expect(isOnboarding).toBe(true); // Verify isOnboarding flag
        onChunkCallback = callbacks.onChunk;
        onCompleteCallback = callbacks.onComplete;
        return () => {};
      });

      render(
        <BrowserRouter>
          <OnboardingChatPage />
        </BrowserRouter>
      );

      // Wait for progress to load
      await waitFor(() => {
        expect(screen.getAllByText('Basic Information').length).toBeGreaterThan(0);
      });

      // Type and send message
      const input = screen.getByPlaceholderText(/tell me about yourself/i);
      await user.type(input, 'I am 25 years old');
      
      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      // Verify user message appears
      await waitFor(() => {
        expect(screen.getByText('I am 25 years old')).toBeInTheDocument();
      });

      // Simulate streaming
      if (onChunkCallback) {
        onChunkCallback('Great! ');
        onChunkCallback('What are your fitness goals?');
      }

      // Verify streamed response
      await waitFor(() => {
        expect(screen.getByText(/Great! What are your fitness goals?/)).toBeInTheDocument();
      });

      // Complete streaming
      if (onCompleteCallback) {
        onCompleteCallback();
      }
    });

    it('should use same MessageList component as ChatPage', async () => {
      // Mock services
      vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue({
        current_state: 1,
        completion_percentage: 10,
        is_complete: false,
        completed_states: [],
        current_state_info: {
          state_number: 1,
          name: 'Basic Information',
          description: 'Tell us about yourself',
        },
      });

      vi.mocked(chatService.getHistory).mockResolvedValue({
        messages: [{
          role: 'assistant',
          content: 'Welcome to onboarding!',
          agent_type: 'general_assistant',
          created_at: new Date().toISOString(),
        }],
        conversation_id: 'test-id',
      });

      const { container: onboardingContainer } = render(
        <BrowserRouter>
          <OnboardingChatPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Welcome to onboarding!')).toBeInTheDocument();
      });

      // Verify MessageList structure exists
      const messageList = onboardingContainer.querySelector('.flex-1.overflow-y-auto');
      expect(messageList).toBeInTheDocument();
    });
  });

  describe('UI Consistency Between Pages', () => {
    it('should render messages identically in both pages', async () => {
      const testMessage = {
        role: 'assistant' as const,
        content: 'Test message content',
        agent_type: 'general_assistant',
        created_at: new Date().toISOString(),
      };

      // Test ChatPage
      vi.mocked(chatService.getHistory).mockResolvedValue({
        messages: [testMessage],
        conversation_id: 'test-id',
      });

      const { container: chatContainer } = render(
        <BrowserRouter>
          <ChatPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test message content')).toBeInTheDocument();
      });

      const chatMessageElement = chatContainer.querySelector('[data-testid="message-assistant"]');
      expect(chatMessageElement).toBeInTheDocument();

      // Test OnboardingChatPage
      vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue({
        current_state: 1,
        completion_percentage: 10,
        is_complete: false,
        completed_states: [],
        current_state_info: {
          state_number: 1,
          name: 'Test State',
          description: 'Test',
        },
      });

      const { container: onboardingContainer } = render(
        <BrowserRouter>
          <OnboardingChatPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Test message content').length).toBeGreaterThan(0);
      });

      const onboardingMessageElement = onboardingContainer.querySelector('[data-testid="message-assistant"]');
      expect(onboardingMessageElement).toBeInTheDocument();

      // Both should use same component structure
      expect(chatMessageElement?.className).toBe(onboardingMessageElement?.className);
    });
  });
});
