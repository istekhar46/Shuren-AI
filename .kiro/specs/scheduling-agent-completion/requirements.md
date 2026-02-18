# Requirements Document

## Introduction

The Scheduling Agent & Onboarding Completion feature implements the final specialized onboarding agent (Steps 8-9) that sets up workout, meal, and hydration schedules, and completes the onboarding flow by creating a locked UserProfile from all collected agent context. This agent marks the transition from onboarding to the post-onboarding state where only the General Assistant Agent is available. This is the fourth and final specification that completes the conversational onboarding system.

## Glossary

- **Scheduling_Agent**: AI agent specialized in setting up workout schedules, meal timing, and hydration reminders
- **Workout_Schedule**: Database entity defining which days and times user will workout
- **Meal_Schedule**: Database entity defining timing for each meal throughout the day
- **Hydration_Preference**: Database entity defining water intake reminders and daily target
- **Profile_Creation**: Process of extracting data from agent_context and creating complete UserProfile with all related entities
- **Profile_Locking**: Setting is_locked=True on UserProfile to prevent casual modifications post-onboarding
- **Onboarding_Completion**: Marking onboarding_state.is_complete=True and transitioning to General Assistant
- **General_Assistant_Agent**: Post-onboarding agent with read-only access to user profile for answering queries
- **Agent_Context_Extraction**: Process of mapping agent_context data to database entities
- **Atomic_Transaction**: Database transaction where all operations succeed or all fail together

## Requirements

### Requirement 1: Scheduling Agent Implementation

**User Story:** As a user, I want to have a conversation about my daily schedule and set up workout times, meal times, and hydration reminders, so that I have a structured routine that fits my lifestyle.

#### Acceptance Criteria

1. WHEN SchedulingAgent is instantiated, THE System SHALL inherit from BaseOnboardingAgent with agent_type="scheduling"
2. WHEN process_message is called, THE System SHALL access workout_plan and meal_plan from agent_context
3. WHEN the agent asks about workout schedule, THE System SHALL inquire about preferred workout days of the week
4. WHEN the agent asks about workout schedule, THE System SHALL inquire about preferred workout times for each day
5. WHEN the agent asks about meal timing, THE System SHALL inquire about preferred times for each meal in the meal plan
6. WHEN the agent asks about hydration, THE System SHALL inquire about preferred reminder frequency
7. WHEN the agent asks about hydration, THE System SHALL inquire about daily water intake target in milliliters
8. WHEN sufficient schedule information is collected, THE System SHALL call save_workout_schedule tool
9. WHEN sufficient schedule information is collected, THE System SHALL call save_meal_schedule tool
10. WHEN sufficient schedule information is collected, THE System SHALL call save_hydration_preferences tool
11. WHEN all schedules are saved, THE System SHALL set step_complete=True and next_action="complete_onboarding"

### Requirement 2: Workout Schedule Data Collection

**User Story:** As a Scheduling Agent, I want to collect realistic workout schedule data, so that users receive timely workout reminders aligned with their availability.

#### Acceptance Criteria

1. WHEN the agent asks about workout days, THE System SHALL accept responses indicating specific days of the week
2. WHEN the agent asks about workout times, THE System SHALL accept responses in 24-hour or 12-hour format
3. WHEN workout frequency from workout_plan is 4 days, THE System SHALL collect 4 specific days and times
4. WHEN the user suggests unrealistic timing, THE System SHALL provide gentle guidance toward sustainable schedules
5. WHEN the user has time constraints, THE System SHALL suggest optimal workout timing based on goals and meal timing
6. WHEN workout days conflict with user's stated availability, THE System SHALL ask for clarification or alternative days

### Requirement 3: Meal Schedule Data Collection

**User Story:** As a Scheduling Agent, I want to collect realistic meal timing data, so that users receive timely meal reminders and can plan their nutrition around workouts.

#### Acceptance Criteria

1. WHEN the agent asks about meal times, THE System SHALL collect timing for each meal in the meal_plan
2. WHEN meal_frequency is 4, THE System SHALL collect times for 4 meals throughout the day
3. WHEN the agent suggests meal timing, THE System SHALL consider workout schedule to optimize pre/post-workout nutrition
4. WHEN the user suggests meal times too close together, THE System SHALL provide guidance on spacing meals appropriately
5. WHEN the user has work schedule constraints, THE System SHALL suggest meal timing that fits their routine
6. WHEN meal timing is collected, THE System SHALL ensure at least 2-3 hours between meals for proper digestion

### Requirement 4: Hydration Preferences Data Collection

**User Story:** As a Scheduling Agent, I want to collect hydration reminder preferences, so that users stay hydrated throughout the day.

#### Acceptance Criteria

1. WHEN the agent asks about hydration reminders, THE System SHALL inquire about preferred reminder frequency in hours
2. WHEN the agent asks about water intake target, THE System SHALL inquire about daily target in milliliters
3. WHEN the user is unsure about water intake, THE System SHALL suggest a target based on body weight and activity level
4. WHEN reminder frequency is provided, THE System SHALL validate it is between 1 and 4 hours
5. WHEN daily target is provided, THE System SHALL validate it is between 1500 and 5000 milliliters
6. WHEN workout intensity is high, THE System SHALL suggest higher water intake targets

### Requirement 5: Scheduling Agent Tools

**User Story:** As a Scheduling Agent, I want tools to save workout schedules, meal schedules, and hydration preferences, so that I can persist user's daily routine configuration.

#### Acceptance Criteria

1. WHEN save_workout_schedule tool is defined, THE System SHALL use LangChain @tool decorator
2. WHEN save_workout_schedule is called, THE System SHALL accept days (list of strings) and times (list of strings) as parameters
3. WHEN save_workout_schedule is called, THE System SHALL validate days are valid day names (Monday-Sunday)
4. WHEN save_workout_schedule is called, THE System SHALL validate times are in valid time format (HH:MM)
5. WHEN save_workout_schedule is called, THE System SHALL validate length of days matches length of times
6. WHEN save_workout_schedule succeeds, THE System SHALL save data to agent_context["scheduling"]["workout_schedule"]
7. WHEN save_meal_schedule tool is defined, THE System SHALL accept meal_times (dict mapping meal names to times) as parameter
8. WHEN save_meal_schedule is called, THE System SHALL validate all times are in valid time format (HH:MM)
9. WHEN save_meal_schedule is called, THE System SHALL validate number of meals matches meal_frequency from meal_plan
10. WHEN save_meal_schedule succeeds, THE System SHALL save data to agent_context["scheduling"]["meal_schedule"]
11. WHEN save_hydration_preferences tool is defined, THE System SHALL accept frequency_hours (int) and target_ml (int) as parameters
12. WHEN save_hydration_preferences is called, THE System SHALL validate frequency_hours is between 1 and 4
13. WHEN save_hydration_preferences is called, THE System SHALL validate target_ml is between 1500 and 5000
14. WHEN save_hydration_preferences succeeds, THE System SHALL save data to agent_context["scheduling"]["hydration_preferences"]
15. WHEN any save tool succeeds, THE System SHALL include completed_at timestamp in ISO 8601 format

### Requirement 6: Scheduling Agent System Prompt

**User Story:** As a Scheduling Agent, I want a clear system prompt with context from previous steps, so that I can suggest optimal scheduling based on user's complete profile.

#### Acceptance Criteria

1. WHEN get_system_prompt is called, THE System SHALL return a prompt including workout_plan summary from agent_context
2. WHEN get_system_prompt is called, THE System SHALL return a prompt including meal_plan summary from agent_context
3. WHEN the prompt is used, THE System SHALL instruct the agent to ask about workout days and times
4. WHEN the prompt is used, THE System SHALL instruct the agent to ask about meal timing for each meal
5. WHEN the prompt is used, THE System SHALL instruct the agent to ask about hydration reminder preferences
6. WHEN the prompt is used, THE System SHALL instruct the agent to consider user's daily routine and constraints
7. WHEN the prompt is used, THE System SHALL instruct the agent to suggest optimal timing based on goals and workout plan
8. WHEN the prompt is used, THE System SHALL instruct the agent to be flexible with user preferences
9. WHEN the prompt is used, THE System SHALL instruct the agent to explain importance of consistency in scheduling

### Requirement 7: Onboarding Completion Verification

**User Story:** As a system, I want to verify all agents have completed their steps before creating the user profile, so that profile creation only happens with complete data.

#### Acceptance Criteria

1. WHEN onboarding completion is triggered, THE System SHALL verify agent_context contains "fitness_assessment" with completed_at timestamp
2. WHEN onboarding completion is triggered, THE System SHALL verify agent_context contains "goal_setting" with completed_at timestamp
3. WHEN onboarding completion is triggered, THE System SHALL verify agent_context contains "workout_planning" with user_approved=True
4. WHEN onboarding completion is triggered, THE System SHALL verify agent_context contains "diet_planning" with user_approved=True
5. WHEN onboarding completion is triggered, THE System SHALL verify agent_context contains "scheduling" with all three schedule types
6. WHEN any agent data is missing, THE System SHALL raise OnboardingIncompleteError with details of missing data
7. WHEN all agent data is present, THE System SHALL proceed to profile creation

### Requirement 8: Profile Creation from Agent Context

**User Story:** As a system, I want to create a complete UserProfile from agent_context data, so that users have a fully configured profile after onboarding.

#### Acceptance Criteria

1. WHEN create_user_profile is called, THE System SHALL extract fitness_level from agent_context["fitness_assessment"]["fitness_level"]
2. WHEN create_user_profile is called, THE System SHALL create UserProfile entity with user_id and fitness_level
3. WHEN create_user_profile is called, THE System SHALL set is_locked=True on the UserProfile
4. WHEN create_user_profile is called, THE System SHALL create FitnessGoal entities from agent_context["goal_setting"]
5. WHEN create_user_profile is called, THE System SHALL create PhysicalConstraint entities from agent_context["fitness_assessment"]["limitations"]
6. WHEN create_user_profile is called, THE System SHALL create DietaryPreference entity from agent_context["diet_planning"]["preferences"]
7. WHEN create_user_profile is called, THE System SHALL create MealPlan entity from agent_context["diet_planning"]["proposed_plan"]
8. WHEN create_user_profile is called, THE System SHALL create MealSchedule entities from agent_context["scheduling"]["meal_schedule"]
9. WHEN create_user_profile is called, THE System SHALL create WorkoutSchedule entities from agent_context["scheduling"]["workout_schedule"]
10. WHEN create_user_profile is called, THE System SHALL create HydrationPreference entity from agent_context["scheduling"]["hydration_preferences"]
11. WHEN create_user_profile is called, THE System SHALL execute all database operations in a single atomic transaction
12. WHEN profile creation succeeds, THE System SHALL commit the transaction and return the created UserProfile
13. WHEN profile creation fails, THE System SHALL rollback the transaction and raise an error

### Requirement 9: Workout Plan to Database Mapping

**User Story:** As a system, I want to map workout plan data from agent_context to database entities, so that workout plans are persisted correctly.

#### Acceptance Criteria

1. WHEN mapping workout_plan, THE System SHALL extract frequency from agent_context["workout_planning"]["proposed_plan"]["frequency"]
2. WHEN mapping workout_plan, THE System SHALL extract duration_minutes from agent_context["workout_planning"]["proposed_plan"]["duration_minutes"]
3. WHEN mapping workout_plan, THE System SHALL extract training_split from agent_context["workout_planning"]["proposed_plan"]["training_split"]
4. WHEN mapping workout_plan, THE System SHALL extract exercises list from agent_context["workout_planning"]["proposed_plan"]["exercises"]
5. WHEN mapping workout_plan, THE System SHALL store exercises as JSONB in a WorkoutPlan-related entity
6. WHEN mapping workout_schedule, THE System SHALL create one WorkoutSchedule entity per workout day
7. WHEN creating WorkoutSchedule, THE System SHALL set day_of_week from agent_context["scheduling"]["workout_schedule"]["days"]
8. WHEN creating WorkoutSchedule, THE System SHALL set time_of_day from agent_context["scheduling"]["workout_schedule"]["times"]

### Requirement 10: Meal Plan to Database Mapping

**User Story:** As a system, I want to map meal plan data from agent_context to database entities, so that meal plans are persisted correctly.

#### Acceptance Criteria

1. WHEN mapping meal_plan, THE System SHALL extract daily_calories from agent_context["diet_planning"]["proposed_plan"]["daily_calories"]
2. WHEN mapping meal_plan, THE System SHALL extract protein_g from agent_context["diet_planning"]["proposed_plan"]["protein_g"]
3. WHEN mapping meal_plan, THE System SHALL extract carbs_g from agent_context["diet_planning"]["proposed_plan"]["carbs_g"]
4. WHEN mapping meal_plan, THE System SHALL extract fats_g from agent_context["diet_planning"]["proposed_plan"]["fats_g"]
5. WHEN mapping meal_plan, THE System SHALL extract meal_frequency from agent_context["diet_planning"]["proposed_plan"]["meal_frequency"]
6. WHEN mapping meal_plan, THE System SHALL store sample_meals as JSONB in MealPlan entity
7. WHEN mapping meal_schedule, THE System SHALL create one MealSchedule entity per meal
8. WHEN creating MealSchedule, THE System SHALL set meal_name and time_of_day from agent_context["scheduling"]["meal_schedule"]

### Requirement 11: Dietary Preferences to Database Mapping

**User Story:** As a system, I want to map dietary preferences from agent_context to database entities, so that dietary restrictions are persisted correctly.

#### Acceptance Criteria

1. WHEN mapping dietary_preferences, THE System SHALL extract diet_type from agent_context["diet_planning"]["preferences"]["diet_type"]
2. WHEN mapping dietary_preferences, THE System SHALL extract allergies from agent_context["diet_planning"]["preferences"]["allergies"]
3. WHEN mapping dietary_preferences, THE System SHALL extract dislikes from agent_context["diet_planning"]["preferences"]["dislikes"]
4. WHEN mapping dietary_preferences, THE System SHALL create DietaryPreference entity with diet_type
5. WHEN allergies are present, THE System SHALL store them as JSONB array in DietaryPreference entity
6. WHEN dislikes are present, THE System SHALL store them as JSONB array in DietaryPreference entity

### Requirement 12: Fitness Goals to Database Mapping

**User Story:** As a system, I want to map fitness goals from agent_context to database entities, so that user goals are persisted correctly.

#### Acceptance Criteria

1. WHEN mapping fitness_goals, THE System SHALL extract primary_goal from agent_context["goal_setting"]["primary_goal"]
2. WHEN mapping fitness_goals, THE System SHALL create FitnessGoal entity with goal_type=primary_goal and is_primary=True
3. WHEN secondary_goal is present, THE System SHALL create FitnessGoal entity with goal_type=secondary_goal and is_primary=False
4. WHEN target_weight_kg is present, THE System SHALL store it in the primary FitnessGoal entity
5. WHEN target_body_fat_percentage is present, THE System SHALL store it in the primary FitnessGoal entity

### Requirement 13: Physical Constraints to Database Mapping

**User Story:** As a system, I want to map physical limitations from agent_context to database entities, so that user constraints are persisted correctly.

#### Acceptance Criteria

1. WHEN mapping physical_constraints, THE System SHALL extract limitations from agent_context["fitness_assessment"]["limitations"]
2. WHEN limitations is a list, THE System SHALL create one PhysicalConstraint entity per limitation
3. WHEN creating PhysicalConstraint, THE System SHALL set constraint_type based on limitation category
4. WHEN creating PhysicalConstraint, THE System SHALL set description from limitation text
5. WHEN limitations list is empty, THE System SHALL not create any PhysicalConstraint entities

### Requirement 14: Hydration Preferences to Database Mapping

**User Story:** As a system, I want to map hydration preferences from agent_context to database entities, so that hydration reminders are configured correctly.

#### Acceptance Criteria

1. WHEN mapping hydration_preferences, THE System SHALL extract frequency_hours from agent_context["scheduling"]["hydration_preferences"]["frequency_hours"]
2. WHEN mapping hydration_preferences, THE System SHALL extract target_ml from agent_context["scheduling"]["hydration_preferences"]["target_ml"]
3. WHEN creating HydrationPreference, THE System SHALL set reminder_frequency_hours from frequency_hours
4. WHEN creating HydrationPreference, THE System SHALL set daily_target_ml from target_ml

### Requirement 15: Onboarding State Completion

**User Story:** As a system, I want to mark onboarding as complete and transition to post-onboarding state, so that users can access the General Assistant Agent.

#### Acceptance Criteria

1. WHEN profile creation succeeds, THE System SHALL set onboarding_state.is_complete=True
2. WHEN profile creation succeeds, THE System SHALL set onboarding_state.current_agent="general_assistant"
3. WHEN profile creation succeeds, THE System SHALL set onboarding_state.current_step to the final step number
4. WHEN onboarding is marked complete, THE System SHALL commit the OnboardingState update
5. WHEN onboarding completion fails, THE System SHALL rollback both profile creation and onboarding state updates

### Requirement 16: Post-Onboarding Agent Routing

**User Story:** As a system, I want to route post-onboarding chat messages to the General Assistant Agent, so that users can interact with their profile after onboarding.

#### Acceptance Criteria

1. WHEN onboarding_state.is_complete is True, THE System SHALL route chat messages to General Assistant Agent
2. WHEN onboarding_state.current_agent is "general_assistant", THE System SHALL not route to onboarding agents
3. WHEN General Assistant Agent is active, THE System SHALL have read access to complete UserProfile
4. WHEN General Assistant Agent is active, THE System SHALL not modify profile without explicit user request
5. WHEN user requests profile modifications post-onboarding, THE System SHALL require explicit confirmation before unlocking profile

### Requirement 17: Backward Compatibility with Existing Onboarding

**User Story:** As a system administrator, I want the new onboarding completion to coexist with existing onboarding flow, so that we can deploy incrementally without breaking existing functionality.

#### Acceptance Criteria

1. WHEN existing onboarding completion endpoint is called, THE System SHALL continue to function without errors
2. WHEN users mid-onboarding during migration exist, THE System SHALL handle gracefully with fallback to old flow
3. WHEN existing step_data structure is present, THE System SHALL preserve it during agent-based onboarding
4. WHEN profile creation from agent_context fails, THE System SHALL allow rollback to old onboarding flow
5. WHEN both old and new onboarding data exist, THE System SHALL prioritize agent_context data for profile creation

### Requirement 18: Error Handling for Profile Creation

**User Story:** As a user, I want clear error messages when profile creation fails, so that I understand what went wrong and can take corrective action.

#### Acceptance Criteria

1. WHEN required agent_context data is missing, THE System SHALL return HTTP 400 with details of missing data
2. WHEN database constraint violations occur, THE System SHALL return HTTP 409 with conflict details
3. WHEN profile creation transaction fails, THE System SHALL rollback all changes and return HTTP 500
4. WHEN data validation fails during mapping, THE System SHALL return HTTP 422 with validation errors
5. WHEN profile creation succeeds, THE System SHALL return HTTP 201 with created UserProfile data
6. WHEN any error occurs, THE System SHALL log detailed error information for debugging

### Requirement 19: Profile Creation Service

**User Story:** As a developer, I want a dedicated service for profile creation from agent context, so that the logic is reusable and testable.

#### Acceptance Criteria

1. WHEN ProfileCreationService is instantiated, THE System SHALL accept db (AsyncSession) as parameter
2. WHEN create_profile_from_agent_context is called, THE System SHALL accept user_id and agent_context as parameters
3. WHEN create_profile_from_agent_context is called, THE System SHALL verify all required agent data is present
4. WHEN create_profile_from_agent_context is called, THE System SHALL create UserProfile and all related entities
5. WHEN create_profile_from_agent_context is called, THE System SHALL execute all operations in atomic transaction
6. WHEN create_profile_from_agent_context succeeds, THE System SHALL return created UserProfile with all relationships loaded
7. WHEN create_profile_from_agent_context fails, THE System SHALL raise descriptive exception with error details

### Requirement 20: Onboarding Completion API Endpoint

**User Story:** As a client application, I want an endpoint to trigger onboarding completion, so that I can finalize onboarding after all agents complete.

#### Acceptance Criteria

1. WHEN POST /api/v1/onboarding/complete is called, THE System SHALL require authentication via JWT token
2. WHEN the request is authenticated, THE System SHALL load user's OnboardingState
3. WHEN OnboardingState is loaded, THE System SHALL verify all agents have completed
4. WHEN verification passes, THE System SHALL call ProfileCreationService to create profile
5. WHEN profile creation succeeds, THE System SHALL mark onboarding as complete
6. WHEN profile creation succeeds, THE System SHALL return HTTP 201 with UserProfile data
7. WHEN onboarding is already complete, THE System SHALL return HTTP 409 Conflict
8. WHEN required agent data is missing, THE System SHALL return HTTP 400 Bad Request
9. WHEN user is not authenticated, THE System SHALL return HTTP 401 Unauthorized

### Requirement 21: Data Validation for Schedule Times

**User Story:** As a system, I want to validate schedule times are realistic and non-conflicting, so that users have practical schedules.

#### Acceptance Criteria

1. WHEN workout times are validated, THE System SHALL ensure times are in HH:MM format
2. WHEN workout times are validated, THE System SHALL ensure times are between 00:00 and 23:59
3. WHEN meal times are validated, THE System SHALL ensure at least 2 hours between consecutive meals
4. WHEN meal times are validated, THE System SHALL ensure times are in chronological order throughout the day
5. WHEN hydration frequency is validated, THE System SHALL ensure reminders don't occur more than once per hour
6. WHEN workout and meal times overlap, THE System SHALL provide warning but allow user to proceed

### Requirement 22: Graceful Handling of Partial Data

**User Story:** As a system, I want to handle missing optional data gracefully, so that profile creation succeeds even with incomplete information.

#### Acceptance Criteria

1. WHEN secondary_goal is missing, THE System SHALL create profile with only primary goal
2. WHEN target_weight_kg is missing, THE System SHALL create profile without weight target
3. WHEN target_body_fat_percentage is missing, THE System SHALL create profile without body fat target
4. WHEN limitations list is empty, THE System SHALL create profile without PhysicalConstraint entities
5. WHEN optional fields are missing, THE System SHALL use sensible defaults where appropriate
6. WHEN required fields are missing, THE System SHALL raise validation error and not create profile

### Requirement 23: Testing Coverage

**User Story:** As a developer, I want comprehensive tests for scheduling agent and profile creation, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. WHEN unit tests are run for SchedulingAgent, THE System SHALL verify schedule data collection works correctly
2. WHEN unit tests are run for ProfileCreationService, THE System SHALL verify profile creation from complete agent_context
3. WHEN unit tests are run for ProfileCreationService, THE System SHALL verify graceful handling of missing optional data
4. WHEN integration tests are run, THE System SHALL verify complete onboarding flow from Step 1 through profile creation
5. WHEN property tests are run, THE System SHALL verify schedule time validation for all valid time formats
6. WHEN property tests are run, THE System SHALL verify meal time spacing validation
7. WHEN end-to-end tests are run, THE System SHALL verify user can complete onboarding and access General Assistant
8. WHEN tests are run, THE System SHALL achieve minimum 80% code coverage for new code
9. WHEN migration tests are run, THE System SHALL verify existing users can complete onboarding with new system
10. WHEN transaction tests are run, THE System SHALL verify atomic profile creation (all or nothing)
