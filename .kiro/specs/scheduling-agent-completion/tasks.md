# Implementation Plan: Scheduling Agent & Onboarding Completion

## Overview

This implementation plan creates the final specialized onboarding agent (Scheduling Agent) and the profile creation service that completes the onboarding flow. The implementation follows a bottom-up approach: first building validation utilities, then the scheduling agent with its tools, then the profile creation service, and finally the completion endpoint. Testing is integrated throughout to catch errors early.

## Tasks

- [x] 1. Create validation utilities for schedule data
  - Create `app/utils/schedule_validation.py` with validation functions
  - Implement `validate_day_name(day: str) -> bool` for day name validation
  - Implement `validate_time_format(time: str) -> bool` for HH:MM format validation
  - Implement `validate_time_range(time: str) -> bool` for 00:00-23:59 range validation
  - Implement `validate_meal_spacing(meal_times: Dict[str, str]) -> bool` for 2-hour minimum spacing
  - Implement `validate_meal_ordering(meal_times: Dict[str, str]) -> bool` for chronological order
  - Implement `day_name_to_number(day: str) -> int` for Monday=0, Sunday=6 conversion
  - Implement `time_str_to_time(time_str: str) -> time` for string to time object conversion
  - _Requirements: 5.3, 5.4, 21.2, 21.3, 21.4_

- [x]* 1.1 Write property tests for validation utilities
  - **Property 1: Workout Schedule Day Validation**
  - **Validates: Requirements 5.3**
  - **Property 2: Workout Schedule Time Format Validation**
  - **Validates: Requirements 5.4, 21.2**
  - **Property 12: Meal Time Spacing Validation**
  - **Validates: Requirements 21.3**
  - **Property 13: Meal Time Chronological Order**
  - **Validates: Requirements 21.4**

- [x] 2. Implement Scheduling Agent tools
  - [x] 2.1 Create `app/agents/tools/scheduling_tools.py` module
    - Import validation utilities from step 1
    - Import OnboardingState model and database dependencies
    - Set up async database operations
    - _Requirements: 5.1, 5.7, 5.11_
  
  - [x] 2.2 Implement save_workout_schedule tool
    - Use LangChain @tool decorator
    - Accept days: List[str], times: List[str], user_id: UUID, db: AsyncSession
    - Validate days using validate_day_name for each day
    - Validate times using validate_time_format and validate_time_range for each time
    - Validate len(days) == len(times)
    - Load OnboardingState for user_id
    - Save to agent_context["scheduling"]["workout_schedule"] with days and times
    - Add completed_at timestamp in ISO 8601 format
    - Return success status dict
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.15_
  
  - [x] 2.3 Implement save_meal_schedule tool
    - Use LangChain @tool decorator
    - Accept meal_times: Dict[str, str], user_id: UUID, db: AsyncSession
    - Validate all times using validate_time_format and validate_time_range
    - Load meal_frequency from agent_context["diet_planning"]["proposed_plan"]["meal_frequency"]
    - Validate len(meal_times) == meal_frequency
    - Validate meal spacing using validate_meal_spacing
    - Validate meal ordering using validate_meal_ordering
    - Save to agent_context["scheduling"]["meal_schedule"]
    - Add completed_at timestamp in ISO 8601 format
    - Return success status dict
    - _Requirements: 5.8, 5.9, 5.10, 5.15, 21.3, 21.4_
  
  - [x] 2.4 Implement save_hydration_preferences tool
    - Use LangChain @tool decorator
    - Accept frequency_hours: int, target_ml: int, user_id: UUID, db: AsyncSession
    - Validate frequency_hours is between 1 and 4 (inclusive)
    - Validate target_ml is between 1500 and 5000 (inclusive)
    - Load OnboardingState for user_id
    - Save to agent_context["scheduling"]["hydration_preferences"]
    - Add completed_at timestamp in ISO 8601 format
    - Return success status dict
    - _Requirements: 5.12, 5.13, 5.14, 5.15_

- [ ]* 2.5 Write property tests for scheduling tools
  - **Property 3: Workout Schedule Length Matching**
  - **Validates: Requirements 5.5**
  - **Property 4: Meal Schedule Time Format Validation**
  - **Validates: Requirements 5.8**
  - **Property 5: Meal Schedule Frequency Matching**
  - **Validates: Requirements 5.9**
  - **Property 6: Hydration Frequency Range Validation**
  - **Validates: Requirements 5.12**
  - **Property 7: Hydration Target Range Validation**
  - **Validates: Requirements 5.13**
  - **Property 8: Timestamp Format Consistency**
  - **Validates: Requirements 5.15**

- [x] 3. Implement Scheduling Agent
  - [x] 3.1 Create `app/agents/scheduling_agent.py` module
    - Create SchedulingAgent class inheriting from BaseOnboardingAgent
    - Set agent_type = "scheduling"
    - Import scheduling tools from step 2
    - _Requirements: 1.1_
  
  - [x] 3.2 Implement get_system_prompt method
    - Extract workout_plan summary from agent_context["workout_planning"]["proposed_plan"]
    - Extract meal_plan summary from agent_context["diet_planning"]["proposed_plan"]
    - Build system prompt with workout and meal context
    - Include instructions for asking about workout days/times, meal timing, and hydration
    - Include instructions for calling save tools when user confirms
    - Return hardcoded prompt string with context interpolated
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_
  
  - [x] 3.3 Implement get_tools method
    - Return list containing save_workout_schedule, save_meal_schedule, save_hydration_preferences
    - Bind user_id and db to tools using functools.partial
    - _Requirements: 1.2_
  
  - [x] 3.4 Implement process_message method
    - Use LangChain create_tool_calling_agent with llm, tools, and system prompt
    - Process user message through agent
    - Check if all three schedules are saved in agent_context["scheduling"]
    - If all saved, set step_complete=True and next_action="complete_onboarding"
    - Return AgentResponse with message, agent_type, step_complete, next_action
    - _Requirements: 1.2, 1.11_

- [x]* 3.5 Write unit tests for Scheduling Agent
  - Test agent instantiation and inheritance
  - Test get_system_prompt includes workout and meal context
  - Test get_tools returns correct tools
  - Test process_message returns valid AgentResponse
  - Test step_complete=True when all schedules saved

- [x] 4. Checkpoint - Ensure scheduling agent tests pass
  - Run `poetry run pytest tests/test_scheduling_agent.py -v`
  - Verify all unit and property tests pass
  - Ask user if questions arise

- [x] 5. Implement onboarding completion verification
  - [x] 5.1 Create `app/services/onboarding_completion.py` module
    - Create OnboardingIncompleteError exception class
    - _Requirements: 7.6_
  
  - [x] 5.2 Implement verify_onboarding_completion function
    - Accept agent_context: dict parameter
    - Check agent_context["fitness_assessment"] exists with completed_at
    - Check agent_context["goal_setting"] exists with completed_at
    - Check agent_context["workout_planning"] exists with user_approved=True
    - Check agent_context["diet_planning"] exists with user_approved=True
    - Check agent_context["scheduling"] exists with workout_schedule, meal_schedule, hydration_preferences
    - If any check fails, raise OnboardingIncompleteError with details of missing data
    - Return None if all checks pass
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ]* 5.3 Write property tests for verification
  - **Property 9: Missing Agent Data Error Handling**
  - **Validates: Requirements 7.6**

- [x] 6. Implement profile creation service
  - [x] 6.1 Create `app/services/profile_creation_service.py` module
    - Create ProfileCreationService class
    - Accept db: AsyncSession in constructor
    - Import all model classes (UserProfile, FitnessGoal, PhysicalConstraint, etc.)
    - Import validation utilities
    - _Requirements: 19.1_
  
  - [x] 6.2 Implement data extraction helper methods
    - Implement _extract_fitness_data(agent_context) -> dict
    - Implement _extract_goal_data(agent_context) -> dict
    - Implement _extract_workout_data(agent_context) -> dict
    - Implement _extract_diet_data(agent_context) -> dict
    - Implement _extract_schedule_data(agent_context) -> dict
    - Each method extracts and validates data from agent_context
    - _Requirements: 8.1, 9.1-9.8, 10.1-10.7, 11.1-11.6, 12.1-12.5, 13.1-13.5, 14.1-14.3_
  
  - [x] 6.3 Implement entity creation helper methods
    - Implement _create_profile_entity(user_id, fitness_level) -> UserProfile
    - Implement _create_fitness_goals(profile_id, goal_data) -> List[FitnessGoal]
    - Implement _create_physical_constraints(profile_id, limitations) -> List[PhysicalConstraint]
    - Implement _create_dietary_preference(profile_id, diet_data) -> DietaryPreference
    - Implement _create_meal_plan(profile_id, meal_plan_data) -> MealPlan
    - Implement _create_meal_schedules(profile_id, meal_schedule_data) -> List[MealSchedule]
    - Implement _create_workout_plan(user_id, workout_data) -> WorkoutPlan
    - Implement _create_workout_schedules(profile_id, workout_schedule_data) -> List[WorkoutSchedule]
    - Implement _create_hydration_preference(profile_id, hydration_data) -> HydrationPreference
    - Each method creates database entities but doesn't commit
    - Handle missing optional data gracefully with defaults
    - _Requirements: 8.2-8.10, 22.1-22.4_
  
  - [x] 6.4 Implement create_profile_from_agent_context method
    - Accept user_id: UUID, agent_context: dict
    - Call verify_onboarding_completion(agent_context)
    - Extract data using helper methods from 6.2
    - Begin database transaction
    - Create UserProfile with is_locked=True
    - Create all related entities using helper methods from 6.3
    - Add all entities to session
    - Commit transaction
    - Refresh profile to load relationships
    - Return UserProfile
    - If any error occurs, rollback transaction and raise
    - _Requirements: 8.11, 8.12, 8.13, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7_

- [x]* 6.5 Write property tests for profile creation
  - **Property 10: Profile Creation Atomicity**
  - **Validates: Requirements 8.11**
  - **Property 11: Profile Creation Rollback on Failure**
  - **Validates: Requirements 8.13**

- [x]* 6.6 Write unit tests for profile creation service
  - Test data extraction methods with complete agent_context
  - Test data extraction with missing optional data
  - Test entity creation methods
  - Test create_profile_from_agent_context with complete data
  - Test graceful handling of missing optional fields
  - Test error handling for missing required fields

- [x] 7. Checkpoint - Ensure profile creation tests pass
  - Run `poetry run pytest tests/test_profile_creation_service.py -v`
  - Verify all unit and property tests pass
  - Ask user if questions arise

- [x] 8. Update OnboardingAgentOrchestrator
  - [x] 8.1 Update `app/services/onboarding_agent_orchestrator.py`
    - Import SchedulingAgent
    - Update _step_to_agent method to map steps 8-9 to OnboardingAgentType.SCHEDULING
    - Update _create_agent method to instantiate SchedulingAgent for SCHEDULING type
    - _Requirements: 1.1_
  
  - [x] 8.2 Update agent routing for post-onboarding
    - Check if onboarding_state.is_complete is True
    - If complete and current_agent is "general_assistant", route to General Assistant
    - Do not route to onboarding agents if onboarding complete
    - _Requirements: 16.1, 16.2_

- [x]* 8.3 Write integration tests for orchestrator
  - Test routing to SchedulingAgent for steps 8-9
  - Test routing to General Assistant after onboarding complete
  - Test no routing to onboarding agents when complete

- [x] 9. Implement onboarding completion endpoint
  - [x] 9.1 Create completion endpoint in `app/api/v1/endpoints/onboarding.py`
    - Add POST /api/v1/onboarding/complete endpoint
    - Require authentication via get_current_user dependency
    - Load OnboardingState for current user
    - Check if onboarding already complete, return 409 if true
    - Call ProfileCreationService.create_profile_from_agent_context
    - Set onboarding_state.is_complete = True
    - Set onboarding_state.current_agent = "general_assistant"
    - Commit OnboardingState update
    - Return OnboardingCompleteResponse with profile data
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 20.9_
  
  - [x] 9.2 Create OnboardingCompleteResponse schema
    - Create schema in `app/schemas/onboarding.py`
    - Include profile_id, user_id, fitness_level, is_locked, onboarding_complete, message fields
    - _Requirements: 20.6_
  
  - [x] 9.3 Implement error handling
    - Catch OnboardingIncompleteError and return 400 with details
    - Catch ValidationError and return 422 with field errors
    - Catch database errors and return 500 with generic message
    - Log all errors for debugging
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

- [x]* 9.4 Write integration tests for completion endpoint
  - Test successful completion with complete agent_context
  - Test 409 error when already complete
  - Test 400 error when agent data missing
  - Test 401 error when not authenticated
  - Test profile is locked after completion
  - Test onboarding_state.is_complete is True after completion

- [x] 10. Checkpoint - Ensure completion endpoint tests pass
  - Run `poetry run pytest tests/test_onboarding_endpoints.py::test_complete_onboarding -v`
  - Verify all integration tests pass
  - Ask user if questions arise

- [ ]* 11. Implement backward compatibility (NOT NEEDED - User confirmed to skip)
  - [ ]* 11.1 Update existing onboarding completion logic
    - Ensure existing completion endpoint still works
    - Add fallback to old flow if agent_context is empty
    - Preserve step_data structure during agent-based onboarding
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_
  
  - [ ]* 11.2 Add migration support
    - Handle users mid-onboarding during deployment
    - Allow completion via either old or new flow
    - Prioritize agent_context data when both exist

- [ ]* 11.3 Write migration tests
  - Test users with only step_data can complete
  - Test users with both step_data and agent_context use agent_context
  - Test rollback to old flow when agent_context incomplete

- [x] 12. End-to-end integration testing
  - [x] 12.1 Write complete onboarding flow test
    - Create test in `tests/test_onboarding_e2e.py`
    - Test full flow: Fitness Assessment → Goal Setting → Workout Planning → Diet Planning → Scheduling → Completion
    - Verify all agent_context data collected correctly
    - Verify profile created with all entities
    - Verify profile is locked
    - Verify onboarding marked complete
    - Verify user can chat with General Assistant
    - _Requirements: 23.4_
  
  - [x] 12.2 Write error scenario tests
    - Test completion with incomplete data returns 400
    - Test completion twice returns 409
    - Test profile creation failure rolls back
    - Test invalid schedule data returns validation errors
    - _Requirements: 23.4_

- [x]* 12.3 Run all property tests
  - Run `poetry run pytest tests/ -m property -v`
  - Verify all 13 properties pass with 100+ iterations each
  - _Requirements: 23.1-23.10_

- [x] 13. Final checkpoint - Ensure all tests pass
  - Run `poetry run pytest tests/ --cov=app --cov-report=html`
  - Verify minimum 80% code coverage for new code
  - Verify all unit, property, integration, and e2e tests pass
  - Review coverage report in htmlcov/index.html
  - Ask user if questions arise

## Notes

- Tasks marked with `*` are optional property and unit tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and early error detection
- Property tests validate universal correctness properties across many inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate component interactions
- E2E tests validate complete user flows
- All tests should use pytest with async support (pytest-asyncio)
- Use Hypothesis for property-based testing with minimum 100 iterations per property
- Tag each property test with: **Feature: scheduling-agent-completion, Property {number}: {property_text}**
