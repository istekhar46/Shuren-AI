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
