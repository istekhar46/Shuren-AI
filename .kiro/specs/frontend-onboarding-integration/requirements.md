# Requirements Document

## Introduction

This document specifies the requirements for updating the Shuren frontend to align with the redesigned 4-step backend onboarding flow. The backend has been refactored from a 9-step to a 4-step onboarding process with updated agent types and API structures. The frontend must be updated to reflect these changes across TypeScript types, React hooks, services, and UI components.

## Glossary

- **Onboarding_System**: The frontend application components responsible for user onboarding
- **Backend_API**: The FastAPI backend service providing onboarding endpoints
- **Agent_Type**: Enumeration of specialized AI agents (FITNESS_ASSESSMENT, WORKOUT_PLANNING, DIET_PLANNING, SCHEDULING)
- **Step**: One of four onboarding stages in the new flow
- **State**: Legacy term from 9-step flow, now replaced by "step"
- **Progress_Tracker**: UI component displaying onboarding completion status
- **Type_System**: TypeScript type definitions ensuring type safety
- **Chat_Interface**: Conversational UI for agent interactions

## Requirements

### Requirement 1: Update Type Definitions

**User Story:** As a developer, I want accurate TypeScript types that match the backend API, so that I have type safety and prevent runtime errors.

#### Acceptance Criteria

1. THE Type_System SHALL define AgentType enum with exactly four values: FITNESS_ASSESSMENT, WORKOUT_PLANNING, DIET_PLANNING, SCHEDULING
2. THE Type_System SHALL remove GOAL_SETTING from AgentType enum
3. THE Type_System SHALL define OnboardingProgress interface with total_states equal to 4
4. THE Type_System SHALL define StateMetadata interface with state_number ranging from 1 to 4
5. THE Type_System SHALL define step completion flags (step_1_complete through step_4_complete) in OnboardingStateResponse interface
6. THE Type_System SHALL use "step" terminology instead of "state" in new interfaces where appropriate

### Requirement 2: Update Progress Tracking Logic

**User Story:** As a user, I want to see accurate progress through the 4-step onboarding flow, so that I understand how much is left to complete.

#### Acceptance Criteria

1. WHEN the Onboarding_System initializes, THE Progress_Tracker SHALL display 4 total steps
2. WHEN a step is completed, THE Progress_Tracker SHALL update completion percentage based on 4 steps (25% per step)
3. WHEN the Backend_API returns progress data, THE Onboarding_System SHALL correctly parse completed_states array with values 1-4
4. THE Progress_Tracker SHALL display step names: "Fitness Assessment", "Workout Planning", "Diet Planning", "Scheduling"
5. WHEN all 4 steps are complete, THE Onboarding_System SHALL enable the completion button

### Requirement 3: Update API Service Layer

**User Story:** As a developer, I want the API service to correctly communicate with the 4-step backend, so that data flows properly between frontend and backend.

#### Acceptance Criteria

1. WHEN calling getOnboardingProgress, THE Backend_API SHALL return total_states equal to 4
2. WHEN calling streamOnboardingMessage, THE Onboarding_System SHALL send current_state values between 1 and 4
3. WHEN receiving progress updates, THE Onboarding_System SHALL handle step completion flags (step_1_complete through step_4_complete)
4. THE Onboarding_System SHALL correctly parse agent_type values matching the 4 agent types
5. WHEN state transitions occur, THE Onboarding_System SHALL update from step N to step N+1 where N is 1-3

### Requirement 4: Update Chat Hook Logic

**User Story:** As a user, I want the chat interface to work correctly with the 4-step flow, so that I can complete onboarding without errors.

#### Acceptance Criteria

1. THE Chat_Interface SHALL initialize with totalStates equal to 4
2. WHEN receiving streaming responses, THE Chat_Interface SHALL handle currentState values from 1 to 4
3. WHEN state updates occur, THE Chat_Interface SHALL fetch updated metadata for steps 1-4
4. THE Chat_Interface SHALL display agent descriptions for the 4 agent types
5. WHEN the user completes step 4, THE Chat_Interface SHALL enable onboarding completion

### Requirement 5: Update UI Components

**User Story:** As a user, I want the onboarding UI to accurately reflect the 4-step process, so that I have a clear understanding of my progress.

#### Acceptance Criteria

1. THE Progress_Tracker SHALL display 4 progress indicators (one per step)
2. WHEN rendering agent headers, THE Onboarding_System SHALL display correct agent names for 4 agent types
3. THE Progress_Tracker SHALL show completion percentage calculated as (completed_steps / 4) * 100
4. WHEN displaying step metadata, THE Onboarding_System SHALL show step numbers 1-4
5. THE Progress_Tracker SHALL visually distinguish completed steps from incomplete steps

### Requirement 6: Remove Legacy References

**User Story:** As a developer, I want all references to the 9-step flow removed, so that the codebase is clean and maintainable.

#### Acceptance Criteria

1. THE Onboarding_System SHALL remove all hardcoded references to 9 states
2. THE Onboarding_System SHALL remove all references to GOAL_SETTING agent type
3. THE Onboarding_System SHALL remove state-specific logic for states 5-9
4. THE Onboarding_System SHALL update comments and documentation to reference 4 steps
5. THE Onboarding_System SHALL remove any conditional logic checking for state numbers greater than 4

### Requirement 7: Maintain Backward Compatibility

**User Story:** As a developer, I want the changes to integrate smoothly with existing code, so that other features continue working.

#### Acceptance Criteria

1. WHEN updating types, THE Onboarding_System SHALL maintain existing interface names where possible
2. THE Chat_Interface SHALL continue supporting streaming responses with the same callback structure
3. THE Onboarding_System SHALL maintain existing error handling patterns
4. THE Progress_Tracker SHALL continue using the same component props structure
5. THE Onboarding_System SHALL preserve existing accessibility attributes (ARIA labels, roles)

### Requirement 8: Update Step Metadata

**User Story:** As a user, I want to see accurate descriptions for each onboarding step, so that I know what information is being collected.

#### Acceptance Criteria

1. THE Onboarding_System SHALL display "Fitness Assessment" for step 1 with FITNESS_ASSESSMENT agent
2. THE Onboarding_System SHALL display "Workout Planning" for step 2 with WORKOUT_PLANNING agent
3. THE Onboarding_System SHALL display "Diet Planning" for step 3 with DIET_PLANNING agent
4. THE Onboarding_System SHALL display "Scheduling" for step 4 with SCHEDULING agent
5. WHEN displaying step descriptions, THE Onboarding_System SHALL show agent-specific guidance text

### Requirement 9: Update Progress Calculation

**User Story:** As a user, I want accurate progress percentages, so that I can track my completion status.

#### Acceptance Criteria

1. WHEN 0 steps are complete, THE Progress_Tracker SHALL display 0% completion
2. WHEN 1 step is complete, THE Progress_Tracker SHALL display 25% completion
3. WHEN 2 steps are complete, THE Progress_Tracker SHALL display 50% completion
4. WHEN 3 steps are complete, THE Progress_Tracker SHALL display 75% completion
5. WHEN 4 steps are complete, THE Progress_Tracker SHALL display 100% completion

### Requirement 10: Ensure Mobile Responsiveness

**User Story:** As a mobile user, I want the 4-step progress UI to work well on my device, so that I can complete onboarding on any screen size.

#### Acceptance Criteria

1. THE Progress_Tracker SHALL display all 4 steps clearly on mobile screens (320px width minimum)
2. WHEN viewing on mobile, THE Progress_Tracker SHALL use vertical or compact horizontal layout
3. THE Progress_Tracker SHALL maintain touch-friendly spacing between interactive elements
4. WHEN displaying step names, THE Onboarding_System SHALL truncate or wrap text appropriately on small screens
5. THE Progress_Tracker SHALL remain accessible and readable across all viewport sizes
