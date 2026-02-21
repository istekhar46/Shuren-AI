# Requirements Document: Phase 1 Foundation

## Introduction

Phase 1 establishes the foundational infrastructure for the Shuren AI fitness application backend. This phase implements the core FastAPI project structure, database schema, authentication system, and onboarding API endpoints. The system must support a mandatory one-time onboarding flow that captures user fitness profiles, with strict profile locking mechanisms to prevent silent configuration changes.

## Glossary

- **System**: The Shuren backend API service
- **User**: An individual using the Shuren fitness application
- **Onboarding_Flow**: The mandatory 11-step process for initial user configuration
- **User_Profile**: The current active configuration for a user (single source of truth)
- **Profile_Lock**: A mechanism preventing modifications to user configuration without explicit user action
- **Profile_Version**: An immutable audit record of profile changes
- **Onboarding_State**: The current progress through the onboarding flow (steps 0-11)
- **Fitness_Goal**: A quantifiable target the user wants to achieve
- **Physical_Constraint**: Equipment availability, injuries, or physical limitations
- **Dietary_Preference**: Diet type, restrictions, and allergies
- **Meal_Plan**: A fixed nutritional structure defining daily caloric and macro targets
- **Meal_Schedule**: Timing configuration for meal notifications
- **Workout_Schedule**: Days and times for workout sessions
- **Hydration_Preference**: Water intake reminder configuration
- **Lifestyle_Baseline**: Self-reported energy, stress, and sleep patterns
- **JWT_Token**: JSON Web Token for authentication
- **OAuth_Provider**: External authentication service (e.g., Google)
- **Provider_User_ID**: Unique identifier from OAuth provider
- **Soft_Delete**: Marking records as deleted without physical removal (deleted_at timestamp)

## Requirements

### Requirement 1: User Registration and Authentication

**User Story:** As a new user, I want to register and authenticate with the system using email/password or Google OAuth, so that I can securely access my personalized fitness data.

#### Acceptance Criteria

1. WHEN a user provides valid registration data (email, password, name), THE System SHALL create a new user account with a unique identifier
2. WHEN a user provides an email that already exists for email/password auth, THE System SHALL reject the registration and return a descriptive error
3. WHEN a user provides valid login credentials, THE System SHALL generate a JWT_Token using HS256 algorithm and return it with 24-hour expiration
4. WHEN a user provides invalid login credentials, THE System SHALL reject the authentication and return an error
5. THE System SHALL hash all passwords using bcrypt with a cost factor of 12 before storage
6. WHEN a JWT_Token is presented in the Authorization header (Bearer scheme), THE System SHALL validate the token signature and expiration before granting access
7. THE System SHALL include the user_id in the JWT_Token payload for identity verification
8. WHEN a JWT_Token expires, THE System SHALL reject requests and return HTTP 401 with an appropriate message
9. WHEN a user authenticates via Google OAuth, THE System SHALL validate the Google ID token using Google's token verification endpoint
10. WHEN a valid Google ID token is received for a new user, THE System SHALL create a user account with OAuth provider information
11. WHEN a valid Google ID token is received for an existing user, THE System SHALL return a JWT_Token for that user
12. THE System SHALL store the OAuth provider type (google) and provider user ID for OAuth users
13. WHEN an OAuth user is created, THE System SHALL mark the password field as nullable
14. THE System SHALL expose POST /api/v1/auth/register for email/password registration
15. THE System SHALL expose POST /api/v1/auth/login for email/password authentication
16. THE System SHALL expose POST /api/v1/auth/google for Google OAuth authentication

### Requirement 2: Project Structure and Configuration

**User Story:** As a developer, I want a well-organized project structure with proper configuration management, so that the codebase is maintainable and follows best practices.

#### Acceptance Criteria

1. THE System SHALL organize code following the layered architecture pattern (api, models, schemas, services, core, db)
2. THE System SHALL create an app/api/v1/endpoints/ directory for REST endpoint modules
3. THE System SHALL create an app/models/ directory for SQLAlchemy ORM models
4. THE System SHALL create an app/schemas/ directory for Pydantic validation schemas
5. THE System SHALL create an app/services/ directory for business logic services
6. THE System SHALL create an app/core/ directory for security, cache, and configuration utilities
7. THE System SHALL create an app/db/ directory for database session management and migrations
8. THE System SHALL use Pydantic BaseSettings for environment configuration management
9. THE System SHALL load configuration from .env file or environment variables
10. THE System SHALL define configuration for database URL, JWT secret, JWT algorithm, and token expiration
11. THE System SHALL define configuration for Google OAuth client ID and client secret
12. THE System SHALL create a requirements.txt file with all necessary dependencies and their versions
13. THE System SHALL include FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, python-jose, bcrypt, and asyncpg in dependencies

### Requirement 3: Database Schema Implementation

**User Story:** As a system architect, I want a normalized database schema with proper relationships, so that data integrity is maintained and queries are efficient.

#### Acceptance Criteria

1. THE System SHALL implement all 12 core entity tables in Third Normal Form (3NF)
2. WHEN creating any record, THE System SHALL automatically set created_at to the current UTC timestamp
3. WHEN updating any record, THE System SHALL automatically set updated_at to the current UTC timestamp
4. THE System SHALL use UUID primary keys for all entity tables
5. THE System SHALL enforce foreign key constraints between related entities
6. WHEN a record is deleted, THE System SHALL perform a soft delete by setting deleted_at timestamp
7. THE System SHALL use JSONB columns for flexible preference storage where appropriate
8. THE System SHALL define enum tables for type-safe categorical data

### Requirement 4: Onboarding Flow Management

**User Story:** As a new user, I want to complete a structured onboarding process, so that the system understands my fitness level, goals, and preferences.

#### Acceptance Criteria

1. WHEN a new user is created, THE System SHALL initialize an Onboarding_State at step 0
2. WHEN onboarding data is submitted for a step, THE System SHALL validate the data against step-specific requirements
3. WHEN valid onboarding data is submitted, THE System SHALL save the data and advance the Onboarding_State to the next step
4. WHEN invalid onboarding data is submitted, THE System SHALL reject the submission and return validation errors
5. THE System SHALL track onboarding progress from step 0 through step 11 (12 total steps)
6. WHEN all onboarding steps are completed, THE System SHALL mark the onboarding as complete
7. THE System SHALL allow users to retrieve their current Onboarding_State at any time

### Requirement 5: User Profile Management

**User Story:** As a user, I want my fitness configuration stored in a single profile, so that all system components use consistent data about my preferences.

#### Acceptance Criteria

1. WHEN onboarding is completed, THE System SHALL create a User_Profile containing all configuration data
2. THE System SHALL maintain exactly one active User_Profile per user
3. WHEN a User_Profile is created or modified, THE System SHALL create a Profile_Version record for audit purposes
4. WHEN a user requests their profile, THE System SHALL return the profile data within 100ms
5. THE System SHALL include all related entities (goals, constraints, preferences, schedules) in profile responses
6. WHEN a User_Profile does not exist, THE System SHALL return a descriptive error

### Requirement 6: Profile Locking Mechanism

**User Story:** As a user, I want my fitness plan to remain stable unless I explicitly request changes, so that I have consistency in my training program.

#### Acceptance Criteria

1. WHEN onboarding is completed, THE System SHALL lock the User_Profile by setting is_locked to true
2. WHEN a locked User_Profile modification is requested without explicit unlock, THE System SHALL reject the modification
3. WHEN a user explicitly requests to modify a locked profile, THE System SHALL allow the modification and create a new Profile_Version
4. THE System SHALL record the reason for profile modifications in the Profile_Version
5. WHEN a profile is modified, THE System SHALL maintain the locked status unless explicitly changed

### Requirement 7: Fitness Goals Configuration

**User Story:** As a user, I want to define my fitness goals with specific targets, so that the system can tailor recommendations to my objectives.

#### Acceptance Criteria

1. WHEN a user defines a Fitness_Goal, THE System SHALL require a goal type (fat_loss, muscle_gain, general_fitness)
2. WHEN a user defines a Fitness_Goal, THE System SHALL optionally accept quantifiable targets (target weight, target body fat percentage)
3. THE System SHALL associate Fitness_Goals with the user's User_Profile
4. WHEN a user has multiple goals, THE System SHALL maintain all goals with their priorities
5. THE System SHALL validate that target values are within reasonable ranges

### Requirement 8: Physical Constraints Management

**User Story:** As a user, I want to specify my physical limitations and available equipment, so that workout recommendations are safe and practical.

#### Acceptance Criteria

1. WHEN a user specifies Physical_Constraints, THE System SHALL accept equipment availability information
2. WHEN a user specifies Physical_Constraints, THE System SHALL accept injury or limitation descriptions
3. THE System SHALL store Physical_Constraints as structured data with categories
4. THE System SHALL associate Physical_Constraints with the user's User_Profile
5. WHEN Physical_Constraints are updated, THE System SHALL create a new Profile_Version

### Requirement 9: Dietary Preferences Configuration

**User Story:** As a user, I want to specify my dietary preferences and restrictions, so that meal recommendations align with my eating habits and health needs.

#### Acceptance Criteria

1. WHEN a user specifies Dietary_Preferences, THE System SHALL require a diet type (omnivore, vegetarian, vegan, pescatarian, keto, paleo)
2. WHEN a user specifies Dietary_Preferences, THE System SHALL accept food allergies and intolerances
3. WHEN a user specifies Dietary_Preferences, THE System SHALL accept food dislikes
4. THE System SHALL store dietary restrictions as structured lists
5. THE System SHALL associate Dietary_Preferences with the user's User_Profile

### Requirement 10: Meal Planning Configuration

**User Story:** As a user, I want to define my daily nutritional targets and meal timing, so that the system can provide appropriate meal recommendations.

#### Acceptance Criteria

1. WHEN a user creates a Meal_Plan, THE System SHALL require daily caloric target
2. WHEN a user creates a Meal_Plan, THE System SHALL require macronutrient distribution (protein, carbs, fats percentages)
3. WHEN a user creates a Meal_Plan, THE System SHALL validate that macronutrient percentages sum to 100
4. WHEN a user creates a Meal_Schedule, THE System SHALL accept meal times and notification preferences
5. THE System SHALL associate Meal_Plans and Meal_Schedules with the user's User_Profile

### Requirement 11: Workout Schedule Configuration

**User Story:** As a user, I want to define when I plan to work out, so that the system can send timely reminders and track my adherence.

#### Acceptance Criteria

1. WHEN a user creates a Workout_Schedule, THE System SHALL accept days of the week for workouts
2. WHEN a user creates a Workout_Schedule, THE System SHALL accept preferred workout times
3. WHEN a user creates a Workout_Schedule, THE System SHALL accept notification preferences
4. THE System SHALL validate that workout times are valid time values
5. THE System SHALL associate Workout_Schedules with the user's User_Profile

### Requirement 12: Hydration and Lifestyle Tracking

**User Story:** As a user, I want to configure hydration reminders and track my lifestyle baselines, so that the system understands my overall wellness context.

#### Acceptance Criteria

1. WHEN a user creates Hydration_Preferences, THE System SHALL accept daily water intake targets
2. WHEN a user creates Hydration_Preferences, THE System SHALL accept reminder frequency preferences
3. WHEN a user creates Lifestyle_Baselines, THE System SHALL accept energy level ratings (1-10 scale)
4. WHEN a user creates Lifestyle_Baselines, THE System SHALL accept stress level ratings (1-10 scale)
5. WHEN a user creates Lifestyle_Baselines, THE System SHALL accept sleep quality ratings (1-10 scale)
6. THE System SHALL associate Hydration_Preferences and Lifestyle_Baselines with the user's User_Profile

### Requirement 13: API Response Performance

**User Story:** As a user, I want fast API responses, so that the application feels responsive and smooth.

#### Acceptance Criteria

1. WHEN a user requests their User_Profile, THE System SHALL respond within 100ms under normal load
2. WHEN a user submits onboarding data, THE System SHALL respond within 200ms under normal load
3. WHEN a user authenticates, THE System SHALL respond within 150ms under normal load
4. THE System SHALL use database indexes on frequently queried columns
5. THE System SHALL use async database operations for all I/O

### Requirement 14: Data Validation and Error Handling

**User Story:** As a user, I want clear error messages when I submit invalid data, so that I can correct my input and proceed.

#### Acceptance Criteria

1. WHEN invalid data is submitted to any endpoint, THE System SHALL return HTTP 422 with detailed validation errors
2. WHEN a resource is not found, THE System SHALL return HTTP 404 with a descriptive message
3. WHEN authentication fails, THE System SHALL return HTTP 401 with an appropriate message
4. WHEN authorization fails, THE System SHALL return HTTP 403 with an appropriate message
5. WHEN a server error occurs, THE System SHALL return HTTP 500 and log the error details
6. THE System SHALL validate all input data using Pydantic schemas before processing

### Requirement 15: Database Migrations

**User Story:** As a developer, I want automated database migrations, so that schema changes can be applied consistently across environments.

#### Acceptance Criteria

1. THE System SHALL use Alembic for database migration management
2. WHEN a schema change is made, THE System SHALL generate a migration file with upgrade and downgrade functions
3. WHEN migrations are applied, THE System SHALL track applied migrations in the alembic_version table
4. THE System SHALL support rolling back migrations to previous versions
5. THE System SHALL validate migration integrity before applying changes

### Requirement 16: GDPR Compliance and Data Privacy

**User Story:** As a user, I want my personal data handled securely and in compliance with privacy regulations, so that my information is protected.

#### Acceptance Criteria

1. THE System SHALL use soft deletes for all user data (deleted_at timestamp)
2. WHEN a user requests data deletion, THE System SHALL mark all related records as deleted
3. THE System SHALL exclude soft-deleted records from all queries by default
4. THE System SHALL store all timestamps in UTC format
5. THE System SHALL not log sensitive information (passwords, tokens) in application logs
6. THE System SHALL use secure password hashing (bcrypt with appropriate cost factor)
