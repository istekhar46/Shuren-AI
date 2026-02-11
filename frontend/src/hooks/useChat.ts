import { useState, useCallback, useEffect } from 'react';
import { chatService } from '../services/chatService';
import type { AgentType, ChatMessage } from '../types';

interface UseChatReturn {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  sendMessage: (message: string, agentType: AgentType) => Promise<void>;
  clearMessages: () => void;
  conversationId: string | null;
}

/**
 * Custom hook for managing chat state and interactions
 * Handles message sending, history, loading states, and errors
 */
export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  /**
   * Load chat history on mount
   */
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await chatService.getHistory();
        // Extract messages array from the response object
        setMessages(history.messages || []);
      } catch (err) {
        console.error('Failed to load chat history:', err);
        // Don't set error state for history load failure
        // Set empty array to prevent undefined errors
        setMessages([]);
      }
    };

    loadHistory();
  }, []);

  /**
   * Send a message to the AI agent
   */
  const sendMessage = useCallback(
    async (message: string, agentType: AgentType) => {
      if (!message.trim()) {
        return;
      }

      setLoading(true);
      setError(null);

      // Add user message to UI immediately (optimistic update)
      const userMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: message,
        agentType,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const response = await chatService.sendMessage(
          message,
          agentType,
          conversationId || undefined
        );

        // Update conversation ID if this is the first message
        if (!conversationId) {
          setConversationId(response.conversationId);
        }

        // Add agent response to messages
        const agentMessage: ChatMessage = {
          id: `${response.conversationId}-${Date.now()}`,
          role: 'assistant',
          content: response.message,
          agentType: response.agentType,
          timestamp: response.timestamp,
        };
        setMessages((prev) => [...prev, agentMessage]);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);

        // Remove the optimistic user message on error
        setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id));
      } finally {
        setLoading(false);
      }
    },
    [conversationId]
  );

  /**
   * Clear all messages and reset conversation
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearMessages,
    conversationId,
  };
};
