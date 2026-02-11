import api from './api';
import type {
  OnboardingStateResponse,
  OnboardingStepRequest,
  OnboardingStepResponse,
  UserProfileResponse,
} from '../types/api';

/**
 * Onboarding service for managing user onboarding flow
 */
export const onboardingService = {
  /**
   * Get current onboarding state
   * @returns Current onboarding progress with step data
   */
  async getOnboardingState(): Promise<OnboardingStateResponse> {
    const response = await api.get<OnboardingStateResponse>('/onboarding/state');
    return response.data;
  },

  /**
   * Save onboarding step data
   * @param step - Step number (1-based)
   * @param data - Step-specific data to save
   * @returns Updated onboarding state
   */
  async saveStep(step: number, data: Record<string, any>): Promise<OnboardingStepResponse> {
    const payload: OnboardingStepRequest = { step, data };
    const response = await api.post<OnboardingStepResponse>('/onboarding/step', payload);
    return response.data;
  },

  /**
   * Complete onboarding and create user profile
   * @returns Created user profile
   */
  async completeOnboarding(): Promise<UserProfileResponse> {
    const response = await api.post<UserProfileResponse>('/onboarding/complete');
    return response.data;
  },

  /**
   * Legacy method for backward compatibility
   * @deprecated Use getOnboardingState() instead
   * @returns Current step and completion status
   */
  async getProgress(): Promise<{ currentStep: number; completed: boolean }> {
    console.warn('getProgress() is deprecated. Use getOnboardingState() instead.');
    const state = await this.getOnboardingState();
    return {
      currentStep: state.current_step,
      completed: state.is_complete,
    };
  },
};
