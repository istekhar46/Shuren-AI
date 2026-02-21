import { useEffect, useRef, useState } from 'react';
import type { TokenResponse } from '../../types/auth.types';
import { env } from '../../config/env';
import { getCookie } from '../../utils/cookies';

/**
 * Google credential response from Google Identity Services
 */
interface CredentialResponse {
  credential: string;
  select_by: string;
}

/**
 * Props for GoogleSignInButton component
 */
interface GoogleSignInButtonProps {
  /**
   * Callback invoked when Google authentication succeeds
   * @param response - The authentication response with token and user ID
   */
  onSuccess: (response: TokenResponse) => void;

  /**
   * Callback invoked when Google authentication fails
   * @param error - The error that occurred during authentication
   */
  onError: (error: Error) => void;

  /**
   * Whether the button should be disabled
   * @default false
   */
  disabled?: boolean;
}

/**
 * Google Sign-In Button Component
 * 
 * Renders the official Google Sign-In button using Google Identity Services.
 * Handles script loading, initialization, and authentication flow.
 * 
 * Implementation follows official Google Identity Services documentation:
 * https://developers.google.com/identity/gsi/web/guides/display-button
 * 
 * @example
 * ```tsx
 * <GoogleSignInButton
 *   onSuccess={(response) => console.log('Authenticated:', response)}
 *   onError={(error) => console.error('Auth failed:', error)}
 *   disabled={isLoading}
 * />
 * ```
 */
export function GoogleSignInButton({ onSuccess, onError, disabled = false }: GoogleSignInButtonProps) {
  const [loading, setLoading] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const buttonContainerRef = useRef<HTMLDivElement>(null);
  const initializationAttempted = useRef(false);

  // Credential response handler
  const handleCredentialResponse = async (response: CredentialResponse) => {
    try {
      // Set loading state
      setLoading(true);

      // Extract credential from Google response
      const { credential } = response;

      // Extract CSRF token from cookies (optional for button flow)
      // Google Identity Services only sets g_csrf_token for One Tap flow
      // For button flow, we send empty string or the token if available
      const csrfToken = getCookie('g_csrf_token') || '';

      // Import authService dynamically
      const { authService } = await import('../../services/authService');

      // Call backend Google OAuth endpoint
      const authResponse = await authService.googleLogin(credential, csrfToken);

      // Invoke success callback
      onSuccess(authResponse);
    } catch (error) {
      // Handle errors and invoke error callback
      const errorMessage = error instanceof Error ? error : new Error('Google authentication failed');
      console.error('Google Sign-In error:', errorMessage);
      onError(errorMessage);
    } finally {
      // Clear loading state
      setLoading(false);
    }
  };

  // Initialize and render Google Sign-In button
  const initializeGoogleButton = () => {
    // Prevent multiple initialization attempts
    if (initializationAttempted.current) {
      return;
    }

    // Check if Google Identity Services is available
    if (!window.google?.accounts?.id) {
      console.warn('Google Identity Services not yet available');
      return;
    }

    // Check if button container is available
    if (!buttonContainerRef.current) {
      console.warn('Button container ref not yet available');
      return;
    }

    // Get Google Client ID from environment
    const clientId = env.googleClientId;

    // Validate client ID is configured
    if (!clientId) {
      const error = new Error('Google Client ID is not configured. Please set VITE_GOOGLE_CLIENT_ID in your .env file.');
      console.error(error);
      onError(error);
      return;
    }

    // Mark initialization as attempted
    initializationAttempted.current = true;

    try {
      // Initialize Google Sign-In
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
      });

      // Render button with official Google styling
      window.google.accounts.id.renderButton(
        buttonContainerRef.current,
        {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          shape: 'rectangular',
          logo_alignment: 'left',
          width: 350,
        }
      );

      console.log('Google Sign-In button initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Google Sign-In button:', error);
      initializationAttempted.current = false; // Allow retry on error
    }
  };

  // Load Google Identity Services script
  useEffect(() => {
    // Check if script is already loaded
    if (window.google?.accounts?.id) {
      setScriptLoaded(true);
      return;
    }

    // Check if script element already exists
    const existingScript = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
    if (existingScript) {
      // Script is loading, wait for it
      const checkInterval = setInterval(() => {
        if (window.google?.accounts?.id) {
          setScriptLoaded(true);
          clearInterval(checkInterval);
        }
      }, 100);

      return () => clearInterval(checkInterval);
    }

    // Create script element
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;

    // Handle successful script load
    script.onload = () => {
      console.log('Google Identity Services script loaded successfully');
      setScriptLoaded(true);
    };

    // Handle script load failure
    script.onerror = () => {
      const error = new Error('Failed to load Google Identity Services script');
      console.error(error);
      onError(error);
    };

    // Append script to document
    document.head.appendChild(script);

    // Cleanup: remove script on unmount (only if we added it)
    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, [onError]);

  // Initialize button when script is loaded and container is ready
  useEffect(() => {
    if (scriptLoaded && buttonContainerRef.current) {
      // Small delay to ensure DOM is fully ready
      const timer = setTimeout(() => {
        initializeGoogleButton();
      }, 50);

      return () => clearTimeout(timer);
    }
  }, [scriptLoaded]);

  // Reset initialization flag when component unmounts
  useEffect(() => {
    return () => {
      initializationAttempted.current = false;
    };
  }, []);

  return (
    <div>
      {/* Button container for Google Identity Services */}
      <div 
        ref={buttonContainerRef}
        style={{ 
          opacity: disabled || loading ? 0.5 : 1,
          pointerEvents: disabled || loading ? 'none' : 'auto',
          minHeight: '40px', // Reserve space for button
        }}
      />
      
      {/* Loading indicator */}
      {loading && (
        <div className="text-center text-sm text-gray-500 mt-2">
          Signing in with Google...
        </div>
      )}
    </div>
  );
}
