# Design Document

## Overview

This design document outlines the technical approach for updating the Shuren frontend to align with the redesigned 4-step backend onboarding flow. The changes involve updating TypeScript type definitions, React hooks, API services, and UI components to reflect the transition from a 9-step to a 4-step onboarding process with four specialized agents instead of five.

The design maintains backward compatibility where possible while ensuring type safety, proper state management, and responsive UI across all device sizes.

## Architecture

### High-Level Architecture

The frontend onboarding system follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Components Layer                      │
│  (OnboardingChatPage, AgentHeader, OnboardingProgressBar)   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   React Hooks Layer                          │
│              (useOnboardingChat hook)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Service Layer                               │
│            (onboardingService)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Type System                                │
│         (onboarding.types.ts)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                Backend API (FastAPI)                         │
│         4-Step Onboarding Flow                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Initialization**: Component mounts → Hook fetches progress from API → Updates local state
2. **User Interaction**: User sends message → Hook calls service → Service streams from API → Hook updates state → Component re-renders
3. **State Transitions**: Backend advances step → Progress update in stream → Hook fetches fresh metadata → UI updates

### Key Design Decisions

1. **Minimal Breaking Changes**: Update types and constants while preserving interface structures
2. **Progressive Enhancement**: Update components incrementally without requiring full rewrite
3. **Type Safety First**: Ensure TypeScript catches mismatches between frontend and backend
4. **Responsive Design**: Maintain existing mobile-first approach with 4-step UI

## Components and Interfaces

### Type System Updates

#### Updated AgentType Enum

```typescript
// frontend/src/types/onboarding.types.ts

/**
 * Agent types for 4-step onboarding flow
 * Maps to backend OnboardingAgentType enum
 */
export const AgentType = {
  FITNESS_ASSESSMENT: 'fitness_assessment',
  WORKOUT_PLANNING: 'workout_planning',
  DIET_PLANNING: 'diet_planning',
  SCHEDULING: 'scheduling'
} as const;

export type AgentType = typeof AgentType[keyof typeof AgentType];
```

**Changes:**
- Remove `GOAL_SETTING: 'goal_setting'` entry
- Keep remaining 4 agent types unchanged

#### Updated OnboardingProgress Interface

```typescript
/**
 * Onboarding progress response
 * Returned by GET /api/v1/onboarding/progress
 */
export interface OnboardingProgress {
  current_state: number;        // 1-4
  total_states: number;          // Always 4
  completed_states: number[];    // Array of completed step numbers (1-4)
  is_complete: boolean;
  completion_percentage: number; // 0-100
  can_complete: boolean;
  current_state_info: StateMetadata;
  next_state_info: StateMetadata | null;
}
```

**Changes:**
- Update JSDoc comments to reflect 1-4 range
- Update `total_states` comment to "Always 4"
- No structural changes needed

#### Updated StateMetadata Interface

```typescript
/**
 * State metadata for UI rendering
 * Provides information about each onboarding step (1-4)
 */
export interface StateMetadata {
  state_number: number;      // 1-4
  name: string;              // e.g., "Fitness Assessment"
  agent: AgentType;          // One of 4 agent types
  description: string;
  required_fields: string[];
}
```

**Changes:**
- Update JSDoc to reference "step (1-4)" instead of "state"
- No structural changes needed

#### New Step Completion Interface

```typescript
/**
 * Step completion flags for 4-step flow
 * Used internally to track which steps are complete
 */
export interface StepCompletionFlags {
  step_1_complete: boolean;
  step_2_complete: boolean;
  step_3_complete: boolean;
  step_4_complete: boolean;
}
```

**Purpose:** Provides type-safe access to step completion flags from backend

### Hook Updates

#### useOnboardingChat Hook

**Key Changes:**

1. **Update totalStates constant:**
```typescript
const [totalStates] = useState<number>(4);  // Changed from 9
```

2. **Update state validation:**
```typescript
// Ensure currentState is always 1-4
const validateState = (state: number): number => {
  return Math.max(1, Math.min(4, state));
};
```

3. **Update progress calculation:**
```typescript
// Calculate completion percentage based on 4 steps
const calculatePercentage = (completed: number[]): number => {
  return Math.round((completed.length / 4) * 100);
};
```

4. **Update agent type handling:**
```typescript
// Remove GOAL_SETTING from agent type checks
const isValidAgent = (agent: string): agent is OnboardingAgentType => {
  return ['fitness_assessment', 'workout_planning', 'diet_planning', 'scheduling']
    .includes(agent);
};
```

**No changes needed for:**
- Streaming logic
- Message handling
- Plan detection
- Error handling

### Service Layer Updates

#### onboardingService

**Key Changes:**

1. **Update request validation:**
```typescript
streamOnboardingMessage(
  message: string,
  currentState: number,  // Now expects 1-4
  callbacks: StreamCallbacks
): () => void {
  // Validate state is 1-4
  if (currentState < 1 || currentState > 4) {
    console.warn(`Invalid state ${currentState}, clamping to valid range`);
    currentState = Math.max(1, Math.min(4, currentState));
  }
  
  // Rest of implementation unchanged
}
```

2. **Update response parsing:**
```typescript
// Handle progress updates with 4-step structure
onComplete: (data: OnboardingStreamChunk) => {
  if (data.progress) {
    // Validate completed_states contains only 1-4
    const validCompletedStates = data.progress.completed_states
      .filter(s => s >= 1 && s <= 4);
    
    // Update with validated data
    callbacks.onComplete({
      ...data,
      progress: {
        ...data.progress,
        completed_states: validCompletedStates,
        total_states: 4
      }
    });
  }
}
```

**No changes needed for:**
- API endpoint URLs
- Authentication handling
- Error handling
- Retry logic

### UI Component Updates

#### AgentHeader Component

**Key Changes:**

1. **Update agent name mapping:**
```typescript
const getAgentName = (type: OnboardingAgentType): string => {
  const agentNames: Record<OnboardingAgentType, string> = {
    [AgentType.FITNESS_ASSESSMENT]: 'Fitness Assessment Agent',
    [AgentType.WORKOUT_PLANNING]: 'Workout Planning Agent',
    [AgentType.DIET_PLANNING]: 'Diet Planning Agent',
    [AgentType.SCHEDULING]: 'Scheduling Agent',
    // GOAL_SETTING removed
  };
  return agentNames[type];
};
```

2. **Update agent icon mapping:**
```typescript
const getAgentIcon = (type: OnboardingAgentType): string => {
  const agentIcons: Record<OnboardingAgentType, string> = {
    [AgentType.FITNESS_ASSESSMENT]: '💪',
    [AgentType.WORKOUT_PLANNING]: '🏋️',
    [AgentType.DIET_PLANNING]: '🥗',
    [AgentType.SCHEDULING]: '📅',
    // GOAL_SETTING (🎯) removed
  };
  return agentIcons[type];
};
```

3. **Update color theme mapping:**
```typescript
const getAgentColorClass = (type: OnboardingAgentType): string => {
  const agentColors: Record<OnboardingAgentType, string> = {
    [AgentType.FITNESS_ASSESSMENT]: 'bg-purple-600',
    [AgentType.WORKOUT_PLANNING]: 'bg-green-600',
    [AgentType.DIET_PLANNING]: 'bg-orange-600',
    [AgentType.SCHEDULING]: 'bg-indigo-600',
    // GOAL_SETTING (bg-blue-600) removed
  };
  return agentColors[type];
};
```

#### OnboardingProgressBar Component

**Key Changes:**

1. **Update state definitions:**
```typescript
// Define all 4 onboarding steps with their names
const allStates = [
  { number: 1, name: 'Fitness Assessment', agent: 'fitness_assessment' },
  { number: 2, name: 'Workout Planning', agent: 'workout_planning' },
  { number: 3, name: 'Diet Planning', agent: 'diet_planning' },
  { number: 4, name: 'Scheduling', agent: 'scheduling' },
];
```

2. **Update progress calculation:**
```typescript
// Progress bar width calculation (unchanged, but now based on 4 steps)
<div
  className="bg-blue-600 h-full rounded-full transition-all duration-500 ease-out"
  style={{ width: `${completionPercentage}%` }}
/>
```

3. **Update step status logic:**
```typescript
const getStateStatus = (stateNumber: number): 'completed' | 'current' | 'upcoming' => {
  // Validate state number is 1-4
  if (stateNumber < 1 || stateNumber > 4) {
    return 'upcoming';
  }
  
  if (completedStates.includes(stateNumber)) {
    return 'completed';
  }
  if (stateNumber === currentState) {
    return 'current';
  }
  return 'upcoming';
};
```

4. **Update mobile layout:**
```typescript
// Mobile collapsible content - now shows 4 steps instead of 9
<div className="space-y-2">
  <h3 className="text-xs font-medium text-gray-700 mb-2">All Steps</h3>
  {allStates.map((state) => {
    // Render 4 steps with same styling
  })}
</div>
```

#### OnboardingChatPage Component

**Key Changes:**

1. **Update completion message:**
```typescript
{canComplete && !isComplete && (
  <div className="mt-6 p-6 bg-green-50 border-2 border-green-300 rounded-lg">
    <div className="text-center">
      <h3 className="text-xl font-bold text-green-900 mb-2">
        <span role="img" aria-label="celebration">🎉</span> Onboarding Complete!
      </h3>
      <p className="text-green-800 mb-4">
        You've completed all 4 onboarding steps. Click below to finalize your profile and start your fitness journey!
      </p>
      {/* Button unchanged */}
    </div>
  </div>
)}
```

**No other changes needed** - component uses hook state which will automatically reflect 4-step flow

## Data Models

### Step Metadata Structure

Each of the 4 steps has the following metadata structure:

```typescript
interface StepMetadata {
  state_number: number;
  name: string;
  agent: AgentType;
  description: string;
  required_fields: string[];
}
```

**Step 1: Fitness Assessment**
```typescript
{
  state_number: 1,
  name: "Fitness Assessment",
  agent: "fitness_assessment",
  description: "Assess your current fitness level and goals",
  required_fields: ["fitness_level", "experience_years", "primary_goal", "target_weight"]
}
```

**Step 2: Workout Planning**
```typescript
{
  state_number: 2,
  name: "Workout Planning",
  agent: "workout_planning",
  description: "Create your personalized workout plan",
  required_fields: ["equipment", "injuries", "limitations", "days_per_week", "workout_schedule"]
}
```

**Step 3: Diet Planning**
```typescript
{
  state_number: 3,
  name: "Diet Planning",
  agent: "diet_planning",
  description: "Build your personalized meal plan",
  required_fields: ["diet_type", "allergies", "restrictions", "meal_frequency", "meal_schedule"]
}
```

**Step 4: Scheduling**
```typescript
{
  state_number: 4,
  name: "Scheduling",
  agent: "scheduling",
  description: "Set up your hydration and supplement reminders",
  required_fields: ["hydration_schedule", "supplement_preferences"]
}
```

### Progress State Model

```typescript
interface ProgressState {
  // Current step (1-4)
  currentStep: number;
  
  // Total steps (always 4)
  totalSteps: 4;
  
  // Completed steps array (e.g., [1, 2] means steps 1 and 2 are done)
  completedSteps: number[];
  
  // Completion percentage (0, 25, 50, 75, or 100)
  completionPercentage: number;
  
  // Whether all steps are complete
  isComplete: boolean;
  
  // Whether user can finalize onboarding
  canComplete: boolean;
  
  // Current step metadata
  currentStepInfo: StepMetadata;
  
  // Next step metadata (null if on step 4)
  nextStepInfo: StepMetadata | null;
}
```

### Agent Context Model

The agent context structure remains unchanged but now only contains data for 4 agents:

```typescript
interface AgentContext {
  fitness_assessment?: {
    fitness_level: string;
    experience_years: number;
    primary_goal: string;
    target_weight?: number;
    completed_at: string;
  };
  
  workout_planning?: {
    equipment: string[];
    injuries: string[];
    limitations: string[];
    days_per_week: number;
    workout_schedule: WorkoutSchedule[];
    completed_at: string;
  };
  
  diet_planning?: {
    diet_type: string;
    allergies: string[];
    restrictions: string[];
    meal_frequency: number;
    meal_schedule: MealSchedule[];
    completed_at: string;
  };
  
  scheduling?: {
    hydration_schedule: HydrationSchedule;
    supplement_preferences: SupplementPreferences;
    completed_at: string;
  };
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Agent Type Enum Completeness

*For any* agent type string received from the backend API, it should match exactly one of the four valid agent types: FITNESS_ASSESSMENT, WORKOUT_PLANNING, DIET_PLANNING, or SCHEDULING.

**Validates: Requirements 1.1, 3.4**

### Property 2: Progress Percentage Calculation

*For any* number of completed steps (0 through 4), the completion percentage should equal (completed_steps / 4) * 100, rounded to the nearest integer.

**Validates: Requirements 2.2, 5.3, 9.1, 9.2, 9.3, 9.4, 9.5**

### Property 3: State Number Range Validation

*For any* StateMetadata object or progress update, the state_number field should be an integer between 1 and 4 (inclusive).

**Validates: Requirements 1.4, 5.4**

### Property 4: Completed States Array Validation

*For any* completed_states array received from the backend, all values should be integers between 1 and 4, and the system should filter out any invalid values.

**Validates: Requirements 2.3**

### Property 5: State Input Clamping

*For any* current_state value passed to streamOnboardingMessage, if the value is outside the range 1-4, it should be clamped to the nearest valid value (1 or 4).

**Validates: Requirements 3.2**

### Property 6: State Transition Sequence

*For any* state transition from step N where N is between 1 and 3, the next state should be N+1.

**Validates: Requirements 3.5**

### Property 7: Metadata Fetching for Valid Steps

*For any* step number between 1 and 4, the system should be able to fetch and display metadata for that step.

**Validates: Requirements 4.3**

### Property 8: Current State Handling in Streaming

*For any* streaming response containing a currentState value, if the value is between 1 and 4, the system should process it without errors.

**Validates: Requirements 4.2**

### Property 9: Step Name Mapping Consistency

*For any* step number between 1 and 4, the system should consistently map it to the correct step name: 1→"Fitness Assessment", 2→"Workout Planning", 3→"Diet Planning", 4→"Scheduling".

**Validates: Requirements 2.4, 8.1, 8.2, 8.3, 8.4**

## Error Handling

### Type Safety Errors

**Invalid Agent Type:**
- **Detection**: TypeScript compiler catches invalid agent type assignments
- **Handling**: Compile-time error prevents deployment
- **User Impact**: None (caught during development)

**Invalid State Number:**
- **Detection**: Runtime validation in service layer
- **Handling**: Clamp to valid range (1-4) and log warning
- **User Impact**: Minimal - system continues with corrected value

### API Response Errors

**Missing total_states Field:**
- **Detection**: Response validation in service layer
- **Handling**: Default to 4 and log warning
- **User Impact**: None - system uses correct default

**Invalid completed_states Values:**
- **Detection**: Array validation in hook
- **Handling**: Filter out invalid values, keep only 1-4
- **User Impact**: None - progress displays correctly

**Unknown Agent Type:**
- **Detection**: Agent type validation in hook
- **Handling**: Fall back to FITNESS_ASSESSMENT and log error
- **User Impact**: Minimal - user sees default agent

### UI Rendering Errors

**Missing Step Metadata:**
- **Detection**: Null check in component
- **Handling**: Display loading state or placeholder
- **User Impact**: Temporary - resolves when metadata loads

**Progress Calculation Overflow:**
- **Detection**: Percentage validation (0-100 range)
- **Handling**: Clamp to 0-100 range
- **User Impact**: None - progress displays correctly

### State Synchronization Errors

**Backend Returns State > 4:**
- **Detection**: State validation in hook
- **Handling**: Clamp to 4 and fetch fresh progress
- **User Impact**: Minimal - system self-corrects

**Completed States Out of Order:**
- **Detection**: Array sorting in progress tracker
- **Handling**: Sort array before display
- **User Impact**: None - progress displays correctly

## Testing Strategy

### Unit Testing Approach

The frontend onboarding integration will use **Jest** and **React Testing Library** for unit tests, focusing on:

1. **Type Definition Tests** - Verify enum structures and interface shapes
2. **Hook Logic Tests** - Test state management and calculations
3. **Component Rendering Tests** - Verify UI displays correct content
4. **Service Layer Tests** - Test API communication and data transformation

**Unit Test Focus Areas:**
- Specific examples of state transitions (1→2, 2→3, 3→4)
- Edge cases (state 0, state 5, negative states)
- Error conditions (missing data, invalid responses)
- Component prop validation
- Accessibility attribute presence

### Property-Based Testing Approach

Property-based tests will use **fast-check** library to verify universal properties across randomized inputs:

**Configuration:**
- Minimum 100 iterations per property test
- Custom generators for valid state numbers (1-4)
- Custom generators for agent types
- Custom generators for progress data structures

**Property Test Implementation:**

Each correctness property will be implemented as a single property-based test with appropriate tagging:

```typescript
// Example property test structure
import fc from 'fast-check';

describe('Property Tests: Frontend Onboarding Integration', () => {
  it('Property 2: Progress Percentage Calculation', () => {
    // Feature: frontend-onboarding-integration, Property 2: Progress percentage calculation
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 4 }), // completed steps
        (completedSteps) => {
          const percentage = calculatePercentage(completedSteps);
          const expected = Math.round((completedSteps / 4) * 100);
          expect(percentage).toBe(expected);
        }
      ),
      { numRuns: 100 }
    );
  });
  
  it('Property 3: State Number Range Validation', () => {
    // Feature: frontend-onboarding-integration, Property 3: State number range validation
    fc.assert(
      fc.property(
        fc.record({
          state_number: fc.integer({ min: 1, max: 4 }),
          name: fc.string(),
          agent: fc.constantFrom('fitness_assessment', 'workout_planning', 'diet_planning', 'scheduling'),
          description: fc.string(),
          required_fields: fc.array(fc.string())
        }),
        (metadata) => {
          expect(metadata.state_number).toBeGreaterThanOrEqual(1);
          expect(metadata.state_number).toBeLessThanOrEqual(4);
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### Testing Library Selection

**Jest**: Primary testing framework
- Built-in mocking capabilities
- Snapshot testing for components
- Code coverage reporting
- Fast parallel test execution

**React Testing Library**: Component testing
- User-centric testing approach
- Accessibility-focused queries
- Async utilities for hooks
- Integration with Jest

**fast-check**: Property-based testing
- Randomized input generation
- Shrinking for minimal failing examples
- Custom generators for domain types
- TypeScript support

### Test Organization

```
frontend/src/
├── types/
│   └── __tests__/
│       └── onboarding.types.test.ts
├── hooks/
│   └── __tests__/
│       ├── useOnboardingChat.test.ts
│       └── useOnboardingChat.properties.test.ts
├── services/
│   └── __tests__/
│       ├── onboardingService.test.ts
│       └── onboardingService.properties.test.ts
└── components/
    └── onboarding/
        └── __tests__/
            ├── AgentHeader.test.tsx
            ├── OnboardingProgressBar.test.tsx
            ├── OnboardingProgressBar.properties.test.tsx
            └── OnboardingChatPage.test.tsx
```

### Coverage Goals

- **Unit Test Coverage**: 80%+ for business logic
- **Property Test Coverage**: All 9 correctness properties implemented
- **Component Coverage**: 90%+ for onboarding components
- **Integration Coverage**: End-to-end flow from API to UI

### Test Execution

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run property tests only
npm test -- --testNamePattern="Property"

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test -- useOnboardingChat.test.ts
```

## Implementation Notes

### Migration Strategy

1. **Phase 1: Type Updates** (Low Risk)
   - Update AgentType enum
   - Update interface comments
   - Add new interfaces
   - No runtime changes

2. **Phase 2: Hook Updates** (Medium Risk)
   - Update totalStates constant
   - Add validation functions
   - Update state calculations
   - Test thoroughly

3. **Phase 3: Component Updates** (Medium Risk)
   - Update AgentHeader mappings
   - Update OnboardingProgressBar state list
   - Update step metadata
   - Test UI rendering

4. **Phase 4: Service Updates** (Low Risk)
   - Add input validation
   - Add response validation
   - No API contract changes

### Backward Compatibility Considerations

**Preserved Interfaces:**
- `OnboardingProgress` structure unchanged
- `StateMetadata` structure unchanged
- `OnboardingStreamChunk` structure unchanged
- Streaming callback signatures unchanged

**Breaking Changes:**
- `AgentType` enum loses GOAL_SETTING value
- Components expecting 9 states will break
- Hardcoded state checks for 5-9 will fail

**Migration Path:**
- Update all imports of AgentType
- Search and replace "9" with "4" in onboarding context
- Remove GOAL_SETTING references
- Update tests to expect 4 steps

### Performance Considerations

**No Performance Impact Expected:**
- Fewer states means less data to process
- Fewer UI elements to render (4 vs 9 progress indicators)
- Same streaming mechanism
- Same API call patterns

**Potential Improvements:**
- Faster progress bar animations (fewer steps)
- Reduced memory footprint (less state metadata)
- Simpler state validation logic

### Accessibility Considerations

**Maintained Accessibility:**
- ARIA labels updated to reflect 4 steps
- Progress bar aria-valuenow updated
- Screen reader announcements updated
- Keyboard navigation unchanged

**Improved Accessibility:**
- Simpler progress structure easier to understand
- Fewer steps to navigate through
- Clearer step names

### Browser Compatibility

**No New Browser Requirements:**
- Uses existing React patterns
- No new CSS features
- No new JavaScript features
- Same browser support as before (modern browsers)

### Mobile Considerations

**Improved Mobile Experience:**
- Fewer progress indicators fit better on small screens
- Less scrolling needed in progress sidebar
- Simpler mental model for users
- Faster completion (4 steps vs 9)

**Responsive Breakpoints:**
- Mobile: < 1024px (collapsible progress)
- Desktop: >= 1024px (sidebar progress)
- Touch targets: Minimum 44x44px maintained

## Deployment Considerations

### Deployment Strategy

**Recommended Approach: Feature Flag**

1. Deploy frontend changes behind feature flag
2. Enable for internal testing
3. Monitor for errors
4. Gradually roll out to users
5. Remove feature flag after stable

**Alternative Approach: Big Bang**

1. Deploy backend changes first
2. Deploy frontend changes immediately after
3. Monitor closely for issues
4. Rollback plan ready

### Rollback Plan

**If Issues Detected:**

1. **Immediate**: Revert frontend deployment
2. **Short-term**: Fix issues in development
3. **Long-term**: Re-deploy with fixes

**Rollback Triggers:**
- Error rate > 5%
- User complaints about progress tracking
- State synchronization failures
- Agent type errors

### Monitoring

**Key Metrics to Monitor:**

1. **Error Rates**
   - Invalid agent type errors
   - State validation errors
   - API response parsing errors

2. **User Behavior**
   - Onboarding completion rate
   - Time to complete onboarding
   - Step abandonment rates

3. **Performance**
   - Page load times
   - API response times
   - Streaming latency

**Alerting Thresholds:**
- Error rate > 1%: Warning
- Error rate > 5%: Critical
- Completion rate drop > 10%: Warning
- API latency > 2s: Warning

## Future Enhancements

### Potential Improvements

1. **Step Validation**
   - Add client-side validation for required fields
   - Show validation errors inline
   - Prevent advancing with incomplete data

2. **Progress Persistence**
   - Save progress to localStorage
   - Resume from last step on refresh
   - Sync with backend periodically

3. **Step Navigation**
   - Allow users to go back to previous steps
   - Edit previous step data
   - Preview all collected data

4. **Enhanced Feedback**
   - Show estimated time remaining
   - Display step-specific tips
   - Provide progress milestones

5. **Analytics Integration**
   - Track step completion times
   - Identify drop-off points
   - A/B test step ordering

### Extensibility

**Adding New Steps:**

If future requirements add a 5th step:

1. Update `totalStates` constant to 5
2. Add new agent type to enum
3. Add step metadata to allStates array
4. Update percentage calculation (divide by 5)
5. Add new agent mappings (name, icon, color)
6. Update tests to expect 5 steps

**Adding New Agent Types:**

If new agents are added:

1. Add to AgentType enum
2. Add to agent name mapping
3. Add to agent icon mapping
4. Add to agent color mapping
5. Update type guards
6. Update tests

## Conclusion

This design provides a comprehensive approach to updating the Shuren frontend for the 4-step onboarding flow. The changes are minimal and focused, maintaining backward compatibility where possible while ensuring type safety and proper state management.

The key design principles are:
- **Type Safety**: TypeScript catches mismatches at compile time
- **Progressive Enhancement**: Update incrementally without breaking existing code
- **User Experience**: Maintain smooth, responsive UI across all devices
- **Testability**: Comprehensive unit and property-based test coverage
- **Maintainability**: Clean, well-documented code with clear separation of concerns

The implementation follows React best practices, maintains accessibility standards, and provides a solid foundation for future enhancements.
