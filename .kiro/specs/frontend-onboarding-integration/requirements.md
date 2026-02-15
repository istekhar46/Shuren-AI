# Frontend Onboarding Integration - Requirements

## 1. Overview

This spec addresses the frontend modifications required to align with the refined product requirements documented in `docs/product/refined_product_requirement_shuren.md`. The backend implementation is complete and validated (see `validation_report.md`), but the frontend needs significant updates to implement:

1. Mandatory onboarding with navigation lock
2. Chat-based onboarding interface (replacing form-based approach)
3. Progress indicators using backend state metadata
4. Proper routing between `/chat/onboarding` and `/chat` endpoints
5. Post-onboarding navigation unlock

## 2. Problem Statement

**Current State**:
- Frontend has form-based onboarding with 12 steps (Step1FitnessLevel.tsx through Step12Confirmation.tsx)
- No navigation lock enforcement - users can access all routes after login
- Onboarding uses direct API calls to save step data
- Chat page exists but doesn't integrate with onboarding flow
- No distinction between onboarding chat and post-onboarding chat

**Desired State**:
- Chat-based onboarding interface with specialized agents (9 states)
- All navigation locked until onboarding complete (except `/onboarding`)
- Progress indicators driven by backend `STATE_METADATA`
- Separate chat endpoints: `/chat/onboarding` during onboarding, `/chat` post-onboarding
- Automatic redirect to `/onboarding` after registration
- Navigation unlocks automatically when `onboarding_completed = true`

## 3. User Stories

### US-1: Mandatory Onboarding After Registration
**As a** new user  
**I want to** be automatically directed to onboarding after registration  
**So that** I complete my profile setup before accessing the app

**Acceptance Criteria**:
- After successful registration, user is redirected to `/onboarding`
- User cannot access `/dashboard`, `/meals`, `/workouts`, `/voice`, or `/chat` until onboarding complete
- Attempting to access locked routes shows helpful message: "Complete onboarding to unlock full access"
- User can only access `/onboarding` route during onboarding

### US-2: Chat-Based Onboarding Interface
**As a** new user  
**I want to** complete onboarding through a conversational chat interface  
**So that** the process feels natural and guided

**Acceptance Criteria**:
- Onboarding page displays a chat interface (not forms)
- Welcome message explains the onboarding process
- Each state presents clear questions from specialized agents
- User responds via text input
- Agent validates, saves data, and moves to next state
- Progress bar shows "Step X of 9" with percentage
- State names displayed from backend `STATE_METADATA`

### US-3: Navigation Lock During Onboarding
**As a** user in onboarding  
**I want** navigation to be locked  
**So that** I complete the required setup before exploring the app

**Acceptance Criteria**:
- Sidebar/menu items are disabled during onboarding
- Disabled items show tooltip: "Complete onboarding to unlock"
- Clicking disabled items does nothing or shows modal with progress
- Only "Onboarding" menu item is active
- Logout button remains functional

### US-4: Progress Indicators
**As a** user in onboarding  
**I want to** see my progress clearly  
**So that** I know how much is left to complete

**Acceptance Criteria**:
- Progress bar shows percentage: `(current_step / 9) * 100`
- Current state name displayed prominently
- List of completed states with checkmarks
- Current state highlighted
- Upcoming states visible but grayed out
- Progress data fetched from `GET /api/v1/onboarding/progress` endpoint

### US-5: Automatic Navigation Unlock
**As a** user who completed onboarding  
**I want** navigation to unlock automatically  
**So that** I can access all features without manual intervention

**Acceptance Criteria**:
- After completing state 9, user is redirected to `/dashboard`
- All navigation items become enabled
- User can access `/chat`, `/meals`, `/workouts`, `/voice`, `/dashboard`
- Attempting to access `/onboarding` redirects to `/dashboard` with message: "Onboarding already completed"
- User's `onboarding_completed` flag is `true`

### US-6: Post-Onboarding Chat Access
**As a** completed user  
**I want to** access the general chat  
**So that** I can ask fitness questions and get guidance

**Acceptance Criteria**:
- Chat page uses `POST /api/v1/chat` endpoint (not `/chat/onboarding`)
- Only general agent is available (no agent selector)
- Chat history is saved and persisted
- User can ask about workouts, meals, schedules, exercises
- Error handling for 403 responses (if onboarding incomplete)

## 4. Functional Requirements

### FR-1: Update ProtectedRoute Component
**Priority**: High  
**Description**: Enhance `ProtectedRoute` to check `onboarding_completed` flag

**Requirements**:
- Add `requireOnboardingComplete` prop (default: `true`)
- Fetch user profile with `onboarding_completed` flag
- If `onboarding_completed = false` and `requireOnboardingComplete = true`, redirect to `/onboarding`
- If `onboarding_completed = true` and accessing `/onboarding`, redirect to `/dashboard`
- Show loading spinner while checking onboarding status

### FR-2: Create OnboardingChatPage Component
**Priority**: High  
**Description**: Replace form-based onboarding with chat-based interface

**Requirements**:
- Display chat interface similar to `ChatPage`
- Fetch onboarding state from `GET /api/v1/onboarding/progress`
- Display progress bar with current step and percentage
- Display state metadata (name, description) from backend
- Send messages to `POST /api/v1/chat/onboarding` endpoint
- Handle `state_updated` flag in response to update progress
- Redirect to `/dashboard` when `is_complete = true`
- No agent selector (backend routes to correct agent)

### FR-3: Update MainLayout for Navigation Lock
**Priority**: High  
**Description**: Disable navigation items during onboarding

**Requirements**:
- Fetch user's `onboarding_completed` flag
- If `false`, disable all nav items except "Onboarding" and "Logout"
- Add tooltip to disabled items: "Complete onboarding to unlock"
- Style disabled items with gray color and cursor-not-allowed
- Re-enable all items when `onboarding_completed = true`

### FR-4: Update ChatPage for Post-Onboarding
**Priority**: High  
**Description**: Modify chat page to use correct endpoint and enforce access control

**Requirements**:
- Use `POST /api/v1/chat` endpoint (not `/chat/onboarding`)
- Remove agent selector (only general agent available)
- Handle 403 error with redirect to `/onboarding` if incomplete
- Display helpful error message from backend
- Save conversation history to database

### FR-5: Update App.tsx Routing
**Priority**: High  
**Description**: Update routing to enforce onboarding flow

**Requirements**:
- Add `requireOnboardingComplete={false}` to `/onboarding` route
- Add `requireOnboardingComplete={true}` to all other protected routes
- Redirect from `/` to `/onboarding` if incomplete, else `/dashboard`
- Update 404 fallback to check onboarding status

### FR-6: Create OnboardingProgressBar Component
**Priority**: Medium  
**Description**: Reusable progress indicator component

**Requirements**:
- Display "Step X of 9" with percentage
- Visual progress bar with animation
- List of states with checkmarks for completed
- Current state highlighted
- Upcoming states grayed out
- Fetch state metadata from backend

### FR-7: Update UserContext
**Priority**: Medium  
**Description**: Add `onboarding_completed` flag to user context

**Requirements**:
- Fetch user profile on login/registration
- Store `onboarding_completed` flag in context
- Provide `refreshUser()` method to refetch profile
- Update flag when onboarding completes

### FR-8: Create OnboardingGuard Component
**Priority**: Low  
**Description**: Modal/banner to prevent navigation during onboarding

**Requirements**:
- Show modal when user tries to access locked route
- Display current progress and remaining steps
- Provide "Continue Onboarding" button to return to `/onboarding`
- Optional: Allow "Skip for now" with warning (if product allows)

## 5. Non-Functional Requirements

### NFR-1: Performance
- Onboarding state fetch < 100ms
- Progress updates in real-time (no page refresh)
- Smooth transitions between states
- No flickering during navigation lock checks

### NFR-2: User Experience
- Clear, friendly messaging throughout onboarding
- Helpful error messages from backend displayed properly
- Loading states for all async operations
- Responsive design for mobile and desktop

### NFR-3: Accessibility
- Keyboard navigation support
- Screen reader friendly progress indicators
- ARIA labels for disabled navigation items
- Focus management during state transitions

### NFR-4: Error Handling
- Graceful handling of network errors
- Retry logic for failed API calls
- Clear error messages for validation failures
- Fallback UI for missing state metadata

## 6. Technical Constraints

### TC-1: Backend API Compatibility
- Must use existing backend endpoints:
  - `GET /api/v1/onboarding/progress` - Get current state
  - `POST /api/v1/chat/onboarding` - Onboarding chat
  - `POST /api/v1/chat` - Post-onboarding chat
  - `GET /api/v1/users/me` - Get user profile with `onboarding_completed`
- Must handle backend response format exactly as specified

### TC-2: React Router Integration
- Use React Router v6 patterns
- Leverage `Navigate` component for redirects
- Use `useLocation` for state passing
- Implement route guards with `ProtectedRoute`

### TC-3: State Management
- Use React Context for user state
- Use local state for chat messages
- Use `useEffect` for data fetching
- Avoid prop drilling with context

### TC-4: TypeScript Types
- Update types in `frontend/src/types/onboarding.types.ts`
- Add `onboarding_completed` to `User` type
- Add types for progress response
- Add types for state metadata

## 7. Out of Scope

- Voice-based onboarding (text only for MVP)
- Mid-onboarding pause/resume
- Editing onboarding data after completion
- Multi-language support
- Advanced analytics during onboarding
- Onboarding skip functionality

## 8. Success Criteria

### Quantitative Metrics
- All 6 user stories pass acceptance criteria
- Zero navigation lock bypasses possible
- 100% of users complete onboarding before accessing app
- Progress indicators update in < 100ms
- Zero console errors during onboarding flow

### Qualitative Metrics
- Users understand they must complete onboarding
- Progress is clear and motivating
- Chat interface feels natural and conversational
- Error messages are helpful and actionable
- Navigation unlock feels seamless

## 9. Dependencies

### Backend Dependencies (Already Complete)
- ✅ `POST /api/v1/chat/onboarding` endpoint
- ✅ `GET /api/v1/onboarding/progress` endpoint
- ✅ `STATE_METADATA` in backend
- ✅ `User.onboarding_completed` property
- ✅ Access control in agent orchestrator

### Frontend Dependencies (Existing)
- React 18+
- React Router v6
- TypeScript
- Tailwind CSS
- Axios for API calls

## 10. Risks & Mitigations

### Risk 1: Breaking Existing Onboarding Flow
**Impact**: High  
**Probability**: Medium  
**Mitigation**: Create new components alongside old ones, test thoroughly, then swap

### Risk 2: Navigation Lock Bypass
**Impact**: High  
**Probability**: Low  
**Mitigation**: Implement multiple layers of protection (route guards, UI disabling, backend enforcement)

### Risk 3: Poor Chat UX During Onboarding
**Impact**: Medium  
**Probability**: Medium  
**Mitigation**: Add clear instructions, progress indicators, and helpful error messages

### Risk 4: State Synchronization Issues
**Impact**: Medium  
**Probability**: Medium  
**Mitigation**: Use backend as source of truth, refresh state after each step

## 11. Open Questions

1. Should we allow users to go back to previous onboarding states?
   - **Recommendation**: No, backend enforces sequential progression

2. Should we show a summary screen after onboarding completion?
   - **Recommendation**: Yes, brief confirmation before redirecting to dashboard

3. Should we persist chat history during onboarding?
   - **Recommendation**: Yes, backend already saves conversation history

4. Should we add a "Help" button during onboarding?
   - **Recommendation**: Out of scope for MVP, add in future iteration

## 12. Acceptance Criteria Summary

### Must Have (P0)
- [ ] ProtectedRoute checks `onboarding_completed` flag
- [ ] OnboardingChatPage component with chat interface
- [ ] Navigation lock in MainLayout during onboarding
- [ ] ChatPage uses correct endpoint post-onboarding
- [ ] App.tsx routing enforces onboarding flow
- [ ] Progress indicators show current state and percentage
- [ ] All user stories pass acceptance criteria

### Should Have (P1)
- [ ] OnboardingProgressBar component
- [ ] UserContext includes `onboarding_completed`
- [ ] Smooth transitions and loading states
- [ ] Comprehensive error handling
- [ ] Mobile-responsive design

### Nice to Have (P2)
- [ ] OnboardingGuard modal for locked routes
- [ ] Animated progress transitions
- [ ] Onboarding completion celebration
- [ ] Keyboard shortcuts for navigation

## 13. Implementation Plan

### Phase 1: Core Infrastructure (2-3 hours)
1. Update `User` type with `onboarding_completed`
2. Update `UserContext` to fetch and store flag
3. Update `ProtectedRoute` with onboarding check
4. Update `App.tsx` routing with guards

### Phase 2: Onboarding Chat Interface (3-4 hours)
1. Create `OnboardingChatPage` component
2. Create `OnboardingProgressBar` component
3. Integrate with `POST /api/v1/chat/onboarding` endpoint
4. Handle state progression and completion

### Phase 3: Navigation Lock (1-2 hours)
1. Update `MainLayout` to disable nav items
2. Add tooltips to disabled items
3. Style disabled state
4. Test navigation lock enforcement

### Phase 4: Post-Onboarding Chat (1 hour)
1. Update `ChatPage` to use `/chat` endpoint
2. Remove agent selector
3. Handle 403 errors
4. Test post-onboarding access

### Phase 5: Testing & Polish (2-3 hours)
1. End-to-end testing of onboarding flow
2. Test navigation lock bypasses
3. Test error scenarios
4. Mobile responsiveness
5. Accessibility audit

**Total Estimated Time**: 9-13 hours

## 14. Testing Strategy

### Unit Tests
- `ProtectedRoute` onboarding check logic
- `UserContext` state management
- Progress calculation functions
- Navigation lock logic

### Integration Tests
- Complete onboarding flow from registration to dashboard
- Navigation lock enforcement across all routes
- Chat endpoint switching (onboarding vs post-onboarding)
- Error handling and recovery

### E2E Tests
- New user registration → onboarding → dashboard flow
- Returning user with incomplete onboarding
- Returning user with complete onboarding
- Navigation lock bypass attempts

## 15. Migration Strategy

### Backward Compatibility
- Keep old onboarding components temporarily
- Add feature flag to switch between old/new onboarding
- Test new flow with subset of users first
- Remove old components after successful rollout

### Data Migration
- No database migration needed (backend already updated)
- Frontend only needs to use new endpoints
- Existing users with incomplete onboarding will see new flow

## 16. References

- Validation Report: `validation_report.md`
- Refined Product Requirements: `docs/product/refined_product_requirement_shuren.md`
- Backend Chat Endpoint: `backend/app/api/v1/endpoints/chat.py`
- Backend Onboarding Service: `backend/app/services/onboarding_service.py`
- Current Frontend Onboarding: `frontend/src/pages/OnboardingPage.tsx`
- Current Frontend Chat: `frontend/src/pages/ChatPage.tsx`

## 17. API Endpoints Reference

### Onboarding Endpoints
```typescript
// Get current onboarding progress
GET /api/v1/onboarding/progress
Response: {
  current_step: number;
  is_complete: boolean;
  completion_percentage: number;
  state_metadata: {
    step: number;
    name: string;
    description: string;
    agent_type: string;
  };
}

// Send message during onboarding
POST /api/v1/chat/onboarding
Request: {
  message: string;
  current_state: number; // Optional, for validation
}
Response: {
  response: string;
  state_updated: boolean;
  new_state?: number;
  is_complete: boolean;
  progress: {
    current_step: number;
    completion_percentage: number;
  };
}
```

### Post-Onboarding Endpoints
```typescript
// Get user profile
GET /api/v1/users/me
Response: {
  id: string;
  email: string;
  full_name: string;
  onboarding_completed: boolean;
  // ... other fields
}

// Send message post-onboarding
POST /api/v1/chat
Request: {
  message: string;
}
Response: {
  response: string;
  conversation_id: string;
}
```

## 18. UI/UX Mockup Requirements

### Onboarding Chat Interface
```
┌─────────────────────────────────────────────┐
│ Shuren AI - Onboarding                      │
├─────────────────────────────────────────────┤
│ Progress: Step 3 of 9 (33%)                 │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│                                             │
│ ✓ Fitness Level Assessment                  │
│ ✓ Primary Fitness Goals                     │
│ ▶ Workout Preferences & Constraints         │
│   Diet Preferences & Restrictions           │
│   Fixed Meal Plan Selection                 │
│   ... (remaining states)                    │
├─────────────────────────────────────────────┤
│ Chat Messages:                              │
│                                             │
│ [Agent] Great! Now let's talk about your    │
│         workout preferences. Do you have    │
│         access to a gym, or will you be     │
│         working out at home?                │
│                                             │
│ [User] I have a home gym with dumbbells     │
│        and a bench.                         │
│                                             │
│ [Agent] Perfect! I've saved your equipment  │
│         preferences. Moving to next step... │
│                                             │
├─────────────────────────────────────────────┤
│ [Type your message here...]          [Send] │
└─────────────────────────────────────────────┘
```

### Navigation Lock State
```
┌─────────────────────────────────────────────┐
│ Sidebar (During Onboarding)                 │
├─────────────────────────────────────────────┤
│ ▶ Onboarding (Active)                       │
│ ⊘ Dashboard (Locked) 🛈                     │
│ ⊘ Chat (Locked) 🛈                          │
│ ⊘ Meals (Locked) 🛈                         │
│ ⊘ Workouts (Locked) 🛈                      │
│ ⊘ Voice (Locked) 🛈                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ ✓ Logout                                    │
└─────────────────────────────────────────────┘

Tooltip on hover: "Complete onboarding to unlock"
```

---

**Document Version**: 1.0  
**Created**: February 14, 2026  
**Status**: Draft - Awaiting Review
