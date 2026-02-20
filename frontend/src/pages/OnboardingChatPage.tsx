import React from 'react';
import { useOnboardingChat } from '../hooks/useOnboardingChat';
import { AgentHeader } from '../components/onboarding/AgentHeader';
import { OnboardingProgressBar } from '../components/onboarding/OnboardingProgressBar';
import { PlanPreviewCard } from '../components/onboarding/PlanPreviewCard';
import { MessageList } from '../components/chat/MessageList';
import { MessageInput } from '../components/chat/MessageInput';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

/**
 * OnboardingChatPage Component
 * 
 * Agent-based onboarding interface with streaming chat support.
 * Users interact with specialized AI agents through conversation to complete onboarding.
 * 
 * Features:
 * - Agent context display showing current agent
 * - Progress tracking with 9-state system
 * - Streaming chat interface
 * - Plan preview and approval workflow
 * - Automatic state progression
 * - Completion button when ready
 * 
 * Requirements: US-1, US-2, US-3, US-4, US-5, US-6
 */
export const OnboardingChatPage: React.FC = () => {
  const {
    // Progress state
    currentState,
    totalStates,
    completedStates,
    completionPercentage,
    isComplete,
    canComplete,
    
    // Agent state
    currentAgent,
    agentDescription,
    stateMetadata,
    
    // Chat state
    messages,
    isStreaming,
    error,
    
    // Plan state
    pendingPlan,
    planType,
    showPlanPreview,
    
    // Actions
    sendMessage,
    approvePlan,
    modifyPlan,
    closePlanPreview,
    completeOnboarding,
    
    // Loading state
    initialLoadComplete,
  } = useOnboardingChat();

  // Show loading state during initial fetch
  if (!initialLoadComplete) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-gray-600 mt-4">Loading your onboarding progress...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50" role="main" aria-label="Onboarding chat interface">
      {/* Agent Header - Sticky at top */}
      {currentAgent && stateMetadata && (
        <AgentHeader
          agentType={currentAgent}
          agentDescription={agentDescription}
          currentState={currentState}
          totalStates={totalStates}
          stateName={stateMetadata.name}
        />
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden" role="region" aria-label="Chat and progress area">
        {/* Progress Sidebar (Desktop) / Collapsible (Mobile) */}
        <OnboardingProgressBar
          currentState={currentState}
          totalStates={totalStates}
          completionPercentage={completionPercentage}
          stateMetadata={stateMetadata}
          completedStates={completedStates}
        />

        {/* Chat Area */}
        <div className="flex-1 flex flex-col overflow-hidden" role="region" aria-label="Chat messages">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto" role="log" aria-live="polite" aria-atomic="false">
            <div className="max-w-4xl mx-auto px-4 py-6">
              <MessageList 
                messages={messages} 
                onRetry={() => {
                  // Retry last message if needed
                  const lastUserMessage = [...messages]
                    .reverse()
                    .find(msg => msg.role === 'user');
                  if (lastUserMessage) {
                    sendMessage(lastUserMessage.content);
                  }
                }}
              />

              {/* Error Display */}
              {error && (
                <div className="mt-4" role="alert" aria-live="assertive">
                  <ErrorMessage message={error} />
                </div>
              )}

              {/* Complete Onboarding Button */}
              {canComplete && !isComplete && (
                <div 
                  className="mt-6 p-6 bg-green-50 border-2 border-green-300 rounded-lg"
                  role="status"
                  aria-live="polite"
                >
                  <div className="text-center">
                    <h3 className="text-xl font-bold text-green-900 mb-2">
                      <span role="img" aria-label="celebration">🎉</span> Onboarding Complete!
                    </h3>
                    <p className="text-green-800 mb-4">
                      You've completed all onboarding steps. Click below to finalize your profile and start your fitness journey!
                    </p>
                    <button
                      onClick={completeOnboarding}
                      className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                      aria-label="Complete onboarding and go to dashboard"
                    >
                      Complete Onboarding & Go to Dashboard
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 bg-white" role="region" aria-label="Message input">
            <div className="max-w-4xl mx-auto px-4 py-4">
              <MessageInput 
                onSend={sendMessage} 
                disabled={isStreaming}
                placeholder={
                  isStreaming 
                    ? 'Agent is typing...' 
                    : stateMetadata 
                    ? `Tell me about ${stateMetadata.name.toLowerCase()}...`
                    : 'Type your message...'
                }
              />
            </div>
          </div>
        </div>
      </div>

      {/* Plan Preview Modal */}
      {showPlanPreview && pendingPlan && planType && (
        <PlanPreviewCard
          plan={pendingPlan}
          planType={planType}
          onApprove={approvePlan}
          onModify={modifyPlan}
          onClose={closePlanPreview}
        />
      )}
    </div>
  );
};
