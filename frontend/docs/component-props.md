# Onboarding Components - Props and Usage Documentation

This document provides comprehensive documentation for all onboarding-related components, their props, and usage examples.

## Table of Contents

1. [AgentHeader](#agentheader)
2. [OnboardingProgressBar](#onboardingprogressbar)
3. [PlanPreviewCard](#planpreviewcard)
4. [WorkoutPlanPreview](#workoutplanpreview)
5. [MealPlanPreview](#mealplanpreview)
6. [OnboardingChatPage](#onboardingchatpage)

---

## AgentHeader

Displays current agent context and state information at the top of the onboarding chat.

### Props

```typescript
interface AgentHeaderProps {
  agentType: AgentType;
  agentDescription: string;
  currentState: number;
  totalStates: number;
  stateName: string;
}
```

#### `agentType: AgentType` (required)

The type of the current onboarding agent.

- **Type**: `AgentType` enum
- **Values**:
  - `AgentType.FITNESS_ASSESSMENT` - Fitness Assessment Agent (💪)
  - `AgentType.GOAL_SETTING` - Goal Setting Agent (🎯)
  - `AgentType.WORKOUT_PLANNING` - Workout Planning Agent (🏋️)
  - `AgentType.DIET_PLANNING` - Diet Planning Agent (🥗)
  - `AgentType.SCHEDULING` - Scheduling Agent (📅)

#### `agentDescription: string` (required)

Description of what the current agent does.

- **Type**: `string`
- **Example**: `"Review and approve your workout plan"`

#### `currentState: number` (required)

The current onboarding state number.

- **Type**: `number`
- **Range**: 0-8

#### `totalStates: number` (required)

Total number of onboarding states.

- **Type**: `number`
- **Value**: `9`

#### `stateName: string` (required)

Name of the current state.

- **Type**: `string`
- **Example**: `"Workout Plan Generation & Approval"`

### Usage Example

```typescript
import { AgentHeader } from '../components/onboarding/AgentHeader';
import { AgentType } from '../types/onboarding.types';

function OnboardingPage() {
  return (
    <AgentHeader
      agentType={AgentType.WORKOUT_PLANNING}
      agentDescription="Review and approve your workout plan"
      currentState={7}
      totalStates={9}
      stateName="Workout Plan Generation & Approval"
    />
  );
}
```

### Features

- **Color-coded by agent**: Each agent has a unique background color
- **Responsive design**: Adapts layout for mobile and desktop
- **Sticky header**: Remains visible while scrolling
- **Smooth transitions**: Animated agent changes
- **Accessibility**: ARIA labels and semantic HTML

### Styling

The component uses Tailwind CSS with agent-specific color themes:
- Fitness Assessment: Purple (`bg-purple-600`)
- Goal Setting: Blue (`bg-blue-600`)
- Workout Planning: Green (`bg-green-600`)
- Diet Planning: Orange (`bg-orange-600`)
- Scheduling: Indigo (`bg-indigo-600`)

---

## OnboardingProgressBar

Displays visual progress through onboarding states with a progress bar, state list, and status indicators.

### Props

```typescript
interface OnboardingProgressBarProps {
  currentState: number;
  totalStates: number;
  completionPercentage: number;
  stateMetadata: StateMetadata | null;
  completedStates: number[];
}
```

#### `currentState: number` (required)

The current onboarding state number.

- **Type**: `number`
- **Range**: 0-8

#### `totalStates: number` (required)

Total number of onboarding states.

- **Type**: `number`
- **Value**: `9`

#### `completionPercentage: number` (required)

Percentage of onboarding completion.

- **Type**: `number`
- **Range**: 0-100

#### `stateMetadata: StateMetadata | null` (required)

Complete metadata for the current state.

- **Type**: `StateMetadata | null`
- **Structure**:
  ```typescript
  {
    state_number: number;
    name: string;
    agent: AgentType;
    description: string;
    required_fields: string[];
  }
  ```

#### `completedStates: number[]` (required)

Array of completed state numbers.

- **Type**: `number[]`
- **Example**: `[0, 1, 2, 3, 4, 5, 6]`

### Usage Example

```typescript
import { OnboardingProgressBar } from '../components/onboarding/OnboardingProgressBar';

function OnboardingPage() {
  const { 
    currentState, 
    totalStates, 
    completionPercentage, 
    stateMetadata, 
    completedStates 
  } = useOnboardingChat();

  return (
    <OnboardingProgressBar
      currentState={currentState}
      totalStates={totalStates}
      completionPercentage={completionPercentage}
      stateMetadata={stateMetadata}
      completedStates={completedStates}
    />
  );
}
```

### Features

- **Visual progress bar**: Animated fill showing completion percentage
- **State list**: All 9 states with status indicators
- **Status icons**:
  - ✓ Checkmark for completed states (green)
  - → Arrow for current state (blue, pulsing)
  - ○ Circle for upcoming states (gray)
- **Responsive design**:
  - Desktop: Fixed sidebar on left (300px wide)
  - Mobile: Collapsible panel at top
- **Smooth animations**: State transitions and progress updates
- **Accessibility**: ARIA labels, progressbar role, keyboard support

### State Status

Each state can have one of three statuses:

1. **Completed**: State is in `completedStates` array
2. **Current**: State number matches `currentState`
3. **Upcoming**: State number is greater than `currentState`

---

## PlanPreviewCard

Displays workout or meal plans in a modal/slide-in panel for user review and approval.

### Props

```typescript
interface PlanPreviewCardProps {
  plan: WorkoutPlan | MealPlan;
  planType: 'workout' | 'meal';
  onApprove: () => void;
  onModify: (feedback: string) => void;
  onClose: () => void;
}
```

#### `plan: WorkoutPlan | MealPlan` (required)

The plan data to display.

- **Type**: `WorkoutPlan | MealPlan`
- **Note**: Type depends on `planType` prop

#### `planType: 'workout' | 'meal'` (required)

Type of plan being displayed.

- **Type**: `'workout' | 'meal'`
- **Values**:
  - `'workout'` - Displays WorkoutPlanPreview
  - `'meal'` - Displays MealPlanPreview

#### `onApprove: () => void` (required)

Callback function when user approves the plan.

- **Type**: `() => void`
- **Behavior**: Called when "Approve Plan" button is clicked

#### `onModify: (feedback: string) => void` (required)

Callback function when user requests modifications.

- **Type**: `(feedback: string) => void`
- **Parameters**:
  - `feedback: string` - User's modification request
- **Behavior**: Called when user submits modification feedback

#### `onClose: () => void` (required)

Callback function when user closes the preview.

- **Type**: `() => void`
- **Behavior**: Called when close button (X) is clicked or Escape key is pressed

### Usage Example

```typescript
import { PlanPreviewCard } from '../components/onboarding/PlanPreviewCard';

function OnboardingPage() {
  const { 
    pendingPlan, 
    planType, 
    showPlanPreview,
    approvePlan,
    modifyPlan,
    closePlanPreview
  } = useOnboardingChat();

  return (
    <>
      {showPlanPreview && pendingPlan && (
        <PlanPreviewCard
          plan={pendingPlan}
          planType={planType!}
          onApprove={approvePlan}
          onModify={modifyPlan}
          onClose={closePlanPreview}
        />
      )}
    </>
  );
}
```

### Features

- **Modal overlay**: Semi-transparent background
- **Slide-in panel**: Animates from bottom (mobile) or right (desktop)
- **Scrollable content**: Long plans can be scrolled
- **Two-step modification**: Click "Request Changes" → Enter feedback → Submit
- **Keyboard support**:
  - Escape key closes preview or cancels modification
- **Responsive design**:
  - Mobile: Full-width bottom sheet
  - Desktop: Right sidebar (600-700px wide)
- **Accessibility**: Dialog role, modal attributes, focus management

### Action Flow

1. **Approve**: Click "Approve Plan" → `onApprove()` called → Preview closes
2. **Modify**: Click "Request Changes" → Enter feedback → Click "Send Feedback" → `onModify(feedback)` called → Preview closes
3. **Close**: Click X or press Escape → `onClose()` called → Preview closes

---

## WorkoutPlanPreview

Displays detailed workout plan information within PlanPreviewCard.

### Props

```typescript
interface WorkoutPlanPreviewProps {
  plan: WorkoutPlan;
}
```

#### `plan: WorkoutPlan` (required)

The workout plan data to display.

- **Type**: `WorkoutPlan`
- **Structure**:
  ```typescript
  {
    frequency: number;           // Days per week
    location: string;             // Home, Gym, etc.
    duration_minutes: number;     // Minutes per session
    equipment: string[];          // Required equipment
    days: WorkoutDay[];           // Day-by-day breakdown
  }
  ```

### Usage Example

```typescript
import { WorkoutPlanPreview } from '../components/onboarding/WorkoutPlanPreview';

function PlanCard() {
  const workoutPlan: WorkoutPlan = {
    frequency: 3,
    location: 'Home',
    duration_minutes: 45,
    equipment: ['Dumbbells', 'Resistance bands'],
    days: [
      {
        day_number: 1,
        name: 'Upper Body',
        exercises: [
          {
            name: 'Dumbbell Press',
            sets: 3,
            reps: '10-12',
            rest_seconds: 60,
            notes: 'Focus on controlled movement'
          }
        ]
      }
    ]
  };

  return <WorkoutPlanPreview plan={workoutPlan} />;
}
```

### Display Sections

1. **Plan Summary**: Frequency, location, duration
2. **Equipment List**: Required equipment
3. **Day-by-Day Breakdown**: Each workout day with:
   - Day number and name
   - Exercise list with sets, reps, rest
   - Exercise notes (if present)

---

## MealPlanPreview

Displays detailed meal plan information within PlanPreviewCard.

### Props

```typescript
interface MealPlanPreviewProps {
  plan: MealPlan;
}
```

#### `plan: MealPlan` (required)

The meal plan data to display.

- **Type**: `MealPlan`
- **Structure**:
  ```typescript
  {
    diet_type: string;            // Vegetarian, Vegan, etc.
    meal_frequency: number;       // Meals per day
    daily_calories: number;       // Target calories
    macros: MacroBreakdown;       // Protein, carbs, fats
    sample_meals: SampleMeal[];   // Sample meal list
  }
  ```

### Usage Example

```typescript
import { MealPlanPreview } from '../components/onboarding/MealPlanPreview';

function PlanCard() {
  const mealPlan: MealPlan = {
    diet_type: 'Vegetarian',
    meal_frequency: 4,
    daily_calories: 2000,
    macros: {
      protein_g: 120,
      carbs_g: 220,
      fats_g: 67
    },
    sample_meals: [
      {
        meal_number: 1,
        name: 'Breakfast',
        calories: 500,
        protein_g: 25,
        carbs_g: 60,
        fats_g: 15,
        foods: ['Oatmeal', 'Berries', 'Almond butter']
      }
    ]
  };

  return <MealPlanPreview plan={mealPlan} />;
}
```

### Display Sections

1. **Plan Summary**: Calorie target, diet type, meal frequency
2. **Macro Breakdown**: Protein, carbs, fats (grams and percentages)
3. **Sample Meals**: Each meal with:
   - Meal number and name
   - Calorie and macro information
   - Food list

---

## OnboardingChatPage

Main container component for the agent-based onboarding flow.

### Props

None - uses `useOnboardingChat` hook internally.

### Usage Example

```typescript
import { OnboardingChatPage } from '../pages/OnboardingChatPage';

// In your router
<Route path="/onboarding" element={<OnboardingChatPage />} />
```

### Component Structure

```typescript
function OnboardingChatPage() {
  const {
    // All state and methods from useOnboardingChat
  } = useOnboardingChat();

  return (
    <div className="h-screen flex flex-col">
      <AgentHeader {...agentProps} />
      
      <div className="flex-1 flex overflow-hidden">
        <OnboardingProgressBar {...progressProps} />
        
        <div className="flex-1 flex flex-col">
          <MessageList messages={messages} />
          <MessageInput onSend={sendMessage} disabled={isStreaming} />
        </div>
      </div>

      {showPlanPreview && (
        <PlanPreviewCard {...planProps} />
      )}

      {canComplete && (
        <CompleteButton onClick={completeOnboarding} />
      )}
    </div>
  );
}
```

### Features

- **Full-screen layout**: Optimized for chat experience
- **Responsive design**: Adapts to all screen sizes
- **State management**: Uses `useOnboardingChat` hook
- **Error handling**: Displays error messages
- **Loading states**: Shows loading indicators
- **Completion flow**: Shows completion button when ready

---

## Common Patterns

### Conditional Rendering

```typescript
// Show component only when data is available
{stateMetadata && (
  <AgentHeader
    agentType={stateMetadata.agent}
    agentDescription={stateMetadata.description}
    currentState={currentState}
    totalStates={totalStates}
    stateName={stateMetadata.name}
  />
)}
```

### Loading States

```typescript
// Show loading spinner until data loads
if (!initialLoadComplete) {
  return <LoadingSpinner />;
}

return <OnboardingProgressBar {...props} />;
```

### Error Handling

```typescript
// Display error messages
{error && (
  <div className="error-banner">
    {error}
  </div>
)}
```

### Disabled States

```typescript
// Disable input during streaming
<MessageInput
  onSend={sendMessage}
  disabled={isStreaming}
  placeholder={isStreaming ? 'Agent is typing...' : 'Type a message'}
/>
```

---

## Accessibility Guidelines

All components follow WCAG AA standards:

1. **Semantic HTML**: Proper use of headings, landmarks, buttons
2. **ARIA Labels**: Descriptive labels for all interactive elements
3. **Keyboard Navigation**: Full keyboard support
4. **Focus Management**: Visible focus indicators
5. **Color Contrast**: Minimum 4.5:1 ratio
6. **Screen Reader Support**: Live regions for dynamic content

---

## Styling Guidelines

All components use Tailwind CSS with:

1. **Responsive classes**: `sm:`, `md:`, `lg:` breakpoints
2. **Transitions**: Smooth animations with `transition-*` classes
3. **Color themes**: Consistent color palette
4. **Spacing**: Consistent padding and margins
5. **Typography**: Clear hierarchy with font sizes

---

## Testing

Each component has comprehensive tests:

- **Unit tests**: Component rendering and props
- **Integration tests**: Component interactions
- **E2E tests**: Complete user flows
- **Accessibility tests**: ARIA and keyboard support

See `tests/unit/components/` for examples.

---

## Related Documentation

- [useOnboardingChat Hook API](./useOnboardingChat-API.md)
- [Onboarding Flow Guide](./onboarding-flow-guide.md)
- [Migration Guide](./migration-guide.md)
- [Main README](../README.md)
