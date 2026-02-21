# Implementation Plan: Phase 1.1 Core Endpoints

## Overview

This implementation plan breaks down Phase 1.1 Core Endpoints into discrete, incremental coding tasks. Each task builds on previous work and includes validation through tests. The plan follows the established patterns from Phase 1 Foundation and introduces new database tables for workout plan storage and chat functionality.

**Implementation Language:** Python (FastAPI, SQLAlchemy, Pydantic)

**Key Principles:**
- Incremental implementation with early validation
- Property-based tests for universal correctness
- Unit tests for specific examples and edge cases
- Profile locking and versioning throughout

## Tasks

- [x] 1. Create database migration for new tables
  - Create Alembic migration file for workout and chat tables
  - Define workout_plans, workout_days, workout_exercises, exercise_library tables
  - Define chat_sessions, chat_messages tables
  - Add indexes for performance optimization
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Seed exercise library with reference data
  - Create seed data script for exercise_library table
  - Include compound movements (squats, deadlifts, bench press, rows)
  - Include isolation exercises (curls, extensions, raises)
  - Include cardio exercises (running, cycling, rowing)
  - Add GIF URLs for visual guidance
  - _Requirements: 1.4, 1.7_

- [x] 3. Create SQLAlchemy models for workout tables
  - [x] 3.1 Create WorkoutPlan model
    - Define model with all fields from schema
    - Add relationships to WorkoutDay
    - Add validation constraints
    - _Requirements: 1.1, 1.5_
  
  - [x] 3.2 Create WorkoutDay model
    - Define model with all fields from schema
    - Add relationship to WorkoutPlan and WorkoutExercise
    - Add validation constraints
    - _Requirements: 1.2_
  
  - [x] 3.3 Create WorkoutExercise model
    - Define model with all fields from schema
    - Add relationship to WorkoutDay and ExerciseLibrary
    - Add validation constraints
    - _Requirements: 1.3_
  
  - [x] 3.4 Create ExerciseLibrary model
    - Define model with all fields from schema
    - Add indexes for search optimization
    - _Requirements: 1.4_

- [ ]* 3.5 Write property test for workout plan persistence
  - **Property 1: Data Persistence Round-Trip**
  - **Validates: Requirements 1.1, 1.2, 1.3**
  - Test that storing and retrieving workout plans preserves all data


- [x] 4. Create SQLAlchemy models for chat tables
  - [x] 4.1 Create ChatSession model
    - Define model with all fields from schema
    - Add relationship to ChatMessage
    - Add validation constraints
    - _Requirements: 8.2_
  
  - [x] 4.2 Create ChatMessage model
    - Define model with all fields from schema
    - Add relationship to ChatSession
    - Add validation constraints
    - _Requirements: 8.1, 8.5_

- [ ]* 4.3 Write property test for chat message persistence
  - **Property 1: Data Persistence Round-Trip**
  - **Validates: Requirements 8.1, 8.5**
  - Test that storing and retrieving chat messages preserves all data

- [x] 5. Create Pydantic schemas for workout endpoints
  - [x] 5.1 Create workout response schemas
    - ExerciseLibraryBase schema
    - WorkoutExerciseResponse schema
    - WorkoutDayResponse schema
    - WorkoutPlanResponse schema
    - WorkoutScheduleResponse schema
    - _Requirements: 2.1, 2.2, 3.1_
  
  - [x] 5.2 Create workout update schemas
    - ExerciseUpdate schema with validation
    - WorkoutDayUpdate schema with validation
    - WorkoutPlanUpdate schema with validation
    - WorkoutScheduleUpdate schema with validation
    - _Requirements: 4.1, 5.1_

- [ ]* 5.3 Write property test for input validation
  - **Property 4: Input Validation Rejection**
  - **Validates: Requirements 1.8, 4.5**
  - Test that invalid workout data is rejected with 422 error

- [x] 6. Create Pydantic schemas for meal endpoints
  - [x] 6.1 Create meal response schemas
    - MealPlanResponse schema
    - MealScheduleItemResponse schema
    - MealScheduleResponse schema
    - _Requirements: 6.1, 6.2_
  
  - [x] 6.2 Create meal update schemas
    - MealPlanUpdate schema with validation
    - MealScheduleItemUpdate schema with validation
    - MealScheduleUpdate schema with validation
    - _Requirements: 7.1, 7.4_

- [ ]* 6.3 Write property test for meal time validation
  - **Property 4: Input Validation Rejection**
  - **Validates: Requirements 7.4**
  - Test that invalid time formats are rejected

- [x] 7. Create Pydantic schemas for chat endpoints
  - [x] 7.1 Create chat request schemas
    - ChatMessageRequest schema
    - ChatSessionCreate schema
    - _Requirements: 8.1, 8.2_
  
  - [x] 7.2 Create chat response schemas
    - ChatMessageResponse schema
    - ChatSessionResponse schema
    - ChatHistoryResponse schema
    - _Requirements: 8.1, 8.3_

- [x] 8. Checkpoint - Ensure models and schemas are complete
  - Ensure all tests pass, ask the user if questions arise.


- [x] 9. Implement WorkoutService
  - [x] 9.1 Create WorkoutService class with core methods
    - get_workout_plan with eager loading
    - get_workout_day with exercise details
    - get_today_workout with day matching logic
    - get_week_workouts with filtering
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [x] 9.2 Add workout schedule methods
    - get_workout_schedule
    - get_next_workout with time-based filtering
    - _Requirements: 3.1, 3.2_
  
  - [x] 9.3 Add profile lock checking methods
    - check_profile_lock
    - create_profile_version
    - _Requirements: 4.1, 4.4_
  
  - [x] 9.4 Add workout modification methods
    - update_workout_plan with lock validation
    - update_workout_schedule with lock validation
    - _Requirements: 4.3, 5.3_

- [ ]* 9.5 Write property test for profile lock authorization
  - **Property 2: Profile Lock Authorization**
  - **Validates: Requirements 4.1, 4.2, 5.1, 5.2**
  - Test that locked profiles reject modifications with 403

- [ ]* 9.6 Write property test for profile version creation
  - **Property 3: Profile Version Creation**
  - **Validates: Requirements 4.4, 5.4**
  - Test that modifying locked profiles creates version records

- [ ]* 9.7 Write unit tests for WorkoutService
  - Test get_today_workout with various days
  - Test get_next_workout time calculations
  - Test empty result handling
  - _Requirements: 2.3, 3.2, 3.3_

- [x] 10. Implement MealService
  - [x] 10.1 Create MealService class with core methods
    - get_meal_plan
    - get_meal_schedule
    - get_today_meals with filtering
    - get_next_meal with time-based filtering
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 10.2 Add profile lock checking methods
    - check_profile_lock (reuse pattern from WorkoutService)
    - create_profile_version
    - _Requirements: 7.1, 7.5_
  
  - [x] 10.3 Add meal modification methods
    - update_meal_plan with lock validation
    - update_meal_schedule with lock validation
    - validate_macro_percentages
    - _Requirements: 7.3, 7.4_

- [ ]* 10.4 Write property test for time-based filtering
  - **Property 10: Time-Based Filtering Correctness**
  - **Validates: Requirements 6.4**
  - Test that next meal calculation returns correct upcoming meal

- [ ]* 10.5 Write unit tests for MealService
  - Test get_next_meal with various times
  - Test macro percentage validation
  - Test empty result handling
  - _Requirements: 6.4, 7.3_


- [x] 11. Implement ChatService
  - [x] 11.1 Create ChatService class with session management
    - create_session
    - get_or_create_session
    - end_session with state transition
    - _Requirements: 8.2, 8.4_
  
  - [x] 11.2 Add message handling methods
    - send_message (stores user message and generates response)
    - get_history with pagination
    - _Requirements: 8.1, 8.3_
  
  - [x] 11.3 Add placeholder for AI agent routing
    - route_to_agent method (returns placeholder response for now)
    - Add TODO comment for future LiveKit integration
    - _Requirements: 8.1_

- [ ]* 11.4 Write property test for message ordering
  - **Property 8: Chronological Message Ordering**
  - **Validates: Requirements 8.3**
  - Test that chat history returns messages in chronological order

- [ ]* 11.5 Write property test for session state transitions
  - **Property 9: Session State Transitions**
  - **Validates: Requirements 8.2, 8.4**
  - Test that session states follow valid transitions

- [ ]* 11.6 Write unit tests for ChatService
  - Test session creation
  - Test message storage and retrieval
  - Test pagination
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 12. Checkpoint - Ensure all services are complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement workout endpoints
  - [x] 13.1 Create /api/v1/workouts/plan GET endpoint
    - Use get_current_user dependency for authentication
    - Call WorkoutService.get_workout_plan
    - Return WorkoutPlanResponse
    - Handle 404 if plan not found
    - _Requirements: 2.1, 9.1_
  
  - [x] 13.2 Create /api/v1/workouts/plan/day/{day_number} GET endpoint
    - Validate day_number parameter (1-7)
    - Call WorkoutService.get_workout_day
    - Return WorkoutDayResponse
    - Handle 404 if day not found
    - _Requirements: 2.2_
  
  - [x] 13.3 Create /api/v1/workouts/today GET endpoint
    - Call WorkoutService.get_today_workout
    - Return WorkoutDayResponse or 404
    - _Requirements: 2.3_
  
  - [x] 13.4 Create /api/v1/workouts/week GET endpoint
    - Call WorkoutService.get_week_workouts
    - Return list of WorkoutDayResponse
    - _Requirements: 2.4_
  
  - [x] 13.5 Create /api/v1/workouts/plan PATCH endpoint
    - Validate request body with WorkoutPlanUpdate
    - Call WorkoutService.update_workout_plan
    - Handle 403 if profile locked
    - Return updated WorkoutPlanResponse
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 13.6 Create /api/v1/workouts/schedule GET endpoint
    - Call WorkoutService.get_workout_schedule
    - Return WorkoutScheduleResponse
    - _Requirements: 3.1_
  
  - [x] 13.7 Create /api/v1/workouts/schedule PATCH endpoint
    - Validate request body with WorkoutScheduleUpdate
    - Call WorkoutService.update_workout_schedule
    - Handle 403 if profile locked
    - Return updated WorkoutScheduleResponse
    - _Requirements: 5.1, 5.2, 5.3_

- [ ]* 13.8 Write property test for authentication requirement
  - **Property 11: Authentication Requirement**
  - **Validates: Requirements 9.1**
  - Test that requests without JWT are rejected with 401

- [ ]* 13.9 Write property test for user data isolation
  - **Property 5: User Data Isolation**
  - **Validates: Requirements 9.2**
  - Test that users cannot access other users' workout data

- [ ]* 13.10 Write unit tests for workout endpoints
  - Test successful GET requests
  - Test 404 handling
  - Test 403 for locked profiles
  - Test validation errors
  - _Requirements: 2.1, 2.2, 2.3, 4.2, 10.1, 10.2_


- [x] 14. Implement meal endpoints
  - [x] 14.1 Create /api/v1/meals/plan GET endpoint
    - Use get_current_user dependency for authentication
    - Call MealService.get_meal_plan
    - Return MealPlanResponse
    - Handle 404 if plan not found
    - _Requirements: 6.1, 9.1_
  
  - [x] 14.2 Create /api/v1/meals/plan PATCH endpoint
    - Validate request body with MealPlanUpdate
    - Call MealService.update_meal_plan
    - Handle 403 if profile locked
    - Return updated MealPlanResponse
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 14.3 Create /api/v1/meals/schedule GET endpoint
    - Call MealService.get_meal_schedule
    - Return MealScheduleResponse
    - _Requirements: 6.2_
  
  - [x] 14.4 Create /api/v1/meals/schedule PATCH endpoint
    - Validate request body with MealScheduleUpdate
    - Call MealService.update_meal_schedule
    - Return updated MealScheduleResponse
    - _Requirements: 7.4_
  
  - [x] 14.5 Create /api/v1/meals/today GET endpoint
    - Call MealService.get_today_meals
    - Return list of MealScheduleItemResponse
    - _Requirements: 6.3_
  
  - [x] 14.6 Create /api/v1/meals/next GET endpoint
    - Call MealService.get_next_meal
    - Return MealScheduleItemResponse or 404
    - _Requirements: 6.4_

- [ ]* 14.7 Write property test for response completeness
  - **Property 6: Response Completeness**
  - **Validates: Requirements 6.1, 6.2**
  - Test that all required fields are present in responses

- [ ]* 14.8 Write unit tests for meal endpoints
  - Test successful GET requests
  - Test 404 handling
  - Test 403 for locked profiles
  - Test time-based filtering
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 7.2, 10.2_

- [x] 15. Implement chat endpoints
  - [x] 15.1 Create /api/v1/chat/message POST endpoint
    - Validate request body with ChatMessageRequest
    - Call ChatService.send_message
    - Return ChatMessageResponse
    - _Requirements: 8.1_
  
  - [x] 15.2 Create /api/v1/chat/session/start POST endpoint
    - Validate request body with ChatSessionCreate
    - Call ChatService.create_session
    - Return ChatSessionResponse
    - _Requirements: 8.2_
  
  - [x] 15.3 Create /api/v1/chat/history GET endpoint
    - Parse query parameters (session_id, limit, offset)
    - Call ChatService.get_history
    - Return ChatHistoryResponse with pagination
    - _Requirements: 8.3_
  
  - [x] 15.4 Create /api/v1/chat/session/{session_id} DELETE endpoint
    - Validate session_id parameter
    - Call ChatService.end_session
    - Return 204 No Content
    - Handle 404 if session not found
    - _Requirements: 8.4_

- [ ]* 15.5 Write unit tests for chat endpoints
  - Test message sending and receiving
  - Test session creation and ending
  - Test history pagination
  - Test 404 handling
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 10.2_

- [x] 16. Checkpoint - Ensure all endpoints are complete
  - Ensure all tests pass, ask the user if questions arise.


- [x] 17. Add error handling and validation
  - [x] 17.1 Create error response schemas
    - ErrorResponse schema
    - Add error_code field for client handling
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
  
  - [x] 17.2 Add global exception handler
    - Handle unexpected exceptions with 500 error
    - Log exceptions with stack traces
    - Return consistent error format
    - _Requirements: 10.4_
  
  - [x] 17.3 Add profile lock exception handling
    - Create ProfileLockedException
    - Return 403 with explanation
    - _Requirements: 10.3_

- [ ]* 17.4 Write property test for error response consistency
  - **Property 12: Error Response Consistency**
  - **Validates: Requirements 10.2, 10.4**
  - Test that all errors return consistent response format

- [ ]* 17.5 Write unit tests for error handling
  - Test 404 responses
  - Test 422 validation errors
  - Test 403 profile locked errors
  - Test 500 internal errors
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 18. Add timestamp and versioning validation
  - [x] 18.1 Add timestamp validation to models
    - Ensure created_at is set on creation
    - Ensure updated_at is updated on modification
    - _Requirements: 11.3_
  
  - [x] 18.2 Add profile version immutability checks
    - Prevent deletion of profile versions
    - Prevent modification of profile versions
    - _Requirements: 11.5_

- [ ]* 18.3 Write property test for timestamp presence
  - **Property 14: Timestamp Presence**
  - **Validates: Requirements 11.3**
  - Test that all entities have valid created_at timestamps

- [ ]* 18.4 Write property test for profile version immutability
  - **Property 13: Profile Version Immutability**
  - **Validates: Requirements 11.5**
  - Test that profile versions cannot be deleted or modified

- [x] 19. Add API documentation
  - [x] 19.1 Add endpoint descriptions and examples
    - Add docstrings to all endpoint functions
    - Add request/response examples
    - Document error responses
    - _Requirements: 13.1, 13.2, 13.3_
  
  - [x] 19.2 Add schema descriptions
    - Add field descriptions to Pydantic models
    - Add validation examples
    - _Requirements: 13.4_

- [x] 20. Integration testing
  - [x] 20.1 Create end-to-end test scenarios
    - Test complete workout plan creation and retrieval
    - Test complete meal plan modification flow
    - Test complete chat conversation flow
    - _Requirements: 2.1, 6.1, 8.1_
  
  - [x] 20.2 Test profile locking workflow
    - Test unlock → modify → lock cycle
    - Test version creation during modification
    - _Requirements: 4.1, 4.4, 7.1, 7.5_

- [ ]* 20.3 Write property test for API response format consistency
  - **Property 15: API Response Format Consistency**
  - **Validates: Requirements 13.2**
  - Test that all responses follow consistent format

- [ ] 21. Performance validation
  - [ ] 21.1 Add performance tests for read operations
    - Test workout plan queries < 100ms
    - Test meal plan queries < 100ms
    - Test chat history queries < 100ms
    - _Requirements: 12.1_
  
  - [ ] 21.2 Add performance tests for write operations
    - Test workout plan updates < 200ms
    - Test meal plan updates < 200ms
    - Test chat message creation < 200ms
    - _Requirements: 12.2_

- [ ] 22. Final checkpoint - Complete system validation
  - Run all tests (unit, property, integration, performance)
  - Verify all endpoints work correctly
  - Check API documentation is complete
  - Ensure all requirements are met
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (100 iterations each)
- Unit tests validate specific examples and edge cases
- All database operations use async SQLAlchemy
- All commands should use `poetry run` prefix
