# Requirements Document

## Introduction

The Planning Agents with Proposal Workflow feature implements the Workout Planning Agent (Steps 4-5) and Diet Planning Agent (Steps 6-7) that generate personalized plans and present them to users for approval. Unlike the previous agents that only collect information, these agents actively create workout and meal plans, explain their reasoning, detect approval intent from natural language, and allow iterative modifications before saving. This is the third of four specifications building on the Onboarding Agent Foundation and Fitness & Goal Agents to create a complete conversational onboarding system.

## Glossary

- **Workout_Planning_Agent**: AI agent specialized in collecting workout preferences and generating personalized workout plans
- **Diet_Planning_Agent**: AI agent specialized in collecting dietary preferences and generating personalized meal plans
- **Plan_Generator**: Service that creates structured workout or meal plans based on user profile and preferences
- **Approval_Intent**: Natural language signal from user indicating they approve a proposed plan
- **Modification_Request**: Natural language signal from user requesting changes to a proposed plan
- **Workout_Plan**: Structured data containing exercise schedule, sets, reps, and progression strategy
- **Meal_Plan**: Structured data containing daily calorie target, macro breakdown, meal frequency, and sample meals
- **Plan_Proposal**: Process of presenting a generated plan to user with explanation and rationale
- **Iterative_Refinement**: Process of modifying a plan based on user feedback until approval is obtained

## Requirements

### Requirement 1: Workout Planning Agent Implementation

**User Story:** As a user, I want to have a conversation about my workout preferences and receive a personalized workout plan, so that I have a structured training program aligned with my goals and constraints.

#### Acceptance Criteria

1. WHEN WorkoutPlanningAgent is instantiated, THE System SHALL inherit from BaseOnboardingAgent with agent_type="workout_planning"
2. WHEN process_message is called, THE System SHALL access fitness_level and primary_goal from agent_context
3. WHEN the agent asks about preferences, THE System SHALL inquire about workout location (home/gym)
4. WHEN the agent asks about preferences, THE System SHALL inquire about available equipment
5. WHEN the agent asks about preferences, THE System SHALL inquire about preferred workout frequency per week
6. WHEN the agent asks about preferences, THE System SHALL inquire about available time per session
7. WHEN sufficient preferences are collected, THE System SHALL call generate_workout_plan tool to create a plan
8. WHEN a plan is generated, THE System SHALL present it to the user with clear explanation of the structure and rationale
9. WHEN the user approves the plan, THE System SHALL call save_workout_plan tool with user_approved=True
10. WHEN the plan is saved, THE System SHALL set step_complete=True and next_action="advance_step"

### Requirement 2: Workout Plan Generation Service

**User Story:** As a Workout Planning Agent, I want a service that generates realistic workout plans, so that I can propose structured training programs to users.

#### Acceptance Criteria

1. WHEN WorkoutPlanGenerator.generate_plan is called, THE System SHALL accept fitness_level, primary_goal, frequency, location, duration_minutes, and equipment as parameters
2. WHEN fitness_level is "beginner", THE System SHALL generate plans with 2-4 days per week and focus on compound movements
3. WHEN fitness_level is "intermediate", THE System SHALL generate plans with 3-5 days per week and include progressive overload
4. WHEN fitness_level is "advanced", THE System SHALL generate plans with 4-6 days per week and include periodization
5. WHEN primary_goal is "muscle_gain", THE System SHALL emphasize resistance training with 8-12 rep ranges
6. WHEN primary_goal is "fat_loss", THE System SHALL include both resistance training and cardio components
7. WHEN primary_goal is "general_fitness", THE System SHALL balance strength, cardio, and flexibility work
8. WHEN location is "home" and equipment is limited, THE System SHALL generate bodyweight-focused exercises
9. WHEN location is "gym", THE System SHALL include equipment-based exercises appropriate for the goal
10. WHEN duration_minutes is provided, THE System SHALL structure workouts to fit within the time constraint
11. WHEN a plan is generated, THE System SHALL include exercise names, sets, reps, rest periods, and progression notes
12. WHEN a plan is generated, THE System SHALL return a structured WorkoutPlan object with all required fields

### Requirement 3: Workout Planning Agent Tools

**User Story:** As a Workout Planning Agent, I want tools to generate, modify, and save workout plans, so that I can create and refine plans based on user feedback.

#### Acceptance Criteria

1. WHEN generate_workout_plan tool is defined, THE System SHALL use LangChain @tool decorator
2. WHEN generate_workout_plan is called, THE System SHALL accept frequency (int), location (str), duration_minutes (int), and equipment (list) as parameters
3. WHEN generate_workout_plan is called, THE System SHALL invoke WorkoutPlanGenerator service with user's fitness_level and primary_goal from context
4. WHEN generate_workout_plan succeeds, THE System SHALL return a dictionary representation of the WorkoutPlan
5. WHEN save_workout_plan tool is defined, THE System SHALL accept plan_data (dict) and user_approved (bool) as parameters
6. WHEN save_workout_plan is called with user_approved=False, THE System SHALL return an error message
7. WHEN save_workout_plan is called with user_approved=True, THE System SHALL save plan_data to agent_context["workout_planning"]
8. WHEN save_workout_plan saves data, THE System SHALL include user_approved=True and completed_at timestamp
9. WHEN modify_workout_plan tool is defined, THE System SHALL accept current_plan (dict) and modifications (dict) as parameters
10. WHEN modify_workout_plan is called, THE System SHALL invoke WorkoutPlanGenerator.modify_plan to apply requested changes
11. WHEN modify_workout_plan succeeds, THE System SHALL return the modified plan as a dictionary

### Requirement 4: Diet Planning Agent Implementation

**User Story:** As a user, I want to have a conversation about my dietary preferences and receive a personalized meal plan, so that I have nutritional guidance aligned with my fitness goals.

#### Acceptance Criteria

1. WHEN DietPlanningAgent is instantiated, THE System SHALL inherit from BaseOnboardingAgent with agent_type="diet_planning"
2. WHEN process_message is called, THE System SHALL access fitness_level, primary_goal, and workout_plan from agent_context
3. WHEN the agent asks about preferences, THE System SHALL inquire about dietary type (omnivore/vegetarian/vegan/pescatarian)
4. WHEN the agent asks about preferences, THE System SHALL inquire about food allergies and intolerances
5. WHEN the agent asks about preferences, THE System SHALL inquire about foods the user dislikes
6. WHEN the agent asks about preferences, THE System SHALL inquire about meal prep willingness and cooking skills
7. WHEN the agent asks about preferences, THE System SHALL inquire about preferred number of meals per day
8. WHEN sufficient preferences are collected, THE System SHALL call generate_meal_plan tool to create a plan
9. WHEN a plan is generated, THE System SHALL present it with calorie target, macro breakdown, and sample meals
10. WHEN the user approves the plan, THE System SHALL call save_meal_plan tool with user_approved=True
11. WHEN the plan is saved, THE System SHALL set step_complete=True and next_action="advance_step"

### Requirement 5: Meal Plan Generation Service

**User Story:** As a Diet Planning Agent, I want a service that generates realistic meal plans, so that I can propose nutritional strategies to users.

#### Acceptance Criteria

1. WHEN MealPlanGenerator.generate_plan is called, THE System SHALL accept fitness_level, primary_goal, workout_plan, diet_type, allergies, dislikes, and meal_frequency as parameters
2. WHEN primary_goal is "muscle_gain", THE System SHALL calculate calorie surplus (TDEE + 300-500 calories) and high protein macros (2.0-2.2g/kg)
3. WHEN primary_goal is "fat_loss", THE System SHALL calculate calorie deficit (TDEE - 300-500 calories) and moderate protein macros (1.8-2.0g/kg)
4. WHEN primary_goal is "general_fitness", THE System SHALL calculate maintenance calories (TDEE) and balanced macros
5. WHEN diet_type is "vegetarian", THE System SHALL exclude meat and fish from sample meals
6. WHEN diet_type is "vegan", THE System SHALL exclude all animal products from sample meals
7. WHEN allergies are provided, THE System SHALL exclude allergenic ingredients from sample meals
8. WHEN dislikes are provided, THE System SHALL avoid disliked foods in sample meals
9. WHEN meal_frequency is provided, THE System SHALL structure the plan with that number of meals per day
10. WHEN workout_plan indicates high training volume, THE System SHALL adjust calorie and carbohydrate targets upward
11. WHEN a plan is generated, THE System SHALL include daily calorie target, protein/carbs/fats in grams, meal timing suggestions, and 3-5 sample meal ideas
12. WHEN a plan is generated, THE System SHALL return a structured MealPlan object with all required fields

### Requirement 6: Diet Planning Agent Tools

**User Story:** As a Diet Planning Agent, I want tools to generate, modify, and save meal plans, so that I can create and refine plans based on user feedback.

#### Acceptance Criteria

1. WHEN generate_meal_plan tool is defined, THE System SHALL use LangChain @tool decorator
2. WHEN generate_meal_plan is called, THE System SHALL accept diet_type (str), allergies (list), dislikes (list), meal_frequency (int), and meal_prep_level (str) as parameters
3. WHEN generate_meal_plan is called, THE System SHALL invoke MealPlanGenerator service with user's fitness_level, primary_goal, and workout_plan from context
4. WHEN generate_meal_plan succeeds, THE System SHALL return a dictionary representation of the MealPlan
5. WHEN save_meal_plan tool is defined, THE System SHALL accept plan_data (dict) and user_approved (bool) as parameters
6. WHEN save_meal_plan is called with user_approved=False, THE System SHALL return an error message
7. WHEN save_meal_plan is called with user_approved=True, THE System SHALL save plan_data to agent_context["diet_planning"]
8. WHEN save_meal_plan saves data, THE System SHALL include user_approved=True and completed_at timestamp
9. WHEN modify_meal_plan tool is defined, THE System SHALL accept current_plan (dict) and modifications (dict) as parameters
10. WHEN modify_meal_plan is called, THE System SHALL invoke MealPlanGenerator.modify_plan to apply requested changes
11. WHEN modify_meal_plan succeeds, THE System SHALL return the modified plan as a dictionary

### Requirement 7: Approval Intent Detection

**User Story:** As an agent, I want to detect when the user approves a proposed plan from natural language, so that I can save the plan without requiring explicit commands.

#### Acceptance Criteria

1. WHEN the user says "yes", "looks good", "perfect", "I approve", or "let's do it", THE System SHALL interpret this as approval intent
2. WHEN the user says "sounds great", "that works", "I'm happy with this", or similar affirmative phrases, THE System SHALL interpret this as approval intent
3. WHEN approval intent is detected, THE System SHALL call the appropriate save tool with user_approved=True
4. WHEN the user provides feedback without clear approval, THE System SHALL not call the save tool
5. WHEN the user asks questions about the plan, THE System SHALL answer questions without interpreting as approval
6. WHEN approval intent is ambiguous, THE System SHALL ask for explicit confirmation before saving

### Requirement 8: Modification Request Detection and Handling

**User Story:** As a user, I want to request changes to a proposed plan conversationally, so that I can refine the plan to better fit my needs.

#### Acceptance Criteria

1. WHEN the user says "can we change...", "I'd prefer...", "what about...", or "could we do... instead", THE System SHALL interpret this as a modification request
2. WHEN a modification request is detected, THE System SHALL extract the requested changes from the user's message
3. WHEN modifications are extracted, THE System SHALL call the appropriate modify tool with the current plan and requested changes
4. WHEN a modified plan is generated, THE System SHALL present it to the user with explanation of what changed
5. WHEN the user approves the modified plan, THE System SHALL save it with user_approved=True
6. WHEN multiple modification iterations occur, THE System SHALL maintain conversation context and reference previous versions
7. WHEN modifications are not feasible, THE System SHALL explain why and suggest alternatives

### Requirement 9: Plan Presentation and Explanation

**User Story:** As a user, I want to understand why a plan was designed the way it was, so that I can make informed decisions about approval or modifications.

#### Acceptance Criteria

1. WHEN a workout plan is presented, THE System SHALL explain the training split and why it fits the user's goal
2. WHEN a workout plan is presented, THE System SHALL explain the frequency and why it's appropriate for the user's fitness level
3. WHEN a workout plan is presented, THE System SHALL highlight key exercises and their purpose
4. WHEN a workout plan is presented, THE System SHALL explain the progression strategy
5. WHEN a meal plan is presented, THE System SHALL explain the calorie target and how it aligns with the goal
6. WHEN a meal plan is presented, THE System SHALL explain the macro breakdown and why those ratios were chosen
7. WHEN a meal plan is presented, THE System SHALL provide 3-5 sample meal ideas that fit the plan
8. WHEN a meal plan is presented, THE System SHALL explain meal timing relative to workouts if relevant
9. WHEN any plan is presented, THE System SHALL invite questions and feedback before asking for approval

### Requirement 10: Workout Planning Agent System Prompt

**User Story:** As a Workout Planning Agent, I want a clear system prompt with context from previous steps, so that I generate appropriate workout plans and handle the approval workflow correctly.

#### Acceptance Criteria

1. WHEN get_system_prompt is called, THE System SHALL return a prompt including fitness_level and primary_goal from agent_context
2. WHEN the prompt is used, THE System SHALL instruct the agent to ask about workout preferences before generating a plan
3. WHEN the prompt is used, THE System SHALL instruct the agent to call generate_workout_plan after collecting preferences
4. WHEN the prompt is used, THE System SHALL instruct the agent to present the plan with clear explanation
5. WHEN the prompt is used, THE System SHALL instruct the agent to detect approval intent from user responses
6. WHEN the prompt is used, THE System SHALL instruct the agent to call save_workout_plan ONLY when user explicitly approves
7. WHEN the prompt is used, THE System SHALL instruct the agent to call modify_workout_plan when user requests changes
8. WHEN the prompt is used, THE System SHALL instruct the agent to explain plan rationale to help user decide

### Requirement 11: Diet Planning Agent System Prompt

**User Story:** As a Diet Planning Agent, I want a clear system prompt with context from previous steps, so that I generate appropriate meal plans and handle the approval workflow correctly.

#### Acceptance Criteria

1. WHEN get_system_prompt is called, THE System SHALL return a prompt including fitness_level, primary_goal, and workout_plan summary from agent_context
2. WHEN the prompt is used, THE System SHALL instruct the agent to ask about dietary preferences before generating a plan
3. WHEN the prompt is used, THE System SHALL instruct the agent to call generate_meal_plan after collecting preferences
4. WHEN the prompt is used, THE System SHALL instruct the agent to present the plan with calorie/macro explanation
5. WHEN the prompt is used, THE System SHALL instruct the agent to detect approval intent from user responses
6. WHEN the prompt is used, THE System SHALL instruct the agent to call save_meal_plan ONLY when user explicitly approves
7. WHEN the prompt is used, THE System SHALL instruct the agent to call modify_meal_plan when user requests changes
8. WHEN the prompt is used, THE System SHALL instruct the agent to respect dietary restrictions strictly

### Requirement 12: Context Flow from Previous Agents

**User Story:** As a planning agent, I want to access data collected by previous agents, so that I can generate plans tailored to the user's complete profile.

#### Acceptance Criteria

1. WHEN WorkoutPlanningAgent is instantiated, THE System SHALL receive agent_context containing fitness_assessment and goal_setting data
2. WHEN WorkoutPlanningAgent generates a plan, THE System SHALL use fitness_level from agent_context["fitness_assessment"]["fitness_level"]
3. WHEN WorkoutPlanningAgent generates a plan, THE System SHALL use primary_goal from agent_context["goal_setting"]["primary_goal"]
4. WHEN WorkoutPlanningAgent generates a plan, THE System SHALL consider limitations from agent_context["fitness_assessment"]["limitations"]
5. WHEN DietPlanningAgent is instantiated, THE System SHALL receive agent_context containing fitness_assessment, goal_setting, and workout_planning data
6. WHEN DietPlanningAgent generates a plan, THE System SHALL use workout_plan from agent_context["workout_planning"]["proposed_plan"]
7. WHEN DietPlanningAgent generates a plan, THE System SHALL adjust calories based on workout frequency and intensity

### Requirement 13: Plan Data Structure and Validation

**User Story:** As a system, I want structured, validated plan data, so that subsequent systems can reliably use the plans.

#### Acceptance Criteria

1. WHEN a WorkoutPlan is created, THE System SHALL include fields: frequency, duration_minutes, training_split, exercises, progression_strategy
2. WHEN a WorkoutPlan is created, THE System SHALL validate frequency is between 2 and 7 days per week
3. WHEN a WorkoutPlan is created, THE System SHALL validate duration_minutes is between 20 and 180 minutes
4. WHEN a WorkoutPlan exercises list is created, THE System SHALL include exercise_name, sets, reps, rest_seconds, and notes for each exercise
5. WHEN a MealPlan is created, THE System SHALL include fields: daily_calories, protein_g, carbs_g, fats_g, meal_frequency, sample_meals
6. WHEN a MealPlan is created, THE System SHALL validate daily_calories is between 1200 and 5000
7. WHEN a MealPlan is created, THE System SHALL validate protein_g + carbs_g + fats_g approximately equals daily_calories (within 10%)
8. WHEN a MealPlan is created, THE System SHALL validate meal_frequency is between 2 and 6 meals per day
9. WHEN sample_meals are included, THE System SHALL provide at least 3 meal examples with ingredients and approximate macros

### Requirement 14: Error Handling for Plan Generation

**User Story:** As a user, I want clear feedback when plan generation fails, so that I understand what went wrong and can provide corrected information.

#### Acceptance Criteria

1. WHEN generate_workout_plan fails due to invalid parameters, THE System SHALL return an error message describing the validation issue
2. WHEN generate_meal_plan fails due to conflicting constraints, THE System SHALL return an error message explaining the conflict
3. WHEN a plan generation service raises an exception, THE System SHALL log the error and return a user-friendly message
4. WHEN a save tool is called before a plan is generated, THE System SHALL return an error message indicating no plan exists to save
5. WHEN a modify tool is called with invalid modifications, THE System SHALL return an error message describing what's invalid
6. WHEN any tool fails, THE System SHALL allow the agent to retry with corrected parameters

### Requirement 15: Conversational Flow for Plan Approval

**User Story:** As a user, I want a natural conversation flow when reviewing plans, so that the approval process feels collaborative rather than transactional.

#### Acceptance Criteria

1. WHEN preferences are collected, THE System SHALL summarize them before generating the plan
2. WHEN a plan is generated, THE System SHALL present it in a clear, readable format
3. WHEN a plan is presented, THE System SHALL explain the reasoning behind key decisions
4. WHEN a plan is presented, THE System SHALL explicitly ask if the user approves or wants changes
5. WHEN the user asks questions about the plan, THE System SHALL answer before asking for approval again
6. WHEN the user requests modifications, THE System SHALL acknowledge the request and generate a modified plan
7. WHEN a modified plan is presented, THE System SHALL highlight what changed from the previous version
8. WHEN the user approves, THE System SHALL confirm the plan is saved and preview the next step

### Requirement 16: Testing Coverage

**User Story:** As a developer, I want comprehensive tests for planning agents and services, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. WHEN unit tests are run for WorkoutPlanGenerator, THE System SHALL verify plans are generated correctly for all fitness levels and goals
2. WHEN unit tests are run for MealPlanGenerator, THE System SHALL verify calorie and macro calculations are accurate
3. WHEN unit tests are run for WorkoutPlanningAgent, THE System SHALL verify approval detection works correctly
4. WHEN unit tests are run for DietPlanningAgent, THE System SHALL verify modification requests are handled correctly
5. WHEN integration tests are run, THE System SHALL verify complete flow from preference collection through plan approval
6. WHEN property tests are run, THE System SHALL verify plan validation for all parameter combinations
7. WHEN property tests are run, THE System SHALL verify macro calculations always sum to approximately daily calories
8. WHEN tests are run, THE System SHALL achieve minimum 80% code coverage for new agent and service code
9. WHEN end-to-end tests are run, THE System SHALL verify context flows correctly from Fitness Assessment through Diet Planning
10. WHEN approval detection tests are run, THE System SHALL verify >95% accuracy on a test set of approval and non-approval phrases
