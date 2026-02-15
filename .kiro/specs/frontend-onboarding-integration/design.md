# Frontend Onboarding Integration - Design Document

## Overview

This design document outlines the technical implementation for integrating chat-based onboarding into the Shuren frontend. The backend is fully implemented and validated, providing:
- Chat-based onboarding endpoints (`POST /api/v1/chat/onboarding`)
- Progress tracking (`GET /api/v1/onboarding/progress`)
- Access control enforcement (navigation lock)
- Specialized agent routing (9 states)

The frontend needs to be updated to replace the form-based onboarding with a chat interface and implement navigation locking.

## Architecture

### High-Level Component Structure

```
App.tsx (Routing)
├── AuthProvider
├── UserProvider (Enhanced with onboarding_completed)
│   └── VoiceProvider
│       ├── Public Routes (Login, Register)
│       └── Protected Routes
│           ├── OnboardingChatPage (requireOnboardingComplete=false)
│           │   ├── OnboardingProgressBar
│           │   ├── ChatInterface
│           │   └── MessageInput
│           └── Other Pages (requireOnboardingComplete=true)
│               ├── MainLayout (with NavigationLock)
│               ├── ChatPage (post-onboarding)
│               ├── DashboardPage
│               ├── MealsPage
│               └── WorkoutsPage
```

### Data Flow

```
User Registration
    ↓
Redirect to /onboarding
    ↓
OnboardingChatPage loads
    ↓
Fetch progress (GET /api/v1/onboarding/progress)
    ↓
Display chat interface with progress bar
    ↓
User sends message
    ↓
POST /api/v1/chat/onboarding
    ↓
Backend routes to specialized agent
    ↓
Agent saves data, updates state
    ↓
Response includes state_updated flag
    ↓
Frontend updates progress bar
    ↓
Repeat until is_complete = true
    ↓
Redirect to /dashboard
    ↓
Navigation unlocks automatically
```

## Components

### 1. Enhanced UserContext

**Purpose**: Add `onboarding_completed` flag to user context

**Current State**:
- Manages user profile
- Provides `refreshProfile()` method
- No onboarding status tracking

**Changes Needed**:
- Add `onboardingCompleted: boolean` to context
- Fetch onboarding status from `GET /api/v1/users/me`
- Update status after onboarding completion

**Interface**:
```typescript
interface UserContextType {
  profile: UserProfile | null;
  onboardingCompleted: boolean;  // NEW
  refreshProfile: () => Promise<void>;
  refreshOnboardingStatus: () => Promise<void>;  // NEW
  unlockProfile: () => Promise<void>;
  loading: boolean;
  error: string | null;
}
```

**Implementation Notes**:
- Fetch user data on context initialization
- Store `onboarding_completed` flag separately from profile
- Provide method to refresh onboarding status independently

---

### 2. Enhanced ProtectedRoute Component

**Purpose**: Enforce onboarding completion check before accessing protected routes

**Current State**:
- Only checks authentication
- Has TODO comment for onboarding check
- No redirect logic for incomplete onboarding

**Changes Needed**:
- Add `requireOnboardingComplete` prop (default: `true`)
- Check `onboardingCompleted` from UserContext
- Redirect to `/onboarding` if incomplete and required
- Redirect to `/dashboard` if complete and accessing `/onboarding`

**Interface**:
```typescript
interface ProtectedRouteProps {
  children: React.ReactNode;
  requireOnboardingComplete?: boolean;  // NEW, default: true
}
```

**Logic**:
```typescript
// If onboarding required and not complete
if (requireOnboardingComplete && !onboardingCompleted) {
  return <Navigate to="/onboarding" replace />;
}

// If onboarding complete and accessing /onboarding
if (onboardingCompleted && location.pathname === '/onboarding') {
  return <Navigate to="/dashboard" replace />;
}
```

---

### 3. OnboardingChatPage Component (NEW)

**Purpose**: Replace form-based onboarding with chat-based interface

**Location**: `frontend/src/pages/OnboardingChatPage.tsx`

**Responsibilities**:
- Display chat interface for onboarding
- Show progress indicators (Step X of 9)
- Send messages to `/api/v1/chat/onboarding`
- Update progress after each state transition
- Redirect to dashboard when complete

**State Management**:
```typescript
interface OnboardingChatState {
  messages: Message[];
  currentState: number;
  totalStates: number;
  completionPercentage: number;
  stateMetadata: StateMetadata | null;
  loading: boolean;
  error: string | null;
}
```

**Key Methods**:
- `fetchProgress()` - Load current onboarding state
- `sendMessage(message: string)` - Send to onboarding chat endpoint
- `handleStateUpdate()` - Update progress when state changes
- `handleCompletion()` - Redirect to dashboard when done

**UI Structure**:
```tsx
<div className="onboarding-chat-page">
  <OnboardingProgressBar
    currentState={currentState}
    totalStates={totalStates}
    completionPercentage={completionPercentage}
    stateMetadata={stateMetadata}
  />
  
  <ChatInterface
    messages={messages}
    loading={loading}
    error={error}
  />
  
  <MessageInput
    onSend={sendMessage}
    disabled={loading}
    placeholder="Type your response..."
  />
</div>
```

---

### 4. OnboardingProgressBar Component (NEW)

**Purpose**: Display visual progress through onboarding states

**Location**: `frontend/src/components/onboarding/OnboardingProgressBar.tsx`

**Props**:
```typescript
interface OnboardingProgressBarProps {
  currentState: number;
  totalStates: number;
  completionPercentage: number;
  stateMetadata: StateMetadata | null;
  completedStates: number[];
}
```

**UI Elements**:
- Progress bar with percentage
- "Step X of 9" text
- Current state name and description
- List of states with checkmarks for completed
- Current state highlighted
- Upcoming states grayed out

**Visual Design**:
```
┌─────────────────────────────────────────────┐
│ Progress: Step 3 of 9 (33%)                 │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│                                             │
│ ✓ Fitness Level Assessment                  │
│ ✓ Primary Fitness Goals                     │
│ ▶ Workout Preferences & Constraints         │
│   Diet Preferences & Restrictions           │
│   Fixed Meal Plan Selection                 │
│   Meal Timing Schedule                      │
│   Workout Schedule                          │
│   Hydration Schedule                        │
│   Supplement Preferences                    │
└─────────────────────────────────────────────┘
```

---

### 5. Enhanced MainLayout Component

**Purpose**: Disable navigation items during onboarding

**Current State**:
- Renders Header, Footer, and children
- No navigation lock logic

**Changes Needed**:
- Check `onboardingCompleted` from UserContext
- Pass `onboardingCompleted` to Header component
- Header disables nav items if incomplete

**Props**:
```typescript
interface MainLayoutProps {
  children: React.ReactNode;
  className?: string;
}
```

**Implementation**:
```typescript
const { onboardingCompleted } = useUser();

return (
  <div className="min-h-screen flex flex-col bg-gray-50">
    <Header onboardingCompleted={onboardingCompleted} />
    <main>{children}</main>
    <Footer />
  </div>
);
```

---

### 6. Enhanced Header Component

**Purpose**: Disable navigation links during onboarding

**Current State**: (Need to check existing implementation)

**Changes Needed**:
- Accept `onboardingCompleted` prop
- Disable all nav links except "Onboarding" and "Logout"
- Add tooltips to disabled links
- Style disabled links with gray color and cursor-not-allowed

**Props**:
```typescript
interface HeaderProps {
  onboardingCompleted: boolean;
}
```

**Navigation Items**:
```typescript
const navItems = [
  { path: '/dashboard', label: 'Dashboard', requiresOnboarding: true },
  { path: '/chat', label: 'Chat', requiresOnboarding: true },
  { path: '/meals', label: 'Meals', requiresOnboarding: true },
  { path: '/workouts', label: 'Workouts', requiresOnboarding: true },
  { path: '/voice', label: 'Voice', requiresOnboarding: true },
  { path: '/onboarding', label: 'Onboarding', requiresOnboarding: false },
];
```

**Rendering Logic**:
```typescript
{navItems.map(item => {
  const isDisabled = item.requiresOnboarding && !onboardingCompleted;
  
  return (
    <NavLink
      key={item.path}
      to={item.path}
      disabled={isDisabled}
      tooltip={isDisabled ? "Complete onboarding to unlock" : undefined}
    />
  );
})}
```

---

### 7. Enhanced ChatPage Component

**Purpose**: Use correct endpoint post-onboarding and remove agent selector

**Current State**:
- Uses `/chat/chat` endpoint (correct)
- Has agent selector (needs removal)
- No onboarding completion check

**Changes Needed**:
- Remove `AgentSelector` component
- Force `agent_type` to `"general"` or omit it
- Add error handling for 403 responses
- Redirect to `/onboarding` if 403 with `ONBOARDING_REQUIRED`

**Updated Structure**:
```tsx
<div className="chat-page">
  <div className="header">
    <h1>AI Chat</h1>
    {/* AgentSelector removed */}
    <button onClick={clearMessages}>Clear Chat</button>
  </div>
  
  <MessageList messages={messages} />
  <MessageInput onSend={sendMessage} />
</div>
```

**Error Handling**:
```typescript
try {
  await sendMessage(message);
} catch (error) {
  if (error.response?.status === 403) {
    const detail = error.response.data.detail;
    if (detail.error_code === 'ONBOARDING_REQUIRED') {
      navigate('/onboarding');
    }
  }
}
```

---

### 8. Enhanced App.tsx Routing

**Purpose**: Update routing to enforce onboarding flow

**Current State**:
- All protected routes use same `ProtectedRoute` wrapper
- No `requireOnboardingComplete` prop usage
- Root path redirects to `/login`

**Changes Needed**:
- Add `requireOnboardingComplete={false}` to `/onboarding` route
- Add `requireOnboardingComplete={true}` to all other protected routes
- Update root path redirect logic based on onboarding status
- Update 404 fallback to check onboarding status

**Updated Routing**:
```tsx
<Routes>
  {/* Public routes */}
  <Route path="/" element={<RootRedirect />} />
  <Route path="/login" element={<LoginPage />} />
  <Route path="/register" element={<RegisterPage />} />

  {/* Onboarding route - accessible during onboarding */}
  <Route
    path="/onboarding"
    element={
      <ProtectedRoute requireOnboardingComplete={false}>
        <OnboardingChatPage />
      </ProtectedRoute>
    }
  />

  {/* Protected routes - require onboarding completion */}
  <Route
    path="/dashboard"
    element={
      <ProtectedRoute requireOnboardingComplete={true}>
        <MainLayout><DashboardPage /></MainLayout>
      </ProtectedRoute>
    }
  />
  
  {/* ... other protected routes with requireOnboardingComplete={true} */}
  
  {/* 404 fallback */}
  <Route path="*" element={<NotFoundRedirect />} />
</Routes>
```

**RootRedirect Component**:
```typescript
const RootRedirect = () => {
  const { isAuthenticated } = useAuth();
  const { onboardingCompleted } = useUser();
  
  if (!isAuthenticated) return <Navigate to="/login" />;
  if (!onboardingCompleted) return <Navigate to="/onboarding" />;
  return <Navigate to="/dashboard" />;
};
```

---

## Services

### 1. Enhanced onboardingService

**Purpose**: Add methods for chat-based onboarding

**Current Methods**:
- `getOnboardingState()` - Get current state
- `saveStep()` - Save step data (form-based)
- `completeOnboarding()` - Complete onboarding

**New Methods Needed**:
```typescript
/**
 * Get onboarding progress with state metadata
 */
async getProgress(): Promise<OnboardingProgress> {
  const response = await api.get<OnboardingProgress>('/onboarding/progress');
  return response.data;
}

/**
 * Send message during onboarding
 */
async sendOnboardingMessage(
  message: string,
  currentState: number
): Promise<OnboardingChatResponse> {
  const response = await api.post<OnboardingChatResponse>('/chat/onboarding', {
    message,
    current_state: currentState
  });
  return response.data;
}
```

---

### 2. Enhanced chatService

**Purpose**: Update to use correct endpoint and handle errors

**Current Implementation**:
- Uses `/chat/chat` endpoint (correct)
- Has `agentType` parameter (needs to be removed or forced to "general")

**Changes Needed**:
- Remove or ignore `agentType` parameter for post-onboarding chat
- Add error handling for 403 responses
- Return error details for UI to handle redirects

**Updated Method**:
```typescript
async sendMessage(message: string): Promise<ChatResponse> {
  try {
    const response = await api.post<ChatResponse>('/chat', {
      message,
      // agent_type omitted - backend forces general agent
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      // Re-throw with structured error for UI handling
      throw {
        status: 403,
        code: error.response.data.detail?.error_code,
        message: error.response.data.detail?.message,
        redirect: error.response.data.detail?.redirect,
      };
    }
    throw error;
  }
}
```

---

## Types

### New Type Definitions

**Location**: `frontend/src/types/onboarding.types.ts`

```typescript
/**
 * Onboarding progress response
 * Returned by GET /api/v1/onboarding/progress
 */
export interface OnboardingProgress {
  current_state: number;
  total_states: number;
  completed_states: number[];
  is_complete: boolean;
  completion_percentage: number;
  current_state_info: StateMetadata;
}

/**
 * State metadata for UI rendering
 */
export interface StateMetadata {
  state_number: number;
  name: string;
  agent: string;
  description: string;
  required_fields: string[];
}

/**
 * Onboarding chat request
 */
export interface OnboardingChatRequest {
  message: string;
  current_state: number;
}

/**
 * Onboarding chat response
 */
export interface OnboardingChatResponse {
  response: string;
  agent_type: string;
  state_updated: boolean;
  new_state?: number;
  is_complete: boolean;
  progress: {
    current_state: number;
    completion_percentage: number;
  };
}
```

**Location**: `frontend/src/types/auth.types.ts`

```typescript
/**
 * User type with onboarding status
 */
export interface User {
  id: string;
  email: string;
  full_name: string;
  onboarding_completed: boolean;  // NEW
  created_at: string;
  updated_at: string;
}
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

Before writing properties, let me identify and eliminate redundant properties from the prework:

**Redundancy Analysis**:

1. **Navigation Lock Properties** (US-1.2, US-1.4, US-3.1, US-3.3):
   - US-1.2: "User cannot access protected routes until onboarding complete"
   - US-1.4: "User can only access `/onboarding` route during onboarding"
   - US-3.1: "Sidebar/menu items are disabled during onboarding"
   - US-3.3: "Clicking disabled items does nothing"
   - **Consolidation**: These can be combined into one comprehensive property about route access control during onboarding

2. **Progress Display Properties** (US-2.6, US-4.1):
   - US-2.6: "Progress bar shows 'Step X of 9' with percentage"
   - US-4.1: "Progress bar shows percentage: `(current_step / 9) * 100`"
   - **Consolidation**: These are testing the same thing - combine into one property

3. **State Display Properties** (US-4.2, US-4.3, US-4.4, US-4.5):
   - US-4.2: "Current state name displayed prominently"
   - US-4.3: "List of completed states with checkmarks"
   - US-4.4: "Current state highlighted"
   - US-4.5: "Upcoming states visible but grayed out"
   - **Consolidation**: These can be combined into one comprehensive property about state list rendering

4. **Post-Onboarding Access Properties** (US-5.2, US-5.3):
   - US-5.2: "All navigation items become enabled"
   - US-5.3: "User can access all protected routes"
   - **Consolidation**: These are testing the same thing - combine into one property

**Remaining Unique Properties**:
- Navigation lock during onboarding (consolidated from US-1.2, US-1.4, US-3.1, US-3.3)
- Helpful message on locked routes (US-1.3)
- Disabled items show tooltip (US-3.2)
- Progress calculation (consolidated from US-2.6, US-4.1)
- State metadata display (US-2.7)
- State list rendering (consolidated from US-4.2, US-4.3, US-4.4, US-4.5)
- Questions presented for all states (US-2.3)
- Post-onboarding access (consolidated from US-5.2, US-5.3)

---

### Correctness Properties

#### Property 1: Navigation Lock During Onboarding

*For any* user with incomplete onboarding (`onboarding_completed = false`), attempting to access any protected route (dashboard, chat, meals, workouts, voice) should result in a redirect to `/onboarding`, and clicking on disabled navigation items should not change the current route.

**Validates: Requirements US-1.2, US-1.4, US-3.1, US-3.3**

**Test Strategy**: Generate random protected routes and verify all redirect to `/onboarding` when onboarding is incomplete. Simulate clicks on disabled navigation items and verify route doesn't change.

---

#### Property 2: Helpful Message on Locked Routes

*For any* protected route accessed during incomplete onboarding, the UI should display a message containing "Complete onboarding to unlock" or similar helpful text.

**Validates: Requirements US-1.3**

**Test Strategy**: Attempt to access various protected routes during onboarding and verify the presence of helpful messaging in the UI or redirect behavior.

---

#### Property 3: Disabled Items Show Tooltip

*For any* navigation item that requires onboarding completion, when onboarding is incomplete, hovering over the item should display a tooltip containing "Complete onboarding to unlock".

**Validates: Requirements US-3.2**

**Test Strategy**: Iterate through all navigation items that require onboarding, simulate hover events, and verify tooltip content.

---

#### Property 4: Progress Calculation Accuracy

*For any* onboarding state number `n` where `1 ≤ n ≤ 9`, the displayed progress percentage should equal `(n / 9) * 100`, and the step indicator should show "Step n of 9".

**Validates: Requirements US-2.6, US-4.1**

**Test Strategy**: Generate random state numbers from 1-9, render the progress bar, and verify the percentage calculation and step text are correct.

---

#### Property 5: State Metadata Display

*For any* onboarding state, the state name and description displayed in the UI should match the `STATE_METADATA` returned from the backend `GET /api/v1/onboarding/progress` endpoint.

**Validates: Requirements US-2.7**

**Test Strategy**: Mock backend responses with various state metadata, render the UI, and verify the displayed state name and description match the mocked data.

---

#### Property 6: State List Rendering

*For any* onboarding progress state, the state list should display:
- Completed states (state number < current state) with checkmarks
- Current state highlighted with a distinct style
- Upcoming states (state number > current state) grayed out

**Validates: Requirements US-4.2, US-4.3, US-4.4, US-4.5**

**Test Strategy**: Generate random current state values (1-9), render the state list, and verify:
- States before current have checkmarks
- Current state has highlight styling
- States after current have grayed-out styling

---

#### Property 7: Questions Presented for All States

*For any* onboarding state from 1-9, when the chat interface loads that state, the UI should display question content from the agent (either from initial load or first agent message).

**Validates: Requirements US-2.3**

**Test Strategy**: Iterate through all 9 states, mock agent responses with questions, and verify question content is displayed in the chat interface.

---

#### Property 8: Post-Onboarding Access

*For any* user with completed onboarding (`onboarding_completed = true`), all navigation items should be enabled, and all protected routes (dashboard, chat, meals, workouts, voice) should be accessible without redirects.

**Validates: Requirements US-5.2, US-5.3**

**Test Strategy**: Set onboarding as complete, attempt to access all protected routes, and verify no redirects occur. Check that all navigation items are enabled (not disabled).

---

### Example-Based Tests

The following scenarios should be tested with specific examples rather than property-based testing:

#### Example 1: Registration Redirect
After successful registration, verify user is redirected to `/onboarding`.
**Validates: Requirements US-1.1**

#### Example 2: Chat Interface Display
When accessing `/onboarding`, verify the page displays a chat interface (not forms).
**Validates: Requirements US-2.1**

#### Example 3: Welcome Message
On first load of onboarding, verify a welcome message is displayed explaining the process.
**Validates: Requirements US-2.2**

#### Example 4: Text Input Present
Verify the onboarding chat interface contains a text input field for user responses.
**Validates: Requirements US-2.4**

#### Example 5: Onboarding Menu Active
During onboarding, verify only the "Onboarding" menu item is active/highlighted.
**Validates: Requirements US-3.4**

#### Example 6: Logout Functional
During onboarding, verify the logout button works and logs the user out.
**Validates: Requirements US-3.5**

#### Example 7: Progress Endpoint Called
Verify that `GET /api/v1/onboarding/progress` is called when loading the onboarding page.
**Validates: Requirements US-4.6**

#### Example 8: Completion Redirect
After completing state 9, verify user is redirected to `/dashboard`.
**Validates: Requirements US-5.1**

#### Example 9: Onboarding Redirect After Completion
After onboarding is complete, attempting to access `/onboarding` should redirect to `/dashboard`.
**Validates: Requirements US-5.4**

#### Example 10: Onboarding Completed Flag
After completing onboarding, verify `onboarding_completed` flag in UserContext is `true`.
**Validates: Requirements US-5.5**

#### Example 11: Post-Onboarding Chat Endpoint
After onboarding, verify chat page uses `POST /api/v1/chat` endpoint (not `/chat/onboarding`).
**Validates: Requirements US-6.1**

#### Example 12: No Agent Selector
After onboarding, verify the chat page does not display an agent selector component.
**Validates: Requirements US-6.2**

#### Example 13: 403 Error Handling
When chat endpoint returns 403 with `ONBOARDING_REQUIRED`, verify user is redirected to `/onboarding`.
**Validates: Requirements US-6.5**

---

## Error Handling

### Error Scenarios

1. **Network Errors During Onboarding**
   - **Scenario**: API call to `/chat/onboarding` fails
   - **Handling**: Display error message, allow retry, don't lose user's message
   - **UI**: Show error banner with "Failed to send message. Retry?"

2. **Progress Fetch Failure**
   - **Scenario**: `GET /api/v1/onboarding/progress` fails
   - **Handling**: Show loading state, retry with exponential backoff
   - **UI**: Display "Loading your progress..." with spinner

3. **State Mismatch Error**
   - **Scenario**: Backend returns 400 with state mismatch
   - **Handling**: Refresh progress from backend, update UI state
   - **UI**: Show "Syncing your progress..." message

4. **Onboarding Already Complete**
   - **Scenario**: User accesses `/onboarding` after completion
   - **Handling**: Redirect to `/dashboard` immediately
   - **UI**: Brief message "Onboarding already completed"

5. **Incomplete Onboarding Access**
   - **Scenario**: User tries to access protected route before completion
   - **Handling**: Redirect to `/onboarding` with state preservation
   - **UI**: Show progress modal "Complete onboarding to unlock"

6. **Authentication Expiry During Onboarding**
   - **Scenario**: JWT token expires mid-onboarding
   - **Handling**: Redirect to login, preserve onboarding state on backend
   - **UI**: Show "Session expired. Please log in again."

### Error Recovery Strategies

1. **Automatic Retry**: Network errors retry up to 3 times with exponential backoff
2. **State Synchronization**: On any error, refresh progress from backend
3. **Optimistic UI**: Show message immediately, rollback on error
4. **Graceful Degradation**: If progress fetch fails, show basic UI without metadata

---

## Testing Strategy

### Unit Tests

**Component Tests**:
- `OnboardingProgressBar`: Renders correct step, percentage, state list
- `OnboardingChatPage`: Handles message sending, state updates, completion
- `ProtectedRoute`: Redirects based on onboarding status
- `MainLayout/Header`: Disables navigation items correctly
- `ChatPage`: Uses correct endpoint, handles 403 errors

**Service Tests**:
- `onboardingService.getProgress()`: Calls correct endpoint, parses response
- `onboardingService.sendOnboardingMessage()`: Sends correct payload
- `chatService.sendMessage()`: Uses `/chat` endpoint, handles errors

**Context Tests**:
- `UserContext`: Fetches and stores `onboarding_completed` flag
- `UserContext.refreshOnboardingStatus()`: Updates flag correctly

### Integration Tests

**Onboarding Flow**:
1. User registers → redirected to `/onboarding`
2. Progress loads → displays state 1
3. User sends message → state updates to 2
4. Repeat through state 9 → redirects to `/dashboard`
5. Navigation unlocks → all routes accessible

**Navigation Lock**:
1. User with incomplete onboarding tries to access `/dashboard`
2. Redirected to `/onboarding`
3. Navigation items disabled
4. Tooltips show on hover
5. Clicking disabled items does nothing

**Post-Onboarding**:
1. User completes onboarding
2. Redirected to `/dashboard`
3. All navigation items enabled
4. Chat page accessible
5. Chat uses `/chat` endpoint
6. No agent selector visible

### Property-Based Tests

**Test Framework**: Use a property-based testing library for React (e.g., `fast-check` with React Testing Library)

**Configuration**:
- Minimum 100 iterations per property test
- Generate random state numbers (1-9)
- Generate random route paths
- Generate random onboarding completion states

**Property Test Examples**:

```typescript
// Property 1: Navigation Lock
test('Property 1: Navigation lock during onboarding', () => {
  fc.assert(
    fc.property(
      fc.constantFrom('/dashboard', '/chat', '/meals', '/workouts', '/voice'),
      (route) => {
        // Setup: User with incomplete onboarding
        const { result } = renderHook(() => useUser(), {
          wrapper: createWrapper({ onboardingCompleted: false })
        });
        
        // Action: Navigate to protected route
        const { container } = render(
          <MemoryRouter initialEntries={[route]}>
            <App />
          </MemoryRouter>
        );
        
        // Assert: Redirected to /onboarding
        expect(window.location.pathname).toBe('/onboarding');
      }
    ),
    { numRuns: 100 }
  );
});

// Property 4: Progress Calculation
test('Property 4: Progress calculation accuracy', () => {
  fc.assert(
    fc.property(
      fc.integer({ min: 1, max: 9 }),
      (currentState) => {
        const expectedPercentage = Math.round((currentState / 9) * 100);
        
        const { getByText } = render(
          <OnboardingProgressBar
            currentState={currentState}
            totalStates={9}
            completionPercentage={expectedPercentage}
            stateMetadata={mockStateMetadata[currentState]}
            completedStates={Array.from({ length: currentState - 1 }, (_, i) => i + 1)}
          />
        );
        
        // Assert: Correct step text
        expect(getByText(`Step ${currentState} of 9`)).toBeInTheDocument();
        
        // Assert: Correct percentage
        expect(getByText(`${expectedPercentage}%`)).toBeInTheDocument();
      }
    ),
    { numRuns: 100 }
  );
});
```

**Property Test Tags**:
Each property test must include a comment tag:
```typescript
// Feature: frontend-onboarding-integration, Property 1: Navigation lock during onboarding
```

### End-to-End Tests

**Complete Onboarding Flow** (Playwright/Cypress):
1. Register new user
2. Verify redirect to `/onboarding`
3. Complete all 9 states via chat
4. Verify redirect to `/dashboard`
5. Verify navigation unlocked
6. Verify chat accessible

**Navigation Lock Enforcement**:
1. Login with incomplete onboarding user
2. Attempt to access each protected route
3. Verify all redirect to `/onboarding`
4. Verify navigation items disabled
5. Complete onboarding
6. Verify navigation unlocked

---

## Implementation Notes

### React Router v6 Patterns

**Redirect with State Preservation**:
```typescript
<Navigate to="/onboarding" state={{ from: location.pathname }} replace />
```

**Check Location in Component**:
```typescript
const location = useLocation();
const from = location.state?.from || '/dashboard';
```

### TypeScript Best Practices

**Strict Null Checks**:
```typescript
// Always check for null/undefined
if (!onboardingCompleted) {
  return <Navigate to="/onboarding" />;
}
```

**Type Guards**:
```typescript
function isOnboardingError(error: any): error is OnboardingError {
  return error.code === 'ONBOARDING_REQUIRED';
}
```

### Performance Optimizations

1. **Lazy Load Onboarding Components**: Use `React.lazy()` for OnboardingChatPage
2. **Memoize Progress Bar**: Use `React.memo()` to prevent unnecessary re-renders
3. **Debounce Message Input**: Debounce user typing to reduce re-renders
4. **Cache Progress Data**: Cache progress response for 30 seconds

### Accessibility

1. **Keyboard Navigation**: All interactive elements accessible via keyboard
2. **Screen Reader Support**: ARIA labels for progress indicators
3. **Focus Management**: Focus input after state transitions
4. **Color Contrast**: Ensure disabled items have sufficient contrast

---

## Migration Strategy

### Phase 1: Add New Components (No Breaking Changes)

1. Create `OnboardingChatPage` component
2. Create `OnboardingProgressBar` component
3. Add new types to `onboarding.types.ts`
4. Add new methods to `onboardingService`
5. Update `UserContext` with `onboarding_completed`

**Testing**: Unit tests for new components

### Phase 2: Update Routing (Feature Flag)

1. Add feature flag `USE_CHAT_ONBOARDING`
2. Update `App.tsx` to conditionally use new onboarding page
3. Update `ProtectedRoute` with onboarding check
4. Test both old and new flows

**Testing**: Integration tests with feature flag on/off

### Phase 3: Update Navigation (Gradual Rollout)

1. Update `MainLayout` to pass `onboardingCompleted` to Header
2. Update `Header` to disable items during onboarding
3. Update `ChatPage` to remove agent selector
4. Test navigation lock enforcement

**Testing**: E2E tests for navigation lock

### Phase 4: Remove Old Components (Cleanup)

1. Remove old onboarding step components (Step1-Step12)
2. Remove old `OnboardingPage` component
3. Remove feature flag
4. Update documentation

**Testing**: Full regression test suite

### Rollback Plan

If issues arise:
1. Disable feature flag `USE_CHAT_ONBOARDING`
2. Revert routing changes
3. Keep old components in place
4. Investigate and fix issues
5. Re-enable feature flag

---

## Security Considerations

1. **JWT Token Validation**: All API calls include valid JWT token
2. **CSRF Protection**: Use CSRF tokens for state-changing operations
3. **XSS Prevention**: Sanitize all user input before displaying
4. **Rate Limiting**: Implement client-side rate limiting for message sending
5. **Secure Storage**: Store tokens in httpOnly cookies (if possible)

---

## Performance Targets

- **Initial Load**: Onboarding page loads in < 1 second
- **Progress Fetch**: Progress data fetched in < 200ms
- **Message Send**: Message sent and response received in < 2 seconds
- **State Update**: UI updates after state change in < 100ms
- **Navigation**: Route transitions in < 300ms

---

## Monitoring and Analytics

### Key Metrics

1. **Onboarding Completion Rate**: % of users who complete all 9 states
2. **Average Completion Time**: Time from start to finish
3. **Drop-off Points**: Which states have highest abandonment
4. **Error Rate**: % of messages that fail to send
5. **Navigation Lock Bypasses**: Any attempts to bypass lock (should be 0)

### Logging

**Client-Side Logging**:
```typescript
logger.info('Onboarding started', { userId, timestamp });
logger.info('State completed', { userId, state, timestamp });
logger.error('Message send failed', { userId, state, error });
logger.info('Onboarding completed', { userId, duration, timestamp });
```

**Events to Track**:
- Onboarding started
- Each state completed
- Onboarding completed
- Navigation lock triggered
- Error occurred
- User dropped off

---

## Future Enhancements

1. **Voice-Based Onboarding**: Add voice input option
2. **Progress Persistence**: Save progress across sessions
3. **Onboarding Pause/Resume**: Allow users to pause and resume later
4. **Animated Transitions**: Add smooth animations between states
5. **Onboarding Summary**: Show summary screen before completion
6. **Accessibility Improvements**: Enhanced screen reader support
7. **Mobile Optimization**: Optimize for mobile devices
8. **Offline Support**: Allow onboarding to work offline with sync

---

## References

- **Backend Validation Report**: `validation_report.md`
- **Refined Product Requirements**: `docs/product/refined_product_requirement_shuren.md`
- **Backend Chat Endpoint**: `backend/app/api/v1/endpoints/chat.py`
- **Backend Onboarding Service**: `backend/app/services/onboarding_service.py`
- **Backend Agent Orchestrator**: `backend/app/services/agent_orchestrator.py`
- **React Router v6 Docs**: https://reactrouter.com/en/main
- **React Testing Library**: https://testing-library.com/react
- **Fast-Check (Property Testing)**: https://github.com/dubzzz/fast-check

---

**Document Version**: 1.0  
**Created**: 2026-02-14  
**Status**: Draft - Awaiting Review
