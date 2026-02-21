/**
 * Authentication Type Definitions
 * 
 * These types define the structure of authentication-related requests and responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

/**
 * Response from successful authentication (login/register)
 * Returned by POST /auth/login and POST /auth/register
 */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

/**
 * User information response
 * Returned by GET /auth/me
 */
export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  oauth_provider: string | null;
  is_active: boolean;
  onboarding_completed: boolean;
  created_at: string;
}

/**
 * Login request payload
 * Sent to POST /auth/login
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Registration request payload
 * Sent to POST /auth/register
 */
export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}
