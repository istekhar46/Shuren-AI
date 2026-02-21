# Implementation Plan: Fix Authentication System

## Overview

This plan fixes three critical authentication failures: incorrect database connection protocol, missing registration field validation in tests, and incomplete test data. The implementation focuses on configuration updates, test data fixes, and comprehensive testing to ensure authentication works correctly.

## Tasks

- [x] 1. Fix database connection configuration
  - [x] 1.1 Add async_database_url property to Settings class
    - Update `backend/app/config.py` to add property that converts `postgres://` to `postgresql+asyncpg://`
    - Handle both `postgres://` and `postgresql://` prefixes
    - Return unchanged URL if already using `postgresql+asyncpg://`
    - _Requirements: 1.1, 1.3_
  
  - [ ]* 1.2 Write property test for database URL conversion
    - **Property 1: Database URL Protocol Conversion**
    - **Validates: Requirements 1.1, 1.3**
    - Test with various URL formats (postgres://, postgresql://, postgresql+asyncpg://)
    - Verify all components preserved (host, port, database, credentials)
  
  - [x] 1.3 Update database session factory to use async_database_url
    - Modify `backend/app/db/session.py` to use `settings.async_database_url`
    - Replace direct `settings.DATABASE_URL` usage
    - _Requirements: 1.1_
  
  - [ ]* 1.4 Write integration test for database connection
    - Test that application can connect to database and query users table
    - Verify no connection errors occur
    - _Requirements: 1.2, 1.4_

- [x] 2. Update .env file with correct database URL
  - Update `backend/.env` to use `postgresql+asyncpg://` protocol
  - Preserve existing host, port, database name, and credentials
  - Add comment explaining the protocol requirement
  - _Requirements: 1.1_

- [x] 3. Checkpoint - Verify database connection works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update test data to include full_name field
  - [x] 4.1 Update Node.js test script
    - Modify `test-api-endpoints.js` to include `full_name` in registration data
    - Use value "Test User" for full_name
    - _Requirements: 4.1, 4.3_
  
  - [x] 4.2 Update Postman collection
    - Modify `.postman.json` to include `full_name` in registration request body
    - Add `{{full_name}}` variable to collection
    - Set default value "Test User" for full_name variable
    - _Requirements: 4.2, 4.3_
  
  - [ ]* 4.3 Write unit test to verify test data completeness
    - Verify test scripts include all required fields (email, password, full_name)
    - Verify Postman collection includes all required fields
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 5. Implement comprehensive registration validation tests
  - [ ]* 5.1 Write property test for registration field validation
    - **Property 2: Registration Field Validation**
    - **Validates: Requirements 2.1, 2.3, 2.4, 2.5**
    - Generate registration data with missing fields
    - Verify 422 status and descriptive error messages
  
  - [ ]* 5.2 Write property test for successful registration
    - **Property 3: Successful User Registration**
    - **Validates: Requirements 2.2, 8.1**
    - Generate valid registration data with all fields
    - Verify 201 status and user details returned (no password)
  
  - [ ]* 5.3 Write unit tests for specific validation edge cases
    - Test missing full_name returns 422
    - Test invalid email format returns 422
    - Test duplicate email returns 409
    - _Requirements: 2.3, 2.4_

- [ ] 6. Implement comprehensive authentication tests
  - [ ]* 6.1 Write property test for successful authentication
    - **Property 4: Successful Authentication**
    - **Validates: Requirements 3.1, 8.2**
    - Register random users and authenticate with valid credentials
    - Verify 200 status, JWT token, and token_type returned
  
  - [ ]* 6.2 Write property test for invalid credentials rejection
    - **Property 5: Invalid Credentials Rejection**
    - **Validates: Requirements 3.2, 3.3, 8.4**
    - Test with wrong passwords and non-existent users
    - Verify 401 status returned
  
  - [ ]* 6.3 Write unit tests for specific authentication scenarios
    - Test login with correct credentials succeeds
    - Test login with wrong password fails
    - Test login with non-existent user fails
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 7. Implement JWT token validation tests
  - [ ]* 7.1 Write property test for JWT token structure
    - **Property 6: JWT Token Structure and Signing**
    - **Validates: Requirements 3.4, 7.1, 7.4**
    - Generate tokens for random users
    - Verify token contains user ID and email
    - Verify token signed with JWT_SECRET_KEY
    - Verify expiration is 24 hours from generation
  
  - [ ]* 7.2 Write property test for protected endpoint access
    - **Property 7: Protected Endpoint Access**
    - **Validates: Requirements 3.5**
    - Generate valid tokens and use in protected endpoint requests
    - Verify access granted (non-401 status)
  
  - [ ]* 7.3 Write property test for expired token rejection
    - **Property 8: Expired Token Rejection**
    - **Validates: Requirements 7.2, 7.3**
    - Generate expired tokens
    - Verify 401 status when used
  
  - [ ]* 7.4 Write unit tests for token validation scenarios
    - Test valid token grants access
    - Test expired token is rejected
    - Test invalid signature is rejected
    - Test missing token is rejected
    - _Requirements: 3.5, 7.2_

- [ ] 8. Checkpoint - Verify authentication flow works end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement password security tests
  - [ ]* 9.1 Write property test for password hashing
    - **Property 9: Password Hashing**
    - **Validates: Requirements 6.1, 6.2, 6.3**
    - Register users with random passwords
    - Verify stored password is bcrypt hash (not plain text)
    - Verify login with correct password succeeds
    - Verify login with wrong password fails
  
  - [ ]* 9.2 Write property test for password security in errors
    - **Property 10: Password Security in Errors**
    - **Validates: Requirements 6.4, 5.3**
    - Trigger various errors (validation, authentication)
    - Verify plain text passwords not in response or logs
  
  - [ ]* 9.3 Write unit tests for password security
    - Test password is hashed before storage
    - Test password verification works correctly
    - Test passwords not exposed in error messages
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 10. Implement error handling validation tests
  - [ ]* 10.1 Write property test for validation error format
    - **Property 11: Validation Error Format**
    - **Validates: Requirements 5.1, 8.3**
    - Trigger validation errors with missing/invalid fields
    - Verify 422 status and field-level error details
  
  - [ ]* 10.2 Write unit tests for error response formats
    - Test 422 validation error format
    - Test 401 authentication error format
    - Test 409 duplicate user error format
    - Test 500 server error format (generic message)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 11. Run complete test suite and verify improvements
  - [ ] 11.1 Run all authentication tests
    - Execute: `poetry run pytest tests/test_auth* -v`
    - Verify all tests pass
    - _Requirements: All_
  
  - [ ] 11.2 Run test coverage report
    - Execute: `poetry run pytest --cov=app.api.v1.endpoints.auth --cov=app.core.security --cov-report=html`
    - Verify coverage >= 90% for auth module
    - _Requirements: All_
  
  - [ ] 11.3 Run Node.js test script
    - Execute: `node test-api-endpoints.js`
    - Verify test pass rate improves from 21% to 80%+
    - _Requirements: 4.1, 4.4_
  
  - [ ] 11.4 Run Postman collection
    - Execute Postman collection with updated registration data
    - Verify all authentication tests pass
    - _Requirements: 4.2, 4.4_

- [ ] 12. Final checkpoint - Verify all authentication issues resolved
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis library with 100+ iterations
- Unit tests focus on specific examples and edge cases
- Database URL fix is backward compatible (auto-converts old format)
- Test data updates ensure complete field coverage
- Comprehensive testing validates all authentication flows
