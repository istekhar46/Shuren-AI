# useOnboardingChat Hook API Documentation

## Overview

`useOnboardingChat` is a custom React hook that manages the complete state and interactions for the agent-based onboarding flow. It handles progress tracking, streaming chat messages, plan approval workflows, and state synchronization with the backend.

## Import

```typescript
import { useOnboardingChat } from '../hooks/useOnboardingChat';
```

## Usage

```typescript
function OnboardingChatPage() {
  const {
    // Progress state
    currentState,
    totalStates,
    completedStates,
    completionPercentage,
    isComplete,
    canComplete,
    
    // Agent state
    currentAgent,
    agentDescription,
    stateMetadata,
    
    // Chat state
    messages,
    isStreaming,
    error,
    
    // Plan state
    pendingPlan,
    planType,
    showPlanPreview,
    
    // Actions
    sendMessage,
    approvePlan,
    modifyPlan,
    closePlanPreview,
    completeOnboarding,
    
    // Loading state
    initialLoadComplete,
  } = useOnboardingChat();
  
  // Use the state and methods in your component
}
```

## Return Value

The hook returns an object with the following properties and methods:

### Progress State

#### `currentState: number`
The current onboarding state (0-8).

- **Type**: `number`
- **Range**: 0-8
- **Example**: `7` (Workout Plan Generation & Approval)

#### `totalStates: number`
Total number of onboarding states.

- **Type**: `number`
- **Value**: `9` (constant)

#### `completedStates: number[]`
Array of completed state numbers.

- **Type**: `number[]`
- **Example**: `[0, 1, 2, 3, 4, 5, 6]`

#### `completionPercentage: number`
Percentage of onboarding completion.

- **Type**: `number`
- **Range**: 0-100
- **Example**: `78` (7 of 9 states completed)

#### `isComplete: boolean`
Whether onboarding is fully complete.

- **Type**: `boolean`
- **Default**: `false`

#### `canComplete: boolean`
Whether user can complete onboarding (all required states done).

- **Type**: `boolean`
- **Default**: `false`
- **Note**: When `true`, the "Complete Onboarding" button should be shown

### Agent State

#### `currentAgent: AgentType | null`
The current onboarding agent handling the conversation.

- **Type**: `AgentType | null`
- **Values**:
  - `'fitness_assessment'`
  - `'goal_setting'`
  - `'workout_planning'`
  - `'diet_planning'`
  - `'scheduling'`

#### `agentDescription: string`
Description of what the current agent does.

- **Type**: `string`
- **Example**: `"Review and approve your workout plan"`

#### `stateMetadata: StateMetadata | null`
Complete metadata for the current state.

- **Type**: `StateMetadata | null`
- **Properties**:
  - `state_number: number` - Current state number
  - `name: string` - State name
  - `agent: AgentType` - Agent handling this state
  - `description: string` - State description
  - `required_fields: string[]` - Required data fields

### Chat State

#### `messages: ChatMessage[]`
Array of all chat messages in the conversation.

- **Type**: `ChatMessage[]`
- **Message Structure**:
  ```typescript
  {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    agentType: AgentType;
    timestamp: string;
    isStreaming?: boolean;
    error?: string;
  }
  ```

#### `isStreaming: boolean`
Whether a message is currently being streamed.

- **Type**: `boolean`
- **Default**: `false`
- **Note**: Use to disable input during streaming

#### `error: string | null`
Current error message, if any.

- **Type**: `string | null`
- **Default**: `null`

### Plan State

#### `pendingPlan: WorkoutPlan | MealPlan | null`
Plan awaiting user approval.

- **Type**: `WorkoutPlan | MealPlan | null`
- **Default**: `null`
- **Note**: Automatically detected from agent responses

#### `planType: 'workout' | 'meal' | null`
Type of the pending plan.

- **Type**: `'workout' | 'meal' | null`
- **Default**: `null`

#### `showPlanPreview: boolean`
Whether to show the plan preview modal.

- **Type**: `boolean`
- **Default**: `false`

### Actions

#### `sendMessage(message: string): Promise<void>`
Send a message to the onboarding agent with streaming support.

**Parameters:**
- `message: string` - The message to send

**Behavior:**
1. Adds user message to chat
2. Creates assistant placeholder with streaming indicator
3. Streams response chunks in real-time
4. Updates progress if state changes
5. Detects and displays plans if present

**Example:**
```typescript
await sendMessage('I am a beginner');
```

**Requirements Validated:**
- TR-2.2: Uses `/chat/onboarding-stream` endpoint
- TR-2.3: Parses `state_updated`, `new_state`, `progress`
- TR-5.1: Handles progress object in streaming response
- TR-5.2: Updates UI when state changes

#### `approvePlan(): void`
Approve the pending workout or meal plan.

**Behavior:**
1. Sends approval message ("Yes, looks perfect!")
2. Closes plan preview
3. Clears pending plan state

**Example:**
```typescript
<button onClick={approvePlan}>Approve Plan</button>
```

**Note:** Only works when not currently streaming

#### `modifyPlan(feedback: string): void`
Request modifications to the pending plan.

**Parameters:**
- `feedback: string` - Modification request message

**Behavior:**
1. Sends feedback message to agent
2. Closes plan preview
3. Agent will generate revised plan

**Example:**
```typescript
<button onClick={() => modifyPlan('Can we add more cardio?')}>
  Request Changes
</button>
```

#### `closePlanPreview(): void`
Close the plan preview modal without taking action.

**Example:**
```typescript
<button onClick={closePlanPreview}>Close</button>
```

#### `completeOnboarding(): Promise<void>`
Complete onboarding and redirect to dashboard.

**Behavior:**
1. Validates `canComplete` is true
2. Calls `/onboarding/complete` endpoint
3. Redirects to `/dashboard` on success
4. Sets error message on failure

**Example:**
```typescript
<button 
  onClick={completeOnboarding}
  disabled={!canComplete}
>
  Complete Onboarding
</button>
```

**Requirements Validated:**
- TR-2.4: Calls `/onboarding/complete` when `can_complete` is true

### Loading State

#### `initialLoadComplete: boolean`
Whether initial progress data has been loaded.

- **Type**: `boolean`
- **Default**: `false`
- **Note**: Use to show loading spinner on mount

## Lifecycle

### On Mount
1. Fetches onboarding progress from `/onboarding/progress`
2. Updates all progress and agent state
3. Redirects to dashboard if already complete
4. Sets `initialLoadComplete` to `true`

### On Message Send
1. Validates message is not empty and not currently streaming
2. Adds user message to chat
3. Creates assistant placeholder
4. Starts SSE streaming connection
5. Updates message content as chunks arrive
6. Handles state updates from backend
7. Detects plans in response
8. Cleans up streaming connection

### On Unmount
- Cancels active streaming connection if present

## Error Handling

The hook handles errors in several scenarios:

### Initial Load Failure
```typescript
if (error) {
  return <div>Error: {error}</div>;
}
```

### Streaming Errors
- Sets error message in state
- Marks message as failed
- Stops streaming indicator

### Completion Errors
- Sets error message
- Does not redirect
- Allows retry

## State Synchronization

The hook maintains synchronization with the backend:

1. **Initial Load**: Fetches complete progress on mount
2. **After State Change**: Refetches progress to get updated metadata
3. **Streaming Updates**: Applies progress updates from stream
4. **Completion**: Validates with backend before redirect

## Plan Detection

Plans are automatically detected in agent responses:

```typescript
// Workout plan detection
if (response.includes('workout plan')) {
  setPendingPlan(workoutPlan);
  setPlanType('workout');
  setShowPlanPreview(true);
}

// Meal plan detection
if (response.includes('meal plan')) {
  setPendingPlan(mealPlan);
  setPlanType('meal');
  setShowPlanPreview(true);
}
```

## Best Practices

### 1. Check Loading State
```typescript
if (!initialLoadComplete) {
  return <LoadingSpinner />;
}
```

### 2. Disable Input During Streaming
```typescript
<input 
  disabled={isStreaming}
  placeholder={isStreaming ? 'Agent is typing...' : 'Type a message'}
/>
```

### 3. Show Error Messages
```typescript
{error && (
  <div className="error-banner">
    {error}
  </div>
)}
```

### 4. Conditional Plan Preview
```typescript
{showPlanPreview && pendingPlan && (
  <PlanPreviewCard
    plan={pendingPlan}
    planType={planType}
    onApprove={approvePlan}
    onModify={modifyPlan}
    onClose={closePlanPreview}
  />
)}
```

### 5. Completion Button
```typescript
{canComplete && (
  <button 
    onClick={completeOnboarding}
    disabled={isStreaming}
  >
    Complete Onboarding
  </button>
)}
```

## TypeScript Types

### UseOnboardingChatReturn
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
  currentAgent: AgentType | null;
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
```

### AgentType
```typescript
enum AgentType {
  FITNESS_ASSESSMENT = 'fitness_assessment',
  GOAL_SETTING = 'goal_setting',
  WORKOUT_PLANNING = 'workout_planning',
  DIET_PLANNING = 'diet_planning',
  SCHEDULING = 'scheduling'
}
```

### StateMetadata
```typescript
interface StateMetadata {
  state_number: number;
  name: string;
  agent: AgentType;
  description: string;
  required_fields: string[];
}
```

### ChatMessage
```typescript
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentType: AgentType;
  timestamp: string;
  isStreaming?: boolean;
  error?: string;
}
```

## Testing

The hook is tested with:

- **Unit Tests**: State management logic
- **Integration Tests**: API interactions
- **Property-Based Tests**: State consistency
- **E2E Tests**: Complete user flows

See `tests/unit/useOnboardingChat.test.ts` for examples.

## Related Documentation

- [Onboarding Service API](./onboardingService-API.md)
- [Component Props Documentation](./component-props.md)
- [Onboarding Flow Guide](./onboarding-flow-guide.md)
- [Migration Guide](./migration-guide.md)

## Support

For issues or questions:
1. Check the troubleshooting section in the main README
2. Review the E2E tests for usage examples
3. Consult the design document in `.kiro/specs/frontend-onboarding-agent-integration/design.md`
