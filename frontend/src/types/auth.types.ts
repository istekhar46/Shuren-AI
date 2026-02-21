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

/**
 * Google OAuth authentication request payload
 * Sent to POST /auth/google
 * 
 * This payload contains the Google ID token (credential) and CSRF token
 * for secure authentication via Google Identity Services.
 */
export interface GoogleAuthRequest {
  /**
   * The Google ID token (JWT) returned by Google Identity Services
   * This token is validated by the backend to authenticate the user
   */
  credential: string;

  /**
   * CSRF token extracted from the g_csrf_token cookie
   * Used for double-submit-cookie CSRF protection
   */
  g_csrf_token: string;
}

/**
 * Google OAuth authentication response
 * Returned by POST /auth/google
 * 
 * This response is identical to TokenResponse, containing the JWT access token
 * and user ID for authenticated sessions.
 */
export interface GoogleAuthResponse extends TokenResponse {
  // Inherits all fields from TokenResponse:
  // - access_token: string
  // - token_type: string
  // - user_id: string
}
