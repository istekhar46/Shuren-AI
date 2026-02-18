# Implementation Plan: Fitness and Goal Setting Agents

## Overview

This implementation plan breaks down the Fitness and Goal Setting Agents feature into discrete, incremental coding tasks. Each task builds on previous work and includes testing to validate correctness early. The plan follows the design document and ensures all requirements are met through systematic implementation.

## Tasks

- [x] 1. Create Fitness Assessment Agent implementation
  - [x] 1.1 Create FitnessAssessmentAgent class file
    - Create `backend/app/agents/onboarding/fitness_assessment.py`
    - Implement class inheriting from BaseOnboardingAgent
    - Set agent_type = "fitness_assessment"
    - Implement `__init__` method accepting db and context
    - _Requirements: 1.1_
  
  - [x] 1.2 Implement get_system_prompt method
    - Write hardcoded system prompt for fitness assessment
    - Include role definition, guidelines, and fitness level definitions
    - Include instructions for when to call save_fitness_assessment tool
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_
  
  - [x] 1.3 Implement save_fitness_assessment tool
    - Create tool function with @tool decorator
    - Accept parameters: fitness_level, experience_details, limitations
    - Validate fitness_level is in ["beginner", "intermediate", "advanced"]
    - Normalize fitness_level to lowercase
    - Trim whitespace from limitations list
    - Add completed_at timestamp in ISO 8601 format
    - Call save_context to persist data
    - Return success/error status dict
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 13.1, 13.4, 13.6_
  
  - [x] 1.4 Implement get_tools method
    - Return list containing save_fitness_assessment tool
    - _Requirements: 3.1_
  
  - [x] 1.5 Implement process_message method
    - Create ChatPromptTemplate with system prompt and placeholders
    - Create tool-calling agent using create_tool_calling_agent
    - Create AgentExecutor with tools and error handling
    - Execute agent with user message
    - Check completion status with _check_if_complete
    - Return AgentResponse with message, agent_type, step_complete, next_action
    - _Requirements: 1.2, 1.3, 1.4, 1.5_
  
  - [x] 1.6 Implement _check_if_complete helper method
    - Query OnboardingState for user_id
    - Check if "fitness_assessment" exists in agent_context
    - Return boolean indicating completion
    - _Requirements: 1.4_
  
  - [x]* 1.7 Write unit tests for FitnessAssessmentAgent
    - Test agent instantiation and inheritance
    - Test system prompt contains required content
    - Test get_tools returns save_fitness_assessment tool
    - Test _check_if_complete with and without saved data
    - Test medical topic handling (redirect to fitness questions)
    - _Requirements: 15.1_

- [x] 2. Create Goal Setting Agent implementation
  - [x] 2.1 Create GoalSettingAgent class file
    - Create `backend/app/agents/onboarding/goal_setting.py`
    - Implement class inheriting from BaseOnboardingAgent
    - Set agent_type = "goal_setting"
    - Implement `__init__` method accepting db and context
    - _Requirements: 4.1_
  
  - [x] 2.2 Implement get_system_prompt method with context
    - Extract fitness_level from context["fitness_assessment"]
    - Extract limitations from context["fitness_assessment"]
    - Build system prompt including fitness level and limitations
    - Include role definition, goal definitions, and realistic expectations
    - Include instructions for when to call save_fitness_goals tool
    - Handle missing context gracefully with defaults
    - _Requirements: 4.2, 7.1, 7.2, 7.3, 7.4, 7.5, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_
  
  - [x] 2.3 Implement save_fitness_goals tool
    - Create tool function with @tool decorator
    - Accept parameters: primary_goal, secondary_goal, target_weight_kg, target_body_fat_percentage
    - Validate primary_goal is in ["fat_loss", "muscle_gain", "general_fitness"]
    - Validate target_weight_kg is between 30 and 300 if provided
    - Validate target_body_fat_percentage is between 3 and 50 if provided
    - Normalize primary_goal and secondary_goal to lowercase with underscores
    - Add completed_at timestamp in ISO 8601 format
    - Call save_context to persist data
    - Return success/error status dict
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 13.1, 13.2, 13.3, 13.6_
  
  - [x] 2.4 Implement get_tools method
    - Return list containing save_fitness_goals tool
    - _Requirements: 6.1_
  
  - [x] 2.5 Implement process_message method
    - Create ChatPromptTemplate with system prompt and placeholders
    - Create tool-calling agent using create_tool_calling_agent
    - Create AgentExecutor with tools and error handling
    - Execute agent with user message
    - Check completion status with _check_if_complete
    - Return AgentResponse with message, agent_type, step_complete, next_action
    - _Requirements: 4.3, 4.4, 4.5, 4.6_
  
  - [x] 2.6 Implement _check_if_complete helper method
    - Query OnboardingState for user_id
    - Check if "goal_setting" exists in agent_context
    - Return boolean indicating completion
    - _Requirements: 4.5_
  
  - [x]* 2.7 Write unit tests for GoalSettingAgent
    - Test agent instantiation and inheritance
    - Test system prompt includes fitness_level from context
    - Test system prompt includes limitations from context
    - Test get_tools returns save_fitness_goals tool
    - Test _check_if_complete with and without saved data
    - Test handling of missing fitness_assessment context
    - _Requirements: 15.2_

- [x] 3. Implement tool error handling and validation
  - [x] 3.1 Add comprehensive error handling to save_fitness_assessment
    - Wrap save_context call in try-except
    - Log errors with user_id and error details
    - Return user-friendly error messages
    - Ensure no partial data saved on failure
    - _Requirements: 11.1, 11.2, 11.3, 11.5_
  
  - [x] 3.2 Add comprehensive error handling to save_fitness_goals
    - Wrap save_context call in try-except
    - Log errors with user_id and error details
    - Return user-friendly error messages
    - Ensure no partial data saved on failure
    - _Requirements: 11.1, 11.2, 11.3, 11.5_
  
  - [x]* 3.3 Write unit tests for tool error handling
    - Test invalid fitness_level returns error without saving
    - Test invalid primary_goal returns error without saving
    - Test target_weight_kg out of range returns error
    - Test target_body_fat_percentage out of range returns error
    - Test database error returns error without saving
    - Test tool retry after error works correctly
    - _Requirements: 15.6, 15.7_

- [x] 4. Implement context handover integration
  - [x] 4.1 Verify BaseOnboardingAgent.save_context works correctly
    - Test that save_context updates agent_context in OnboardingState
    - Test that multiple agents can save to different keys
    - Test that context persists across agent instantiations
    - _Requirements: 7.1_
  
  - [x] 4.2 Test context passing from Fitness to Goal agent
    - Save fitness_assessment data
    - Instantiate GoalSettingAgent with saved context
    - Verify agent can access fitness_level
    - Verify agent can access limitations
    - Verify system prompt includes context data
    - _Requirements: 7.1, 7.2, 7.3, 7.5_
  
  - [x]* 4.3 Write integration tests for context handover
    - Test complete flow: fitness assessment → goal setting
    - Test that goal agent receives fitness context
    - Test that goal agent system prompt includes fitness data
    - Test graceful handling of missing context
    - _Requirements: 15.3_

- [x] 5. Implement step advancement logic
  - [x] 5.1 Add step advancement to OnboardingAgentOrchestrator
    - After agent returns step_complete=True, increment current_step
    - Update current_agent to reflect new agent type
    - Commit database transaction
    - _Requirements: 14.1, 14.2, 14.3, 14.4_
  
  - [x] 5.2 Test step advancement after fitness assessment
    - Complete fitness assessment
    - Verify current_step increments from 2 to 3
    - Verify current_agent changes to "goal_setting"
    - Verify next message routes to GoalSettingAgent
    - _Requirements: 14.1, 14.5_
  
  - [x] 5.3 Test step advancement after goal setting
    - Complete goal setting
    - Verify current_step increments from 3 to 4
    - Verify current_agent changes to "workout_planning"
    - _Requirements: 14.2, 14.3, 14.4_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Write property-based tests
  - [ ]* 7.1 Write property test for tool input validation (Property 1)
    - **Property 1: Tool Input Validation**
    - **Validates: Requirements 3.3, 3.7, 6.3, 6.7, 11.1, 11.3, 13.2, 13.3**
    - Generate random invalid fitness_level values
    - Generate random out-of-range target_weight_kg values
    - Generate random out-of-range target_body_fat_percentage values
    - Verify all return error without saving data
  
  - [ ]* 7.2 Write property test for tool success persistence (Property 2)
    - **Property 2: Tool Success Persistence**
    - **Validates: Requirements 3.4, 3.5, 3.6, 6.4, 6.5, 6.6, 11.5**
    - Generate random valid fitness_level values
    - Generate random valid primary_goal values
    - Generate random valid target metrics
    - Verify all save successfully with ISO 8601 timestamp
  
  - [ ]* 7.3 Write property test for completion detection (Property 3)
    - **Property 3: Completion Detection and Step Advancement**
    - **Validates: Requirements 1.4, 1.5, 4.5, 4.6, 8.3, 8.4, 8.5, 14.1, 14.2, 14.3, 14.4, 14.5**
    - For any agent with saved data, verify step_complete=True
    - Verify next_action="advance_step"
    - Verify current_step increments
    - Verify current_agent updates
  
  - [ ]* 7.4 Write property test for context handover (Property 4)
    - **Property 4: Context Handover Integrity**
    - **Validates: Requirements 4.2, 7.1, 7.2, 7.3, 7.5**
    - For any fitness_assessment context, verify GoalSettingAgent can access it
    - Verify system prompt includes fitness_level
    - Verify system prompt includes limitations
  
  - [ ]* 7.5 Write property test for data normalization (Property 5)
    - **Property 5: Data Normalization**
    - **Validates: Requirements 13.1, 13.4, 13.6**
    - Generate random mixed-case fitness_level values
    - Generate random mixed-case primary_goal values
    - Generate random limitations with whitespace
    - Verify all normalized to lowercase and trimmed
  
  - [ ]* 7.6 Write property test for agent response validity (Property 6)
    - **Property 6: Agent Response Validity**
    - **Validates: Requirements 1.2, 4.4**
    - For any process_message call, verify AgentResponse has all required fields
    - Verify field types are correct
  
  - [ ]* 7.7 Write property test for completion intent recognition (Property 7)
    - **Property 7: Completion Intent Recognition**
    - **Validates: Requirements 8.1, 8.2, 8.3**
    - Generate random completion phrases
    - Verify agent calls save tool when information is complete
  
  - [ ]* 7.8 Write property test for goal type parsing (Property 8)
    - **Property 8: Goal Type Parsing**
    - **Validates: Requirements 2.1, 2.4, 5.1**
    - Generate random natural language goal expressions
    - Verify correct mapping to fat_loss/muscle_gain/general_fitness
  
  - [ ]* 7.9 Write property test for fitness level classification (Property 9)
    - **Property 9: Fitness Level Classification**
    - **Validates: Requirements 2.1, 2.4**
    - Generate random natural language fitness descriptions
    - Verify correct classification as beginner/intermediate/advanced
  
  - [ ]* 7.10 Write property test for transaction integrity (Property 10)
    - **Property 10: Transaction Integrity on Failure**
    - **Validates: Requirements 11.2, 11.3, 11.4**
    - Simulate database errors during tool execution
    - Verify agent_context remains unchanged
    - Verify tool returns error allowing retry

- [x] 8. Write end-to-end integration tests
  - [x]* 8.1 Write test for complete fitness assessment flow
    - Start with step 0
    - Send messages about fitness level and experience
    - Verify agent asks appropriate questions
    - Complete assessment
    - Verify data saved to agent_context
    - Verify step advances to 3
    - _Requirements: 15.3_
  
  - [x]* 8.2 Write test for complete goal setting flow
    - Start with step 3 and fitness_assessment context
    - Send messages about fitness goals
    - Verify agent references fitness level
    - Complete goal setting
    - Verify data saved to agent_context
    - Verify step advances to 4
    - _Requirements: 15.3_
  
  - [x]* 8.3 Write test for complete fitness → goal flow
    - Start with step 0
    - Complete fitness assessment
    - Verify advancement to goal setting
    - Complete goal setting
    - Verify both contexts saved correctly
    - Verify step advances to 4
    - _Requirements: 15.3_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- All agents use LangChain's tool-calling agent pattern
- All tools validate inputs before saving to database
- All errors are handled gracefully with user-friendly messages
