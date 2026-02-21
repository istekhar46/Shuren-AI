# Frontend Onboarding Agent Integration - Tasks

## 1. Type Definitions and Interfaces

- [x] 1.1 Create AgentType enum in onboarding.types.ts
- [x] 1.2 Update OnboardingProgress interface to match backend response
- [x] 1.3 Add OnboardingStreamChunk interface for streaming responses
- [x] 1.4 Create WorkoutPlan, WorkoutDay, and Exercise interfaces
- [x] 1.5 Create MealPlan, MacroBreakdown, and SampleMeal interfaces
- [x] 1.6 Add OnboardingCompleteResponse interface
- [x] 1.7 Update StateMetadata interface with agent field

## 2. Service Layer Updates

- [x] 2.1 Update onboardingService.streamOnboardingMessage() to handle new response format
  - [x] 2.1.1 Parse state_updated, new_state, and progress from stream
  - [x] 2.1.2 Handle done event with complete data
  - [x] 2.1.3 Add proper error handling for SSE connection
- [x] 2.2 Create planDetectionService.ts
  - [x] 2.2.1 Implement detectWorkoutPlan() method
  - [x] 2.2.2 Implement detectMealPlan() method
  - [x] 2.2.3 Add plan parsing utilities (if needed)
- [x] 2.3 Add retry logic to onboardingService for network errors
- [x] 2.4 Update error handling to match backend error responses

## 3. Custom Hook: useOnboardingChat

- [x] 3.1 Create useOnboardingChat.ts hook file
- [x] 3.2 Implement state management
  - [x] 3.2.1 Add progress state (currentState, completedStates, completionPercentage)
  - [x] 3.2.2 Add agent state (currentAgent, agentDescription, stateMetadata)
  - [x] 3.2.3 Add chat state (messages, isStreaming, error)
  - [x] 3.2.4 Add plan state (pendingPlan, planType, showPlanPreview)
- [x] 3.3 Implement fetchProgress() on mount
- [x] 3.4 Implement sendMessage() with streaming
  - [x] 3.4.1 Add user message to state
  - [x] 3.4.2 Create assistant placeholder with isStreaming: true
  - [x] 3.4.3 Handle chunk updates
  - [x] 3.4.4 Handle completion with state updates
  - [x] 3.4.5 Detect plans in response
- [x] 3.5 Implement approvePlan() method
- [x] 3.6 Implement modifyPlan() method
- [x] 3.7 Implement completeOnboarding() method
- [x] 3.8 Add error recovery logic

## 4. Component: AgentHeader

- [x] 4.1 Create AgentHeader.tsx component
- [x] 4.2 Define AgentHeaderProps interface
- [x] 4.3 Implement agent icon display (different icon per agent type)
- [x] 4.4 Display agent name and description
- [x] 4.5 Show current state indicator (e.g., "Step 1 of 9")
- [x] 4.6 Add Tailwind styling
- [x] 4.7 Make header sticky at top
- [x] 4.8 Add smooth transitions for agent changes

## 5. Component: OnboardingProgressBar Updates

- [x] 5.1 Update OnboardingProgressBar.tsx for 9-state system
- [x] 5.2 Update props to use new OnboardingProgress interface
- [x] 5.3 Display all 9 states with names
- [x] 5.4 Show checkmarks for completed states
- [x] 5.5 Highlight current state
- [x] 5.6 Add completion percentage display
- [x] 5.7 Make responsive (sidebar on desktop, collapsible on mobile)
- [x] 5.8 Add smooth animations for state transitions

## 6. Component: PlanPreviewCard

- [x] 6.1 Create PlanPreviewCard.tsx component
- [x] 6.2 Define PlanPreviewCardProps interface
- [x] 6.3 Implement conditional rendering (workout vs meal plan)
- [x] 6.4 Add modal/slide-in panel layout
- [x] 6.5 Add close button (X)
- [x] 6.6 Add "Approve Plan" button
- [x] 6.7 Add "Request Changes" button with text input
- [x] 6.8 Make scrollable for long plans
- [x] 6.9 Add Tailwind styling

## 7. Component: WorkoutPlanPreview

- [x] 7.1 Create WorkoutPlanPreview.tsx subcomponent
- [x] 7.2 Display plan summary (frequency, location, duration)
- [x] 7.3 Display equipment list
- [x] 7.4 Render day-by-day breakdown
- [x] 7.5 Display exercises with sets, reps, rest
- [x] 7.6 Add exercise notes if present
- [x] 7.7 Format for readability
- [x] 7.8 Add Tailwind styling

## 8. Component: MealPlanPreview

- [x] 8.1 Create MealPlanPreview.tsx subcomponent
- [x] 8.2 Display calorie target
- [x] 8.3 Display macro breakdown (protein, carbs, fats)
- [x] 8.4 Render sample meals list
- [x] 8.5 Show meal nutrition info (calories, macros per meal)
- [x] 8.6 Display meal timing suggestions
- [x] 8.7 Note dietary restrictions
- [x] 8.8 Add Tailwind styling

## 9. Page: OnboardingChatPage Updates

- [x] 9.1 Update OnboardingChatPage.tsx to use useOnboardingChat hook
- [x] 9.2 Replace existing state management with hook
- [x] 9.3 Add AgentHeader component
- [x] 9.4 Update OnboardingProgressBar with new props
- [x] 9.5 Add PlanPreviewCard with conditional rendering
- [x] 9.6 Handle plan approval flow
- [x] 9.7 Handle plan modification flow
- [x] 9.8 Add "Complete Onboarding" button when canComplete is true
- [x] 9.9 Implement completeOnboarding() and redirect to dashboard
- [x] 9.10 Update error handling UI
- [x] 9.11 Update loading states

## 10. Deprecate Old Onboarding Flow

- [x] 10.1 Add deprecation notice to OnboardingPage.tsx
- [x] 10.2 Update routing to default to OnboardingChatPage
- [x] 10.3 Remove old step components (Step1-Step12)
- [x] 10.4 Clean up unused types in onboarding.types.ts
- [x] 10.5 Remove unused onboardingService methods

## 11. Styling and Responsiveness

- [x] 11.1 Add responsive layout for mobile (<768px)
- [x] 11.2 Add responsive layout for tablet (768px-1024px)
- [x] 11.3 Add responsive layout for desktop (>1024px)
- [x] 11.4 Test on multiple screen sizes
- [x] 11.5 Add smooth animations for state transitions
- [x] 11.6 Add loading spinners and skeletons
- [x] 11.7 Ensure color contrast meets WCAG AA standards

## 12. Accessibility

- [x] 12.1 Add ARIA labels to all interactive elements
- [ ] 12.2 Implement keyboard navigation
  - [ ] 12.2.1 Tab through all elements
  - [ ] 12.2.2 Enter to send message
  - [x] 12.2.3 Escape to close plan preview
- [x] 12.3 Add live regions for streaming messages
- [x] 12.4 Add descriptive alt text for agent icons
- [x] 12.5 Ensure focus indicators are visible
- [ ] 12.6 Test with screen reader (NVDA/JAWS)

## 13. Testing

### Unit Tests
- [x] 13.1 Write tests for useOnboardingChat hook
  - [x] 13.1.1 Test fetchProgress on mount
  - [x] 13.1.2 Test sendMessage with streaming
  - [x] 13.1.3 Test state updates from streaming response
  - [x] 13.1.4 Test plan detection
  - [x] 13.1.5 Test approvePlan
  - [x] 13.1.6 Test modifyPlan
  - [x] 13.1.7 Test error handling
- [x] 13.2 Write tests for AgentHeader component
- [x] 13.3 Write tests for OnboardingProgressBar component
- [x] 13.4 Write tests for PlanPreviewCard component
- [x] 13.5 Write tests for WorkoutPlanPreview component
- [x] 13.6 Write tests for MealPlanPreview component

### Property-Based Tests
- [x] 13.7 Write property test for state consistency
- [x] 13.8 Write property test for progress monotonicity
- [x] 13.9 Write property test for message ordering
- [x] 13.10 Write property test for plan approval idempotency
- [x] 13.11 Write property test for streaming completeness

### Integration Tests
- [x] 13.12 Test complete onboarding flow (all 9 states)
- [x] 13.13 Test plan approval workflow
- [x] 13.14 Test plan modification workflow
- [ ] 13.15 Test error recovery scenarios
- [ ] 13.16 Test state synchronization

### E2E Tests
- [x] 13.17 Test new user completes onboarding
- [x] 13.18 Test user approves workout plan
- [x] 13.19 Test user requests meal plan changes
- [x] 13.20 Test user completes onboarding and redirects to dashboard

## 14. Documentation

- [x] 14.1 Update README with new onboarding flow
- [x] 14.2 Document useOnboardingChat hook API
- [x] 14.3 Document component props and usage
- [ ] 14.4 Add inline code comments
- [ ] 14.5 Create user guide for onboarding flow
- [ ] 14.6 Document migration from old flow

## 15. Deployment and Monitoring

- [ ] 15.1 Deploy to staging environment
- [ ] 15.2 QA testing on staging
- [ ] 15.3 Fix any bugs found in QA
- [ ] 15.4 Deploy to production
- [ ] 15.5 Monitor error rates
- [ ] 15.6 Monitor onboarding completion rates
- [ ] 15.7 Monitor streaming connection failures
- [ ] 15.8 Set up alerts for critical errors
