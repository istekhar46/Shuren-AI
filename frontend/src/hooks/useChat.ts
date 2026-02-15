import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { chatService } from '../services/chatService';
import type { ChatMessage } from '../types';

interface UseChatReturn {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearMessages: () => void;
  conversationId: string | null;
}

/**
 * Custom hook for managing chat state and interactions
 * Handles message sending, history, loading states, and errors
 */
export const useChat = (): UseChatReturn => {
  const navigate = useNavigate();
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
        // Convert MessageDict[] to ChatMessage[]
        const chatMessages: ChatMessage[] = history.messages.map((msg, index) => ({
          id: `history-${index}-${Date.now()}`,
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          agentType: (msg.agent_type || 'general_assistant') as any,
          timestamp: msg.created_at,
        }));
        setMessages(chatMessages);
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
    async (message: string) => {
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
        agentType: 'general_assistant',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const response = await chatService.sendMessage(message);

        // Update conversation ID if this is the first message
        if (!conversationId) {
          setConversationId(response.conversation_id);
        }

        // Add agent response to messages
        const agentMessage: ChatMessage = {
          id: `${response.conversation_id}-${Date.now()}`,
          role: 'assistant',
          content: response.response,
          agentType: response.agent_type as any,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, agentMessage]);
      } catch (err: any) {
        // Handle structured ChatServiceError (403 with onboarding required)
        if (err.status === 403 && err.code === 'ONBOARDING_REQUIRED') {
          // Display error message from backend
          const errorMessage = err.message || 'Complete onboarding to access this feature';
          setError(errorMessage);
          
          // Remove the optimistic user message
          setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id));
          
          // Redirect to onboarding page
          navigate(err.redirect || '/onboarding');
          return;
        }

        // Handle other errors
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);

        // Remove the optimistic user message on error
        setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id));
      } finally {
        setLoading(false);
      }
    },
    [conversationId, navigate]
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
