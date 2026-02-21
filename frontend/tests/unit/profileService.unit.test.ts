import { describe, it, expect, vi, beforeEach } from 'vitest';
import { profileService } from '../../src/services/profileService';
import api from '../../src/services/api';
import type { UserProfileResponse, ProfileUpdateRequest } from '../../src/types/api';

// Mock the api module
vi.mock('../../src/services/api');

describe('profileService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getProfile', () => {
    it('should call GET /profiles/me and return profile data', async () => {
      const mockProfileResponse: UserProfileResponse = {
        id: 'profile-123',
        user_id: 'user-123',
        is_locked: false,
        fitness_level: 'intermediate',
        fitness_goals: [
          {
            id: 'goal-1',
            goal_type: 'fat_loss',
            target_value: 10,
            target_unit: 'kg',
            target_date: '2024-06-01',
            priority: 1,
            is_active: true,
          },
        ],
        physical_constraints: [],
        dietary_preferences: {
          id: 'diet-1',
          diet_type: 'vegetarian',
          allergies: ['peanuts'],
          dislikes: ['mushrooms'],
          preferred_cuisines: ['indian', 'italian'],
          meals_per_day: 3,
        },
        meal_plan: null,
        meal_schedules: [],
        workout_schedules: [],
        hydration_preferences: null,
        lifestyle_baseline: null,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockProfileResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await profileService.getProfile();

      expect(api.get).toHaveBeenCalledWith('/profiles/me');
      expect(api.get).toHaveBeenCalledTimes(1);
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

      vi.mocked(api.get).mockResolvedValue({
        data: mockProfileResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await profileService.getProfile();

      expect(result.is_locked).toBe(true);
      expect(result.fitness_level).toBe('advanced');
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(profileService.getProfile()).rejects.toThrow('Network error');
      expect(api.get).toHaveBeenCalledWith('/profiles/me');
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(profileService.getProfile()).rejects.toThrow();
      expect(api.get).toHaveBeenCalledWith('/profiles/me');
    });

    it('should throw error when profile not found (404)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Profile not found' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(profileService.getProfile()).rejects.toThrow();
      expect(api.get).toHaveBeenCalledWith('/profiles/me');
    });
  });

  describe('updateProfile', () => {
    it('should call PATCH /profiles/me with correct payload', async () => {
      const updates = { fitness_level: 'advanced' };
      const reason = 'User completed intermediate program';

      const mockProfileResponse: UserProfileResponse = {
        id: 'profile-123',
        user_id: 'user-123',
        is_locked: false,
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

      vi.mocked(api.patch).mockResolvedValue({
        data: mockProfileResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await profileService.updateProfile(updates, reason);

      const expectedPayload: ProfileUpdateRequest = {
        updates,
        reason,
      };

      expect(api.patch).toHaveBeenCalledWith('/profiles/me', expectedPayload);
      expect(api.patch).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockProfileResponse);
      expect(result.fitness_level).toBe('advanced');
    });

    it('should use default reason when not provided', async () => {
      const updates = { fitness_level: 'beginner' };

      const mockProfileResponse: UserProfileResponse = {
        id: 'profile-123',
        user_id: 'user-123',
        is_locked: false,
        fitness_level: 'beginner',
        fitness_goals: [],
        physical_constraints: [],
        dietary_preferences: null,
        meal_plan: null,
        meal_schedules: [],
        workout_schedules: [],
        hydration_preferences: null,
        lifestyle_baseline: null,
      };

      vi.mocked(api.patch).mockResolvedValue({
        data: mockProfileResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await profileService.updateProfile(updates);

      const expectedPayload: ProfileUpdateRequest = {
        updates,
        reason: 'User requested update',
      };

      expect(api.patch).toHaveBeenCalledWith('/profiles/me', expectedPayload);
      expect(result.fitness_level).toBe('beginner');
    });

    it('should update multiple fields at once', async () => {
      const updates = {
        fitness_level: 'advanced',
        dietary_preferences: {
          diet_type: 'vegan',
          allergies: [],
        },
      };

      const mockProfileResponse: UserProfileResponse = {
        id: 'profile-123',
        user_id: 'user-123',
        is_locked: false,
        fitness_level: 'advanced',
        fitness_goals: [],
        physical_constraints: [],
        dietary_preferences: {
          id: 'diet-1',
          diet_type: 'vegan',
          allergies: [],
          dislikes: [],
          preferred_cuisines: [],
          meals_per_day: 3,
        },
        meal_plan: null,
        meal_schedules: [],
        workout_schedules: [],
        hydration_preferences: null,
        lifestyle_baseline: null,
      };

      vi.mocked(api.patch).mockResolvedValue({
        data: mockProfileResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await profileService.updateProfile(updates, 'Switching to vegan diet');

      expect(api.patch).toHaveBeenCalledWith('/profiles/me', {
        updates,
        reason: 'Switching to vegan diet',
      });
      expect(result.fitness_level).toBe('advanced');
      expect(result.dietary_preferences?.diet_type).toBe('vegan');
    });

    it('should throw error when validation fails (422)', async () => {
      const mockError = {
        response: {
          status: 422,
          data: { detail: 'Invalid fitness level' },
        },
      };
      vi.mocked(api.patch).mockRejectedValue(mockError);

      await expect(
        profileService.updateProfile({ fitness_level: 'invalid' })
      ).rejects.toThrow();
      expect(api.patch).toHaveBeenCalledWith('/profiles/me', {
        updates: { fitness_level: 'invalid' },
        reason: 'User requested update',
      });
    });

    it('should throw error when profile is locked without valid reason', async () => {
      const mockError = {
        response: {
          status: 403,
          data: { detail: 'Profile is locked' },
        },
      };
      vi.mocked(api.patch).mockRejectedValue(mockError);

      await expect(
        profileService.updateProfile({ fitness_level: 'advanced' })
      ).rejects.toThrow();
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.patch).mockRejectedValue(mockError);

      await expect(
        profileService.updateProfile({ fitness_level: 'advanced' })
      ).rejects.toThrow('Network error');
    });

    it('should handle empty updates object', async () => {
      const updates = {};

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

      vi.mocked(api.patch).mockResolvedValue({
        data: mockProfileResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await profileService.updateProfile(updates);

      expect(api.patch).toHaveBeenCalledWith('/profiles/me', {
        updates: {},
        reason: 'User requested update',
      });
      expect(result).toEqual(mockProfileResponse);
    });
  });

  describe('lockProfile', () => {
    it('should call POST /profiles/me/lock and return locked profile', async () => {
      const mockProfileResponse: UserProfileResponse = {
        id: 'profile-123',
        user_id: 'user-123',
        is_locked: true,
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

      const result = await profileService.lockProfile();

      expect(api.post).toHaveBeenCalledWith('/profiles/me/lock');
      expect(api.post).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockProfileResponse);
      expect(result.is_locked).toBe(true);
    });

    it('should throw error when profile is already locked', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { detail: 'Profile is already locked' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(profileService.lockProfile()).rejects.toThrow();
      expect(api.post).toHaveBeenCalledWith('/profiles/me/lock');
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(profileService.lockProfile()).rejects.toThrow();
      expect(api.post).toHaveBeenCalledWith('/profiles/me/lock');
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(profileService.lockProfile()).rejects.toThrow('Network error');
      expect(api.post).toHaveBeenCalledWith('/profiles/me/lock');
    });

    it('should throw error when profile not found (404)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Profile not found' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(profileService.lockProfile()).rejects.toThrow();
      expect(api.post).toHaveBeenCalledWith('/profiles/me/lock');
    });
  });
});
