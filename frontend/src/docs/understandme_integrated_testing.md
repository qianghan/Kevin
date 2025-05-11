# KAI Integrated Testing Environment

This document outlines the integrated testing environment for the KAI application, providing a comprehensive framework for full-stack testing across UI, frontend, and backend components.

## Table of Contents

1. [Overview](#overview)
2. [Environment Components](#environment-components)
3. [Unified Startup Process](#unified-startup-process)
4. [Containerized Test Environment](#containerized-test-environment)
5. [Service Configuration](#service-configuration)
6. [Environment Variables](#environment-variables)
7. [Health Check System](#health-check-system)
8. [Test Data Seeding](#test-data-seeding)
9. [End-to-End Testing](#end-to-end-testing)
10. [Troubleshooting](#troubleshooting)

## Overview

The KAI Integrated Testing Environment provides a unified system for testing the entire application stack from backend services to frontend components. This environment enables:

- Full-stack integration testing of UI, frontend, and backend components
- Consistent testing environments across development, CI/CD, and staging
- Automated setup and teardown of all required services
- Deterministic test runs with controlled data seeding
- Comprehensive test coverage with BDD scenarios

## Environment Components

The testing environment consists of several interconnected components:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Backend APIs   │◄────┤  UI Services    │◄────┤  Frontend App   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ▲                       ▲                       ▲
        │                       │                       │
        └───────────────┬───────┴───────────────┬───────┘
                        │                       │
                ┌───────────────┐       ┌───────────────┐
                │               │       │               │
                │  Test Runner  │◄──────┤  Test Data    │
                │               │       │               │
                └───────────────┘       └───────────────┘
```

### Component Descriptions:

- **Backend APIs**: Core services including chat, profile, auth, and agent APIs
- **UI Services**: Legacy UI application services from the `/ui` directory
- **Frontend App**: Next.js-based frontend application
- **Test Runner**: Orchestrates test execution and manages service lifecycle
- **Test Data**: Provides controlled, deterministic test data

## Unified Startup Process

The integrated testing environment uses a unified startup script that orchestrates all required services:

```typescript
// tests/integration/startup.ts
import { startBackendServices } from './services/backend';
import { startUIServices } from './services/ui';
import { startFrontendServices } from './services/frontend';
import { healthCheck } from './utils/health-check';

export async function startIntegratedTestEnvironment(options = {}) {
  console.log('Starting backend services...');
  const backendConfig = await startBackendServices(options.backend);
  
  console.log('Starting UI services...');
  const uiConfig = await startUIServices({
    ...options.ui,
    backendEndpoints: backendConfig.endpoints,
  });
  
  console.log('Starting frontend services...');
  await startFrontendServices({
    ...options.frontend,
    backendEndpoints: backendConfig.endpoints,
    uiEndpoints: uiConfig.endpoints,
  });
  
  console.log('Running health checks...');
  await healthCheck(backendConfig, uiConfig);
  
  return {
    backend: backendConfig,
    ui: uiConfig,
    teardown: async () => {
      console.log('Shutting down all services...');
      await Promise.all([
        backendConfig.shutdown(),
        uiConfig.shutdown(),
      ]);
    }
  };
}
```

This startup script is used by both the test runner and development environments to ensure consistency.

## Containerized Test Environment

### Docker Compose Configuration

The integrated test environment is containerized using Docker Compose, allowing for consistent setup across different environments:

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  # Backend services
  kai-api:
    build:
      context: ./backend
      dockerfile: Dockerfile.test
    ports:
      - "4000:4000"
    environment:
      - NODE_ENV=test
      - DB_CONNECTION_STRING=mongodb://mongo:27017/kai-test
    depends_on:
      - mongo
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      
  # Database
  mongo:
    image: mongo:5.0
    ports:
      - "27017:27017"
    volumes:
      - mongo-test-data:/data/db
    
  # UI services
  kai-ui:
    build:
      context: ./ui
      dockerfile: Dockerfile.test
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=test
      - API_URL=http://kai-api:4000
    depends_on:
      - kai-api
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      
  # Frontend application
  kai-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.test
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=test
      - API_URL=http://kai-api:4000
      - UI_URL=http://kai-ui:3001
    depends_on:
      - kai-ui
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      
  # Test runner
  test-runner:
    build:
      context: ./tests
      dockerfile: Dockerfile
    depends_on:
      - kai-frontend
    volumes:
      - ./test-results:/app/test-results
    environment:
      - FRONTEND_URL=http://kai-frontend:3000
      - API_URL=http://kai-api:4000
      - UI_URL=http://kai-ui:3001

volumes:
  mongo-test-data:
```

### Running the Containerized Environment

To start the containerized test environment:

```bash
# Start all services
docker-compose -f docker-compose.test.yml up -d

# Run tests
docker-compose -f docker-compose.test.yml run test-runner

# Stop all services
docker-compose -f docker-compose.test.yml down
```

## Service Configuration

### Backend Service Configuration

The backend services are configured with test-specific settings:

```typescript
// tests/integration/services/backend.ts
import { spawn } from 'child_process';
import { waitForEndpoint } from '../utils/network';

export async function startBackendServices(options = {}) {
  const config = {
    port: options.port || 4000,
    dbUri: options.dbUri || 'mongodb://localhost:27017/kai-test',
    environment: options.environment || 'test',
  };
  
  // Start backend server with test configuration
  const backendProcess = spawn('node', [
    'server.js',
    '--port', config.port.toString(),
    '--db', config.dbUri,
    '--env', config.environment,
  ], {
    cwd: '../backend',
    env: {
      ...process.env,
      NODE_ENV: 'test',
    },
  });
  
  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
  
  // Wait for backend to be ready
  await waitForEndpoint(`http://localhost:${config.port}/health`, 30000);
  
  return {
    process: backendProcess,
    endpoints: {
      api: `http://localhost:${config.port}`,
    },
    shutdown: () => {
      return new Promise((resolve) => {
        backendProcess.on('close', resolve);
        backendProcess.kill();
      });
    },
  };
}
```

### UI Service Configuration

The UI services are configured to connect to the test backend:

```typescript
// tests/integration/services/ui.ts
import { spawn } from 'child_process';
import { waitForEndpoint } from '../utils/network';

export async function startUIServices(options = {}) {
  const config = {
    port: options.port || 3001,
    backendEndpoints: options.backendEndpoints || { api: 'http://localhost:4000' },
    environment: options.environment || 'test',
  };
  
  // Start UI server with test configuration
  const uiProcess = spawn('npm', ['run', 'start:test'], {
    cwd: '../ui',
    env: {
      ...process.env,
      NODE_ENV: 'test',
      PORT: config.port.toString(),
      API_URL: config.backendEndpoints.api,
    },
  });
  
  uiProcess.stdout.on('data', (data) => {
    console.log(`UI: ${data}`);
  });
  
  // Wait for UI server to be ready
  await waitForEndpoint(`http://localhost:${config.port}/health`, 30000);
  
  return {
    process: uiProcess,
    endpoints: {
      ui: `http://localhost:${config.port}`,
    },
    shutdown: () => {
      return new Promise((resolve) => {
        uiProcess.on('close', resolve);
        uiProcess.kill();
      });
    },
  };
}
```

### Frontend Service Configuration

The frontend service is configured to connect to both the backend and UI services:

```typescript
// tests/integration/services/frontend.ts
import { spawn } from 'child_process';
import { waitForEndpoint } from '../utils/network';

export async function startFrontendServices(options = {}) {
  const config = {
    port: options.port || 3000,
    backendEndpoints: options.backendEndpoints || { api: 'http://localhost:4000' },
    uiEndpoints: options.uiEndpoints || { ui: 'http://localhost:3001' },
    environment: options.environment || 'test',
  };
  
  // Create temporary .env.test file
  const envContent = `
NEXT_PUBLIC_API_URL=${config.backendEndpoints.api}
NEXT_PUBLIC_UI_URL=${config.uiEndpoints.ui}
NEXT_PUBLIC_ENVIRONMENT=test
`;
  
  // Write to temporary .env.test file
  // ...
  
  // Start frontend server with test configuration
  const frontendProcess = spawn('npm', ['run', 'dev'], {
    cwd: './',
    env: {
      ...process.env,
      NODE_ENV: 'test',
      PORT: config.port.toString(),
    },
  });
  
  frontendProcess.stdout.on('data', (data) => {
    console.log(`Frontend: ${data}`);
  });
  
  // Wait for frontend server to be ready
  await waitForEndpoint(`http://localhost:${config.port}/api/health`, 30000);
  
  return {
    process: frontendProcess,
    shutdown: () => {
      return new Promise((resolve) => {
        frontendProcess.on('close', resolve);
        frontendProcess.kill();
      });
    },
  };
}
```

## Environment Variables

The integrated test environment uses a centralized environment variable management system:

```typescript
// tests/integration/utils/env.ts
import dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';

export function loadTestEnvironment() {
  // Load environment-specific variables
  const envFiles = [
    '.env.test.local', // Local overrides
    '.env.test',       // Test environment defaults
    '.env',            // Global defaults
  ];
  
  for (const file of envFiles) {
    const filePath = path.resolve(process.cwd(), file);
    if (fs.existsSync(filePath)) {
      const result = dotenv.config({ path: filePath });
      if (result.error) {
        console.error(`Error loading environment from ${file}:`, result.error);
      }
    }
  }
  
  // Validate required variables
  const requiredVars = [
    'API_URL',
    'MONGODB_URI',
  ];
  
  const missing = requiredVars.filter(name => !process.env[name]);
  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }
  
  return process.env;
}

// Usage in test runner
export function getIntegrationConfig() {
  const env = loadTestEnvironment();
  
  return {
    backend: {
      port: parseInt(env.API_PORT || '4000', 10),
      dbUri: env.MONGODB_URI,
    },
    ui: {
      port: parseInt(env.UI_PORT || '3001', 10),
    },
    frontend: {
      port: parseInt(env.FRONTEND_PORT || '3000', 10),
    },
  };
}
```

## Health Check System

The health check system ensures all services are running correctly before tests begin:

```typescript
// tests/integration/utils/health-check.ts
import fetch from 'node-fetch';

// Health check service with retry logic
export async function checkEndpoint(url, maxRetries = 5, retryInterval = 2000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return true;
      }
      console.log(`Health check failed for ${url}, status: ${response.status}, retrying...`);
    } catch (error) {
      console.log(`Health check error for ${url}: ${error.message}, retrying...`);
    }
    
    // Wait before retry
    await new Promise(resolve => setTimeout(resolve, retryInterval));
  }
  
  throw new Error(`Health check failed for ${url} after ${maxRetries} attempts`);
}

// Check all services
export async function healthCheck(backendConfig, uiConfig) {
  console.log('Running health checks...');
  
  const checks = [
    checkEndpoint(`${backendConfig.endpoints.api}/health`),
    checkEndpoint(`${uiConfig.endpoints.ui}/health`),
    checkEndpoint('http://localhost:3000/api/health'),
  ];
  
  try {
    await Promise.all(checks);
    console.log('All services are healthy');
    return true;
  } catch (error) {
    console.error('Health check failed:', error.message);
    throw error;
  }
}
```

## Test Data Seeding

The test data seeding mechanism provides consistent data for tests:

```typescript
// tests/integration/utils/seed-data.ts
import mongoose from 'mongoose';
import { loadTestEnvironment } from './env';

// Sample test data
const testData = {
  users: [
    {
      _id: 'user1',
      name: 'Test User',
      email: 'test@example.com',
      password: 'hashedpassword123',
    },
    // Additional users...
  ],
  chatSessions: [
    {
      _id: 'session1',
      userId: 'user1',
      title: 'Test Session',
      messages: [
        {
          type: 'user',
          content: 'Hello KAI',
          timestamp: new Date().toISOString(),
        },
        {
          type: 'ai',
          content: 'Hello! How can I assist you today?',
          timestamp: new Date().toISOString(),
        },
      ],
    },
    // Additional sessions...
  ],
  // Other collections...
};

// Seed database with test data
export async function seedTestData() {
  const env = loadTestEnvironment();
  
  try {
    // Connect to test database
    await mongoose.connect(env.MONGODB_URI);
    
    // Clear existing data
    const collections = Object.keys(mongoose.connection.collections);
    for (const collection of collections) {
      await mongoose.connection.collections[collection].deleteMany({});
    }
    
    // Insert test data
    for (const [collection, documents] of Object.entries(testData)) {
      if (documents.length > 0) {
        await mongoose.connection.collection(collection).insertMany(documents);
        console.log(`Seeded ${documents.length} documents to ${collection}`);
      }
    }
    
    console.log('Test data seeding complete');
  } catch (error) {
    console.error('Error seeding test data:', error);
    throw error;
  } finally {
    await mongoose.disconnect();
  }
}

// Clean up test data after tests
export async function cleanupTestData() {
  const env = loadTestEnvironment();
  
  try {
    await mongoose.connect(env.MONGODB_URI);
    
    const collections = Object.keys(mongoose.connection.collections);
    for (const collection of collections) {
      await mongoose.connection.collections[collection].deleteMany({});
    }
    
    console.log('Test data cleanup complete');
  } catch (error) {
    console.error('Error cleaning up test data:', error);
  } finally {
    await mongoose.disconnect();
  }
}
```

## End-to-End Testing

### BDD Test Implementation

The end-to-end tests use Cucumber.js for BDD-style testing:

```gherkin
# tests/features/integration/chat.feature
Feature: Chat Integration
  As a user of the KAI application
  I want to send messages in a chat session
  So that I can interact with the AI assistant

  Background:
    Given I am logged in as a test user
    And I have an active chat session

  Scenario: Send a message using the frontend
    When I type "Hello KAI" in the chat input
    And I submit the message
    Then I should see my message in the chat history
    And I should receive a response from KAI

  Scenario: Chat session persists between page reloads
    When I send several messages in a chat session
    And I reload the page
    Then I should see my previous messages
    And the chat session should maintain continuity

  Scenario: Attachments are properly handled
    When I attach a file to my message
    And I submit the message with the attachment
    Then the attachment should be uploaded successfully
    And the message with attachment should appear in the chat history
```

### Test Step Implementation

The test steps are implemented using Playwright for browser automation:

```typescript
// tests/steps/integration/chat.steps.ts
import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { getPage } from '../support/browser';

Given('I am logged in as a test user', async function() {
  const page = getPage();
  await page.goto('/login');
  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await page.waitForURL('/dashboard');
});

Given('I have an active chat session', async function() {
  const page = getPage();
  await page.goto('/chat');
  // Start new session or select existing one
  if (await page.isVisible('text="Start New Chat"')) {
    await page.click('text="Start New Chat"');
  } else {
    await page.click('.chat-session-item:first-child');
  }
  // Wait for chat interface to load
  await page.waitForSelector('.chat-container');
});

When('I type {string} in the chat input', async function(message) {
  const page = getPage();
  await page.fill('.chat-input textarea', message);
});

When('I submit the message', async function() {
  const page = getPage();
  await page.click('button.send-button');
  // Store the message for later verification
  this.lastMessage = await page.$eval('.chat-input textarea', el => el.value);
  // Wait for message to appear in history
  await page.waitForSelector(`.user-message:has-text("${this.lastMessage}")`);
});

Then('I should see my message in the chat history', async function() {
  const page = getPage();
  const messageVisible = await page.isVisible(`.user-message:has-text("${this.lastMessage}")`);
  expect(messageVisible).toBe(true);
});

Then('I should receive a response from KAI', async function() {
  const page = getPage();
  // Wait for AI response with timeout
  await page.waitForSelector('.ai-message', { timeout: 10000 });
  const hasResponse = await page.isVisible('.ai-message');
  expect(hasResponse).toBe(true);
});

// Additional step implementations for the other scenarios...
```

### Running End-to-End Tests

The end-to-end tests can be run with:

```bash
# Start services and run tests
npm run test:integration

# With specific tags
npm run test:integration -- --tags @critical
```

## Troubleshooting

### Common Issues

1. **Services don't start properly**
   - Check individual service logs with `docker-compose logs [service-name]`
   - Verify port availability on your system
   - Ensure database connection is properly configured

2. **Tests fail intermittently**
   - Check for race conditions in test setup
   - Increase timeouts for network operations
   - Ensure test data is properly isolated between runs

3. **Environment variable issues**
   - Verify .env files are properly configured
   - Check for typos in variable names
   - Ensure variables are properly passed to containerized services

### Viewing Logs

To view logs for troubleshooting:

```bash
# All service logs
docker-compose -f docker-compose.test.yml logs

# Specific service logs
docker-compose -f docker-compose.test.yml logs kai-api

# Follow logs in real-time
docker-compose -f docker-compose.test.yml logs -f
```

### Manual Service Testing

To manually test services:

```bash
# Enter a service container
docker-compose -f docker-compose.test.yml exec kai-api bash

# Run manual tests
curl http://localhost:4000/health
```

## Conclusion

The KAI Integrated Testing Environment provides a comprehensive framework for testing all components of the application together. By using containerization, centralized configuration, and automated setup, we ensure consistent and reliable testing across environments. The BDD approach enables clear specification of expected behavior and facilitates communication between technical and non-technical stakeholders. 