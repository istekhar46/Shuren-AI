# Requirements Document

## Introduction

This specification addresses the critical misalignment between the Shuren frontend API service layer and the actual backend API endpoints. The frontend currently makes incorrect API calls with wrong endpoints, HTTP methods, request parameters, and response structures. This causes runtime errors, failed requests, and broken functionality across authentication, onboarding, profiles, chat, meals, and workouts.

The goal is to update all frontend API service files to correctly integrate with the actual backend endpoints, ensuring type-safe communication and proper error handling.

## Glossary

- **Frontend_Service**: TypeScript service module that encapsulates API calls to the backend
- **Backend_Endpoint**: FastAPI route handler that processes HTTP requests
- **API_Contract**: The agreed-upon interface between frontend and backend including URL, method, request body, query parameters, and response structure
- **Type_Definition**: TypeScript interface defining the shape of request/response data
- **HTTP_Method**: The HTTP verb used for the request (GET, POST, PATCH, PUT, DELETE)
- **Query_Parameter**: URL parameter passed in the query string
- **Request_Body**: JSON payload sent in the HTTP request body
- **Response_Schema**: The structure of data returned by the backend

## Requirements

### Requirement 1: Onboarding API Alignment

**User Story:** As a developer, I want the onboarding service to use the correct backend endpoints, so that users can successfully save onboarding progress and retrieve their current state.

#### Acceptance Criteria

1. WHEN the frontend calls `getProgress()`, THE Frontend_Service SHALL send a GET request to `/onboarding/state`
2. WHEN the backend returns onboarding state, THE Frontend_Service SHALL map the response fields `current_step` and `is_complete` to the expected frontend format
3. WHEN the frontend calls `saveStep()`, THE Frontend_Service SHALL send a POST request to `/onboarding/step` with `{step, data}` in the request body
4. WHEN the frontend calls `completeOnboarding()`, THE Frontend_Service SHALL send a POST request to `/onboarding/complete`
5. THE Frontend_Service SHALL define TypeScript interfaces matching the backend's `OnboardingStateResponse` schema

### Requirement 2: Profile API Alignment

**User Story:** As a developer, I want the profile service to use the correct HTTP methods and endpoints, so that profile operations succeed without errors.

#### Acceptance Criteria

1. WHEN the frontend calls `getProfile()`, THE Frontend_Service SHALL send a GET request to `/profiles/me`
2. WHEN the frontend calls `updateProfile()`, THE Frontend_Service SHALL send a PATCH request (not PUT) to `/profiles/me`
3. WHEN the frontend calls `lockProfile()`, THE Frontend_Service SHALL send a POST request to `/profiles/me/lock`
4. THE Frontend_Service SHALL remove the `unlockProfile()` method as the backend does not support profile unlocking
5. WHEN updating a profile, THE Frontend_Service SHALL send a request body with `{reason, updates}` structure matching `ProfileUpdateRequest`
6. THE Frontend_Service SHALL define TypeScript interfaces matching the backend's `UserProfileResponse` schema

### Requirement 3: Chat API Alignment

**User Story:** As a developer, I want the chat service to correctly handle conversation context and streaming, so that users can have coherent conversations with AI agents.

#### Acceptance Criteria

1. WHEN the frontend calls `sendMessage()`, THE Frontend_Service SHALL send a POST request to `/chat/chat` with `{message, agent_type}` only
2. THE Frontend_Service SHALL remove `conversation_id` from the request body as the backend does not accept it
3. WHEN the backend returns a chat response, THE Frontend_Service SHALL extract `conversation_id` from the response for tracking
4. WHEN the frontend calls `getHistory()`, THE Frontend_Service SHALL send a GET request with query parameter `limit` (not `conversation_id`)
5. WHEN the frontend calls `streamMessage()`, THE Frontend_Service SHALL send a POST request to `/chat/stream` with `{message, agent_type}` in the request body
6. THE Frontend_Service SHALL handle Server-Sent Events (SSE) responses from the streaming endpoint
7. WHEN the frontend calls `clearHistory()`, THE Frontend_Service SHALL send a DELETE request to `/chat/history`
8. THE Frontend_Service SHALL define TypeScript interfaces matching `ChatRequest`, `ChatResponse`, and `ChatHistoryResponse` schemas

### Requirement 4: Meal API Alignment

**User Story:** As a developer, I want the meal service to use the correct endpoints and parameters, so that users can view meal plans, search dishes, and generate shopping lists.

#### Acceptance Criteria

1. WHEN the frontend calls `getMealPlan()`, THE Frontend_Service SHALL send a GET request to `/meals/plan` without date parameters
2. THE Frontend_Service SHALL remove date filtering parameters as the backend does not support them
3. WHEN the frontend calls `getMealSchedule()`, THE Frontend_Service SHALL send a GET request to `/meals/schedule`
4. WHEN the frontend calls `getTodayMeals()`, THE Frontend_Service SHALL send a GET request to `/meals/today`
5. WHEN the frontend calls `getNextMeal()`, THE Frontend_Service SHALL send a GET request to `/meals/next`
6. THE Frontend_Service SHALL remove `getMealDetails(mealId)` as the backend does not have individual meal endpoints
7. WHEN the frontend calls `searchDishes()`, THE Frontend_Service SHALL send a GET request to `/dishes/search` (not `/meals/dishes/search`)
8. WHEN searching dishes, THE Frontend_Service SHALL support query parameters: `meal_type`, `diet_type`, `max_prep_time`, `max_calories`, `limit`, `offset`
9. WHEN the frontend calls `getDishDetails()`, THE Frontend_Service SHALL send a GET request to `/dishes/{dish_id}`
10. WHEN the frontend calls `generateShoppingList()`, THE Frontend_Service SHALL send a GET request to `/shopping-list/` with query parameter `weeks`
11. THE Frontend_Service SHALL remove date-based shopping list parameters and use week-based parameters instead
12. THE Frontend_Service SHALL define TypeScript interfaces matching `MealPlanResponse`, `MealScheduleResponse`, `DishResponse`, and `ShoppingListResponse` schemas

### Requirement 5: Workout API Alignment

**User Story:** As a developer, I want the workout service to correctly retrieve workout data, so that users can view their workout plans and schedules.

#### Acceptance Criteria

1. WHEN the frontend calls `getWorkoutPlan()`, THE Frontend_Service SHALL send a GET request to `/workouts/plan`
2. WHEN the frontend calls `getWorkoutDay()`, THE Frontend_Service SHALL send a GET request to `/workouts/plan/day/{day_number}`
3. WHEN the frontend calls `getTodayWorkout()`, THE Frontend_Service SHALL send a GET request to `/workouts/today`
4. WHEN the frontend calls `getWeekWorkouts()`, THE Frontend_Service SHALL send a GET request to `/workouts/week`
5. WHEN the frontend calls `getWorkoutSchedule()`, THE Frontend_Service SHALL send a GET request to `/workouts/schedule`
6. WHEN the frontend calls `updateWorkoutSchedule()`, THE Frontend_Service SHALL send a PATCH request to `/workouts/schedule`
7. THE Frontend_Service SHALL remove `logSet()` method as the backend does not have a workout logging endpoint
8. THE Frontend_Service SHALL remove `completeWorkout()` method as the backend does not have a workout completion endpoint
9. THE Frontend_Service SHALL remove `getHistory()` method as the backend does not have a workout history endpoint
10. THE Frontend_Service SHALL define TypeScript interfaces matching `WorkoutPlanResponse`, `WorkoutDayResponse`, and `WorkoutScheduleResponse` schemas

### Requirement 6: Meal Template API Integration

**User Story:** As a developer, I want to integrate meal template endpoints, so that users can view and regenerate their meal templates with assigned dishes.

#### Acceptance Criteria

1. WHEN the frontend calls `getTodayMealsWithDishes()`, THE Frontend_Service SHALL send a GET request to `/meal-templates/today`
2. WHEN the frontend calls `getNextMealWithDishes()`, THE Frontend_Service SHALL send a GET request to `/meal-templates/next`
3. WHEN the frontend calls `getMealTemplate()`, THE Frontend_Service SHALL send a GET request to `/meal-templates/template` with optional query parameter `week_number`
4. WHEN the frontend calls `regenerateMealTemplate()`, THE Frontend_Service SHALL send a POST request to `/meal-templates/template/regenerate` with request body matching `TemplateRegenerateRequest`
5. THE Frontend_Service SHALL define TypeScript interfaces matching `TodayMealsResponse`, `NextMealResponse`, and `MealTemplateResponse` schemas

### Requirement 7: Authentication API Verification

**User Story:** As a developer, I want to verify that authentication endpoints are correctly implemented, so that users can register, login, and access protected resources.

#### Acceptance Criteria

1. WHEN the frontend calls `register()`, THE Frontend_Service SHALL send a POST request to `/auth/register` with `{email, password}`
2. WHEN the frontend calls `login()`, THE Frontend_Service SHALL send a POST request to `/auth/login` with `{email, password}`
3. WHEN the frontend calls `getCurrentUser()`, THE Frontend_Service SHALL send a GET request to `/auth/me`
4. WHEN authentication succeeds, THE Frontend_Service SHALL store the `access_token` from the `TokenResponse`
5. THE Frontend_Service SHALL define TypeScript interfaces matching `TokenResponse` and `UserResponse` schemas

### Requirement 8: Voice Session API Verification

**User Story:** As a developer, I want to verify that voice session endpoints are correctly implemented, so that users can start, monitor, and end voice coaching sessions.

#### Acceptance Criteria

1. WHEN the frontend calls `startSession()`, THE Frontend_Service SHALL send a POST request to `/voice-sessions/start` with `{agent_type}`
2. WHEN the frontend calls `getSessionStatus()`, THE Frontend_Service SHALL send a GET request to `/voice-sessions/{room_name}/status`
3. WHEN the frontend calls `endSession()`, THE Frontend_Service SHALL send a DELETE request to `/voice-sessions/{room_name}`
4. WHEN the frontend calls `getActiveSessions()`, THE Frontend_Service SHALL send a GET request to `/voice-sessions/active`
5. THE Frontend_Service SHALL define TypeScript interfaces matching `VoiceSessionResponse` and `VoiceSessionStatus` schemas

### Requirement 9: Type Safety and Validation

**User Story:** As a developer, I want all API calls to be type-safe, so that type errors are caught at compile time rather than runtime.

#### Acceptance Criteria

1. THE Frontend_Service SHALL define TypeScript interfaces for all request payloads
2. THE Frontend_Service SHALL define TypeScript interfaces for all response payloads
3. THE Frontend_Service SHALL use generic typing for axios responses to ensure type safety
4. WHEN an API call is made, THE Frontend_Service SHALL validate request data against TypeScript interfaces at compile time
5. WHEN a response is received, THE Frontend_Service SHALL type the response data according to the expected schema

### Requirement 10: Error Handling and Response Mapping

**User Story:** As a developer, I want consistent error handling across all API services, so that errors are properly caught and reported to users.

#### Acceptance Criteria

1. WHEN an API call fails with a 4xx error, THE Frontend_Service SHALL throw an error with the backend's error message
2. WHEN an API call fails with a 5xx error, THE Frontend_Service SHALL throw a generic server error
3. WHEN a network error occurs, THE Frontend_Service SHALL throw a network connectivity error
4. WHEN the backend returns a 401 Unauthorized, THE Frontend_Service SHALL clear authentication tokens and redirect to login
5. THE Frontend_Service SHALL preserve error details from the backend for debugging purposes
