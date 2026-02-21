# Frontend Onboarding Agent Integration - Design

## 1. Architecture Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Application                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         OnboardingChatPage (Main UI)               │    │
│  │                                                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │    │
│  │  │ AgentHeader  │  │ ProgressBar  │  │ PlanCard│ │    │
│  │  └──────────────┘  └──────────────┘  └─────────┘ │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │         MessageList (Chat History)           │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │         MessageInput (User Input)            │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              useOnboardingChat Hook                 │    │
│  │  - State management                                 │    │
│  │  - Streaming integration                            │    │
│  │  - Progress tracking                                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           onboardingService (API Layer)             │    │
│  │  - getOnboardingProgress()                          │    │
│  │  - streamOnboardingMessage()                        │    │
│  │  - completeOnboarding()                             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS/SSE
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│  /onboarding/progress                                        │
│  /chat/onboarding-stream (SSE)                              │
│  /onboarding/complete                                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Component Hierarchy

```
OnboardingChatPage
├── AgentHeader
│   ├── AgentIcon
│   ├── AgentName
│   └── AgentDescription
├── OnboardingProgressBar
│   ├── ProgressIndicator
│   ├── StateList
│   └── CompletionPercentage
├── ChatContainer
│   ├── MessageList
│   │   ├── UserMessage
│   │   ├── AssistantMessage
│   │   └── StreamingIndicator
│   └── PlanPreviewCard (conditional)
│       ├── WorkoutPlanPreview
│       │   ├── PlanHeader
│       │   ├── DaysList
│       │   └── ApprovalButtons
│       └── MealPlanPreview
│           ├── PlanHeader
│           ├── MacroBreakdown
│           ├── SampleMeals
│           └── ApprovalButtons
└── MessageInput
    ├── TextArea
    ├── SendButton
    └── DisabledOverlay (when streaming)
```

## 2. Data Models

### 2.1 Type Definitions


```typescript
// Agent Types
export enum AgentType {
  FITNESS_ASSESSMENT = 'fitness_assessment',
  GOAL_SETTING = 'goal_setting',
  WORKOUT_PLANNING = 'workout_planning',
  DIET_PLANNING = 'diet_planning',
  SCHEDULING = 'scheduling'
}

// State Metadata
export interface StateMetadata {
  state_number: number;
  name: string;
  agent: AgentType;
  description: string;
  required_fields: string[];
}

// Onboarding Progress
export interface OnboardingProgress {
  current_state: number;
  total_states: number;
  completed_states: number[];
  is_complete: boolean;
  completion_percentage: number;
  can_complete: boolean;
  current_state_info: StateMetadata;
  next_state_info: StateMetadata | null;
}

// Streaming Response
export interface OnboardingStreamChunk {
  chunk?: string;
  done?: boolean;
  error?: string;
  agent_type?: string;
  state_updated?: boolean;
  new_state?: number;
  progress?: {
    current_state: number;
    total_states: number;
    completed_states: number[];
    completion_percentage: number;
    is_complete: boolean;
    can_complete: boolean;
  };
}

// Workout Plan
export interface WorkoutPlan {
  frequency: number;
  location: string;
  duration_minutes: number;
  equipment: string[];
  days: WorkoutDay[];
}

export interface WorkoutDay {
  day_number: number;
  name: string;
  exercises: Exercise[];
}

export interface Exercise {
  name: string;
  sets: number;
  reps: string;
  rest_seconds: number;
  notes?: string;
}

// Meal Plan
export interface MealPlan {
  diet_type: string;
  meal_frequency: number;
  daily_calories: number;
  macros: MacroBreakdown;
  sample_meals: SampleMeal[];
}

export interface MacroBreakdown {
  protein_g: number;
  carbs_g: number;
  fats_g: number;
}

export interface SampleMeal {
  meal_number: number;
  name: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fats_g: number;
  foods: string[];
}
```

### 2.2 State Management

```typescript
// Onboarding Chat State
interface OnboardingChatState {
  // Progress tracking
  currentState: number;
  totalStates: number;
  completedStates: number[];
  completionPercentage: number;
  isComplete: boolean;
  canComplete: boolean;
  
  // Agent context
  currentAgent: AgentType;
  agentDescription: string;
  stateMetadata: StateMetadata | null;
  
  // Chat state
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  
  // Plan state
  pendingPlan: WorkoutPlan | MealPlan | null;
  planType: 'workout' | 'meal' | null;
  showPlanPreview: boolean;
}
```

## 3. Component Specifications

### 3.1 OnboardingChatPage

**Purpose**: Main container for agent-based onboarding flow

**Props**: None (uses routing)

**State**:
- All OnboardingChatState fields
- initialLoadComplete: boolean

**Lifecycle**:
1. Mount: Fetch onboarding progress
2. Check if complete → redirect to dashboard
3. Initialize chat with agent context
4. Handle streaming responses
5. Update progress on state changes
6. Show completion button when can_complete

**Key Methods**:
```typescript
async function fetchProgress(): Promise<void>
async function handleSendMessage(message: string): Promise<void>
async function handleCompleteOnboarding(): Promise<void>
function handlePlanApproval(): void
function handlePlanModification(feedback: string): void
```

### 3.2 AgentHeader

**Purpose**: Display current agent context and state information

**Props**:
```typescript
interface AgentHeaderProps {
  agentType: AgentType;
  agentDescription: string;
  currentState: number;
  totalStates: number;
  stateName: string;
}
```

**Rendering**:
- Agent icon (different for each agent type)
- Agent name (e.g., "Fitness Assessment Agent")
- Agent description
- Current state indicator (e.g., "Step 1 of 9")

**Styling**:
- Sticky header at top of chat
- Smooth transitions when agent changes
- Clear visual hierarchy

### 3.3 OnboardingProgressBar

**Purpose**: Visual progress indicator for onboarding states

**Props**:
```typescript
interface OnboardingProgressBarProps {
  currentState: number;
  totalStates: number;
  completedStates: number[];
  completionPercentage: number;
  stateMetadata: StateMetadata | null;
}
```

**Features**:
- Horizontal progress bar with percentage
- List of all 9 states with checkmarks for completed
- Current state highlighted
- State names and descriptions
- Smooth animations on state changes

**Layout**:
- Sidebar on desktop (left side)
- Collapsible on mobile (top)

### 3.4 PlanPreviewCard

**Purpose**: Display workout or meal plans for user review

**Props**:
```typescript
interface PlanPreviewCardProps {
  plan: WorkoutPlan | MealPlan;
  planType: 'workout' | 'meal';
  onApprove: () => void;
  onModify: (feedback: string) => void;
  onClose: () => void;
}
```

**Workout Plan Display**:
- Plan summary (frequency, location, duration)
- Day-by-day breakdown
- Exercise list with sets/reps
- Equipment needed

**Meal Plan Display**:
- Calorie target and macro breakdown
- Sample meals with nutrition info
- Meal timing suggestions
- Dietary restrictions noted

**Actions**:
- "Approve Plan" button (primary)
- "Request Changes" button (secondary)
- Close button (X)

**Behavior**:
- Modal overlay or slide-in panel
- Scrollable content
- Approve sends approval message to agent
- Modify opens text input for feedback

## 4. Service Layer

### 4.1 onboardingService Updates


```typescript
// Enhanced onboardingService
export const onboardingService = {
  /**
   * Get onboarding progress with state metadata
   * Calls GET /api/v1/onboarding/progress
   */
  async getOnboardingProgress(): Promise<OnboardingProgress> {
    const response = await api.get<OnboardingProgress>('/onboarding/progress');
    return response.data;
  },

  /**
   * Stream onboarding message with SSE
   * Calls GET /api/v1/chat/onboarding-stream
   * Returns cancel function
   */
  streamOnboardingMessage(
    message: string,
    currentState: number,
    callbacks: {
      onChunk: (chunk: string) => void;
      onComplete: (data: OnboardingStreamChunk) => void;
      onError: (error: string) => void;
    }
  ): () => void {
    const token = localStorage.getItem('auth_token');
    const baseURL = api.defaults.baseURL || 'http://localhost:8000/api/v1';
    const url = new URL(`${baseURL}/chat/onboarding-stream`);
    
    if (token) url.searchParams.append('token', token);
    url.searchParams.append('message', message);
    
    const eventSource = new EventSource(url.toString());
    
    eventSource.onmessage = (event) => {
      const data: OnboardingStreamChunk = JSON.parse(event.data);
      
      if (data.error) {
        callbacks.onError(data.error);
        eventSource.close();
      } else if (data.done) {
        callbacks.onComplete(data);
        eventSource.close();
      } else if (data.chunk) {
        callbacks.onChunk(data.chunk);
      }
    };
    
    eventSource.onerror = () => {
      callbacks.onError('Connection error');
      eventSource.close();
    };
    
    return () => eventSource.close();
  },

  /**
   * Complete onboarding and create profile
   * Calls POST /api/v1/onboarding/complete
   */
  async completeOnboarding(): Promise<OnboardingCompleteResponse> {
    const response = await api.post<OnboardingCompleteResponse>('/onboarding/complete');
    return response.data;
  }
};
```

### 4.2 Plan Detection Service

```typescript
// planDetectionService.ts
export const planDetectionService = {
  /**
   * Detect if message contains a workout plan
   */
  detectWorkoutPlan(message: string): WorkoutPlan | null {
    // Look for workout plan indicators
    const hasWorkoutIndicators = /workout plan|training plan|exercise schedule/i.test(message);
    if (!hasWorkoutIndicators) return null;
    
    // Parse plan from structured response
    // Backend should ideally send structured data, but we can parse text as fallback
    try {
      return this.parseWorkoutPlan(message);
    } catch {
      return null;
    }
  },

  /**
   * Detect if message contains a meal plan
   */
  detectMealPlan(message: string): MealPlan | null {
    // Look for meal plan indicators
    const hasMealIndicators = /meal plan|nutrition plan|calorie target|macro breakdown/i.test(message);
    if (!hasMealIndicators) return null;
    
    try {
      return this.parseMealPlan(message);
    } catch {
      return null;
    }
  },

  /**
   * Parse workout plan from text
   * Note: This is a fallback. Ideally backend sends structured JSON
   */
  parseWorkoutPlan(text: string): WorkoutPlan {
    // Implementation depends on backend response format
    // For now, return null and rely on structured responses
    throw new Error('Plan parsing not implemented - use structured responses');
  },

  /**
   * Parse meal plan from text
   */
  parseMealPlan(text: string): MealPlan {
    throw new Error('Plan parsing not implemented - use structured responses');
  }
};
```

## 5. Custom Hooks

### 5.1 useOnboardingChat

```typescript
interface UseOnboardingChatReturn {
  // Progress state
  currentState: number;
  totalStates: number;
  completedStates: number[];
  completionPercentage: number;
  isComplete: boolean;
  canComplete: boolean;
  
  // Agent state
  currentAgent: AgentType;
  agentDescription: string;
  stateMetadata: StateMetadata | null;
  
  // Chat state
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  
  // Plan state
  pendingPlan: WorkoutPlan | MealPlan | null;
  planType: 'workout' | 'meal' | null;
  showPlanPreview: boolean;
  
  // Actions
  sendMessage: (message: string) => Promise<void>;
  approvePlan: () => void;
  modifyPlan: (feedback: string) => void;
  closePlanPreview: () => void;
  completeOnboarding: () => Promise<void>;
  
  // Loading state
  initialLoadComplete: boolean;
}

export function useOnboardingChat(): UseOnboardingChatReturn {
  // State initialization
  const [currentState, setCurrentState] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [pendingPlan, setPendingPlan] = useState<WorkoutPlan | MealPlan | null>(null);
  // ... other state
  
  // Fetch progress on mount
  useEffect(() => {
    async function fetchProgress() {
      const progress = await onboardingService.getOnboardingProgress();
      setCurrentState(progress.current_state);
      setCompletedStates(progress.completed_states);
      setCompletionPercentage(progress.completion_percentage);
      setCanComplete(progress.can_complete);
      setStateMetadata(progress.current_state_info);
      setCurrentAgent(progress.current_state_info.agent as AgentType);
      setInitialLoadComplete(true);
    }
    fetchProgress();
  }, []);
  
  // Send message with streaming
  const sendMessage = useCallback(async (message: string) => {
    if (isStreaming) return;
    
    // Add user message
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Create assistant placeholder
    const assistantId = crypto.randomUUID();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true
    };
    setMessages(prev => [...prev, assistantMessage]);
    setIsStreaming(true);
    
    // Stream response
    onboardingService.streamOnboardingMessage(
      message,
      currentState,
      {
        onChunk: (chunk) => {
          setMessages(prev => prev.map(msg =>
            msg.id === assistantId
              ? { ...msg, content: msg.content + chunk }
              : msg
          ));
        },
        onComplete: (data) => {
          setMessages(prev => prev.map(msg =>
            msg.id === assistantId
              ? { ...msg, isStreaming: false }
              : msg
          ));
          setIsStreaming(false);
          
          // Handle state update
          if (data.state_updated && data.progress) {
            setCurrentState(data.progress.current_state);
            setCompletedStates(data.progress.completed_states);
            setCompletionPercentage(data.progress.completion_percentage);
            setCanComplete(data.progress.can_complete);
          }
          
          // Detect plan in response
          const lastMessage = messages[messages.length - 1];
          const workoutPlan = planDetectionService.detectWorkoutPlan(lastMessage.content);
          const mealPlan = planDetectionService.detectMealPlan(lastMessage.content);
          
          if (workoutPlan) {
            setPendingPlan(workoutPlan);
            setPlanType('workout');
            setShowPlanPreview(true);
          } else if (mealPlan) {
            setPendingPlan(mealPlan);
            setPlanType('meal');
            setShowPlanPreview(true);
          }
        },
        onError: (error) => {
          setError(error);
          setIsStreaming(false);
        }
      }
    );
  }, [currentState, isStreaming, messages]);
  
  // Approve plan
  const approvePlan = useCallback(() => {
    sendMessage('Yes, looks perfect!');
    setShowPlanPreview(false);
    setPendingPlan(null);
  }, [sendMessage]);
  
  // Modify plan
  const modifyPlan = useCallback((feedback: string) => {
    sendMessage(feedback);
    setShowPlanPreview(false);
  }, [sendMessage]);
  
  // Complete onboarding
  const completeOnboarding = useCallback(async () => {
    await onboardingService.completeOnboarding();
    // Redirect handled by parent component
  }, []);
  
  return {
    currentState,
    totalStates: 9,
    completedStates,
    completionPercentage,
    isComplete,
    canComplete,
    currentAgent,
    agentDescription: stateMetadata?.description || '',
    stateMetadata,
    messages,
    isStreaming,
    error,
    pendingPlan,
    planType,
    showPlanPreview,
    sendMessage,
    approvePlan,
    modifyPlan,
    closePlanPreview: () => setShowPlanPreview(false),
    completeOnboarding,
    initialLoadComplete
  };
}
```

## 6. UI/UX Design

### 6.1 Layout

**Desktop (>1024px)**:
```
┌─────────────────────────────────────────────────────────┐
│                     AgentHeader                          │
├──────────────┬──────────────────────────────────────────┤
│              │                                           │
│  Progress    │          Chat Messages                    │
│  Sidebar     │                                           │
│  (300px)     │                                           │
│              │                                           │
│              │                                           │
│              ├──────────────────────────────────────────┤
│              │          Message Input                    │
└──────────────┴──────────────────────────────────────────┘
```

**Mobile (<768px)**:
```
┌─────────────────────────────────────────────────────────┐
│                     AgentHeader                          │
├─────────────────────────────────────────────────────────┤
│  [Progress] (Collapsible)                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│                  Chat Messages                           │
│                                                          │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                  Message Input                           │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Color Scheme

- Primary: Blue (#3B82F6) - Agent messages, buttons
- Success: Green (#10B981) - Completed states, approval
- Warning: Yellow (#F59E0B) - Pending actions
- Error: Red (#EF4444) - Errors, validation
- Neutral: Gray (#6B7280) - Text, borders
- Background: Light Gray (#F9FAFB)

### 6.3 Agent Icons

Each agent type has a unique icon:
- Fitness Assessment: 💪 (flexed bicep)
- Goal Setting: 🎯 (target)
- Workout Planning: 🏋️ (weight lifter)
- Diet Planning: 🥗 (salad)
- Scheduling: 📅 (calendar)

### 6.4 Animations

- State transitions: Smooth fade and slide
- Progress bar: Animated fill on update
- Message streaming: Typing indicator
- Plan preview: Slide up from bottom (mobile) or modal (desktop)

## 7. Error Handling

### 7.1 Error Types

1. **Network Errors**: Connection failures, timeouts
2. **Authentication Errors**: Token expired, unauthorized
3. **Validation Errors**: Invalid state, missing data
4. **Streaming Errors**: SSE connection lost
5. **State Sync Errors**: Frontend/backend state mismatch

### 7.2 Error Recovery


```typescript
// Error Recovery Strategies
const errorRecoveryStrategies = {
  // Network errors: Retry with exponential backoff
  networkError: {
    maxRetries: 3,
    retryDelay: [1000, 2000, 4000],
    fallback: 'Show offline message and retry button'
  },
  
  // Authentication errors: Redirect to login
  authError: {
    action: 'Redirect to /login',
    preserveState: true
  },
  
  // Streaming errors: Fallback to non-streaming
  streamingError: {
    fallback: 'Use POST /chat/onboarding instead of streaming',
    notify: 'Show warning about degraded experience'
  },
  
  // State sync errors: Refresh from backend
  stateSyncError: {
    action: 'Fetch fresh state from /onboarding/progress',
    notify: 'Show "Syncing..." message'
  }
};
```

### 7.3 Error Messages

User-friendly error messages:
- "Connection lost. Retrying..." (network error)
- "Session expired. Please log in again." (auth error)
- "Something went wrong. Please try again." (generic error)
- "Syncing your progress..." (state sync)

## 8. Testing Strategy

### 8.1 Unit Tests

**Components to Test**:
- AgentHeader: Renders correct agent info
- OnboardingProgressBar: Shows correct progress
- PlanPreviewCard: Displays plans correctly
- useOnboardingChat: State management logic

**Test Cases**:
```typescript
describe('useOnboardingChat', () => {
  it('fetches progress on mount', async () => {
    // Mock API response
    // Assert state is updated
  });
  
  it('handles streaming messages', async () => {
    // Mock streaming response
    // Assert messages are updated
  });
  
  it('detects state updates', async () => {
    // Mock state_updated: true
    // Assert progress is refreshed
  });
  
  it('shows plan preview when plan detected', async () => {
    // Mock workout plan in response
    // Assert showPlanPreview is true
  });
});
```

### 8.2 Integration Tests

**Scenarios**:
1. Complete onboarding flow (all 9 states)
2. Plan approval workflow
3. Plan modification workflow
4. Error recovery scenarios
5. State synchronization

### 8.3 E2E Tests

**User Journeys**:
1. New user completes onboarding
2. User approves workout plan
3. User requests meal plan changes
4. User completes onboarding and redirects to dashboard

## 9. Performance Considerations

### 9.1 Optimization Strategies

1. **Message Batching**: Use React 19 automatic batching for rapid updates
2. **Lazy Loading**: Load plan preview components only when needed
3. **Memoization**: Memoize expensive computations (plan parsing)
4. **Debouncing**: Debounce input to prevent excessive API calls
5. **Virtual Scrolling**: For long message lists (if needed)

### 9.2 Performance Targets

- Initial load: < 2 seconds
- Message send: < 100ms (before streaming starts)
- Streaming latency: < 200ms per chunk
- State update: < 500ms
- Plan preview render: < 300ms

## 10. Accessibility

### 10.1 Keyboard Navigation

- Tab through all interactive elements
- Enter to send message
- Escape to close plan preview
- Arrow keys to navigate progress states

### 10.2 Screen Reader Support

- ARIA labels for all buttons
- Live regions for streaming messages
- Descriptive alt text for agent icons
- Semantic HTML structure

### 10.3 Visual Accessibility

- Color contrast ratio ≥ 4.5:1
- Focus indicators visible
- Text size adjustable
- No color-only information

## 11. Migration Strategy

### 11.1 Deprecation Plan

**Phase 1: Soft Deprecation** (Week 1)
- Keep OnboardingPage.tsx but add deprecation notice
- Route new users to OnboardingChatPage.tsx
- Allow existing in-progress users to finish old flow

**Phase 2: Hard Deprecation** (Week 2)
- Redirect all users to OnboardingChatPage.tsx
- Remove OnboardingPage.tsx and step components
- Clean up unused types and services

### 11.2 Data Migration

No data migration needed:
- Backend already uses new agent_context structure
- Old step_data is ignored by new system
- Users who started old flow must restart

### 11.3 Rollback Plan

If critical issues arise:
1. Revert routing to OnboardingPage.tsx
2. Disable OnboardingChatPage.tsx
3. Fix issues in separate branch
4. Re-deploy when stable

## 12. Implementation Checklist

### Phase 1: Type Definitions (1-2 days)
- [ ] Create AgentType enum
- [ ] Update OnboardingProgress interface
- [ ] Add OnboardingStreamChunk interface
- [ ] Add WorkoutPlan and MealPlan types
- [ ] Update onboarding.types.ts

### Phase 2: Service Layer (1-2 days)
- [ ] Update onboardingService.streamOnboardingMessage()
- [ ] Add planDetectionService
- [ ] Update API error handling
- [ ] Add retry logic for network errors

### Phase 3: Custom Hook (2-3 days)
- [ ] Create useOnboardingChat hook
- [ ] Implement state management
- [ ] Add streaming integration
- [ ] Add plan detection logic
- [ ] Add error handling

### Phase 4: Components (2-3 days)
- [ ] Create AgentHeader component
- [ ] Update OnboardingProgressBar for 9 states
- [ ] Create PlanPreviewCard component
- [ ] Create WorkoutPlanPreview subcomponent
- [ ] Create MealPlanPreview subcomponent
- [ ] Update OnboardingChatPage to use new hook

### Phase 5: Styling (1-2 days)
- [ ] Add Tailwind classes for all components
- [ ] Implement responsive design
- [ ] Add animations and transitions
- [ ] Test on multiple screen sizes

### Phase 6: Testing (2-3 days)
- [ ] Write unit tests for hook
- [ ] Write component tests
- [ ] Write integration tests
- [ ] Write E2E tests
- [ ] Manual testing on all browsers

### Phase 7: Documentation (1 day)
- [ ] Update README with new onboarding flow
- [ ] Document component props
- [ ] Add inline code comments
- [ ] Create user guide

### Phase 8: Deployment (1 day)
- [ ] Deploy to staging
- [ ] QA testing
- [ ] Deploy to production
- [ ] Monitor for errors

## 13. Correctness Properties

### Property 1: State Consistency
**Validates: Requirements US-4, TR-1**

**Property**: At any point during onboarding, the frontend's current_state must match the backend's current_step.

**Test Strategy**:
```typescript
// Property-based test
test('state consistency property', async () => {
  forAll(
    arbitrary.onboardingState(),
    async (initialState) => {
      // Given: User at some onboarding state
      const { result } = renderHook(() => useOnboardingChat());
      
      // When: User sends message and state updates
      await act(async () => {
        await result.current.sendMessage('test message');
      });
      
      // Then: Frontend state matches backend state
      const backendState = await onboardingService.getOnboardingProgress();
      expect(result.current.currentState).toBe(backendState.current_state);
    }
  );
});
```

### Property 2: Progress Monotonicity
**Validates: Requirements US-4, AC-4.1**

**Property**: The completion_percentage must never decrease during onboarding.

**Test Strategy**:
```typescript
test('progress monotonicity property', async () => {
  const percentages: number[] = [];
  
  // Track all percentage updates
  const { result } = renderHook(() => useOnboardingChat());
  
  // Send messages through all states
  for (let i = 0; i < 9; i++) {
    percentages.push(result.current.completionPercentage);
    await act(async () => {
      await result.current.sendMessage('complete state');
    });
  }
  
  // Assert: Each percentage >= previous
  for (let i = 1; i < percentages.length; i++) {
    expect(percentages[i]).toBeGreaterThanOrEqual(percentages[i - 1]);
  }
});
```

### Property 3: Message Ordering
**Validates: Requirements US-1, AC-1.5**

**Property**: Messages must always appear in chronological order (user, assistant, user, assistant, ...).

**Test Strategy**:
```typescript
test('message ordering property', async () => {
  const { result } = renderHook(() => useOnboardingChat());
  
  // Send multiple messages
  await act(async () => {
    await result.current.sendMessage('message 1');
    await result.current.sendMessage('message 2');
    await result.current.sendMessage('message 3');
  });
  
  // Assert: Messages alternate user/assistant
  const messages = result.current.messages;
  for (let i = 0; i < messages.length - 1; i++) {
    if (messages[i].role === 'user') {
      expect(messages[i + 1].role).toBe('assistant');
    }
  }
});
```

### Property 4: Plan Approval Idempotency
**Validates: Requirements US-3, AC-3.4**

**Property**: Approving a plan multiple times should only send one approval message.

**Test Strategy**:
```typescript
test('plan approval idempotency property', async () => {
  const { result } = renderHook(() => useOnboardingChat());
  
  // Given: Plan is shown
  act(() => {
    result.current.setPendingPlan(mockWorkoutPlan);
    result.current.setShowPlanPreview(true);
  });
  
  const initialMessageCount = result.current.messages.length;
  
  // When: User clicks approve multiple times
  await act(async () => {
    result.current.approvePlan();
    result.current.approvePlan();
    result.current.approvePlan();
  });
  
  // Then: Only one approval message sent
  expect(result.current.messages.length).toBe(initialMessageCount + 2); // user + assistant
});
```

### Property 5: Streaming Completeness
**Validates: Requirements US-5, AC-5.1**

**Property**: All streamed chunks must be concatenated in order to form the complete response.

**Test Strategy**:
```typescript
test('streaming completeness property', async () => {
  const chunks = ['Hello', ' ', 'world', '!'];
  const expectedComplete = 'Hello world!';
  
  // Mock streaming response
  mockStreamingResponse(chunks);
  
  const { result } = renderHook(() => useOnboardingChat());
  
  await act(async () => {
    await result.current.sendMessage('test');
  });
  
  // Assert: Final message content equals concatenated chunks
  const lastMessage = result.current.messages[result.current.messages.length - 1];
  expect(lastMessage.content).toBe(expectedComplete);
});
```

## 14. Security Considerations

### 14.1 Authentication

- JWT token passed in SSE query parameter (EventSource limitation)
- Token validated on every streaming request
- Token expiration handled gracefully

### 14.2 Input Validation

- Sanitize user messages before sending
- Validate state numbers (0-9 only)
- Prevent XSS in rendered messages

### 14.3 Data Privacy

- No sensitive data in localStorage
- Messages encrypted in transit (HTTPS)
- No logging of user messages on frontend

## 15. Monitoring and Analytics

### 15.1 Metrics to Track

- Onboarding completion rate
- Average time per state
- Plan approval rate
- Plan modification rate
- Error rates by type
- Streaming connection failures

### 15.2 Logging

```typescript
// Log important events
logger.info('Onboarding started', { userId, timestamp });
logger.info('State advanced', { userId, fromState, toState });
logger.info('Plan approved', { userId, planType });
logger.error('Streaming failed', { userId, error });
```

## 16. Future Enhancements

1. **Voice Integration**: Add voice input/output for onboarding
2. **Plan Customization**: Allow inline editing of plans
3. **Progress Saving**: Save partial progress for later
4. **Multi-language**: Support multiple languages
5. **Accessibility**: Enhanced screen reader support
6. **Offline Mode**: Cache progress for offline completion

## 17. References

- Backend TRD: `docs/technichal/onboarding_agent_system_trd.md`
- Backend Agents: `backend/app/agents/onboarding/`
- Backend API: `backend/app/api/v1/endpoints/onboarding.py`
- Backend Chat API: `backend/app/api/v1/endpoints/chat.py`
- React 19 Docs: https://react.dev/
- EventSource API: https://developer.mozilla.org/en-US/docs/Web/API/EventSource
- Tailwind CSS: https://tailwindcss.com/
