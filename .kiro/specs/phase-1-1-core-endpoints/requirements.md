# Requirements Document

## Introduction

Phase 1.1 Core Endpoints builds upon Phase 1 Foundation by implementing the remaining core API endpoints for workout management, meal management, and AI chat interaction. This phase completes the REST API layer needed for the Shuren AI fitness application, enabling users to access their personalized workout plans and schedules, meal plans, and interact with AI agents through a conversational interface.

The system maintains the principle of "fixed plans with flexible execution" - workout and meal plans are stable structures that require explicit unlocking to modify, ensuring users understand when their core configuration changes. This phase also introduces the database schema for storing complete workout plans with exercises, sets, and reps.

## Glossary

- **System**: The Shuren backend API server
- **User**: An authenticated user with a completed onboarding profile
- **Workout_Plan**: A user's complete weekly workout structure with exercises
- **Workout_Day**: A single day's workout within a plan (e.g., "Chest + Triceps")
- **Exercise**: A specific movement with sets, reps, and instructions
- **Exercise_Library**: Reference database of all available exercises
- **Workout_Schedule**: A user's configured workout days and timing preferences
- **Meal_Plan**: A user's nutritional structure (calories, macros, meal count)
- **Meal_Schedule**: A user's meal timing preferences throughout the day
- **Profile_Lock**: A mechanism preventing silent configuration changes (is_locked flag)
- **Profile_Version**: An immutable audit record of profile changes
- **Chat_Session**: A conversation context between user and AI agent
- **AI_Agent**: One of six specialized agents providing fitness guidance
- **Database**: PostgreSQL database with existing schema from Phase 1

## Requirements

### Requirement 1: Workout Plan Storage

**User Story:** As a user, I want my complete workout plan stored in the system, so that I can access my exercises, sets, and reps at any time.

#### Acceptance Criteria

1. THE System SHALL store workout plans with weekly structure and duration
2. THE System SHALL store individual workout days with muscle group focus and exercise lists
3. THE System SHALL store exercises with sets, reps, weight, and rest periods
4. THE System SHALL maintain an exercise library with names, types, muscle groups, and instructions
5. THE System SHALL associate workout plans with users through foreign key relationships
6. THE System SHALL support progressive overload tracking through exercise history
7. THE System SHALL store exercise GIF URLs for visual guidance
8. THE System SHALL validate all exercise data before persistence

### Requirement 2: Workout Plan Access

**User Story:** As a user, I want to view my complete workout plan, so that I know what exercises to perform.

#### Acceptance Criteria

1. WHEN a user requests their workout plan, THE System SHALL return the complete weekly structure with all workout days
2. WHEN a user requests a specific workout day, THE System SHALL return all exercises with sets, reps, and instructions
3. WHEN a user requests today's workout, THE System SHALL return the workout scheduled for the current day with complete exercise details
4. WHEN a user requests this week's workouts, THE System SHALL return all workouts scheduled for the current week with exercise summaries
5. THE System SHALL include exercise GIF URLs in workout responses for visual guidance
6. THE System SHALL complete workout plan queries within 100ms

### Requirement 3: Workout Schedule Access

**User Story:** As a user, I want to view my workout schedule, so that I know when I'm supposed to exercise.

#### Acceptance Criteria

1. WHEN a user requests their workout schedule, THE System SHALL return all configured workout days with timing
2. WHEN a user requests the next scheduled workout, THE System SHALL return the next upcoming workout based on current time and day
3. WHEN no workout is scheduled for a requested time period, THE System SHALL return an empty result without error
4. THE System SHALL complete workout schedule queries within 100ms

### Requirement 4: Workout Plan Modification

**User Story:** As a user, I want to update my workout plan, so that I can adjust exercises based on progress or changing goals.

#### Acceptance Criteria

1. WHEN a user attempts to modify their workout plan, THE System SHALL verify the profile is unlocked
2. IF the profile is locked, THEN THE System SHALL reject the modification with a 403 error
3. WHEN a user successfully modifies an unlocked workout plan, THE System SHALL persist the changes to the database
4. WHEN a locked profile is unlocked and modified, THE System SHALL create a new profile version record
5. THE System SHALL validate exercise data before persisting modifications
6. THE System SHALL complete workout plan updates within 200ms

### Requirement 5: Workout Schedule Modification

**User Story:** As a user, I want to update my workout schedule, so that I can adjust when I exercise based on my changing availability.

#### Acceptance Criteria

1. WHEN a user attempts to modify their workout schedule, THE System SHALL verify the profile is unlocked
2. IF the profile is locked, THEN THE System SHALL reject the modification with a 403 error
3. WHEN a user successfully modifies an unlocked workout schedule, THE System SHALL persist the changes to the database
4. WHEN a locked profile is unlocked and modified, THE System SHALL create a new profile version record
5. THE System SHALL complete workout schedule updates within 200ms

### Requirement 6: Meal Plan Access

**User Story:** As a user, I want to view my meal plan, so that I understand my nutritional targets.

#### Acceptance Criteria

1. WHEN a user requests their meal plan, THE System SHALL return calories, macros, and meal count
2. WHEN a user requests their meal schedule, THE System SHALL return all configured meal times
3. WHEN a user requests today's meals, THE System SHALL return all meals scheduled for the current day
4. WHEN a user requests the next meal, THE System SHALL return the next upcoming meal based on current time
5. THE System SHALL complete meal plan queries within 100ms

### Requirement 7: Meal Plan Modification

**User Story:** As a user, I want to update my meal plan and schedule, so that I can adjust my nutrition based on changing goals or lifestyle.

#### Acceptance Criteria

1. WHEN a user attempts to modify their meal plan, THE System SHALL verify the profile is unlocked
2. IF the profile is locked, THEN THE System SHALL reject the modification with a 403 error
3. WHEN a user successfully modifies an unlocked meal plan, THE System SHALL persist the changes to the database
4. WHEN a user modifies meal schedule timing, THE System SHALL validate all times are in valid 24-hour format
5. WHEN a locked profile is unlocked and modified, THE System SHALL create a new profile version record
6. THE System SHALL complete meal plan updates within 200ms

### Requirement 8: AI Chat Interaction

**User Story:** As a user, I want to send messages to AI agents, so that I can get personalized fitness guidance and support.

#### Acceptance Criteria

1. WHEN a user sends a chat message, THE System SHALL accept the message and return a response
2. WHEN a user starts a new chat session, THE System SHALL create a session context
3. WHEN a user requests chat history, THE System SHALL return previous messages in chronological order
4. WHEN a user ends a chat session, THE System SHALL mark the session as completed
5. THE System SHALL associate all chat messages with the authenticated user

### Requirement 9: Authentication and Authorization

**User Story:** As a system administrator, I want all endpoints to require authentication, so that user data remains secure.

#### Acceptance Criteria

1. WHEN an unauthenticated request is made to any endpoint, THE System SHALL reject it with a 401 error
2. WHEN a user attempts to access another user's data, THE System SHALL reject the request with a 403 error
3. THE System SHALL validate JWT tokens for all protected endpoints
4. THE System SHALL extract user identity from valid JWT tokens
5. THE System SHALL use the existing authentication dependency from Phase 1

### Requirement 10: Error Handling and Validation

**User Story:** As a developer, I want comprehensive error handling, so that API consumers receive clear feedback about failures.

#### Acceptance Criteria

1. WHEN invalid input is provided, THE System SHALL return a 422 error with validation details
2. WHEN a requested resource does not exist, THE System SHALL return a 404 error
3. WHEN a profile lock prevents modification, THE System SHALL return a 403 error with explanation
4. WHEN an internal error occurs, THE System SHALL return a 500 error and log the exception
5. THE System SHALL use Pydantic validation for all request bodies

### Requirement 11: Data Consistency and Versioning

**User Story:** As a system administrator, I want profile changes to be versioned, so that we maintain an audit trail of modifications.

#### Acceptance Criteria

1. WHEN a locked profile is modified, THE System SHALL create a profile version record before applying changes
2. WHEN creating a profile version, THE System SHALL capture the complete state before modification
3. THE System SHALL include timestamps in all profile version records
4. THE System SHALL maintain referential integrity between profiles and versions
5. THE System SHALL never delete profile version records

### Requirement 12: Performance Requirements

**User Story:** As a user, I want fast API responses, so that the application feels responsive.

#### Acceptance Criteria

1. THE System SHALL complete all read operations within 100ms under normal load
2. THE System SHALL complete all write operations within 200ms under normal load
3. THE System SHALL use database indexes for frequently queried fields
4. THE System SHALL use async database operations for all queries
5. THE System SHALL minimize database round trips through efficient query design

### Requirement 13: API Consistency and Standards

**User Story:** As a frontend developer, I want consistent API patterns, so that integration is predictable.

#### Acceptance Criteria

1. THE System SHALL follow RESTful conventions for all endpoints
2. THE System SHALL use consistent response formats across all endpoints
3. THE System SHALL include appropriate HTTP status codes for all responses
4. THE System SHALL use Pydantic schemas for request and response validation
5. THE System SHALL follow the same patterns established in Phase 1 endpoints
