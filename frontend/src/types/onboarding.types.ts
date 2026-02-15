/**
 * Onboarding Type Definitions
 * 
 * These types define the structure of onboarding-related requests and responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

/**
 * Onboarding state response
 * Returned by GET /onboarding/state
 * Contains the current onboarding progress and step data
 */
export interface OnboardingStateResponse {
  id: string;
  user_id: string;
  current_step: number;
  is_complete: boolean;
  step_data: Record<string, any>;
}

/**
 * Onboarding step request payload
 * Sent to POST /onboarding/step
 * Used to save data for a specific onboarding step
 */
export interface OnboardingStepRequest {
  step: number;
  data: Record<string, any>;
}

/**
 * Onboarding step response
 * Returned by POST /onboarding/step
 * Confirms the step was saved and provides updated state
 */
export interface OnboardingStepResponse {
  current_step: number;
  is_complete: boolean;
  message: string;
}
/**
 * Onboarding progress response
 * Returned by GET /api/v1/onboarding/progress
 * Contains current state, completion status, and metadata
 */
export interface OnboardingProgress {
  current_state: number;
  total_states: number;
  completed_states: number[];
  is_complete: boolean;
  completion_percentage: number;
  current_state_info: StateMetadata;
}

/**
 * State metadata for UI rendering
 * Provides information about each onboarding state
 */
export interface StateMetadata {
  state_number: number;
  name: string;
  agent: string;
  description: string;
  required_fields: string[];
}

/**
 * Onboarding chat request
 * Sent to POST /api/v1/chat/onboarding
 */
export interface OnboardingChatRequest {
  message: string;
  current_state: number;
}

/**
 * Onboarding chat response
 * Returned by POST /api/v1/chat/onboarding
 * Contains agent response and state update information
 */
export interface OnboardingChatResponse {
  response: string;
  agent_type: string;
  state_updated: boolean;
  new_state?: number;
  is_complete: boolean;
  progress: {
    current_state: number;
    completion_percentage: number;
  };
}
