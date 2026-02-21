# Implementation Plan: Onboarding Conversation Memory

## Overview

This implementation aligns onboarding agent architecture with the BaseAgent pattern by adding conversation memory support. The approach follows a phased rollout to minimize risk. Each phase builds incrementally, with testing at each step to ensure stability.

## Tasks

- [x] 1. Create OnboardingAgentContext model
  - Create OnboardingAgentContext class in backend/app/agents/context.py
  - Add fields: user_id (str), conversation_history (List[Dict]), agent_context (Dict), loaded_at (datetime)
  - Set frozen=True for immutability
  - Add Pydantic Config with example
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [ ]* 1.1 Write unit tests for OnboardingAgentContext
  - Test context creation with valid data
  - Test immutability (frozen=True)
  - Test default values for optional fields
  - Test field type validation
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] 2. Add _build_messages helper to BaseOnboardingAgent
  - [x] 2.1 Update BaseOnboardingAgent constructor
    - Modify constructor to accept OnboardingAgentContext
    - Store context as self.context
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.2 Implement _build_messages method
    - Create _build_messages(message: str) method
    - Build list starting with SystemMessage from get_system_prompt()
    - Add conversation history from self.context.conversation_history (limit to last 15)
    - Convert dict format to LangChain messages (HumanMessage, AIMessage)
    - Append current message as HumanMessage
    - Handle malformed messages gracefully with logging
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ]* 2.3 Write property tests for _build_messages
  - **Property 1: Message Structure Invariant**
  - **Validates: Requirements 3.3, 3.6**
  
- [ ]* 2.4 Write property test for history inclusion
  - **Property 2: Conversation History Inclusion with Limiting**
  - **Validates: Requirements 3.4, 3.5**
  
- [ ]* 2.5 Write property test for format conversion
  - **Property 3: History Format Conversion**
  - **Validates: Requirements 3.7**

- [x] 3. Update OnboardingAgentOrchestrator to load conversation history
  - [x] 3.1 Implement _load_conversation_history method
    - Query ConversationMessage table for user's messages
    - Order by created_at ascending
    - Limit to last 20 messages
    - Format as [{"role": "user"|"assistant", "content": "..."}]
    - Handle database errors with empty list fallback
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 3.2 Update _create_agent method
    - Call _load_conversation_history before creating agent
    - Create OnboardingAgentContext with loaded history
    - Pass OnboardingAgentContext to agent constructor
    - Handle context creation errors
    - _Requirements: 4.5, 4.6_
  
  - [x] 3.3 Update get_current_agent method signature
    - Pass user_id to _create_agent
    - Update method calls throughout orchestrator
    - _Requirements: 4.5, 4.6_

- [ ]* 3.4 Write property tests for orchestrator
  - **Property 4: Orchestrator Message Loading with Ordering and Limiting**
  - **Validates: Requirements 4.2, 4.3, 6.1**
  
- [ ]* 3.5 Write property test for orchestrator format transformation
  - **Property 5: Orchestrator Format Transformation**
  - **Validates: Requirements 4.4**

- [ ]* 3.6 Write integration test for orchestrator
  - Test orchestrator loads conversation history from database
  - Test orchestrator creates OnboardingAgentContext
  - Test orchestrator passes context to agent
  - _Requirements: 4.1, 4.5, 4.6_

- [x] 4. Checkpoint - Verify foundation components
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Update FitnessAssessmentAgent to use _build_messages
  - [x] 5.1 Modify stream_response method
    - Replace manual message construction with self._build_messages(message)
    - Remove conversation_history parameter
    - Remove ChatPromptTemplate usage
    - Stream directly from self.llm.astream(messages)
    - _Requirements: 5.1, 5.6, 5.7_

- [ ]* 5.2 Write unit test for FitnessAssessmentAgent
  - Test stream_response uses _build_messages
  - Test agent works with OnboardingAgentContext
  - _Requirements: 5.1_

- [x] 6. Update GoalSettingAgent to use _build_messages
  - [x] 6.1 Modify stream_response method
    - Replace manual message construction with self._build_messages(message)
    - Remove conversation_history parameter
    - Remove ChatPromptTemplate usage
    - Stream directly from self.llm.astream(messages)
    - _Requirements: 5.2, 5.6, 5.7_

- [ ]* 6.2 Write unit test for GoalSettingAgent
  - Test stream_response uses _build_messages
  - Test agent works with OnboardingAgentContext
  - _Requirements: 5.2_

- [x] 7. Update WorkoutPlanningAgent to use _build_messages
  - [x] 7.1 Modify stream_response method
    - Replace manual message construction with self._build_messages(message)
    - Remove conversation_history parameter
    - Remove ChatPromptTemplate usage
    - Stream directly from self.llm.astream(messages)
    - _Requirements: 5.3, 5.6, 5.7_

- [ ]* 7.2 Write unit test for WorkoutPlanningAgent
  - Test stream_response uses _build_messages
  - Test agent works with OnboardingAgentContext
  - _Requirements: 5.3_

- [x] 8. Update DietPlanningAgent to use _build_messages
  - [x] 8.1 Modify stream_response method
    - Replace manual message construction with self._build_messages(message)
    - Remove conversation_history parameter
    - Remove ChatPromptTemplate usage
    - Stream directly from self.llm.astream(messages)
    - _Requirements: 5.4, 5.6, 5.7_

- [ ]* 8.2 Write unit test for DietPlanningAgent
  - Test stream_response uses _build_messages
  - Test agent works with OnboardingAgentContext
  - _Requirements: 5.4_

- [x] 9. Update SchedulingAgent to use _build_messages
  - [x] 9.1 Modify stream_response method
    - Replace manual message construction with self._build_messages(message)
    - Remove conversation_history parameter
    - Remove ChatPromptTemplate usage
    - Stream directly from self.llm.astream(messages)
    - _Requirements: 5.5, 5.6, 5.7_

- [ ]* 9.2 Write unit test for SchedulingAgent
  - Test stream_response uses _build_messages
  - Test agent works with OnboardingAgentContext
  - _Requirements: 5.5_

- [x] 10. Checkpoint - Verify all agents updated
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Write comprehensive property tests for limiting behavior
  - [ ]* 11.1 Write property test for history limiting preserves recency
    - **Property 6: History Limiting Preserves Recency**
    - **Validates: Requirements 6.2, 6.3, 6.4**
  
  - [ ]* 11.2 Write property test for message content preservation
    - **Property 7: Message Content Preservation**
    - **Validates: Requirements 6.5**

- [x] 12. Final validation and cleanup
  - [x] 12.1 Run full test suite
    - Execute poetry run pytest
    - Verify all existing tests pass
    - Verify new tests pass
    - Check test coverage meets 90%+ goal
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 12.2 Manual testing of onboarding flow
    - Test complete onboarding flow with conversation memory
    - Verify agents remember previous messages
    - Verify agents don't ask repeated questions
    - Test with various conversation history sizes
    - _Requirements: All requirements_
  
  - [x] 12.3 Update documentation
    - Add docstrings to new methods
    - Update README if needed
    - Document migration path for future developers

- [x] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
    - Add docstrings to new methods
    - Update README if needed
    - Document migration path for future developers

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Phased approach minimizes risk during implementation
- All agents updated consistently to use the same pattern
