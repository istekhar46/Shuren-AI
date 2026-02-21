# Requirements Document

## Introduction

The Fitness and Goal Setting Agents feature implements the first two specialized onboarding agents that handle fitness assessment (Steps 1-2) and goal setting (Step 3). These agents provide conversational, personalized guidance to understand the user's current fitness level, experience, limitations, and fitness objectives. This is the second of four specifications building on the Onboarding Agent Foundation to create a complete conversational onboarding system.

## Glossary

- **Fitness_Assessment_Agent**: AI agent specialized in assessing user's current fitness level and exercise experience
- **Goal_Setting_Agent**: AI agent specialized in defining user's fitness goals and setting realistic expectations
- **Agent_Tool**: LangChain function decorated with @tool that agents can call to perform actions
- **Fitness_Level**: User's current fitness classification (beginner/intermediate/advanced)
- **Primary_Goal**: User's main fitness objective (fat_loss/muscle_gain/general_fitness)
- **Physical_Limitation**: Non-medical constraint such as equipment availability or injury history
- **Completion_Intent**: Natural language signal from user indicating they're done with current step
- **Context_Handover**: Process of passing collected data from one agent to the next agent

## Requirements

### Requirement 1: Fitness Assessment Agent Implementation

**User Story:** As a user, I want to have a conversation about my fitness level and experience, so that the system understands my starting point and can provide appropriate guidance.

#### Acceptance Criteria

1. WHEN FitnessAssessmentAgent is instantiated, THE System SHALL inherit from BaseOnboardingAgent with agent_type="fitness_assessment"
2. WHEN process_message is called, THE System SHALL use LangChain to create a tool-calling agent with the LLM and agent tools
3. WHEN the agent processes a message, THE System SHALL use the system prompt to guide conversation about fitness level and experience
4. WHEN the agent detects sufficient information has been collected, THE System SHALL set step_complete=True in the response
5. WHEN the agent completes assessment, THE System SHALL set next_action="advance_step" to trigger progression to Goal Setting Agent
6. WHEN the agent responds, THE System SHALL maintain a conversational, encouraging, and non-judgmental tone
7. WHEN medical topics are mentioned, THE System SHALL avoid providing medical advice and redirect to fitness-related questions

### Requirement 2: Fitness Assessment Data Collection

**User Story:** As a system, I want to collect structured fitness assessment data from conversational input, so that subsequent agents can use this information to personalize plans.

#### Acceptance Criteria

1. WHEN the agent asks about fitness level, THE System SHALL accept responses indicating beginner, intermediate, or advanced levels
2. WHEN the agent asks about exercise experience, THE System SHALL collect information about workout frequency, duration, and types of exercises
3. WHEN the agent asks about limitations, THE System SHALL collect non-medical constraints such as equipment availability and injury history
4. WHEN the user provides fitness information, THE System SHALL extract structured data from natural language responses
5. WHEN fitness level is ambiguous, THE System SHALL ask clarifying questions to determine the appropriate classification
6. WHEN the user mentions medical conditions, THE System SHALL acknowledge but not provide medical guidance

### Requirement 3: Fitness Assessment Tool - save_fitness_assessment

**User Story:** As a Fitness Assessment Agent, I want to save collected fitness data to agent context, so that subsequent agents can access this information.

#### Acceptance Criteria

1. WHEN save_fitness_assessment tool is defined, THE System SHALL use LangChain @tool decorator
2. WHEN the tool is called, THE System SHALL accept parameters: fitness_level (str), experience_details (dict), and limitations (list)
3. WHEN fitness_level is provided, THE System SHALL validate it is one of: "beginner", "intermediate", "advanced"
4. WHEN the tool is called, THE System SHALL save data to agent_context["fitness_assessment"] in OnboardingState
5. WHEN the tool saves data, THE System SHALL include a completed_at timestamp in ISO 8601 format
6. WHEN the tool completes successfully, THE System SHALL return a success status message
7. WHEN validation fails, THE System SHALL return an error message without saving data

### Requirement 4: Goal Setting Agent Implementation

**User Story:** As a user, I want to have a conversation about my fitness goals, so that the system understands what I want to achieve and can create appropriate plans.

#### Acceptance Criteria

1. WHEN GoalSettingAgent is instantiated, THE System SHALL inherit from BaseOnboardingAgent with agent_type="goal_setting"
2. WHEN process_message is called, THE System SHALL access fitness_level from agent_context["fitness_assessment"]
3. WHEN the agent generates responses, THE System SHALL reference the user's fitness level to set realistic expectations
4. WHEN the agent processes a message, THE System SHALL use LangChain to create a tool-calling agent with the LLM and agent tools
5. WHEN the agent detects goal information is complete, THE System SHALL set step_complete=True in the response
6. WHEN the agent completes goal setting, THE System SHALL set next_action="advance_step" to trigger progression to Workout Planning Agent
7. WHEN the agent responds, THE System SHALL explain how goals align with the user's fitness level

### Requirement 5: Goal Setting Data Collection

**User Story:** As a system, I want to collect structured goal data from conversational input, so that workout and meal plans can be tailored to user objectives.

#### Acceptance Criteria

1. WHEN the agent asks about primary goal, THE System SHALL accept responses indicating fat_loss, muscle_gain, or general_fitness
2. WHEN the agent asks about secondary goals, THE System SHALL allow users to specify additional objectives or indicate none
3. WHEN the agent asks about target metrics, THE System SHALL collect optional target weight in kilograms
4. WHEN the agent asks about target metrics, THE System SHALL collect optional target body fat percentage
5. WHEN goal information is ambiguous, THE System SHALL ask clarifying questions to understand user intent
6. WHEN multiple conflicting goals are mentioned, THE System SHALL help the user prioritize and select a primary goal

### Requirement 6: Goal Setting Tool - save_fitness_goals

**User Story:** As a Goal Setting Agent, I want to save collected goal data to agent context, so that subsequent agents can create plans aligned with user objectives.

#### Acceptance Criteria

1. WHEN save_fitness_goals tool is defined, THE System SHALL use LangChain @tool decorator
2. WHEN the tool is called, THE System SHALL accept parameters: primary_goal (str), secondary_goal (str | None), target_weight_kg (float | None), target_body_fat_percentage (float | None)
3. WHEN primary_goal is provided, THE System SHALL validate it is one of: "fat_loss", "muscle_gain", "general_fitness"
4. WHEN the tool is called, THE System SHALL save data to agent_context["goal_setting"] in OnboardingState
5. WHEN the tool saves data, THE System SHALL include a completed_at timestamp in ISO 8601 format
6. WHEN the tool completes successfully, THE System SHALL return a success status message
7. WHEN validation fails, THE System SHALL return an error message without saving data

### Requirement 7: Context Handover from Fitness Assessment to Goal Setting

**User Story:** As a Goal Setting Agent, I want to access fitness assessment data, so that I can provide goal recommendations appropriate for the user's fitness level.

#### Acceptance Criteria

1. WHEN GoalSettingAgent is instantiated, THE System SHALL receive agent_context containing fitness_assessment data
2. WHEN the agent generates its system prompt, THE System SHALL include fitness_level from the fitness_assessment context
3. WHEN the agent generates its system prompt, THE System SHALL include limitations from the fitness_assessment context
4. WHEN fitness_assessment data is missing, THE System SHALL handle gracefully with default values or request re-assessment
5. WHEN the agent references fitness level in responses, THE System SHALL use the value from agent_context["fitness_assessment"]["fitness_level"]

### Requirement 8: Completion Intent Detection

**User Story:** As an agent, I want to detect when the user has provided sufficient information and is ready to move forward, so that I can complete the current step without requiring explicit commands.

#### Acceptance Criteria

1. WHEN the user says phrases like "that's all", "I'm done", "let's move on", or "next", THE System SHALL interpret this as completion intent
2. WHEN the user confirms information is correct, THE System SHALL interpret this as completion intent
3. WHEN the agent has collected all required information and user confirms, THE System SHALL call the appropriate save tool
4. WHEN the save tool succeeds, THE System SHALL set step_complete=True in the agent response
5. WHEN the save tool succeeds, THE System SHALL set next_action="advance_step" in the agent response
6. WHEN completion intent is detected but required information is missing, THE System SHALL ask for the missing information before completing

### Requirement 9: Fitness Assessment Agent System Prompt

**User Story:** As a Fitness Assessment Agent, I want a clear system prompt defining my role and behavior, so that I provide consistent, appropriate guidance to users.

#### Acceptance Criteria

1. WHEN get_system_prompt is called, THE System SHALL return a hardcoded prompt describing the agent's role in fitness assessment
2. WHEN the prompt is used, THE System SHALL instruct the agent to ask about current fitness level
3. WHEN the prompt is used, THE System SHALL instruct the agent to inquire about exercise experience and frequency
4. WHEN the prompt is used, THE System SHALL instruct the agent to identify physical limitations (non-medical)
5. WHEN the prompt is used, THE System SHALL instruct the agent to be encouraging and non-judgmental
6. WHEN the prompt is used, THE System SHALL instruct the agent to avoid medical advice
7. WHEN the prompt is used, THE System SHALL instruct the agent to call save_fitness_assessment when user confirms information

### Requirement 10: Goal Setting Agent System Prompt

**User Story:** As a Goal Setting Agent, I want a clear system prompt with context from previous steps, so that I provide goal recommendations appropriate for the user's fitness level.

#### Acceptance Criteria

1. WHEN get_system_prompt is called, THE System SHALL return a prompt including fitness_level from agent_context
2. WHEN the prompt is used, THE System SHALL instruct the agent to understand primary fitness goal
3. WHEN the prompt is used, THE System SHALL instruct the agent to identify secondary goals if any
4. WHEN the prompt is used, THE System SHALL instruct the agent to set realistic expectations based on fitness level
5. WHEN the prompt is used, THE System SHALL instruct the agent to explain how goals align with fitness level
6. WHEN the prompt is used, THE System SHALL instruct the agent to call save_fitness_goals when user confirms goals
7. WHEN the prompt is used, THE System SHALL include limitations from fitness_assessment context

### Requirement 11: Agent Tool Error Handling

**User Story:** As a system, I want agent tools to handle errors gracefully, so that users receive helpful feedback when something goes wrong.

#### Acceptance Criteria

1. WHEN a tool receives invalid parameters, THE System SHALL return an error message describing the validation failure
2. WHEN a database error occurs during tool execution, THE System SHALL log the error and return a user-friendly message
3. WHEN a tool fails, THE System SHALL not update agent_context with partial or invalid data
4. WHEN a tool returns an error, THE System SHALL allow the agent to retry with corrected parameters
5. WHEN a tool succeeds, THE System SHALL commit the database transaction before returning success

### Requirement 12: Conversational Flow Quality

**User Story:** As a user, I want natural, flowing conversations with agents, so that onboarding feels like talking to a knowledgeable coach rather than filling out a form.

#### Acceptance Criteria

1. WHEN the agent asks questions, THE System SHALL ask one or two questions at a time, not overwhelming the user
2. WHEN the user provides information, THE System SHALL acknowledge it before asking the next question
3. WHEN the user provides vague responses, THE System SHALL ask clarifying questions in a friendly manner
4. WHEN the agent transitions to the next step, THE System SHALL explain what comes next
5. WHEN the user seems confused, THE System SHALL provide examples or explanations to help them understand
6. WHEN the agent completes a step, THE System SHALL summarize what was collected before moving forward

### Requirement 13: Data Validation and Sanitization

**User Story:** As a system, I want to validate and sanitize user input before saving, so that agent_context contains clean, structured data.

#### Acceptance Criteria

1. WHEN fitness_level is saved, THE System SHALL normalize it to lowercase before storage
2. WHEN target_weight_kg is provided, THE System SHALL validate it is a positive number between 30 and 300
3. WHEN target_body_fat_percentage is provided, THE System SHALL validate it is a number between 3 and 50
4. WHEN limitations are saved, THE System SHALL store them as a list of strings
5. WHEN experience_details are saved, THE System SHALL store them as a dictionary with consistent keys
6. WHEN any string field is saved, THE System SHALL trim whitespace and handle empty strings appropriately

### Requirement 14: Step Advancement Integration

**User Story:** As a system, I want to automatically advance the onboarding step when an agent completes, so that the next agent becomes active without manual intervention.

#### Acceptance Criteria

1. WHEN Fitness Assessment Agent sets step_complete=True, THE System SHALL increment current_step in OnboardingState
2. WHEN Goal Setting Agent sets step_complete=True, THE System SHALL increment current_step in OnboardingState
3. WHEN current_step is incremented, THE System SHALL update current_agent to reflect the new agent type
4. WHEN step advancement occurs, THE System SHALL commit the database transaction
5. WHEN the next message is received, THE System SHALL route to the new agent based on updated current_step

### Requirement 15: Testing Coverage

**User Story:** As a developer, I want comprehensive tests for both agents, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. WHEN unit tests are run for FitnessAssessmentAgent, THE System SHALL verify process_message returns valid AgentResponse
2. WHEN unit tests are run for GoalSettingAgent, THE System SHALL verify context from fitness_assessment is accessible
3. WHEN integration tests are run, THE System SHALL verify complete flow from Fitness Assessment through Goal Setting
4. WHEN property tests are run, THE System SHALL verify data validation for all tool parameters
5. WHEN tests are run, THE System SHALL achieve minimum 80% code coverage for new agent code
6. WHEN tool tests are run, THE System SHALL verify save operations update database correctly
7. WHEN error handling tests are run, THE System SHALL verify graceful handling of invalid inputs and database errors
