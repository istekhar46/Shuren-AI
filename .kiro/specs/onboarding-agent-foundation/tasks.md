# Implementation Plan: Onboarding Agent Foundation

## Overview

This implementation plan breaks down the Onboarding Agent Foundation into discrete, incremental coding tasks. Each task builds on previous work, with testing integrated throughout to catch errors early. The plan follows a bottom-up approach: database → models → base classes → orchestrator → API → integration.

## Tasks

- [x] 1. Database schema migration
  - Create Alembic migration script to add three new fields to onboarding_states table
  - Add `current_agent` column (String, nullable)
  - Add `agent_context` column (JSONB, default={})
  - Add `conversation_history` column (JSONB, default=[])
  - Test migration on clean database and database with existing records
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [ ]* 1.1 Write property test for migration data preservation
  - **Property 1: Database Migration Preserves Existing Data**
  - **Validates: Requirements 1.5, 1.6**

- [x] 2. Update OnboardingState model
  - Add `current_agent: str | None` field to model class
  - Add `agent_context: dict` field with JSONB type
  - Add `conversation_history: list` field with JSONB type
  - Ensure backward compatibility with existing code
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 3. Create agent type enumeration and response schemas
  - [x] 3.1 Create OnboardingAgentType enum in `app/schemas/onboarding.py`
    - Define five agent types: FITNESS_ASSESSMENT, GOAL_SETTING, WORKOUT_PLANNING, DIET_PLANNING, SCHEDULING
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 3.2 Create AgentResponse schema in `app/schemas/onboarding.py`
    - Define fields: message, agent_type, step_complete, next_action, context_update
    - Add field validators and examples
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ]* 3.3 Write property tests for AgentResponse schema
    - **Property 5: AgentResponse Schema Completeness**
    - **Property 6: AgentResponse Serialization Round-Trip**
    - **Property 7: Optional Fields Handle None Values**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

- [x] 4. Implement BaseOnboardingAgent abstract class
  - [x] 4.1 Create `app/agents/onboarding/base.py` with BaseOnboardingAgent class
    - Implement `__init__(db: AsyncSession, context: dict)` constructor
    - Implement `_init_llm()` method returning ChatAnthropic instance
    - Define abstract methods: process_message, get_tools, get_system_prompt
    - Implement `save_context(user_id, agent_data)` method
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 10.1, 10.2, 10.3, 10.4_
  
  - [x] 4.2 Write unit tests for BaseOnboardingAgent
    - Test that abstract class cannot be instantiated directly
    - Test that _init_llm returns correct ChatAnthropic configuration
    - Test save_context updates database correctly
    - _Requirements: 2.7, 2.6, 2.5_
  
  - [ ]* 4.3 Write property tests for BaseOnboardingAgent
    - **Property 3: Abstract Methods Must Be Implemented**
    - **Property 4: Save Context Updates Database**
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.7**

- [x] 5. Create stub implementations for specialized agents
  - [x] 5.1 Create FitnessAssessmentAgent stub in `app/agents/onboarding/fitness_assessment.py`
    - Extend BaseOnboardingAgent
    - Implement abstract methods with placeholder responses
    - Define hardcoded system prompt for fitness assessment role
    - _Requirements: 2.2, 2.3, 2.4, 12.1_
  
  - [x] 5.2 Create GoalSettingAgent stub in `app/agents/onboarding/goal_setting.py`
    - Extend BaseOnboardingAgent
    - Implement abstract methods with placeholder responses
    - Define hardcoded system prompt for goal setting role
    - _Requirements: 2.2, 2.3, 2.4, 12.2_
  
  - [x] 5.3 Create WorkoutPlanningAgent stub in `app/agents/onboarding/workout_planning.py`
    - Extend BaseOnboardingAgent
    - Implement abstract methods with placeholder responses
    - Define hardcoded system prompt for workout planning role
    - _Requirements: 2.2, 2.3, 2.4, 12.3_
  
  - [x] 5.4 Create DietPlanningAgent stub in `app/agents/onboarding/diet_planning.py`
    - Extend BaseOnboardingAgent
    - Implement abstract methods with placeholder responses
    - Define hardcoded system prompt for diet planning role
    - _Requirements: 2.2, 2.3, 2.4, 12.4_
  
  - [x] 5.5 Create SchedulingAgent stub in `app/agents/onboarding/scheduling.py`
    - Extend BaseOnboardingAgent
    - Implement abstract methods with placeholder responses
    - Define hardcoded system prompt for scheduling role
    - _Requirements: 2.2, 2.3, 2.4, 12.5_

- [x] 6. Implement OnboardingAgentOrchestrator service
  - [x] 6.1 Create `app/services/onboarding_orchestrator.py` with orchestrator class
    - Implement `__init__(db: AsyncSession)` constructor
    - Implement `get_current_agent(user_id: UUID)` method
    - Implement `_step_to_agent(step: int)` mapping method
    - Implement `_create_agent(agent_type, context)` factory method
    - Implement `_load_onboarding_state(user_id)` helper method
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_
  
  - [x]* 6.2 Write unit tests for orchestrator
    - Test _load_onboarding_state loads correct state
    - Test _create_agent returns correct agent class
    - Test error handling for invalid user_id
    - _Requirements: 5.1, 5.8_
  
  - [ ]* 6.3 Write property tests for orchestrator
    - **Property 8: Step to Agent Mapping Correctness**
    - **Property 9: Invalid Steps Raise ValueError**
    - **Property 10: Agent Factory Creates Correct Type**
    - **Property 11: Context Passed to Agent Constructor**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9**

- [x] 7. Create API request and response schemas
  - Create OnboardingChatRequest schema with message and optional step fields
  - Create OnboardingChatResponse schema with all response fields
  - Create CurrentAgentResponse schema with agent info fields
  - Add field validators for message (non-empty, max length)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ]* 7.1 Write property tests for API schemas
  - **Property 12: API Request Validation**
  - **Validates: Requirements 8.1, 8.2, 8.6**

- [x] 8. Implement API endpoints
  - [x] 8.1 Create POST /api/v1/onboarding/chat endpoint
    - Add endpoint to `app/api/v1/endpoints/onboarding.py`
    - Implement authentication via get_current_user dependency
    - Validate request body against OnboardingChatRequest schema
    - Route message to orchestrator and get agent response
    - Append message to conversation_history in database
    - Return OnboardingChatResponse
    - Add error handling for all error types (401, 404, 422, 500)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [x] 8.2 Create GET /api/v1/onboarding/current-agent endpoint
    - Add endpoint to `app/api/v1/endpoints/onboarding.py`
    - Implement authentication via get_current_user dependency
    - Load onboarding state and determine current agent
    - Return CurrentAgentResponse with agent info
    - Add error handling (401, 404, 500)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 11.1, 11.3, 11.4_
  
  - [x]* 8.3 Write unit tests for API endpoints
    - Test authentication requirement (401 without token)
    - Test validation errors (422 for invalid requests)
    - Test not found errors (404 for missing state)
    - Test successful responses (200 with correct data)
    - _Requirements: 6.5, 6.6, 7.6_
  
  - [ ]* 8.4 Write property tests for API endpoints
    - **Property 13: Successful Requests Update Conversation History**
    - **Property 14: Agent Routing Correctness**
    - **Validates: Requirements 6.3, 6.4, 6.8**

- [ ] 9. Checkpoint - Ensure all tests pass
  - Run all unit tests and property tests
  - Verify code coverage meets 80% minimum
  - Fix any failing tests or coverage gaps
  - Ensure all tests pass, ask the user if questions arise

- [ ] 10. Integration testing and backward compatibility verification
  - [ ] 10.1 Write integration tests for end-to-end flow
    - Test complete flow: API request → orchestrator → agent → response
    - Test conversation history persistence across multiple messages
    - Test context building across agent transitions
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.8_
  
  - [ ]* 10.2 Write property tests for backward compatibility
    - **Property 15: Backward Compatibility Preservation**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
  
  - [ ] 10.3 Test existing OnboardingService still works
    - Run existing onboarding tests
    - Verify no breaking changes to existing API endpoints
    - Test that existing step_data operations work correctly
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 11. Add dependencies and configuration
  - Add langchain, langchain-anthropic, langchain-core to pyproject.toml using `poetry add`
  - Add hypothesis to dev dependencies using `poetry add --group dev`
  - Add ANTHROPIC_API_KEY to Settings in app/core/config.py
  - Add LLM configuration settings (model, temperature, max_tokens)
  - Update .env.example with new environment variables
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 12. Documentation and deployment preparation
  - Add docstrings to all new classes and methods
  - Update API documentation with new endpoints
  - Create migration rollback plan
  - Add monitoring and logging for agent operations
  - Document error codes and responses
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [ ] 13. Final checkpoint - Ensure all tests pass
  - Run complete test suite with coverage report
  - Verify all property tests pass with 100 iterations
  - Verify all integration tests pass
  - Verify backward compatibility tests pass
  - Review code coverage report (target: 80%+)
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties across many generated inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- The implementation follows a bottom-up approach: database → models → base classes → orchestrator → API
- Stub agent implementations will be fully developed in subsequent specifications (Specs 2-4)
- All database operations use async/await patterns
- All API endpoints require JWT authentication
- Use `poetry run` prefix for all commands (pytest, alembic, etc.)
