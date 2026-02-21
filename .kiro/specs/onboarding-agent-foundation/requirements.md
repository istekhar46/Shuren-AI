# Requirements Document

## Introduction

The Onboarding Agent Foundation establishes the core infrastructure for a conversational onboarding system where specialized AI agents guide users through each onboarding step. This foundation provides the database schema, base agent architecture, orchestration service, and API endpoints that subsequent agent implementations will build upon. This is the first of four specifications that will transform the current form-based onboarding into an intelligent, conversational experience.

## Glossary

- **Onboarding_Agent**: An AI agent specialized for a specific onboarding step (e.g., Fitness Assessment, Goal Setting)
- **Agent_Orchestrator**: Service that routes user messages to the appropriate onboarding agent based on current step
- **Agent_Context**: JSONB data structure containing information collected by previous agents
- **Conversation_History**: JSONB array storing chat messages between user and agents
- **Base_Agent**: Abstract class defining the interface all onboarding agents must implement
- **Agent_Response**: Structured response from an agent containing message, completion status, and next action
- **LLM**: Large Language Model (Anthropic Claude Sonnet 4) used by agents for natural language processing
- **OnboardingState**: Database entity tracking user's progress through onboarding steps

## Requirements

### Requirement 1: Database Schema Enhancement

**User Story:** As a system, I want to track which agent is handling each onboarding step and store agent context, so that agents can access previous conversation data and maintain continuity.

#### Acceptance Criteria

1. WHEN the OnboardingState model is updated, THE System SHALL add a `current_agent` field of type String with nullable=True
2. WHEN the OnboardingState model is updated, THE System SHALL add an `agent_context` field of type JSONB with default={}
3. WHEN the OnboardingState model is updated, THE System SHALL add a `conversation_history` field of type JSONB with default=[]
4. WHEN a database migration is created, THE System SHALL generate an Alembic migration script that adds these three fields
5. WHEN the migration is applied to existing data, THE System SHALL preserve all existing onboarding_states records without data loss
6. WHEN querying OnboardingState, THE System SHALL return the new fields with their default values for existing records

### Requirement 2: Base Agent Architecture

**User Story:** As a developer, I want a base agent class that defines the interface for all onboarding agents, so that agents have consistent behavior and can be easily extended.

#### Acceptance Criteria

1. WHEN BaseOnboardingAgent is instantiated, THE System SHALL accept db (AsyncSession) and context (dict) as constructor parameters
2. WHEN a subclass is created, THE System SHALL require implementation of `process_message(message: str, user_id: UUID) -> AgentResponse` method
3. WHEN a subclass is created, THE System SHALL require implementation of `get_tools() -> List` method
4. WHEN a subclass is created, THE System SHALL require implementation of `get_system_prompt() -> str` method
5. WHEN `save_context` is called, THE System SHALL update the agent_context field in OnboardingState for the given user_id
6. WHEN `_init_llm` is called, THE System SHALL initialize and return a ChatAnthropic instance with model="claude-sonnet-4-5-20250929"
7. WHEN BaseOnboardingAgent is instantiated directly, THE System SHALL raise TypeError due to abstract methods

### Requirement 3: Agent Response Schema

**User Story:** As a system, I want a standardized response format from agents, so that the API can consistently communicate agent outputs to clients.

#### Acceptance Criteria

1. WHEN AgentResponse is created, THE System SHALL include a `message` field of type string containing the agent's response text
2. WHEN AgentResponse is created, THE System SHALL include an `agent_type` field of type string identifying which agent generated the response
3. WHEN AgentResponse is created, THE System SHALL include a `step_complete` field of type boolean indicating if the current step is finished
4. WHEN AgentResponse is created, THE System SHALL include a `next_action` field of type string indicating what should happen next
5. WHEN AgentResponse is serialized, THE System SHALL produce valid JSON matching the Pydantic schema
6. WHEN AgentResponse includes optional fields, THE System SHALL handle None values gracefully

### Requirement 4: Agent Type Enumeration

**User Story:** As a system, I want to define all onboarding agent types, so that the orchestrator can route to the correct agent implementation.

#### Acceptance Criteria

1. WHEN OnboardingAgentType enum is defined, THE System SHALL include FITNESS_ASSESSMENT with value "fitness_assessment"
2. WHEN OnboardingAgentType enum is defined, THE System SHALL include GOAL_SETTING with value "goal_setting"
3. WHEN OnboardingAgentType enum is defined, THE System SHALL include WORKOUT_PLANNING with value "workout_planning"
4. WHEN OnboardingAgentType enum is defined, THE System SHALL include DIET_PLANNING with value "diet_planning"
5. WHEN OnboardingAgentType enum is defined, THE System SHALL include SCHEDULING with value "scheduling"
6. WHEN an invalid agent type string is used, THE System SHALL raise a validation error

### Requirement 5: Onboarding Agent Orchestrator

**User Story:** As a system, I want an orchestrator service that routes messages to the appropriate agent, so that users interact with the correct specialist for their current onboarding step.

#### Acceptance Criteria

1. WHEN `get_current_agent` is called with a user_id, THE System SHALL load the OnboardingState for that user
2. WHEN the current step is 0-2, THE System SHALL map to OnboardingAgentType.FITNESS_ASSESSMENT
3. WHEN the current step is 3, THE System SHALL map to OnboardingAgentType.GOAL_SETTING
4. WHEN the current step is 4-5, THE System SHALL map to OnboardingAgentType.WORKOUT_PLANNING
5. WHEN the current step is 6-7, THE System SHALL map to OnboardingAgentType.DIET_PLANNING
6. WHEN the current step is 8-9, THE System SHALL map to OnboardingAgentType.SCHEDULING
7. WHEN the current step is invalid (>9 or <0), THE System SHALL raise ValueError
8. WHEN `_create_agent` is called, THE System SHALL instantiate the correct agent class with db and context parameters
9. WHEN agent_context is loaded, THE System SHALL pass it to the agent constructor for context continuity

### Requirement 6: Chat API Endpoint

**User Story:** As a user, I want to send messages to the onboarding agent, so that I can have a conversational onboarding experience.

#### Acceptance Criteria

1. WHEN POST /api/v1/onboarding/chat is called, THE System SHALL require authentication via JWT token
2. WHEN the request body is received, THE System SHALL validate it against OnboardingChatRequest schema
3. WHEN the request is valid, THE System SHALL route the message to the current agent via the orchestrator
4. WHEN the agent processes the message, THE System SHALL return an OnboardingChatResponse with the agent's reply
5. WHEN the user is not authenticated, THE System SHALL return HTTP 401 Unauthorized
6. WHEN the request body is invalid, THE System SHALL return HTTP 422 Unprocessable Entity with validation errors
7. WHEN a database error occurs, THE System SHALL return HTTP 500 Internal Server Error
8. WHEN the endpoint is called, THE System SHALL append the message to conversation_history in OnboardingState

### Requirement 7: Current Agent Info API Endpoint

**User Story:** As a client application, I want to retrieve information about the current onboarding agent, so that I can display appropriate UI and context to the user.

#### Acceptance Criteria

1. WHEN GET /api/v1/onboarding/current-agent is called, THE System SHALL require authentication via JWT token
2. WHEN the request is authenticated, THE System SHALL load the user's OnboardingState
3. WHEN the OnboardingState is loaded, THE System SHALL determine the current agent type based on current_step
4. WHEN the agent type is determined, THE System SHALL return CurrentAgentResponse with agent_type, current_step, and context_summary
5. WHEN the user has no OnboardingState, THE System SHALL return HTTP 404 Not Found
6. WHEN the user is not authenticated, THE System SHALL return HTTP 401 Unauthorized

### Requirement 8: Request and Response Schemas

**User Story:** As a developer, I want Pydantic schemas for API requests and responses, so that data validation is automatic and type-safe.

#### Acceptance Criteria

1. WHEN OnboardingChatRequest is defined, THE System SHALL include `message` field of type string with min_length=1
2. WHEN OnboardingChatRequest is defined, THE System SHALL include optional `step` field of type integer
3. WHEN OnboardingChatResponse is defined, THE System SHALL include all fields from AgentResponse
4. WHEN OnboardingChatResponse is defined, THE System SHALL include `current_step` field of type integer
5. WHEN CurrentAgentResponse is defined, THE System SHALL include `agent_type`, `current_step`, `agent_description`, and `context_summary` fields
6. WHEN any schema receives invalid data, THE System SHALL raise Pydantic ValidationError

### Requirement 9: Backward Compatibility

**User Story:** As a system administrator, I want the new agent foundation to coexist with the existing onboarding flow, so that we can deploy incrementally without breaking existing functionality.

#### Acceptance Criteria

1. WHEN the database migration is applied, THE System SHALL not modify existing step_data or is_complete fields
2. WHEN the existing OnboardingService is used, THE System SHALL continue to function without errors
3. WHEN existing API endpoints are called, THE System SHALL return responses in the same format as before
4. WHEN new fields are null or empty, THE System SHALL not affect existing onboarding logic
5. WHEN both old and new systems access OnboardingState, THE System SHALL prevent data corruption through proper transaction handling

### Requirement 10: LLM Integration

**User Story:** As an agent, I want to use a language model for natural language understanding, so that I can process user messages conversationally.

#### Acceptance Criteria

1. WHEN `_init_llm` is called, THE System SHALL initialize ChatAnthropic with the Anthropic API key from environment configuration
2. WHEN the LLM is initialized, THE System SHALL set temperature=0.7 for balanced creativity and consistency
3. WHEN the LLM is initialized, THE System SHALL set max_tokens=2048 for adequate response length
4. WHEN the LLM is initialized, THE System SHALL use model="claude-sonnet-4-5-20250929"
5. WHEN the API key is missing or invalid, THE System SHALL raise a configuration error with a descriptive message
6. WHEN the LLM is called, THE System SHALL handle rate limiting and API errors gracefully

### Requirement 11: Error Handling

**User Story:** As a user, I want clear error messages when something goes wrong, so that I understand what happened and can take corrective action.

#### Acceptance Criteria

1. WHEN an agent raises an exception, THE System SHALL catch it and return HTTP 500 with a generic error message
2. WHEN validation fails, THE System SHALL return HTTP 422 with specific field errors
3. WHEN a user_id is not found, THE System SHALL return HTTP 404 with a "User not found" message
4. WHEN the database is unavailable, THE System SHALL return HTTP 503 Service Unavailable
5. WHEN the LLM API fails, THE System SHALL log the error and return a user-friendly message
6. WHEN an invalid step number is provided, THE System SHALL return HTTP 400 Bad Request

### Requirement 12: Specialized Agent System Prompts

**User Story:** As a developer, I want each specialized agent to have a hardcoded system prompt, so that agents have consistent behavior and clear role definitions without requiring dynamic prompt generation.

#### Acceptance Criteria

1. WHEN FitnessAssessmentAgent is created, THE System SHALL use a hardcoded system prompt describing its role in assessing fitness level
2. WHEN GoalSettingAgent is created, THE System SHALL use a hardcoded system prompt describing its role in defining fitness goals
3. WHEN WorkoutPlanningAgent is created, THE System SHALL use a hardcoded system prompt describing its role in creating workout plans
4. WHEN DietPlanningAgent is created, THE System SHALL use a hardcoded system prompt describing its role in creating meal plans
5. WHEN SchedulingAgent is created, THE System SHALL use a hardcoded system prompt describing its role in setting schedules
6. WHEN `get_system_prompt` is called on any specialized agent, THE System SHALL return the agent's hardcoded prompt string
7. WHEN system prompts are defined, THE System SHALL include guidelines for conversational tone, non-medical disclaimers, and role boundaries

### Requirement 13: Testing Infrastructure

**User Story:** As a developer, I want comprehensive tests for the agent foundation, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. WHEN BaseOnboardingAgent tests are run, THE System SHALL verify that abstract methods cannot be called directly
2. WHEN BaseOnboardingAgent tests are run, THE System SHALL verify that save_context updates the database correctly
3. WHEN OnboardingAgentOrchestrator tests are run, THE System SHALL verify correct agent routing for all step ranges
4. WHEN API endpoint tests are run, THE System SHALL verify authentication, validation, and response formats
5. WHEN database migration tests are run, THE System SHALL verify that new fields are added without data loss
6. WHEN integration tests are run, THE System SHALL verify end-to-end message flow from API to agent and back
7. WHEN all tests are run, THE System SHALL achieve minimum 80% code coverage for new code
