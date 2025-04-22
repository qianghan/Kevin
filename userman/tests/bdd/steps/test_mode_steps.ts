import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';
import sinon from 'sinon';
import express from 'express';
import request from 'supertest';
import { createUserRouter } from '../../../src/api/user_router';
import { UserService } from '../../../src/services/user_service';

// World context to store state between steps
class TestModeWorld {
  users: Map<string, any> = new Map();
  currentUser: any = null;
  app: express.Application;
  userService: any;
  response: any = null;

  constructor() {
    // Set up mock users
    this.setupUsers();
    
    // Set up Express app with mocked service
    this.setupApp();
  }

  setupUsers() {
    // Admin user
    this.users.set('admin@test.com', {
      id: 'admin-id',
      email: 'admin@test.com',
      name: 'Admin User',
      role: 'admin',
      testMode: false
    });

    // Test users
    this.users.set('test1@test.com', {
      id: 'test1-id',
      email: 'test1@test.com',
      name: 'Test User 1',
      role: 'student',
      testMode: true
    });

    this.users.set('test2@test.com', {
      id: 'test2-id',
      email: 'test2@test.com',
      name: 'Test User 2',
      role: 'parent',
      testMode: true
    });

    // Normal user
    this.users.set('normal@test.com', {
      id: 'normal-id',
      email: 'normal@test.com',
      name: 'Normal User',
      role: 'student',
      testMode: false
    });
  }

  setupApp() {
    // Create Express app
    this.app = express();
    this.app.use(express.json());

    // Create mock service
    this.userService = {
      getAllUsers: sinon.stub().callsFake(() => {
        return Array.from(this.users.values());
      }),
      
      getTestModeUsers: sinon.stub().callsFake(() => {
        return Array.from(this.users.values()).filter(user => user.testMode);
      }),
      
      setTestMode: sinon.stub().callsFake((userId, enabled) => {
        const user = Array.from(this.users.values()).find(u => u.id === userId);
        if (!user) {
          throw new Error('User not found');
        }
        user.testMode = enabled;
        return user;
      }),
      
      getUserByEmail: sinon.stub().callsFake((email) => {
        return this.users.get(email) || null;
      })
    };

    // Mock authentication middleware
    const authMiddleware = (req: any, res: any, next: any) => {
      if (this.currentUser) {
        req.user = this.currentUser;
        req.userId = this.currentUser.id;
      }
      next();
    };

    // Create router with mocked auth
    const router = createUserRouter(this.userService as any);
    
    // Apply middleware for tests
    this.app.use((req, res, next) => {
      authMiddleware(req, res, next);
    });
    
    // Mount router
    this.app.use('/api/user', router);
  }
}

// Register world
Given('the following users exist:', function(dataTable) {
  // Users are already set up in the world constructor
  // This step is primarily for documentation in the feature file
});

Given('I am logged in as {string}', function(email) {
  this.currentUser = this.users.get(email);
  if (!this.currentUser) {
    throw new Error(`User with email ${email} not found`);
  }
});

When('I set test mode to {string} for user {string}', async function(modeStr, email) {
  const enabled = modeStr === 'enabled';
  const targetUser = this.users.get(email);
  
  if (!targetUser) {
    throw new Error(`Target user with email ${email} not found`);
  }
  
  this.response = await request(this.app)
    .post(`/api/user/admin/users/${targetUser.id}/test-mode`)
    .send({ enabled });
});

When('I attempt to set test mode to {string} for user {string}', async function(modeStr, email) {
  const enabled = modeStr === 'enabled';
  const targetUser = this.users.get(email);
  
  if (!targetUser) {
    throw new Error(`Target user with email ${email} not found`);
  }
  
  this.response = await request(this.app)
    .post(`/api/user/admin/users/${targetUser.id}/test-mode`)
    .send({ enabled });
});

When('I view all test mode users', async function() {
  this.response = await request(this.app)
    .get('/api/user/admin/users/test-mode');
});

When('I attempt to view all test mode users', async function() {
  this.response = await request(this.app)
    .get('/api/user/admin/users/test-mode');
});

Then('the user {string} should have test mode enabled', function(email) {
  const user = this.users.get(email);
  expect(user.testMode).to.be.true;
});

Then('the user {string} should have test mode disabled', function(email) {
  const user = this.users.get(email);
  expect(user.testMode).to.be.false;
});

Then('I should see {int} users in the list', function(count) {
  expect(this.response.status).to.equal(200);
  expect(this.response.body.data).to.have.lengthOf(count);
});

Then('I should see {string} in the list', function(email) {
  const found = this.response.body.data.some((user: any) => user.email === email);
  expect(found).to.be.true;
});

Then('I should not see {string} in the list', function(email) {
  const found = this.response.body.data.some((user: any) => user.email === email);
  expect(found).to.be.false;
});

Then('I should be denied access', function() {
  expect(this.response.status).to.equal(403);
}); 