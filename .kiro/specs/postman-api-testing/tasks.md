# Implementation Plan: Postman API Testing Framework

## Overview

This implementation plan creates a comprehensive end-to-end API testing framework for the Shuren fitness application backend using Postman. The framework will validate all 8 major API endpoint groups (Authentication, Onboarding, Profiles, Workouts, Meals, Dishes, Meal Templates, Shopping List, Chat) through organized collections, reusable scripts, and automated test execution via the Postman Power integration.

The implementation follows a structured approach:
1. Set up Postman workspace and environments
2. Create collection structure with folders
3. Implement authentication flow tests
4. Build onboarding flow tests
5. Add profile management tests
6. Implement workout and meal plan tests
7. Add dish search and meal template tests
8. Create shopping list and chat tests
9. Add validation and error handling tests
10. Implement end-to-end journey tests
11. Configure collection runner and automation

## Tasks

- [x] 1. Set up Postman workspace and environment configuration
  - Activate Postman Power via Kiro
  - Create "Shuren API Testing" workspace
  - Create three environments (Development, Staging, Production)
  - Define environment variables: base_url, api_base, jwt_token, user_id, test_email, test_password, profile_id, onboarding_step, workout_plan_id, meal_plan_id, meal_template_id, chat_session_id, dish_id
  - Set Development base_url to http://localhost:8000
  - Set Staging base_url to https://staging-api.shuren.app
  - Set Production base_url to https://api.shuren.app
  - _Requirements: 1.1, 1.2, 1.4, 1.5_

- [x] 2. Create main collection with folder structure
  - [x] 2.1 Create "Shuren Backend API - E2E Tests" collection
    - Set collection-level variables: api_version="v1", timeout_ms=5000, test_user_prefix="test_"
    - Add collection-level pre-request script for authentication header setup
    - Add collection-level test script for common validations (response time, valid JSON)
    - _Requirements: 1.2, 12.1, 12.2, 12.3_

  - [x] 2.2 Create folder hierarchy
    - Create folder "01 - Authentication"
    - Create folder "02 - Onboarding"
    - Create folder "03 - Profiles"
    - Create folder "04 - Workouts"
    - Create folder "05 - Meals"
    - Create folder "06 - Dishes"
    - Create folder "07 - Meal Templates"
    - Create folder "08 - Shopping List"
    - Create folder "09 - Chat"
    - _Requirements: 1.3_

- [x] 3. Implement authentication flow tests
  - [x] 3.1 Create user registration requests
    - Add "Register New User" request (POST /api/v1/auth/register)
    - Add pre-request script to generate unique test email and password
    - Add test script to validate 201 status, response schema, and extract user_id
    - Add "Register Duplicate Email" request with existing email
    - Add test script to validate 400 status and error message
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Create login requests
    - Add "Login with Valid Credentials" request (POST /api/v1/auth/login)
    - Add test script to validate 200 status, JWT token presence, and extract jwt_token to environment
    - Add "Login with Invalid Credentials" request with wrong password
    - Add test script to validate 401 status and error message
    - _Requirements: 2.3, 2.4_

  - [x] 3.3 Create OAuth authentication request
    - Add "Google OAuth Login" request (POST /api/v1/auth/oauth/google)
    - Add pre-request script to set mock OAuth token
    - Add test script to validate 200 status and JWT token extraction
    - _Requirements: 2.5_

  - [x] 3.4 Create protected endpoint validation requests
    - Add "Get Current User (Authenticated)" request (GET /api/v1/auth/me)
    - Add test script to validate 200 status and user information
    - Add "Get Current User (No Token)" request without Authorization header
    - Add test script to validate 401 status
    - Add "Get Current User (Expired Token)" request with expired token
    - Add test script to validate 401 status
    - _Requirements: 2.6, 2.7, 2.8_

- [x] 4. Implement onboarding flow tests
  - [x] 4.1 Create onboarding state requests
    - Add "Get Onboarding State" request (GET /api/v1/onboarding/state)
    - Add test script to validate 200 status, current_step field, and step_data structure
    - _Requirements: 3.1_

  - [x] 4.2 Create step submission requests for all 11 steps
    - Add "Submit Step 1 - Basic Info" request (POST /api/v1/onboarding/step)
    - Add pre-request script to generate valid step 1 payload (age, gender)
    - Add test script to validate 200 status and saved data
    - Add "Submit Step 2 - Physical Stats" request with weight and height
    - Add "Submit Step 3 - Fitness Level" request
    - Add "Submit Step 4 - Goals" request
    - Add "Submit Step 5 - Workout Schedule" request
    - Add "Submit Step 6 - Equipment" request
    - Add "Submit Step 7 - Dietary Preferences" request
    - Add "Submit Step 8 - Meal Schedule" request
    - Add "Submit Step 9 - Restrictions" request
    - Add "Submit Step 10 - Lifestyle" request
    - Add "Submit Step 11 - Notifications" request
    - _Requirements: 3.2_

  - [x] 4.3 Create validation error requests
    - Add "Submit Invalid Step" request with missing required fields
    - Add test script to validate 422 status and field errors
    - Add "Submit Step with Wrong Data Types" request
    - Add test script to validate 422 status and type errors
    - _Requirements: 3.3_

  - [x] 4.4 Create out-of-sequence step request
    - Add "Submit Step 10 Before Step 5" request
    - Add test script to validate 200 status (should succeed)
    - _Requirements: 3.4_

  - [x] 4.5 Create onboarding completion requests
    - Add "Complete Onboarding (All Steps Done)" request (POST /api/v1/onboarding/complete)
    - Add test script to validate 200 status and profile creation
    - Add test script to extract profile_id to environment
    - Add "Complete Onboarding (Incomplete Data)" request with missing steps
    - Add test script to validate 400 status and missing fields list
    - _Requirements: 3.5, 3.6_

  - [x] 4.6 Create post-completion validation request
    - Add "Submit Step After Completion" request
    - Add test script to validate rejection with appropriate error
    - _Requirements: 3.7_

- [x] 5. Implement profile management tests
  - [x] 5.1 Create profile retrieval requests
    - Add "Get User Profile" request (GET /api/v1/profiles/me)
    - Add test script to validate 200 status and complete profile structure (goals, constraints, preferences, schedules)
    - Add "Get Non-Existent Profile" request with invalid user_id
    - Add test script to validate 404 status
    - _Requirements: 4.1, 4.6_

  - [x] 5.2 Create profile update requests
    - Add "Update Profile (Valid Data)" request (PUT /api/v1/profiles/me)
    - Add pre-request script to generate valid profile update payload
    - Add test script to validate 200 status, updated data, and version increment
    - Add "Update Profile (Invalid Data)" request with validation errors
    - Add test script to validate 422 status and field errors
    - _Requirements: 4.2, 4.3_

  - [x] 5.3 Create profile locking requests
    - Add "Lock Profile" request (POST /api/v1/profiles/me/lock)
    - Add test script to validate 200 status and is_locked=true
    - Add "Update Locked Profile" request
    - Add test script to validate 403 status and lock error message
    - _Requirements: 4.4, 4.5_

- [x] 6. Implement workout plan tests
  - [x] 6.1 Create workout plan retrieval requests
    - Add "Get Complete Workout Plan" request (GET /api/v1/workouts/plan)
    - Add test script to validate 200 status and all workout days with exercises
    - Add "Get Specific Workout Day" request (GET /api/v1/workouts/plan/day/1)
    - Add test script to validate 200 status and single day data
    - Add "Get Today's Workout" request (GET /api/v1/workouts/today)
    - Add test script to validate 200 status and current day match
    - Add "Get Week's Workouts" request (GET /api/v1/workouts/week)
    - Add test script to validate 200 status and 7 days of data
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 6.2 Create workout plan update requests
    - Add "Update Workout Plan" request (PUT /api/v1/workouts/plan)
    - Add pre-request script to generate valid workout plan update
    - Add test script to validate 200 status and updated plan
    - _Requirements: 5.5_

  - [x] 6.3 Create workout schedule requests
    - Add "Get Workout Schedule" request (GET /api/v1/workouts/schedule)
    - Add test script to validate 200 status and scheduled days/times
    - Add "Update Workout Schedule" request (PUT /api/v1/workouts/schedule)
    - Add test script to validate 200 status and updated schedule
    - _Requirements: 5.6, 5.7_

  - [x] 6.4 Create workout error request
    - Add "Get Workout Without Profile" request for user without profile
    - Add test script to validate 404 status
    - _Requirements: 5.8_

- [x] 7. Implement meal plan tests
  - [x] 7.1 Create meal plan retrieval requests
    - Add "Get Meal Plan" request (GET /api/v1/meals/plan)
    - Add test script to validate 200 status and nutritional structure (calories, protein, carbs, fats)
    - Add "Get Meal Plan Without Profile" request
    - Add test script to validate 404 status
    - _Requirements: 6.1, 6.7_

  - [x] 7.2 Create meal plan update request
    - Add "Update Meal Plan" request (PUT /api/v1/meals/plan)
    - Add pre-request script to generate valid meal plan update
    - Add test script to validate 200 status and updated plan
    - _Requirements: 6.2_

  - [x] 7.3 Create meal schedule requests
    - Add "Get Meal Schedule" request (GET /api/v1/meals/schedule)
    - Add test script to validate 200 status and all meal times
    - Add "Update Meal Schedule" request (PUT /api/v1/meals/schedule)
    - Add test script to validate 200 status and updated schedule
    - _Requirements: 6.3, 6.4_

  - [x] 7.4 Create today's meals and next meal requests
    - Add "Get Today's Meals" request (GET /api/v1/meals/today)
    - Add test script to validate 200 status and current date match
    - Add "Get Next Meal" request (GET /api/v1/meals/next)
    - Add test script to validate 200 status and upcoming meal based on time
    - _Requirements: 6.5, 6.6_

- [x] 8. Implement dish search and details tests
  - [x] 8.1 Create dish search requests
    - Add "Search All Dishes" request (GET /api/v1/dishes)
    - Add test script to validate 200 status and paginated results
    - Add "Search Dishes by Meal Type" request with meal_type query parameter
    - Add test script to validate 200 status and filtered results matching meal_type
    - Add "Search Dishes by Diet Type" request with diet_type query parameter
    - Add test script to validate 200 status and compatible dishes only
    - Add "Search Dishes Excluding Ingredients" request with excluded_ingredients parameter
    - Add test script to validate 200 status and dishes without excluded ingredients
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 8.2 Create dish details requests
    - Add "Get Dish Details" request (GET /api/v1/dishes/{dish_id})
    - Add test script to validate 200 status and complete dish with ingredients
    - Add "Get Non-Existent Dish" request with invalid dish_id
    - Add test script to validate 404 status
    - _Requirements: 7.5, 7.6_

  - [x] 8.3 Create pagination validation request
    - Add "Search Dishes with Pagination" request with page and page_size parameters
    - Add test script to validate pagination metadata (total, page, page_size)
    - _Requirements: 7.7_

- [x] 9. Implement meal template tests
  - [x] 9.1 Create meal template retrieval requests
    - Add "Get Today's Meal Template" request (GET /api/v1/meal-templates/today)
    - Add test script to validate 200 status and meals with dish recommendations for current date
    - Add "Get Next Meal Template" request (GET /api/v1/meal-templates/next)
    - Add test script to validate 200 status and upcoming meal with dishes
    - Add "Get Week's Meal Template" request (GET /api/v1/meal-templates/week)
    - Add test script to validate 200 status and 7 days of meals
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 9.2 Create meal template regeneration request
    - Add "Regenerate Meal Template" request (POST /api/v1/meal-templates/regenerate)
    - Add test script to validate 200 status and new template creation
    - _Requirements: 8.4_

  - [x] 9.3 Create meal template error request
    - Add "Get Meal Template Without Plan" request for user without meal plan
    - Add test script to validate 404 status
    - _Requirements: 8.5_

  - [x] 9.4 Create dietary preference validation tests
    - Add test script to "Get Today's Meal Template" to validate dishes respect diet_type
    - Add test script to validate dishes match meal_type (breakfast, lunch, dinner, snack)
    - Add test script to validate no excluded ingredients in recommended dishes
    - _Requirements: 8.6, 8.7_

- [x] 10. Implement shopping list tests
  - [x] 10.1 Create shopping list request
    - Add "Get Shopping List" request (GET /api/v1/shopping-list)
    - Add test script to validate 200 status and aggregated ingredients
    - Add test script to validate ingredients grouped by category
    - Add test script to validate quantities summed for duplicates
    - Add test script to validate each ingredient has name, quantity, and unit
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

  - [x] 10.2 Create shopping list error request
    - Add "Get Shopping List Without Template" request for user without meal template
    - Add test script to validate 404 status
    - _Requirements: 9.4_

- [x] 11. Implement chat interaction tests
  - [x] 11.1 Create chat session requests
    - Add "Start Chat Session" request (POST /api/v1/chat/sessions)
    - Add test script to validate 200 status and extract session_id to environment
    - Add "End Chat Session" request (POST /api/v1/chat/sessions/{session_id}/end)
    - Add test script to validate 200 status and session marked inactive
    - _Requirements: 10.2, 10.4_

  - [x] 11.2 Create chat message requests
    - Add "Send Chat Message" request (POST /api/v1/chat/sessions/{session_id}/messages)
    - Add pre-request script to generate chat message payload
    - Add test script to validate 200 status and agent response
    - Add "Send Chat Message (Unauthenticated)" request without JWT token
    - Add test script to validate 401 status
    - _Requirements: 10.1, 10.5_

  - [x] 11.3 Create chat history request
    - Add "Get Chat History" request (GET /api/v1/chat/sessions/{session_id}/messages)
    - Add test script to validate 200 status and paginated message history
    - Add "Get Chat History with Pagination" request with page parameter
    - Add test script to validate correct page of messages
    - _Requirements: 10.3, 10.6_

- [x] 12. Implement data validation tests
  - [x] 12.1 Create validation error test requests
    - Add "Request with Missing Required Fields" request to any endpoint
    - Add test script to validate 422 status and field errors
    - Add "Request with Invalid Data Types" request
    - Add test script to validate 422 status and type errors
    - Add "Request with Out-of-Range Values" request
    - Add test script to validate 422 status and constraint errors
    - Add "Request with Invalid String Patterns" request (invalid email, UUID)
    - Add test script to validate 422 status and pattern errors
    - Add "Request with Invalid Enum Values" request
    - Add test script to validate 422 status and enum errors
    - _Requirements: 11.1, 11.2, 11.4, 11.5, 11.6_

  - [x] 12.2 Create response schema validation tests
    - Add test scripts to all successful requests to validate response schema structure
    - Use pm.response.to.have.jsonSchema() for schema validation
    - _Requirements: 11.3_

  - [x] 12.3 Create date/time format validation test
    - Add test script to validate ISO 8601 format for all date/time fields
    - _Requirements: 11.7_

- [x] 13. Implement error handling tests
  - [x] 13.1 Create comprehensive error response tests
    - Add folder-level test script to validate error response structure (detail, status_code, errors)
    - Add test scripts to validate 401 errors for authentication failures
    - Add test scripts to validate 403 errors for authorization failures
    - Add test scripts to validate 404 errors for resource not found
    - Add test scripts to validate 422 errors for validation failures
    - Add test scripts to validate 500 errors for server errors (if testable)
    - Add test scripts to validate 503 errors for service unavailability (if testable)
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

- [x] 14. Implement end-to-end journey tests
  - [x] 14.1 Create new user journey test sequence
    - Create folder "E2E - New User Journey"
    - Add requests in sequence: Register → Login → Onboarding Steps 1-11 → Complete Onboarding → Get Profile
    - Add test scripts to validate data consistency across all steps
    - _Requirements: 14.1_

  - [x] 14.2 Create workout journey test sequence
    - Create folder "E2E - Workout Journey"
    - Add requests in sequence: Get Plan → Get Today's Workout → Update Schedule
    - Add test scripts to validate data consistency
    - _Requirements: 14.2_

  - [x] 14.3 Create meal journey test sequence
    - Create folder "E2E - Meal Journey"
    - Add requests in sequence: Get Plan → Get Meal Template → Get Shopping List
    - Add test scripts to validate data consistency
    - _Requirements: 14.3_

  - [x] 14.4 Create chat journey test sequence
    - Create folder "E2E - Chat Journey"
    - Add requests in sequence: Start Session → Send Messages → Get History → End Session
    - Add test scripts to validate data consistency
    - _Requirements: 14.4_

  - [x] 14.5 Create profile update journey test sequence
    - Create folder "E2E - Profile Update Journey"
    - Add requests in sequence: Get Profile → Update Profile → Verify Version Increment
    - Add test scripts to validate data consistency
    - _Requirements: 14.5_

- [x] 15. Implement performance validation tests
  - [x] 15.1 Add performance test scripts to key endpoints
    - Add test script to profile requests to validate response time < 100ms
    - Add test script to onboarding step saves to validate response time < 200ms
    - Add test script to workout plan requests to validate response time < 150ms
    - Add test script to meal template requests to validate response time < 300ms
    - Add test script to shopping list requests to validate response time < 200ms
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [x] 15.2 Configure collection runner for performance testing
    - Set collection runner to track total execution time
    - Add validation that full collection run completes within 5 minutes
    - _Requirements: 15.6_

- [x] 16. Configure collection runner and automation
  - [x] 16.1 Configure collection runner settings
    - Set iterations to 1
    - Set delay between requests to 100ms
    - Set bail to false (continue on failure)
    - Configure reporters: cli, json, html
    - Set HTML report export path
    - _Requirements: 12.5, 12.7_

  - [x] 16.2 Create test data cleanup scripts
    - Add collection-level teardown script to clean up test users
    - Add script to delete test profiles
    - Add script to remove test chat sessions
    - _Requirements: 12.8_

  - [x] 16.3 Create Postman Power automation script
    - Write script to activate Postman Power via Kiro
    - Add function to import collection to workspace
    - Add function to run collection with specified environment
    - Add function to retrieve and display test results
    - _Requirements: 12.6_

- [x] 17. Final checkpoint - Validate complete testing framework
  - Run complete collection in Development environment
  - Verify all requests execute successfully
  - Verify all test scripts pass
  - Verify test report generation works
  - Verify cleanup scripts remove test data
  - Document any issues or edge cases discovered
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All requests should use environment variables for URLs and dynamic data
- Pre-request scripts should generate unique test data to avoid conflicts
- Test scripts should validate both success and error scenarios
- Each folder should have consistent naming and organization
- Collection runner should execute requests in dependency order
- Performance tests should account for network latency in local vs remote environments
- Cleanup scripts are critical to prevent test data accumulation
- Postman Power integration enables CI/CD automation
