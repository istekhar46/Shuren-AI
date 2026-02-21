# Implementation Plan: General Agent Delegation Tools

## Overview

This implementation plan adds delegation tools to the General Assistant Agent, enabling it to query user data (workouts, meals, schedules, exercises, recipes) by extracting shared query logic into a service layer and creating new LangChain tools.

## Tasks

- [x] 1. Create service layer for workout queries
  - [x] 1.1 Create `app/services/workout_service.py` with `WorkoutService` class
    - Implement `get_today_workout(user_id, db_session)` method
    - Query WorkoutPlan, WorkoutDay, WorkoutExercise, WorkoutSchedule tables
    - Apply soft delete filtering (`deleted_at IS NULL`)
    - Return dict with workout details or None if no workout scheduled
    - Raise ValueError if user profile not found
    - _Requirements: FR-1, US-1.1, US-1.2, NFR-2_
  
  - [x] 1.2 Implement `get_exercise_demo(exercise_name, db_session)` method
    - Query ExerciseLibrary table with case-insensitive partial match
    - Apply soft delete filtering
    - Return dict with exercise details or None if not found
    - _Requirements: FR-4, US-4.1, US-4.2_
  
  - [x] 1.3 Write property test for workout query completeness
    - **Property 1: Workout Query Returns Complete Data**
    - **Validates: Requirements US-1.1, US-1.2**
  
  - [ ]* 1.4 Write unit tests for workout service
    - Test get_today_workout with valid workout
    - Test get_today_workout with no workout (rest day)
    - Test get_today_workout with user not found
    - Test get_exercise_demo with valid exercise
    - Test get_exercise_demo with exercise not found
    - _Requirements: FR-1, FR-4_

- [x] 2. Create service layer for meal queries
  - [x] 2.1 Create `app/services/meal_service.py` with `MealService` class
    - Implement `get_today_meal_plan(user_id, db_session)` method
    - Query MealTemplate, TemplateMeal, Dish, MealSchedule, MealPlan tables
    - Apply soft delete filtering
    - Calculate daily totals (calories, protein, carbs, fats)
    - Return dict with meal details or None if no meal plan configured
    - Raise ValueError if user profile not found
    - _Requirements: FR-2, US-2.1, US-2.2, NFR-2_
  
  - [x] 2.2 Implement `get_recipe_details(dish_name, db_session)` method
    - Query Dish, DishIngredient, Ingredient tables with case-insensitive partial match
    - Apply soft delete filtering
    - Include ingredients list with quantities and units
    - Return dict with recipe details or None if not found
    - _Requirements: FR-5, US-5.1, US-5.2_
  
  - [x]* 2.3 Write property test for meal query completeness
    - **Property 2: Meal Query Returns Complete Data**
    - **Validates: Requirements US-2.1, US-2.2**
  
  - [x]* 2.4 Write property test for recipe query completeness
    - **Property 5: Recipe Query Returns Complete Data**
    - **Validates: Requirements US-5.1, US-5.2**
  
  - [x]* 2.5 Write unit tests for meal service
    - Test get_today_meal_plan with valid meal plan
    - Test get_today_meal_plan with no meal plan configured
    - Test get_today_meal_plan with user not found
    - Test get_recipe_details with valid dish
    - Test get_recipe_details with dish not found
    - _Requirements: FR-2, FR-5_

- [x] 3. Create service layer for schedule queries
  - [x] 3.1 Create `app/services/schedule_service.py` with `ScheduleService` class
    - Implement `get_upcoming_schedule(user_id, db_session)` method
    - Query WorkoutSchedule and MealSchedule tables
    - Apply soft delete filtering
    - Format workout schedules with day names and times
    - Format meal schedules with meal names and times
    - Return dict with both workout and meal schedules
    - Raise ValueError if user profile not found
    - _Requirements: FR-3, US-3.1, US-3.2, NFR-2_
  
  - [x]* 3.2 Write property test for schedule query completeness
    - **Property 3: Schedule Query Returns Complete Data**
    - **Validates: Requirements US-3.1, US-3.2**
  
  - [ ]* 3.3 Write unit tests for schedule service
    - Test get_upcoming_schedule with valid schedules
    - Test get_upcoming_schedule with no schedules configured
    - Test get_upcoming_schedule with user not found
    - _Requirements: FR-3_

- [x] 4. Checkpoint - Ensure service layer tests pass
  - Ensure all service layer tests pass, ask the user if questions arise.

- [x] 5. Add delegation tools to General Assistant Agent
  - [x] 5.1 Add `get_workout_info` tool to `GeneralAssistantAgent.get_tools()`
    - Import WorkoutService
    - Create @tool decorated function
    - Call WorkoutService.get_today_workout with context.user_id
    - Handle None result with rest day message
    - Format response as JSON string with metadata
    - Handle ValueError and SQLAlchemyError exceptions
    - Return user-friendly error messages
    - _Requirements: FR-1, US-1.1, US-1.2, US-1.3, US-1.4, NFR-3_
  
  - [x] 5.2 Add `get_meal_info` tool to `GeneralAssistantAgent.get_tools()`
    - Import MealService
    - Create @tool decorated function
    - Call MealService.get_today_meal_plan with context.user_id
    - Handle None result with helpful message
    - Format response as JSON string with metadata
    - Handle exceptions with user-friendly error messages
    - _Requirements: FR-2, US-2.1, US-2.2, US-2.3, US-2.4, NFR-3_
  
  - [x] 5.3 Add `get_schedule_info` tool to `GeneralAssistantAgent.get_tools()`
    - Import ScheduleService
    - Create @tool decorated function
    - Call ScheduleService.get_upcoming_schedule with context.user_id
    - Format response as JSON string with metadata
    - Handle exceptions with user-friendly error messages
    - _Requirements: FR-3, US-3.1, US-3.2, US-3.3, NFR-3_
  
  - [x] 5.4 Add `get_exercise_demo` tool to `GeneralAssistantAgent.get_tools()`
    - Create @tool decorated function with exercise_name parameter
    - Call WorkoutService.get_exercise_demo
    - Handle None result with helpful error message
    - Format response as JSON string with metadata
    - Handle exceptions with user-friendly error messages
    - _Requirements: FR-4, US-4.1, US-4.2, US-4.3, US-4.4, NFR-3_
  
  - [x] 5.5 Add `get_recipe_details` tool to `GeneralAssistantAgent.get_tools()`
    - Create @tool decorated function with dish_name parameter
    - Call MealService.get_recipe_details
    - Handle None result with helpful error message
    - Format response as JSON string with metadata
    - Handle exceptions with user-friendly error messages
    - _Requirements: FR-5, US-5.1, US-5.2, US-5.3, US-5.4, NFR-3_
  
  - [x] 5.6 Update `_system_prompt` to document new tools
    - Add descriptions for all 5 new tools
    - Explain when to use each tool
    - Maintain friendly, supportive tone
    - _Requirements: FR-1, FR-2, FR-3, FR-4, FR-5_

- [x] 6. Integration testing
  - [x]* 6.1 Write integration test for get_workout_info tool
    - Test end-to-end from tool call to database query
    - Verify response format matches design
    - Test with authenticated client
    - _Requirements: FR-1, US-1.1, US-1.2, US-1.3_
  
  - [x]* 6.2 Write integration test for get_meal_info tool
    - Test end-to-end from tool call to database query
    - Verify response format matches design
    - Test with authenticated client
    - _Requirements: FR-2, US-2.1, US-2.2, US-2.3_
  
  - [x]* 6.3 Write integration test for get_schedule_info tool
    - Test end-to-end from tool call to database query
    - Verify response format matches design
    - Test with authenticated client
    - _Requirements: FR-3, US-3.1, US-3.2, US-3.3_
  
  - [x]* 6.4 Write integration test for get_exercise_demo tool
    - Test end-to-end from tool call to database query
    - Verify response format matches design
    - Test with authenticated client
    - _Requirements: FR-4, US-4.1, US-4.2, US-4.3_
  
  - [x]* 6.5 Write integration test for get_recipe_details tool
    - Test end-to-end from tool call to database query
    - Verify response format matches design
    - Test with authenticated client
    - _Requirements: FR-5, US-5.1, US-5.2, US-5.3_
  
  - [x]* 6.6 Write property test for user data isolation
    - **Property 7: User Data Isolation**
    - **Validates: Requirements TC-2**
  
  - [x]* 6.7 Write property test for soft delete filtering
    - **Property 8: Soft Delete Filtering**
    - **Validates: Requirements TC-1**

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Service layer extraction avoids code duplication with specialized agents
- All tools use consistent error handling and response formats
- All database queries apply soft delete filtering
- All tools use AgentContext.user_id for data isolation

