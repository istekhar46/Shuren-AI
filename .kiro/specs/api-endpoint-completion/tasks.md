# Implementation Plan: API Endpoint Completion

## Overview

This implementation adds two missing API endpoints to achieve 100% test coverage (19/19 tests passing). The approach leverages existing service layer methods and follows established patterns in the codebase. Implementation is divided into three main phases: dishes endpoint, chat endpoint, and testing validation.

## Tasks

- [x] 1. Implement GET /api/v1/dishes endpoint
  - [x] 1.1 Add list_dishes route handler to dishes.py
    - Create new route handler with "/" path
    - Add authentication and database dependencies
    - Extract query parameters (meal_type, diet_type, limit, offset)
    - Get user's allergen preferences from profile
    - Call DishService.search_dishes() with filters and allergen exclusions
    - Convert results to DishSummaryResponse objects
    - Return array of dish summaries
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_
  
  - [ ]* 1.2 Write property test for pagination correctness
    - **Property 1: Pagination Correctness**
    - **Validates: Requirements 1.3, 1.4**
    - Use Hypothesis to generate random limit (1-100) and offset (0-1000) values
    - Verify response length <= limit
    - Verify offset changes results
  
  - [ ]* 1.3 Write property test for filter correctness
    - **Property 2: Filter Correctness**
    - **Validates: Requirements 1.5, 1.6**
    - Use Hypothesis to generate random meal_type and diet_type values
    - Verify all returned dishes match filter criteria
  
  - [ ]* 1.4 Write property test for allergen exclusion
    - **Property 3: Allergen Exclusion**
    - **Validates: Requirements 1.7**
    - Create test user with allergen preferences
    - Verify no returned dishes contain those allergens
  
  - [ ]* 1.5 Write unit tests for GET /dishes endpoint
    - Test authenticated request returns 200 OK
    - Test unauthenticated request returns 401
    - Test default limit is 50
    - Test empty results return empty array
    - Test invalid limit (>100) returns 422
    - Test negative offset returns 422
    - _Requirements: 1.1, 1.2, 1.8, 1.9, 1.10_

- [x] 2. Checkpoint - Verify dishes endpoint works
  - Run `poetry run pytest tests/test_dishes_endpoints.py` to ensure all tests pass
  - Manually test endpoint with curl or Postman
  - Ensure all tests pass, ask the user if questions arise

- [x] 3. Implement POST /api/v1/chat/sessions endpoint
  - [x] 3.1 Add create_chat_session route handler to chat.py
    - Create new route handler with "/sessions" path
    - Add authentication and database dependencies
    - Accept optional ChatSessionCreate request body
    - Default to "general" session type if no body provided
    - Call ChatService.create_session() with user_id and session data
    - Convert result to ChatSessionResponse
    - Return session details with HTTP 201 Created
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6, 2.8, 2.9_
  
  - [ ]* 3.2 Write property test for session type preservation
    - **Property 7: Session Type Preservation**
    - **Validates: Requirements 2.3**
    - Use Hypothesis to generate random session_type values
    - Verify created session has correct session_type
  
  - [ ]* 3.3 Write property test for context data persistence
    - **Property 8: Context Data Persistence**
    - **Validates: Requirements 2.5**
    - Use Hypothesis to generate random context_data dictionaries
    - Verify context data is stored in session
  
  - [ ]* 3.4 Write property test for session initialization invariants
    - **Property 9: Session Initialization Invariants**
    - **Validates: Requirements 2.6, 2.8, 2.9**
    - Verify response contains all required fields
    - Verify status is "active"
    - Verify ended_at is null
    - Verify timestamps are approximately current time
  
  - [ ]* 3.5 Write unit tests for POST /chat/sessions endpoint
    - Test authenticated request returns 201 Created
    - Test unauthenticated request returns 401
    - Test session_type is preserved
    - Test default session_type is "general"
    - Test context_data is stored
    - Test invalid session_type returns 422
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7_

- [x] 4. Register chat router in API v1
  - [x] 4.1 Update backend/app/api/v1/__init__.py
    - Import chat router from endpoints module
    - Add api_router.include_router() call for chat
    - Use prefix="/chat" and tags=["Chat"]
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 5. Checkpoint - Verify chat endpoint works
  - Run `poetry run pytest tests/test_chat_endpoints.py` to ensure all tests pass
  - Manually test endpoint with curl or Postman
  - Ensure all tests pass, ask the user if questions arise

- [x] 6. Add OpenAPI documentation examples
  - [x] 6.1 Add response examples to GET /dishes endpoint
    - Add 200 OK response example with dish array
    - Add 400 Bad Request response example
    - Add 401 Unauthorized response example
    - _Requirements: 4.1, 4.3, 4.4_
  
  - [x] 6.2 Add response examples to POST /chat/sessions endpoint
    - Add 201 Created response example with session object
    - Add 401 Unauthorized response example
    - Add 422 Validation Error response example
    - _Requirements: 4.2, 4.5, 4.6_

- [ ]* 7. Write additional property tests for response format
  - [ ]* 7.1 Write property test for response schema compliance
    - **Property 4: Response Schema Compliance**
    - **Validates: Requirements 6.1**
    - Verify all dishes have required DishSummaryResponse fields
  
  - [ ]* 7.2 Write property test for empty result handling
    - **Property 5: Empty Result Handling**
    - **Validates: Requirements 6.4**
    - Test that no matches returns empty array, not null
  
  - [ ]* 7.3 Write property test for error response format
    - **Property 6: Error Response Format**
    - **Validates: Requirements 5.5, 6.3**
    - Test that errors have "detail" field
  
  - [ ]* 7.4 Write property test for timestamp format compliance
    - **Property 10: Timestamp Format Compliance**
    - **Validates: Requirements 6.5**
    - Verify timestamps are in ISO 8601 format

- [x] 8. Run integration tests
  - [x] 8.1 Start backend server
    - Run `poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
    - Verify server starts without errors
  
  - [x] 8.2 Execute test-api-endpoints.js
    - Run `node test-api-endpoints.js` in separate terminal
    - Verify 19/19 tests pass (100% pass rate)
    - Check that GET /dishes test passes with 200 OK
    - Check that POST /chat/sessions test passes with 201 Created
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9. Final checkpoint - Verify complete implementation
  - Run all unit tests: `poetry run pytest`
  - Run all property tests: `poetry run pytest -m property`
  - Run integration tests: `node test-api-endpoints.js`
  - Verify 100% test pass rate
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end functionality
- Use `poetry run` prefix for all Python commands
- Existing service layer methods (DishService.search_dishes, ChatService.create_session) handle all business logic
- No database schema changes required
- No new dependencies required
