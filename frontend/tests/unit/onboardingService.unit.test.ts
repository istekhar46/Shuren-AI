import { describe, it, expect, vi, beforeEach } from 'vitest';
import { onboardingService } from '../../src/services/onboardingService';
import api from '../../src/services/api';
import type {
  OnboardingStateResponse,
  OnboardingStepResponse,
  UserProfileResponse,
} from '../../src/types/api';

// Mock the api module
vi.mock('../../src/services/api');

describe('onboardingService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Clear console.warn mock
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  describe('getOnboardingState', () => {
    it('should call GET /onboarding/state and return onboarding state', async () => {
      const mockStateResponse: OnboardingStateResponse = {
        id: 'onboarding-123',
        user_id: 'user-123',
        current_step: 3,
        is_complete: false,
        step_data: {
          step1: { fitness_level: 'intermediate' },
          step2: { goals: ['fat_loss'] },
        },
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockStateResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.getOnboardingState();

      expect(api.get).toHaveBeenCalledWith('/onboarding/state');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockStateResponse);
    });

    it('should return state with is_complete true when onboarding is finished', async () => {
      const mockStateResponse: OnboardingStateResponse = {
        id: 'onboarding-456',
        user_id: 'user-456',
        current_step: 10,
        is_complete: true,
        step_data: {},
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockStateResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.getOnboardingState();

      expect(result.is_complete).toBe(true);
      expect(result.current_step).toBe(10);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(onboardingService.getOnboardingState()).rejects.toThrow('Network error');
      expect(api.get).toHaveBeenCalledWith('/onboarding/state');
    });

    it('should handle empty step_data', async () => {
      const mockStateResponse: OnboardingStateResponse = {
        id: 'onboarding-789',
        user_id: 'user-789',
        current_step: 1,
        is_complete: false,
        step_data: {},
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockStateResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.getOnboardingState();

      expect(result.step_data).toEqual({});
    });
  });

  describe('saveStep', () => {
    it('should call POST /onboarding/step with correct payload', async () => {
      const mockStepResponse: OnboardingStepResponse = {
        current_step: 4,
        is_complete: false,
        message: 'Step 3 saved successfully',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockStepResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const stepData = {
        fitness_level: 'intermediate',
        workout_experience: '2-3 years',
      };

      const result = await onboardingService.saveStep(3, stepData);

      expect(api.post).toHaveBeenCalledWith('/onboarding/step', {
        step: 3,
        data: stepData,
      });
      expect(api.post).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockStepResponse);
    });

    it('should handle saving first step', async () => {
      const mockStepResponse: OnboardingStepResponse = {
        current_step: 2,
        is_complete: false,
        message: 'Step 1 saved successfully',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockStepResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.saveStep(1, { name: 'John Doe' });

      expect(api.post).toHaveBeenCalledWith('/onboarding/step', {
        step: 1,
        data: { name: 'John Doe' },
      });
      expect(result.current_step).toBe(2);
    });

    it('should handle saving last step', async () => {
      const mockStepResponse: OnboardingStepResponse = {
        current_step: 10,
        is_complete: true,
        message: 'Step 10 saved successfully',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockStepResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.saveStep(10, { preferences: 'complete' });

      expect(result.is_complete).toBe(true);
    });

    it('should throw error when saving step fails', async () => {
      const mockError = new Error('Validation error');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(onboardingService.saveStep(5, {})).rejects.toThrow('Validation error');
    });

    it('should handle complex step data', async () => {
      const mockStepResponse: OnboardingStepResponse = {
        current_step: 6,
        is_complete: false,
        message: 'Step 5 saved successfully',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockStepResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const complexData = {
        goals: ['fat_loss', 'muscle_gain'],
        dietary_preferences: {
          diet_type: 'vegetarian',
          allergies: ['nuts', 'dairy'],
        },
        workout_schedule: {
          days_per_week: 4,
          preferred_days: ['monday', 'wednesday', 'friday', 'sunday'],
        },
      };

      const result = await onboardingService.saveStep(5, complexData);

      expect(api.post).toHaveBeenCalledWith('/onboarding/step', {
        step: 5,
        data: complexData,
      });
      expect(result.current_step).toBe(6);
    });
  });

  describe('completeOnboarding', () => {
    it('should call POST /onboarding/complete and return user profile', async () => {
      const mockProfileResponse: UserProfileResponse = {
        id: 'profile-123',
        user_id: 'user-123',
        is_locked: false,
        fitness_level: 'intermediate',
        fitness_goals: [],
        physical_constraints: [],
        dietary_preferences: null,
        meal_plan: null,
        meal_schedules: [],
        workout_schedules: [],
        hydration_preferences: null,
        lifestyle_baseline: null,
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockProfileResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.completeOnboarding();

      expect(api.post).toHaveBeenCalledWith('/onboarding/complete');
      expect(api.post).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockProfileResponse);
    });

    it('should return profile with locked status', async () => {
      const mockProfileResponse: UserProfileResponse = {
        id: 'profile-456',
        user_id: 'user-456',
        is_locked: true,
        fitness_level: 'advanced',
        fitness_goals: [],
        physical_constraints: [],
        dietary_preferences: null,
        meal_plan: null,
        meal_schedules: [],
        workout_schedules: [],
        hydration_preferences: null,
        lifestyle_baseline: null,
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockProfileResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.completeOnboarding();

      expect(result.is_locked).toBe(true);
    });

    it('should throw error when completion fails', async () => {
      const mockError = new Error('Onboarding not complete');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(onboardingService.completeOnboarding()).rejects.toThrow(
        'Onboarding not complete'
      );
    });

    it('should handle 400 error when onboarding is incomplete', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { detail: 'All steps must be completed' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(onboardingService.completeOnboarding()).rejects.toThrow();
    });
  });

  describe('getProgress (deprecated)', () => {
    it('should call getOnboardingState and map response', async () => {
      const mockStateResponse: OnboardingStateResponse = {
        id: 'onboarding-123',
        user_id: 'user-123',
        current_step: 5,
        is_complete: false,
        step_data: {},
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockStateResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.getProgress();

      expect(api.get).toHaveBeenCalledWith('/onboarding/state');
      expect(result).toEqual({
        currentStep: 5,
        completed: false,
      });
    });

    it('should show deprecation warning', async () => {
      const mockStateResponse: OnboardingStateResponse = {
        id: 'onboarding-123',
        user_id: 'user-123',
        current_step: 3,
        is_complete: false,
        step_data: {},
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockStateResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      await onboardingService.getProgress();

      expect(console.warn).toHaveBeenCalledWith(
        'getProgress() is deprecated. Use getOnboardingState() instead.'
      );
    });

    it('should map completed state correctly', async () => {
      const mockStateResponse: OnboardingStateResponse = {
        id: 'onboarding-456',
        user_id: 'user-456',
        current_step: 10,
        is_complete: true,
        step_data: {},
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockStateResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.getProgress();

      expect(result).toEqual({
        currentStep: 10,
        completed: true,
      });
    });

    it('should throw error when underlying call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(onboardingService.getProgress()).rejects.toThrow('Network error');
    });
  });
});
