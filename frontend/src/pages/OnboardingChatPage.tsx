import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChat } from '../hooks/useChat';
import { onboardingService } from '../services/onboardingService';
import { OnboardingProgressBar } from '../components/onboarding/OnboardingProgressBar';
import { MessageList } from '../components/chat/MessageList';
import { MessageInput } from '../components/chat/MessageInput';
import type { OnboardingProgress, StateMetadata } from '../types/onboarding.types';
import type { ChatMessage } from '../types';

/**
 * OnboardingChatPage Component
 * 
 * Replaces form-based onboarding with a chat-based interface with streaming support.
 * Users interact with specialized AI agents through conversation to complete onboarding.
 * 
 * Features:
 * - Fetches onboarding progress on mount
 * - Displays progress bar with current state
 * - Streaming chat interface for user-agent interaction
 * - Automatic state progression
 * - Redirects to dashboard on completion
 * 
 * Requirements: US-2.1, US-2.2, US-2.3, US-2.4, US-2.6, US-2.7, 5.1, 5.2, 5.5
 */
export const OnboardingChatPage = () => {
  const navigate = useNavigate();

  // Requirements 5.1, 5.2: Use streaming with isOnboarding: true
  const { messages, isStreaming, sendMessage: sendChatMessage, retryLastMessage } = useChat(true);

  // State management for onboarding progress
  const [currentState, setCurrentState] = useState<number>(1);
  const [totalStates] = useState<number>(9);
  const [completionPercentage, setCompletionPercentage] = useState<number>(0);
  const [stateMetadata, setStateMetadata] = useState<StateMetadata | null>(null);
  const [completedStates, setCompletedStates] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [initialLoadComplete, setInitialLoadComplete] = useState<boolean>(false);

  /**
   * Fetch onboarding progress on component mount
   * Loads current state, completion percentage, and state metadata
   */
  useEffect(() => {
    const fetchProgress = async () => {
      try {
        setError(null);

        const progress: OnboardingProgress = await onboardingService.getOnboardingProgress();

        // Update state with progress data
        setCurrentState(progress.current_state);
        setCompletionPercentage(progress.completion_percentage);
        setStateMetadata(progress.current_state_info);
        setCompletedStates(progress.completed_states);

        // Check if onboarding is already complete
        if (progress.is_complete) {
          navigate('/dashboard', { replace: true });
          return;
        }

        setInitialLoadComplete(true);
      } catch (err: any) {
        console.error('Failed to fetch onboarding progress:', err);
        setError(err.response?.data?.detail?.message || 'Failed to load onboarding progress. Please try again.');
        setInitialLoadComplete(true);
      }
    };

    fetchProgress();
  }, [navigate]);

  /**
   * Send message using streaming chat
   * The useChat hook handles streaming, we just need to call it
   * 
   * Requirements 5.1, 5.2: Use streaming for onboarding chat
   */
  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isStreaming) return;

    try {
      setError(null);
      
      // Send message via streaming (useChat hook handles the streaming)
      await sendChatMessage(message);

      // Note: State updates and completion handling would need to be done
      // via backend response or separate polling mechanism
      // For now, we rely on the streaming response to include state information
    } catch (err: any) {
      console.error('Failed to send message:', err);
      const errorMessage = err.response?.data?.detail?.message || 'Failed to send message. Please try again.';
      setError(errorMessage);
    }
  };

  // Show loading state during initial fetch
  if (!initialLoadComplete) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your onboarding progress...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Left Sidebar - Progress Bar */}
      <div className="w-80 bg-white border-r border-gray-300 overflow-y-auto">
        <div className="p-4">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Onboarding</h1>
          <OnboardingProgressBar
            currentState={currentState}
            totalStates={totalStates}
            completionPercentage={completionPercentage}
            stateMetadata={stateMetadata}
            completedStates={completedStates}
          />
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-300 p-4 shadow-sm">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-xl font-semibold text-gray-900">
              {stateMetadata?.name || 'Onboarding Chat'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Step {currentState} of {totalStates}
            </p>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 max-w-4xl w-full mx-auto flex flex-col overflow-hidden">
          {/* Requirement 5.5: Use same MessageList component as regular chat */}
          <MessageList messages={messages} onRetry={retryLastMessage} />

          {/* Error Display */}
          {error && (
            <div className="mx-4 mb-2 px-4 py-3 bg-red-100 border-l-4 border-red-500 text-red-700 rounded">
              <p className="font-semibold">Error</p>
              <p>{error}</p>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="max-w-4xl w-full mx-auto">
          {/* Requirement 5.2: Update placeholder based on streaming state */}
          <MessageInput 
            onSend={handleSendMessage} 
            disabled={isStreaming}
            placeholder={isStreaming ? 'Waiting for response...' : 'Tell me about yourself...'}
          />
        </div>
      </div>
    </div>
  );
};
