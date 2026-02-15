import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { onboardingService } from '../services/onboardingService';
import { OnboardingProgressBar } from '../components/onboarding/OnboardingProgressBar';
import { MessageList } from '../components/chat/MessageList';
import { MessageInput } from '../components/chat/MessageInput';
import type { OnboardingProgress, StateMetadata } from '../types/onboarding.types';
import type { ChatMessage } from '../types';

/**
 * OnboardingChatPage Component
 * 
 * Replaces form-based onboarding with a chat-based interface.
 * Users interact with specialized AI agents through conversation to complete onboarding.
 * 
 * Features:
 * - Fetches onboarding progress on mount
 * - Displays progress bar with current state
 * - Chat interface for user-agent interaction
 * - Automatic state progression
 * - Redirects to dashboard on completion
 * 
 * Requirements: US-2.1, US-2.2, US-2.3, US-2.4, US-2.6, US-2.7
 */
export const OnboardingChatPage = () => {
  const navigate = useNavigate();

  // State management
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentState, setCurrentState] = useState<number>(1);
  const [totalStates] = useState<number>(9);
  const [completionPercentage, setCompletionPercentage] = useState<number>(0);
  const [stateMetadata, setStateMetadata] = useState<StateMetadata | null>(null);
  const [completedStates, setCompletedStates] = useState<number[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [initialLoadComplete, setInitialLoadComplete] = useState<boolean>(false);

  /**
   * Fetch onboarding progress on component mount
   * Loads current state, completion percentage, and state metadata
   */
  useEffect(() => {
    const fetchProgress = async () => {
      try {
        setLoading(true);
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

        // Display welcome message on first load (state 1, no completed states)
        if (progress.current_state === 1 && progress.completed_states.length === 0) {
          const welcomeMessage: ChatMessage = {
            id: `welcome-${Date.now()}`,
            role: 'assistant',
            content: `Welcome to Shuren! I'm here to help you set up your personalized fitness journey. We'll go through 9 quick steps to understand your fitness level, goals, and preferences. Let's get started!\n\n${progress.current_state_info.description}`,
            agentType: 'general_assistant',
            timestamp: new Date().toISOString(),
          };
          setMessages([welcomeMessage]);
        }

        setInitialLoadComplete(true);
      } catch (err: any) {
        console.error('Failed to fetch onboarding progress:', err);
        setError(err.response?.data?.detail?.message || 'Failed to load onboarding progress. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchProgress();
  }, [navigate]);

  /**
   * Send message to onboarding chat endpoint
   * Handles state updates and completion
   */
  const sendMessage = async (message: string) => {
    if (!message.trim() || loading) return;

    try {
      setLoading(true);
      setError(null);

      // Add user message to chat
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
        agentType: 'general_assistant',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send message to backend
      const response = await onboardingService.sendOnboardingMessage(message, currentState);

      // Add agent response to chat
      const agentMessage: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        agentType: response.agent_type as any,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, agentMessage]);

      // Handle state updates
      if (response.state_updated && response.new_state) {
        setCurrentState(response.new_state);
        setCompletionPercentage(response.progress.completion_percentage);
        
        // Update completed states
        setCompletedStates((prev) => {
          const newCompleted = [...prev];
          if (!newCompleted.includes(currentState)) {
            newCompleted.push(currentState);
          }
          return newCompleted.sort((a, b) => a - b);
        });

        // Fetch updated metadata for new state
        try {
          const updatedProgress = await onboardingService.getOnboardingProgress();
          setStateMetadata(updatedProgress.current_state_info);
        } catch (err) {
          console.error('Failed to fetch updated state metadata:', err);
        }
      }

      // Handle completion
      if (response.is_complete) {
        // Add completion message
        const completionMessage: ChatMessage = {
          id: `completion-${Date.now()}`,
          role: 'assistant',
          content: 'Congratulations! You\'ve completed your onboarding. Redirecting you to your dashboard...',
          agentType: 'general_assistant',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, completionMessage]);

        // Redirect to dashboard after a brief delay
        setTimeout(() => {
          navigate('/dashboard', { replace: true });
        }, 2000);
      }
    } catch (err: any) {
      console.error('Failed to send message:', err);
      const errorMessage = err.response?.data?.detail?.message || 'Failed to send message. Please try again.';
      setError(errorMessage);

      // Add error message to chat
      const errorChatMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}`,
        agentType: 'general_assistant',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorChatMessage]);
    } finally {
      setLoading(false);
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
          <MessageList messages={messages} />
          
          {/* Loading Indicator */}
          {loading && (
            <div className="px-4 py-2">
              <div className="flex items-center gap-2 text-gray-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm">Agent is typing...</span>
              </div>
            </div>
          )}

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
          <MessageInput 
            onSend={sendMessage} 
            disabled={loading}
          />
        </div>
      </div>
    </div>
  );
};
