import api from './api';
import type { ChatResponse, ChatHistoryResponse, ChatServiceError } from '../types/api';

/**
 * Callbacks for streaming message responses
 */
interface StreamCallbacks {
  onChunk: (chunk: string) => void;
  onComplete: (agentType?: string) => void;
  onError: (error: string) => void;
}

/**
 * Chat Service
 * 
 * Handles text-based AI agent interactions including sending messages,
 * retrieving chat history, and streaming responses via Server-Sent Events.
 * All operations require authentication.
 */
class ChatService {
  private activeStream: EventSource | null = null;
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
  }

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
  }

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
  }

  /**
   * Stream a message to an agent using Server-Sent Events (SSE)
   * 
   * Sends a message and receives the response as a stream of chunks,
   * allowing for real-time display of the agent's response as it's generated.
   * Uses EventSource for SSE connection. Authentication token is passed as
   * a query parameter due to EventSource limitations with custom headers.
   * 
   * Official MDN documentation:
   * https://developer.mozilla.org/en-US/docs/Web/API/EventSource
   * 
   * @param {string} message - User's message text
   * @param {StreamCallbacks} callbacks - Callbacks for chunk, completion, and error events
   * @param {boolean} [isOnboarding=false] - Whether this is an onboarding chat session
   * @returns {() => void} Cancellation function to close the stream
   * 
   * @example
   * const cancelStream = chatService.streamMessage(
   *   'Tell me about protein intake',
   *   {
   *     onChunk: (chunk) => console.log('Received:', chunk),
   *     onComplete: (agentType) => console.log('Complete! Agent:', agentType),
   *     onError: (error) => console.error('Error:', error)
   *   },
   *   false
   * );
   * 
   * // Later, to stop streaming:
   * cancelStream();
   */
  streamMessage(
    message: string,
    callbacks: StreamCallbacks,
    isOnboarding: boolean = false
  ): () => void {
    const token = localStorage.getItem('auth_token');
    const baseURL = api.defaults.baseURL || 'http://localhost:8000/api/v1';
    
    // Determine endpoint based on chat type
    const endpoint = isOnboarding ? '/chat/onboarding-stream' : '/chat/stream';
    
    // Create full URL by combining baseURL and endpoint
    // Remove trailing slash from baseURL if present, then append endpoint
    const fullURL = `${baseURL.replace(/\/$/, '')}${endpoint}`;
    const url = new URL(fullURL);
    
    // Add authentication token as query param (EventSource limitation)
    if (token) {
      url.searchParams.append('token', token);
    }
    
    // Add message as query param
    url.searchParams.append('message', message);

    // Create EventSource connection
    this.activeStream = new EventSource(url.toString());

    // Handle incoming messages
    this.activeStream.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.error) {
          callbacks.onError(data.error);
          this.activeStream?.close();
          this.activeStream = null;
        } else if (data.done) {
          callbacks.onComplete(data.agent_type);
          this.activeStream?.close();
          this.activeStream = null;
        } else if (data.chunk) {
          callbacks.onChunk(data.chunk);
        }
      } catch (error) {
        callbacks.onError('Failed to parse response');
        this.activeStream?.close();
        this.activeStream = null;
      }
    };

    // Handle connection errors
    this.activeStream.onerror = () => {
      callbacks.onError('Connection error');
      this.activeStream?.close();
      this.activeStream = null;
    };

    // Return cancellation function
    return () => {
      if (this.activeStream) {
        this.activeStream.close();
        this.activeStream = null;
      }
    };
  }

  /**
   * Cancel active streaming connection
   * 
   * Closes the active EventSource connection if one exists.
   * Safe to call even if no stream is active.
   * 
   * @example
   * chatService.cancelStream();
   */
  cancelStream(): void {
    if (this.activeStream) {
      this.activeStream.close();
      this.activeStream = null;
    }
  }
}

export const chatService = new ChatService();
