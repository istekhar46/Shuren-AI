# Implementation Plan: Planning Agents with Proposal Workflow

## Overview

This implementation plan breaks down the Planning Agents with Proposal Workflow feature into discrete coding tasks. The plan follows an incremental approach: implement services first, then agents, then tools, with testing integrated throughout. Each task builds on previous work and ends with integrated, tested code.

## Tasks

- [x] 1. Implement Workout Plan Generator Service
  - Create `backend/app/services/workout_plan_generator.py`
  - Implement `WorkoutPlan`, `WorkoutDay`, and `Exercise` Pydantic models with validation
  - Implement `WorkoutPlanGenerator.generate_plan()` method with fitness level, goal, and preference parameters
  - Implement training split determination logic (Full Body, Upper/Lower, PPL, Body Part Split)
  - Implement workout day generation for each split type
  - Implement progression strategy determination
  - Implement `WorkoutPlanGenerator.modify_plan()` method for plan modifications
  - Implement input validation with appropriate ValueError messages
  - _Requirements: 2.1-2.12, 13.1-13.4_

- [x]* 1.1 Write unit tests for WorkoutPlanGenerator
  - Test plan generation for all fitness levels (beginner/intermediate/advanced)
  - Test plan generation for all goals (fat_loss/muscle_gain/general_fitness)
  - Test training split determination for different frequencies
  - Test exercise selection based on location and equipment
  - Test duration constraint enforcement
  - Test input validation (invalid fitness_level, frequency out of range, etc.)
  - Test plan modification with various modification requests
  - _Requirements: 2.1-2.12, 13.1-13.4_

- [ ]* 1.2 Write property test for workout plan frequency ranges
  - **Property 3: Fitness Level Determines Frequency Range**
  - **Validates: Requirements 2.2, 2.3, 2.4**

- [ ]* 1.3 Write property test for workout plan structural completeness
  - **Property 8: Workout Plan Structural Completeness**
  - **Validates: Requirements 2.11, 2.12, 13.1, 13.4**

- [ ]* 1.4 Write property test for workout plan validation ranges
  - **Property 9: Workout Plan Validation Ranges**
  - **Validates: Requirements 13.2, 13.3**

- [x] 2. Implement Meal Plan Generator Service
  - Create `backend/app/services/meal_plan_generator.py`
  - Implement `MealPlan`, `SampleMeal`, and `MealType` Pydantic models with validation
  - Implement `MealPlanGenerator.generate_plan()` method with goal, workout plan, and dietary preferences
  - Implement TDEE and calorie target calculation based on goal and workout frequency
  - Implement macro calculation (protein/carbs/fats) based on goal
  - Implement sample meal generation respecting diet type, allergies, and dislikes
  - Implement meal timing suggestions based on meal frequency
  - Implement `MealPlanGenerator.modify_plan()` method for plan modifications
  - Implement input validation with appropriate ValueError messages
  - Implement macro sum validation to ensure macros equal calories within 10%
  - _Requirements: 5.1-5.12, 13.5-13.9_

- [x]* 2.1 Write unit tests for MealPlanGenerator
  - Test plan generation for all goals with calorie calculations
  - Test macro calculations for different goals and workout frequencies
  - Test dietary restriction enforcement (vegetarian, vegan)
  - Test allergen and dislike exclusion from sample meals
  - Test meal frequency matching
  - Test high training volume calorie adjustments
  - Test input validation (invalid diet_type, meal_frequency out of range, etc.)
  - Test plan modification with various modification requests
  - _Requirements: 5.1-5.12, 13.5-13.9_

- [ ]* 2.2 Write property test for calorie targets by goal
  - **Property 10: Calorie Targets Align with Goals**
  - **Validates: Requirements 5.2, 5.3, 5.4**

- [ ]* 2.3 Write property test for dietary restrictions
  - **Property 11: Dietary Restrictions Respected**
  - **Validates: Requirements 5.5, 5.6**

- [ ]* 2.4 Write property test for allergen exclusion
  - **Property 12: Allergen and Dislike Exclusion**
  - **Validates: Requirements 5.7, 5.8**

- [ ]* 2.5 Write property test for macro sum equals calories (CRITICAL)
  - **Property 17: Macro Sum Equals Calories**
  - **Validates: Requirements 13.7**

- [ ]* 2.6 Write property test for meal plan structural completeness
  - **Property 15: Meal Plan Structural Completeness**
  - **Validates: Requirements 5.11, 5.12, 13.5, 13.9**

- [x] 3. Checkpoint - Ensure all service tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Workout Planning Agent
  - Create `backend/app/agents/onboarding/workout_planning.py`
  - Implement `WorkoutPlanningAgent` class extending `BaseOnboardingAgent`
  - Implement `__init__` to initialize `WorkoutPlanGenerator` and `current_plan` storage
  - Implement `process_message()` using LangChain tool-calling agent pattern
  - Implement `get_tools()` with three tools: generate_workout_plan, save_workout_plan, modify_workout_plan
  - Implement `generate_workout_plan` tool to call WorkoutPlanGenerator service
  - Implement `save_workout_plan` tool with user_approved validation and context saving
  - Implement `modify_workout_plan` tool to call WorkoutPlanGenerator.modify_plan
  - Implement `get_system_prompt()` with context from fitness_assessment and goal_setting
  - Implement `_check_if_complete()` to verify user_approved=True in agent_context
  - Add comprehensive error handling in all tools
  - _Requirements: 1.1-1.10, 3.1-3.11_

- [x]* 4.1 Write unit tests for WorkoutPlanningAgent
  - Test agent instantiation and inheritance from BaseOnboardingAgent
  - Test process_message with preference collection
  - Test generate_workout_plan tool invocation
  - Test save_workout_plan tool with user_approved=True
  - Test save_workout_plan tool rejection with user_approved=False
  - Test modify_workout_plan tool invocation
  - Test system prompt includes context from previous agents
  - Test _check_if_complete returns True after approved save
  - Test error handling in tools (invalid parameters, database errors)
  - _Requirements: 1.1-1.10, 3.1-3.11_

- [ ]* 4.2 Write property test for plan approval saves data
  - **Property 1: Plan Approval Saves Data with Metadata**
  - **Validates: Requirements 3.7, 3.8**

- [ ]* 4.3 Write property test for step completion after approval
  - **Property 2: Step Completion After Approval**
  - **Validates: Requirements 1.9, 1.10**

- [x] 5. Implement Diet Planning Agent
  - Create `backend/app/agents/onboarding/diet_planning.py`
  - Implement `DietPlanningAgent` class extending `BaseOnboardingAgent`
  - Implement `__init__` to initialize `MealPlanGenerator` and `current_plan` storage
  - Implement `process_message()` using LangChain tool-calling agent pattern
  - Implement `get_tools()` with three tools: generate_meal_plan, save_meal_plan, modify_meal_plan
  - Implement `generate_meal_plan` tool to call MealPlanGenerator service
  - Implement `save_meal_plan` tool with user_approved validation and context saving
  - Implement `modify_meal_plan` tool to call MealPlanGenerator.modify_plan
  - Implement `get_system_prompt()` with context from fitness_assessment, goal_setting, and workout_planning
  - Implement `_check_if_complete()` to verify user_approved=True in agent_context
  - Add comprehensive error handling in all tools
  - _Requirements: 4.1-4.11, 6.1-6.11_

- [x]* 5.1 Write unit tests for DietPlanningAgent
  - Test agent instantiation and inheritance from BaseOnboardingAgent
  - Test process_message with dietary preference collection
  - Test generate_meal_plan tool invocation with workout plan context
  - Test save_meal_plan tool with user_approved=True
  - Test save_meal_plan tool rejection with user_approved=False
  - Test modify_meal_plan tool invocation
  - Test system prompt includes context from all previous agents
  - Test _check_if_complete returns True after approved save
  - Test error handling in tools (invalid parameters, database errors)
  - _Requirements: 4.1-4.11, 6.1-6.11_

- [ ]* 5.2 Write property test for context handover to diet planning
  - **Property 20: Context Handover to Diet Planning**
  - **Validates: Requirements 12.6, 12.7**

- [x] 6. Checkpoint - Ensure all agent tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Integration Testing and End-to-End Flows
  - Write integration test for complete workout planning flow (preferences → generate → approve → save)
  - Write integration test for complete diet planning flow (preferences → generate → approve → save)
  - Write integration test for modification workflow (generate → modify → approve → save)
  - Write integration test for end-to-end planning flow (workout planning → diet planning with context handover)
  - Write integration test for approval detection with various approval phrases
  - Write integration test for non-approval handling (questions, feedback without approval)
  - Test error scenarios (save before generate, invalid modifications, database failures)
  - _Requirements: 7.1-7.6, 8.1-8.9, 14.1-14.6, 15.1-15.10_

- [x] 8. Update Orchestrator Agent Factory
  - Update `backend/app/services/onboarding_orchestrator.py`
  - Ensure `_create_agent()` imports and instantiates WorkoutPlanningAgent and DietPlanningAgent
  - Verify routing logic in `_step_to_agent()` correctly maps steps 4-5 to WORKOUT_PLANNING and steps 6-7 to DIET_PLANNING
  - No other changes needed - orchestrator already supports new agents
  - _Requirements: Integration with Spec 1_

- [x] 9. Final Checkpoint - Ensure all tests pass
  - Run full test suite: `poetry run pytest backend/tests/test_planning_agents/`
  - Run with coverage: `poetry run pytest backend/tests/test_planning_agents/ --cov=app.agents.onboarding --cov=app.services --cov-report=html`
  - Verify minimum 80% code coverage
  - Verify all property tests pass with 100 iterations
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Checkpoints ensure incremental validation
- All code should follow existing patterns from Specs 1 and 2
- Use `poetry run` prefix for all Python commands
- Services are implemented first to enable agent testing
- Agents are implemented after services are complete and tested
- Integration tests verify complete workflows across multiple agents
