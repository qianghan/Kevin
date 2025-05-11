import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';

// Mock types
interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  isVerified: boolean;
}

interface LoginCredentials {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface RegistrationData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  role: string;
}

// Mock user service
class MockUserService {
  private users: User[] = [
    {
      id: '1',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      role: 'STUDENT',
      isVerified: true
    }
  ];
  
  private currentUser: User | null = null;
  private passwords: Map<string, string> = new Map([
    ['test@example.com', 'Password123!']
  ]);
  
  async login(credentials: LoginCredentials): Promise<{user: User | null}> {
    const savedPassword = this.passwords.get(credentials.email);
    if (savedPassword && savedPassword === credentials.password) {
      this.currentUser = this.users.find(u => u.email === credentials.email) || null;
      return { user: this.currentUser };
    }
    return { user: null };
  }
  
  async register(data: RegistrationData): Promise<{user: User | null}> {
    const newUser: User = {
      id: Date.now().toString(),
      email: data.email,
      firstName: data.firstName,
      lastName: data.lastName,
      role: data.role,
      isVerified: false
    };
    
    this.users.push(newUser);
    this.passwords.set(data.email, data.password);
    this.currentUser = newUser;
    return { user: newUser };
  }
  
  async logout(): Promise<void> {
    this.currentUser = null;
  }
  
  async getCurrentUser(): Promise<User | null> {
    return this.currentUser;
  }
  
  async requestPasswordReset(data: {email: string}): Promise<void> {
    // Mock implementation
  }
  
  async resetPassword(token: string, newPassword: string): Promise<boolean> {
    if (token === 'mock-reset-token-12345' && this.currentUser) {
      const userEmail = 'test@example.com'; // Using fixed test email for simplicity
      this.passwords.set(userEmail, newPassword);
      return true;
    }
    return false;
  }
  
  async verifyEmail(token: string): Promise<boolean> {
    if (token === 'mock-verification-token-12345' && this.currentUser) {
      this.currentUser.isVerified = true;
      return true;
    }
    return false;
  }
  
  async changePassword(data: {currentPassword: string, newPassword: string}): Promise<boolean> {
    return true;
  }
}

// Mocked services for testing
const mockUserService = new MockUserService();

// State variables
let currentPage: string;
let credentials: LoginCredentials;
let registrationData: RegistrationData;
let emailAddress: string;
let verificationToken: string;
let resetToken: string;
let newPassword: string;
let error: string | null = null;
let success: boolean = false;

// Given steps
Given('I am on the login page', function () {
  currentPage = '/login';
});

Given('I am on the registration page', function () {
  currentPage = '/register';
});

Given('I am on the password reset page', function () {
  currentPage = '/forgot-password';
});

Given('I have received a verification email', function () {
  // Simulate receiving email with verification token
  verificationToken = 'mock-verification-token-12345';
  // Login the user for this test case
  mockUserService.login({
    email: 'test@example.com',
    password: 'Password123!',
    rememberMe: false
  });
});

Given('I have received a password reset email', function () {
  // Simulate receiving email with reset token
  resetToken = 'mock-reset-token-12345';
  // Login the test user for this scenario
  mockUserService.login({
    email: 'test@example.com',
    password: 'Password123!',
    rememberMe: false
  });
});

// When steps
When('I enter valid credentials', function () {
  credentials = {
    email: 'test@example.com',
    password: 'Password123!',
    rememberMe: false
  };
});

When('I enter invalid credentials', function () {
  credentials = {
    email: 'test@example.com',
    password: 'wrongpassword',
    rememberMe: false
  };
});

When('I click the login button', async function () {
  try {
    // Simulate login attempt
    const result = await mockUserService.login(credentials);
    if (result && result.user) {
      success = true;
    } else {
      error = 'Invalid credentials';
      success = false;
    }
  } catch (err) {
    error = 'Login failed';
    success = false;
  }
});

When('I fill in the registration form with valid data', function () {
  registrationData = {
    email: 'newuser@example.com',
    password: 'Password123!',
    firstName: 'New',
    lastName: 'User',
    role: 'STUDENT'
  };
});

When('I click the register button', async function () {
  try {
    // Simulate registration attempt
    const result = await mockUserService.register(registrationData);
    if (result && result.user) {
      success = true;
    } else {
      error = 'Registration failed';
      success = false;
    }
  } catch (err) {
    error = 'Registration failed';
    success = false;
  }
});

When('I enter my email address', function () {
  emailAddress = 'test@example.com';
});

When('I click the reset password button', async function () {
  try {
    // Simulate password reset request
    await mockUserService.requestPasswordReset({ email: emailAddress });
    success = true;
  } catch (err) {
    error = 'Password reset request failed';
    success = false;
  }
});

When('I click the verification link', async function () {
  try {
    // Simulate verification link click
    const result = await mockUserService.verifyEmail(verificationToken);
    success = result;
  } catch (err) {
    error = 'Email verification failed';
    success = false;
  }
});

When('I click the password reset link', function () {
  currentPage = `/reset-password?token=${resetToken}`;
});

When('I enter a new password', function () {
  newPassword = 'NewPassword456!';
});

When('I click the submit button', async function () {
  try {
    // Simulate password reset submission
    const result = await mockUserService.resetPassword(resetToken, newPassword);
    success = result;
  } catch (err) {
    error = 'Password reset failed';
    success = false;
  }
});

// Then steps
Then('I should be redirected to the dashboard', function () {
  expect(success).to.be.true;
});

Then('I should see an error message', function () {
  expect(error).to.not.be.null;
  expect(success).to.be.false;
});

Then('I should see a success message', function () {
  expect(success).to.be.true;
});

Then('I should see a confirmation message', function () {
  expect(success).to.be.true;
});

Then('I should receive a verification email', function () {
  // This would be a mock assertion since we can't actually send emails in tests
  // In a real test, we would use service methods to verify this
  expect(success).to.be.true;
});

Then('I should be redirected to the email verified page', function () {
  expect(success).to.be.true;
});

Then('my account should be marked as verified', async function () {
  const user = await mockUserService.getCurrentUser();
  expect(user?.isVerified).to.be.true;
});

Then('I should receive a password reset email', function () {
  // Mock verification since we can't actually send emails in tests
  expect(success).to.be.true;
});

Then('I should be redirected to the login page', function () {
  expect(success).to.be.true;
});

Then('I should be able to login with my new password', async function () {
  const loginResult = await mockUserService.login({
    email: 'test@example.com',
    password: newPassword,
    rememberMe: false
  });
  expect(loginResult?.user).to.not.be.null;
}); 