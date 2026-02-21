# Implementation Tasks: Google OAuth Authentication

## Overview

This task list guides the implementation of secure Google OAuth 2.0 authentication following the latest Google Identity Services documentation. The implementation updates the existing OAuth endpoint to include CSRF protection, enhanced token verification, and proper user identification using Google's immutable `sub` claim.

## Task List

### Phase 1: Schema and Configuration Updates

- [x] 1. Update GoogleAuthRequest schema
  - [x] 1.1 Rename `id_token` field to `credential` in `app/schemas/auth.py`
  - [x] 1.2 Add `g_csrf_token` field to GoogleAuthRequest schema
  - [x] 1.3 Add field validation (min_length=1) for both fields
  - [x] 1.4 Update docstrings to reflect latest Google Identity Services terminology

### Phase 2: CSRF Protection Implementation

- [x] 2. Implement CSRF token validation
  - [x] 2.1 Create `validate_csrf_token` function in `app/core/security.py`
  - [x] 2.2 Implement double-submit-cookie pattern validation logic
  - [x] 2.3 Add constant-time comparison for token matching
  - [x] 2.4 Add security logging for CSRF validation failures
  - [x] 2.5 Raise HTTPException(400) with descriptive error messages

### Phase 3: Enhanced Token Verification

- [x] 3. Update Google token verification
  - [x] 3.1 Update `verify_google_token` function in `app/core/security.py`
  - [x] 3.2 Add email_verified claim validation (must be True)
  - [x] 3.3 Add hosted domain (hd) validation for Workspace accounts
  - [x] 3.4 Enhance error handling with detailed logging
  - [x] 3.5 Update return dictionary to include all required claims (sub, email, email_verified, name, picture, hd)

### Phase 4: API Endpoint Updates

- [x] 4. Update Google OAuth endpoint
  - [x] 4.1 Add FastAPI Request parameter to `google_auth` function in `app/api/v1/endpoints/auth.py`
  - [x] 4.2 Extract g_csrf_token from cookies using `request.cookies.get("g_csrf_token")`
  - [x] 4.3 Call `validate_csrf_token` before token verification
  - [x] 4.4 Update user query to use only oauth_provider and oauth_provider_user_id (remove email-based lookup)
  - [x] 4.5 Use `sub` claim (not email) for oauth_provider_user_id when creating new users
  - [x] 4.6 Update error responses to match new validation requirements

### Phase 5: Testing

- [x] 5. Write unit tests for CSRF validation
  - [x] 5.1 Test successful CSRF validation with matching tokens
  - [x] 5.2 Test CSRF validation failure with missing cookie token
  - [x] 5.3 Test CSRF validation failure with missing body token
  - [x] 5.4 Test CSRF validation failure with mismatched tokens
  - [x] 5.5 Test security logging for CSRF violations

- [x] 6. Write unit tests for enhanced token verification
  - [x] 6.1 Test successful token verification with all valid claims
  - [x] 6.2 Test token verification failure with email_verified=False
  - [x] 6.3 Test hosted domain validation for Workspace accounts
  - [x] 6.4 Test token verification with missing required claims
  - [x] 6.5 Test error handling and logging for verification failures

- [x] 7. Write integration tests for Google OAuth endpoint
  - [x] 7.1 Test successful authentication for new user (creates user + onboarding state)
  - [x] 7.2 Test successful authentication for existing user (returns JWT)
  - [x] 7.3 Test authentication failure with invalid CSRF tokens
  - [x] 7.4 Test authentication failure with invalid Google token
  - [x] 7.5 Test authentication failure with unverified email
  - [x] 7.6 Test that oauth_provider_user_id uses sub claim (not email)
  - [x] 7.7 Test JWT token generation and response format

- [ ] 8. Write property-based tests
  - [ ] 8.1 Property: CSRF validation always rejects when tokens don't match
  - [ ] 8.2 Property: Token verification always rejects unverified emails
  - [ ] 8.3 Property: User lookup always uses oauth_provider + oauth_provider_user_id
  - [ ] 8.4 Property: New users always get onboarding state created

### Phase 6: Documentation and Cleanup

- [x] 9. Update documentation
  - [x] 9.1 Update API documentation with new request schema
  - [x] 9.2 Add CSRF protection documentation for frontend integration
  - [x] 9.3 Update environment variable documentation (.env.example)
  - [x] 9.4 Add migration guide for existing OAuth users (if needed)

- [ ] 10. Code cleanup and review
  - [ ] 10.1 Remove any deprecated OAuth code or comments
  - [ ] 10.2 Ensure consistent error messages across all validation points
  - [ ] 10.3 Verify all security logging is in place
  - [ ] 10.4 Run linting and type checking
  - [ ] 10.5 Update test coverage report

## Testing Strategy

### Unit Tests
- Test individual functions in isolation (CSRF validation, token verification)
- Mock external dependencies (Google token verification API)
- Focus on edge cases and error conditions

### Integration Tests
- Test complete OAuth flow from endpoint to database
- Use test database with real SQLAlchemy operations
- Verify JWT token generation and user creation

### Property-Based Tests
- Use Hypothesis to generate random test inputs
- Verify security properties hold across all inputs
- Test invariants (e.g., CSRF always validates correctly)

## Security Considerations

1. **CSRF Protection**: Double-submit-cookie pattern prevents cross-site request forgery
2. **Token Verification**: Comprehensive validation of all ID token claims
3. **Email Verification**: Only accept tokens with verified email addresses
4. **Immutable Identifiers**: Use Google's `sub` claim for user identification
5. **Security Logging**: Log all authentication failures for monitoring
6. **Constant-Time Comparison**: Prevent timing attacks on CSRF token validation

## Rollout Plan

1. **Development**: Implement and test all changes in development environment
2. **Staging**: Deploy to staging and test with real Google OAuth credentials
3. **Production**: Deploy with monitoring for authentication failures
4. **Monitoring**: Track CSRF validation failures and token verification errors

## Success Criteria

- [ ] All unit tests pass with >90% coverage
- [ ] All integration tests pass
- [ ] All property-based tests pass
- [ ] No security vulnerabilities in code review
- [ ] API documentation is complete and accurate
- [ ] Frontend can successfully authenticate users with new endpoint
- [ ] Existing OAuth users can still authenticate (backward compatibility)
