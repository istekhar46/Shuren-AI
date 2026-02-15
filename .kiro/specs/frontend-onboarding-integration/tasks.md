# Implementation Plan: Frontend Onboarding Integration

## Overview

This implementation plan converts the design document into discrete coding tasks for implementing chat-based onboarding in the Shuren frontend. The backend is fully implemented and validated. This plan focuses on frontend changes to integrate with the existing backend endpoints.

**Key Changes**:
- Replace form-based onboarding with chat interface
- Implement navigation lock until onboarding complete
- Add progress indicators from backend state metadata
- Route between `/chat/onboarding` and `/chat` endpoints
- Automatic navigation unlock post-onboarding

**Technology Stack**: React 18+, TypeScript, React Router v6, Tailwind CSS

---

## Tasks

### 1. Update Type Definitions

- [x] 1.1 Add onboarding types to `frontend/src/types/onboarding.types.ts`
  - Add `OnboardingProgress` interface
  - Add `StateMetadata` interface
  - Add `OnboardingChatRequest` interface
  - Add `OnboardingChatResponse` interface
  - _Requirements: US-2.6, US-2.7, US-4.1_

- [x] 1.2 Update User type in `frontend/src/types/auth.types.ts`
  - Add `onboarding_completed: boolean` field to `User` interface
  - _Requirements: US-5.5_

---

### 2. Enhance UserContext

- [x] 2.1 Update UserContext to include onboarding status
  - Add `onboardingCompleted: boolean` to context interface
  - Add `refreshOnboardingStatus()` method to context interface
  - Fetch user data from `GET /api/v1/users/me` on context initialization
  - Store `onboarding_completed` flag in context state
  - Implement `refreshOnboardingStatus()` to refetch user data
  - _Requirements: US-5.5_

- [x] 2.2 Write unit tests for UserContext onboarding status
  - Test `onboardingCompleted` flag is fetched correctly
  - Test `refreshOnboardingStatus()` updates flag
  - Test context provides correct initial state
  - _Requirements: US-5.5_

---

### 3. Enhance ProtectedRoute Component

- [x] 3.1 Add onboarding check to ProtectedRoute
  - Add `requireOnboardingComplete` prop (default: `true`)
  - Use `useUser()` hook to get `onboardingCompleted` flag
  - Redirect to `/onboarding` if `requireOnboardingComplete=true` and `onboardingCompleted=false`
  - Redirect to `/dashboard` if `onboardingCompleted=true` and accessing `/onboarding`
  - Show loading spinner while checking onboarding status
  - _Requirements: US-1.2, US-1.4, US-5.4_

- [ ]* 3.2 Write property test for ProtectedRoute navigation lock
  - **Property 1: Navigation lock during onboarding**
  - **Validates: Requirements US-1.2, US-1.4**
  - Test that all protected routes redirect to `/onboarding` when `onboardingCompleted=false`
  - Test that `/onboarding` redirects to `/dashboard` when `onboardingCompleted=true`

---

### 4. Update onboardingService

- [x] 4.1 Add chat-based onboarding methods to `frontend/src/services/onboardingService.ts`
  - Add `getProgress()` method that calls `GET /api/v1/onboarding/progress`
  - Add `sendOnboardingMessage(message, currentState)` method that calls `POST /api/v1/chat/onboarding`
  - Update return types to match new interfaces
  - _Requirements: US-2.6, US-2.7, US-4.6_

- [x] 4.2 Write unit tests for onboardingService methods
  - Test `getProgress()` calls correct endpoint and parses response
  - Test `sendOnboardingMessage()` sends correct payload
  - Test error handling for network failures
  - _Requirements: US-2.6, US-2.7_

---

### 5. Create OnboardingProgressBar Component

- [x] 5.1 Implement OnboardingProgressBar component
  - Create `frontend/src/components/onboarding/OnboardingProgressBar.tsx`
  - Accept props: `currentState`, `totalStates`, `completionPercentage`, `stateMetadata`, `completedStates`
  - Render progress bar with percentage
  - Display "Step X of 9" text
  - Display current state name and description from metadata
  - Render list of all 9 states with checkmarks for completed, highlight for current, gray for upcoming
  - Style with Tailwind CSS
  - _Requirements: US-2.6, US-4.1, US-4.2, US-4.3, US-4.4, US-4.5_

- [x]* 5.2 Write property test for progress calculation
  - **Property 4: Progress calculation accuracy**
  - **Validates: Requirements US-2.6, US-4.1**
  - Test that for any state 1-9, percentage equals `(state / 9) * 100`
  - Test that step text shows "Step n of 9"

- [x]* 5.3 Write property test for state list rendering
  - **Property 6: State list rendering**
  - **Validates: Requirements US-4.2, US-4.3, US-4.4, US-4.5**
  - Test that completed states have checkmarks
  - Test that current state is highlighted
  - Test that upcoming states are grayed out

---

### 6. Create OnboardingChatPage Component

- [x] 6.1 Implement OnboardingChatPage component
  - Create `frontend/src/components/pages/OnboardingChatPage.tsx`
  - Use `useState` for messages, currentState, loading, error
  - Use `useEffect` to fetch progress on mount via `onboardingService.getProgress()`
  - Render `OnboardingProgressBar` with progress data
  - Render chat interface with message list
  - Render message input component
  - Implement `sendMessage()` function that calls `onboardingService.sendOnboardingMessage()`
  - Handle `state_updated` flag in response to update progress
  - Redirect to `/dashboard` when `is_complete = true`
  - Display welcome message on first load
  - _Requirements: US-2.1, US-2.2, US-2.3, US-2.4, US-2.6, US-2.7_

- [x]* 6.2 Write unit tests for OnboardingChatPage
  - Test progress is fetched on mount
  - Test messages are sent correctly
  - Test state updates after agent response
  - Test redirect to dashboard on completion
  - Test error handling for failed API calls
  - _Requirements: US-2.1, US-2.6_

- [x] 6.3 Write property test for state metadata display
  - **Property 5: State metadata display**
  - **Validates: Requirements US-2.7**
  - Test that displayed state name matches backend metadata
  - Test that displayed description matches backend metadata

- [x] 6.4 Write property test for questions presented
  - **Property 7: Questions presented for all states**
  - **Validates: Requirements US-2.3**
  - Test that for any state 1-9, question content is displayed

---

### 7. Checkpoint - Verify Onboarding Chat Interface

- [x] 7. Ensure all tests pass, ask the user if questions arise.

---

### 8. Enhance MainLayout and Header Components

- [x] 8.1 Update MainLayout to pass onboarding status to Header
  - Import `useUser` hook
  - Get `onboardingCompleted` from context
  - Pass `onboardingCompleted` prop to `Header` component
  - _Requirements: US-3.1_

- [x] 8.2 Update Header component to disable navigation during onboarding
  - Accept `onboardingCompleted` prop
  - Define navigation items with `requiresOnboarding` flag
  - Disable items where `requiresOnboarding=true` and `onboardingCompleted=false`
  - Add tooltip "Complete onboarding to unlock" to disabled items
  - Style disabled items with gray color and `cursor-not-allowed`
  - Keep "Onboarding" and "Logout" items enabled
  - _Requirements: US-3.1, US-3.2, US-3.3, US-3.4, US-3.5_

- [x] 8.3 Write property test for navigation lock in UI
  - **Property 1: Navigation lock during onboarding** (UI portion)
  - **Validates: Requirements US-3.1, US-3.3**
  - Test that clicking disabled items doesn't change route
  - Test that only "Onboarding" and "Logout" are enabled during onboarding

- [x]* 8.4 Write property test for disabled item tooltips
  - **Property 3: Disabled items show tooltip**
  - **Validates: Requirements US-3.2**
  - Test that hovering over disabled items shows tooltip
  - Test tooltip contains "Complete onboarding to unlock"

---

### 9. Update ChatPage Component

- [x] 9.1 Remove agent selector from ChatPage
  - Remove `AgentSelector` component import and usage
  - Remove `selectedAgent` state
  - Update `sendMessage()` to not pass `agentType` parameter
  - Update UI to remove agent selector section
  - _Requirements: US-6.2_

- [x] 9.2 Add error handling for 403 responses
  - Wrap `sendMessage()` in try-catch
  - Check for 403 status code
  - Check for `ONBOARDING_REQUIRED` error code
  - Redirect to `/onboarding` if onboarding incomplete
  - Display error message from backend
  - _Requirements: US-6.5_

- [x]* 9.3 Write unit tests for ChatPage updates
  - Test agent selector is not rendered
  - Test 403 error redirects to `/onboarding`
  - Test error message is displayed
  - _Requirements: US-6.2, US-6.5_

---

### 10. Update chatService

- [x] 10.1 Update chatService to handle post-onboarding chat
  - Update `sendMessage()` to omit `agentType` parameter or force to "general"
  - Add structured error handling for 403 responses
  - Return error details (status, code, message, redirect) for UI handling
  - _Requirements: US-6.1_

- [x] 10.2 Write unit tests for chatService error handling
  - Test 403 error is caught and structured correctly
  - Test error details are returned to caller
  - _Requirements: US-6.5_

---

### 11. Update App.tsx Routing

- [x] 11.1 Update routing to enforce onboarding flow
  - Add `requireOnboardingComplete={false}` to `/onboarding` route
  - Add `requireOnboardingComplete={true}` to all other protected routes (dashboard, chat, meals, workouts, voice)
  - Create `RootRedirect` component that checks auth and onboarding status
  - Update root path `/` to use `RootRedirect`
  - Create `NotFoundRedirect` component for 404 handling
  - Update 404 fallback to use `NotFoundRedirect`
  - _Requirements: US-1.1, US-1.2, US-1.4, US-5.4_

- [ ]* 11.2 Write integration tests for routing
  - Test registration redirects to `/onboarding`
  - Test incomplete onboarding redirects protected routes to `/onboarding`
  - Test complete onboarding allows access to all routes
  - Test `/onboarding` redirects to `/dashboard` after completion
  - _Requirements: US-1.1, US-1.2, US-5.4_

---

### 12. Checkpoint - Verify Navigation Lock and Routing

- [ ] 12. Ensure all tests pass, ask the user if questions arise.

---

### 13. Add Error Handling and Loading States

- [ ] 13.1 Implement error handling in OnboardingChatPage
  - Add error state for progress fetch failures
  - Add retry logic with exponential backoff
  - Display error banner with retry button
  - Handle state mismatch errors by refreshing progress
  - Handle authentication expiry with redirect to login
  - _Requirements: Error Handling section_

- [ ] 13.2 Add loading states to OnboardingChatPage
  - Show loading spinner while fetching progress
  - Show loading indicator while sending message
  - Disable input while loading
  - Show "Syncing your progress..." during state updates
  - _Requirements: NFR-1, NFR-2_

- [ ]* 13.3 Write unit tests for error handling
  - Test retry logic for network errors
  - Test error banner display
  - Test state synchronization on errors
  - _Requirements: NFR-4_

---

### 14. Implement Property-Based Tests

- [ ]* 14.1 Write property test for helpful message on locked routes
  - **Property 2: Helpful message on locked routes**
  - **Validates: Requirements US-1.3**
  - Test that accessing protected routes during onboarding shows helpful message

- [ ]* 14.2 Write property test for post-onboarding access
  - **Property 8: Post-onboarding access**
  - **Validates: Requirements US-5.2, US-5.3**
  - Test that all navigation items are enabled after onboarding
  - Test that all protected routes are accessible after onboarding

---

### 15. Implement Example-Based Tests

- [ ]* 15.1 Write example tests for onboarding flow
  - Test registration redirect (Example 1)
  - Test chat interface display (Example 2)
  - Test welcome message (Example 3)
  - Test text input present (Example 4)
  - Test onboarding menu active (Example 5)
  - Test logout functional (Example 6)
  - Test progress endpoint called (Example 7)
  - Test completion redirect (Example 8)
  - Test onboarding redirect after completion (Example 9)
  - Test onboarding completed flag (Example 10)
  - Test post-onboarding chat endpoint (Example 11)
  - Test no agent selector (Example 12)
  - Test 403 error handling (Example 13)
  - _Requirements: All user stories_

---

### 16. Add Accessibility Features

- [ ] 16.1 Implement accessibility features
  - Add ARIA labels to progress bar
  - Add ARIA labels to disabled navigation items
  - Ensure keyboard navigation works for all interactive elements
  - Add focus management for input after state transitions
  - Ensure color contrast meets WCAG AA standards
  - Test with screen reader
  - _Requirements: NFR-3_

- [ ]* 16.2 Write accessibility tests
  - Test ARIA labels are present
  - Test keyboard navigation works
  - Test focus management
  - _Requirements: NFR-3_

---

### 17. Performance Optimization

- [ ] 17.1 Optimize component performance
  - Lazy load `OnboardingChatPage` with `React.lazy()`
  - Memoize `OnboardingProgressBar` with `React.memo()`
  - Debounce message input to reduce re-renders
  - Cache progress data for 30 seconds
  - _Requirements: NFR-1, Performance Targets_

- [ ]* 17.2 Write performance tests
  - Test initial load time < 1 second
  - Test progress fetch < 200ms
  - Test state update < 100ms
  - _Requirements: Performance Targets_

---

### 18. Integration Testing

- [ ]* 18.1 Write end-to-end tests for complete onboarding flow
  - Test user registers and is redirected to `/onboarding`
  - Test progress loads and displays state 1
  - Test user sends message and state updates
  - Test user completes all 9 states
  - Test user is redirected to `/dashboard`
  - Test navigation unlocks after completion
  - _Requirements: All user stories_

- [ ]* 18.2 Write end-to-end tests for navigation lock
  - Test user with incomplete onboarding tries to access protected routes
  - Test all protected routes redirect to `/onboarding`
  - Test navigation items are disabled
  - Test tooltips show on hover
  - Test clicking disabled items does nothing
  - Test user completes onboarding and navigation unlocks
  - _Requirements: US-1.2, US-1.4, US-3.1, US-3.2, US-3.3_

---

### 19. Documentation and Cleanup

- [ ] 19.1 Update component documentation
  - Add JSDoc comments to all new components
  - Add prop type documentation
  - Add usage examples in comments
  - Update README with onboarding flow explanation

- [ ] 19.2 Remove old onboarding components
  - Delete `Step1FitnessLevel.tsx` through `Step12Confirmation.tsx`
  - Delete old `OnboardingPage.tsx` (form-based)
  - Remove unused imports
  - Update any references to old components

- [ ] 19.3 Update environment configuration
  - Add any new environment variables if needed
  - Update `.env.example` with new variables
  - Document configuration in README

---

### 20. Final Checkpoint - Complete Testing and Verification

- [ ] 20. Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- All tasks assume the backend is fully implemented and validated

## Testing Configuration

**Property-Based Testing**:
- Library: `fast-check` with React Testing Library
- Minimum iterations: 100 per property test
- Tag format: `// Feature: frontend-onboarding-integration, Property N: [property text]`

**Unit Testing**:
- Library: Vitest with React Testing Library
- Coverage target: 80%+ for new components
- Focus on component behavior, not implementation details

**Integration Testing**:
- Library: Vitest with React Testing Library
- Test complete user flows
- Mock API responses

**End-to-End Testing**:
- Library: Playwright or Cypress
- Test real user interactions
- Use test database

## Estimated Time

- **Phase 1** (Tasks 1-4): Type definitions and services - 2-3 hours
- **Phase 2** (Tasks 5-7): Onboarding chat interface - 4-5 hours
- **Phase 3** (Tasks 8-12): Navigation lock and routing - 3-4 hours
- **Phase 4** (Tasks 13-17): Error handling, testing, optimization - 4-5 hours
- **Phase 5** (Tasks 18-20): Integration testing and cleanup - 2-3 hours

**Total Estimated Time**: 15-20 hours

---

**Document Version**: 1.0  
**Created**: 2026-02-14  
**Status**: Ready for Implementation
