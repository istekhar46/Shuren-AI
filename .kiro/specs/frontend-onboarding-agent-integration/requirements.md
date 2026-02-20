# Frontend Onboarding Agent Integration - Requirements

## 1. Overview

This spec defines the frontend modifications required to integrate with the new specialized onboarding agent system implemented in the backend. The backend has been fully implemented with 5 specialized AI agents that guide users through onboarding via conversational chat, replacing the previous form-based approach.

### Background

The backend now implements the onboarding agent system as specified in `docs/technichal/onboarding_agent_system_trd.md`:
- 5 specialized agents (Fitness Assessment, Goal Setting, Workout Planning, Diet Planning, Scheduling)
- 9 onboarding states (0-9) mapped to agents
- Conversational data collection with streaming responses
- Plan generation and approval workflow
- Agent context passed between agents

The frontend currently has:
- Form-based onboarding (OnboardingPage.tsx) with 12 steps
- Chat-based onboarding (OnboardingChatPage.tsx) with basic streaming
- Misalignment with backend's 9-state system
- No UI for plan display and approval

## 2. Goals

1. **Align frontend with backend architecture**: Update to 9-state system and agent-based flow
2. **Replace form-based onboarding**: Deprecate old 12-step form flow
3. **Enhance chat interface**: Add agent context display, plan preview, and approval UI
4. **Improve streaming integration**: Handle state updates and progress from backend
5. **Maintain user experience**: Ensure smooth, intuitive onboarding flow

## 3. User Stories

### US-1: Agent-Based Onboarding Flow
**As a** new user  
**I want to** complete onboarding through conversation with specialized AI agents  
**So that** I can provide my information naturally and receive personalized guidance

**Acceptance Criteria:**
- AC-1.1: User sees chat interface when starting onboarding
- AC-1.2: Current agent and step are clearly displayed
- AC-1.3: Progress bar shows completion percentage (0-100%)
- AC-1.4: User can send messages and receive streaming responses
- AC-1.5: Conversation history is preserved during onboarding

### US-2: Agent Context Display
**As a** user going through onboarding  
**I want to** know which specialized agent I'm talking to  
**So that** I understand what information is being collected

**Acceptance Criteria:**
- AC-2.1: Agent name is displayed (e.g., "Fitness Assessment Agent")
- AC-2.2: Agent description explains their role
- AC-2.3: Current state number and name are shown (e.g., "Step 1 of 9: Fitness Level")
- AC-2.4: Agent changes are visually indicated when state advances

### US-3: Plan Display and Approval
**As a** user receiving a workout or meal plan  
**I want to** see the plan in a structured, readable format  
**So that** I can review it before approving

**Acceptance Criteria:**
- AC-3.1: Workout plans display with days, exercises, sets, reps
- AC-3.2: Meal plans display with calories, macros, sample meals
- AC-3.3: Plans are shown in a card/modal separate from chat messages
- AC-3.4: User can approve plan with clear "Approve" button
- AC-3.5: User can request modifications via chat
- AC-3.6: Approved plans are visually confirmed

### US-4: State Progression
**As a** user completing onboarding steps  
**I want to** see my progress update automatically  
**So that** I know how far along I am

**Acceptance Criteria:**
- AC-4.1: Progress bar updates when state advances
- AC-4.2: Completed states are marked with checkmarks
- AC-4.3: Current state is highlighted
- AC-4.4: State transitions are smooth and clear
- AC-4.5: User is notified when onboarding is complete

### US-5: Streaming Response Handling
**As a** user chatting with onboarding agents  
**I want to** see responses appear in real-time  
**So that** the conversation feels natural and responsive

**Acceptance Criteria:**
- AC-5.1: Agent responses stream word-by-word
- AC-5.2: Streaming indicator shows agent is typing
- AC-5.3: State updates are processed from streaming response
- AC-5.4: Progress updates automatically after state changes
- AC-5.5: Errors during streaming are handled gracefully

### US-6: Onboarding Completion
**As a** user finishing onboarding  
**I want to** be redirected to the dashboard  
**So that** I can start using the app

**Acceptance Criteria:**
- AC-6.1: User is notified when all states are complete
- AC-6.2: "Complete Onboarding" button appears
- AC-6.3: Clicking button calls `/onboarding/complete` endpoint
- AC-6.4: User is redirected to dashboard on success
- AC-6.5: Profile is created and locked

## 4. Technical Requirements

### TR-1: State Management
- TR-1.1: Update onboarding state from 12 steps to 9 states
- TR-1.2: Track current_state, completed_states, completion_percentage
- TR-1.3: Store agent_type for current state
- TR-1.4: Handle state transitions from streaming responses

### TR-2: API Integration
- TR-2.1: Use `/onboarding/progress` for initial load
- TR-2.2: Use `/chat/onboarding-stream` for chat messages
- TR-2.3: Parse state_updated, new_state, progress from stream
- TR-2.4: Call `/onboarding/complete` when can_complete is true

### TR-3: Component Architecture
- TR-3.1: Deprecate OnboardingPage.tsx (form-based)
- TR-3.2: Enhance OnboardingChatPage.tsx as primary onboarding UI
- TR-3.3: Create PlanPreviewCard component for workout/meal plans
- TR-3.4: Create AgentHeader component for agent context display
- TR-3.5: Update OnboardingProgressBar for 9-state system

### TR-4: Type Definitions
- TR-4.1: Update OnboardingProgress interface to match backend
- TR-4.2: Add OnboardingChatResponse with state_updated, new_state
- TR-4.3: Add WorkoutPlan and MealPlan types
- TR-4.4: Add AgentType enum matching backend

### TR-5: Streaming Enhancements
- TR-5.1: Handle progress object in streaming response
- TR-5.2: Update UI when state_updated is true
- TR-5.3: Detect plan generation in response content
- TR-5.4: Show plan preview when plan is detected

## 5. Non-Functional Requirements

### NFR-1: Performance
- NFR-1.1: Streaming responses render smoothly without lag
- NFR-1.2: State updates don't cause UI flicker
- NFR-1.3: Progress bar animations are smooth

### NFR-2: Usability
- NFR-2.1: Chat interface is intuitive and familiar
- NFR-2.2: Plan previews are easy to read and understand
- NFR-2.3: Progress is always visible
- NFR-2.4: Error messages are clear and actionable

### NFR-3: Accessibility
- NFR-3.1: All interactive elements are keyboard accessible
- NFR-3.2: Screen readers can navigate onboarding flow
- NFR-3.3: Color contrast meets WCAG AA standards
- NFR-3.4: Focus indicators are visible

### NFR-4: Compatibility
- NFR-4.1: Works on modern browsers (Chrome, Firefox, Safari, Edge)
- NFR-4.2: Responsive design for mobile and desktop
- NFR-4.3: Graceful degradation if streaming fails

## 6. Out of Scope

- Voice-based onboarding (future enhancement)
- Editing completed onboarding data (requires separate feature)
- Multi-language support (future enhancement)
- Onboarding analytics dashboard (separate feature)

## 7. Dependencies

### Backend Dependencies (Already Implemented)
- ✅ Onboarding agent system with 5 specialized agents
- ✅ `/onboarding/progress` endpoint
- ✅ `/chat/onboarding-stream` endpoint with SSE
- ✅ `/onboarding/complete` endpoint
- ✅ Agent context and state management
- ✅ Workout and meal plan generation services

### Frontend Dependencies
- React 18+ with hooks
- TypeScript
- Tailwind CSS for styling
- Existing chat components (MessageList, MessageInput)
- Existing useChat hook (needs enhancement)

## 8. Success Criteria

1. **Functional Completeness**: All 9 onboarding states can be completed via chat
2. **Agent Integration**: All 5 agents are accessible and functional
3. **Plan Approval**: Users can review and approve workout/meal plans
4. **State Tracking**: Progress updates correctly as user advances
5. **User Experience**: Onboarding feels natural and conversational
6. **Error Handling**: All error cases are handled gracefully
7. **Testing**: All user stories have passing tests

## 9. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Streaming connection failures | High | Medium | Implement retry logic and fallback to non-streaming |
| Plan parsing from text responses | Medium | Low | Use structured responses from backend |
| State synchronization issues | High | Low | Always fetch fresh state from backend |
| User confusion with chat interface | Medium | Medium | Clear instructions and agent descriptions |
| Mobile responsiveness issues | Medium | Low | Test on multiple devices early |

## 10. Timeline Estimate

- **Phase 1**: Type definitions and API updates (1-2 days)
- **Phase 2**: Component refactoring and new components (2-3 days)
- **Phase 3**: Streaming enhancements and state management (2-3 days)
- **Phase 4**: Plan preview and approval UI (2-3 days)
- **Phase 5**: Testing and bug fixes (2-3 days)

**Total Estimate**: 9-14 days

## 11. References

- Backend TRD: `docs/technichal/onboarding_agent_system_trd.md`
- Backend Implementation: `backend/app/agents/onboarding/`
- Backend API: `backend/app/api/v1/endpoints/onboarding.py`
- Backend Chat API: `backend/app/api/v1/endpoints/chat.py`
- Current Frontend: `frontend/src/pages/OnboardingChatPage.tsx`
