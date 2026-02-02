#!/usr/bin/env node

/**
 * API Endpoint Testing Script
 * 
 * This script systematically tests all Shuren Backend API endpoints
 * and documents failures for spec creation.
 */

const https = require('https');
const http = require('http');

const BASE_URL = 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v1`;

// Test results tracking
const results = {
    passed: [],
    failed: [],
    total: 0
};

// Test data
let testEmail = '';
let testPassword = '';
let jwtToken = '';
let userId = '';
let profileId = '';

// Helper function to make HTTP requests
function makeRequest(method, path, body = null, headers = {}, followRedirect = true) {
    return new Promise((resolve, reject) => {
        const url = new URL(path.startsWith('http') ? path : `${API_BASE}${path}`);
        
        const options = {
            hostname: url.hostname,
            port: url.port || 8000,
            path: url.pathname + url.search,
            method: method,
            headers: {
                'Content-Type': 'application/json',
                ...headers
            }
        };

        const req = http.request(options, (res) => {
            // Handle redirects
            if (followRedirect && (res.statusCode === 301 || res.statusCode === 302 || res.statusCode === 307 || res.statusCode === 308)) {
                const redirectUrl = res.headers.location;
                if (redirectUrl) {
                    // Follow the redirect
                    return makeRequest(method, redirectUrl, body, headers, false).then(resolve).catch(reject);
                }
            }
            
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const jsonData = data ? JSON.parse(data) : {};
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: jsonData
                    });
                } catch (e) {
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: data
                    });
                }
            });
        });

        req.on('error', (error) => {
            console.error(`Request error for ${method} ${path}:`, error);
            reject(error);
        });

        if (body) {
            req.write(JSON.stringify(body));
        }

        req.end();
    });
}

// Test result logging
function logTest(name, passed, expected, actual, error = null) {
    results.total++;
    
    if (passed) {
        results.passed.push({ name, expected, actual });
        console.log(`✓ ${name}`);
    } else {
        results.failed.push({ name, expected, actual, error });
        console.log(`✗ ${name}`);
        console.log(`  Expected: ${expected}`);
        console.log(`  Actual: ${actual}`);
        if (error) console.log(`  Error: ${error}`);
    }
}

// Test functions
async function testAuthenticationEndpoints() {
    console.log('\n=== Testing Authentication Endpoints ===\n');
    
    // 1. Register New User
    try {
        testEmail = `test_${Date.now()}_${Math.floor(Math.random() * 10000)}@example.com`;
        testPassword = `Test${Math.floor(Math.random() * 10000)}!Pass`;
        
        const response = await makeRequest('POST', '/auth/register', {
            email: testEmail,
            password: testPassword,
            full_name: "Test User"
        });
        
        logTest(
            'POST /auth/register - Register New User',
            response.status === 201,
            '201 Created',
            `${response.status} ${response.data.detail || 'OK'}`
        );
        
        if (response.status === 201 && response.data.id) {
            userId = response.data.id;
        }
    } catch (error) {
        console.error('Registration error details:', error);
        logTest('POST /auth/register', false, '201', 'Error', error.message || error.toString());
    }
    
    // 2. Register Duplicate Email
    try {
        const response = await makeRequest('POST', '/auth/register', {
            email: testEmail,
            password: testPassword,
            full_name: "Test User"
        });
        
        logTest(
            'POST /auth/register - Duplicate Email',
            response.status === 400,
            '400 Bad Request',
            `${response.status}`
        );
    } catch (error) {
        logTest('POST /auth/register - Duplicate', false, '400', 'Error', error.message);
    }
    
    // 3. Login with Valid Credentials
    try {
        const response = await makeRequest('POST', '/auth/login', {
            email: testEmail,
            password: testPassword
        });
        
        logTest(
            'POST /auth/login - Valid Credentials',
            response.status === 200 && response.data.access_token,
            '200 OK with JWT token',
            `${response.status} ${response.data.access_token ? 'with token' : 'no token'}`
        );
        
        if (response.data.access_token) {
            jwtToken = response.data.access_token;
        }
    } catch (error) {
        logTest('POST /auth/login', false, '200', 'Error', error.message);
    }
    
    // 4. Login with Invalid Credentials
    try {
        const response = await makeRequest('POST', '/auth/login', {
            email: testEmail,
            password: 'WrongPassword123!'
        });
        
        logTest(
            'POST /auth/login - Invalid Credentials',
            response.status === 401,
            '401 Unauthorized',
            `${response.status}`
        );
    } catch (error) {
        logTest('POST /auth/login - Invalid', false, '401', 'Error', error.message);
    }
    
    // 5. Get Current User (Authenticated)
    try {
        const response = await makeRequest('GET', '/auth/me', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /auth/me - Authenticated',
            response.status === 200,
            '200 OK',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /auth/me', false, '200', 'Error', error.message);
    }
    
    // 6. Get Current User (No Token)
    try {
        const response = await makeRequest('GET', '/auth/me');
        
        logTest(
            'GET /auth/me - No Token',
            response.status === 401,
            '401 Unauthorized',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /auth/me - No Token', false, '401', 'Error', error.message);
    }
}

async function testOnboardingEndpoints() {
    console.log('\n=== Testing Onboarding Endpoints ===\n');
    
    // 1. Get Onboarding State
    try {
        const response = await makeRequest('GET', '/onboarding/state', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /onboarding/state',
            response.status === 200,
            '200 OK',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /onboarding/state', false, '200', 'Error', error.message);
    }
    
    // 2. Submit Step 1 - Basic Info
    try {
        const response = await makeRequest('POST', '/onboarding/step', {
            step: 1,
            data: {
                age: 25,
                gender: 'male',
                height_cm: 175,
                weight_kg: 75
            }
        }, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'POST /onboarding/step - Step 1',
            response.status === 200,
            '200 OK',
            `${response.status}`
        );
    } catch (error) {
        logTest('POST /onboarding/step', false, '200', 'Error', error.message);
    }
    
    // 3. Complete Onboarding (without all steps)
    try {
        const response = await makeRequest('POST', '/onboarding/complete', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'POST /onboarding/complete - Incomplete',
            response.status === 400,
            '400 Bad Request',
            `${response.status}`
        );
    } catch (error) {
        logTest('POST /onboarding/complete', false, '400', 'Error', error.message);
    }
}

async function testProfileEndpoints() {
    console.log('\n=== Testing Profile Endpoints ===\n');
    
    // 1. Get User Profile
    try {
        const response = await makeRequest('GET', '/profiles/me', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /profiles/me',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
        
        if (response.status === 200 && response.data.id) {
            profileId = response.data.id;
        }
    } catch (error) {
        logTest('GET /profiles/me', false, '200/404', 'Error', error.message);
    }
    
    // 2. Update User Profile
    try {
        const response = await makeRequest('PATCH', '/profiles/me', {
            reason: "Testing profile update",
            updates: {
                fitness_goals: {
                    primary_goal: "muscle_gain"
                }
            }
        }, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'PATCH /profiles/me',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('PATCH /profiles/me', false, '200/404', 'Error', error.message);
    }
    
    // 3. Lock User Profile
    try {
        const response = await makeRequest('POST', '/profiles/me/lock', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'POST /profiles/me/lock',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('POST /profiles/me/lock', false, '200/404', 'Error', error.message);
    }
    
    // 4. Get Non-Existent Profile
    try {
        const response = await makeRequest('GET', '/profiles/00000000-0000-0000-0000-000000000000', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /profiles/{invalid_id}',
            response.status === 404,
            '404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /profiles/{invalid_id}', false, '404', 'Error', error.message);
    }
}

async function testWorkoutEndpoints() {
    console.log('\n=== Testing Workout Endpoints ===\n');
    
    // 1. Get Complete Workout Plan
    try {
        const response = await makeRequest('GET', '/workouts/plan', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /workouts/plan',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /workouts/plan', false, '200/404', 'Error', error.message);
    }
    
    // 2. Get Specific Workout Day
    try {
        const response = await makeRequest('GET', '/workouts/plan/day/1', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /workouts/plan/day/{day_number}',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /workouts/plan/day/{day_number}', false, '200/404', 'Error', error.message);
    }
    
    // 3. Get Today's Workout
    try {
        const response = await makeRequest('GET', '/workouts/today', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /workouts/today',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /workouts/today', false, '200/404', 'Error', error.message);
    }
    
    // 4. Get Week's Workouts
    try {
        const response = await makeRequest('GET', '/workouts/week', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /workouts/week',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /workouts/week', false, '200/404', 'Error', error.message);
    }
    
    // 5. Update Workout Plan
    try {
        const response = await makeRequest('PATCH', '/workouts/plan', {
            reason: "Testing workout plan update",
            updates: {
                difficulty_level: "intermediate"
            }
        }, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'PATCH /workouts/plan',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('PATCH /workouts/plan', false, '200/404', 'Error', error.message);
    }
    
    // 6. Get Workout Schedule
    try {
        const response = await makeRequest('GET', '/workouts/schedule', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /workouts/schedule',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /workouts/schedule', false, '200/404', 'Error', error.message);
    }
    
    // 7. Update Workout Schedule
    try {
        const response = await makeRequest('PATCH', '/workouts/schedule', {
            reason: "Testing schedule update",
            updates: {
                preferred_time: "morning"
            }
        }, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'PATCH /workouts/schedule',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('PATCH /workouts/schedule', false, '200/404', 'Error', error.message);
    }
}

async function testMealEndpoints() {
    console.log('\n=== Testing Meal Endpoints ===\n');
    
    // 1. Get Meal Plan
    try {
        const response = await makeRequest('GET', '/meals/plan', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /meals/plan',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /meals/plan', false, '200/404', 'Error', error.message);
    }
    
    // 2. Update Meal Plan
    try {
        const response = await makeRequest('PATCH', '/meals/plan', {
            reason: "Testing meal plan update",
            updates: {
                daily_calories: 2200
            }
        }, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'PATCH /meals/plan',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('PATCH /meals/plan', false, '200/404', 'Error', error.message);
    }
    
    // 3. Get Meal Schedule
    try {
        const response = await makeRequest('GET', '/meals/schedule', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /meals/schedule',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /meals/schedule', false, '200/404', 'Error', error.message);
    }
    
    // 4. Update Meal Schedule
    try {
        const response = await makeRequest('PATCH', '/meals/schedule', {
            meals: [
                {
                    meal_number: 1,
                    scheduled_time: "07:00:00",
                    is_active: true
                }
            ]
        }, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'PATCH /meals/schedule',
            response.status === 200 || response.status === 404 || response.status === 403,
            '200 OK, 403 Forbidden, or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('PATCH /meals/schedule', false, '200/403/404', 'Error', error.message);
    }
    
    // 5. Get Today's Meals
    try {
        const response = await makeRequest('GET', '/meals/today', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /meals/today',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /meals/today', false, '200/404', 'Error', error.message);
    }
    
    // 6. Get Next Meal
    try {
        const response = await makeRequest('GET', '/meals/next', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /meals/next',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /meals/next', false, '200/404', 'Error', error.message);
    }
}

async function testDishEndpoints() {
    console.log('\n=== Testing Dish Endpoints ===\n');
    
    // 1. List All Dishes
    try {
        const response = await makeRequest('GET', '/dishes', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /dishes',
            response.status === 200,
            '200 OK',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /dishes', false, '200', 'Error', error.message);
    }
    
    // 2. Search Dishes with Filters
    try {
        const response = await makeRequest('GET', '/dishes/search?meal_type=breakfast&is_vegetarian=true', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /dishes/search',
            response.status === 200,
            '200 OK',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /dishes/search', false, '200', 'Error', error.message);
    }
    
    // 3. Get Dish Details
    try {
        const response = await makeRequest('GET', '/dishes/00000000-0000-0000-0000-000000000000', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /dishes/{id}',
            response.status === 404,
            '404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /dishes/{id}', false, '404', 'Error', error.message);
    }
}

async function testMealTemplateEndpoints() {
    console.log('\n=== Testing Meal Template Endpoints ===\n');
    
    // 1. Get Today's Meal Template
    try {
        const response = await makeRequest('GET', '/meal-templates/today', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /meal-templates/today',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /meal-templates/today', false, '200/404', 'Error', error.message);
    }
    
    // 2. Get Next Meal Template
    try {
        const response = await makeRequest('GET', '/meal-templates/next', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /meal-templates/next',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /meal-templates/next', false, '200/404', 'Error', error.message);
    }
    
    // 3. Get Week's Meal Template
    try {
        const response = await makeRequest('GET', '/meal-templates/template', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /meal-templates/template',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /meal-templates/template', false, '200/404', 'Error', error.message);
    }
    
    // 4. Regenerate Meal Template
    try {
        const response = await makeRequest('POST', '/meal-templates/template/regenerate', {
            preferences: {
                diet_type: "balanced"
            },
            week_number: 1
        }, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'POST /meal-templates/template/regenerate',
            response.status === 200 || response.status === 201 || response.status === 404,
            '200/201 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('POST /meal-templates/template/regenerate', false, '200/201/404', 'Error', error.message);
    }
}

async function testShoppingListEndpoints() {
    console.log('\n=== Testing Shopping List Endpoints ===\n');
    
    // 1. Get Shopping List
    try {
        const response = await makeRequest('GET', '/shopping-list', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /shopping-list',
            response.status === 200 || response.status === 404,
            '200 OK or 404 Not Found',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /shopping-list', false, '200/404', 'Error', error.message);
    }
}

async function testChatEndpoints() {
    console.log('\n=== Testing Chat Endpoints ===\n');
    
    let sessionId = '';
    
    // 1. Start Chat Session
    try {
        const response = await makeRequest('POST', '/chat/sessions', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'POST /chat/sessions',
            response.status === 200 || response.status === 201,
            '200/201 OK',
            `${response.status}`
        );
        
        if ((response.status === 200 || response.status === 201) && response.data.session_id) {
            sessionId = response.data.session_id;
        }
    } catch (error) {
        logTest('POST /chat/sessions', false, '200/201', 'Error', error.message);
    }
    
    // 2. Alternative Session Start
    try {
        const response = await makeRequest('POST', '/chat/session/start', {
            session_type: "general",
            context_data: {}
        }, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'POST /chat/session/start',
            response.status === 200 || response.status === 201,
            '200/201 OK',
            `${response.status}`
        );
        
        if ((response.status === 200 || response.status === 201) && response.data.session_id) {
            sessionId = response.data.session_id;
        }
    } catch (error) {
        logTest('POST /chat/session/start', false, '200/201', 'Error', error.message);
    }
    
    // 3. Send Chat Message
    try {
        const response = await makeRequest('POST', '/chat/message', {
            message: "Hello, this is a test message",
            session_id: sessionId || undefined
        }, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'POST /chat/message',
            response.status === 200 || response.status === 201,
            '200/201 OK',
            `${response.status}`
        );
    } catch (error) {
        logTest('POST /chat/message', false, '200/201', 'Error', error.message);
    }
    
    // 4. Get Chat History
    try {
        const response = await makeRequest('GET', '/chat/history?limit=10&offset=0', null, {
            'Authorization': `Bearer ${jwtToken}`
        });
        
        logTest(
            'GET /chat/history',
            response.status === 200,
            '200 OK',
            `${response.status}`
        );
    } catch (error) {
        logTest('GET /chat/history', false, '200', 'Error', error.message);
    }
    
    // 5. End Chat Session
    if (sessionId) {
        try {
            const response = await makeRequest('DELETE', `/chat/session/${sessionId}`, null, {
                'Authorization': `Bearer ${jwtToken}`
            });
            
            logTest(
                'DELETE /chat/session/{session_id}',
                response.status === 200 || response.status === 204,
                '200/204 OK',
                `${response.status}`
            );
        } catch (error) {
            logTest('DELETE /chat/session/{session_id}', false, '200/204', 'Error', error.message);
        }
    }
}

// Main execution
async function runTests() {
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║  Shuren Backend API - Endpoint Testing                    ║');
    console.log('║  Testing all endpoints and documenting failures           ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    
    try {
        await testAuthenticationEndpoints();
        await testOnboardingEndpoints();
        await testProfileEndpoints();
        await testWorkoutEndpoints();
        await testMealEndpoints();
        await testDishEndpoints();
        await testMealTemplateEndpoints();
        await testShoppingListEndpoints();
        await testChatEndpoints();
        
        // Print summary
        console.log('\n╔════════════════════════════════════════════════════════════╗');
        console.log('║  Test Results Summary                                      ║');
        console.log('╚════════════════════════════════════════════════════════════╝\n');
        
        console.log(`Total Tests: ${results.total}`);
        console.log(`Passed: ${results.passed.length} (${Math.round(results.passed.length/results.total*100)}%)`);
        console.log(`Failed: ${results.failed.length} (${Math.round(results.failed.length/results.total*100)}%)`);
        
        if (results.failed.length > 0) {
            console.log('\n=== Failed Tests ===\n');
            results.failed.forEach((test, index) => {
                console.log(`${index + 1}. ${test.name}`);
                console.log(`   Expected: ${test.expected}`);
                console.log(`   Actual: ${test.actual}`);
                if (test.error) console.log(`   Error: ${test.error}`);
                console.log('');
            });
        }
        
        // Save results to file
        const fs = require('fs');
        fs.writeFileSync('api-test-results.json', JSON.stringify(results, null, 2));
        console.log('Results saved to api-test-results.json\n');
        
    } catch (error) {
        console.error('Fatal error during testing:', error);
        process.exit(1);
    }
}

// Run the tests
runTests();
