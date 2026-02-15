# Requirements Document

## Introduction

This document defines the requirements for frontend integration to support the onboarding-first approach in the Shuren AI fitness application. The backend implementation is complete and validated. This specification ensures the frontend properly implements navigation locks, progress indicators, endpoint routing, and user state management to create a seamless onboarding experience.

The frontend must enforce that all users complete the mandatory 9-state onboarding flow before accessing any application features. During onboarding, users interact with specialized AI agents through a chat interface. After completion, users gain full access to the application and interact exclusively with the general AI assistant.

## Glossary

- **Onboarding_State**: The current step (1-9) in the onboarding process
- **Navigation_Lock**: UI mechanism that prevents access to features until onboarding completes
- **Specialized_Agent**: AI agents (Workout, Diet, Scheduler, Supplement) available only during onboarding
- **General_Agent**: AI assistant available only after onboarding completion
- **State_Metadata**: Rich information about each onboarding state (name, description, required fields)
- **Progress_Indicator**: Visual UI element showing onboarding completion status
- **Onboarding_Completed_Flag**: Boolean property on User model indicating onboarding status
- **State_Updated_Flag**: Boolean in API response indicating if onboarding progressed
- **Chat_Endpoint**: POST /api/v1/chat - endpoint for post-onboarding conversations
- **Onboarding_Chat_Endpoint**: POST /api/v1/chat/onboarding - endpoint for onboarding conversations
- **HTTP_403_Error**: Forbidden status code returned when accessing locked features
- **Redirect_Path**: URL path to navigate user when access is denied

## Requirements

### Requirement 1: Navigation Lock Implementation

**User Story:** As a new user, I want clear visual feedback that features are locked during onboarding, so that I understand I must complete onboarding first.

#### Acceptance Criteria

1. WHEN a user has not completed onboarding, THEN THE Frontend SHALL disable all navigation menu items except the onboarding chat interface
2. WHEN a user hovers over a locked navigation item, THEN THE Frontend SHALL display a tooltip with the message "Complete onboarding to unlock this feature"
3. WHEN a user attempts to navigate to a locked route directly via URL, THEN THE Frontend SHALL redirect to /onboarding with a message "Complete onboarding to access this feature"
4. WHEN a user completes onboarding, THEN THE Frontend SHALL automatically unlock all navigation items without requiring page refresh
5. WHEN the Frontend receives a 403 error with error_code "ONBOARDING_REQUIRED", THEN THE Frontend SHALL redirect to the path specified in the redirect field

### Requirement 2: Progress Indicator Display

**User Story:** As a user going through onboarding, I want to see my progress visually, so that I know how many steps remain and feel motivated to complete the process.

#### Acceptance Criteria

1. WHEN a user is on the onboarding page, THEN THE Frontend SHALL display a progress bar showing "Step X of 9" where X is the current state number
2. WHEN displaying onboarding progress, THEN THE Frontend SHALL show a list of all 9 states with checkmarks for completed states
3. WHEN displaying onboarding progress, THEN THE Frontend SHALL highlight the current state with distinct visual styling
4. WHEN displaying onboarding progress, THEN THE Frontend SHALL show upcoming states in a grayed-out or disabled visual style
5. WHEN the Frontend fetches state metadata from the backend, THEN THE Frontend SHALL display the state name and description from STATE_METADATA for each state
6. WHEN a state is updated during chat, THEN THE Frontend SHALL animate the transition to the new state and update the progress indicator

### Requirement 3: Endpoint Routing Logic

**User Story:** As a developer, I want the frontend to route chat messages to the correct backend endpoint based on onboarding status, so that users interact with the appropriate agents.

#### Acceptance Criteria

1. WHEN a user has not completed onboarding, THEN THE Frontend SHALL send all chat messages to POST /api/v1/chat/onboarding
2. WHEN a user has completed onboarding, THEN THE Frontend SHALL send all chat messages to POST /api/v1/chat
3. WHEN the Frontend receives a 403 error from POST /api/v1/chat with error_code "ONBOARDING_REQUIRED", THEN THE Frontend SHALL redirect to /onboarding and display the onboarding_progress information
4. WHEN the Frontend receives a 403 error from POST /api/v1/chat/onboarding indicating onboarding is complete, THEN THE Frontend SHALL redirect to the main chat interface
5. WHEN sending a message to POST /api/v1/chat/onboarding, THEN THE Frontend SHALL include the current_state field matching the user's current onboarding step
6. WHEN the Frontend receives a 400 error indicating state mismatch, THEN THE Frontend SHALL fetch the current state from GET /api/v1/onboarding/progress and resync

### Requirement 4: Onboarding Chat Interface

**User Story:** As a user, I want a conversational onboarding experience, so that providing my information feels natural and guided.

#### Acceptance Criteria

1. WHEN a user first enters onboarding, THEN THE Frontend SHALL display a welcome message explaining the onboarding process
2. WHEN a user sends a message during onboarding, THEN THE Frontend SHALL display the message in the chat interface with "user" role styling
3. WHEN the Frontend receives a response from POST /api/v1/chat/onboarding, THEN THE Frontend SHALL display the agent's response with "assistant" role styling
4. WHEN the response includes state_updated: true, THEN THE Frontend SHALL display a confirmation message indicating progress to the next state
5. WHEN the response includes state_updated: true, THEN THE Frontend SHALL update the current_state to the new_state value for subsequent messages
6. WHEN the response includes progress information, THEN THE Frontend SHALL update the progress indicator to reflect the new completion percentage
7. WHEN onboarding is complete (is_complete: true in progress), THEN THE Frontend SHALL display a completion message and redirect to the main application after 3 seconds

### Requirement 5: User State Management

**User Story:** As a user, I want the application to remember my onboarding status across sessions, so that I don't have to restart if I close the app.

#### Acceptance Criteria

1. WHEN a user logs in, THEN THE Frontend SHALL check the onboarding_completed property from the user object
2. WHEN onboarding_completed is false, THEN THE Frontend SHALL redirect to /onboarding immediately after login
3. WHEN onboarding_completed is true, THEN THE Frontend SHALL allow access to the main application
4. WHEN the Frontend loads the onboarding page, THEN THE Frontend SHALL fetch current progress from GET /api/v1/onboarding/progress
5. WHEN the progress response indicates is_complete: true, THEN THE Frontend SHALL redirect to the main application
6. WHEN a state transition occurs, THEN THE Frontend SHALL update the local state to match the new_state from the API response
7. WHEN the user refreshes the page during onboarding, THEN THE Frontend SHALL resume from the current_state without losing progress

### Requirement 6: Error Handling and Recovery

**User Story:** As a user, I want clear error messages when something goes wrong, so that I know how to proceed.

#### Acceptance Criteria

1. WHEN the Frontend receives a 403 error with error_code "ONBOARDING_REQUIRED", THEN THE Frontend SHALL display the message field and redirect to the redirect path
2. WHEN the Frontend receives a 403 error with error_code "AGENT_NOT_ALLOWED", THEN THE Frontend SHALL display an error message explaining only the general agent is available
3. WHEN the Frontend receives a 400 error indicating state mismatch, THEN THE Frontend SHALL fetch the correct state and display a message "Syncing your progress..."
4. WHEN the Frontend receives a 500 error, THEN THE Frontend SHALL display a user-friendly error message and provide a retry button
5. WHEN the Frontend loses network connectivity during onboarding, THEN THE Frontend SHALL display an offline indicator and queue messages for retry
6. WHEN network connectivity is restored, THEN THE Frontend SHALL automatically retry queued messages

### Requirement 7: Post-Onboarding Experience

**User Story:** As a user who completed onboarding, I want seamless access to all features, so that I can start using the application immediately.

#### Acceptance Criteria

1. WHEN onboarding is complete, THEN THE Frontend SHALL unlock all navigation menu items
2. WHEN onboarding is complete, THEN THE Frontend SHALL route all chat messages to POST /api/v1/chat
3. WHEN onboarding is complete, THEN THE Frontend SHALL not include agent_type in chat requests (backend forces general agent)
4. WHEN the Frontend receives a response from POST /api/v1/chat, THEN THE Frontend SHALL display the agent_type in the chat interface
5. WHEN a completed user attempts to access /onboarding, THEN THE Frontend SHALL redirect to the main chat interface with a message "You've already completed onboarding"

### Requirement 8: Responsive Design and Accessibility

**User Story:** As a user on any device, I want the onboarding interface to work smoothly, so that I can complete it on mobile, tablet, or desktop.

#### Acceptance Criteria

1. WHEN the onboarding interface is displayed on mobile devices, THEN THE Frontend SHALL adapt the progress indicator to a compact vertical layout
2. WHEN the onboarding interface is displayed on desktop, THEN THE Frontend SHALL show the progress indicator in a sidebar with full state names
3. WHEN a user navigates using keyboard only, THEN THE Frontend SHALL support tab navigation through all interactive elements
4. WHEN a screen reader is used, THEN THE Frontend SHALL announce progress updates and state transitions
5. WHEN the chat input receives focus, THEN THE Frontend SHALL ensure the input is visible above the mobile keyboard

### Requirement 9: Performance and Optimization

**User Story:** As a user, I want fast responses during onboarding, so that the experience feels smooth and responsive.

#### Acceptance Criteria

1. WHEN the Frontend sends a chat message, THEN THE Frontend SHALL display a loading indicator within 100ms
2. WHEN the Frontend receives an API response, THEN THE Frontend SHALL render the message within 50ms
3. WHEN fetching onboarding progress, THEN THE Frontend SHALL cache the result for 30 seconds to avoid redundant requests
4. WHEN a state transition occurs, THEN THE Frontend SHALL invalidate the progress cache and fetch fresh data
5. WHEN the user types in the chat input, THEN THE Frontend SHALL debounce typing indicators to avoid excessive updates

### Requirement 10: Data Validation and Security

**User Story:** As a developer, I want the frontend to validate data before sending to the backend, so that we catch errors early and reduce server load.

#### Acceptance Criteria

1. WHEN a user sends an empty message, THEN THE Frontend SHALL prevent the request and display a validation message "Please enter a message"
2. WHEN the Frontend stores authentication tokens, THEN THE Frontend SHALL use secure storage mechanisms (httpOnly cookies or secure localStorage)
3. WHEN the Frontend makes API requests, THEN THE Frontend SHALL include the JWT token in the Authorization header
4. WHEN the Frontend receives a 401 error, THEN THE Frontend SHALL clear stored credentials and redirect to login
5. WHEN the Frontend receives user data, THEN THE Frontend SHALL sanitize all text content before rendering to prevent XSS attacks
