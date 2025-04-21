import { Given, When, Then, Before, After } from '@cucumber/cucumber';
import { expect } from 'chai';
import { compare } from 'bcrypt';
import mongoose from 'mongoose';
import { MongoMemoryServer } from 'mongodb-memory-server';

// Import the user management system
import { 
  UserService, 
  MongoUserRepository, 
  UserProfileDTO,
  UserPreferences,
  getUserModel
} from '../../../../src';

// Test context to share data between steps
interface TestContext {
  mongoServer?: MongoMemoryServer;
  userService?: UserService;
  userRepository?: MongoUserRepository;
  User?: ReturnType<typeof getUserModel>;
  registeredUser?: UserProfileDTO;
  authenticatedUser?: UserProfileDTO;
  authenticatedUserId?: string;
  updatedProfile?: UserProfileDTO;
  userPreferences?: UserPreferences;
  searchResults?: UserProfileDTO[];
  passwordChangeResult?: boolean;
  emailChangeResult?: boolean;
  linkResult?: boolean;
}

const testContext: TestContext = {};

// Before each scenario
Before(async function() {
  // Start an in-memory MongoDB server
  testContext.mongoServer = await MongoMemoryServer.create();
  const uri = testContext.mongoServer.getUri();
  
  // Connect mongoose to the in-memory server
  await mongoose.connect(uri);
  
  // Initialize repository and service
  testContext.User = getUserModel();
  testContext.userRepository = new MongoUserRepository();
  testContext.userService = new UserService(testContext.userRepository);
});

// After each scenario
After(async function() {
  // Clean up after tests
  if (mongoose.connection.readyState !== 0) {
    await mongoose.connection.dropDatabase();
    await mongoose.connection.close();
  }
  
  if (testContext.mongoServer) {
    await testContext.mongoServer.stop();
  }
});

// Background steps
Given('the user management system is initialized', function() {
  expect(testContext.userService).to.exist;
  expect(testContext.userRepository).to.exist;
});

Given('the database is connected', function() {
  expect(mongoose.connection.readyState).to.equal(1);
});

// User Registration
When('a user registers with name {string}, email {string}, and password {string}', async function(name, email, password) {
  testContext.registeredUser = await testContext.userService!.register({
    name,
    email,
    role: 'student'
  }, password);
});

Then('the registration should be successful', function() {
  expect(testContext.registeredUser).to.exist;
  expect(testContext.registeredUser!.id).to.exist;
});

Then('the user should be stored in the database', async function() {
  const user = await testContext.User!.findById(testContext.registeredUser!.id);
  expect(user).to.exist;
  expect(user!.email).to.equal(testContext.registeredUser!.email);
});

Then('the password should be securely hashed', async function() {
  const user = await testContext.User!.findById(testContext.registeredUser!.id);
  expect(user!.password).to.exist;
  expect(user!.password).not.to.equal('SecurePass123');
  // Should be a bcrypt hash
  expect(user!.password).to.match(/^\$2[abxy]\$\d+\$/);
});

// User Login
Given('a user exists with email {string} and password {string}', async function(email, password) {
  // Register a user for login tests
  testContext.registeredUser = await testContext.userService!.register({
    name: 'Test User',
    email,
    role: 'student'
  }, password);
});

When('the user attempts to login with email {string} and password {string}', async function(email, password) {
  testContext.authenticatedUser = await testContext.userService!.authenticate(email, password);
});

Then('the login should be successful', function() {
  expect(testContext.authenticatedUser).to.exist;
});

Then('the user profile should be returned', function() {
  expect(testContext.authenticatedUser!.id).to.equal(testContext.registeredUser!.id);
  expect(testContext.authenticatedUser!.email).to.equal(testContext.registeredUser!.email);
});

Then('the login should fail', function() {
  expect(testContext.authenticatedUser).to.be.null;
});

// User Profile
Given('a user is authenticated with ID {string}', async function(userId) {
  // Create a test user
  const user = new testContext.User!({
    _id: userId,
    name: 'Test Authenticated User',
    email: 'authenticated@example.com',
    password: '$2b$12$T7CD3.9T0O25k7tIzF8EWus6W2jMzr.lMvn9WRJLdAZDlr8fzKMYe', // hashed 'OldPass123'
    role: 'student',
    preferences: {
      theme: 'light',
      emailNotifications: true,
      language: 'en'
    }
  });
  
  await user.save();
  testContext.authenticatedUserId = userId;
});

When('the user updates their profile with name {string}', async function(name) {
  testContext.updatedProfile = await testContext.userService!.updateProfile(
    testContext.authenticatedUserId!,
    { name }
  );
});

Then('the profile should be updated in the database', async function() {
  const user = await testContext.User!.findById(testContext.authenticatedUserId);
  expect(user).to.exist;
  expect(user!.name).to.equal(testContext.updatedProfile!.name);
});

Then('the updated profile should be returned', function() {
  expect(testContext.updatedProfile).to.exist;
  expect(testContext.updatedProfile!.id).to.equal(testContext.authenticatedUserId);
});

// User Preferences
When('the user requests their preferences', async function() {
  testContext.userPreferences = await testContext.userService!.getPreferences(
    testContext.authenticatedUserId!
  );
});

Then('the preferences should be returned', function() {
  expect(testContext.userPreferences).to.exist;
  expect(testContext.userPreferences!.theme).to.equal('light');
});

When('the user updates their preferences with theme {string}', async function(theme) {
  testContext.userPreferences = await testContext.userService!.updatePreferences(
    testContext.authenticatedUserId!,
    { theme: theme as any }
  );
});

Then('the preferences should be updated in the database', async function() {
  const user = await testContext.User!.findById(testContext.authenticatedUserId);
  expect(user).to.exist;
  expect(user!.preferences?.theme).to.equal('dark');
});

Then('the updated preferences should be returned', function() {
  expect(testContext.userPreferences).to.exist;
  expect(testContext.userPreferences!.theme).to.equal('dark');
});

// Password Change
When('the user changes their password from {string} to {string}', async function(oldPassword, newPassword) {
  testContext.passwordChangeResult = await testContext.userService!.changePassword(
    testContext.authenticatedUserId!,
    oldPassword,
    newPassword
  );
});

Then('the password change should be successful', function() {
  expect(testContext.passwordChangeResult).to.be.true;
});

Then('the new password should be securely hashed', async function() {
  const user = await testContext.User!.findById(testContext.authenticatedUserId);
  expect(user).to.exist;
  
  // Verify new password works
  const passwordValid = await compare('NewPass456', user!.password!);
  expect(passwordValid).to.be.true;
});

// Email Change
When('the user changes their email to {string} with password {string}', async function(newEmail, password) {
  // First update the password to match what we're testing with
  const user = await testContext.User!.findById(testContext.authenticatedUserId);
  user!.password = '$2b$12$T7CD3.9T0O25k7tIzF8EWus6W2jMzr.lMvn9WRJLdAZDlr8fzKMYe'; // hashed 'SecurePass123'
  await user!.save();
  
  testContext.emailChangeResult = await testContext.userService!.changeEmail(
    testContext.authenticatedUserId!,
    newEmail,
    password
  );
});

Then('the email change should be successful', function() {
  expect(testContext.emailChangeResult).to.be.true;
});

Then('the user should have the new email in the database', async function() {
  const user = await testContext.User!.findById(testContext.authenticatedUserId);
  expect(user).to.exist;
  expect(user!.email).to.equal('newemail@example.com');
});

// Link Accounts
Given('a parent user exists with ID {string}', async function(parentId) {
  const parent = new testContext.User!({
    _id: parentId,
    name: 'Parent User',
    email: 'parent@example.com',
    password: 'hashedPassword',
    role: 'parent',
    studentIds: []
  });
  
  await parent.save();
});

Given('a student user exists with ID {string}', async function(studentId) {
  const student = new testContext.User!({
    _id: studentId,
    name: 'Student User',
    email: 'student@example.com',
    password: 'hashedPassword',
    role: 'student',
    parentIds: []
  });
  
  await student.save();
});

When('the parent links the student account', async function() {
  testContext.linkResult = await testContext.userService!.linkAccounts(
    'parent123',
    'student456',
    'student'
  );
});

Then('the accounts should be linked in the database', function() {
  expect(testContext.linkResult).to.be.true;
});

Then('the student should appear in the parent\'s student list', async function() {
  const parent = await testContext.User!.findById('parent123');
  expect(parent).to.exist;
  expect(parent!.studentIds).to.have.length(1);
  expect(parent!.studentIds![0].toString()).to.equal('student456');
});

Then('the parent should appear in the student\'s parent list', async function() {
  const student = await testContext.User!.findById('student456');
  expect(student).to.exist;
  expect(student!.parentIds).to.have.length(1);
  expect(student!.parentIds![0].toString()).to.equal('parent123');
});

// Search for Users
Given('multiple users exist in the system', async function() {
  // Create multiple users for search testing
  await testContext.User!.create([
    {
      name: 'John Smith',
      email: 'john@example.com',
      password: 'hashedPassword',
      role: 'student'
    },
    {
      name: 'Jane Doe',
      email: 'jane@example.com',
      password: 'hashedPassword',
      role: 'student'
    },
    {
      name: 'Robert Johnson',
      email: 'robert@example.com',
      password: 'hashedPassword',
      role: 'parent'
    },
    {
      name: 'Sarah Williams',
      email: 'johnswife@example.com',
      password: 'hashedPassword',
      role: 'parent'
    }
  ]);
});

When('a user searches for {string}', async function(query) {
  // Create a search user
  const searchUser = new testContext.User!({
    _id: 'searchuser123',
    name: 'Search User',
    email: 'search@example.com',
    password: 'hashedPassword',
    role: 'student'
  });
  await searchUser.save();
  
  testContext.searchResults = await testContext.userService!.searchUsers(query, 'searchuser123');
});

Then('the search results should include users with {string} in their name or email', function(query) {
  expect(testContext.searchResults).to.exist;
  expect(testContext.searchResults!.length).to.be.at.least(1);
  
  // Check if all results contain the query
  const containsQuery = testContext.searchResults!.every(user => 
    user.name!.toLowerCase().includes(query.toLowerCase()) || 
    user.email!.toLowerCase().includes(query.toLowerCase())
  );
  
  expect(containsQuery).to.be.true;
});

Then('the search results should not include the searching user', function() {
  const searchUserInResults = testContext.searchResults!.some(user => 
    user.id === 'searchuser123'
  );
  
  expect(searchUserInResults).to.be.false;
}); 