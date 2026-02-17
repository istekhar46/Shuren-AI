# Shuren Backend API Documentation

**Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Authentication:** JWT Bearer Token

---

## Table of Contents

1. [Authentication](#authentication)
2. [Onboarding Endpoints](#onboarding-endpoints)
3. [Chat Endpoints](#chat-endpoints)
4. [User Endpoints](#user-endpoints)
5. [Error Codes](#error-codes)
6. [Request/Response Examples](#requestresponse-examples)

---

## Authentication

All endpoints (except registration and login) require JWT authentication.

**Header Format:**
```
Authorization: Bearer <jwt_token>
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Valid token but insufficient permissions

---

## Onboarding Endpoints

### 1. Get Onboarding Progress

**Endpoint:** `GET /api/v1/onboarding/progress`

**Description:** Retrieve rich progress metadata for UI indicators including current state, completed states, and completion percentage.

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "current_state": 3,
  "total_states": 9,
  "completed_states": [1, 2],
  "current_state_info": {
    "state_number": 3,
    "name": "Workout Preferences & Constraints",
    "agent": "workout_planning",
    "description": "Tell us about your equipment and any limitations",
    "required_fields": ["equipment", "injuries", "limitations"]
  },
  "next_state_info": {
    "state_number": 4,
    "name": "Diet Preferences & Restrictions",
    "agent": "diet_planning",
    "description": "Share your dietary preferences and restrictions",
    "required_fields": ["diet_type", "allergies", "intolerances", "dislikes"]
  },
  "is_complete": false,
  "completion_percentage": 22,
  "can_complete": false
}
```

**Error Responses:**
- `404 Not Found`: Onboarding state not found

---

### 2. Get Onboarding State

**Endpoint:** `GET /api/v1/onboarding/state`

**Description:** Retrieve current onboarding state with all saved step data.

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "current_step": 3,
  "is_complete": false,
  "step_data": {
    "step_1": {
      "fitness_level": "beginner"
    },
    "step_2": {
      "goals": [
        {
          "goal_type": "fat_loss",
          "priority": 1
        }
      ]
    }
  }
}
```

**Error Responses:**
- `404 Not Found`: Onboarding state not found

---

### 3. Save Onboarding Step

**Endpoint:** `POST /api/v1/onboarding/step`

**Description:** Save onboarding step data with validation. Supports 9 states (1-9). Optionally accepts agent context header for logging.

**Authentication:** Required

**Headers:**
- `X-Agent-Context` (optional): Agent type calling this endpoint (e.g., "workout_planning")

**Request Body:**

```json
{
  "step": 3,
  "data": {
    "equipment": ["dumbbells", "resistance_bands"],
    "injuries": [],
    "limitations": ["lower_back_pain"],
    "target_weight_kg": 75.0
  }
}
```

**Response:** `200 OK`

```json
{
  "current_step": 3,
  "is_complete": false,
  "message": "Step 3 saved successfully",
  "next_state": 4,
  "next_state_info": {
    "state_number": 4,
    "name": "Diet Preferences & Restrictions",
    "agent": "diet_planning",
    "description": "Share your dietary preferences and restrictions",
    "required_fields": ["diet_type", "allergies", "intolerances", "dislikes"]
  }
}
```

**Validation Rules by State:**

**State 1: Fitness Level**
```json
{
  "step": 1,
  "data": {
    "fitness_level": "beginner"  // Required: "beginner", "intermediate", or "advanced"
  }
}
```

**State 2: Fitness Goals**
```json
{
  "step": 2,
  "data": {
    "goals": [  // Required: non-empty array
      {
        "goal_type": "fat_loss",  // Required: "fat_loss", "muscle_gain", or "general_fitness"
        "priority": 1
      }
    ]
  }
}
```

**State 3: Workout Constraints (Merged from old steps 4 & 5)**
```json
{
  "step": 3,
  "data": {
    "equipment": ["dumbbells"],  // Required: array of strings
    "injuries": [],  // Required: array (can be empty)
    "limitations": ["lower_back_pain"],  // Required: array (can be empty)
    "target_weight_kg": 75.0,  // Optional: 30-300
    "target_body_fat_percentage": 15.0  // Optional: 1-50
  }
}
```

**State 4: Dietary Preferences**
```json
{
  "step": 4,
  "data": {
    "diet_type": "omnivore",  // Required: "omnivore", "vegetarian", "vegan", "pescatarian", "keto", "paleo"
    "allergies": ["peanuts"],  // Required: array (can be empty)
    "intolerances": ["lactose"],  // Required: array (can be empty)
    "dislikes": ["mushrooms"]  // Required: array (can be empty)
  }
}
```

**State 5: Meal Plan**
```json
{
  "step": 5,
  "data": {
    "daily_calorie_target": 2000,  // Required: 1000-5000
    "protein_percentage": 30.0,  // Required: 0-100
    "carbs_percentage": 40.0,  // Required: 0-100
    "fats_percentage": 30.0  // Required: 0-100 (sum must equal 100)
  }
}
```

**State 6: Meal Schedule**
```json
{
  "step": 6,
  "data": {
    "meals": [  // Required: non-empty array
      {
        "meal_name": "Breakfast",  // Required
        "scheduled_time": "08:00",  // Required: HH:MM format
        "enable_notifications": true  // Optional: default true
      }
    ]
  }
}
```

**State 7: Workout Schedule**
```json
{
  "step": 7,
  "data": {
    "workouts": [  // Required: non-empty array
      {
        "day_of_week": 1,  // Required: 0-6 (Monday=0, Sunday=6)
        "scheduled_time": "07:00",  // Required: HH:MM format
        "enable_notifications": true  // Optional: default true
      }
    ]
  }
}
```

**State 8: Hydration**
```json
{
  "step": 8,
  "data": {
    "daily_water_target_ml": 2000,  // Required: 500-10000
    "reminder_frequency_minutes": 60  // Required: 15-480
  }
}
```

**State 9: Supplements (Optional)**
```json
{
  "step": 9,
  "data": {
    "interested_in_supplements": false,  // Required: boolean
    "current_supplements": []  // Optional: array of strings
  }
}
```

**Error Responses:**
- `400 Bad Request`: Validation error with field information
  ```json
  {
    "detail": {
      "message": "Protein percentage must be between 0 and 100",
      "field": "protein_percentage",
      "error_code": "VALIDATION_ERROR"
    }
  }
  ```
- `422 Unprocessable Entity`: Request format error

---

### 4. Complete Onboarding

**Endpoint:** `POST /api/v1/onboarding/complete`

**Description:** Complete onboarding and create locked user profile with all related entities.

**Authentication:** Required

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "is_locked": true,
  "fitness_level": "beginner",
  "fitness_goals": [...],
  "physical_constraints": [...],
  "dietary_preferences": {...},
  "meal_plan": {...},
  "meal_schedules": [...],
  "workout_schedules": [...],
  "hydration_preferences": {...},
  "lifestyle_baseline": {...}
}
```

**Error Responses:**
- `400 Bad Request`: Onboarding incomplete

---

## Chat Endpoints

### 1. Chat (Post-Onboarding)

**Endpoint:** `POST /api/v1/chat`

**Description:** Send a message to the AI assistant. Only available to users who have completed onboarding. All queries are routed to the general agent.

**Authentication:** Required

**Request Body:**

```json
{
  "message": "What should I eat for breakfast?",
  "agent_type": "general"  // Optional: must be "general" if provided
}
```

**Response:** `200 OK`

```json
{
  "response": "Based on your meal plan, I recommend...",
  "agent_type": "general",
  "conversation_id": "user-uuid",
  "tools_used": ["get_meal_plan", "get_dietary_preferences"]
}
```

**Error Responses:**
- `403 Forbidden`: Onboarding not completed
  ```json
  {
    "detail": {
      "message": "Complete onboarding to access this feature",
      "error_code": "ONBOARDING_REQUIRED",
      "redirect": "/onboarding",
      "onboarding_progress": {
        "current_state": 3,
        "completion_percentage": 33
      }
    }
  }
  ```
- `403 Forbidden`: Non-general agent requested
  ```json
  {
    "detail": {
      "message": "Only general agent available after onboarding",
      "error_code": "AGENT_NOT_ALLOWED",
      "requested_agent": "workout",
      "allowed_agent": "general"
    }
  }
  ```

---

### 2. Onboarding Chat

**Endpoint:** `POST /api/v1/chat/onboarding`

**Description:** Handle chat-based onboarding with specialized agent routing. Routes to appropriate agent based on current state. Agent can save data via function tools.

**Authentication:** Required

**Request Body:**

```json
{
  "message": "I'm a beginner",
  "current_state": 1
}
```

**Response:** `200 OK`

```json
{
  "response": "Great! As a beginner, I'll create a plan that...",
  "agent_type": "workout_planning",
  "state_updated": true,
  "new_state": 2,
  "progress": {
    "current_state": 2,
    "total_states": 9,
    "completed_states": [1],
    "completion_percentage": 11,
    "is_complete": false,
    "can_complete": false
  }
}
```

**State-to-Agent Mapping:**
- States 1-3: `workout_planning` (Fitness Level, Goals, Constraints)
- States 4-5: `diet_planning` (Dietary Preferences, Meal Plan)
- States 6-8: `scheduler` (Meal Schedule, Workout Schedule, Hydration)
- State 9: `supplement` (Supplement Preferences)

**Error Responses:**
- `403 Forbidden`: Onboarding already completed
  ```json
  {
    "detail": "Onboarding already completed"
  }
  ```
- `400 Bad Request`: State mismatch
  ```json
  {
    "detail": "State mismatch. Current: 5, Requested: 3"
  }
  ```
- `404 Not Found`: Onboarding state not found

---

### 3. Chat Stream

**Endpoint:** `GET /api/v1/chat/stream`

**Description:** Send a message and receive a streaming response using Server-Sent Events (SSE). This endpoint provides real-time text streaming as the AI generates responses, offering better user experience compared to waiting for complete responses.

**Authentication:** Required (via query parameter due to EventSource API limitations)

**Query Parameters:**
- `message` (required): The user's message to send to the AI
- `token` (required): JWT authentication token (EventSource doesn't support custom headers)

**Example Request:**
```
GET /api/v1/chat/stream?message=What%20should%20I%20eat%20for%20breakfast%3F&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

**Response:** `200 OK` (text/event-stream)

The response is a stream of Server-Sent Events following the SSE specification. Each event is formatted as:
```
data: <JSON payload>\n\n
```

**Event Types:**

1. **Chunk Event** - Contains a piece of the AI response
```
data: {"chunk": "Based on "}

data: {"chunk": "your meal plan, "}

data: {"chunk": "I recommend..."}
```

2. **Completion Event** - Signals the end of the stream
```
data: {"done": true, "agent_type": "general"}
```

3. **Error Event** - Indicates an error occurred during streaming
```
data: {"error": "Failed to process message"}
```

**SSE Event Format Specification:**

All events follow the W3C Server-Sent Events specification:
- Each event starts with `data: ` prefix
- Event payload is valid JSON
- Each event ends with double newline `\n\n`
- Events are sent in order and cannot be reordered

**Chunk Event Schema:**
```json
{
  "chunk": "string"  // A piece of the AI response text
}
```

**Completion Event Schema:**
```json
{
  "done": true,
  "agent_type": "string"  // The agent that handled the request (e.g., "general")
}
```

**Error Event Schema:**
```json
{
  "error": "string"  // Human-readable error message
}
```

**Client Implementation Example (JavaScript):**
```javascript
const token = localStorage.getItem('jwt_token');
const message = encodeURIComponent('What should I eat for breakfast?');
const url = `/api/v1/chat/stream?message=${message}&token=${token}`;

const eventSource = new EventSource(url);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.error) {
    console.error('Error:', data.error);
    eventSource.close();
  } else if (data.done) {
    console.log('Stream complete. Agent:', data.agent_type);
    eventSource.close();
  } else if (data.chunk) {
    // Append chunk to UI
    appendToMessage(data.chunk);
  }
};

eventSource.onerror = (error) => {
  console.error('Connection error:', error);
  eventSource.close();
};
```

**Error Responses:**

- `401 Unauthorized`: Invalid or missing authentication token
  ```json
  {
    "detail": "Invalid authentication credentials"
  }
  ```
  
- `403 Forbidden`: Onboarding not completed
  ```json
  {
    "detail": {
      "message": "Complete onboarding to access this feature",
      "error_code": "ONBOARDING_REQUIRED"
    }
  }
  ```

**Timeout Behavior:**
- If no chunks are generated for 30 seconds, the server sends an error event and closes the stream
- Client should implement reconnection logic with exponential backoff

**Connection Management:**
- Maximum 1 concurrent stream per user
- Stream automatically closes after completion or error
- Client should close EventSource when navigating away

**Performance Characteristics:**
- First chunk typically arrives within 500ms
- Subsequent chunks stream as generated by the LLM
- Average chunk size: 5-20 characters
- Total response time depends on message complexity

---

### 4. Onboarding Chat Stream

**Endpoint:** `GET /api/v1/chat/onboarding-stream`

**Description:** Handle chat-based onboarding with streaming responses using Server-Sent Events (SSE). This endpoint provides the same real-time streaming experience during onboarding as the regular chat stream endpoint.

**Authentication:** Required (via query parameter due to EventSource API limitations)

**Query Parameters:**
- `message` (required): The user's message to send to the onboarding agent
- `token` (required): JWT authentication token (EventSource doesn't support custom headers)

**Example Request:**
```
GET /api/v1/chat/onboarding-stream?message=I%27m%20a%20beginner&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

**Response:** `200 OK` (text/event-stream)

The response follows the same SSE format as the regular chat stream endpoint.

**Event Types:**

1. **Chunk Event** - Contains a piece of the AI response
```
data: {"chunk": "Great! "}

data: {"chunk": "As a beginner, "}

data: {"chunk": "I'll create a plan that..."}
```

2. **Completion Event** - Signals the end of the stream
```
data: {"done": true, "agent_type": "workout_planning"}
```

3. **Error Event** - Indicates an error occurred during streaming
```
data: {"error": "Failed to process onboarding message"}
```

**State-to-Agent Routing:**

The endpoint automatically routes to the appropriate agent based on the user's current onboarding state:
- States 1-3: `workout_planning` (Fitness Level, Goals, Constraints)
- States 4-5: `diet_planning` (Dietary Preferences, Meal Plan)
- States 6-8: `scheduler` (Meal Schedule, Workout Schedule, Hydration)
- State 9: `supplement` (Supplement Preferences)

**Onboarding State Management:**

After streaming completes, the endpoint:
1. Saves the complete conversation to the database
2. Updates onboarding progress if the agent saved data via function tools
3. Returns the agent type in the completion event

**Client Implementation Example (JavaScript):**
```javascript
const token = localStorage.getItem('jwt_token');
const message = encodeURIComponent("I'm a beginner");
const url = `/api/v1/chat/onboarding-stream?message=${message}&token=${token}`;

const eventSource = new EventSource(url);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.error) {
    console.error('Error:', data.error);
    eventSource.close();
  } else if (data.done) {
    console.log('Stream complete. Agent:', data.agent_type);
    // Refresh onboarding progress
    fetchOnboardingProgress();
    eventSource.close();
  } else if (data.chunk) {
    // Append chunk to UI
    appendToMessage(data.chunk);
  }
};

eventSource.onerror = (error) => {
  console.error('Connection error:', error);
  eventSource.close();
};
```

**Error Responses:**

- `401 Unauthorized`: Invalid or missing authentication token
  ```json
  {
    "detail": "Invalid authentication credentials"
  }
  ```
  
- `403 Forbidden`: Onboarding already completed
  ```json
  {
    "detail": "Onboarding already completed"
  }
  ```

- `404 Not Found`: Onboarding state not found
  ```json
  {
    "detail": "Onboarding state not found"
  }
  ```

**Timeout Behavior:**
- If no chunks are generated for 30 seconds, the server sends an error event and closes the stream
- Client should implement reconnection logic with exponential backoff

**Connection Management:**
- Maximum 1 concurrent stream per user
- Stream automatically closes after completion or error
- Client should close EventSource when navigating away or switching onboarding states

**Performance Characteristics:**
- First chunk typically arrives within 500ms
- Subsequent chunks stream as generated by the LLM
- Average chunk size: 5-20 characters
- Onboarding state updates occur after stream completion

---

### 5. Get Chat History

**Endpoint:** `GET /api/v1/chat/history?limit=50`

**Description:** Retrieve conversation history in chronological order.

**Authentication:** Required

**Query Parameters:**
- `limit` (optional): Maximum messages to return (default: 50, max: 200)

**Response:** `200 OK`

```json
{
  "messages": [
    {
      "role": "user",
      "content": "What should I eat?",
      "agent_type": null,
      "created_at": "2026-02-13T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "I recommend...",
      "agent_type": "general",
      "created_at": "2026-02-13T10:00:02Z"
    }
  ],
  "total": 42
}
```

---

### 6. Delete Chat History

**Endpoint:** `DELETE /api/v1/chat/history`

**Description:** Permanently delete all conversation history for the authenticated user.

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "status": "cleared"
}
```

---

## User Endpoints

### 1. Get Current User

**Endpoint:** `GET /api/v1/users/me`

**Description:** Retrieve current user information with access control flags.

**Authentication:** Required

**Response:** `200 OK`

**For Incomplete Onboarding:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "onboarding_completed": false,
  "access_control": {
    "can_access_dashboard": false,
    "can_access_workouts": false,
    "can_access_meals": false,
    "can_access_chat": true,
    "can_access_profile": false,
    "locked_features": ["dashboard", "workouts", "meals", "profile"],
    "unlock_message": "Complete onboarding to unlock all features",
    "onboarding_progress": {
      "current_state": 3,
      "total_states": 9,
      "completion_percentage": 33
    }
  }
}
```

**For Completed Onboarding:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "onboarding_completed": true,
  "access_control": {
    "can_access_dashboard": true,
    "can_access_workouts": true,
    "can_access_meals": true,
    "can_access_chat": true,
    "can_access_profile": true,
    "locked_features": [],
    "unlock_message": null,
    "onboarding_progress": null
  }
}
```

---

## Error Codes

### Standard HTTP Status Codes

| Code | Description | When It Occurs |
|------|-------------|----------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data or validation error |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Request format error (Pydantic validation) |
| 500 | Internal Server Error | Unexpected server error |

### Custom Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Data validation failed (includes field information) |
| `ONBOARDING_REQUIRED` | 403 | User must complete onboarding first |
| `AGENT_NOT_ALLOWED` | 403 | Requested agent not available |
| `STATE_MISMATCH` | 400 | Frontend state doesn't match backend |
| `PROFILE_LOCKED` | 403 | Profile must be unlocked before modifications |
| `NOT_FOUND` | 404 | Resource not found |
| `DATABASE_ERROR` | 500 | Database operation failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Request/Response Examples

### Example 1: Complete Onboarding Flow via Chat

**Step 1: Check Progress**
```bash
GET /api/v1/onboarding/progress
Authorization: Bearer <token>
```

Response:
```json
{
  "current_state": 1,
  "total_states": 9,
  "completed_states": [],
  "completion_percentage": 0,
  "can_complete": false
}
```

**Step 2: Chat with Workout Agent (State 1)**
```bash
POST /api/v1/chat/onboarding
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "I'm a beginner",
  "current_state": 1
}
```

Response:
```json
{
  "response": "Great! I've saved your fitness level as beginner...",
  "agent_type": "workout_planning",
  "state_updated": true,
  "new_state": 2,
  "progress": {
    "current_state": 2,
    "completion_percentage": 11
  }
}
```

**Step 3: Continue Through States 2-9**
(Repeat chat requests for each state)

**Step 4: Complete Onboarding**
```bash
POST /api/v1/onboarding/complete
Authorization: Bearer <token>
```

Response: `201 Created` with full profile

---

### Example 2: Post-Onboarding Chat

```bash
POST /api/v1/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "What exercises should I do today?"
}
```

Response:
```json
{
  "response": "Based on your workout schedule, today is leg day...",
  "agent_type": "general",
  "conversation_id": "user-uuid",
  "tools_used": ["get_workout_schedule", "get_workout_plan"]
}
```

---

### Example 3: Validation Error

```bash
POST /api/v1/onboarding/step
Authorization: Bearer <token>
Content-Type: application/json

{
  "step": 5,
  "data": {
    "daily_calorie_target": 2000,
    "protein_percentage": 150.0,  // Invalid: > 100
    "carbs_percentage": 40.0,
    "fats_percentage": 30.0
  }
}
```

Response: `400 Bad Request`
```json
{
  "detail": {
    "message": "Protein percentage must be between 0 and 100",
    "field": "protein_percentage",
    "error_code": "VALIDATION_ERROR"
  }
}
```

---

### Example 4: Access Control Error

```bash
POST /api/v1/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Hello"
}
```

Response (if onboarding incomplete): `403 Forbidden`
```json
{
  "detail": {
    "message": "Complete onboarding to access this feature",
    "error_code": "ONBOARDING_REQUIRED",
    "redirect": "/onboarding",
    "onboarding_progress": {
      "current_state": 3,
      "completion_percentage": 33
    }
  }
}
```

---

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI:** `/api/docs`
- **ReDoc:** `/api/redoc`
- **OpenAPI JSON:** `/api/openapi.json`

These interfaces allow you to:
- Browse all endpoints
- View request/response schemas
- Test endpoints directly in the browser
- Download OpenAPI specification

---

## Rate Limiting

All endpoints are rate-limited to prevent abuse:

- **Limit:** 100 requests per minute per user
- **Response:** `429 Too Many Requests` when exceeded

---

## Changelog

### Version 1.0.0 (2026-02-13)

**New Endpoints:**
- `GET /api/v1/onboarding/progress` - Rich progress metadata
- `POST /api/v1/chat/onboarding` - Chat-based onboarding

**Modified Endpoints:**
- `GET /api/v1/users/me` - Added `access_control` object
- `POST /api/v1/onboarding/step` - Now supports 9 states (was 11), accepts `X-Agent-Context` header
- `POST /api/v1/chat` - Enforces agent restrictions post-onboarding

**Breaking Changes:**
- None - all changes are backward compatible

**State Consolidation:**
- Onboarding reduced from 11 steps to 9 states
- Old steps 4 & 5 merged into new state 3
- Original data preserved in migration metadata

---

## Support

For API support or bug reports, contact the backend team or file an issue in the repository.
