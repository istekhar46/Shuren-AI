# Implementation Plan: Frontend Onboarding Integration

## Overview

This implementation plan breaks down the frontend updates needed to align with the 4-step backend onboarding flow. The approach follows a phased migration strategy, starting with low-risk type updates and progressing to component and service layer changes. Each task builds incrementally to ensure the system remains functional throughout the implementation.

## Tasks

- [x] 1. Update TypeScript type definitions
  - [x] 1.1 Update AgentType enum in onboarding.types.ts
    - Remove GOAL_SETTING from AgentType enum
    - Verify enum has exactly 4 values: FITNESS_ASSESSMENT, WORKOUT_PLANNING, DIET_PLANNING, SCHEDULING
    - Update JSDoc comments to reference 4 agent types
    - _Requirements: 1.1, 1.2_
  
  - [ ]* 1.2 Write unit tests for AgentType enum
    - Test enum has exactly 4 keys
    - Test GOAL_SETTING is not present
    - Test all 4 agent type values match backend
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.3 Update interface comments and documentation
    - Update OnboardingProgress JSDoc to reference 4 steps
    - Update StateMetadata JSDoc to reference state_number range 1-4
    - Update total_states comment to "Always 4"
    - Add StepCompletionFlags interface for step_1_complete through step_4_complete
    - _Requirements: 1.3, 1.4, 1.5, 1.6_
  
  - [ ]* 1.4 Write property test for state number range validation
    - **Property 3: State Number Range Validation**
    - **Validates: Requirements 1.4, 5.4**

- [x] 2. Update useOnboardingChat hook
  - [x] 2.1 Update totalStates constant
    - Change totalStates from 9 to 4
    - Update all references to totalStates in hook
    - _Requirements: 2.1, 4.1_
  
  - [x] 2.2 Add state validation and clamping functions
    - Implement validateState function to clamp values to 1-4 range
    - Implement calculatePercentage function for 4-step calculation
    - Implement isValidAgent function without GOAL_SETTING
    - _Requirements: 3.2, 3.4_
  
  - [ ]* 2.3 Write property test for progress percentage calculation
    - **Property 2: Progress Percentage Calculation**
    - **Validates: Requirements 2.2, 5.3, 9.1, 9.2, 9.3, 9.4, 9.5**
  
  - [ ]* 2.4 Write property test for state input clamping
    - **Property 5: State Input Clamping**
    - **Validates: Requirements 3.2**
  
  - [x] 2.5 Update progress update handling
    - Add validation for completed_states array (filter to 1-4 range)
    - Update state transition logic for 4 steps
    - Ensure metadata fetching works for steps 1-4
    - _Requirements: 2.3, 3.5, 4.3_
  
  - [ ]* 2.6 Write property tests for state handling
    - **Property 4: Completed States Array Validation**
    - **Property 6: State Transition Sequence**
    - **Property 7: Metadata Fetching for Valid Steps**
    - **Property 8: Current State Handling in Streaming**
    - **Validates: Requirements 2.3, 3.5, 4.2, 4.3**

- [x] 3. Checkpoint - Verify hook updates
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update onboardingService
  - [x] 4.1 Add input validation for streamOnboardingMessage
    - Validate currentState is between 1-4
    - Clamp invalid values and log warnings
    - _Requirements: 3.2_
  
  - [x] 4.2 Add response validation for progress updates
    - Validate total_states equals 4
    - Filter completed_states to only include 1-4
    - Validate agent_type matches one of 4 types
    - _Requirements: 3.1, 3.3, 3.4_
  
  - [ ]* 4.3 Write unit tests for service validation
    - Test state clamping behavior
    - Test response validation and filtering
    - Test error handling for invalid data
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5. Update AgentHeader component
  - [x] 5.1 Update agent name mapping
    - Remove GOAL_SETTING from getAgentName function
    - Verify mapping for 4 agent types
    - Update TypeScript Record type to use 4 agents
    - _Requirements: 5.2, 8.1, 8.2, 8.3, 8.4_
  
  - [x] 5.2 Update agent icon mapping
    - Remove GOAL_SETTING (🎯) from getAgentIcon function
    - Verify icons for 4 agent types
    - Update TypeScript Record type to use 4 agents
    - _Requirements: 5.2_
  
  - [x] 5.3 Update agent color mapping
    - Remove GOAL_SETTING (bg-blue-600) from getAgentColorClass function
    - Verify colors for 4 agent types
    - Update TypeScript Record type to use 4 agents
    - _Requirements: 5.2_
  
  - [ ]* 5.4 Write unit tests for AgentHeader
    - Test agent name mapping for all 4 types
    - Test agent icon mapping for all 4 types
    - Test agent color mapping for all 4 types
    - Test component renders correctly with 4-step data
    - _Requirements: 5.2, 8.1, 8.2, 8.3, 8.4_
  
  - [ ]* 5.5 Write property test for step name mapping
    - **Property 9: Step Name Mapping Consistency**
    - **Validates: Requirements 2.4, 8.1, 8.2, 8.3, 8.4**

- [x] 6. Update OnboardingProgressBar component
  - [x] 6.1 Update allStates array definition
    - Replace 9-state array with 4-state array
    - Define states: 1-Fitness Assessment, 2-Workout Planning, 3-Diet Planning, 4-Scheduling
    - Add agent field to each state object
    - _Requirements: 2.4, 5.1, 8.1, 8.2, 8.3, 8.4_
  
  - [x] 6.2 Update getStateStatus function
    - Add validation for state numbers 1-4
    - Return 'upcoming' for invalid state numbers
    - _Requirements: 5.4_
  
  - [x] 6.3 Update progress bar rendering
    - Verify progress bar works with 4 steps
    - Update "Step X of Y" text to show 4 total
    - Ensure mobile and desktop layouts work with 4 steps
    - _Requirements: 2.1, 5.1, 10.1, 10.2_
  
  - [ ]* 6.4 Write unit tests for OnboardingProgressBar
    - Test component renders 4 progress indicators
    - Test state status calculation for steps 1-4
    - Test progress percentage display
    - Test mobile responsive layout
    - Test accessibility attributes (ARIA labels)
    - _Requirements: 2.1, 5.1, 5.4, 7.5_
  
  - [ ]* 6.5 Write property test for completed states validation
    - Test component handles completed_states arrays correctly
    - Test filtering of invalid state numbers
    - _Requirements: 2.3_

- [x] 7. Update OnboardingChatPage component
  - [x] 7.1 Update completion message text
    - Change "all onboarding steps" to "all 4 onboarding steps"
    - Verify completion button logic works with 4 steps
    - _Requirements: 2.5, 4.5_
  
  - [ ]* 7.2 Write integration tests for OnboardingChatPage
    - Test full onboarding flow with 4 steps
    - Test completion button appears after step 4
    - Test streaming responses work correctly
    - Test plan preview workflow
    - _Requirements: 2.5, 4.5, 7.2_

- [x] 8. Checkpoint - Verify all component updates
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Remove legacy references
  - [x] 9.1 Search and remove hardcoded "9" references
    - Search codebase for hardcoded "9" in onboarding context
    - Replace with "4" or totalStates constant
    - _Requirements: 6.1_
  
  - [x] 9.2 Remove state-specific logic for states 5-9
    - Search for conditional checks for state > 4
    - Remove or update logic to handle only 1-4
    - _Requirements: 6.3, 6.5_
  
  - [x] 9.3 Update comments and documentation
    - Update inline comments to reference 4 steps
    - Update component documentation
    - Update README if applicable
    - _Requirements: 6.4_

- [x] 10. Add edge case handling
  - [x] 10.1 Add error handling for invalid state numbers
    - Handle state < 1 by clamping to 1
    - Handle state > 4 by clamping to 4
    - Log warnings for invalid states
    - _Requirements: 6.5_
  
  - [x] 10.2 Add error handling for missing metadata
    - Display loading state when metadata is null
    - Fetch fresh metadata on errors
    - Show user-friendly error messages
    - _Requirements: 7.3_
  
  - [ ]* 10.3 Write unit tests for edge cases
    - Test state clamping for values < 1 and > 4
    - Test handling of null/undefined metadata
    - Test handling of empty completed_states arrays
    - Test handling of invalid agent types
    - _Requirements: 6.5_

- [x] 11. Final integration testing
  - [ ]* 11.1 Write end-to-end integration tests
    - Test complete onboarding flow from step 1 to 4
    - Test state transitions between all steps
    - Test progress tracking updates correctly
    - Test agent switching between steps
    - Test completion workflow
    - _Requirements: All requirements_
  
  - [ ]* 11.2 Run all property-based tests
    - Execute all 9 property tests with 100+ iterations
    - Verify no failures or edge cases found
    - Document any issues discovered
    - _Requirements: All property requirements_

- [x] 12. Final checkpoint - Complete verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples, edge cases, and error conditions
- The implementation follows a phased approach: Types → Hooks → Services → Components → Cleanup
- All changes maintain backward compatibility with existing streaming and error handling patterns
- TypeScript will catch many issues at compile time, reducing runtime errors
