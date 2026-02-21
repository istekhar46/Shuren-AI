# Implementation Plan: Minimal Frontend for Backend Testing

## Overview

This implementation plan breaks down the React TypeScript frontend into discrete, incremental tasks. Each task builds on previous work, with testing integrated throughout. The frontend will enable comprehensive testing of the Shuren AI backend's Phase 1 & 2 functionality including authentication, onboarding, AI agents (text and voice), meals, and workouts.

**Project Location:** All frontend code will be created in the `/frontend` directory at the repository root.

**Technology Stack:**
- React with TypeScript
- Vite for build tooling
- React Router for navigation
- Context API for state management
- Axios for HTTP requests
- Shadcn/ui for UI components
- LiveKit React SDK for voice sessions
- Vitest + React Testing Library for testing
- fast-check for property-based testing

## Tasks

- [x] 1. Project setup and configuration
  - Initialize Vite project with React and TypeScript in `/frontend` directory
  - Install core dependencies (react-router-dom, axios, tailwind)
  - Configure Tailwind CSS and Shadcn/ui
  - Set up ESLint and Prettier
  - Create environment variable configuration (.env files)
  - Set up project structure (folders: components, pages, services, contexts, hooks, types)
  - _Requirements: 3.1, 3.2_
  - _Note: All frontend code goes in `/frontend` directory at repository root_

- [x] 2. Core infrastructure and API client
  - [x] 2.1 Create TypeScript type definitions
    - Define all interfaces in types/index.ts (AuthResponse, UserProfile, ChatMessage, etc.)
    - _Requirements: 3.3_
    - _Location: /frontend/src/types/index.ts_
  
  - [x] 2.2 Implement API client with interceptors
    - Create services/api.ts with Axios instance
    - Add request interceptor for JWT token injection
    - Add response interceptor for error handling (401 redirect)
    - _Requirements: 3.3_
  
  - [ ]* 2.3 Write property test for API client
    - **Property 3: JWT token included in authenticated requests**
    - **Validates: Requirements 2.1.3**
  
  - [x] 2.4 Create error handling utilities
    - Implement AppError class and handleApiError function
    - _Requirements: 3.3_

- [x] 3. Authentication system
  - [x] 3.1 Implement AuthContext and provider
    - Create contexts/AuthContext.tsx with login, register, logout functions
    - Implement token persistence in localStorage
    - _Requirements: 2.1.1, 2.1.2, 2.1.3, 2.1.4_
  
  - [x] 3.2 Create AuthService
    - Implement services/authService.ts with register, login, logout methods
    - _Requirements: 2.1.1, 2.1.2, 2.1.4_
  
  - [x] 3.3 Build Login and Register pages
    - Create pages/LoginPage.tsx with form validation
    - Create pages/RegisterPage.tsx with form validation
    - Add error message display
    - _Requirements: 2.1.1, 2.1.2_
  
  - [x] 3.4 Implement ProtectedRoute component
    - Create components/common/ProtectedRoute.tsx
    - Add authentication check and redirect logic
    - _Requirements: 2.1.5_
  
  - [ ]* 3.5 Write property tests for authentication
    - **Property 1: Valid registration creates authenticated session**
    - **Property 2: Valid credentials authenticate user**
    - **Property 4: Protected routes require authentication**
    - **Validates: Requirements 2.1.1, 2.1.2, 2.1.5**
  
  - [ ]* 3.6 Write unit tests for auth components
    - Test login form validation
    - Test registration form validation
    - Test logout functionality
    - _Requirements: 2.1.1, 2.1.2, 2.1.4_

- [ ] 4. Checkpoint - Ensure authentication works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. User profile and context
  - [x] 5.1 Implement UserContext and provider
    - Create contexts/UserContext.tsx with profile state
    - Implement refreshProfile and unlockProfile functions
    - _Requirements: 2.3.1, 2.3.4, 2.3.5_
  
  - [x] 5.2 Create ProfileService
    - Implement services/profileService.ts with getProfile, unlockProfile, updateProfile
    - _Requirements: 2.3.4, 2.3.5_
  
  - [ ]* 5.3 Write unit tests for profile service
    - Test profile fetching
    - Test profile unlock with confirmation
    - _Requirements: 2.3.4, 2.3.5_

- [x] 6. Onboarding flow
  - [x] 6.1 Create OnboardingService
    - Implement services/onboardingService.ts with saveStep and getProgress
    - _Requirements: 2.2.2_
  
  - [x] 6.2 Build OnboardingPage with step navigation
    - Create pages/OnboardingPage.tsx with progress indicator
    - Implement step navigation (back/next buttons)
    - Add step state management
    - _Requirements: 2.2.1, 2.2.3, 2.2.4_
  
  - [x] 6.3 Implement onboarding step components (Steps 1-6)
    - Create components/onboarding/Step1FitnessLevel.tsx
    - Create components/onboarding/Step2Goals.tsx
    - Create components/onboarding/Step3PhysicalConstraints.tsx
    - Create components/onboarding/Step4DietaryPreferences.tsx
    - Create components/onboarding/Step5MealPlan.tsx
    - Create components/onboarding/Step6MealSchedule.tsx
    - Each step saves data via OnboardingService
    - _Requirements: 2.2.2_
  
  - [x] 6.4 Implement onboarding step components (Steps 7-12)
    - Create components/onboarding/Step7WorkoutSchedule.tsx
    - Create components/onboarding/Step8Hydration.tsx
    - Create components/onboarding/Step9LifestyleBaseline.tsx
    - Create components/onboarding/Step10Notifications.tsx
    - Create components/onboarding/Step11Review.tsx
    - Create components/onboarding/Step12Confirmation.tsx
    - Step 12 locks profile and redirects to dashboard
    - _Requirements: 2.2.2, 2.2.5_
  
  - [x] 6.5 Add validation error handling
    - Display backend validation errors in each step
    - _Requirements: 2.2.6_
  
  - [x] 6.6 Write property tests for onboarding
    - **Property 5: Onboarding steps persist data**
    - **Property 6: Backward navigation in onboarding**
    - **Property 7: Validation errors displayed**
    - **Validates: Requirements 2.2.2, 2.2.3, 2.2.6**
  
  - [x] 6.7 Write integration test for onboarding flow
    - Test complete onboarding flow from step 1 to 12
    - Verify profile lock and redirect
    - _Requirements: 2.2.5_

- [x] 7. Checkpoint - Ensure onboarding works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Dashboard page
  - [x] 8.1 Create Dashboard page with summary cards
    - Create pages/DashboardPage.tsx
    - Create components/dashboard/ProfileSummary.tsx
    - Create components/dashboard/MealPlanSummary.tsx
    - Create components/dashboard/WorkoutScheduleSummary.tsx
    - Create components/dashboard/QuickActions.tsx
    - _Requirements: 2.3.1, 2.3.2, 2.3.3_
  
  - [x] 8.2 Write unit tests for dashboard components
    - Test profile summary rendering
    - Test meal plan summary rendering
    - Test workout schedule rendering
    - _Requirements: 2.3.1, 2.3.2, 2.3.3_

- [x] 9. Text chat interface
  - [x] 9.1 Create ChatService
    - Implement services/chatService.ts with sendMessage, getHistory, streamMessage
    - _Requirements: 2.4.2, 2.4.5_
  
  - [x] 9.2 Create useChat hook
    - Implement hooks/useChat.ts for chat state management
    - Handle message sending, history, loading states
    - _Requirements: 2.4.2, 2.4.5, 2.4.6_
  
  - [x] 9.3 Build ChatPage with message interface
    - Create pages/ChatPage.tsx
    - Create components/chat/AgentSelector.tsx (dropdown for agent types)
    - Create components/chat/MessageList.tsx with auto-scroll
    - Create components/chat/MessageInput.tsx with send button
    - Create components/chat/LoadingIndicator.tsx
    - _Requirements: 2.4.1, 2.4.2, 2.4.4, 2.4.6_
  
  - [x] 9.4 Add error handling for chat
    - Display error messages when agent fails
    - _Requirements: 2.4.7_
  
  - [x] 9.5 Write property tests for chat
    - **Property 8: Messages routed to selected agent**
    - **Property 9: Chat history accumulates messages**
    - **Property 10: Chat errors displayed**
    - **Validates: Requirements 2.4.2, 2.4.4, 2.4.5, 2.4.7**
  
  - [x] 9.6 Write unit tests for chat components
    - Test message sending
    - Test agent selection
    - Test error display
    - _Requirements: 2.4.2, 2.4.4, 2.4.7_

- [x] 10. Checkpoint - Ensure text chat works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Voice session interface
  - [x] 11.1 Install and configure LiveKit dependencies
    - Install livekit-client and @livekit/components-react
    - _Requirements: 3.1_
  
  - [x] 11.2 Create VoiceService
    - Implement services/voiceService.ts with startSession, getStatus, endSession
    - _Requirements: 2.7.2, 2.7.8_
  
  - [x] 11.3 Create VoiceContext and provider
    - Implement contexts/VoiceContext.tsx for voice session state
    - _Requirements: 2.7.2, 2.7.7_
  
  - [x] 11.4 Implement useVoiceSession hook
    - Create hooks/useVoiceSession.ts
    - Handle LiveKit room connection, events, transcription
    - Request microphone permissions
    - Track session status and latency
    - _Requirements: 2.7.2, 2.7.3, 2.7.4, 2.7.5, 2.7.7, 2.7.10_
  
  - [x] 11.5 Build VoicePage with session controls
    - Create pages/VoicePage.tsx
    - Create components/voice/AgentSelector.tsx
    - Create components/voice/VoiceControls.tsx (start/stop buttons)
    - Create components/voice/TranscriptionDisplay.tsx
    - Create components/voice/SessionStatus.tsx (connection, participants, duration)
    - Create components/voice/LatencyIndicator.tsx
    - _Requirements: 2.7.1, 2.7.5, 2.7.7, 2.7.8, 2.7.10_
  
  - [x] 11.6 Add error handling for voice sessions
    - Handle connection failures, permission denied, room join errors
    - _Requirements: 2.7.9_
  
  - [x] 11.7 Write property tests for voice sessions
    - **Property 14: Transcription updates from LiveKit data**
    - **Property 15: Session status reflects LiveKit events**
    - **Property 16: Voice connection errors handled**
    - **Property 17: Latency updates from agent data**
    - **Validates: Requirements 2.7.5, 2.7.7, 2.7.9, 2.7.10**
  
  - [x] 11.8 Write unit tests for voice components
    - Test session start/stop
    - Test microphone permission handling
    - Test error display
    - _Requirements: 2.7.2, 2.7.3, 2.7.8, 2.7.9_

- [x] 12. Checkpoint - Ensure voice sessions work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Meal management interface
  - [x] 13.1 Create MealService
    - Implement services/mealService.ts with getMealPlan, getMealDetails, searchDishes, generateShoppingList
    - _Requirements: 2.5.1, 2.5.2, 2.5.3, 2.5.5_
  
  - [x] 13.2 Build MealsPage with meal views
    - Create pages/MealsPage.tsx
    - Create components/meals/MealPlanView.tsx (weekly grid)
    - Create components/meals/MealDetails.tsx (modal with ingredients, macros, instructions)
    - Create components/meals/DishBrowser.tsx with search
    - Create components/meals/ShoppingList.tsx with category grouping
    - _Requirements: 2.5.1, 2.5.2, 2.5.3, 2.5.6_
  
  - [x] 13.3 Add meal substitution request button
    - Button opens chat with pre-filled substitution message
    - _Requirements: 2.5.4_
  
  - [x] 13.4 Write property tests for meals
    - **Property 11: Dish search filters results**
    - **Property 12: Shopping list groups by category**
    - **Validates: Requirements 2.5.3, 2.5.6**
  
  - [x] 13.5 Write unit tests for meal components
    - Test meal plan display
    - Test dish search
    - Test shopping list generation
    - Test substitution request
    - _Requirements: 2.5.1, 2.5.3, 2.5.4, 2.5.5_

- [x] 14. Workout management interface
  - [x] 14.1 Create WorkoutService
    - Implement services/workoutService.ts with getSchedule, getTodayWorkout, logSet, completeWorkout, getHistory
    - _Requirements: 2.6.1, 2.6.2, 2.6.3, 2.6.4, 2.6.5_
  
  - [x] 14.2 Build WorkoutsPage with workout views
    - Create pages/WorkoutsPage.tsx
    - Create components/workouts/WorkoutSchedule.tsx (calendar view)
    - Create components/workouts/TodayWorkout.tsx (exercise list)
    - Create components/workouts/ExerciseLogger.tsx (log sets with reps/weight)
    - Create components/workouts/WorkoutHistory.tsx (past workouts)
    - _Requirements: 2.6.1, 2.6.2, 2.6.3, 2.6.5_
  
  - [x] 14.3 Add workout completion functionality
    - Mark workout as complete button
    - _Requirements: 2.6.4_
  
  - [x] 14.4 Add exercise demonstration request button
    - Button opens chat with pre-filled demo request message
    - _Requirements: 2.6.6_
  
  - [x] 14.5 Write property tests for workouts
    - **Property 13: Workout set logging persists**
    - **Validates: Requirements 2.6.3**
  
  - [x] 14.6 Write unit tests for workout components
    - Test workout schedule display
    - Test set logging
    - Test workout completion
    - Test demo request
    - _Requirements: 2.6.1, 2.6.3, 2.6.4, 2.6.6_

- [x] 15. Checkpoint - Ensure meals and workouts work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Shared components and utilities
  - [x] 16.1 Create shared UI components
    - Create components/common/LoadingSpinner.tsx
    - Create components/common/ErrorMessage.tsx with auto-dismiss
    - Create components/common/ConfirmDialog.tsx for destructive actions
    - _Requirements: 4.1_
  
  - [x] 16.2 Create layout components
    - Create components/layout/Header.tsx with navigation
    - Create components/layout/Footer.tsx
    - Create components/layout/MainLayout.tsx
    - _Requirements: 3.2_
  
  - [x] 16.3 Write unit tests for shared components
    - Test loading spinner
    - Test error message display and dismiss
    - Test confirm dialog
    - _Requirements: 4.1_

- [x] 17. Routing and navigation
  - [x] 17.1 Set up React Router
    - Configure routes in App.tsx
    - Add protected routes for authenticated pages
    - Add lazy loading for code splitting
    - _Requirements: 3.1, 3.5_
  
  - [x] 17.2 Implement navigation menu
    - Add navigation links in Header component
    - Highlight active route
    - _Requirements: 3.2_

- [ ] 18. Styling and responsive design
  - [ ] 18.1 Apply Tailwind styles to all components
    - Ensure consistent color scheme and typography
    - _Requirements: 3.4_
  
  - [ ] 18.2 Implement responsive breakpoints
    - Test mobile (< 640px), tablet (640-1024px), desktop (> 1024px)
    - Adjust layouts for different screen sizes
    - _Requirements: 3.4_
  
  - [ ] 18.3 Add accessibility features
    - Semantic HTML, ARIA labels, keyboard navigation
    - _Requirements: 4.2_

- [ ] 19. Testing infrastructure setup
  - [ ] 19.1 Configure Vitest and React Testing Library
    - Install vitest, @testing-library/react, @testing-library/user-event
    - Create tests/setup.ts with test configuration
    - _Requirements: Testing Strategy_
  
  - [ ] 19.2 Configure fast-check for property-based testing
    - Install fast-check
    - Create example property test
    - _Requirements: Testing Strategy_
  
  - [ ] 19.3 Set up MSW for API mocking
    - Install msw
    - Create mock handlers for all API endpoints
    - _Requirements: Testing Strategy_

- [ ] 20. Final integration and polish
  - [ ] 20.1 Test all user flows end-to-end
    - Registration → Login → Onboarding → Dashboard
    - Chat with all agent types
    - Voice session with agent
    - Meal browsing and shopping list
    - Workout logging and completion
    - _Requirements: All_
  
  - [ ] 20.2 Fix any bugs or issues found during testing
    - Address edge cases
    - Improve error messages
    - _Requirements: All_
  
  - [ ] 20.3 Add loading states and optimistic UI updates
    - Improve perceived performance
    - _Requirements: 3.5_
  
  - [ ] 20.4 Document setup and usage
    - Create README.md with setup instructions
    - Document environment variables
    - Add troubleshooting guide
    - _Requirements: All_

- [ ] 21. Final checkpoint - Complete testing
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end user flows
- All code should use TypeScript for type safety
- Follow React best practices and hooks patterns
- Use Shadcn/ui components for consistent UI
- Ensure all API calls include proper error handling
- Test on multiple browsers and screen sizes before completion

