import api from './api';
import type { TokenResponse, UserResponse, LoginRequest, RegisterRequest } from '../types/api';

/**
 * Authentication service for handling user registration, login, and logout
 */
export const authService = {
  /**
   * Register a new user
   * @param email User's email address
   * @param password User's password
   * @param fullName User's full name
   * @returns Authentication response with token and user data
   */
  async register(email: string, password: string, fullName: string): Promise<TokenResponse> {
    const payload: RegisterRequest = { email, password, full_name: fullName };
    const response = await api.post<TokenResponse>('/auth/register', payload);
    return response.data;
  },

  /**
   * Log in an existing user
   * @param email User's email address
   * @param password User's password
   * @returns Authentication response with token and user data
   */
  async login(email: string, password: string): Promise<TokenResponse> {
    const payload: LoginRequest = { email, password };
    const response = await api.post<TokenResponse>('/auth/login', payload);
    return response.data;
  },

  /**
   * Get current authenticated user information
   * @returns Current user details
   * @throws Error if not authenticated or request fails
   */
  async getCurrentUser(): Promise<UserResponse> {
    const response = await api.get<UserResponse>('/auth/me');
    return response.data;
  },

  /**
   * Log out the current user by clearing stored token
   */
  logout(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  },

  /**
   * Get the stored authentication token
   * @returns JWT token or null if not authenticated
   */
  getToken(): string | null {
    return localStorage.getItem('auth_token');
  },

  /**
   * Set the authentication token in localStorage
   * @param token JWT token to store
   */
  setToken(token: string): void {
    localStorage.setItem('auth_token', token);
  },

  /**
   * Check if user is currently authenticated
   * @returns true if token exists, false otherwise
   */
  isAuthenticated(): boolean {
    return !!this.getToken();
  },
};
