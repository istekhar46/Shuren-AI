# Requirements Document

## Introduction

This document specifies the requirements for implementing Google OAuth 2.0 authentication in the Shuren frontend React application. The implementation integrates with the existing backend Google OAuth endpoint (POST /api/v1/auth/google) which provides secure authentication with CSRF protection. The feature enables users to sign in or register using their Google accounts through a seamless "Sign in with Google" button on both the login and registration pages.

## Glossary

- **Google_Sign_In_Button**: The official Google Identity Services button component for OAuth authentication
- **GSI_Library**: Google Identity Services JavaScript library for OAuth 2.0 flows
- **ID_Token**: The credential JWT token received from Google after successful authentication
- **CSRF_Token**: Cross-Site Request Forgery token used for double-submit-cookie validation
- **Auth_Context**: React context managing authentication state (user, token, login, logout)
- **Auth_Service**: Service layer handling API calls for authentication operations
- **Login_Page**: React component for existing user authentication
- **Register_Page**: React component for new user registration
- **OAuth_Response**: Backend response containing access_token, token_type, and user_id
- **Loading_State**: UI state indicating an ongoing authentication operation
- **Error_State**: UI state displaying authentication failure messages
- **Environment_Variable**: Configuration value stored in .env file (VITE_GOOGLE_CLIENT_ID)

## Requirements

### Requirement 1: Google Identity Services Integration

**User Story:** As a developer, I want to integrate Google Identity Services library, so that the application can use official Google OAuth components.

#### Acceptance Criteria

1. THE Login_Page SHALL load the GSI_Library from https://accounts.google.com/gsi/client
2. THE Register_Page SHALL load the GSI_Library from https://accounts.google.com/gsi/client
3. WHEN the GSI_Library loads successfully, THE application SHALL initialize it with the configured client ID
4. IF the GSI_Library fails to load, THEN THE application SHALL log the error and continue without Google sign-in functionality
5. THE application SHALL read the Google client ID from Environment_Variable named VITE_GOOGLE_CLIENT_ID

### Requirement 2: Google Sign-In Button Display

**User Story:** As a user, I want to see a "Sign in with Google" button, so that I can authenticate using my Google account.

#### Acceptance Criteria

1. THE Login_Page SHALL display a Google_Sign_In_Button below the email/password form
2. THE Register_Page SHALL display a Google_Sign_In_Button below the registration form
3. WHEN displaying the Google_Sign_In_Button, THE application SHALL include a visual separator (e.g., "OR" text with horizontal lines)
4. THE Google_Sign_In_Button SHALL follow Google's official branding guidelines for size, color, and styling
5. THE Google_Sign_In_Button SHALL be centered horizontally within its container

### Requirement 3: OAuth Authentication Flow

**User Story:** As a user, I want to authenticate with Google, so that I can access the application without creating a password.

#### Acceptance Criteria

1. WHEN a user clicks the Google_Sign_In_Button, THE application SHALL trigger the Google OAuth flow
2. WHEN Google authentication succeeds, THE application SHALL receive an ID_Token and CSRF_Token from Google
3. WHEN tokens are received, THE application SHALL extract the g_csrf_token from the cookie
4. WHEN tokens are received, THE application SHALL send a POST request to /api/v1/auth/google with credential (ID_Token) and g_csrf_token in the body
5. WHEN the backend responds with OAuth_Response, THE application SHALL store the access_token in localStorage

### Requirement 4: User State Management

**User Story:** As a user, I want my authentication state maintained after Google sign-in, so that I remain logged in across page refreshes.

#### Acceptance Criteria

1. WHEN OAuth authentication succeeds, THE Auth_Context SHALL update the token state with the access_token
2. WHEN the token is stored, THE Auth_Context SHALL fetch the current user data from /api/v1/auth/me
3. WHEN user data is fetched, THE Auth_Context SHALL store the user object in localStorage
4. WHEN user data is fetched, THE Auth_Context SHALL update the user state in Auth_Context
5. THE Auth_Context SHALL maintain the same authentication state structure for both email/password and Google OAuth users

### Requirement 5: Navigation After Authentication

**User Story:** As a user, I want to be redirected appropriately after Google sign-in, so that I can continue to the correct part of the application.

#### Acceptance Criteria

1. WHEN a new user completes Google authentication on Register_Page, THE application SHALL redirect to /onboarding
2. WHEN an existing user completes Google authentication on Login_Page, THE application SHALL redirect to /dashboard
3. WHEN a new user completes Google authentication on Login_Page, THE application SHALL redirect to /onboarding
4. WHEN an existing user completes Google authentication on Register_Page, THE application SHALL redirect to /dashboard
5. THE application SHALL determine user status by checking the onboarding_completed field from user data

### Requirement 6: Loading State Management

**User Story:** As a user, I want to see loading indicators during authentication, so that I know the system is processing my request.

#### Acceptance Criteria

1. WHEN Google OAuth flow starts, THE application SHALL set Loading_State to true
2. WHILE Loading_State is true, THE application SHALL disable the Google_Sign_In_Button
3. WHILE Loading_State is true, THE application SHALL disable the email/password form submit button
4. WHILE Loading_State is true, THE application SHALL display a loading indicator on or near the Google_Sign_In_Button
5. WHEN authentication completes (success or failure), THE application SHALL set Loading_State to false

### Requirement 7: Error Handling

**User Story:** As a user, I want to see clear error messages when Google authentication fails, so that I understand what went wrong and can try again.

#### Acceptance Criteria

1. IF the backend returns a 400 error, THEN THE application SHALL display "Authentication failed. Please try again."
2. IF the backend returns a 401 error, THEN THE application SHALL display "Google authentication failed. Please verify your account."
3. IF the network request fails, THEN THE application SHALL display "Network error. Please check your connection and try again."
4. IF Google OAuth flow is cancelled by the user, THEN THE application SHALL not display an error message
5. WHEN an error occurs, THE application SHALL set Error_State with the error message and display it above the Google_Sign_In_Button

### Requirement 8: Type Safety

**User Story:** As a developer, I want TypeScript types for Google OAuth requests and responses, so that the code is type-safe and maintainable.

#### Acceptance Criteria

1. THE application SHALL define a GoogleAuthRequest interface with credential and g_csrf_token fields
2. THE application SHALL define a GoogleAuthResponse interface matching the OAuth_Response structure
3. THE Auth_Service SHALL include a googleLogin method with proper TypeScript signatures
4. THE Auth_Context SHALL include a googleLogin method with proper TypeScript signatures
5. THE application SHALL use these types consistently across all Google OAuth code

### Requirement 9: Reusable Component Design

**User Story:** As a developer, I want a reusable Google sign-in component, so that it can be used consistently across login and registration pages.

#### Acceptance Criteria

1. THE application SHALL create a GoogleSignInButton component in frontend/src/components/auth/
2. THE GoogleSignInButton component SHALL accept an onSuccess callback prop
3. THE GoogleSignInButton component SHALL accept an onError callback prop
4. THE GoogleSignInButton component SHALL handle all Google OAuth initialization and flow internally
5. THE GoogleSignInButton component SHALL be used by both Login_Page and Register_Page

### Requirement 10: CSRF Token Handling

**User Story:** As a developer, I want proper CSRF token extraction and submission, so that the backend's CSRF protection works correctly.

#### Acceptance Criteria

1. WHEN Google provides the g_csrf_token cookie, THE application SHALL extract it using document.cookie
2. WHEN sending the authentication request, THE application SHALL include the g_csrf_token in the request body
3. WHEN sending the authentication request, THE application SHALL ensure the g_csrf_token cookie is sent with the request
4. IF the g_csrf_token cannot be extracted from cookies, THEN THE application SHALL display an error message
5. THE application SHALL use a utility function to extract the g_csrf_token from document.cookie

### Requirement 11: Backward Compatibility

**User Story:** As a user, I want email/password authentication to continue working, so that I can choose my preferred authentication method.

#### Acceptance Criteria

1. WHEN Google OAuth is added, THE email/password login form SHALL remain fully functional
2. WHEN Google OAuth is added, THE email/password registration form SHALL remain fully functional
3. THE Login_Page SHALL display both authentication options with clear visual separation
4. THE Register_Page SHALL display both authentication options with clear visual separation
5. THE Auth_Context SHALL support both authentication methods without conflicts

### Requirement 12: Environment Configuration

**User Story:** As a developer, I want Google OAuth configuration managed through environment variables, so that credentials can be changed per environment.

#### Acceptance Criteria

1. THE application SHALL read VITE_GOOGLE_CLIENT_ID from the .env file
2. IF VITE_GOOGLE_CLIENT_ID is not configured, THEN THE application SHALL not display the Google_Sign_In_Button
3. IF VITE_GOOGLE_CLIENT_ID is not configured, THEN THE application SHALL log a warning to the console
4. THE application SHALL include VITE_GOOGLE_CLIENT_ID in .env.example with a placeholder value
5. THE application SHALL validate that VITE_GOOGLE_CLIENT_ID is a non-empty string before initializing Google OAuth

### Requirement 13: UI/UX Consistency

**User Story:** As a user, I want the Google sign-in button to match the application's design, so that the interface feels cohesive.

#### Acceptance Criteria

1. THE Google_Sign_In_Button SHALL use the same border radius as other buttons in the application
2. THE Google_Sign_In_Button SHALL maintain proper spacing above and below (consistent with form spacing)
3. THE visual separator (OR divider) SHALL use the application's gray color palette
4. THE error messages for Google OAuth SHALL use the same styling as email/password error messages
5. THE loading indicator SHALL use the same styling as other loading states in the application
