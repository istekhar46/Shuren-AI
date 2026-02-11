# Implementation Plan: Backend Onboarding Chat Integration

## Overview

This implementation plan breaks down the backend onboarding chat integration feature into discrete, incremental tasks. Each task builds on previous work and includes testing to validate functionality early.

## Tasks

- [ ] 1. Database schema updates and migration
  - [ ] 1.1 Create Alembic migration for OnboardingState model
    - Add `agent_history` JSONB column with default empty list
    - Update check constraint from `current_step <= 11` to `current_step <= 9`
    - Test migration on local database
    - _Requirements: 3.1, 4.1.1_
  
  - [ ] 1.2 Implement data migration script
    - Write Python migration logic to consolidate 11 steps → 9 states
    - Merge steps 4 & 5 into state 3 (constraints + targets)
    - Preserve original data in `_migration_metadata` field
    - Test with sample production-like data
    - _Requirements: 3.1, 4.2_
  
  - [ ]* 1.3 Write property test for migration data integrity
    - **Property: Data Migration Preservation**
    - **Validates: Requirements 3.1**
    - Test that all original data is preserved in metadata
    - Test that state numbers are correctly remapped

- [ ] 2. Update OnboardingService with new methods and validators
  - [ ] 2.1 Add state metadata constant
    - Create STATE_METADATA dictionary with all 9 states
    - Include state_number, name, agent, description, required_fields
    - _Requirements: 3.1.1, 3.3.1_
  
  - [ ] 2.2 Implement get_progress method
    - Calculate completed states from step_data JSONB
    - Get current and next state metadata
    - Calculate completion percentage
    - Return OnboardingProgress object
    - _Requirements: 2.2.1, 2.2.2, 2.2.3, 2.2.4, 3.3.1_
  
  - [ ] 2.3 Implement can_complete_onboarding method
    - Check if all 9 states have data in step_data
    - Return boolean
    - _Requirements: 2.2.4, 3.3.1_
  
  - [ ] 2.4 Update _validate_step_data method
    - Remap validators from 11 steps to 9 states
    - Update validator dictionary keys (1-9 instead of 1-11)
    - _Requirements: 3.3.1_
  
  - [ ] 2.5 Implement _validate_state_3_workout_constraints
    - Merge validation logic from old steps 4 & 5
    - Validate equipment, injuries, limitations (required lists)
    - Validate optional target_weight_kg and target_body_fat_percentage
    - _Requirements: 3.3.1, 5.1_
  
  - [ ]* 2.6 Write unit tests for OnboardingService updates
    - Test get_progress with various completion states
    - Test can_complete_onboarding edge cases
    - Test merged state 3 validation
    - _Requirements: 3.3.1_
  
  - [ ]* 2.7 Write property test for completion percentage calculation
    - **Property 6: Completion Percentage Calculation**
    - **Validates: Requirements 2.2.4**
    - For any set of completed states, verify percentage = (completed/9)*100


- [ ] 3. Create agent onboarding function tools
  - [ ] 3.1 Create onboarding_tools.py helper module
    - Implement call_onboarding_step helper function
    - Handle OnboardingValidationError and return structured response
    - Log agent context (agent_type, user_id, step)
    - _Requirements: 2.3.1, 2.3.2, 2.3.4, 3.4.1_
  
  - [ ] 3.2 Add function tools to WorkoutPlannerAgent
    - Implement save_fitness_level (state 1)
    - Implement save_fitness_goals (state 2)
    - Implement save_workout_constraints (state 3)
    - Add tools to _get_tools method
    - _Requirements: 2.3.1, 3.4.2_
  
  - [ ] 3.3 Add function tools to DietPlannerAgent
    - Implement save_dietary_preferences (state 4)
    - Implement save_meal_plan (state 5)
    - Add tools to _get_tools method
    - _Requirements: 2.3.1, 3.4.3_
  
  - [ ] 3.4 Add function tools to SchedulerAgent
    - Implement save_meal_schedule (state 6)
    - Implement save_workout_schedule (state 7)
    - Implement save_hydration_schedule (state 8)
    - Add tools to _get_tools method
    - _Requirements: 2.3.1, 3.4.4_
  
  - [ ] 3.5 Add function tools to SupplementGuideAgent
    - Implement save_supplement_preferences (state 9)
    - Add tool to _get_tools method
    - _Requirements: 2.3.1, 3.4.5_
  
  - [ ]* 3.6 Write unit tests for agent function tools
    - Test each tool calls correct endpoint
    - Test error handling and structured responses
    - Test agent context logging
    - _Requirements: 2.3.1, 2.3.2, 2.3.4_
  
  - [ ]* 3.7 Write property test for agent function tool invocation
    - **Property 16: Agent Function Tool Invocation**
    - **Validates: Requirements 2.3.1**
    - For any agent with tools, verify tool successfully invokes endpoint

- [ ] 4. Update AgentOrchestrator with onboarding mode
  - [ ] 4.1 Add onboarding_mode parameter to route_query
    - Add parameter with default False
    - Update method signature and docstring
    - _Requirements: 2.1.2, 3.3.2_
  
  - [ ] 4.2 Implement access control logic
    - Check user.onboarding_completed status
    - If onboarding_mode=True: allow specialized agents, reject if completed
    - If onboarding_mode=False: force general agent, reject if not completed
    - Raise appropriate errors with helpful messages
    - _Requirements: 2.4.1, 2.4.2, 3.3.2_
  
  - [ ] 4.3 Add onboarding_mode to response metadata
    - Include in AgentResponse metadata dict
    - _Requirements: 3.3.2_
  
  - [ ]* 4.4 Write unit tests for orchestrator access control
    - Test onboarding_mode=True with incomplete user
    - Test onboarding_mode=True with completed user (should fail)
    - Test onboarding_mode=False with incomplete user (should fail)
    - Test onboarding_mode=False with completed user
    - _Requirements: 2.4.1, 2.4.2_
  
  - [ ]* 4.5 Write property test for onboarding mode access control
    - **Property 2: Onboarding Mode Access Control**
    - **Validates: Requirements 2.1.1, 2.4.1**
    - For any user, verify access control based on onboarding_completed status


- [ ] 5. Implement new API endpoints
  - [ ] 5.1 Create onboarding progress endpoint
    - Add GET /api/v1/onboarding/progress route
    - Implement endpoint handler with authentication
    - Call OnboardingService.get_progress
    - Return OnboardingProgressResponse schema
    - Handle 404 if onboarding state not found
    - _Requirements: 2.2.1, 2.2.2, 2.2.3, 2.2.4, 2.2.5, 3.1.1_
  
  - [ ] 5.2 Create onboarding progress response schema
    - Define StateInfo Pydantic model
    - Define OnboardingProgressResponse Pydantic model
    - Include all required fields per requirements
    - _Requirements: 3.1.1_
  
  - [ ] 5.3 Create onboarding chat endpoint
    - Add POST /api/v1/chat/onboarding route
    - Implement endpoint handler with authentication
    - Verify user is not onboarding_completed (403 if completed)
    - Verify current_state matches onboarding state (400 if mismatch)
    - Route to appropriate agent using STATE_TO_AGENT_MAP
    - Call orchestrator with onboarding_mode=True
    - Check if state was updated after agent call
    - Return OnboardingChatResponse with progress
    - _Requirements: 2.1.1, 2.1.2, 2.1.4, 3.1.2_
  
  - [ ] 5.4 Create onboarding chat request/response schemas
    - Define OnboardingChatRequest with message and current_state
    - Define OnboardingChatResponse with response, agent_type, state_updated, new_state, progress
    - Add validation constraints (current_state 1-9)
    - _Requirements: 3.1.2_
  
  - [ ] 5.5 Create STATE_TO_AGENT_MAP constant
    - Map states 1-9 to AgentType enum values
    - States 1-3: WORKOUT, 4-5: DIET, 6-8: SCHEDULER, 9: SUPPLEMENT
    - _Requirements: 2.1.2, 3.1.2_
  
  - [ ]* 5.6 Write unit tests for progress endpoint
    - Test successful response with various completion states
    - Test 404 when onboarding state not found
    - Test response structure matches schema
    - _Requirements: 3.1.1_
  
  - [ ]* 5.7 Write unit tests for onboarding chat endpoint
    - Test successful chat interaction
    - Test 403 when user already completed onboarding
    - Test 400 when state mismatch
    - Test agent routing based on current_state
    - Test state_updated flag
    - _Requirements: 3.1.2_
  
  - [ ]* 5.8 Write property test for state-to-agent mapping
    - **Property 1: State-to-Agent Mapping Consistency**
    - **Validates: Requirements 2.1.2**
    - For any state (1-9), verify correct agent is selected
  
  - [ ]* 5.9 Write property test for progress endpoint completeness
    - **Property 5: Progress Endpoint Completeness**
    - **Validates: Requirements 2.2.1, 2.2.2, 2.2.3, 2.2.5**
    - For any user, verify all required fields are present in response

- [ ] 6. Checkpoint - Test new endpoints and agent tools
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 7. Modify existing API endpoints
  - [ ] 7.1 Update GET /api/v1/users/me endpoint
    - Create AccessControl Pydantic schema
    - Build access_control object based on onboarding_completed status
    - If incomplete: set locked_features, include onboarding_progress
    - If complete: set all can_access_* to true, empty locked_features
    - Add access_control to UserResponse schema
    - _Requirements: 2.4.4, 3.2.1_
  
  - [ ] 7.2 Update POST /api/v1/onboarding/step endpoint
    - Change step validation from 1-11 to 1-9
    - Add X-Agent-Context header parameter (optional)
    - Log agent context if provided
    - Include next_state_info in response
    - Update error responses to include field information
    - _Requirements: 2.3.4, 2.5.3, 3.2.2_
  
  - [ ] 7.3 Update POST /api/v1/chat endpoint
    - Add onboarding_completed check (403 if false)
    - Reject explicit agent_type if not "general" (403)
    - Force agent_type to GENERAL for all completed users
    - Pass onboarding_mode=False to orchestrator
    - Update error responses with helpful messages
    - _Requirements: 2.4.1, 2.4.2, 3.2.3_
  
  - [ ]* 7.4 Write unit tests for modified endpoints
    - Test users/me with incomplete vs complete onboarding
    - Test onboarding/step with agent context header
    - Test chat endpoint access control
    - Test error responses match expected format
    - _Requirements: 3.2.1, 3.2.2, 3.2.3_
  
  - [ ]* 7.5 Write property test for feature lock enforcement
    - **Property 11: Feature Lock Enforcement**
    - **Validates: Requirements 2.4.4**
    - For any incomplete user, verify access_control flags are correct
  
  - [ ]* 7.6 Write property test for post-onboarding agent restriction
    - **Property 10: Post-Onboarding Agent Restriction**
    - **Validates: Requirements 2.4.1, 2.4.2**
    - For any completed user, verify only general agent is accessible

- [ ] 8. Implement logging and observability
  - [ ] 8.1 Add agent context logging to onboarding_tools
    - Log agent_type, user_id, step on every tool call
    - Log validation errors with agent context
    - Use structured logging with extra fields
    - _Requirements: 2.3.4, 2.5.3, 2.5.5_
  
  - [ ] 8.2 Add agent routing history tracking
    - Update OnboardingState.agent_history on state changes
    - Record agent_type, state, timestamp
    - Append to JSONB array
    - _Requirements: 2.5.2_
  
  - [ ] 8.3 Add agent_type to conversation responses
    - Include agent_type in OnboardingChatResponse
    - Include agent_type in regular ChatResponse
    - _Requirements: 2.5.1_
  
  - [ ]* 8.4 Write property test for agent context logging
    - **Property 13: Agent Context Logging**
    - **Validates: Requirements 2.3.4, 2.5.3, 2.5.5**
    - For any agent operation, verify logging includes agent context
  
  - [ ]* 8.5 Write property test for agent routing history
    - **Property 14: Agent Routing History Tracking**
    - **Validates: Requirements 2.5.2**
    - For any state update via agent, verify history is recorded

- [ ] 9. Checkpoint - Test modified endpoints and logging
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 10. Integration testing and validation
  - [ ] 10.1 Write integration test for complete onboarding flow
    - Test all 9 states via chat endpoint
    - Verify agent routing for each state
    - Verify state transitions and progress updates
    - Verify completion and access control changes
    - _Requirements: 2.1.1, 2.1.2, 2.1.4, 2.1.5_
  
  - [ ] 10.2 Write integration test for agent function tools
    - Test each agent's tools call correct endpoints
    - Test validation errors are handled correctly
    - Test success responses include next state info
    - _Requirements: 2.3.1, 2.3.2, 2.3.5_
  
  - [ ] 10.3 Write integration test for access control flow
    - Test incomplete user can only access chat onboarding
    - Test completed user can access all features
    - Test completed user cannot access onboarding chat
    - Test completed user forced to general agent
    - _Requirements: 2.4.1, 2.4.2, 2.4.3, 2.4.4_
  
  - [ ]* 10.4 Write property test for validation before persistence
    - **Property 3: Validation Before Persistence**
    - **Validates: Requirements 2.1.3**
    - For any invalid data, verify rejection before database changes
  
  - [ ]* 10.5 Write property test for incremental progress persistence
    - **Property 8: Incremental Progress Persistence**
    - **Validates: Requirements 2.1.5**
    - For any saved state, verify data is immediately queryable
  
  - [ ]* 10.6 Write property test for idempotent state saves
    - **Property 9: Idempotent State Saves**
    - **Validates: Requirements 2.1.5**
    - For any state and data, verify multiple saves produce same result

- [ ] 11. Run database migration
  - [ ] 11.1 Test migration on local database
    - Create test data with 11-step onboarding states
    - Run migration: `poetry run alembic upgrade head`
    - Verify constraint updated (0-9 instead of 0-11)
    - Verify agent_history column added
    - Verify data correctly migrated
    - _Requirements: 3.1, 4.1.1, 4.2_
  
  - [ ] 11.2 Test migration rollback
    - Run downgrade: `poetry run alembic downgrade -1`
    - Verify original data restored from metadata
    - Verify constraint reverted to 0-11
    - Verify agent_history column removed
    - _Requirements: 4.2_
  
  - [ ] 11.3 Prepare migration for staging
    - Document migration steps
    - Create backup procedure
    - Define rollback plan
    - _Requirements: 4.2_

- [ ] 12. Documentation and cleanup
  - [ ] 12.1 Update API documentation
    - Document new endpoints in OpenAPI/Swagger
    - Document modified endpoints
    - Include request/response examples
    - Document error codes
    - _Requirements: All_
  
  - [ ] 12.2 Update README with new features
    - Document chat-based onboarding flow
    - Document state consolidation (11→9)
    - Document agent function tools
    - _Requirements: All_
  
  - [ ] 12.3 Add inline code documentation
    - Docstrings for all new methods
    - Comments for complex logic
    - Type hints for all parameters
    - _Requirements: All_

- [ ] 13. Final checkpoint - Run full test suite
  - Run all unit tests: `poetry run pytest tests/`
  - Run all property tests: `poetry run pytest -m property`
  - Run integration tests: `poetry run pytest -m integration`
  - Run with coverage: `poetry run pytest --cov=app --cov-report=html`
  - Verify coverage >= 80% for new code
  - Ensure all tests pass, ask the user if questions arise.


## Notes

- Tasks marked with `*` are optional test-related sub-tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- All Python commands should use `poetry run` prefix
- Database migrations should be tested thoroughly before production deployment
- Agent function tools reuse existing validation logic via REST endpoints
- Access control is enforced at multiple layers (endpoint, orchestrator, service)
- Logging includes agent context for debugging and analytics
- Original 11-step data is preserved in migration metadata for rollback capability

## Implementation Order Rationale

1. **Database first**: Schema changes must be in place before code changes
2. **Service layer**: Core business logic before API endpoints
3. **Agent tools**: Function tools before endpoints that use them
4. **Orchestrator**: Routing logic before endpoints that depend on it
5. **New endpoints**: New functionality before modifying existing
6. **Modified endpoints**: Changes to existing endpoints last to maintain compatibility
7. **Logging**: Observability throughout implementation
8. **Integration tests**: End-to-end validation after all components complete

## Testing Strategy

- **Unit tests**: Test individual components in isolation
- **Property tests**: Test universal properties with generated inputs (100+ iterations)
- **Integration tests**: Test complete flows across multiple components
- **Coverage target**: 80%+ for new code
- **Test execution**: Use `poetry run pytest` for all test commands

## Deployment Checklist

Before deploying to staging/production:
- [ ] All tests passing
- [ ] Coverage >= 80%
- [ ] Migration tested on production-like data
- [ ] API documentation updated
- [ ] Rollback plan documented
- [ ] Monitoring and alerts configured
- [ ] Feature flags configured (if applicable)

