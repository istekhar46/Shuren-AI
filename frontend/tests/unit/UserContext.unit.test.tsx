import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { UserProvider, useUser } from '../../src/contexts/UserContext';
import { authService } from '../../src/services/authService';
import { profileService } from '../../src/services/profileService';
import type { UserResponse, UserProfileResponse } from '../../src/types/api';
import type { ReactNode } from 'react';

// Mock the services
vi.mock('../../src/services/authService');
vi.mock('../../src/services/profileService');

describe('UserContext Onboarding Status Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <UserProvider>{children}</UserProvider>
  );

  describe('onboardingCompleted flag', () => {
    it('should fetch onboardingCompleted flag correctly on initialization', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-123',
        email: 'test@example.com',
        full_name: 'Test User',
        oauth_provider: null,
        is_active: true,
        onboarding_completed: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(authService.isAuthenticated).mockReturnValue(true);
      vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUserResponse);

      const { result } = renderHook(() => useUser(), { wrapper });

      // Initially loading
      expect(result.current.loading).toBe(true);

      // Wait for the onboarding status to be fetched
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(authService.getCurrentUser).toHaveBeenCalledTimes(1);
      expect(result.current.onboardingCompleted).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should set onboardingCompleted to false when user has not completed onboarding', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-456',
        email: 'newuser@example.com',
        full_name: 'New User',
        oauth_provider: null,
        is_active: true,
        onboarding_completed: false,
        created_at: '2024-01-15T00:00:00Z',
      };

      vi.mocked(authService.isAuthenticated).mockReturnValue(true);
      vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUserResponse);

      const { result } = renderHook(() => useUser(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.onboardingCompleted).toBe(false);
    });

    it('should not fetch onboarding status when user is not authenticated', async () => {
      vi.mocked(authService.isAuthenticated).mockReturnValue(false);

      const { result } = renderHook(() => useUser(), { wrapper });

      // Wait a bit to ensure no calls are made
      await new Promise((resolve) => setTimeout(resolve, 100));

      expect(authService.getCurrentUser).not.toHaveBeenCalled();
      expect(result.current.onboardingCompleted).toBe(false);
    });

    it('should handle errors gracefully when fetching onboarding status fails', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      vi.mocked(authService.isAuthenticated).mockReturnValue(true);
      vi.mocked(authService.getCurrentUser).mockRejectedValue(
        new Error('Network error')
      );

      const { result } = renderHook(() => useUser(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to fetch initial onboarding status:',
        expect.any(Error)
      );
      expect(result.current.onboardingCompleted).toBe(false);

      consoleErrorSpy.mockRestore();
    });
  });

  describe('refreshOnboardingStatus method', () => {
    it('should update onboardingCompleted flag when refreshOnboardingStatus is called', async () => {
      const initialUserResponse: UserResponse = {
        id: 'user-789',
        email: 'user@example.com',
        full_name: 'User',
        oauth_provider: null,
        is_active: true,
        onboarding_completed: false,
        created_at: '2024-01-01T00:00:00Z',
      };

      const updatedUserResponse: UserResponse = {
        ...initialUserResponse,
        onboarding_completed: true,
      };

      vi.mocked(authService.isAuthenticated).mockReturnValue(true);
      vi.mocked(authService.getCurrentUser)
        .mockResolvedValueOnce(initialUserResponse)
        .mockResolvedValueOnce(updatedUserResponse);

      const { result } = renderHook(() => useUser(), { wrapper });

      // Wait for initial fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.onboardingCompleted).toBe(false);

      // Call refreshOnboardingStatus wrapped in act
      await act(async () => {
        await result.current.refreshOnboardingStatus();
      });

      expect(authService.getCurrentUser).toHaveBeenCalledTimes(2);
      expect(result.current.onboardingCompleted).toBe(true);
    });

    it('should set loading state during refreshOnboardingStatus', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-123',
        email: 'test@example.com',
        full_name: 'Test User',
        oauth_provider: null,
        is_active: true,
        onboarding_completed: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(authService.isAuthenticated).mockReturnValue(true);
      vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUserResponse);

      const { result } = renderHook(() => useUser(), { wrapper });

      // Wait for initial fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Start refresh wrapped in act
      let refreshPromise: Promise<void>;
      act(() => {
        refreshPromise = result.current.refreshOnboardingStatus();
      });

      // Check loading state immediately after starting
      await waitFor(() => {
        expect(result.current.loading).toBe(true);
      });

      await act(async () => {
        await refreshPromise!;
      });

      // Should finish loading
      expect(result.current.loading).toBe(false);
    });

    it('should set error state when refreshOnboardingStatus fails', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-123',
        email: 'test@example.com',
        full_name: 'Test User',
        oauth_provider: null,
        is_active: true,
        onboarding_completed: false,
        created_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(authService.isAuthenticated).mockReturnValue(true);
      vi.mocked(authService.getCurrentUser)
        .mockResolvedValueOnce(mockUserResponse)
        .mockRejectedValueOnce(new Error('Failed to fetch user'));

      const { result } = renderHook(() => useUser(), { wrapper });

      // Wait for initial fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Call refreshOnboardingStatus and expect it to throw
      await act(async () => {
        await expect(result.current.refreshOnboardingStatus()).rejects.toThrow(
          'Failed to fetch user'
        );
      });

      // Error message should be set (the actual error message from the catch block)
      expect(result.current.error).toBe('Failed to fetch user');
    });

    it('should clear previous error when refreshOnboardingStatus succeeds', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-123',
        email: 'test@example.com',
        full_name: 'Test User',
        oauth_provider: null,
        is_active: true,
        onboarding_completed: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      vi.mocked(authService.isAuthenticated).mockReturnValue(true);
      vi.mocked(authService.getCurrentUser)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockUserResponse);

      const { result } = renderHook(() => useUser(), { wrapper });

      // Wait for initial fetch to fail
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Call refreshOnboardingStatus successfully
      await act(async () => {
        await result.current.refreshOnboardingStatus();
      });

      expect(result.current.error).toBeNull();
      expect(result.current.onboardingCompleted).toBe(true);

      consoleErrorSpy.mockRestore();
    });
  });

  describe('context initial state', () => {
    it('should provide correct initial state before data is fetched', () => {
      vi.mocked(authService.isAuthenticated).mockReturnValue(false);

      const { result } = renderHook(() => useUser(), { wrapper });

      expect(result.current.profile).toBeNull();
      expect(result.current.onboardingCompleted).toBe(false);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(typeof result.current.refreshProfile).toBe('function');
      expect(typeof result.current.refreshOnboardingStatus).toBe('function');
      expect(typeof result.current.unlockProfile).toBe('function');
    });

    it('should throw error when useUser is called outside UserProvider', () => {
      expect(() => {
        renderHook(() => useUser());
      }).toThrow('useUser must be used within a UserProvider');
    });
  });

  describe('integration with other context methods', () => {
    it('should maintain onboardingCompleted state when refreshProfile is called', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-123',
        email: 'test@example.com',
        full_name: 'Test User',
        oauth_provider: null,
        is_active: true,
        onboarding_completed: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      const mockProfileResponse: UserProfileResponse = {
        id: 'profile-123',
        user_id: 'user-123',
        fitness_level: 'intermediate',
        is_locked: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(authService.isAuthenticated).mockReturnValue(true);
      vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUserResponse);
      vi.mocked(profileService.getProfile).mockResolvedValue(mockProfileResponse);

      const { result } = renderHook(() => useUser(), { wrapper });

      // Wait for initial onboarding status fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.onboardingCompleted).toBe(true);

      // Call refreshProfile wrapped in act
      await act(async () => {
        await result.current.refreshProfile();
      });

      // onboardingCompleted should remain unchanged
      expect(result.current.onboardingCompleted).toBe(true);
      expect(result.current.profile).toEqual(mockProfileResponse);
    });

    it('should maintain onboardingCompleted state independently of profile operations', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-123',
        email: 'test@example.com',
        full_name: 'Test User',
        oauth_provider: null,
        is_active: true,
        onboarding_completed: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      const mockProfileResponse: UserProfileResponse = {
        id: 'profile-123',
        user_id: 'user-123',
        fitness_level: 'intermediate',
        is_locked: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(authService.isAuthenticated).mockReturnValue(true);
      vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUserResponse);
      
      // Mock unlockProfile as a function
      vi.mocked(profileService).unlockProfile = vi.fn().mockResolvedValue(mockProfileResponse);
      vi.mocked(profileService.getProfile).mockResolvedValue(mockProfileResponse);

      const { result } = renderHook(() => useUser(), { wrapper });

      // Wait for initial onboarding status fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.onboardingCompleted).toBe(true);

      // Call unlockProfile (which internally calls refreshProfile)
      await act(async () => {
        await result.current.unlockProfile();
      });

      // onboardingCompleted should remain unchanged
      expect(result.current.onboardingCompleted).toBe(true);
    });
  });
});
