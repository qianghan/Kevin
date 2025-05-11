#!/usr/bin/env node

/**
 * Test Chat Implementation against UITasks requirements
 * 
 * This script helps test the chat implementation to validate that
 * the tasks in ui/uitasks.md section 6.x have been properly implemented.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Configuration
const CONFIG = {
  backendPort: 4000,
  uiPort: 3001,
  frontendPort: 3000,
  uitasksPath: path.resolve(__dirname, '../../ui/uitasks.md'),
  componentDocsPath: path.resolve(__dirname, '../src/docs/understandme_chat_components.md'),
  serviceTests: ['chat.feature'],
  chatFeatures: [
    'send message', 
    'view message history',
    'session persistence',
    'attachments',
    'ui/frontend synchronization'
  ]
};

// ANSI color codes for terminal output
const COLORS = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

function log(message, color = COLORS.reset) {
  console.log(`${color}${message}${COLORS.reset}`);
}

/**
 * Check if a given item is completed in the UITasks file
 */
function checkUITasksItem(searchString) {
  try {
    const content = fs.readFileSync(CONFIG.uitasksPath, 'utf-8');
    const regex = new RegExp(`\\[(x|X)\\]\\s*${searchString}`);
    return regex.test(content);
  } catch (error) {
    log(`Error checking UITasks item: ${error.message}`, COLORS.red);
    return false;
  }
}

/**
 * Validate documentation exists
 */
function checkDocumentation() {
  log('\n--- Checking Documentation ---', COLORS.cyan);
  
  const docsExist = fs.existsSync(CONFIG.componentDocsPath);
  if (docsExist) {
    const stats = fs.statSync(CONFIG.componentDocsPath);
    const isSubstantial = stats.size > 1000; // At least 1KB
    
    log(`Documentation exists: ${docsExist ? '✅' : '❌'}`, docsExist ? COLORS.green : COLORS.red);
    log(`Documentation has substantial content: ${isSubstantial ? '✅' : '❌'}`, isSubstantial ? COLORS.green : COLORS.red);
    
    return docsExist && isSubstantial;
  } else {
    log(`Documentation file not found at ${CONFIG.componentDocsPath}`, COLORS.red);
    return false;
  }
}

/**
 * Start all services required for testing
 */
function startServices() {
  log('\n--- Starting Test Services ---', COLORS.cyan);
  
  try {
    log('Starting integrated test environment...', COLORS.yellow);
    
    // Use the existing startup script to launch the services
    const startCmd = 'npm run start:services';
    execSync(startCmd, { stdio: 'inherit', cwd: __dirname });
    
    return true;
  } catch (error) {
    log(`Failed to start services: ${error.message}`, COLORS.red);
    return false;
  }
}

/**
 * Run BDD tests for chat features
 */
function runChatFeatureTests() {
  log('\n--- Running Chat Feature Tests ---', COLORS.cyan);
  
  try {
    // Run cucumber tests for chat features
    const testCmd = `npm run test -- --tags @chat`;
    log('Running chat integration tests...', COLORS.yellow);
    execSync(testCmd, { stdio: 'inherit', cwd: __dirname });
    
    return true;
  } catch (error) {
    log(`Tests failed: ${error.message}`, COLORS.red);
    return false;
  }
}

/**
 * Validate UI implementation against UITasks requirements
 */
function validateUITasksImplementation() {
  log('\n--- Validating UITasks Implementation ---', COLORS.cyan);
  
  const checkItems = [
    { name: 'Chat Component Interfaces', task: 'Define component interfaces aligned with existing /ui implementations (ISP)' },
    { name: 'ChatContainer component', task: 'Implement ChatContainer component with theming adaptations for Chakra UI' },
    { name: 'ChatHeader with session controls', task: 'Create ChatHeader with session controls compatible with both systems' },
    { name: 'ChatMessageList', task: 'Implement ChatMessageList with virtualization and consistent rendering' },
    { name: 'Message Components', task: 'Create UserMessage and AIMessage components with shared rendering logic (LSP)' },
    { name: 'StreamingMessage component', task: 'Implement StreamingMessage component with animations that works with existing stream formats' },
    { name: 'ThinkingSteps visualization', task: 'Create ThinkingSteps visualization component with backend compatibility' },
    { name: 'ChatInput with attachments', task: 'Implement ChatInput with attachments support using unified handling' },
    { name: 'Component mapping layer', task: 'Create component mapping layer for gradual transition' },
    { name: 'Component compatibility docs', task: 'Document component compatibility strategy in understandme_chat_components.md' },
    { name: 'Service integration', task: 'Create service factory with strategy pattern for delegating to /ui implementations' },
    { name: 'Service proxy', task: 'Implement service proxy pattern for /ui chat functionality' },
  ];
  
  let completed = 0;
  
  checkItems.forEach(item => {
    const isCompleted = checkUITasksItem(item.task);
    log(`${item.name}: ${isCompleted ? '✅ Completed' : '❌ Not completed'}`, isCompleted ? COLORS.green : COLORS.red);
    if (isCompleted) completed++;
  });
  
  const percentage = (completed / checkItems.length) * 100;
  log(`\nCompletion: ${percentage.toFixed(1)}% (${completed}/${checkItems.length} items)`, 
    percentage === 100 ? COLORS.green : (percentage >= 75 ? COLORS.yellow : COLORS.red));
  
  return percentage === 100;
}

/**
 * Test the chat implementation in the browser
 */
function runManualBrowserTests() {
  log('\n--- Manual Browser Testing ---', COLORS.cyan);
  log('Please perform the following manual tests in your browser:', COLORS.yellow);
  
  log('\n1. Open both UIs side by side:', COLORS.magenta);
  log(`   - Frontend: http://localhost:${CONFIG.frontendPort}/chat`);
  log(`   - Legacy UI: http://localhost:${CONFIG.uiPort}/chat`);
  
  log('\n2. Test session synchronization:', COLORS.magenta);
  log('   - Create a chat session in the frontend');
  log('   - Send a message');
  log('   - Verify the session appears in the legacy UI');
  log('   - Verify messages are synchronized');
  
  log('\n3. Test theme synchronization:', COLORS.magenta);
  log('   - Change theme in the frontend');
  log('   - Open settings page in the legacy UI');
  log('   - Verify theme preference is synchronized');
  
  log('\n4. Test component toggle:', COLORS.magenta);
  log('   - Go to settings and toggle "Use New UI Components"');
  log('   - Verify chat interface updates accordingly');

  log('\nPress Ctrl+C when testing is complete', COLORS.yellow);
}

/**
 * Main function
 */
async function main() {
  log('=== KAI UI Chat Implementation Test ===', COLORS.magenta);
  
  // Step 1: Check documentation
  const docsValid = checkDocumentation();
  
  // Step 2: Validate UITasks completion
  const taskImplementation = validateUITasksImplementation();
  
  // Step 3: Start services for testing (if previous checks pass)
  if (docsValid && taskImplementation) {
    if (startServices()) {
      // Step 4: Run automated tests (feature-based tests)
      const testsPassed = runChatFeatureTests();
      
      // Step 5: Manual browser testing instructions
      if (testsPassed) {
        runManualBrowserTests();
      }
    }
  } else {
    log('\n⚠️  Please complete the missing requirements before running the tests', COLORS.yellow);
  }
}

// Run the main function
main().catch(error => {
  console.error('Test script failed:', error);
  process.exit(1);
}); 