# Quick Start Guide - Postman API Testing

This guide provides the fastest way to start testing the Shuren Backend API.

---

## Prerequisites

✅ Backend server running at `http://localhost:8000`  
✅ Postman Desktop App or Postman Power via Kiro  
✅ Collection file: `.postman.json`

---

## Option 1: Postman Desktop App (Fastest)

### Step 1: Import Collection
1. Open Postman Desktop App
2. Click **Import** button
3. Select `.postman.json` file
4. Collection "Shuren Backend API - E2E Tests" will be imported

### Step 2: Create Environment
1. Click **Environments** in left sidebar
2. Click **+** to create new environment
3. Name it "Development"
4. Add these variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| base_url | http://localhost:8000 | http://localhost:8000 |
| api_base | {{base_url}}/api/v1 | {{base_url}}/api/v1 |
| jwt_token | | |
| user_id | | |
| test_email | | |
| test_password | | |
| profile_id | | |

5. Click **Save**

### Step 3: Run Collection
1. Click on "Shuren Backend API - E2E Tests" collection
2. Click **Run** button (top right)
3. Select "Development" environment
4. Click **Run Shuren Backend API - E2E Tests**
5. Watch tests execute in real-time

### Step 4: Review Results
- Green checkmarks = Passed tests
- Red X marks = Failed tests
- Click on any request to see details
- Export results via **Export Results** button

---

## Option 2: Via Postman Power (Kiro Integration)

### Step 1: Activate Postman Power
```javascript
kiroPowers.activate("postman")
```

### Step 2: Get Authenticated User
```javascript
kiroPowers.use({
  powerName: "postman",
  serverName: "postman",
  toolName: "getAuthenticatedUser",
  arguments: {}
})
```

### Step 3: Create Workspace
```javascript
kiroPowers.use({
  powerName: "postman",
  serverName: "postman",
  toolName: "createWorkspace",
  arguments: {
    workspace: {
      name: "Shuren API Testing",
      type: "team",
      description: "E2E API testing for Shuren fitness application"
    }
  }
})
```
**Save the returned `workspace.id`**

### Step 4: Import Collection
```javascript
// Load collection data
const collectionData = require('./.postman.json');

kiroPowers.use({
  powerName: "postman",
  serverName: "postman",
  toolName: "createCollection",
  arguments: {
    workspace: "<workspace-id-from-step-3>",
    collection: collectionData.collection
  }
})
```
**Save the returned `collection.uid`**

### Step 5: Create Environment
```javascript
kiroPowers.use({
  powerName: "postman",
  serverName: "postman",
  toolName: "createEnvironment",
  arguments: {
    workspace: "<workspace-id-from-step-3>",
    environment: {
      name: "Development",
      values: [
        { key: "base_url", value: "http://localhost:8000", enabled: true },
        { key: "api_base", value: "{{base_url}}/api/v1", enabled: true },
        { key: "jwt_token", value: "", enabled: true },
        { key: "user_id", value: "", enabled: true },
        { key: "test_email", value: "", enabled: true },
        { key: "test_password", value: "", enabled: true },
        { key: "profile_id", value: "", enabled: true }
      ]
    }
  }
})
```
**Save the returned `environment.id`**

### Step 6: Run Collection
```javascript
kiroPowers.use({
  powerName: "postman",
  serverName: "postman",
  toolName: "runCollection",
  arguments: {
    collectionId: "<collection-uid-from-step-4>",
    environmentId: "<environment-id-from-step-5>",
    iterationCount: 1,
    stopOnError: false,
    stopOnFailure: false,
    requestTimeout: 5000,
    scriptTimeout: 5000
  }
})
```

### Step 7: Review Results
The response will include:
```javascript
{
  run: {
    stats: {
      requests: { total: 33, pending: 0, failed: 0 },
      assertions: { total: 120, pending: 0, failed: 0 },
      testScripts: { total: 33, pending: 0, failed: 0 }
    },
    failures: [],
    executions: [/* detailed execution data */]
  }
}
```

---

## Option 3: Via Newman CLI

### Step 1: Install Newman
```bash
npm install -g newman
npm install -g newman-reporter-html
```

### Step 2: Create Environment File
Create `postman-dev-env.json`:
```json
{
  "name": "Development",
  "values": [
    { "key": "base_url", "value": "http://localhost:8000", "enabled": true },
    { "key": "api_base", "value": "{{base_url}}/api/v1", "enabled": true },
    { "key": "jwt_token", "value": "", "enabled": true },
    { "key": "user_id", "value": "", "enabled": true },
    { "key": "test_email", "value": "", "enabled": true },
    { "key": "test_password", "value": "", "enabled": true },
    { "key": "profile_id", "value": "", "enabled": true }
  ]
}
```

### Step 3: Run Tests
```bash
newman run .postman.json -e postman-dev-env.json --reporters cli,html --reporter-html-export ./test-results/report.html
```

### Step 4: View Results
- Console output shows real-time results
- HTML report saved to `./test-results/report.html`
- Open HTML file in browser for detailed view

---

## Troubleshooting

### Backend Not Running
**Error:** Connection refused to localhost:8000

**Solution:**
```bash
cd backend
.\run_local.bat
```
Wait for "Application startup complete" message.

### Authentication Failures
**Error:** 401 Unauthorized on protected endpoints

**Solution:**
1. Check that registration and login requests run first
2. Verify JWT token is extracted to environment variable
3. Check collection pre-request script sets Authorization header

### Test Data Conflicts
**Error:** 400 Bad Request - Email already exists

**Solution:**
1. Run cleanup script: `node postman-cleanup.js`
2. Or manually delete test users from database
3. Ensure unique test data generation in pre-request scripts

### Timeout Errors
**Error:** Request timeout after 5000ms

**Solution:**
1. Increase timeout in `.postman-runner-config.json`
2. Check backend server performance
3. Verify database connection is stable

---

## Expected Results

### Successful Run
- ✅ All 33 requests execute
- ✅ 100+ test assertions pass
- ✅ No failures
- ✅ Response times within limits
- ✅ Test data cleaned up

### Common Failures
1. **First run failures:** Database may need seeding
2. **Timing issues:** Increase delay between requests
3. **Data dependencies:** Ensure sequential execution

---

## Next Steps

After successful test run:

1. **Review Results:** Check all tests passed
2. **Fix Failures:** Address any failing tests
3. **Run Cleanup:** Execute cleanup script
4. **Integrate CI/CD:** Add to deployment pipeline
5. **Monitor Performance:** Track response times

---

## Quick Commands Reference

```bash
# Start backend server
cd backend
.\run_local.bat

# Validate framework
node validate-postman-framework.js

# Run tests via Newman
newman run .postman.json -e postman-dev-env.json --reporters cli,html

# Run cleanup
node postman-cleanup.js postman-dev-env.json http://localhost:8000/api/v1 <jwt-token>

# View HTML report
start ./test-results/report.html
```

---

## Support

For issues or questions:
1. Check `POSTMAN_TESTING_README.md` for detailed documentation
2. Review `POSTMAN_AUTOMATION_GUIDE.md` for automation help
3. See `FINAL_VALIDATION_REPORT.md` for validation details
4. Check backend logs for API errors

---

**Last Updated:** February 1, 2026  
**Framework Version:** 1.0  
**Status:** Production Ready
