import api from './api';
import type { UserProfileResponse, ProfileUpdateRequest } from '../types/api';
import type { UserProfile } from '../types';

/**
 * Profile Service
 * 
 * Handles user profile operations including retrieval, updates, and locking.
 * All operations require authentication.
 */
export const profileService = {
  /**
   * Get the current user's profile
   * 
   * Retrieves the complete user profile including fitness level, goals,
   * dietary preferences, meal plans, workout schedules, and all related data.
   * 
   * @returns {Promise<UserProfileResponse>} Complete user profile with all relationships
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * const profile = await profileService.getProfile();
   * console.log(profile.fitness_level); // 'intermediate'
   */
  async getProfile(): Promise<UserProfile> {
    const response = await api.get('/profiles/me');
    return mapProfileResponseToUserProfile(response.data);
  },

  /**
   * Update the user's profile
   * 
   * Updates specific fields in the user's profile. For locked profiles,
   * a reason must be provided. Uses PATCH method for partial updates.
   * 
   * @param {Record<string, any>} updates - Object containing fields to update
   * @param {string} [reason='User requested update'] - Reason for update (required for locked profiles)
   * @returns {Promise<UserProfileResponse>} Updated user profile
   * @throws {Error} If the request fails, validation fails, or profile is locked without valid reason
   * 
   * @example
   * const updated = await profileService.updateProfile(
   *   { fitness_level: 'advanced' },
   *   'User completed intermediate program'
   * );
   */
  async updateProfile(
    updates: Record<string, any>,
    reason: string = 'User requested update'
  ): Promise<UserProfile> {
    const payload: ProfileUpdateRequest = { updates, reason };
    const response = await api.patch('/profiles/me', payload);
    return mapProfileResponseToUserProfile(response.data);
  },

  /**
   * Lock user's profile to prevent modifications
   * 
   * Locks the profile to prevent accidental or unauthorized changes.
   * Once locked, updates require a valid reason. This is typically used
   * after onboarding is complete to maintain plan consistency.
   * 
   * @returns {Promise<UserProfileResponse>} Updated user profile with is_locked=true
   * @throws {Error} If the request fails or profile is already locked
   * 
   * @example
   * const locked = await profileService.lockProfile();
   * console.log(locked.is_locked); // true
   */
  async lockProfile(): Promise<UserProfile> {
    const response = await api.post('/profiles/me/lock');
    return mapProfileResponseToUserProfile(response.data);
  },
};

/**
 * Maps the backend UserProfileResponse to the frontend UserProfile format
 */
export function mapProfileResponseToUserProfile(response: UserProfileResponse): UserProfile {
  return {
    id: response.id,
    email: '', // Not provided in profile response
    fitnessLevel: response.fitness_level as any,
    goals: response.fitness_goals?.map(g => ({
      type: g.goal_type as any,
      targetWeight: g.target_value || undefined,
      targetDate: g.target_date || undefined
    })) || [],
    physicalConstraints: response.physical_constraints?.map(c => ({
      type: c.constraint_type as any,
      description: c.description
    })) || [],
    dietaryPreferences: response.dietary_preferences ? {
      dietType: response.dietary_preferences.diet_type as any,
      allergies: response.dietary_preferences.allergies || [],
      dislikes: response.dietary_preferences.dislikes || []
    } : { dietType: 'omnivore', allergies: [], dislikes: [] },
    mealPlan: response.meal_plan ? {
      dailyCalories: (response.meal_plan as any).daily_calorie_target || response.meal_plan.daily_calories_target || 0,
      macros: {
        protein: Math.round((((response.meal_plan as any).daily_calorie_target || response.meal_plan.daily_calories_target || 0) * (response.meal_plan.protein_percentage / 100)) / 4),
        carbs: Math.round((((response.meal_plan as any).daily_calorie_target || response.meal_plan.daily_calories_target || 0) * (response.meal_plan.carbs_percentage / 100)) / 4),
        fats: Math.round((((response.meal_plan as any).daily_calorie_target || response.meal_plan.daily_calories_target || 0) * (response.meal_plan.fats_percentage / 100)) / 9),
      },
      mealsPerDay: response.meal_schedules?.length || 3
    } : { dailyCalories: 0, macros: { protein: 0, carbs: 0, fats: 0 }, mealsPerDay: 3 },
    mealSchedule: response.meal_schedules?.map(s => ({
      mealType: s.meal_name as any,
      time: s.scheduled_time
    })) || [],
    workoutSchedule: {
      daysPerWeek: response.workout_schedules?.length || 0,
      preferredDays: response.workout_schedules?.map(s => ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][s.day_of_week]) || [],
      preferredTime: response.workout_schedules?.[0]?.scheduled_time || '07:00:00',
      sessionDuration: 45
    },
    hydrationPreferences: response.hydration_preferences ? {
      dailyGoal: response.hydration_preferences.daily_water_target_ml / 1000,
      reminderInterval: response.hydration_preferences.reminder_interval_minutes || 60
    } : { dailyGoal: 2.5, reminderInterval: 60 },
    lifestyleBaseline: response.lifestyle_baseline ? {
      energyLevel: response.lifestyle_baseline.energy_level > 7 ? 'high' : response.lifestyle_baseline.energy_level > 4 ? 'medium' : 'low',
      stressLevel: response.lifestyle_baseline.stress_level > 7 ? 'high' : response.lifestyle_baseline.stress_level > 4 ? 'medium' : 'low',
      sleepQuality: response.lifestyle_baseline.sleep_hours > 8 ? 'excellent' : response.lifestyle_baseline.sleep_hours > 6 ? 'good' : response.lifestyle_baseline.sleep_hours > 4 ? 'fair' : 'poor'
    } : { energyLevel: 'high', stressLevel: 'low', sleepQuality: 'excellent' },
    notificationPreferences: {
      workoutReminders: true,
      mealReminders: true,
      hydrationReminders: true,
      motivationalMessages: true
    },
    isLocked: response.is_locked,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
}
