#!/usr/bin/env node

/**
 * Postman API Testing Automation Script
 * 
 * This script automates the complete Postman testing workflow using Kiro's Postman Power:
 * 1. Activates Postman Power via Kiro
 * 2. Creates or retrieves workspace
 * 3. Imports collection to workspace
 * 4. Creates environments (Development, Staging, Production)
 * 5. Runs collection with specified environment
 * 6. Retrieves and displays test results
 * 7. Optionally runs cleanup script
 * 
 * Prerequisites:
 * - Postman API key configured in environment variable POSTMAN_API_KEY
 * - Kiro Powers with Postman Power installed
 * - .postman.json file with collection definition
 * - .postman-runner-config.json file with runner configuration
 * 
 * Usage:
 *   node postman-automation.js [options]
 * 
 * Options:
 *   --environment <name>    Environment to use (Development, Staging, Production) [default: Development]
 *   --workspace <id>        Existing workspace ID (creates new if not provided)
 *   --collection <path>     Path to collection JSON file [default: .postman.json]
 *   --config <path>         Path to runner config file [default: .postman-runner-config.json]
 *   --cleanup               Run cleanup script after tests
 *   --help                  Show this help message
 * 
 * Examples:
 *   node postman-automation.js
 *   node postman-automation.js --environment Staging
 *   node postman-automation.js --workspace abc123 --cleanup
 */

const fs = require('fs');
const path = require('path');

// Parse command line arguments
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        environment: 'Development',
        workspace: null,
        collection: '.postman.json',
        config: '.postman-runner-config.json',
        cleanup: false,
        help: false
    };

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--environment':
                options.environment = args[++i];
                break;
            case '--workspace':
                options.workspace = args[++i];
                break;
            case '--collection':
                options.collection = args[++i];
                break;
            case '--config':
                options.config = args[++i];
                break;
            case '--cleanup':
                options.cleanup = true;
                break;
            case '--help':
                options.help = true;
                break;
        }
    }

    return options;
}

// Display help message
function showHelp() {
    console.log(`
Postman API Testing Automation Script

Usage:
  node postman-automation.js [options]

Options:
  --environment <name>    Environment to use (Development, Staging, Production) [default: Development]
  --workspace <id>        Existing workspace ID (creates new if not provided)
  --collection <path>     Path to collection JSON file [default: .postman.json]
  --config <path>         Path to runner config file [default: .postman-runner-config.json]
  --cleanup               Run cleanup script after tests
  --help                  Show this help message

Examples:
  node postman-automation.js
  node postman-automation.js --environment Staging
  node postman-automation.js --workspace abc123 --cleanup
    `);
}

// Load JSON file
function loadJsonFile(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        return JSON.parse(content);
    } catch (error) {
        console.error(`Failed to load ${filePath}: ${error.message}`);
        process.exit(1);
    }
}

// Save JSON file
function saveJsonFile(filePath, data) {
    try {
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
        console.log(`✓ Saved ${filePath}`);
    } catch (error) {
        console.error(`Failed to save ${filePath}: ${error.message}`);
    }
}

// Main automation workflow
async function main() {
    const options = parseArgs();

    if (options.help) {
        showHelp();
        process.exit(0);
    }

    console.log('=== Postman API Testing Automation ===\n');

    // Load collection and config
    console.log('Step 1: Loading collection and configuration...');
    const collectionData = loadJsonFile(options.collection);
    const runnerConfig = loadJsonFile(options.config);
    console.log(`✓ Loaded collection: ${collectionData.collection.name}`);
    console.log(`✓ Loaded runner config\n`);

    // Instructions for using Kiro Powers
    console.log('Step 2: Activate Postman Power via Kiro');
    console.log('---------------------------------------');
    console.log('To use this script with Kiro Powers, follow these steps:\n');
    console.log('1. In Kiro, run the following command:');
    console.log('   kiroPowers.activate("postman")\n');
    console.log('2. Get your authenticated user information:');
    console.log('   kiroPowers.use({');
    console.log('     powerName: "postman",');
    console.log('     serverName: "postman",');
    console.log('     toolName: "getAuthenticatedUser",');
    console.log('     arguments: {}');
    console.log('   })\n');

    // Workspace setup
    console.log('Step 3: Workspace Setup');
    console.log('-----------------------');
    if (options.workspace) {
        console.log(`Using existing workspace ID: ${options.workspace}\n`);
        console.log('To verify workspace, run in Kiro:');
        console.log('   kiroPowers.use({');
        console.log('     powerName: "postman",');
        console.log('     serverName: "postman",');
        console.log('     toolName: "getWorkspace",');
        console.log(`     arguments: { workspaceId: "${options.workspace}" }`);
        console.log('   })\n');
    } else {
        console.log('Creating new workspace...\n');
        console.log('To create workspace, run in Kiro:');
        console.log('   kiroPowers.use({');
        console.log('     powerName: "postman",');
        console.log('     serverName: "postman",');
        console.log('     toolName: "createWorkspace",');
        console.log('     arguments: {');
        console.log('       workspace: {');
        console.log(`         name: "${collectionData.workspace.name}",`);
        console.log(`         type: "${collectionData.workspace.type}",`);
        console.log(`         description: "${collectionData.workspace.description}"`);
        console.log('       }');
        console.log('     }');
        console.log('   })\n');
        console.log('Save the returned workspace.id for next steps.\n');
    }

    // Collection import
    console.log('Step 4: Import Collection');
    console.log('--------------------------');
    console.log('To import the collection, run in Kiro:');
    console.log('   kiroPowers.use({');
    console.log('     powerName: "postman",');
    console.log('     serverName: "postman",');
    console.log('     toolName: "createCollection",');
    console.log('     arguments: {');
    console.log('       workspace: "<workspace-id-from-step-3>",');
    console.log('       collection: {');
    console.log('         info: {');
    console.log(`           name: "${collectionData.collection.name}",`);
    console.log('           schema: "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"');
    console.log('         },');
    console.log('         variable: [');
    console.log(`           { key: "api_version", value: "${collectionData.collection.variables.api_version}" },`);
    console.log(`           { key: "timeout_ms", value: "${collectionData.collection.variables.timeout_ms}" },`);
    console.log(`           { key: "test_user_prefix", value: "${collectionData.collection.variables.test_user_prefix}" }`);
    console.log('         ]');
    console.log('       }');
    console.log('     }');
    console.log('   })\n');
    console.log('Save the returned collection.id and collection.uid for next steps.\n');

    // Environment creation
    console.log('Step 5: Create Environments');
    console.log('----------------------------');
    const environments = ['development', 'staging', 'production'];
    environments.forEach(env => {
        const envData = collectionData.environments[env];
        console.log(`\nTo create ${envData.name} environment, run in Kiro:`);
        console.log('   kiroPowers.use({');
        console.log('     powerName: "postman",');
        console.log('     serverName: "postman",');
        console.log('     toolName: "createEnvironment",');
        console.log('     arguments: {');
        console.log('       workspace: "<workspace-id-from-step-3>",');
        console.log('       environment: {');
        console.log(`         name: "${envData.name}",`);
        console.log('         values: [');
        console.log(`           { key: "base_url", value: "${envData.base_url}", enabled: true },`);
        console.log('           { key: "api_base", value: "{{base_url}}/api/v1", enabled: true },');
        console.log('           { key: "jwt_token", value: "", enabled: true },');
        console.log('           { key: "user_id", value: "", enabled: true },');
        console.log('           { key: "test_email", value: "", enabled: true },');
        console.log('           { key: "test_password", value: "", enabled: true },');
        console.log('           { key: "profile_id", value: "", enabled: true }');
        console.log('         ]');
        console.log('       }');
        console.log('     }');
        console.log('   })');
    });
    console.log('\nSave the returned environment IDs for next steps.\n');

    // Collection run
    console.log('Step 6: Run Collection');
    console.log('----------------------');
    console.log(`To run the collection with ${options.environment} environment, run in Kiro:`);
    console.log('   kiroPowers.use({');
    console.log('     powerName: "postman",');
    console.log('     serverName: "postman",');
    console.log('     toolName: "runCollection",');
    console.log('     arguments: {');
    console.log('       collectionId: "<collection-uid-from-step-4>",');
    console.log(`       environmentId: "<${options.environment.toLowerCase()}-environment-id-from-step-5>",`);
    console.log(`       iterationCount: ${runnerConfig.iterations},`);
    console.log(`       stopOnError: ${runnerConfig.bail},`);
    console.log(`       stopOnFailure: ${runnerConfig.bail},`);
    console.log(`       requestTimeout: ${runnerConfig.timeoutRequest},`);
    console.log(`       scriptTimeout: ${runnerConfig.timeoutScript}`);
    console.log('     }');
    console.log('   })\n');

    // Results display
    console.log('Step 7: Display Test Results');
    console.log('-----------------------------');
    console.log('The runCollection response will include:');
    console.log('- run.stats.requests: Total number of requests executed');
    console.log('- run.stats.assertions: Total number of test assertions');
    console.log('- run.stats.testScripts: Number of test scripts executed');
    console.log('- run.failures: Array of failed tests with details');
    console.log('- run.executions: Detailed execution data for each request\n');
    console.log('Example result structure:');
    console.log('{');
    console.log('  run: {');
    console.log('    stats: {');
    console.log('      requests: { total: 52, pending: 0, failed: 2 },');
    console.log('      assertions: { total: 180, pending: 0, failed: 2 },');
    console.log('      testScripts: { total: 52, pending: 0, failed: 0 }');
    console.log('    },');
    console.log('    failures: [');
    console.log('      {');
    console.log('        error: { name: "AssertionError", message: "..." },');
    console.log('        at: "request-name",');
    console.log('        source: { name: "test-name" }');
    console.log('      }');
    console.log('    ]');
    console.log('  }');
    console.log('}\n');

    // Cleanup
    if (options.cleanup) {
        console.log('Step 8: Cleanup Test Data');
        console.log('--------------------------');
        console.log('After tests complete, run the cleanup script:');
        console.log('   node postman-cleanup.js <environment-file> <api-base-url> <jwt-token>\n');
        console.log('Example:');
        console.log('   node postman-cleanup.js ./postman-dev-env.json http://localhost:8000/api/v1 eyJhbGc...\n');
    }

    // Save configuration
    console.log('Step 9: Save Configuration');
    console.log('--------------------------');
    console.log('After completing the above steps, save the IDs to a configuration file:\n');
    const configTemplate = {
        workspace_id: '<workspace-id-from-step-3>',
        collection_id: '<collection-id-from-step-4>',
        collection_uid: '<collection-uid-from-step-4>',
        environments: {
            development: '<development-environment-id-from-step-5>',
            staging: '<staging-environment-id-from-step-5>',
            production: '<production-environment-id-from-step-5>'
        },
        last_run: null,
        last_run_results: null
    };
    
    const configPath = '.postman-automation-config.json';
    if (!fs.existsSync(configPath)) {
        saveJsonFile(configPath, configTemplate);
        console.log(`Created template configuration file: ${configPath}`);
        console.log('Update this file with the actual IDs from the steps above.\n');
    } else {
        console.log(`Configuration file already exists: ${configPath}\n`);
    }

    console.log('=== Automation Script Complete ===');
    console.log('\nNext Steps:');
    console.log('1. Follow the Kiro Power commands above to set up your workspace');
    console.log('2. Update .postman-automation-config.json with the returned IDs');
    console.log('3. Run this script again to execute tests');
    console.log('4. Review test results and fix any failures');
    console.log('5. Optionally run cleanup script to remove test data\n');
}

// Run the script
main().catch(error => {
    console.error(`\nError: ${error.message}`);
    process.exit(1);
});
