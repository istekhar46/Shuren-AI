import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { onboardingService } from '../services/onboardingService';
import { planDetectionService } from '../services/planDetectionService';
import type {
  OnboardingStreamChunk,
  StateMetadata,
  OnboardingWorkoutPlan,
  OnboardingMealPlan,
  AgentType as OnboardingAgentType,
} from '../types/onboarding.types';
import type { ChatMessage, AgentType as GeneralAgentType } from '../types';

interface UseOnboardingChatReturn {
  // Progress state
  currentState: number;
  totalStates: number;
  completedStates: number[];
  completionPercentage: number;
  isComplete: boolean;
  canComplete: boolean;
  
  // Agent state
  currentAgent: OnboardingAgentType | null;
  agentDescription: string;
  stateMetadata: StateMetadata | null;
  
  // Chat state
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  
  // Plan state
  pendingPlan: OnboardingWorkoutPlan | OnboardingMealPlan | null;
  planType: 'workout' | 'meal' | null;
  showPlanPreview: boolean;
  
  // Actions
  sendMessage: (message: string) => Promise<void>;
  approvePlan: () => void;
  modifyPlan: (feedback: string) => void;
  closePlanPreview: () => void;
  completeOnboarding: () => Promise<void>;
  
  // Loading state
  initialLoadComplete: boolean;
}

/**
 * Custom hook for managing onboarding chat state and interactions
 * 
 * Handles:
 * - Onboarding progress tracking (4 steps)
 * - Agent context and state metadata
 * - Streaming chat messages
 * - Plan detection and approval workflow
 * - State synchronization with backend
 * 
 * @returns {UseOnboardingChatReturn} Onboarding chat state and methods
 */
export const useOnboardingChat = (): UseOnboardingChatReturn => {
  // Progress state
  const [currentState, setCurrentState] = useState<number>(0);
  const [totalStates] = useState<number>(4);
  const [completedStates, setCompletedStates] = useState<number[]>([]);
  const [completionPercentage, setCompletionPercentage] = useState<number>(0);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [canComplete, setCanComplete] = useState<boolean>(false);
  
  // Agent state
  const [currentAgent, setCurrentAgent] = useState<OnboardingAgentType | null>(null);
  const [agentDescription, setAgentDescription] = useState<string>('');
  const [stateMetadata, setStateMetadata] = useState<StateMetadata | null>(null);
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Plan state
  const [pendingPlan, setPendingPlan] = useState<OnboardingWorkoutPlan | OnboardingMealPlan | null>(null);
  const [planType, setPlanType] = useState<'workout' | 'meal' | null>(null);
  const [showPlanPreview, setShowPlanPreview] = useState<boolean>(false);
  
  // Loading state
  const [initialLoadComplete, setInitialLoadComplete] = useState<boolean>(false);
  
  // Refs
  const cancelStreamRef = useRef<(() => void) | null>(null);
  const navigate = useNavigate();
  
  /**
   * Validate and clamp state to valid range (1-4)
   */
  const validateState = useCallback((state: number): number => {
    return Math.max(1, Math.min(4, state));
  }, []);
  
  /**
   * Check if agent type is valid (one of 4 types)
   */
  const isValidAgent = useCallback((agent: string): agent is OnboardingAgentType => {
    return ['fitness_assessment', 'workout_planning', 'diet_planning', 'scheduling'].includes(agent);
  }, []);
  
  /**
   * Fetch onboarding progress and conversation history on mount
   * Requirements:
   * - TR-2.1: Use /onboarding/progress for initial load
   * - Load conversation history from /chat/onboarding/history
   */
  useEffect(() => {
    const fetchProgressAndHistory = async () => {
      try {
        // Fetch progress and history in parallel
        const [progress, history] = await Promise.all([
          onboardingService.getOnboardingProgress(),
          onboardingService.getOnboardingHistory(),
        ]);
        
        // Update progress state
        setCurrentState(validateState(progress.current_state));
        setCompletedStates(progress.completed_states.filter(s => s >= 1 && s <= 4));
        setCompletionPercentage(progress.completion_percentage);
        setIsComplete(progress.is_complete);
        setCanComplete(progress.can_complete);
        
        // Update agent state
        setStateMetadata(progress.current_state_info);
        // Validate agent type before setting
        if (isValidAgent(progress.current_state_info.agent)) {
          setCurrentAgent(progress.current_state_info.agent);
        } else {
          console.warn(`Invalid agent type: ${progress.current_state_info.agent}, defaulting to fitness_assessment`);
          setCurrentAgent('fitness_assessment');
        }
        setAgentDescription(progress.current_state_info.description);
        
        // Load conversation history
        if (history && history.length > 0) {
          const chatMessages: ChatMessage[] = history.map((msg) => ({
            id: crypto.randomUUID(),
            role: msg.role as 'user' | 'assistant',
            content: msg.content,
            agentType: (progress.current_state_info.agent || 'fitness_assessment') as GeneralAgentType,
            timestamp: new Date().toISOString(),
            isStreaming: false,
          }));
          setMessages(chatMessages);
        }
        
        setInitialLoadComplete(true);
        
        // Redirect if already complete
        if (progress.is_complete) {
          navigate('/dashboard');
        }
      } catch (err) {
        console.error('Failed to fetch onboarding data:', err);
        setError('Failed to load onboarding progress. Please refresh the page.');
        setInitialLoadComplete(true);
      }
    };
    
    fetchProgressAndHistory();
  }, [navigate]);
  
  /**
   * Send message with streaming support
   * Requirements:
   * - TR-2.2: Use /chat/onboarding-stream for chat messages
   * - TR-2.3: Parse state_updated, new_state, progress from stream
   * - TR-5.1: Handle progress object in streaming response
   * - TR-5.2: Update UI when state_updated is true
   */
  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isStreaming) {
      return;
    }
    
    setError(null);
    
    // Add user message
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
      agentType: (currentAgent || 'fitness_assessment') as GeneralAgentType,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Create assistant placeholder
    const assistantId = crypto.randomUUID();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      agentType: (currentAgent || 'fitness_assessment') as GeneralAgentType,
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };
    setMessages(prev => [...prev, assistantMessage]);
    setIsStreaming(true);
    
    // Start streaming
    cancelStreamRef.current = onboardingService.streamOnboardingMessage(
      message,
      currentState,
      {
        // Handle chunk updates
        onChunk: (chunk: string) => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === assistantId
                ? { ...msg, content: msg.content + chunk }
                : msg
            )
          );
        },
        
        // Handle completion
        onComplete: (data: OnboardingStreamChunk) => {
          // Update message streaming state
          setMessages(prev =>
            prev.map(msg =>
              msg.id === assistantId
                ? { 
                    ...msg, 
                    isStreaming: false,
                    agentType: (data.agent_type as GeneralAgentType) || (currentAgent as GeneralAgentType) || ('fitness_assessment' as GeneralAgentType)
                  }
                : msg
            )
          );
          setIsStreaming(false);
          cancelStreamRef.current = null;
          
          // Handle state updates
          if (data.state_updated && data.progress) {
            // Validate and filter completed_states to only include 1-4
            const validCompletedStates = data.progress.completed_states.filter(s => s >= 1 && s <= 4);
            
            setCurrentState(validateState(data.progress.current_state));
            setCompletedStates(validCompletedStates);
            setCompletionPercentage(data.progress.completion_percentage);
            setIsComplete(data.progress.is_complete);
            setCanComplete(data.progress.can_complete);
            
            // Fetch fresh progress to get updated state metadata
            onboardingService.getOnboardingProgress()
              .then(progress => {
                setStateMetadata(progress.current_state_info);
                // Validate agent type before setting
                if (isValidAgent(progress.current_state_info.agent)) {
                  setCurrentAgent(progress.current_state_info.agent);
                } else {
                  console.warn(`Invalid agent type: ${progress.current_state_info.agent}, defaulting to fitness_assessment`);
                  setCurrentAgent('fitness_assessment');
                }
                setAgentDescription(progress.current_state_info.description);
              })
              .catch(err => {
                console.error('Failed to fetch updated progress:', err);
              });
          }
          
          // Detect plans in response
          const lastMessage = messages[messages.length - 1];
          if (lastMessage && lastMessage.role === 'assistant') {
            const workoutPlan = planDetectionService.detectWorkoutPlan(lastMessage.content);
            const mealPlan = planDetectionService.detectMealPlan(lastMessage.content);
            
            if (workoutPlan) {
              setPendingPlan(workoutPlan);
              setPlanType('workout');
              setShowPlanPreview(true);
            } else if (mealPlan) {
              setPendingPlan(mealPlan);
              setPlanType('meal');
              setShowPlanPreview(true);
            }
          }
        },
        
        // Handle errors
        onError: (errorMessage: string) => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === assistantId
                ? { ...msg, isStreaming: false, error: errorMessage }
                : msg
            )
          );
          setError(errorMessage);
          setIsStreaming(false);
          cancelStreamRef.current = null;
        },
      }
    );
  }, [currentState, isStreaming, currentAgent, messages]);
  
  /**
   * Approve pending plan
   * Sends approval message and closes preview
   */
  const approvePlan = useCallback(() => {
    if (!isStreaming) {
      sendMessage('Yes, looks perfect!');
      setShowPlanPreview(false);
      setPendingPlan(null);
      setPlanType(null);
    }
  }, [sendMessage, isStreaming]);
  
  /**
   * Request plan modifications
   * Sends feedback message and closes preview
   */
  const modifyPlan = useCallback((feedback: string) => {
    if (!isStreaming && feedback.trim()) {
      sendMessage(feedback);
      setShowPlanPreview(false);
    }
  }, [sendMessage, isStreaming]);
  
  /**
   * Close plan preview without action
   */
  const closePlanPreview = useCallback(() => {
    setShowPlanPreview(false);
  }, []);
  
  /**
   * Complete onboarding and redirect to dashboard
   * Requirement: TR-2.4 - Call /onboarding/complete when can_complete is true
   */
  const completeOnboarding = useCallback(async () => {
    if (!canComplete) {
      setError('Cannot complete onboarding yet. Please finish all steps.');
      return;
    }
    
    try {
      await onboardingService.completeOnboarding();
      navigate('/dashboard');
    } catch (err) {
      console.error('Failed to complete onboarding:', err);
      setError('Failed to complete onboarding. Please try again.');
    }
  }, [canComplete, navigate]);
  
  /**
   * Cleanup effect for component unmount
   * Cancel active stream on unmount
   */
  useEffect(() => {
    return () => {
      if (cancelStreamRef.current) {
        cancelStreamRef.current();
      }
    };
  }, []);
  
  return {
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
  };
};
