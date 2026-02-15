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

  describe('getOnboardingProgress', () => {
    it('should call GET /onboarding/progress and return progress data', async () => {
      const mockProgressResponse = {
        current_state: 3,
        total_states: 9,
        completed_states: [1, 2],
        is_complete: false,
        completion_percentage: 33,
        current_state_info: {
          state_number: 3,
          name: 'Workout Preferences',
          agent: 'workout_planning',
          description: 'Configure your workout preferences and constraints',
          required_fields: ['equipment', 'workout_days'],
        },
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockProgressResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.getOnboardingProgress();

      expect(api.get).toHaveBeenCalledWith('/onboarding/progress');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockProgressResponse);
      expect(result.current_state).toBe(3);
      expect(result.total_states).toBe(9);
      expect(result.completed_states).toEqual([1, 2]);
      expect(result.is_complete).toBe(false);
      expect(result.completion_percentage).toBe(33);
    });

    it('should parse response with complete onboarding', async () => {
      const mockProgressResponse = {
        current_state: 9,
        total_states: 9,
        completed_states: [1, 2, 3, 4, 5, 6, 7, 8, 9],
        is_complete: true,
        completion_percentage: 100,
        current_state_info: {
          state_number: 9,
          name: 'Supplement Preferences',
          agent: 'supplement_guidance',
          description: 'Configure supplement preferences',
          required_fields: ['supplements'],
        },
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockProgressResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.getOnboardingProgress();

      expect(result.is_complete).toBe(true);
      expect(result.completion_percentage).toBe(100);
      expect(result.completed_states).toHaveLength(9);
    });

    it('should parse response with state metadata', async () => {
      const mockProgressResponse = {
        current_state: 1,
        total_states: 9,
        completed_states: [],
        is_complete: false,
        completion_percentage: 11,
        current_state_info: {
          state_number: 1,
          name: 'Fitness Level Assessment',
          agent: 'workout_planning',
          description: 'Assess your current fitness level',
          required_fields: ['fitness_level', 'experience'],
        },
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockProgressResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.getOnboardingProgress();

      expect(result.current_state_info).toBeDefined();
      expect(result.current_state_info.name).toBe('Fitness Level Assessment');
      expect(result.current_state_info.agent).toBe('workout_planning');
      expect(result.current_state_info.description).toBe('Assess your current fitness level');
      expect(result.current_state_info.required_fields).toEqual(['fitness_level', 'experience']);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(onboardingService.getOnboardingProgress()).rejects.toThrow('Network error');
      expect(api.get).toHaveBeenCalledWith('/onboarding/progress');
    });

    it('should handle 401 unauthorized error', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(onboardingService.getOnboardingProgress()).rejects.toThrow();
    });

    it('should handle 500 server error', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(onboardingService.getOnboardingProgress()).rejects.toThrow();
    });
  });

  describe('sendOnboardingMessage', () => {
    it('should call POST /chat/onboarding with correct payload', async () => {
      const mockChatResponse = {
        response: 'Great! I understand you are a beginner. Let me help you get started.',
        agent_type: 'workout_planning',
        state_updated: true,
        new_state: 2,
        is_complete: false,
        progress: {
          current_state: 2,
          completion_percentage: 22,
        },
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.sendOnboardingMessage('I am a beginner', 1);

      expect(api.post).toHaveBeenCalledWith('/chat/onboarding', {
        message: 'I am a beginner',
        current_state: 1,
      });
      expect(api.post).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockChatResponse);
    });

    it('should send correct payload with different state numbers', async () => {
      const mockChatResponse = {
        response: 'Perfect! Your workout preferences have been saved.',
        agent_type: 'workout_planning',
        state_updated: true,
        new_state: 4,
        is_complete: false,
        progress: {
          current_state: 4,
          completion_percentage: 44,
        },
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.sendOnboardingMessage(
        'I have a home gym with dumbbells',
        3
      );

      expect(api.post).toHaveBeenCalledWith('/chat/onboarding', {
        message: 'I have a home gym with dumbbells',
        current_state: 3,
      });
      expect(result.state_updated).toBe(true);
      expect(result.new_state).toBe(4);
    });

    it('should handle response when state is not updated', async () => {
      const mockChatResponse = {
        response: 'Could you provide more details about your fitness level?',
        agent_type: 'workout_planning',
        state_updated: false,
        is_complete: false,
        progress: {
          current_state: 1,
          completion_percentage: 11,
        },
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.sendOnboardingMessage('I want to get fit', 1);

      expect(result.state_updated).toBe(false);
      expect(result.new_state).toBeUndefined();
    });

    it('should handle completion response', async () => {
      const mockChatResponse = {
        response: 'Congratulations! Your onboarding is complete.',
        agent_type: 'supplement_guidance',
        state_updated: true,
        new_state: 9,
        is_complete: true,
        progress: {
          current_state: 9,
          completion_percentage: 100,
        },
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.sendOnboardingMessage('No supplements for me', 9);

      expect(result.is_complete).toBe(true);
      expect(result.progress.completion_percentage).toBe(100);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(
        onboardingService.sendOnboardingMessage('test message', 1)
      ).rejects.toThrow('Network error');
      expect(api.post).toHaveBeenCalledWith('/chat/onboarding', {
        message: 'test message',
        current_state: 1,
      });
    });

    it('should handle 400 validation error', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { detail: 'Invalid state number' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(
        onboardingService.sendOnboardingMessage('test', 99)
      ).rejects.toThrow();
    });

    it('should handle 403 onboarding already complete error', async () => {
      const mockError = {
        response: {
          status: 403,
          data: { detail: 'Onboarding already completed' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(
        onboardingService.sendOnboardingMessage('test', 1)
      ).rejects.toThrow();
    });

    it('should handle empty message', async () => {
      const mockChatResponse = {
        response: 'Please provide a valid response.',
        agent_type: 'workout_planning',
        state_updated: false,
        is_complete: false,
        progress: {
          current_state: 1,
          completion_percentage: 11,
        },
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.sendOnboardingMessage('', 1);

      expect(api.post).toHaveBeenCalledWith('/chat/onboarding', {
        message: '',
        current_state: 1,
      });
      expect(result.state_updated).toBe(false);
    });

    it('should handle long message', async () => {
      const longMessage = 'I am a beginner with no prior experience. '.repeat(20);
      const mockChatResponse = {
        response: 'Thank you for the detailed information.',
        agent_type: 'workout_planning',
        state_updated: true,
        new_state: 2,
        is_complete: false,
        progress: {
          current_state: 2,
          completion_percentage: 22,
        },
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockChatResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await onboardingService.sendOnboardingMessage(longMessage, 1);

      expect(api.post).toHaveBeenCalledWith('/chat/onboarding', {
        message: longMessage,
        current_state: 1,
      });
      expect(result.state_updated).toBe(true);
    });

    it('should handle network timeout error', async () => {
      const mockError = {
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded',
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(
        onboardingService.sendOnboardingMessage('test', 1)
      ).rejects.toThrow();
    });
  });
});
