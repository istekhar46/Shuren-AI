import React, { createContext, useContext, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { UserProfile } from '../types';
import { profileService } from '../services/profileService';

interface UserContextType {
  profile: UserProfile | null;
  refreshProfile: () => Promise<void>;
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
      setProfile(fetchedProfile);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch profile';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Unlock the user's profile for editing
   * After unlocking, refresh the profile to get the updated lock status
   */
  const unlockProfile = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      await profileService.unlockProfile();
      // Refresh profile to get updated lock status
      await refreshProfile();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to unlock profile';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [refreshProfile]);

  const value: UserContextType = {
    profile,
    refreshProfile,
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
