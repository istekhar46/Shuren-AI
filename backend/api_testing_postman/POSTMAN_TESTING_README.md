# Postman API Testing Framework

Comprehensive end-to-end API testing framework for the Shuren fitness application backend using Postman.

## Overview

This testing framework validates all 8 major API endpoint groups (Authentication, Onboarding, Profiles, Workouts, Meals, Dishes, Meal Templates, Shopping List, Chat) through organized collections, reusable scripts, and automated test execution.

## Files

### Configuration Files

- **`.postman.json`** - Complete Postman collection definition with all requests, folders, and test scripts
- **`.postman-runner-config.json`** - Collection runner configuration (iterations, delays, reporters)
- **`.postman-automation-config.json`** - Saved workspace, collection, and environment IDs (created after setup)
- **`.postman-cleanup-scripts.json`** - Cleanup script templates for test data removal

### Automation Scripts

- **`postman-automation.js`** - Main automation script with step-by-step Kiro Power commands
- **`postman-cleanup.js`** - Standalone cleanup script for removing test data
- **`POSTMAN_AUTOMATION_GUIDE.md`** - Comprehensive guide for using the automation framework
- **`POSTMAN_TESTING_README.md`** - This file

## Quick Start

### 1. Prerequisites

- Postman API key (get from [postman.com](https://postman.com) → Settings → API Keys)
- Kiro with Postman Power installed
- Backend API server running (for local testing)

### 2. Configure API Key

Set your Postman API key as an environment variable:

```bash
# Windows (PowerShell)
$env:POSTMAN_API_KEY="your-api-key-here"

# macOS/Linux
export POSTMAN_API_KEY="your-api-key-here"
```

Or add to Kiro MCP config (`~/.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "postman": {
      "url": "https://mcp.postman.com/minimal",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY_HERE"
      }
    }
  }
}
```

### 3. Run Automation Script

```bash
node postman-automation.js
```

This will display step-by-step Kiro Power commands to:
1. Create workspace
2. Import collection
3. Create environments
4. Run tests
5. Display results

### 4. Follow the Guide

Open `POSTMAN_AUTOMATION_GUIDE.md` for detailed instructions on each step.

## Collection Structure

```
Shuren Backend API - E2E Tests
├── 01 - Authentication
│   ├── Register New User
│   ├── Register Duplicate Email
│   ├── Login with Valid Credentials
│   ├── Login with Invalid Credentials
│   ├── Google OAuth Login
│   ├── Get Current User (Authenticated)
│   ├── Get Current User (No Token)
│   └── Get Current User (Expired Token)
├── 02 - Onboarding
│   ├── Get Onboarding State
│   ├── Submit Step 1-11
│   ├── Submit Invalid Step
│   ├── Complete Onboarding
│   └── Submit Step After Completion
├── 03 - Profiles
│   ├── Get User Profile
│   ├── Update Profile (Valid Data)
│   ├── Update Profile (Invalid Data)
│   ├── Lock Profile
│   └── Update Locked Profile
├── 04 - Workouts
│   ├── Get Complete Workout Plan
│   ├── Get Specific Workout Day
│   ├── Get Today's Workout
│   ├── Get Week's Workouts
│   ├── Update Workout Plan
│   ├── Get Workout Schedule
│   └── Update Workout Schedule
├── 05 - Meals
│   ├── Get Meal Plan
│   ├── Update Meal Plan
│   ├── Get Meal Schedule
│   ├── Update Meal Schedule
│   ├── Get Today's Meals
│   └── Get Next Meal
├── 06 - Dishes
│   ├── Search All Dishes
│   ├── Search Dishes by Meal Type
│   ├── Search Dishes by Diet Type
│   ├── Search Dishes Excluding Ingredients
│   ├── Get Dish Details
│   └── Search Dishes with Pagination
├── 07 - Meal Templates
│   ├── Get Today's Meal Template
│   ├── Get Next Meal Template
│   ├── Get Week's Meal Template
│   └── Regenerate Meal Template
├── 08 - Shopping List
│   └── Get Shopping List
└── 09 - Chat
    ├── Start Chat Session
    ├── End Chat Session
    ├── Send Chat Message
    ├── Send Chat Message (Unauthenticated)
    ├── Get Chat History
    └── Get Chat History with Pagination
```

## Test Coverage

### Functional Tests
- ✅ Authentication flows (registration, login, OAuth)
- ✅ Onboarding process (11 steps + completion)
- ✅ Profile management (CRUD + versioning + locking)
- ✅ Workout plans (retrieval, updates, scheduling)
- ✅ Meal plans (retrieval, updates, scheduling)
- ✅ Dish search and filtering
- ✅ Meal template generation
- ✅ Shopping list aggregation
- ✅ Chat interactions

### Validation Tests
- ✅ Request validation (missing fields, invalid types, constraints)
- ✅ Response schema validation
- ✅ Error handling (401, 403, 404, 422, 500, 503)
- ✅ Date/time format validation (ISO 8601)

### Performance Tests
- ✅ Profile requests < 100ms
- ✅ Onboarding saves < 200ms
- ✅ Workout plans < 150ms
- ✅ Meal templates < 300ms
- ✅ Shopping lists < 200ms
- ✅ Full collection run < 5 minutes

### End-to-End Tests
- ✅ New user journey (register → onboard → profile)
- ✅ Workout journey (plan → today → schedule)
- ✅ Meal journey (plan → template → shopping list)
- ✅ Chat journey (session → messages → history)
- ✅ Profile update journey (get → update → verify)

## Environments

### Development
- Base URL: `http://localhost:8000`
- Use for local testing during development

### Staging
- Base URL: `https://staging-api.shuren.app`
- Use for pre-production testing

### Production
- Base URL: `https://api.shuren.app`
- Use for production validation (with caution)

## Running Tests

### Via Kiro Powers

```javascript
// Run with Development environment
kiroPowers.use({
  powerName: "postman",
  serverName: "postman",
  toolName: "runCollection",
  arguments: {
    collectionId: "<collection-uid>",
    environmentId: "<development-environment-id>",
    iterationCount: 1,
    stopOnError: false,
    stopOnFailure: false
  }
})
```

### Via Automation Script

```bash
# Run with default (Development) environment
node postman-automation.js

# Run with Staging environment
node postman-automation.js --environment Staging

# Run with cleanup
node postman-automation.js --cleanup
```

### Via Newman CLI (Alternative)

```bash
# Install Newman
npm install -g newman

# Run collection
newman run .postman.json \
  -e postman-dev-env.json \
  --delay-request 100 \
  --reporters cli,json,html \
  --reporter-html-export ./test-results/report.html
```

## Test Results

Results include:
- Total requests executed
- Total assertions run
- Failed requests and assertions
- Detailed error messages
- Execution time per request
- Overall collection execution time

Example output:
```
Run Summary:
  Total Requests: 52
  Failed Requests: 0
  Total Assertions: 180
  Failed Assertions: 0
  Total Time: 45.2s
```

## Cleanup

After tests complete, clean up test data:

```bash
node postman-cleanup.js <environment-file> <api-base-url> <jwt-token>
```

This removes:
- Test users created during registration
- Test profiles created during onboarding
- Test chat sessions created during chat tests

## CI/CD Integration

### GitHub Actions Example

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start API Server
        run: docker-compose up -d api
      - name: Wait for API
        run: sleep 10
      - name: Run Postman Tests
        env:
          POSTMAN_API_KEY: ${{ secrets.POSTMAN_API_KEY }}
        run: node postman-automation.js
      - name: Cleanup
        if: always()
        run: node postman-cleanup.js
```

## Troubleshooting

### Tests Failing

1. **Check API server is running**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. **Verify environment variables**
   - Check `base_url` is correct
   - Ensure `api_base` is set to `{{base_url}}/api/v1`

3. **Review test logs**
   - Check console output for error details
   - Review HTML report in `./test-results/`

4. **Database state**
   - Ensure database is seeded with required data
   - Check for conflicting test data

### Collection Not Found

1. **Verify collection ID**
   ```javascript
   kiroPowers.use({
     powerName: "postman",
     serverName: "postman",
     toolName: "getCollections",
     arguments: { workspace: "<workspace-id>" }
   })
   ```

2. **Check permissions**
   - Ensure API key has collection read/write permissions

### Environment Not Found

1. **List environments**
   ```javascript
   kiroPowers.use({
     powerName: "postman",
     serverName: "postman",
     toolName: "getEnvironments",
     arguments: { workspace: "<workspace-id>" }
   })
   ```

2. **Verify environment ID in config**

## Best Practices

1. **Run tests before deployment** - Always validate API changes
2. **Use appropriate environment** - Local for dev, Staging for pre-prod
3. **Clean up test data** - Prevent database pollution
4. **Review failures** - Investigate and fix failing tests immediately
5. **Update tests** - Keep tests in sync with API changes
6. **Version control** - Commit collection and config files
7. **Monitor performance** - Track response times and optimize slow endpoints

## Support

For issues or questions:
1. Review `POSTMAN_AUTOMATION_GUIDE.md` for detailed instructions
2. Check Postman API documentation
3. Verify API server logs
4. Review test script errors in collection

## References

- [Postman API Documentation](https://learning.postman.com/docs/developer/postman-api/intro-api/)
- [Postman Collection Format](https://schema.postman.com/collection/json/v2.1.0/draft-07/docs/index.html)
- [Kiro Powers Documentation](https://kiro.dev/docs/powers/)
- [Shuren API Documentation](./docs/technichal/backend_trd.md)
