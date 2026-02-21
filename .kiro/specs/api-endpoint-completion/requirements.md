# Requirements Document

## Introduction

This specification addresses the completion of missing API endpoints in the Shuren fitness backend to achieve 100% test coverage. Currently, the system has 89% test pass rate (17/19 tests passing). Two critical endpoints are missing implementation:

1. **GET /api/v1/dishes** - List all dishes endpoint
2. **POST /api/v1/chat/sessions** - Create chat session endpoint

These endpoints are essential for the frontend application to function properly, allowing users to browse available dishes and initiate chat conversations with AI agents.

## Glossary

- **API**: Application Programming Interface - REST endpoints for client-server communication
- **Dish**: A meal recipe with nutritional information, ingredients, and preparation details
- **Chat_Session**: A conversation context between a user and AI agents
- **JWT**: JSON Web Token - authentication token for API requests
- **Pagination**: Technique for dividing large result sets into smaller pages
- **Allergen**: Food ingredient that may cause allergic reactions
- **DishService**: Backend service layer for dish-related business logic
- **ChatService**: Backend service layer for chat-related business logic
- **Router**: FastAPI component that groups related endpoints

## Requirements

### Requirement 1: Dishes List Endpoint

**User Story:** As a mobile app user, I want to browse all available dishes, so that I can explore meal options and select dishes for my meal plan.

#### Acceptance Criteria

1. WHEN a user sends GET request to /api/v1/dishes with valid JWT token, THE System SHALL return HTTP 200 OK with an array of dish summary objects
2. WHEN a user sends GET request to /api/v1/dishes without authentication token, THE System SHALL return HTTP 401 Unauthorized
3. WHEN a user sends GET request to /api/v1/dishes with limit parameter, THE System SHALL return at most the specified number of dishes
4. WHEN a user sends GET request to /api/v1/dishes with offset parameter, THE System SHALL skip the specified number of dishes before returning results
5. WHEN a user sends GET request to /api/v1/dishes with meal_type parameter, THE System SHALL return only dishes matching that meal type
6. WHEN a user sends GET request to /api/v1/dishes with diet_type parameter, THE System SHALL return only dishes matching that diet type
7. WHEN a user with allergen preferences sends GET request to /api/v1/dishes, THE System SHALL exclude dishes containing those allergens
8. WHEN a user sends GET request to /api/v1/dishes without any parameters, THE System SHALL return the first 50 dishes ordered by popularity
9. WHEN a user sends GET request to /api/v1/dishes with limit greater than 100, THE System SHALL return HTTP 400 Bad Request
10. WHEN a user sends GET request to /api/v1/dishes with negative offset, THE System SHALL return HTTP 400 Bad Request

### Requirement 2: Chat Sessions Endpoint

**User Story:** As a mobile app user, I want to create new chat sessions, so that I can start conversations with AI fitness agents.

#### Acceptance Criteria

1. WHEN a user sends POST request to /api/v1/chat/sessions with valid JWT token, THE System SHALL create a new chat session and return HTTP 201 Created
2. WHEN a user sends POST request to /api/v1/chat/sessions without authentication token, THE System SHALL return HTTP 401 Unauthorized
3. WHEN a user sends POST request to /api/v1/chat/sessions with session_type in request body, THE System SHALL create a session with that type
4. WHEN a user sends POST request to /api/v1/chat/sessions without session_type in request body, THE System SHALL create a session with type "general"
5. WHEN a user sends POST request to /api/v1/chat/sessions with context_data in request body, THE System SHALL store that context data in the session
6. WHEN a user sends POST request to /api/v1/chat/sessions, THE System SHALL return session object containing id, session_type, status, started_at, ended_at, and last_activity_at fields
7. WHEN a user sends POST request to /api/v1/chat/sessions with invalid session_type, THE System SHALL return HTTP 422 Unprocessable Entity
8. WHEN a user sends POST request to /api/v1/chat/sessions, THE System SHALL set session status to "active"
9. WHEN a user sends POST request to /api/v1/chat/sessions, THE System SHALL set started_at and last_activity_at to current timestamp

### Requirement 3: Chat Router Registration

**User Story:** As a backend developer, I want the chat router registered in API v1, so that chat endpoints are accessible via the /api/v1 prefix.

#### Acceptance Criteria

1. WHEN the FastAPI application starts, THE System SHALL register the chat router with prefix "/chat"
2. WHEN the FastAPI application starts, THE System SHALL tag chat endpoints with "Chat" tag
3. WHEN a user accesses /api/v1/chat/sessions, THE System SHALL route the request to the chat sessions endpoint
4. WHEN a user accesses /api/v1/chat/message, THE System SHALL route the request to the chat message endpoint
5. WHEN a user accesses /api/v1/chat/history, THE System SHALL route the request to the chat history endpoint

### Requirement 4: API Documentation

**User Story:** As a frontend developer, I want comprehensive API documentation, so that I can understand how to use the endpoints correctly.

#### Acceptance Criteria

1. WHEN a developer accesses /docs, THE System SHALL display OpenAPI documentation for GET /api/v1/dishes endpoint
2. WHEN a developer accesses /docs, THE System SHALL display OpenAPI documentation for POST /api/v1/chat/sessions endpoint
3. WHEN a developer views GET /api/v1/dishes documentation, THE System SHALL show example request with query parameters
4. WHEN a developer views GET /api/v1/dishes documentation, THE System SHALL show example response with dish array
5. WHEN a developer views POST /api/v1/chat/sessions documentation, THE System SHALL show example request body with session_type
6. WHEN a developer views POST /api/v1/chat/sessions documentation, THE System SHALL show example response with session object

### Requirement 5: Service Layer Integration

**User Story:** As a backend developer, I want endpoints to use existing service layer methods, so that business logic remains centralized and maintainable.

#### Acceptance Criteria

1. WHEN GET /api/v1/dishes endpoint is called, THE System SHALL use DishService.search_dishes method
2. WHEN POST /api/v1/chat/sessions endpoint is called, THE System SHALL use ChatService.create_session method
3. WHEN GET /api/v1/dishes endpoint retrieves user profile, THE System SHALL extract allergen preferences from dietary_preferences
4. WHEN POST /api/v1/chat/sessions endpoint creates session, THE System SHALL pass user_id from authenticated user
5. WHEN endpoints encounter service layer exceptions, THE System SHALL convert them to appropriate HTTP error responses

### Requirement 6: Response Format Consistency

**User Story:** As a frontend developer, I want consistent response formats across all endpoints, so that I can write predictable client code.

#### Acceptance Criteria

1. WHEN GET /api/v1/dishes returns dishes, THE System SHALL use DishSummaryResponse schema for each dish
2. WHEN POST /api/v1/chat/sessions returns session, THE System SHALL use ChatSessionResponse schema
3. WHEN endpoints return errors, THE System SHALL use FastAPI standard error format with detail field
4. WHEN endpoints return arrays, THE System SHALL return empty array when no results found
5. WHEN endpoints return timestamps, THE System SHALL use ISO 8601 format

### Requirement 7: Performance Requirements

**User Story:** As a mobile app user, I want fast API responses, so that the app feels responsive and smooth.

#### Acceptance Criteria

1. WHEN GET /api/v1/dishes is called with default parameters, THE System SHALL respond within 200 milliseconds
2. WHEN POST /api/v1/chat/sessions is called, THE System SHALL respond within 150 milliseconds
3. WHEN GET /api/v1/dishes is called with filters, THE System SHALL use database indexes for efficient querying
4. WHEN endpoints access user profile, THE System SHALL use existing database session without additional queries
5. WHEN endpoints serialize responses, THE System SHALL use Pydantic model validation for efficient conversion

### Requirement 8: Test Coverage

**User Story:** As a QA engineer, I want all endpoints to pass automated tests, so that I can verify system correctness.

#### Acceptance Criteria

1. WHEN test-api-endpoints.js runs, THE System SHALL pass GET /dishes test with HTTP 200 response
2. WHEN test-api-endpoints.js runs, THE System SHALL pass POST /chat/sessions test with HTTP 200 or 201 response
3. WHEN all tests run, THE System SHALL achieve 100% pass rate (19/19 tests passing)
4. WHEN GET /dishes test runs, THE System SHALL return array of dish objects
5. WHEN POST /chat/sessions test runs, THE System SHALL return session object with id field
