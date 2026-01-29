# Implementation Plan: Phase 1 Foundation

## Overview

This implementation plan breaks down the Phase 1 Foundation into discrete, actionable tasks. The approach follows a bottom-up strategy: starting with core infrastructure (database, configuration, models), then building the service layer, and finally implementing the API endpoints. Each major component includes property-based tests to validate the 27 correctness properties defined in the design document.

The implementation uses FastAPI 0.109+ with Python 3.11+, PostgreSQL 15+, SQLAlchemy 2.0+ (async), and follows the layered architecture pattern defined in the design.

## Tasks

- [x] 1. Set up project structure and core infrastructure
  - Create backend/ directory with app/ subdirectory
  - Create directory structure: api/v1/endpoints/, models/, schemas/, services/, core/, db/, tests/
  - Create __init__.py files in all package directories
  - Create requirements.txt with FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.0+, asyncpg, alembic, python-jose[cryptography], passlib[bcrypt], google-auth
  - Create .env.example with configuration template (DATABASE_URL, JWT_SECRET_KEY, GOOGLE_CLIENT_ID, etc.)
  - Create README.md with setup instructions
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.12, 2.13_

- [x] 2. Implement configuration management
  - [x] 2.1 Create app/core/config.py with Pydantic BaseSettings
    - Define Settings class with all configuration fields (DATABASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_HOURS, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
    - Configure env_file loading from .env
    - Export settings singleton instance
    - _Requirements: 2.8, 2.9, 2.10, 2.11_

  - [ ]* 2.2 Write property test for configuration loading
    - **Property: Configuration Validation**
    - **Validates: Requirements 2.8, 2.9**

- [x] 3. Implement database foundation
  - [x] 3.1 Create app/db/base.py with BaseModel class
    - Define declarative_base() for SQLAlchemy
    - Create BaseModel with id (UUID), created_at, updated_at, deleted_at columns
    - Use server_default=func.now() for created_at, onupdate=func.now() for updated_at
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_

  - [x] 3.2 Create app/db/session.py for async database session management
    - Create async engine with asyncpg driver
    - Create AsyncSessionLocal with async_sessionmaker
    - Implement get_db() dependency function yielding AsyncSession
    - _Requirements: 2.1, 13.5_

  - [ ]* 3.3 Write property test for automatic timestamp management
    - **Property 6: Automatic Timestamp Management**
    - **Validates: Requirements 3.2, 3.3**

  - [ ]* 3.4 Write property test for UUID primary keys
    - **Property 7: UUID Primary Keys**
    - **Validates: Requirements 3.4**

  - [ ]* 3.5 Write property test for soft delete behavior
    - **Property 8: Soft Delete Behavior**
    - **Validates: Requirements 3.6, 16.3**

- [x] 4. Implement database models
  - [x] 4.1 Create app/models/user.py with User model
    - Define users table with email, hashed_password, full_name, oauth_provider, oauth_provider_user_id, is_active
    - Add unique constraint on email
    - Add unique constraint on (oauth_provider, oauth_provider_user_id)
    - Create indexes on email and oauth fields
    - Define relationships to onboarding_state and profile
    - _Requirements: 1.1, 1.5, 1.9, 1.12, 1.13, 3.1, 3.5_

  - [x] 4.2 Create app/models/onboarding.py with OnboardingState model
    - Define onboarding_states table with user_id, current_step, is_complete, step_data (JSONB)
    - Add unique constraint on user_id
    - Add foreign key to users table
    - Define relationship to user
    - _Requirements: 4.1, 4.5, 3.1, 3.7_

  - [x] 4.3 Create app/models/profile.py with UserProfile and UserProfileVersion models
    - Define user_profiles table with user_id, is_locked, fitness_level
    - Add unique constraint on user_id
    - Define user_profile_versions table with profile_id, version_number, change_reason, snapshot (JSONB)
    - Add index on (profile_id, version_number)
    - Define relationships to all preference entities
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 3.1_

  - [x] 4.4 Create app/models/preferences.py with all preference models
    - Define FitnessGoal model (profile_id, goal_type, target_weight_kg, target_body_fat_percentage, priority)
    - Define PhysicalConstraint model (profile_id, constraint_type, description, severity)
    - Define DietaryPreference model (profile_id, diet_type, allergies, intolerances, dislikes as ARRAY)
    - Define MealPlan model (profile_id, daily_calorie_target, protein_percentage, carbs_percentage, fats_percentage) with CHECK constraint
    - Define MealSchedule model (profile_id, meal_name, scheduled_time, enable_notifications)
    - Define WorkoutSchedule model (profile_id, day_of_week, scheduled_time, enable_notifications)
    - Define HydrationPreference model (profile_id, daily_water_target_ml, reminder_frequency_minutes, enable_notifications)
    - Define LifestyleBaseline model (profile_id, energy_level, stress_level, sleep_quality) with CHECK constraints
    - Add appropriate indexes and relationships
    - _Requirements: 7.1, 7.2, 8.1, 8.2, 9.1, 9.2, 9.3, 10.1, 10.2, 10.4, 11.1, 11.2, 11.3, 12.1, 12.2, 12.3, 12.4, 12.5, 3.1, 3.7, 3.8_

  - [ ]* 4.5 Write property test for single active profile per user
    - **Property 12: Single Active Profile Per User**
    - **Validates: Requirements 5.2**

- [x] 5. Set up Alembic for database migrations
  - [x] 5.1 Initialize Alembic in backend/ directory
    - Run alembic init alembic
    - Configure alembic.ini with database URL from settings
    - Update alembic/env.py to import Base and use async engine
    - _Requirements: 15.1_

  - [x] 5.2 Create initial migration for all tables
    - Generate migration with alembic revision --autogenerate -m "Initial schema"
    - Review and adjust migration file
    - Test upgrade and downgrade functions
    - _Requirements: 15.2, 15.3, 15.4_

  - [ ]* 5.3 Write unit tests for migration integrity
    - Test that migrations can be applied and rolled back
    - Test that schema matches model definitions
    - _Requirements: 15.5_

- [x] 6. Implement authentication and security utilities
  - [x] 6.1 Create app/core/security.py with password and JWT functions
    - Implement hash_password() using passlib with bcrypt (cost factor 12)
    - Implement verify_password() for password verification
    - Implement create_access_token() generating JWT with HS256, user_id payload, 24-hour expiration
    - Implement decode_access_token() for JWT validation
    - Implement verify_google_token() using google-auth library
    - _Requirements: 1.3, 1.5, 1.6, 1.7, 1.9_

  - [ ]* 6.2 Write property test for password hashing security
    - **Property 2: Password Hashing Security**
    - **Validates: Requirements 1.5**

  - [ ]* 6.3 Write property test for JWT token structure and validity
    - **Property 3: JWT Token Structure and Validity**
    - **Validates: Requirements 1.3, 1.6, 1.7**

  - [ ]* 6.4 Write property test for sensitive data protection
    - **Property 27: Sensitive Data Protection**
    - **Validates: Requirements 16.5**

- [x] 7. Implement authentication dependencies
  - [x] 7.1 Create app/core/deps.py with FastAPI dependencies
    - Implement get_current_user() dependency using HTTPBearer
    - Extract token from Authorization header
    - Decode JWT and validate expiration
    - Fetch user from database by user_id
    - Check for soft-deleted users
    - Raise HTTPException(401) for invalid tokens or missing users
    - _Requirements: 1.6, 1.8_

  - [ ]* 7.2 Write property test for token authentication
    - **Property 4: Token Authentication**
    - **Validates: Requirements 1.6**

  - [ ]* 7.3 Write property test for authentication error responses
    - **Property 23: Authentication Error Responses**
    - **Validates: Requirements 14.3, 1.8**

- [x] 8. Implement Pydantic schemas
  - [x] 8.1 Create app/schemas/auth.py with authentication schemas
    - Define UserRegister (email, password min 8 chars, full_name)
    - Define UserLogin (email, password)
    - Define GoogleAuthRequest (id_token)
    - Define TokenResponse (access_token, token_type, user_id)
    - Define UserResponse (id, email, full_name, oauth_provider, is_active, created_at)
    - _Requirements: 1.14, 1.15, 1.16_

  - [x] 8.2 Create app/schemas/onboarding.py with onboarding schemas
    - Define OnboardingStateResponse (id, user_id, current_step, is_complete, step_data)
    - Define OnboardingStepRequest (step, data)
    - Define OnboardingStepResponse (current_step, is_complete, message)
    - _Requirements: 4.7_

  - [x] 8.3 Create app/schemas/profile.py with profile schemas
    - Define FitnessGoalSchema, PhysicalConstraintSchema, DietaryPreferenceSchema
    - Define MealPlanSchema with macro percentage validation
    - Define MealScheduleSchema, WorkoutScheduleSchema with time fields
    - Define HydrationPreferenceSchema, LifestyleBaselineSchema with range validation (1-10)
    - Define UserProfileResponse with all nested schemas
    - Define ProfileUpdateRequest (reason, updates)
    - _Requirements: 5.5, 7.1, 7.2, 8.1, 8.2, 9.1, 9.2, 10.1, 10.2, 10.4, 11.1, 11.2, 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ]* 8.4 Write property test for validation error responses
    - **Property 21: Validation Error Responses**
    - **Validates: Requirements 14.1, 14.6**

- [x] 9. Implement onboarding service
  - [x] 9.1 Create app/services/onboarding_service.py with OnboardingService class
    - Implement __init__(db: AsyncSession)
    - Implement get_onboarding_state(user_id) returning OnboardingState
    - Implement save_onboarding_step(user_id, step, data) with step-specific validation
    - Implement step validation logic for steps 1-11 (age ranges, fitness levels, goal types, macro sums, etc.)
    - Advance current_step on successful validation
    - Store step data in step_data JSONB field
    - _Requirements: 4.2, 4.3, 4.4, 4.7_

  - [x] 9.2 Implement complete_onboarding(user_id) method
    - Verify all 11 steps are complete
    - Create UserProfile from onboarding step_data
    - Set is_locked=True on profile
    - Create all related entities (goals, constraints, preferences, schedules)
    - Create initial ProfileVersion with reason="Onboarding completed"
    - Mark onboarding_state as is_complete=True
    - Use database transaction for atomicity
    - _Requirements: 4.6, 5.1, 6.1_

  - [ ]* 9.3 Write property test for onboarding step validation
    - **Property 9: Onboarding Step Validation**
    - **Validates: Requirements 4.2, 4.4**

  - [ ]* 9.4 Write property test for onboarding step progression
    - **Property 10: Onboarding Step Progression**
    - **Validates: Requirements 4.3**

  - [ ]* 9.5 Write property test for onboarding state retrieval
    - **Property 11: Onboarding State Retrieval**
    - **Validates: Requirements 4.7**

- [x] 10. Implement profile service
  - [x] 10.1 Create app/services/profile_service.py with ProfileService class
    - Implement __init__(db: AsyncSession)
    - Implement get_profile(user_id) with eager loading of all relationships
    - Use selectinload() for all related entities to minimize queries
    - Ensure response time < 100ms through proper indexing
    - _Requirements: 5.4, 5.5, 13.1_

  - [x] 10.2 Implement update_profile(user_id, updates, reason) method
    - Check if profile is locked (is_locked=True)
    - If locked and no explicit unlock, raise HTTPException(403)
    - Create ProfileVersion before applying updates
    - Increment version_number, store reason and snapshot
    - Apply updates to profile and related entities
    - Maintain is_locked status unless explicitly changed
    - Use database transaction for atomicity
    - _Requirements: 6.2, 6.3, 6.4, 6.5_

  - [x] 10.3 Implement lock_profile(user_id) method
    - Set is_locked=True on user profile
    - _Requirements: 6.1_

  - [ ]* 10.4 Write property test for profile versioning on modification
    - **Property 13: Profile Versioning on Modification**
    - **Validates: Requirements 5.3, 6.3, 6.4**

  - [ ]* 10.5 Write property test for profile response completeness
    - **Property 14: Profile Response Completeness**
    - **Validates: Requirements 5.5**

  - [ ]* 10.6 Write property test for profile lock enforcement
    - **Property 15: Profile Lock Enforcement**
    - **Validates: Requirements 6.2**

  - [ ]* 10.7 Write property test for profile lock persistence
    - **Property 16: Profile Lock Persistence**
    - **Validates: Requirements 6.5**

- [x] 11. Implement authentication endpoints
  - [x] 11.1 Create app/api/v1/endpoints/auth.py with authentication routes
    - Implement POST /api/v1/auth/register endpoint
    - Check if email already exists, return 400 if duplicate
    - Hash password using hash_password()
    - Create User with hashed_password
    - Create OnboardingState at step 0
    - Generate JWT token with create_access_token()
    - Return 201 with TokenResponse
    - _Requirements: 1.1, 1.2, 1.14_

  - [x] 11.2 Implement POST /api/v1/auth/login endpoint
    - Fetch user by email
    - Verify password using verify_password()
    - Return 401 if credentials invalid
    - Generate JWT token
    - Return 200 with TokenResponse
    - _Requirements: 1.3, 1.4, 1.15_

  - [x] 11.3 Implement POST /api/v1/auth/google endpoint
    - Verify Google ID token using verify_google_token()
    - Extract email, name, sub from token
    - Check if user exists by email or (oauth_provider, oauth_provider_user_id)
    - Create user if new with oauth_provider='google', hashed_password=None
    - Create OnboardingState for new users
    - Generate JWT token
    - Return 200 with TokenResponse
    - _Requirements: 1.9, 1.10, 1.11, 1.12, 1.16_

  - [x] 11.4 Implement GET /api/v1/auth/me endpoint
    - Use get_current_user dependency
    - Return UserResponse with user data
    - _Requirements: 1.6_

  - [ ]* 11.5 Write property test for user registration
    - **Property 1: User Registration Creates Valid Account**
    - **Validates: Requirements 1.1, 4.1**

  - [ ]* 11.6 Write property test for OAuth user creation
    - **Property 5: OAuth User Creation**
    - **Validates: Requirements 1.12, 1.13**

  - [ ]* 11.7 Write unit tests for authentication endpoints
    - Test duplicate email registration returns 400
    - Test invalid login credentials return 401
    - Test expired token returns 401
    - Test /auth/me with valid token returns user data
    - _Requirements: 1.2, 1.4, 1.8_

- [x] 12. Checkpoint - Ensure authentication tests pass
  - Run all authentication-related tests
  - Verify JWT token generation and validation
  - Verify password hashing and verification
  - Verify OAuth flow
  - Ask the user if questions arise

- [x] 13. Implement onboarding endpoints
  - [x] 13.1 Create app/api/v1/endpoints/onboarding.py with onboarding routes
    - Implement GET /api/v1/onboarding/state endpoint
    - Use get_current_user dependency
    - Call onboarding_service.get_onboarding_state()
    - Return 200 with OnboardingStateResponse
    - Return 404 if state not found
    - Ensure response time < 200ms
    - _Requirements: 4.7, 13.2_

  - [x] 13.2 Implement POST /api/v1/onboarding/step endpoint
    - Use get_current_user dependency
    - Validate OnboardingStepRequest
    - Call onboarding_service.save_onboarding_step()
    - Return 200 with OnboardingStepResponse on success
    - Return 400 for invalid step data
    - Return 422 for validation errors
    - Ensure response time < 200ms
    - _Requirements: 4.2, 4.3, 4.4, 13.2_

  - [x] 13.3 Implement POST /api/v1/onboarding/complete endpoint
    - Use get_current_user dependency
    - Call onboarding_service.complete_onboarding()
    - Return 201 with UserProfileResponse
    - Return 400 if onboarding incomplete
    - _Requirements: 4.6, 5.1, 6.1_

  - [ ]* 13.4 Write unit tests for onboarding endpoints
    - Test GET /onboarding/state returns current state
    - Test POST /onboarding/step with valid data advances step
    - Test POST /onboarding/step with invalid data returns 400
    - Test POST /onboarding/complete creates locked profile
    - Test POST /onboarding/complete with incomplete onboarding returns 400
    - _Requirements: 4.2, 4.4, 4.6_

- [x] 14. Implement profile endpoints
  - [x] 14.1 Create app/api/v1/endpoints/profiles.py with profile routes
    - Implement GET /api/v1/profiles/me endpoint
    - Use get_current_user dependency
    - Call profile_service.get_profile()
    - Return 200 with UserProfileResponse
    - Return 404 if profile not found
    - Ensure response time < 100ms
    - _Requirements: 5.4, 5.5, 5.6, 13.1_

  - [x] 14.2 Implement PATCH /api/v1/profiles/me endpoint
    - Use get_current_user dependency
    - Validate ProfileUpdateRequest
    - Call profile_service.update_profile()
    - Return 200 with UserProfileResponse
    - Return 403 if profile locked without unlock
    - Return 422 for validation errors
    - _Requirements: 6.2, 6.3, 6.4, 6.5_

  - [x] 14.3 Implement POST /api/v1/profiles/me/lock endpoint
    - Use get_current_user dependency
    - Call profile_service.lock_profile()
    - Return 200 with UserProfileResponse
    - Return 404 if profile not found
    - _Requirements: 6.1_

  - [ ]* 14.4 Write property test for resource not found responses
    - **Property 22: Resource Not Found Responses**
    - **Validates: Requirements 14.2, 5.6**

  - [ ]* 14.5 Write property test for authorization error responses
    - **Property 24: Authorization Error Responses**
    - **Validates: Requirements 14.4**

  - [ ]* 14.6 Write unit tests for profile endpoints
    - Test GET /profiles/me returns complete profile with all relationships
    - Test PATCH /profiles/me with locked profile returns 403
    - Test PATCH /profiles/me with reason creates new version
    - Test POST /profiles/me/lock sets is_locked=True
    - _Requirements: 5.5, 6.2, 6.3_

- [x] 15. Implement data validation property tests
  - [x]* 15.1 Write property test for meal plan macro validation
    - **Property 17: Meal Plan Macro Validation**
    - **Validates: Requirements 10.3**

  - [x]* 15.2 Write property test for fitness goal target ranges
    - **Property 18: Fitness Goal Target Ranges**
    - **Validates: Requirements 7.5**

  - [x]* 15.3 Write property test for lifestyle rating ranges
    - **Property 19: Lifestyle Rating Ranges**
    - **Validates: Requirements 12.3, 12.4, 12.5**

  - [x]* 15.4 Write property test for workout schedule day validation
    - **Property 20: Workout Schedule Day Validation**
    - **Validates: Requirements 11.4**

- [x] 16. Implement data privacy property tests
  - [x]* 16.1 Write property test for soft delete cascade
    - **Property 25: Soft Delete Cascade**
    - **Validates: Requirements 16.2**

  - [x]* 16.2 Write property test for deleted record exclusion
    - **Property 26: Deleted Record Exclusion**
    - **Validates: Requirements 16.3**

- [x] 17. Create FastAPI application entry point
  - [x] 17.1 Create app/main.py with FastAPI app initialization
    - Create FastAPI app instance with title, version, docs_url
    - Include authentication router with prefix /api/v1/auth
    - Include onboarding router with prefix /api/v1/onboarding
    - Include profiles router with prefix /api/v1/profiles
    - Add CORS middleware for development
    - Add exception handlers for common errors (404, 401, 403, 422, 500)
    - Configure logging
    - _Requirements: 2.1, 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ]* 17.2 Write unit tests for error handlers
    - Test 404 handler returns proper format
    - Test 401 handler returns proper format
    - Test 403 handler returns proper format
    - Test 422 handler returns proper format with field errors
    - Test 500 handler logs error and returns generic message
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 18. Create test configuration and fixtures
  - [x] 18.1 Create tests/conftest.py with pytest fixtures
    - Create test database fixture using pytest-asyncio
    - Create async test client fixture
    - Create authenticated user fixture
    - Create sample onboarding data fixtures
    - Configure test database to use separate schema or database
    - _Requirements: Testing infrastructure_

  - [x] 18.2 Configure pytest.ini with async settings
    - Set asyncio_mode = auto
    - Configure test discovery patterns
    - Set up coverage reporting
    - _Requirements: Testing infrastructure_

- [x] 19. Final checkpoint - Run complete test suite
  - Run all unit tests and property-based tests
  - Verify all 27 correctness properties pass
  - Check test coverage (aim for >80% on core logic)
  - Run alembic migrations on test database
  - Verify API endpoints with manual testing or integration tests
  - Ask the user if questions arise

- [ ] 20. Create deployment documentation
  - [x] 20.1 Update README.md with comprehensive setup instructions
    - Document prerequisites (Python 3.11+, PostgreSQL 15+)
    - Document environment variable configuration
    - Document database setup and migration commands
    - Document how to run the development server
    - Document how to run tests
    - Document API endpoint documentation location (Swagger UI)
    - _Requirements: 2.12_

  - [ ] 20.2 Create docker-compose.yml for local development (optional)
    - Define PostgreSQL service
    - Define backend API service
    - Configure environment variables
    - Set up volume mounts for development
    - _Requirements: Development infrastructure_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and error conditions
- Checkpoints ensure incremental validation at major milestones
- The implementation follows a bottom-up approach: infrastructure → services → API
- All database operations use async/await for optimal performance
- Profile queries must meet <100ms performance target through proper indexing and eager loading
