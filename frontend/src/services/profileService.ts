import api from './api';
import type { UserProfileResponse, ProfileUpdateRequest } from '../types/api';

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
  async getProfile(): Promise<UserProfileResponse> {
    const response = await api.get('/profiles/me');
    return response.data;
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
  ): Promise<UserProfileResponse> {
    const payload: ProfileUpdateRequest = { updates, reason };
    const response = await api.patch('/profiles/me', payload);
    return response.data;
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
  async lockProfile(): Promise<UserProfileResponse> {
    const response = await api.post('/profiles/me/lock');
    return response.data;
  },
};
