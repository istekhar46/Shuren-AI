# Implementation Plan: Frontend Google OAuth Integration

## Overview

This implementation plan guides the integration of Google OAuth 2.0 authentication into the Shuren frontend React application. The implementation adds a "Sign in with Google" button to both login and registration pages, integrates with the existing backend OAuth endpoint, and maintains backward compatibility with email/password authentication.

## Tasks

- [x] 1. Set up environment configuration and dependencies
  - Add VITE_GOOGLE_CLIENT_ID to .env.example with placeholder
  - Document Google Cloud Console setup steps in README or docs
  - Verify environment variable loading in Vite configuration
  - _Requirements: 1.5, 12.1, 12.4_

- [x] 2. Create cookie utility functions
  - [x] 2.1 Implement getCookie function in frontend/src/utils/cookies.ts
    - Extract cookie value by name from document.cookie
    - Return null if cookie not found
    - Handle edge cases (empty cookies, special characters)
    - _Requirements: 3.3, 10.1_
  
  - [ ]* 2.2 Write property tests for cookie extraction
    - **Property 1: Cookie Extraction Correctness**
    - **Validates: Requirements 3.3, 10.1**
    - Test with various cookie string formats
    - Test with missing cookies
    - Test with multiple cookies
  
  - [x] 2.3 Implement getAllCookies helper function
    - Parse all cookies into key-value object
    - Handle malformed cookie strings gracefully
    - _Requirements: 10.1_

- [x] 3. Update TypeScript type definitions
  - [x] 3.1 Add GoogleAuthRequest interface to frontend/src/types/auth.types.ts
    - Define credential field (string)
    - Define g_csrf_token field (string)
    - Add JSDoc comments
    - _Requirements: 8.1_
  
  - [x] 3.2 Add GoogleAuthResponse interface
    - Extend TokenResponse interface
    - Ensure compatibility with existing auth types
    - _Requirements: 8.2_

- [x] 4. Update authentication service
  - [x] 4.1 Add googleLogin method to frontend/src/services/authService.ts
    - Accept credential and csrfToken parameters
    - Create GoogleAuthRequest payload
    - POST to /auth/google endpoint
    - Return TokenResponse
    - _Requirements: 3.4, 8.3_
  
  - [ ]* 4.2 Write unit tests for googleLogin method
    - Test successful authentication
    - Test API call structure
    - Test error handling
    - Mock axios responses
    - _Requirements: 3.4_

- [x] 5. Update authentication context
  - [x] 5.1 Add googleLogin method to AuthContext interface
    - Define method signature with TypeScript types
    - _Requirements: 8.4_
  
  - [x] 5.2 Implement googleLogin method in AuthProvider
    - Call authService.googleLogin
    - Store access_token in localStorage
    - Update token state
    - Fetch user data from /auth/me
    - Store user data in localStorage
    - Update user state
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 5.3 Write integration tests for googleLogin in AuthContext
    - **Property 3: Authentication State Consistency**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    - Test token storage
    - Test user data fetching
    - Test state updates
    - Test localStorage operations

- [x] 6. Create GoogleSignInButton component
  - [x] 6.1 Create component file at frontend/src/components/auth/GoogleSignInButton.tsx
    - Define component props interface (onSuccess, onError, disabled)
    - Set up component state (loading)
    - Create button container ref
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [x] 6.2 Implement Google Identity Services script loading
    - Check if script already loaded (window.google)
    - Create script element dynamically
    - Set src to https://accounts.google.com/gsi/client
    - Handle load success and failure
    - _Requirements: 1.1, 1.2, 1.4_
  
  - [x] 6.3 Implement Google Sign-In initialization
    - Read VITE_GOOGLE_CLIENT_ID from environment
    - Validate client ID is non-empty
    - Call google.accounts.id.initialize with config
    - Render button with official styling
    - _Requirements: 1.3, 1.5, 12.2, 12.3, 12.5_
  
  - [x] 6.4 Implement credential response handler
    - Extract credential from Google response
    - Extract g_csrf_token from cookies using getCookie
    - Handle missing CSRF token error
    - Call authService.googleLogin
    - Invoke onSuccess callback with response
    - Handle errors and invoke onError callback
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 10.1, 10.4_
  
  - [x] 6.5 Implement loading state management
    - Set loading to true when OAuth flow starts
    - Disable button during loading
    - Display loading indicator
    - Set loading to false when complete
    - _Requirements: 6.1, 6.2, 6.4, 6.5_
  
  - [ ]* 6.6 Write unit tests for GoogleSignInButton
    - Test script loading
    - Test initialization with valid client ID
    - Test initialization without client ID
    - Test credential response handling
    - Test CSRF token extraction
    - Test success callback invocation
    - Test error callback invocation
    - Test loading state management
    - _Requirements: 1.1, 1.3, 3.1, 9.2, 9.3_
  
  - [ ]* 6.7 Write property tests for GoogleSignInButton
    - **Property 4: Loading State Management**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
    - **Property 5: Callback Invocation**
    - **Validates: Requirements 9.2, 9.3**
    - **Property 8: GSI Initialization**
    - **Validates: Requirements 1.3**

- [x] 7. Checkpoint - Verify component works in isolation
  - Test GoogleSignInButton in Storybook or standalone page
  - Verify script loads correctly
  - Verify button renders with Google styling
  - Verify callbacks are invoked
  - Ask user if questions arise

- [x] 8. Update LoginPage component
  - [x] 8.1 Import GoogleSignInButton component
    - Add import statement
    - _Requirements: 9.5_
  
  - [x] 8.2 Add OR divider below email/password form
    - Create divider with horizontal lines
    - Add "OR" text in center
    - Style with Tailwind CSS (gray-300 border, gray-500 text)
    - _Requirements: 2.3, 13.3_
  
  - [x] 8.3 Add GoogleSignInButton below divider
    - Pass onSuccess handler
    - Pass onError handler
    - Pass disabled prop based on loading state
    - _Requirements: 2.1, 9.5_
  
  - [x] 8.4 Implement handleGoogleSuccess callback
    - Fetch user data to check onboarding_completed
    - Navigate to /dashboard if onboarding_completed is true
    - Navigate to /onboarding if onboarding_completed is false
    - Handle errors
    - _Requirements: 5.2, 5.3, 5.5_
  
  - [x] 8.5 Implement handleGoogleError callback
    - Set error state with error message
    - Display error above Google button
    - _Requirements: 7.1, 7.2, 7.3, 7.5_
  
  - [ ]* 8.6 Write integration tests for LoginPage with Google OAuth
    - Test GoogleSignInButton is rendered
    - Test OR divider is displayed
    - Test successful authentication navigation
    - Test error handling
    - Test backward compatibility with email/password
    - _Requirements: 2.1, 2.3, 5.2, 11.1, 11.3_

- [x] 9. Update RegisterPage component
  - [x] 9.1 Import GoogleSignInButton component
    - Add import statement
    - _Requirements: 9.5_
  
  - [x] 9.2 Add OR divider below registration form
    - Create divider with horizontal lines
    - Add "OR" text in center
    - Style with Tailwind CSS
    - _Requirements: 2.3, 13.3_
  
  - [x] 9.3 Add GoogleSignInButton below divider
    - Pass onSuccess handler
    - Pass onError handler
    - Pass disabled prop based on loading state
    - _Requirements: 2.2, 9.5_
  
  - [x] 9.4 Implement handleGoogleSuccess callback
    - Fetch user data to check onboarding_completed
    - Navigate to /onboarding if onboarding_completed is false
    - Navigate to /dashboard if onboarding_completed is true (edge case)
    - Handle errors
    - _Requirements: 5.1, 5.4, 5.5_
  
  - [x] 9.5 Implement handleGoogleError callback
    - Set error state with error message
    - Display error above Google button
    - _Requirements: 7.1, 7.2, 7.3, 7.5_
  
  - [ ]* 9.6 Write integration tests for RegisterPage with Google OAuth
    - Test GoogleSignInButton is rendered
    - Test OR divider is displayed
    - Test successful authentication navigation
    - Test error handling
    - Test backward compatibility with email/password
    - _Requirements: 2.2, 2.3, 5.1, 11.2, 11.4_

- [x] 10. Checkpoint - Test complete OAuth flow
  - Test login page with Google OAuth
  - Test register page with Google OAuth
  - Verify navigation works correctly
  - Verify error handling works
  - Verify email/password auth still works
  - Ask user if questions arise

- [ ] 11. Write property-based tests
  - [ ]* 11.1 Property test for authentication request structure
    - **Property 2: Authentication Request Structure**
    - **Validates: Requirements 3.4, 10.2**
    - Generate random credentials and CSRF tokens
    - Verify request payload structure
    - Verify API endpoint is correct
  
  - [ ]* 11.2 Property test for navigation logic
    - **Property 6: Navigation Based on Onboarding Status**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
    - Generate random user data with different onboarding_completed values
    - Verify navigation destination is correct
  
  - [ ]* 11.3 Property test for token storage
    - **Property 7: Token Storage After Authentication**
    - **Validates: Requirements 3.5**
    - Generate random OAuth responses
    - Verify token is stored in localStorage
    - Verify Auth_Context state is updated
  
  - [ ]* 11.4 Property test for error message display
    - **Property 9: Error Message Display**
    - **Validates: Requirements 7.5**
    - Generate various error scenarios
    - Verify error messages are displayed correctly

- [x] 12. Update documentation
  - [x] 12.1 Add Google OAuth setup instructions to README
    - Document Google Cloud Console setup
    - Document environment variable configuration
    - Document testing with localhost
    - _Requirements: 12.1_
  
  - [x] 12.2 Update .env.example with VITE_GOOGLE_CLIENT_ID
    - Add placeholder value
    - Add comment explaining where to get client ID
    - _Requirements: 12.4_
  
  - [x] 12.3 Add inline code comments
    - Document GoogleSignInButton component
    - Document cookie utility functions
    - Document auth service methods
    - _Requirements: General code quality_

- [ ] 13. Final testing and validation
  - [ ] 13.1 Run all unit tests
    - Verify all tests pass
    - Check test coverage (target 80%+)
  
  - [ ] 13.2 Run all property-based tests
    - Verify all properties hold
    - Check for edge cases found by property tests
  
  - [ ] 13.3 Manual testing checklist
    - Test on LoginPage with new user
    - Test on LoginPage with existing user
    - Test on RegisterPage with new user
    - Test on RegisterPage with existing user
    - Test error scenarios (missing CSRF, invalid token, network error)
    - Test loading states
    - Test email/password auth still works
    - Test UI matches design specifications
  
  - [ ] 13.4 Browser compatibility testing
    - Test on Chrome
    - Test on Firefox
    - Test on Safari
    - Test on Edge
  
  - [ ] 13.5 Accessibility testing
    - Test keyboard navigation
    - Test screen reader compatibility
    - Test error message announcements

- [ ] 14. Final checkpoint - Complete implementation
  - All tests passing
  - Documentation complete
  - Manual testing complete
  - Ready for code review
  - Ask user if questions arise

## Notes

- Tasks marked with `*` are optional test tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- Manual testing ensures UI/UX quality

## Testing Strategy

### Unit Tests (Vitest)
- Test individual components and functions in isolation
- Mock external dependencies (Google library, API calls)
- Focus on edge cases and error conditions
- Target: 80%+ code coverage

### Property-Based Tests (fast-check)
- Test universal properties across many generated inputs
- Each property test runs minimum 100 iterations
- Validates correctness properties from design document
- Catches edge cases that unit tests might miss

### Integration Tests
- Test complete OAuth flow from button click to navigation
- Use real React components with mocked API
- Verify state management and localStorage operations
- Test backward compatibility with existing auth

### Manual Testing
- Verify UI matches design specifications
- Test user experience and error messages
- Verify browser compatibility
- Test accessibility features

## Security Considerations

- CSRF protection handled by backend (double-submit-cookie pattern)
- Google ID token validation handled by backend
- Client ID is public (not a secret)
- Tokens stored in localStorage (same as existing auth)
- HTTPS required in production

## Rollout Plan

1. **Development**: Implement and test all changes locally
2. **Staging**: Deploy to staging environment with test Google OAuth credentials
3. **Production**: Deploy with production Google OAuth credentials
4. **Monitoring**: Track authentication success/failure rates

## Success Criteria

- [ ] All unit tests pass with 80%+ coverage
- [ ] All property-based tests pass
- [ ] All integration tests pass
- [ ] Manual testing checklist complete
- [ ] Google OAuth works on login page
- [ ] Google OAuth works on register page
- [ ] Navigation works correctly for new/existing users
- [ ] Error handling works for all scenarios
- [ ] Email/password authentication still works
- [ ] UI matches design specifications
- [ ] Documentation is complete
