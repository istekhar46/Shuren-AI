/**
 * Environment configuration
 * Centralizes access to environment variables with validation
 */

export const env = {
  // API Configuration
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  
  // LiveKit Configuration
  livekitUrl: import.meta.env.VITE_LIVEKIT_URL || 'ws://localhost:7880',
  
  // Google OAuth Configuration
  googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
} as const;

/**
 * Validates that required environment variables are set
 * @throws Error if required variables are missing
 */
export function validateEnv(): void {
  const errors: string[] = [];

  if (!env.apiBaseUrl) {
    errors.push('VITE_API_BASE_URL is not set');
  }

  if (errors.length > 0) {
    throw new Error(`Environment validation failed:\n${errors.join('\n')}`);
  }
}

/**
 * Checks if Google OAuth is configured
 * @returns true if Google Client ID is set
 */
export function isGoogleOAuthEnabled(): boolean {
  return env.googleClientId.length > 0;
}
