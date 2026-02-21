/**
 * Cookie utility functions for extracting and parsing browser cookies
 */

/**
 * Extracts a cookie value by name from document.cookie
 * 
 * @param name - The name of the cookie to retrieve
 * @returns The cookie value if found, null otherwise
 * 
 * @example
 * ```ts
 * const csrfToken = getCookie('g_csrf_token');
 * if (csrfToken) {
 *   console.log('CSRF token:', csrfToken);
 * }
 * ```
 */
export function getCookie(name: string): string | null {
  // Handle edge case: empty cookie string
  if (!document.cookie) {
    return null;
  }

  // Split cookies by semicolon and trim whitespace
  const cookies = document.cookie.split(';').map(cookie => cookie.trim());

  // Find the cookie with the matching name
  for (const cookie of cookies) {
    // Split by first '=' to handle values that contain '='
    const equalIndex = cookie.indexOf('=');
    if (equalIndex === -1) {
      continue; // Skip malformed cookies without '='
    }

    const cookieName = cookie.substring(0, equalIndex).trim();
    const cookieValue = cookie.substring(equalIndex + 1).trim();

    // Check if this is the cookie we're looking for
    if (cookieName === name) {
      // Decode URI component to handle special characters
      try {
        return decodeURIComponent(cookieValue);
      } catch (error) {
        // If decoding fails, return the raw value
        return cookieValue;
      }
    }
  }

  // Cookie not found
  return null;
}

/**
 * Parses all cookies into a key-value object
 * 
 * @returns An object containing all cookies as key-value pairs
 * 
 * @example
 * ```ts
 * const allCookies = getAllCookies();
 * console.log(allCookies); // { g_csrf_token: 'abc123', session_id: 'xyz789' }
 * ```
 */
export function getAllCookies(): Record<string, string> {
  const cookieObject: Record<string, string> = {};

  // Handle edge case: empty cookie string
  if (!document.cookie) {
    return cookieObject;
  }

  // Split cookies by semicolon and trim whitespace
  const cookies = document.cookie.split(';').map(cookie => cookie.trim());

  // Parse each cookie into the object
  for (const cookie of cookies) {
    // Split by first '=' to handle values that contain '='
    const equalIndex = cookie.indexOf('=');
    if (equalIndex === -1) {
      // Skip malformed cookies without '='
      continue;
    }

    const cookieName = cookie.substring(0, equalIndex).trim();
    const cookieValue = cookie.substring(equalIndex + 1).trim();

    // Skip empty cookie names
    if (!cookieName) {
      continue;
    }

    // Decode URI component to handle special characters
    try {
      cookieObject[cookieName] = decodeURIComponent(cookieValue);
    } catch (error) {
      // If decoding fails, use the raw value
      cookieObject[cookieName] = cookieValue;
    }
  }

  return cookieObject;
}
