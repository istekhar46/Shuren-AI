# Google OAuth 2.0 Integration Guide

## Overview

This document describes the Google OAuth 2.0 authentication implementation in the Shuren backend, following the latest Google Identity Services documentation (December 2024). The implementation provides secure user authentication with CSRF protection, comprehensive token verification, and proper user identification.

## Features

- **CSRF Protection**: Double-submit-cookie pattern prevents cross-site request forgery attacks
- **Enhanced Token Verification**: Validates signature, claims, email verification, and hosted domains
- **Immutable User Identification**: Uses Google's `sub` claim for stable user identification
- **Automatic User Creation**: Creates user accounts and onboarding state for new OAuth users
- **Security Logging**: Comprehensive logging of authentication failures for monitoring

## API Endpoint

### POST /api/v1/auth/google

Authenticates users with Google OAuth 2.0 credentials.

#### Request Schema

```json
{
  "credential": "string (required)",     // Google ID token from OAuth flow
  "g_csrf_token": "string (required)"    // CSRF token for validation
}
```

#### Request Headers

```
Cookie: g_csrf_token=<token_value>
```

The CSRF token must be present in both the request body and as a cookie with matching values.

#### Response Schema (Success - 200 OK)

```json
{
  "access_token": "string",    // JWT token for session management
  "token_type": "bearer",
  "user_id": "string"          // UUID of authenticated user
}
```

#### Error Responses

- **400 Bad Request**: CSRF validation failed
  ```json
  {
    "detail": "CSRF validation failed: Missing g_csrf_token cookie"
  }
  ```

- **401 Unauthorized**: Invalid Google token or email not verified
  ```json
  {
    "detail": "Invalid Google token: Email address is not verified"
  }
  ```

- **422 Unprocessable Entity**: Request validation failed (missing required fields)

## Frontend Integration

### Step 1: Load Google Identity Services

Include the Google Identity Services library in your HTML:

```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

### Step 2: Initialize Google Sign-In

```javascript
function initializeGoogleSignIn() {
  google.accounts.id.initialize({
    client_id: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com',
    callback: handleGoogleSignIn,
    auto_select: false,
    cancel_on_tap_outside: true
  });

  // Render the sign-in button
  google.accounts.id.renderButton(
    document.getElementById('google-signin-button'),
    {
      theme: 'outline',
      size: 'large',
      text: 'signin_with',
      shape: 'rectangular'
    }
  );
}
```

### Step 3: Handle Sign-In Response with CSRF Protection

```javascript
async function handleGoogleSignIn(response) {
  // Extract the ID token (credential) from Google's response
  const credential = response.credential;
  
  // Get CSRF token from cookie
  const csrfToken = getCookie('g_csrf_token');
  
  if (!csrfToken) {
    console.error('CSRF token not found in cookie');
    return;
  }
  
  try {
    // Send authentication request to backend
    const authResponse = await fetch('http://localhost:8000/api/v1/auth/google', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',  // Important: Include cookies
      body: JSON.stringify({
        credential: credential,
        g_csrf_token: csrfToken
      })
    });
    
    if (!authResponse.ok) {
      const error = await authResponse.json();
      console.error('Authentication failed:', error.detail);
      return;
    }
    
    const data = await authResponse.json();
    
    // Store JWT token for authenticated requests
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user_id', data.user_id);
    
    // Redirect to dashboard or home page
    window.location.href = '/dashboard';
    
  } catch (error) {
    console.error('Error during authentication:', error);
  }
}

// Helper function to get cookie value
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}
```

### Step 4: Initialize on Page Load

```javascript
window.onload = function() {
  initializeGoogleSignIn();
};
```

## CSRF Protection Details

### How It Works

The implementation uses the **double-submit-cookie pattern**:

1. Google Identity Services automatically sets a `g_csrf_token` cookie when the user initiates sign-in
2. The same token is included in the credential response
3. Frontend sends both the cookie and the token in the request body
4. Backend validates that both tokens match using constant-time comparison

### Security Benefits

- Prevents CSRF attacks by ensuring requests originate from the same domain
- Uses constant-time comparison to prevent timing attacks
- Logs all validation failures for security monitoring

## Token Verification Process

The backend performs comprehensive verification of Google ID tokens:

### 1. Signature Verification
- Uses Google's public keys to verify token signature
- Ensures token was issued by Google and hasn't been tampered with

### 2. Claims Validation
- **Issuer (iss)**: Must be `accounts.google.com` or `https://accounts.google.com`
- **Audience (aud)**: Must match configured `GOOGLE_CLIENT_ID`
- **Expiration (exp)**: Token must not be expired
- **Email Verified**: `email_verified` claim must be `true`

### 3. Hosted Domain Validation (Workspace Accounts)
- If `hd` claim is present, validates it matches the email domain
- Ensures Workspace users are from the expected organization

## User Account Management

### New Users

When a user authenticates for the first time:

1. Backend creates a new `User` record with:
   - `oauth_provider`: "google"
   - `oauth_provider_user_id`: Google's `sub` claim (immutable identifier)
   - `email`: User's email address
   - `full_name`: User's name from Google
   - `hashed_password`: `null` (OAuth users don't have passwords)

2. Backend creates an `OnboardingState` record:
   - `current_step`: 1
   - `is_complete`: false

3. Returns JWT token for immediate authentication

### Existing Users

For returning users:

1. Backend queries by `oauth_provider` and `oauth_provider_user_id` (not email)
2. Returns JWT token for the existing user
3. No database modifications

### Why Use `sub` Claim?

The `sub` (subject) claim is Google's immutable user identifier:
- Never changes even if user changes email
- Unique across all Google accounts
- Recommended by Google for user identification

## Environment Configuration

### Required Environment Variables

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# JWT Configuration (for session tokens)
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24
```

### Getting Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure OAuth consent screen
6. Add authorized JavaScript origins (e.g., `http://localhost:3000`)
7. Add authorized redirect URIs
8. Copy Client ID and Client Secret to `.env` file

## Security Considerations

### CSRF Protection
- Always validate CSRF tokens before processing authentication
- Use constant-time comparison to prevent timing attacks
- Log all CSRF validation failures

### Token Verification
- Never trust tokens without verification
- Validate all required claims (iss, aud, exp, email_verified)
- Check hosted domain for Workspace accounts

### User Identification
- Always use `sub` claim for user identification
- Never rely on email for user lookup (emails can change)
- Query by `oauth_provider` + `oauth_provider_user_id`

### Security Logging
- Log all authentication failures with structured data
- Monitor for suspicious patterns (repeated CSRF failures, invalid tokens)
- Never log sensitive data (tokens, passwords)

## Testing

### Unit Tests

Located in `tests/test_security.py`:
- CSRF validation tests
- Token verification tests
- Security logging tests

### Integration Tests

Located in `tests/test_auth_endpoints.py`:
- End-to-end OAuth flow tests
- User creation and lookup tests
- Error handling tests

Run tests:
```bash
poetry run pytest tests/test_security.py::TestCSRFValidation -v
poetry run pytest tests/test_security.py::TestGoogleOAuth -v
poetry run pytest tests/test_auth_endpoints.py::TestGoogleAuthEndpoint -v
```

## Troubleshooting

### "CSRF validation failed: Missing g_csrf_token cookie"

**Cause**: Cookie not being sent with request

**Solution**:
- Ensure `credentials: 'include'` is set in fetch request
- Check that cookie domain matches request domain
- Verify cookie is not blocked by browser settings

### "Email address is not verified"

**Cause**: User's Google account email is not verified

**Solution**:
- User must verify their email with Google
- Cannot be bypassed for security reasons

### "Invalid token issuer"

**Cause**: Token not issued by Google

**Solution**:
- Ensure using official Google Identity Services library
- Check for token tampering or man-in-the-middle attacks

### "Hosted domain does not match email domain"

**Cause**: Workspace account with mismatched domain

**Solution**:
- Verify user is signing in with correct Workspace account
- Check Google Workspace configuration

## Migration Guide

### For Existing OAuth Users

The current implementation is backward compatible. No migration is required for existing users as long as:

1. Users are identified by `oauth_provider` + `oauth_provider_user_id`
2. The `oauth_provider_user_id` field contains Google's `sub` claim

If your existing implementation used email for identification, you'll need to:

1. Update user records to populate `oauth_provider_user_id` with `sub` claim
2. Update authentication queries to use OAuth credentials instead of email

## References

- [Google Identity Services Documentation](https://developers.google.com/identity/gsi/web/guides/overview)
- [Google ID Token Verification](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetsecurity.info/cheatsheet/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet)
