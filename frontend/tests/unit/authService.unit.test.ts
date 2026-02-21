import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authService } from '../../src/services/authService';
import api from '../../src/services/api';
import type { TokenResponse, UserResponse } from '../../src/types/api';

// Mock the api module
vi.mock('../../src/services/api');

describe('authService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('getCurrentUser', () => {
    it('should call GET /auth/me and return user data', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-123',
        email: 'test@example.com',
        full_name: 'Test User',
        oauth_provider: null,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockUserResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await authService.getCurrentUser();

      expect(api.get).toHaveBeenCalledWith('/auth/me');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockUserResponse);
    });

    it('should return user with OAuth provider', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-456',
        email: 'oauth@example.com',
        full_name: 'OAuth User',
        oauth_provider: 'google',
        is_active: true,
        created_at: '2024-01-15T10:30:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockUserResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await authService.getCurrentUser();

      expect(result.oauth_provider).toBe('google');
      expect(result.email).toBe('oauth@example.com');
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(authService.getCurrentUser()).rejects.toThrow('Network error');
      expect(api.get).toHaveBeenCalledWith('/auth/me');
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(authService.getCurrentUser()).rejects.toThrow();
      expect(api.get).toHaveBeenCalledWith('/auth/me');
    });

    it('should handle inactive user', async () => {
      const mockUserResponse: UserResponse = {
        id: 'user-789',
        email: 'inactive@example.com',
        full_name: 'Inactive User',
        oauth_provider: null,
        is_active: false,
        created_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockUserResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await authService.getCurrentUser();

      expect(result.is_active).toBe(false);
    });
  });

  describe('register', () => {
    it('should call POST /auth/register with correct payload', async () => {
      const mockTokenResponse: TokenResponse = {
        access_token: 'token-123',
        token_type: 'bearer',
        user_id: 'user-123',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockTokenResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await authService.register('test@example.com', 'password123');

      expect(api.post).toHaveBeenCalledWith('/auth/register', {
        email: 'test@example.com',
        password: 'password123',
      });
      expect(result).toEqual(mockTokenResponse);
    });

    it('should throw error when registration fails', async () => {
      const mockError = new Error('Email already exists');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(authService.register('existing@example.com', 'password123')).rejects.toThrow(
        'Email already exists'
      );
    });
  });

  describe('login', () => {
    it('should call POST /auth/login with correct payload', async () => {
      const mockTokenResponse: TokenResponse = {
        access_token: 'token-456',
        token_type: 'bearer',
        user_id: 'user-456',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockTokenResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await authService.login('test@example.com', 'password123');

      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      });
      expect(result).toEqual(mockTokenResponse);
    });

    it('should throw error when login fails with invalid credentials', async () => {
      const mockError = new Error('Invalid credentials');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(authService.login('test@example.com', 'wrongpassword')).rejects.toThrow(
        'Invalid credentials'
      );
    });
  });

  describe('logout', () => {
    it('should remove auth_token from localStorage', () => {
      localStorage.setItem('auth_token', 'token-123');
      localStorage.setItem('auth_user', JSON.stringify({ id: 'user-123' }));

      authService.logout();

      expect(localStorage.getItem('auth_token')).toBeNull();
      expect(localStorage.getItem('auth_user')).toBeNull();
    });

    it('should not throw error when tokens do not exist', () => {
      expect(() => authService.logout()).not.toThrow();
    });
  });

  describe('getToken', () => {
    it('should return token from localStorage', () => {
      localStorage.setItem('auth_token', 'token-789');

      const token = authService.getToken();

      expect(token).toBe('token-789');
    });

    it('should return null when token does not exist', () => {
      const token = authService.getToken();

      expect(token).toBeNull();
    });
  });

  describe('setToken', () => {
    it('should store token in localStorage', () => {
      authService.setToken('new-token-123');

      expect(localStorage.getItem('auth_token')).toBe('new-token-123');
    });

    it('should overwrite existing token', () => {
      localStorage.setItem('auth_token', 'old-token');

      authService.setToken('new-token');

      expect(localStorage.getItem('auth_token')).toBe('new-token');
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when token exists', () => {
      localStorage.setItem('auth_token', 'token-123');

      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should return false when token does not exist', () => {
      expect(authService.isAuthenticated()).toBe(false);
    });

    it('should return false when token is empty string', () => {
      localStorage.setItem('auth_token', '');

      expect(authService.isAuthenticated()).toBe(false);
    });
  });
});
