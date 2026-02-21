# Requirements Document

## Introduction

This document specifies the requirements for implementing secure Google OAuth 2.0 authentication in the Shuren backend application. The implementation follows the latest official Google Identity Services documentation (December 2024) and integrates with the existing JWT-based authentication system. The feature enables users to authenticate using their Google accounts (both Gmail and Google Workspace) while maintaining security best practices including CSRF protection, comprehensive token verification, and proper user identification.

## Glossary

- **OAuth_System**: The Google OAuth 2.0 authentication subsystem within Shuren
- **ID_Token**: A JSON Web Token (JWT) issued by Google containing user identity information
- **CSRF_Token**: Cross-Site Request Forgery token used for double-submit-cookie validation
- **Sub_Claim**: The unique Google user identifier in the ID token (subject claim)
- **Aud_Claim**: The audience claim in the ID token specifying the intended recipient
- **Iss_Claim**: The issuer claim in the ID token identifying Google as the token issuer
- **Exp_Claim**: The expiration claim in the ID token specifying when the token expires
- **Hd_Claim**: The hosted domain claim for Google Workspace accounts
- **Email_Verified_Field**: Boolean field in ID token indicating email verification status
- **JWT_Session**: The application's JWT token used for maintaining user sessions
- **User_Record**: Database record representing a user account in the system
- **OAuth_Provider_Field**: Database field storing the OAuth provider name (e.g., "google")
- **OAuth_Provider_User_ID_Field**: Database field storing the provider's unique user identifier

## Requirements

### Requirement 1: CSRF Protection

**User Story:** As a security engineer, I want CSRF protection for OAuth flows, so that the application is protected against cross-site request forgery attacks.

#### Acceptance Criteria

1. WHEN a Google OAuth request is received, THE OAuth_System SHALL validate the g_csrf_token cookie matches the g_csrf_token body parameter
2. IF the g_csrf_token cookie is missing, THEN THE OAuth_System SHALL reject the request with a 400 error
3. IF the g_csrf_token body parameter is missing, THEN THE OAuth_System SHALL reject the request with a 400 error
4. IF the g_csrf_token cookie does not match the body parameter, THEN THE OAuth_System SHALL reject the request with a 400 error and log the security violation
5. WHEN CSRF validation passes, THE OAuth_System SHALL proceed to ID token verification

### Requirement 2: ID Token Signature Verification

**User Story:** As a security engineer, I want ID token signatures verified using Google's public keys, so that only authentic tokens from Google are accepted.

#### Acceptance Criteria

1. WHEN verifying an ID token, THE OAuth_System SHALL use the verify_oauth2_token function from google.oauth2.id_token library
2. WHEN calling verify_oauth2_token, THE OAuth_System SHALL pass the ID token, a requests.Request() object, and the configured Google client ID
3. IF the token signature is invalid, THEN THE OAuth_System SHALL reject the request with a 401 error
4. IF the token verification raises a ValueError, THEN THE OAuth_System SHALL reject the request with a 401 error and log the verification failure
5. WHEN signature verification succeeds, THE OAuth_System SHALL proceed to claims validation

### Requirement 3: ID Token Claims Validation

**User Story:** As a security engineer, I want comprehensive validation of ID token claims, so that only valid tokens with correct audience, issuer, and expiration are accepted.

#### Acceptance Criteria

1. WHEN validating token claims, THE OAuth_System SHALL verify the Aud_Claim matches the configured Google client ID exactly
2. WHEN validating token claims, THE OAuth_System SHALL verify the Iss_Claim is either "accounts.google.com" or "https://accounts.google.com"
3. WHEN validating token claims, THE OAuth_System SHALL verify the Exp_Claim indicates the token has not expired
4. IF the Aud_Claim does not match the client ID, THEN THE OAuth_System SHALL reject the request with a 401 error
5. IF the Iss_Claim is not from Google, THEN THE OAuth_System SHALL reject the request with a 401 error
6. IF the token has expired, THEN THE OAuth_System SHALL reject the request with a 401 error

### Requirement 4: Email Verification and Domain Validation

**User Story:** As a security engineer, I want email addresses verified and domains validated, so that only confirmed email addresses from legitimate domains are accepted.

#### Acceptance Criteria

1. WHEN processing an ID token, THE OAuth_System SHALL verify the Email_Verified_Field is true
2. IF the Email_Verified_Field is false, THEN THE OAuth_System SHALL reject the request with a 401 error
3. WHERE the email domain is gmail.com, THE OAuth_System SHALL accept the email if Email_Verified_Field is true
4. WHERE the Hd_Claim is present, THE OAuth_System SHALL verify it matches the email domain
5. IF the Hd_Claim is present but does not match the email domain, THEN THE OAuth_System SHALL reject the request with a 401 error

### Requirement 5: User Account Creation and Linking

**User Story:** As a user, I want to authenticate with my Google account, so that I can access the application without creating a separate password.

#### Acceptance Criteria

1. WHEN a valid ID token is verified, THE OAuth_System SHALL extract the Sub_Claim as the unique user identifier
2. WHEN processing authentication, THE OAuth_System SHALL query for an existing User_Record where OAuth_Provider_Field is "google" and OAuth_Provider_User_ID_Field matches the Sub_Claim
3. IF a matching User_Record exists, THEN THE OAuth_System SHALL generate a JWT_Session for that user
4. IF no matching User_Record exists, THEN THE OAuth_System SHALL create a new User_Record with OAuth_Provider_Field set to "google" and OAuth_Provider_User_ID_Field set to the Sub_Claim
5. WHEN creating a new User_Record, THE OAuth_System SHALL store the email, name, and profile picture URL from the ID token
6. WHEN creating a new User_Record for an OAuth user, THE OAuth_System SHALL set the password field to null
7. WHEN a new User_Record is created, THE OAuth_System SHALL generate a JWT_Session for the new user

### Requirement 6: JWT Session Management Integration

**User Story:** As a user, I want my Google authentication to integrate seamlessly with the application's session management, so that I have a consistent experience across authentication methods.

#### Acceptance Criteria

1. WHEN Google OAuth authentication succeeds, THE OAuth_System SHALL generate a JWT_Session using the existing JWT configuration
2. WHEN generating a JWT_Session, THE OAuth_System SHALL use the HS256 algorithm with the configured secret key
3. WHEN generating a JWT_Session, THE OAuth_System SHALL set the expiration to 24 hours from creation
4. WHEN generating a JWT_Session, THE OAuth_System SHALL include the user ID in the token payload
5. WHEN returning the authentication response, THE OAuth_System SHALL return the JWT_Session token in the same format as email/password authentication

### Requirement 7: Error Handling and Security Logging

**User Story:** As a security engineer, I want comprehensive error handling and security logging, so that authentication failures are properly tracked and debugged.

#### Acceptance Criteria

1. WHEN any authentication step fails, THE OAuth_System SHALL return an appropriate HTTP error code (400 for bad requests, 401 for authentication failures)
2. WHEN returning an error, THE OAuth_System SHALL include a descriptive error message without exposing sensitive implementation details
3. WHEN a CSRF validation fails, THE OAuth_System SHALL log the failure with timestamp, IP address, and token mismatch details
4. WHEN an ID token verification fails, THE OAuth_System SHALL log the failure with timestamp, error type, and sanitized token information
5. WHEN a security violation is detected, THE OAuth_System SHALL log the event at ERROR level for security monitoring

### Requirement 8: Database Schema Support

**User Story:** As a developer, I want the database schema to properly support OAuth users, so that user data is stored correctly and efficiently.

#### Acceptance Criteria

1. THE User_Record SHALL include an OAuth_Provider_Field that stores the provider name as a string
2. THE User_Record SHALL include an OAuth_Provider_User_ID_Field that stores the provider's unique user identifier as a string
3. THE User_Record SHALL allow the password field to be null for OAuth users
4. THE OAuth_System SHALL create a unique index on the combination of OAuth_Provider_Field and OAuth_Provider_User_ID_Field
5. WHEN querying for OAuth users, THE OAuth_System SHALL use the indexed fields for efficient lookups

### Requirement 9: Configuration Management

**User Story:** As a developer, I want OAuth configuration managed through environment variables, so that credentials are not hardcoded and can be changed per environment.

#### Acceptance Criteria

1. THE OAuth_System SHALL read the Google client ID from an environment variable named GOOGLE_CLIENT_ID
2. THE OAuth_System SHALL read the Google client secret from an environment variable named GOOGLE_CLIENT_SECRET
3. IF the GOOGLE_CLIENT_ID is not configured, THEN THE OAuth_System SHALL raise a configuration error on startup
4. IF the GOOGLE_CLIENT_SECRET is not configured, THEN THE OAuth_System SHALL raise a configuration error on startup
5. THE OAuth_System SHALL validate that configuration values are non-empty strings on startup

### Requirement 10: API Endpoint Specification

**User Story:** As a frontend developer, I want a clear API endpoint for Google OAuth authentication, so that I can integrate the authentication flow into the client application.

#### Acceptance Criteria

1. THE OAuth_System SHALL expose a POST endpoint at /api/v1/auth/google
2. WHEN receiving a request, THE OAuth_System SHALL expect a JSON body with fields: credential (ID token) and g_csrf_token
3. WHEN receiving a request, THE OAuth_System SHALL expect a cookie named g_csrf_token
4. WHEN authentication succeeds, THE OAuth_System SHALL return a 200 response with a JSON body containing the access_token and token_type fields
5. WHEN authentication fails, THE OAuth_System SHALL return an appropriate error response (400 or 401) with an error message
