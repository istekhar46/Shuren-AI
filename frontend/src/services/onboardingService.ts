import api from './api';
import { retryRequest, RetryPresets } from '../utils/retry';
import type {
  OnboardingProgress,
  OnboardingChatResponse,
  OnboardingStreamChunk,
  OnboardingCompleteResponse,
} from '../types/onboarding.types';

/**
 * Onboarding service for managing user onboarding flow
 */
export const onboardingService = {
  /**
   * Get onboarding progress with state metadata
   * Calls GET /api/v1/onboarding/progress
   * @returns Onboarding progress with current state info and metadata
   */
  async getOnboardingProgress(): Promise<OnboardingProgress> {
    return retryRequest(
      async () => {
        const response = await api.get<OnboardingProgress>('/onboarding/progress');
        return response.data;
      },
      RetryPresets.standard
    );
  },

  /**
   * Complete onboarding and create user profile
   * Calls POST /api/v1/onboarding/complete
   * @returns Created user profile with onboarding completion status
   */
  async completeOnboarding(): Promise<OnboardingCompleteResponse> {
    return retryRequest(
      async () => {
        const response = await api.post<OnboardingCompleteResponse>('/onboarding/complete');
        return response.data;
      },
      RetryPresets.standard
    );
  },

  /**
   * Send message during onboarding (non-streaming)
   * Calls POST /api/v1/chat/onboarding
   * @param message - User's message
   * @param currentState - Current onboarding state number
   * @returns Agent response with state update information
   */
  async sendOnboardingMessage(
    message: string,
    currentState: number
  ): Promise<OnboardingChatResponse> {
    return retryRequest(
      async () => {
        const response = await api.post<OnboardingChatResponse>('/chat/onboarding', {
          message,
          current_state: currentState,
        });
        return response.data;
      },
      RetryPresets.standard
    );
  },

  /**
   * Get onboarding conversation history
   * Calls GET /api/v1/chat/onboarding/history
   * @returns Array of conversation messages in chronological order
   */
  async getOnboardingHistory(): Promise<Array<{ role: string; content: string; agent_type?: string; created_at?: string }>> {
    return retryRequest(
      async () => {
        const response = await api.get<{ messages: Array<{ role: string; content: string; agent_type?: string; created_at?: string }>; total: number }>('/chat/onboarding/history');
        return response.data.messages;
      },
      RetryPresets.standard
    );
  },

  /**
   * Stream onboarding message with SSE
   * Calls GET /api/v1/chat/onboarding-stream
   * @param message - User's message to the onboarding agent
   * @param currentState - Current onboarding state number (1-4)
   * @param callbacks - Callbacks for handling streaming events
   * @returns Cancel function to abort the stream
   */
  streamOnboardingMessage(
    message: string,
    currentState: number,
    callbacks: {
      onChunk: (chunk: string) => void;
      onComplete: (data: OnboardingStreamChunk) => void;
      onError: (error: string) => void;
    }
  ): () => void {
    // Validate state is 1-4
    if (currentState < 1 || currentState > 4) {
      console.warn(`Invalid state ${currentState}, clamping to valid range`);
      currentState = Math.max(1, Math.min(4, currentState));
    }
    
    const token = localStorage.getItem('auth_token');
    const baseURL = api.defaults.baseURL || 'http://localhost:8000/api/v1';
    
    // Build SSE URL with query parameters
    const url = new URL(`${baseURL}/chat/onboarding-stream`);
    if (token) {
      url.searchParams.append('token', token);
    }
    url.searchParams.append('message', message);
    url.searchParams.append('current_state', currentState.toString());
    
    // Create EventSource for SSE
    const eventSource = new EventSource(url.toString());
    let hasReceivedData = false;
    
    // Handle incoming messages
    eventSource.onmessage = (event) => {
      try {
        hasReceivedData = true;
        const data: OnboardingStreamChunk = JSON.parse(event.data);
        
        // Handle error in stream
        if (data.error) {
          callbacks.onError(data.error);
          eventSource.close();
          return;
        }
        
        // Handle completion
        if (data.done) {
          // Validate and filter progress data if present
          if (data.progress) {
            // Validate total_states equals 4
            if (data.progress.total_states !== 4) {
              console.warn(`Expected total_states to be 4, got ${data.progress.total_states}`);
              data.progress.total_states = 4;
            }
            
            // Filter completed_states to only include 1-4
            const validCompletedStates = data.progress.completed_states.filter(s => s >= 1 && s <= 4);
            if (validCompletedStates.length !== data.progress.completed_states.length) {
              console.warn('Filtered invalid state numbers from completed_states');
              data.progress.completed_states = validCompletedStates;
            }
            
            // Validate agent_type matches one of 4 types
            if (data.agent_type) {
              const validAgentTypes = ['fitness_assessment', 'workout_planning', 'diet_planning', 'scheduling'];
              if (!validAgentTypes.includes(data.agent_type)) {
                console.warn(`Invalid agent_type: ${data.agent_type}, defaulting to fitness_assessment`);
                data.agent_type = 'fitness_assessment';
              }
            }
          }
          
          callbacks.onComplete(data);
          eventSource.close();
          return;
        }
        
        // Handle chunk
        if (data.chunk) {
          callbacks.onChunk(data.chunk);
        }
      } catch (error) {
        console.error('Failed to parse streaming response:', error);
        callbacks.onError('Failed to parse streaming response');
        eventSource.close();
      }
    };
    
    // Handle connection errors
    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      
      // Provide more specific error messages
      if (!hasReceivedData) {
        callbacks.onError('Failed to connect to server. Please check your connection and try again.');
      } else {
        callbacks.onError('Connection lost. Please try sending your message again.');
      }
      
      eventSource.close();
    };
    
    // Return cancel function
    return () => {
      eventSource.close();
    };
  },
};
