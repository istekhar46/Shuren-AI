# Requirements Document: Test Suite Fixes

## Introduction

This document specifies the requirements for fixing 43 failing tests in the Shuren backend test suite. The test failures span multiple categories including missing schema definitions, incomplete API responses, external API quota issues, event loop management problems, and integration test failures. The goal is to restore all tests to passing status while maintaining the existing 343 passing tests.

## Glossary

- **Test_Suite**: The collection of automated tests validating the Shuren backend application
- **Chat_Endpoint**: REST API endpoints for text-based chat interactions
- **Meal_Template**: Weekly meal plan structure with daily meal assignments
- **Property_Test**: Hypothesis-based test validating universal properties across generated inputs
- **Schema**: Pydantic model defining API request/response structure
- **Event_Loop**: Asyncio event loop managing asynchronous operations in tests
- **API_Quota**: Rate limit imposed by external API providers (Google Gemini)
- **Fixture**: Pytest fixture providing test dependencies and setup

## Requirements

### Requirement 1: Fix Chat Endpoint Schema Definitions

**User Story:** As a developer, I want all chat endpoint tests to pass, so that I can verify the chat API works correctly.

#### Acceptance Criteria

1. WHEN tests import ChatMessageResponse THEN the System SHALL provide a valid Pydantic schema definition
2. WHEN chat endpoints return message data THEN the System SHALL format responses using ChatMessageResponse schema
3. WHEN tests access ChatService attribute THEN the System SHALL provide the service class in the chat endpoints module
4. WHEN tests send invalid chat requests THEN the System SHALL return 422 validation errors (not 404)
5. THE System SHALL ensure all 14 chat endpoint tests pass without import or attribute errors

### Requirement 2: Fix Meal Template Response Fields

**User Story:** As a developer, I want meal template responses to include all required fields, so that frontend applications receive complete data.

#### Acceptance Criteria

1. WHEN the System returns dish data THEN the System SHALL include cuisine_type field in the response
2. WHEN the System returns today's meals summary THEN the System SHALL include total_carbs_g field
3. WHEN the System returns today's meals summary THEN the System SHALL include total_fats_g field
4. WHEN meal template service tests run THEN the System SHALL ensure active meal templates exist for test users
5. THE System SHALL ensure all 13 meal template tests pass with complete response data

### Requirement 3: Handle External API Quota Limits

**User Story:** As a developer, I want tests to handle API quota limits gracefully, so that test failures don't block development when quotas are exceeded.

#### Acceptance Criteria

1. WHEN Google Gemini API quota is exceeded THEN the System SHALL skip affected tests with clear messaging
2. WHEN diet planner agent tests encounter quota errors THEN the System SHALL mark tests as skipped (not failed)
3. WHEN general assistant agent tests encounter quota errors THEN the System SHALL mark tests as skipped (not failed)
4. WHEN langchain foundation tests encounter quota errors THEN the System SHALL mark tests as skipped (not failed)
5. THE System SHALL provide mock implementations for quota-limited tests as an alternative
6. THE System SHALL ensure all 6 quota-affected tests either pass or skip gracefully

### Requirement 4: Fix Event Loop Management in Property Tests

**User Story:** As a developer, I want property tests to manage event loops correctly, so that tests don't fail with "Event loop is closed" errors.

#### Acceptance Criteria

1. WHEN property tests create AsyncClient instances THEN the System SHALL properly manage the event loop lifecycle
2. WHEN property tests complete THEN the System SHALL close AsyncClient instances before event loop closure
3. WHEN TestUserDataIsolation tests run THEN the System SHALL prevent "Event loop is closed" RuntimeErrors
4. THE System SHALL use async context managers for AsyncClient lifecycle management
5. THE System SHALL ensure all 3 event loop tests pass without RuntimeErrors

### Requirement 5: Fix Integration Test Failures

**User Story:** As a developer, I want integration tests to validate end-to-end flows correctly, so that I can verify the system works as a whole.

#### Acceptance Criteria

1. WHEN integration tests create chat conversations THEN the System SHALL return 201 status code (not 404)
2. WHEN integration tests receive chat responses THEN the System SHALL include 'id' key in response data
3. WHEN chat conversation flow tests run THEN the System SHALL properly route requests to implemented endpoints
4. THE System SHALL ensure both integration tests pass with correct status codes and response structure

### Requirement 6: Fix Shopping List Error Messages

**User Story:** As a developer, I want shopping list tests to validate correct error messages, so that API consumers receive accurate feedback.

#### Acceptance Criteria

1. WHEN shopping list tests assert error messages THEN the System SHALL match the actual error message format
2. WHEN shopping list validation fails THEN the System SHALL return consistent error message text
3. THE System SHALL ensure the shopping list test passes with correct error message validation

### Requirement 7: Maintain Existing Passing Tests

**User Story:** As a developer, I want all currently passing tests to remain passing, so that fixes don't introduce regressions.

#### Acceptance Criteria

1. WHEN test fixes are implemented THEN the System SHALL maintain all 343 currently passing tests
2. WHEN schema changes are made THEN the System SHALL ensure backward compatibility with existing tests
3. WHEN service implementations are modified THEN the System SHALL preserve existing functionality
4. THE System SHALL run the complete test suite and verify 386 total tests pass (343 existing + 43 fixed)

### Requirement 8: Test Isolation and Cleanup

**User Story:** As a developer, I want tests to properly clean up resources, so that tests don't interfere with each other.

#### Acceptance Criteria

1. WHEN tests create database records THEN the System SHALL use isolated test database sessions
2. WHEN tests create HTTP clients THEN the System SHALL close clients after test completion
3. WHEN tests use external resources THEN the System SHALL clean up resources in teardown
4. WHEN property tests generate random data THEN the System SHALL ensure data doesn't leak between test runs
5. THE System SHALL use pytest fixtures with proper scope and cleanup for all shared resources
