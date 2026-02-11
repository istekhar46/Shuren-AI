import api from './api';
import type { ChatRequest, ChatResponse, ChatHistoryResponse } from '../types/api';

/**
 * Chat Service
 * 
 * Handles text-based AI agent interactions including sending messages,
 * retrieving chat history, and streaming responses via Server-Sent Events.
 * All operations require authentication.
 */
export const chatService = {
  /**
   * Send a message to an AI agent
   * 
   * Sends a text message to the backend which routes it to the appropriate
   * AI agent. The backend manages conversation context automatically and
   * returns the conversation_id in the response for tracking.
   * 
   * @param {string} message - User's message text
   * @param {string} [agentType] - Type of agent to route to (optional, backend will auto-route if not specified)
   * @returns {Promise<ChatResponse>} Agent's response with conversation metadata and tools used
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * const response = await chatService.sendMessage('What should I eat for lunch?', 'diet_planning');
   * console.log(response.response); // Agent's text response
   * console.log(response.conversation_id); // For tracking conversation
   */
  async sendMessage(
    message: string,
    agentType?: string
  ): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat/chat', {
      message,
      agent_type: agentType,
    });
    return response.data;
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
   * @param {string} message - User's message text
   * @param {string | undefined} agentType - Type of agent to route to (optional)
   * @param {(chunk: string) => void} onChunk - Callback invoked for each chunk of the response
   * @param {(agentType: string) => void} onComplete - Callback invoked when streaming completes, receives agent type
   * @param {(error: Error) => void} onError - Callback invoked on errors
   * @returns {EventSource} EventSource instance for managing the connection (call .close() to terminate)
   * 
   * @example
   * const eventSource = chatService.streamMessage(
   *   'Tell me about protein intake',
   *   'diet_planning',
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
    agentType: string | undefined,
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
    
    // Add message and agent_type as query params
    url.searchParams.append('message', message);
    if (agentType) {
      url.searchParams.append('agent_type', agentType);
    }

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
