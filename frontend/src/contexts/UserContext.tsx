import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { UserProfile } from '../types';
import { profileService } from '../services/profileService';
import { authService } from '../services/authService';

interface UserContextType {
  profile: UserProfile | null;
  onboardingCompleted: boolean;
  refreshProfile: () => Promise<void>;
  refreshOnboardingStatus: () => Promise<void>;
  unlockProfile: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

interface UserProviderProps {
  children: ReactNode;
}

export const UserProvider: React.FC<UserProviderProps> = ({ children }) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [onboardingCompleted, setOnboardingCompleted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch and refresh the user's profile from the backend
   */
  const refreshProfile = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const fetchedProfile = await profileService.getProfile();
      // Cast UserProfileResponse to UserProfile for context state
      setProfile(fetchedProfile as any);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch profile';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch and refresh the user's onboarding status from the backend
   */
  const refreshOnboardingStatus = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const userData = await authService.getCurrentUser();
      setOnboardingCompleted(userData.onboarding_completed);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch onboarding status';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Unlock the user's profile for editing
   * After unlocking, refresh the profile to get the updated lock status
   * Note: unlockProfile method doesn't exist in profileService yet
   */
  const unlockProfile = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      // TODO: Implement unlockProfile in profileService when backend endpoint is available
      // For now, just refresh the profile
      await refreshProfile();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to unlock profile';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [refreshProfile]);

  /**
   * Fetch onboarding status on context initialization
   */
  useEffect(() => {
    const initializeOnboardingStatus = async () => {
      if (authService.isAuthenticated()) {
        try {
          await refreshOnboardingStatus();
        } catch (err) {
          // Silently fail - user might not be authenticated yet
          console.error('Failed to fetch initial onboarding status:', err);
        }
      }
    };

    initializeOnboardingStatus();
  }, [refreshOnboardingStatus]);

  const value: UserContextType = {
    profile,
    onboardingCompleted,
    refreshProfile,
    refreshOnboardingStatus,
    unlockProfile,
    loading,
    error,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

export const useUser = (): UserContextType => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
