import api from './api';
import type { ChatResponse, ChatHistoryResponse, ChatServiceError } from '../types/api';

/**
 * Chat Service
 * 
 * Handles text-based AI agent interactions including sending messages,
 * retrieving chat history, and streaming responses via Server-Sent Events.
 * All operations require authentication.
 */
export const chatService = {
  /**
   * Send a message to an AI agent (post-onboarding)
   * 
   * Sends a text message to the backend which routes it to the general agent.
   * This method is for post-onboarding chat only. The backend manages 
   * conversation context automatically and returns the conversation_id 
   * in the response for tracking.
   * 
   * Note: agentType parameter is omitted for post-onboarding chat as the
   * backend enforces routing to the general agent only.
   * 
   * @param {string} message - User's message text
   * @returns {Promise<ChatResponse>} Agent's response with conversation metadata and tools used
   * @throws {ChatServiceError} Structured error with status, code, message, and redirect info
   * 
   * @example
   * try {
   *   const response = await chatService.sendMessage('What should I eat for lunch?');
   *   console.log(response.response); // Agent's text response
   *   console.log(response.conversation_id); // For tracking conversation
   * } catch (error) {
   *   if (error.status === 403 && error.code === 'ONBOARDING_REQUIRED') {
   *     // Redirect to onboarding
   *     navigate(error.redirect || '/onboarding');
   *   }
   * }
   */
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const response = await api.post<ChatResponse>('/chat/chat', {
        message,
        // agent_type omitted - backend forces general agent for post-onboarding
      });
      return response.data;
    } catch (error: any) {
      // Handle 403 errors with structured error details
      if (error.response?.status === 403) {
        const detail = error.response.data?.detail;
        const structuredError: ChatServiceError = {
          status: 403,
          code: detail?.error_code,
          message: detail?.message || 'Access forbidden',
          redirect: detail?.redirect,
        };
        throw structuredError;
      }
      // Re-throw other errors as-is
      throw error;
    }
  },

  /**
   * Get chat history
   * 
   * Retrieves the user's chat history with AI agents. Returns messages
   * in reverse chronological order (newest first) with pagination support.
   * 
   * @param {number} [limit=50] - Maximum number of messages to return (default: 50)
   * @returns {Promise<ChatHistoryResponse>} Chat history with messages array and total count
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * const history = await chatService.getHistory(20);
   * console.log(history.messages); // Array of message objects
   * console.log(history.total); // Total number of messages
   */
  async getHistory(limit: number = 50): Promise<ChatHistoryResponse> {
    const response = await api.get<ChatHistoryResponse>('/chat/history', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Clear all chat history
   * 
   * Deletes all chat messages for the current user. This action cannot be undone.
   * Use with caution as it permanently removes conversation history.
   * 
   * @returns {Promise<{ status: string }>} Success status message
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * const result = await chatService.clearHistory();
   * console.log(result.status); // 'success'
   */
  async clearHistory(): Promise<{ status: string }> {
    const response = await api.delete<{ status: string }>('/chat/history');
    return response.data;
  },

  /**
   * Stream a message to an agent using Server-Sent Events (SSE)
   * 
   * Sends a message and receives the response as a stream of chunks,
   * allowing for real-time display of the agent's response as it's generated.
   * Uses EventSource for SSE connection. Authentication token is passed as
   * a query parameter due to EventSource limitations with custom headers.
   * 
   * Note: For post-onboarding chat, agentType is omitted as backend routes
   * to general agent only.
   * 
   * @param {string} message - User's message text
   * @param {(chunk: string) => void} onChunk - Callback invoked for each chunk of the response
   * @param {(agentType: string) => void} onComplete - Callback invoked when streaming completes, receives agent type
   * @param {(error: Error) => void} onError - Callback invoked on errors
   * @returns {EventSource} EventSource instance for managing the connection (call .close() to terminate)
   * 
   * @example
   * const eventSource = chatService.streamMessage(
   *   'Tell me about protein intake',
   *   (chunk) => console.log('Received:', chunk),
   *   (agentType) => console.log('Complete! Agent:', agentType),
   *   (error) => console.error('Error:', error)
   * );
   * 
   * // Later, to stop streaming:
   * eventSource.close();
   */
  streamMessage(
    message: string,
    onChunk: (chunk: string) => void,
    onComplete: (agentType: string) => void,
    onError: (error: Error) => void
  ): EventSource {
    const token = localStorage.getItem('auth_token');
    const baseURL = api.defaults.baseURL || 'http://localhost:8000/api/v1';
    
    // Create URL with query params for SSE
    const url = new URL('/chat/stream', baseURL);
    
    // Add authentication token as query param (SSE limitation)
    if (token) {
      url.searchParams.append('token', token);
    }
    
    // Add message as query param
    url.searchParams.append('message', message);
    // agent_type omitted - backend forces general agent for post-onboarding

    const eventSource = new EventSource(url.toString());

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.error) {
          onError(new Error(data.error));
          eventSource.close();
        } else if (data.done) {
          onComplete(data.agent_type);
          eventSource.close();
        } else if (data.chunk) {
          onChunk(data.chunk);
        }
      } catch (error) {
        onError(new Error('Failed to parse stream data'));
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      onError(new Error('Stream connection failed'));
      eventSource.close();
    };

    return eventSource;
  },
};
