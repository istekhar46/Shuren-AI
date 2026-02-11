# Design Document

## Overview

This design document specifies the implementation details for aligning the Shuren frontend API service layer with the actual backend API endpoints. The design addresses all identified mismatches and provides a complete mapping of frontend service methods to backend endpoints.

## Architecture

### Component Structure

```
frontend/src/services/
├── api.ts                    # Base axios instance with interceptors
├── authService.ts            # Authentication operations
├── onboardingService.ts      # Onboarding flow management
├── profileService.ts         # User profile operations
├── chatService.ts            # AI chat interactions
├── mealService.ts            # Meal plan and schedule operations
├── dishService.ts            # NEW: Dish search and details
├── mealTemplateService.ts    # NEW: Meal template operations
├── shoppingListService.ts    # NEW: Shopping list generation
├── workoutService.ts         # Workout plan and schedule operations
└── voiceService.ts           # Voice session management
```

### Design Principles

1. **Single Responsibility**: Each service handles one domain
2. **Type Safety**: All requests and responses are strongly typed
3. **Error Handling**: Consistent error handling across all services
4. **Separation of Concerns**: API layer separated from business logic
5. **Backward Compatibility**: Maintain existing method signatures where possible

## API Endpoint Mapping

### 1. Authentication Service (`authService.ts`)

**Status**: ✅ Already Correct - No changes needed

**Endpoints**:
- `POST /auth/register` → `register(email, password)`
- `POST /auth/login` → `login(email, password)`
- `GET /auth/me` → `getCurrentUser()` (NEW method to add)

**Type Definitions**:
```typescript
interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  oauth_provider: string | null;
  is_active: boolean;
  created_at: string;
}
```

### 2. Onboarding Service (`onboardingService.ts`)

**Changes Required**: Update endpoint from `/progress` to `/state`

**Endpoints**:
- `GET /onboarding/state` → `getOnboardingState()`
- `POST /onboarding/step` → `saveStep(step, data)`
- `POST /onboarding/complete` → `completeOnboarding()` (NEW)

**Type Definitions**:
```typescript
interface OnboardingStateResponse {
  id: string;
  user_id: string;
  current_step: number;
  is_complete: boolean;
  step_data: Record<string, any>;
}

interface OnboardingStepRequest {
  step: number;
  data: Record<string, any>;
}
```


### 3. Profile Service (`profileService.ts`)

**Changes Required**: 
- Change PUT to PATCH
- Remove `unlockProfile()` method
- Add `lockProfile()` method
- Update request structure for updates

**Endpoints**:
- `GET /profiles/me` → `getProfile()`
- `PATCH /profiles/me` → `updateProfile(updates, reason)`
- `POST /profiles/me/lock` → `lockProfile()` (NEW)

**Type Definitions**:
```typescript
interface ProfileUpdateRequest {
  reason: string;
  updates: Record<string, any>;
}

interface UserProfileResponse {
  id: string;
  user_id: string;
  is_locked: boolean;
  fitness_level: string;
  fitness_goals: FitnessGoal[];
  physical_constraints: PhysicalConstraint[];
  dietary_preferences: DietaryPreferences | null;
  meal_plan: MealPlan | null;
  meal_schedules: MealSchedule[];
  workout_schedules: WorkoutSchedule[];
  hydration_preferences: HydrationPreferences | null;
  lifestyle_baseline: LifestyleBaseline | null;
}
```

### 4. Chat Service (`chatService.ts`)

**Changes Required**:
- Remove `conversation_id` from request
- Extract `conversation_id` from response
- Change history endpoint to use `limit` param
- Fix streaming to use POST body
- Add `clearHistory()` method

**Endpoints**:
- `POST /chat/chat` → `sendMessage(message, agentType)`
- `POST /chat/stream` → `streamMessage(message, agentType, callbacks)`
- `GET /chat/history?limit=N` → `getHistory(limit)`
- `DELETE /chat/history` → `clearHistory()` (NEW)

**Type Definitions**:
```typescript
interface ChatRequest {
  message: string;
  agent_type?: string;
}

interface ChatResponse {
  response: string;
  agent_type: string;
  conversation_id: string;
  tools_used: string[];
}

interface ChatHistoryResponse {
  messages: MessageDict[];
  total: number;
}

interface MessageDict {
  role: string;
  content: string;
  agent_type: string | null;
  created_at: string;
}
```


### 5. Meal Service (`mealService.ts`)

**Changes Required**:
- Remove date filtering from `getMealPlan()`
- Remove `getMealDetails(mealId)` method
- Move dish search to separate service
- Move shopping list to separate service
- Add meal schedule methods

**Endpoints**:
- `GET /meals/plan` → `getMealPlan()`
- `PATCH /meals/plan` → `updateMealPlan(updates)` (NEW)
- `GET /meals/schedule` → `getMealSchedule()` (NEW)
- `PATCH /meals/schedule` → `updateMealSchedule(updates)` (NEW)
- `GET /meals/today` → `getTodayMeals()` (NEW)
- `GET /meals/next` → `getNextMeal()` (NEW)

**Type Definitions**:
```typescript
interface MealPlanResponse {
  id: string;
  meals_per_day: number;
  daily_calories_target: number;
  daily_calories_min: number;
  daily_calories_max: number;
  protein_grams_target: number;
  carbs_grams_target: number;
  fats_grams_target: number;
  protein_percentage: number;
  carbs_percentage: number;
  fats_percentage: number;
  plan_rationale: string;
  is_locked: boolean;
  created_at: string;
  updated_at: string;
}

interface MealScheduleResponse {
  meals: MealScheduleItemResponse[];
}

interface MealScheduleItemResponse {
  id: string;
  meal_number: number;
  meal_name: string;
  scheduled_time: string;
  notification_offset_minutes: number;
  earliest_time: string;
  latest_time: string;
  is_active: boolean;
}
```

### 6. Dish Service (`dishService.ts`) - NEW SERVICE

**Purpose**: Handle dish search and details (moved from mealService)

**Endpoints**:
- `GET /dishes/` → `listDishes(filters)`
- `GET /dishes/search` → `searchDishes(filters)`
- `GET /dishes/{dish_id}` → `getDishDetails(dishId)`

**Type Definitions**:
```typescript
interface DishSearchFilters {
  meal_type?: string;
  diet_type?: string;
  max_prep_time?: number;
  max_calories?: number;
  limit?: number;
  offset?: number;
}

interface DishSummaryResponse {
  id: string;
  name: string;
  name_hindi: string;
  meal_type: string;
  cuisine_type: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fats_g: number;
  prep_time_minutes: number;
  cook_time_minutes: number;
  total_time_minutes: number;
  difficulty_level: string;
  is_vegetarian: boolean;
  is_vegan: boolean;
}

interface DishResponse extends DishSummaryResponse {
  description: string;
  dish_category: string;
  serving_size_g: number;
  fiber_g: number;
  is_gluten_free: boolean;
  is_dairy_free: boolean;
  is_nut_free: boolean;
  contains_allergens: string[];
  is_active: boolean;
  popularity_score: number;
  ingredients: DishIngredient[];
}
```


### 7. Meal Template Service (`mealTemplateService.ts`) - NEW SERVICE

**Purpose**: Handle meal templates with assigned dishes

**Endpoints**:
- `GET /meal-templates/today` → `getTodayMealsWithDishes()`
- `GET /meal-templates/next` → `getNextMealWithDishes()`
- `GET /meal-templates/template` → `getMealTemplate(weekNumber?)`
- `POST /meal-templates/template/regenerate` → `regenerateMealTemplate(preferences?, weekNumber?)`

**Type Definitions**:
```typescript
interface TodayMealsResponse {
  date: string;
  day_of_week: number;
  day_name: string;
  meals: MealSlot[];
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fats_g: number;
}

interface MealSlot {
  meal_name: string;
  scheduled_time: string;
  day_of_week: number;
  primary_dish: DishSummaryResponse;
  alternative_dishes: DishSummaryResponse[];
}

interface NextMealResponse {
  meal_name: string;
  scheduled_time: string;
  time_until_meal_minutes: number;
  primary_dish: DishSummaryResponse;
  alternative_dishes: DishSummaryResponse[];
}

interface MealTemplateResponse {
  id: string;
  week_number: number;
  is_active: boolean;
  days: DayMeals[];
  created_at: string;
  updated_at: string;
}

interface TemplateRegenerateRequest {
  preferences?: string;
  week_number?: number;
}
```

### 8. Shopping List Service (`shoppingListService.ts`) - NEW SERVICE

**Purpose**: Generate shopping lists from meal templates

**Endpoints**:
- `GET /shopping-list/?weeks=N` → `getShoppingList(weeks)`

**Type Definitions**:
```typescript
interface ShoppingListResponse {
  week_number: number;
  start_date: string;
  end_date: string;
  categories: IngredientCategory[];
  total_items: number;
}

interface IngredientCategory {
  category: string;
  ingredients: ShoppingListIngredient[];
}

interface ShoppingListIngredient {
  ingredient_id: string;
  name: string;
  name_hindi: string;
  category: string;
  total_quantity: number;
  unit: string;
  is_optional: boolean;
  used_in_dishes: string[];
}
```


### 9. Workout Service (`workoutService.ts`)

**Changes Required**:
- Remove `logSet()`, `completeWorkout()`, `getHistory()` methods
- Add missing methods for workout plan and day retrieval
- Keep existing schedule methods

**Endpoints**:
- `GET /workouts/plan` → `getWorkoutPlan()` (NEW)
- `GET /workouts/plan/day/{day_number}` → `getWorkoutDay(dayNumber)` (NEW)
- `GET /workouts/today` → `getTodayWorkout()`
- `GET /workouts/week` → `getWeekWorkouts()` (NEW)
- `GET /workouts/schedule` → `getWorkoutSchedule()`
- `PATCH /workouts/schedule` → `updateWorkoutSchedule(updates)` (NEW)
- `PATCH /workouts/plan` → `updateWorkoutPlan(updates)` (NEW)

**Type Definitions**:
```typescript
interface WorkoutPlanResponse {
  id: string;
  plan_name: string;
  plan_description: string;
  duration_weeks: number;
  days_per_week: number;
  plan_rationale: string;
  is_locked: boolean;
  workout_days: WorkoutDayResponse[];
  created_at: string;
  updated_at: string;
}

interface WorkoutDayResponse {
  id: string;
  day_number: number;
  day_name: string;
  muscle_groups: string[];
  workout_type: string;
  description: string;
  estimated_duration_minutes: number;
  exercises: WorkoutExercise[];
}

interface WorkoutExercise {
  id: string;
  exercise_order: number;
  sets: number;
  reps_target: number;
  weight_kg: number;
  rest_seconds: number;
  exercise: ExerciseLibrary;
}

interface ExerciseLibrary {
  id: string;
  exercise_name: string;
  exercise_type: string;
  primary_muscle_group: string;
  gif_url: string;
}

interface WorkoutScheduleResponse {
  id: string;
  day_of_week: number;
  scheduled_time: string;
  enable_notifications: boolean;
}
```

### 10. Voice Service (`voiceService.ts`)

**Status**: ✅ Already Correct - Minor additions needed

**Endpoints**:
- `POST /voice-sessions/start` → `startSession(agentType)`
- `GET /voice-sessions/{room_name}/status` → `getSessionStatus(roomName)`
- `DELETE /voice-sessions/{room_name}` → `endSession(roomName)`
- `GET /voice-sessions/active` → `getActiveSessions()` (NEW)

**Type Definitions**:
```typescript
interface VoiceSessionRequest {
  agent_type: string;
}

interface VoiceSessionResponse {
  room_name: string;
  token: string;
  livekit_url: string;
  agent_type: string;
  expires_at: string;
}

interface VoiceSessionStatus {
  room_name: string;
  active: boolean;
  participants: number;
  agent_connected: boolean;
  created_at: string | null;
}

interface ActiveSessionsResponse {
  sessions: SessionSummary[];
}

interface SessionSummary {
  room_name: string;
  agent_type: string;
  participants: number;
  created_at: string | null;
}
```


## Implementation Details

### Error Handling Strategy

All services will use a consistent error handling pattern:

```typescript
try {
  const response = await api.get('/endpoint');
  return response.data;
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      // Backend returned error response
      const status = error.response.status;
      const message = error.response.data?.detail || 'An error occurred';
      
      if (status === 401) {
        // Handled by axios interceptor
        throw new Error('Unauthorized');
      } else if (status >= 400 && status < 500) {
        // Client error
        throw new Error(message);
      } else if (status >= 500) {
        // Server error
        throw new Error('Server error. Please try again later.');
      }
    } else if (error.request) {
      // Network error
      throw new Error('Network error. Please check your connection.');
    }
  }
  throw error;
}
```

### Type Definition Organization

Create a new `types/api.ts` file to centralize all API-related type definitions:

```typescript
// types/api.ts
export * from './auth.types';
export * from './onboarding.types';
export * from './profile.types';
export * from './chat.types';
export * from './meal.types';
export * from './dish.types';
export * from './mealTemplate.types';
export * from './shoppingList.types';
export * from './workout.types';
export * from './voice.types';
```

### Axios Instance Configuration

The base `api.ts` configuration remains unchanged:

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```


## Service Implementation Examples

### Example 1: Updated Onboarding Service

```typescript
// services/onboardingService.ts
import api from './api';
import type { 
  OnboardingStateResponse, 
  OnboardingStepRequest,
  OnboardingStepResponse,
  UserProfileResponse 
} from '../types/api';

export const onboardingService = {
  /**
   * Get current onboarding state
   * @returns Current onboarding progress
   */
  async getOnboardingState(): Promise<OnboardingStateResponse> {
    const response = await api.get<OnboardingStateResponse>('/onboarding/state');
    return response.data;
  },

  /**
   * Save onboarding step data
   * @param step - Step number
   * @param data - Step data
   * @returns Updated onboarding state
   */
  async saveStep(step: number, data: Record<string, any>): Promise<OnboardingStepResponse> {
    const payload: OnboardingStepRequest = { step, data };
    const response = await api.post<OnboardingStepResponse>('/onboarding/step', payload);
    return response.data;
  },

  /**
   * Complete onboarding and create user profile
   * @returns Created user profile
   */
  async completeOnboarding(): Promise<UserProfileResponse> {
    const response = await api.post<UserProfileResponse>('/onboarding/complete');
    return response.data;
  },

  /**
   * Legacy method for backward compatibility
   * Maps to getOnboardingState()
   */
  async getProgress(): Promise<{ currentStep: number; completed: boolean }> {
    const state = await this.getOnboardingState();
    return {
      currentStep: state.current_step,
      completed: state.is_complete,
    };
  },
};
```

### Example 2: Updated Profile Service

```typescript
// services/profileService.ts
import api from './api';
import type { 
  UserProfileResponse, 
  ProfileUpdateRequest 
} from '../types/api';

export const profileService = {
  /**
   * Get current user's profile
   * @returns User profile with all relationships
   */
  async getProfile(): Promise<UserProfileResponse> {
    const response = await api.get<UserProfileResponse>('/profiles/me');
    return response.data;
  },

  /**
   * Update user's profile
   * @param updates - Fields to update
   * @param reason - Reason for update (required for locked profiles)
   * @returns Updated user profile
   */
  async updateProfile(
    updates: Record<string, any>, 
    reason: string = 'User requested update'
  ): Promise<UserProfileResponse> {
    const payload: ProfileUpdateRequest = { updates, reason };
    const response = await api.patch<UserProfileResponse>('/profiles/me', payload);
    return response.data;
  },

  /**
   * Lock user's profile to prevent modifications
   * @returns Updated user profile with is_locked=true
   */
  async lockProfile(): Promise<UserProfileResponse> {
    const response = await api.post<UserProfileResponse>('/profiles/me/lock');
    return response.data;
  },
};
```


### Example 3: Updated Chat Service

```typescript
// services/chatService.ts
import api from './api';
import type { 
  ChatRequest, 
  ChatResponse, 
  ChatHistoryResponse 
} from '../types/api';

export const chatService = {
  /**
   * Send a message to an AI agent
   * @param message - User's message text
   * @param agentType - Type of agent to route to (optional)
   * @returns Agent's response with conversation metadata
   */
  async sendMessage(
    message: string,
    agentType?: string
  ): Promise<ChatResponse> {
    const payload: ChatRequest = {
      message,
      agent_type: agentType,
    };
    const response = await api.post<ChatResponse>('/chat/chat', payload);
    return response.data;
  },

  /**
   * Get chat history
   * @param limit - Maximum number of messages to return
   * @returns Chat history with messages and total count
   */
  async getHistory(limit: number = 50): Promise<ChatHistoryResponse> {
    const response = await api.get<ChatHistoryResponse>('/chat/history', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Clear all chat history
   * @returns Success status
   */
  async clearHistory(): Promise<{ status: string }> {
    const response = await api.delete<{ status: string }>('/chat/history');
    return response.data;
  },

  /**
   * Stream a message to an agent using Server-Sent Events
   * @param message - User's message text
   * @param agentType - Type of agent to route to (optional)
   * @param onChunk - Callback for each chunk
   * @param onComplete - Callback when complete
   * @param onError - Callback for errors
   * @returns EventSource instance
   */
  streamMessage(
    message: string,
    agentType: string | undefined,
    onChunk: (chunk: string) => void,
    onComplete: (agentType: string) => void,
    onError: (error: Error) => void
  ): EventSource {
    const baseURL = api.defaults.baseURL || 'http://localhost:8000/api/v1';
    
    // Create URL with query params for SSE
    const url = new URL('/chat/stream', baseURL);
    
    // Add authentication token as query param (SSE limitation)
    const token = localStorage.getItem('auth_token');
    if (token) {
      url.searchParams.append('token', token);
    }
    
    // Add message and agent_type as query params
    url.searchParams.append('message', message);
    if (agentType) {
      url.searchParams.append('agent_type', agentType);
    }

    const eventSource = new EventSource(url.toString());

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.error) {
          onError(new Error(data.error));
          eventSource.close();
        } else if (data.done) {
          onComplete(data.agent_type);
          eventSource.close();
        } else if (data.chunk) {
          onChunk(data.chunk);
        }
      } catch (error) {
        onError(new Error('Failed to parse stream data'));
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      onError(new Error('Stream connection failed'));
      eventSource.close();
    };

    return eventSource;
  },
};
```


### Example 4: New Dish Service

```typescript
// services/dishService.ts
import api from './api';
import type { 
  DishSummaryResponse, 
  DishResponse,
  DishSearchFilters 
} from '../types/api';

export const dishService = {
  /**
   * List dishes with optional filters
   * @param filters - Search filters
   * @returns Array of dish summaries
   */
  async listDishes(filters?: DishSearchFilters): Promise<DishSummaryResponse[]> {
    const response = await api.get<DishSummaryResponse[]>('/dishes/', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Search dishes with advanced filters
   * @param filters - Search filters including prep time and calories
   * @returns Array of dish summaries
   */
  async searchDishes(filters: DishSearchFilters): Promise<DishSummaryResponse[]> {
    const response = await api.get<DishSummaryResponse[]>('/dishes/search', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get detailed dish information with ingredients
   * @param dishId - Dish UUID
   * @returns Complete dish details
   */
  async getDishDetails(dishId: string): Promise<DishResponse> {
    const response = await api.get<DishResponse>(`/dishes/${dishId}`);
    return response.data;
  },
};
```

### Example 5: New Meal Template Service

```typescript
// services/mealTemplateService.ts
import api from './api';
import type { 
  TodayMealsResponse, 
  NextMealResponse,
  MealTemplateResponse,
  TemplateRegenerateRequest 
} from '../types/api';

export const mealTemplateService = {
  /**
   * Get today's meals with assigned dishes
   * @returns Today's meal plan with dishes
   */
  async getTodayMealsWithDishes(): Promise<TodayMealsResponse> {
    const response = await api.get<TodayMealsResponse>('/meal-templates/today');
    return response.data;
  },

  /**
   * Get next upcoming meal with dishes
   * @returns Next meal details
   */
  async getNextMealWithDishes(): Promise<NextMealResponse> {
    const response = await api.get<NextMealResponse>('/meal-templates/next');
    return response.data;
  },

  /**
   * Get meal template for a specific week
   * @param weekNumber - Week number (1-4), optional
   * @returns Complete meal template
   */
  async getMealTemplate(weekNumber?: number): Promise<MealTemplateResponse> {
    const response = await api.get<MealTemplateResponse>('/meal-templates/template', {
      params: weekNumber ? { week_number: weekNumber } : {},
    });
    return response.data;
  },

  /**
   * Regenerate meal template with new dishes
   * @param preferences - Optional preferences for dish selection
   * @param weekNumber - Optional week number to regenerate
   * @returns Newly generated meal template
   */
  async regenerateMealTemplate(
    preferences?: string,
    weekNumber?: number
  ): Promise<MealTemplateResponse> {
    const payload: TemplateRegenerateRequest = {};
    if (preferences) payload.preferences = preferences;
    if (weekNumber) payload.week_number = weekNumber;
    
    const response = await api.post<MealTemplateResponse>(
      '/meal-templates/template/regenerate',
      payload
    );
    return response.data;
  },
};
```


## Migration Strategy

### Phase 1: Type Definitions (Week 1)

1. Create new type definition files in `types/` directory
2. Define all request and response interfaces
3. Export types from centralized `types/api.ts`
4. Update existing type imports across the codebase

### Phase 2: Core Services Update (Week 1-2)

1. Update `authService.ts` - Add `getCurrentUser()` method
2. Update `onboardingService.ts` - Change endpoint from `/progress` to `/state`
3. Update `profileService.ts` - Change PUT to PATCH, remove unlock, add lock
4. Update `chatService.ts` - Fix request/response structure, add clearHistory

### Phase 3: New Services Creation (Week 2)

1. Create `dishService.ts` - Move dish operations from mealService
2. Create `mealTemplateService.ts` - Add meal template operations
3. Create `shoppingListService.ts` - Add shopping list generation

### Phase 4: Meal & Workout Services (Week 2-3)

1. Update `mealService.ts` - Remove date filtering, add schedule methods
2. Update `workoutService.ts` - Remove logging methods, add plan methods
3. Update `voiceService.ts` - Add getActiveSessions method

### Phase 5: Testing & Validation (Week 3)

1. Write unit tests for all service methods
2. Write integration tests for API calls
3. Test error handling scenarios
4. Validate type safety with TypeScript compiler

### Phase 6: Documentation & Cleanup (Week 3)

1. Update API documentation
2. Remove deprecated methods
3. Add JSDoc comments to all methods
4. Create migration guide for developers

## Backward Compatibility

To maintain backward compatibility during migration:

### Deprecated Method Wrappers

```typescript
// Example: onboardingService.ts
export const onboardingService = {
  // New method
  async getOnboardingState(): Promise<OnboardingStateResponse> {
    const response = await api.get<OnboardingStateResponse>('/onboarding/state');
    return response.data;
  },

  // Deprecated method - wrapper for backward compatibility
  /** @deprecated Use getOnboardingState() instead */
  async getProgress(): Promise<{ currentStep: number; completed: boolean }> {
    console.warn('getProgress() is deprecated. Use getOnboardingState() instead.');
    const state = await this.getOnboardingState();
    return {
      currentStep: state.current_step,
      completed: state.is_complete,
    };
  },
};
```

### Method Signature Adapters

```typescript
// Example: mealService.ts
export const mealService = {
  // New method
  async getMealPlan(): Promise<MealPlanResponse> {
    const response = await api.get<MealPlanResponse>('/meals/plan');
    return response.data;
  },

  // Deprecated method - ignores date parameters
  /** @deprecated Date filtering not supported. Use getMealPlan() instead */
  async getMealPlanWithDates(startDate?: string, endDate?: string): Promise<MealPlanResponse> {
    if (startDate || endDate) {
      console.warn('Date filtering is not supported by the backend. Returning full meal plan.');
    }
    return this.getMealPlan();
  },
};
```


## Testing Strategy

### Unit Tests

Each service method should have unit tests covering:

1. **Successful API calls** - Verify correct endpoint, method, and parameters
2. **Response mapping** - Verify response data is correctly typed and returned
3. **Error handling** - Verify errors are caught and re-thrown appropriately
4. **Edge cases** - Verify handling of null/undefined parameters

Example unit test:

```typescript
// tests/unit/services/onboardingService.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { onboardingService } from '@/services/onboardingService';
import api from '@/services/api';

vi.mock('@/services/api');

describe('onboardingService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getOnboardingState', () => {
    it('should call GET /onboarding/state', async () => {
      const mockResponse = {
        data: {
          id: '123',
          user_id: '456',
          current_step: 5,
          is_complete: false,
          step_data: {},
        },
      };
      
      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await onboardingService.getOnboardingState();

      expect(api.get).toHaveBeenCalledWith('/onboarding/state');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle errors', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('Network error'));

      await expect(onboardingService.getOnboardingState()).rejects.toThrow('Network error');
    });
  });

  describe('saveStep', () => {
    it('should call POST /onboarding/step with correct payload', async () => {
      const mockResponse = {
        data: {
          current_step: 6,
          is_complete: false,
          message: 'Step 5 saved successfully',
        },
      };
      
      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await onboardingService.saveStep(5, { fitness_level: 'intermediate' });

      expect(api.post).toHaveBeenCalledWith('/onboarding/step', {
        step: 5,
        data: { fitness_level: 'intermediate' },
      });
      expect(result).toEqual(mockResponse.data);
    });
  });
});
```

### Integration Tests

Integration tests should verify end-to-end API communication:

```typescript
// tests/integration/api/onboarding.test.ts
import { describe, it, expect } from 'vitest';
import { onboardingService } from '@/services/onboardingService';

describe('Onboarding API Integration', () => {
  it('should complete full onboarding flow', async () => {
    // Get initial state
    const initialState = await onboardingService.getOnboardingState();
    expect(initialState.current_step).toBeDefined();

    // Save a step
    const stepResult = await onboardingService.saveStep(1, {
      fitness_level: 'beginner',
    });
    expect(stepResult.current_step).toBeGreaterThan(initialState.current_step);

    // Complete onboarding
    const profile = await onboardingService.completeOnboarding();
    expect(profile.id).toBeDefined();
    expect(profile.is_locked).toBe(true);
  });
});
```


## Property-Based Testing

### Correctness Properties

#### Property 1: API Endpoint Consistency

**Validates: Requirements 1-8**

**Property**: For any service method call, the HTTP request MUST use the correct endpoint path, method, and parameters as defined in the backend API specification.

**Test Strategy**:
```typescript
import { describe, it } from 'vitest';
import fc from 'fast-check';

describe('Property: API Endpoint Consistency', () => {
  it('should always call correct endpoints for onboarding operations', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 11 }), // step number
        fc.record({ // step data
          fitness_level: fc.constantFrom('beginner', 'intermediate', 'advanced'),
        }),
        async (step, data) => {
          const spy = vi.spyOn(api, 'post');
          
          await onboardingService.saveStep(step, data);
          
          // Verify correct endpoint
          expect(spy).toHaveBeenCalledWith(
            '/onboarding/step',
            expect.objectContaining({ step, data })
          );
        }
      )
    );
  });
});
```

#### Property 2: Type Safety Preservation

**Validates: Requirement 9**

**Property**: For any API response, the returned data MUST conform to the TypeScript interface defined for that endpoint.

**Test Strategy**:
```typescript
describe('Property: Type Safety Preservation', () => {
  it('should return correctly typed responses for all meal operations', () => {
    fc.assert(
      fc.asyncProperty(
        fc.constantFrom('getMealPlan', 'getMealSchedule', 'getTodayMeals'),
        async (methodName) => {
          const result = await mealService[methodName]();
          
          // Verify result matches expected type structure
          expect(result).toBeDefined();
          expect(typeof result).toBe('object');
          
          // Type-specific validations
          if (methodName === 'getMealPlan') {
            expect(result).toHaveProperty('daily_calories_target');
            expect(typeof result.daily_calories_target).toBe('number');
          }
        }
      )
    );
  });
});
```

#### Property 3: Error Handling Consistency

**Validates: Requirement 10**

**Property**: For any API error response, the service MUST throw an error with appropriate message and preserve error details.

**Test Strategy**:
```typescript
describe('Property: Error Handling Consistency', () => {
  it('should consistently handle errors across all services', () => {
    fc.assert(
      fc.asyncProperty(
        fc.constantFrom(401, 403, 404, 500, 503), // HTTP status codes
        fc.string(), // error message
        async (statusCode, errorMessage) => {
          vi.mocked(api.get).mockRejectedValue({
            response: {
              status: statusCode,
              data: { detail: errorMessage },
            },
          });
          
          await expect(profileService.getProfile()).rejects.toThrow();
        }
      )
    );
  });
});
```

#### Property 4: Request Parameter Validation

**Validates: Requirements 1-8**

**Property**: For any service method with parameters, the parameters MUST be correctly passed to the API request in the expected format.

**Test Strategy**:
```typescript
describe('Property: Request Parameter Validation', () => {
  it('should correctly pass query parameters for dish search', () => {
    fc.assert(
      fc.asyncProperty(
        fc.record({
          meal_type: fc.constantFrom('breakfast', 'lunch', 'dinner'),
          limit: fc.integer({ min: 1, max: 100 }),
          offset: fc.integer({ min: 0, max: 1000 }),
        }),
        async (filters) => {
          const spy = vi.spyOn(api, 'get');
          
          await dishService.searchDishes(filters);
          
          expect(spy).toHaveBeenCalledWith(
            '/dishes/search',
            expect.objectContaining({
              params: expect.objectContaining(filters),
            })
          );
        }
      )
    );
  });
});
```


#### Property 5: Response Data Completeness

**Validates: Requirements 1-8**

**Property**: For any successful API response, all required fields defined in the response schema MUST be present and non-null.

**Test Strategy**:
```typescript
describe('Property: Response Data Completeness', () => {
  it('should return complete workout plan data', () => {
    fc.assert(
      fc.asyncProperty(
        fc.record({
          id: fc.uuid(),
          plan_name: fc.string(),
          duration_weeks: fc.integer({ min: 1, max: 52 }),
          days_per_week: fc.integer({ min: 1, max: 7 }),
          is_locked: fc.boolean(),
        }),
        async (mockPlan) => {
          vi.mocked(api.get).mockResolvedValue({ data: mockPlan });
          
          const result = await workoutService.getWorkoutPlan();
          
          // Verify all required fields are present
          expect(result.id).toBeDefined();
          expect(result.plan_name).toBeDefined();
          expect(result.duration_weeks).toBeGreaterThan(0);
          expect(result.days_per_week).toBeGreaterThan(0);
          expect(typeof result.is_locked).toBe('boolean');
        }
      )
    );
  });
});
```

## Performance Considerations

### Request Optimization

1. **Caching Strategy**: Implement response caching for frequently accessed data
2. **Request Debouncing**: Debounce search requests to reduce API calls
3. **Batch Requests**: Where possible, combine multiple requests into single calls
4. **Lazy Loading**: Load data only when needed

Example caching implementation:

```typescript
// utils/cache.ts
class APICache {
  private cache = new Map<string, { data: any; timestamp: number }>();
  private ttl = 5 * 60 * 1000; // 5 minutes

  get(key: string): any | null {
    const cached = this.cache.get(key);
    if (!cached) return null;
    
    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }

  set(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  clear(): void {
    this.cache.clear();
  }
}

export const apiCache = new APICache();
```

### Error Recovery

Implement retry logic for transient failures:

```typescript
// utils/retry.ts
export async function retryRequest<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on client errors (4xx)
      if (axios.isAxiosError(error) && error.response?.status < 500) {
        throw error;
      }
      
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
      }
    }
  }
  
  throw lastError!;
}
```


## Security Considerations

### Authentication Token Management

1. **Token Storage**: Store JWT tokens in localStorage (current implementation)
2. **Token Refresh**: Implement token refresh logic before expiration
3. **Secure Transmission**: Always use HTTPS in production
4. **Token Cleanup**: Clear tokens on logout and 401 errors

### API Security Best Practices

```typescript
// services/api.ts - Enhanced security
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // Set to true if using cookies
});

// Request interceptor: Add JWT token and security headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add security headers
    config.headers['X-Requested-With'] = 'XMLHttpRequest';
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle authentication errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear authentication state
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

## Documentation Requirements

### JSDoc Comments

All service methods must include comprehensive JSDoc comments:

```typescript
/**
 * Get current user's workout plan with all exercises
 * 
 * @returns {Promise<WorkoutPlanResponse>} Complete workout plan including:
 *   - Plan metadata (name, duration, rationale)
 *   - All workout days with exercises
 *   - Exercise library details with GIF URLs
 * 
 * @throws {Error} If workout plan not found (404)
 * @throws {Error} If user not authenticated (401)
 * @throws {Error} If server error occurs (500)
 * 
 * @example
 * ```typescript
 * const plan = await workoutService.getWorkoutPlan();
 * console.log(plan.plan_name); // "Beginner Full Body"
 * console.log(plan.workout_days.length); // 4
 * ```
 */
async getWorkoutPlan(): Promise<WorkoutPlanResponse> {
  const response = await api.get<WorkoutPlanResponse>('/workouts/plan');
  return response.data;
}
```

### API Documentation

Create a comprehensive API documentation file:

```markdown
# Frontend API Services Documentation

## Overview

This document describes all frontend API service methods and their usage.

## Authentication Service

### `register(email: string, password: string): Promise<TokenResponse>`

Registers a new user account.

**Parameters:**
- `email` - User's email address
- `password` - User's password (min 8 characters)

**Returns:** TokenResponse with access_token and user_id

**Example:**
```typescript
const response = await authService.register('user@example.com', 'password123');
localStorage.setItem('auth_token', response.access_token);
```

[Continue for all services...]
```


## Validation and Constraints

### Input Validation

All service methods should validate inputs before making API calls:

```typescript
// utils/validation.ts
export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

export function validateEmail(email: string): void {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new ValidationError('Invalid email format');
  }
}

export function validateStep(step: number): void {
  if (step < 0 || step > 11) {
    throw new ValidationError('Step must be between 0 and 11');
  }
}

export function validateWeeks(weeks: number): void {
  if (weeks < 1 || weeks > 4) {
    throw new ValidationError('Weeks must be between 1 and 4');
  }
}
```

### Response Validation

Validate API responses match expected schema:

```typescript
// utils/responseValidation.ts
import { z } from 'zod';

// Define Zod schemas for validation
const TokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
  user_id: z.string().uuid(),
});

const MealPlanResponseSchema = z.object({
  id: z.string().uuid(),
  meals_per_day: z.number().int().positive(),
  daily_calories_target: z.number().positive(),
  protein_grams_target: z.number().positive(),
  carbs_grams_target: z.number().positive(),
  fats_grams_target: z.number().positive(),
  is_locked: z.boolean(),
});

export function validateTokenResponse(data: unknown): TokenResponse {
  return TokenResponseSchema.parse(data);
}

export function validateMealPlanResponse(data: unknown): MealPlanResponse {
  return MealPlanResponseSchema.parse(data);
}
```

## Monitoring and Logging

### Request Logging

Implement request/response logging for debugging:

```typescript
// utils/logger.ts
export class APILogger {
  private static isDevelopment = import.meta.env.DEV;

  static logRequest(method: string, url: string, data?: any): void {
    if (this.isDevelopment) {
      console.group(`🔵 API Request: ${method} ${url}`);
      if (data) console.log('Data:', data);
      console.groupEnd();
    }
  }

  static logResponse(method: string, url: string, status: number, data?: any): void {
    if (this.isDevelopment) {
      console.group(`🟢 API Response: ${method} ${url} (${status})`);
      if (data) console.log('Data:', data);
      console.groupEnd();
    }
  }

  static logError(method: string, url: string, error: any): void {
    console.group(`🔴 API Error: ${method} ${url}`);
    console.error('Error:', error);
    console.groupEnd();
  }
}

// Add to axios interceptors
api.interceptors.request.use(
  (config) => {
    APILogger.logRequest(config.method?.toUpperCase() || 'GET', config.url || '');
    return config;
  }
);

api.interceptors.response.use(
  (response) => {
    APILogger.logResponse(
      response.config.method?.toUpperCase() || 'GET',
      response.config.url || '',
      response.status,
      response.data
    );
    return response;
  },
  (error) => {
    APILogger.logError(
      error.config?.method?.toUpperCase() || 'GET',
      error.config?.url || '',
      error
    );
    return Promise.reject(error);
  }
);
```


## Summary of Changes

### Files to Create

1. **`frontend/src/services/dishService.ts`** - New service for dish operations
2. **`frontend/src/services/mealTemplateService.ts`** - New service for meal templates
3. **`frontend/src/services/shoppingListService.ts`** - New service for shopping lists
4. **`frontend/src/types/api.ts`** - Centralized type exports
5. **`frontend/src/types/auth.types.ts`** - Authentication types
6. **`frontend/src/types/onboarding.types.ts`** - Onboarding types
7. **`frontend/src/types/profile.types.ts`** - Profile types
8. **`frontend/src/types/chat.types.ts`** - Chat types
9. **`frontend/src/types/meal.types.ts`** - Meal types
10. **`frontend/src/types/dish.types.ts`** - Dish types
11. **`frontend/src/types/mealTemplate.types.ts`** - Meal template types
12. **`frontend/src/types/shoppingList.types.ts`** - Shopping list types
13. **`frontend/src/types/workout.types.ts`** - Workout types
14. **`frontend/src/types/voice.types.ts`** - Voice session types
15. **`frontend/src/utils/validation.ts`** - Input validation utilities
16. **`frontend/src/utils/responseValidation.ts`** - Response validation utilities
17. **`frontend/src/utils/cache.ts`** - API caching utilities
18. **`frontend/src/utils/retry.ts`** - Request retry utilities
19. **`frontend/src/utils/logger.ts`** - API logging utilities

### Files to Modify

1. **`frontend/src/services/authService.ts`**
   - Add `getCurrentUser()` method
   - Add proper type imports

2. **`frontend/src/services/onboardingService.ts`**
   - Change endpoint from `/progress` to `/state`
   - Rename `getProgress()` to `getOnboardingState()`
   - Add `completeOnboarding()` method
   - Add backward compatibility wrapper

3. **`frontend/src/services/profileService.ts`**
   - Change `updateProfile()` from PUT to PATCH
   - Update request structure to include `reason` field
   - Remove `unlockProfile()` method
   - Add `lockProfile()` method

4. **`frontend/src/services/chatService.ts`**
   - Remove `conversation_id` from request body
   - Update `getHistory()` to use `limit` parameter
   - Fix `streamMessage()` to use query parameters for SSE
   - Add `clearHistory()` method

5. **`frontend/src/services/mealService.ts`**
   - Remove date filtering from `getMealPlan()`
   - Remove `getMealDetails()` method
   - Remove `searchDishes()` method (moved to dishService)
   - Remove `generateShoppingList()` method (moved to shoppingListService)
   - Add `updateMealPlan()` method
   - Add `getMealSchedule()` method
   - Add `updateMealSchedule()` method
   - Add `getTodayMeals()` method
   - Add `getNextMeal()` method

6. **`frontend/src/services/workoutService.ts`**
   - Add `getWorkoutPlan()` method
   - Add `getWorkoutDay()` method
   - Add `getWeekWorkouts()` method
   - Add `updateWorkoutPlan()` method
   - Add `updateWorkoutSchedule()` method
   - Remove `logSet()` method
   - Remove `completeWorkout()` method
   - Remove `getHistory()` method

7. **`frontend/src/services/voiceService.ts`**
   - Add `getActiveSessions()` method
   - Add proper type imports

8. **`frontend/src/services/api.ts`**
   - Add enhanced security headers
   - Add logging interceptors
   - Add retry logic for failed requests

### Breaking Changes

The following methods are being removed or changed:

1. **Removed Methods:**
   - `onboardingService.getProgress()` → Use `getOnboardingState()` instead
   - `profileService.unlockProfile()` → No backend support
   - `mealService.getMealDetails(mealId)` → No backend support
   - `mealService.searchDishes()` → Moved to `dishService.searchDishes()`
   - `mealService.generateShoppingList()` → Moved to `shoppingListService.getShoppingList()`
   - `workoutService.logSet()` → No backend support
   - `workoutService.completeWorkout()` → No backend support
   - `workoutService.getHistory()` → No backend support

2. **Changed Method Signatures:**
   - `profileService.updateProfile(data)` → `updateProfile(updates, reason)`
   - `chatService.sendMessage(message, agentType, conversationId)` → `sendMessage(message, agentType)`
   - `chatService.getHistory(conversationId)` → `getHistory(limit)`
   - `mealService.getMealPlan(startDate, endDate)` → `getMealPlan()`

3. **HTTP Method Changes:**
   - `profileService.updateProfile()`: PUT → PATCH


## Risk Assessment

### High Risk Areas

1. **Breaking Changes Impact**
   - **Risk**: Existing frontend code may break when methods are removed
   - **Mitigation**: Provide backward compatibility wrappers with deprecation warnings
   - **Timeline**: 2-week deprecation period before removal

2. **Type Safety Gaps**
   - **Risk**: Runtime errors if response types don't match expectations
   - **Mitigation**: Implement runtime validation with Zod schemas
   - **Timeline**: Add validation in Phase 1

3. **Authentication Flow**
   - **Risk**: Token management issues could lock users out
   - **Mitigation**: Thorough testing of auth flows, implement token refresh
   - **Timeline**: Test in Phase 2

### Medium Risk Areas

1. **SSE Streaming Implementation**
   - **Risk**: EventSource doesn't support custom headers
   - **Mitigation**: Use query parameters for authentication
   - **Timeline**: Test in Phase 2

2. **Data Migration**
   - **Risk**: Existing cached data may be incompatible
   - **Mitigation**: Clear cache on deployment, version cache keys
   - **Timeline**: Implement in Phase 3

### Low Risk Areas

1. **New Service Creation**
   - **Risk**: Minimal - new services don't affect existing code
   - **Mitigation**: Comprehensive unit tests
   - **Timeline**: Phase 2

2. **Documentation Updates**
   - **Risk**: Minimal - documentation-only changes
   - **Mitigation**: Peer review
   - **Timeline**: Phase 6

## Deployment Strategy

### Pre-Deployment Checklist

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Property-based tests passing
- [ ] TypeScript compilation successful with no errors
- [ ] ESLint checks passing
- [ ] API documentation updated
- [ ] Migration guide created
- [ ] Backward compatibility wrappers in place
- [ ] Deprecation warnings added
- [ ] Cache invalidation strategy implemented

### Deployment Steps

1. **Stage 1: Type Definitions** (Low Risk)
   - Deploy new type definition files
   - No breaking changes
   - Can be deployed independently

2. **Stage 2: New Services** (Low Risk)
   - Deploy dishService, mealTemplateService, shoppingListService
   - No breaking changes
   - Can be deployed independently

3. **Stage 3: Service Updates** (Medium Risk)
   - Deploy updated services with backward compatibility
   - Monitor error rates
   - Rollback plan: Revert to previous version

4. **Stage 4: Deprecation Warnings** (Low Risk)
   - Enable deprecation warnings in console
   - Monitor usage of deprecated methods
   - Communicate with team

5. **Stage 5: Breaking Changes** (High Risk)
   - Remove deprecated methods after 2-week period
   - Ensure all code updated
   - Monitor error rates closely

### Rollback Plan

If critical issues are discovered:

1. **Immediate Actions:**
   - Revert to previous version via Git
   - Clear browser caches
   - Notify users of temporary issues

2. **Investigation:**
   - Review error logs
   - Identify root cause
   - Create hotfix if needed

3. **Re-deployment:**
   - Fix issues in development
   - Re-test thoroughly
   - Deploy with increased monitoring


## Success Metrics

### Technical Metrics

1. **API Call Success Rate**
   - Target: 99.5% success rate for all API calls
   - Measurement: Monitor 4xx and 5xx error rates
   - Baseline: Current error rate (to be measured)

2. **Type Safety Coverage**
   - Target: 100% of API calls use TypeScript interfaces
   - Measurement: TypeScript compiler checks
   - Baseline: Current coverage (to be measured)

3. **Test Coverage**
   - Target: 90% code coverage for service layer
   - Measurement: Vitest coverage reports
   - Baseline: Current coverage (to be measured)

4. **Response Time**
   - Target: 95th percentile < 500ms for all API calls
   - Measurement: Performance monitoring
   - Baseline: Current response times (to be measured)

### User Experience Metrics

1. **Error Rate Reduction**
   - Target: 50% reduction in API-related errors
   - Measurement: Error tracking (Sentry/similar)
   - Timeline: Within 2 weeks of deployment

2. **Feature Availability**
   - Target: 100% of documented features working
   - Measurement: Integration test results
   - Timeline: Before deployment

### Development Metrics

1. **Code Maintainability**
   - Target: All services have JSDoc comments
   - Measurement: Documentation coverage
   - Timeline: Phase 6

2. **Developer Onboarding**
   - Target: New developers can understand API layer in < 1 hour
   - Measurement: Onboarding feedback
   - Timeline: After documentation complete

## Conclusion

This design provides a comprehensive solution for aligning the Shuren frontend API service layer with the actual backend API endpoints. The implementation follows industry best practices for:

- **Type Safety**: Strong TypeScript typing throughout
- **Error Handling**: Consistent error handling across all services
- **Testing**: Comprehensive unit, integration, and property-based tests
- **Documentation**: Clear JSDoc comments and API documentation
- **Security**: Proper authentication and authorization
- **Performance**: Caching, retry logic, and request optimization
- **Maintainability**: Clean code structure and separation of concerns

The phased migration strategy ensures minimal disruption to existing functionality while providing a clear path to full alignment. Backward compatibility wrappers allow for gradual migration of existing code, and comprehensive testing ensures reliability.

### Next Steps

1. Review and approve this design document
2. Create implementation tasks from this design
3. Begin Phase 1: Type Definitions
4. Continue through phases 2-6 as outlined
5. Monitor metrics and adjust as needed

### References

- Backend API Documentation: `backend/app/api/v1/endpoints/`
- Frontend Services: `frontend/src/services/`
- Type Definitions: `frontend/src/types/`
- Product Requirements: `docs/product/RFP.md`
- User Journey: `docs/product/how_completed_product_will_look.md`

