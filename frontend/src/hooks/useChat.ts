import { useState, useCallback, useEffect, useRef } from 'react';
import { chatService } from '../services/chatService';
import type { ChatMessage } from '../types';

// Requirement 9.1: Memory management - limit message history to prevent memory issues
const MAX_MESSAGES_IN_MEMORY = 50;

interface UseChatReturn {
  messages: ChatMessage[];
  error: string | null;
  isStreaming: boolean;
  sendMessage: (message: string) => Promise<void>;
  clearMessages: () => void;
  conversationId: string | null;
  retryLastMessage: () => void;
}

/**
 * Custom hook for managing chat state and interactions with streaming support
 * Handles message sending, history, loading states, streaming responses, and errors
 * 
 * @param {boolean} isOnboarding - Whether this is an onboarding chat session
 * @returns {UseChatReturn} Chat state and methods
 */
export const useChat = (isOnboarding: boolean = false): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const cancelStreamRef = useRef<(() => void) | null>(null);

  /**
   * Trim message history to prevent memory issues
   * Requirement 9.1: Keep only last 50 messages in memory
   * Full conversation is preserved in backend
   */
  const trimMessages = useCallback((msgs: ChatMessage[]): ChatMessage[] => {
    if (msgs.length > MAX_MESSAGES_IN_MEMORY) {
      return msgs.slice(-MAX_MESSAGES_IN_MEMORY);
    }
    return msgs;
  }, []);

  /**
   * Load chat history on mount
   */
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await chatService.getHistory();
        // Convert MessageDict[] to ChatMessage[]
        const chatMessages: ChatMessage[] = history.messages.map((msg, index) => ({
          id: `history-${index}-${Date.now()}`,
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          agentType: (msg.agent_type || 'general_assistant') as any,
          timestamp: msg.created_at,
        }));
        // Requirement 9.1: Trim to last 50 messages for memory management
        setMessages(trimMessages(chatMessages));
      } catch (err) {
        console.error('Failed to load chat history:', err);
        // Don't set error state for history load failure
        // Set empty array to prevent undefined errors
        setMessages([]);
      }
    };

    loadHistory();
  }, [trimMessages]);

  /**
   * Send a message to the AI agent with streaming support
   * 
   * Requirements:
   * - 3.1: Add user message immediately to state
   * - 3.2: Create placeholder assistant message with isStreaming: true
   * - 3.3: Append chunks to placeholder message content
   * - 3.4: Set isStreaming: false on completion
   * - 3.5: Set error state on failure
   * - 3.6: Prevent sending new messages while streaming
   * - 9.1: React 19 automatic batching for performance
   */
  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim()) {
        return;
      }

      // Requirement 3.6: Prevent sending new messages while streaming
      if (isStreaming) {
        return;
      }

      setError(null);

      // Requirement 3.1: Add user message to UI immediately
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: message,
        agentType: 'general_assistant',
        timestamp: new Date().toISOString(),
      };
      
      // Requirement 9.1: React 19 automatic batching
      // Multiple setState calls in the same event handler are automatically batched
      // This reduces re-renders when adding user message and creating placeholder
      // Also trim messages to prevent memory issues with long conversations
      setMessages((prev) => trimMessages([...prev, userMessage]));
      setIsStreaming(true);

      // Requirement 3.2: Create placeholder assistant message with isStreaming: true
      const assistantMessageId = crypto.randomUUID();
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        agentType: 'general_assistant',
        timestamp: new Date().toISOString(),
        isStreaming: true,
      };
      setMessages((prev) => trimMessages([...prev, assistantMessage]));

      // Start streaming
      cancelStreamRef.current = chatService.streamMessage(
        message,
        {
          // Requirement 3.3: Append chunks to placeholder message content
          // Requirement 9.1: React 19 automatic batching ensures rapid chunks
          // arriving in quick succession are batched into single re-renders
          onChunk: (chunk: string) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + chunk }
                  : msg
              )
            );
          },
          // Requirement 3.4: Set isStreaming: false on completion
          // React 19 batches these two setState calls automatically
          onComplete: (agentType?: string) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { 
                      ...msg, 
                      isStreaming: false,
                      agentType: (agentType as any) || 'general_assistant'
                    }
                  : msg
              )
            );
            setIsStreaming(false);
            cancelStreamRef.current = null;
          },
          // Requirement 3.5: Set error state on failure
          // React 19 batches these three setState calls automatically
          onError: (errorMessage: string) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, isStreaming: false, error: errorMessage }
                  : msg
              )
            );
            setError(errorMessage);
            setIsStreaming(false);
            cancelStreamRef.current = null;
          },
        },
        isOnboarding
      );
    },
    [isStreaming, isOnboarding]
  );

  /**
   * Clear all messages and reset conversation
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }, []);

  /**
   * Retry the last failed message
   * 
   * Requirement 6.2: Find last user message, remove failed assistant message, resend
   */
  const retryLastMessage = useCallback(() => {
    const lastUserMessage = [...messages]
      .reverse()
      .find((msg) => msg.role === 'user');

    if (lastUserMessage) {
      // Remove failed assistant message (last message in array)
      setMessages((prev) => prev.slice(0, -1));
      sendMessage(lastUserMessage.content);
    }
  }, [messages, sendMessage]);

  /**
   * Cleanup effect for component unmount
   * 
   * Requirements 7.1, 7.2: Cancel active stream on unmount
   */
  useEffect(() => {
    return () => {
      if (cancelStreamRef.current) {
        cancelStreamRef.current();
      }
    };
  }, []);

  return {
    messages,
    error,
    isStreaming,
    sendMessage,
    clearMessages,
    conversationId,
    retryLastMessage,
  };
};
