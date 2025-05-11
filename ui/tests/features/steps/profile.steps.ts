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
  profilePicture?: string;
  bio?: string;
  phone?: string;
  address?: string;
  preferences?: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    notifications: boolean;
    privacyLevel: 'public' | 'private' | 'contacts';
  };
}

interface ProfileUpdateData {
  firstName?: string;
  lastName?: string;
  bio?: string;
  phone?: string;
  address?: string;
}

interface EmailChangeRequest {
  newEmail: string;
  password: string;
}

// Mock user service with profile management capabilities
class MockUserProfileService {
  private users: User[] = [
    {
      id: '1',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      role: 'STUDENT',
      isVerified: true,
      bio: 'This is a test user',
      phone: '123-456-7890',
      preferences: {
        theme: 'dark',
        language: 'en',
        notifications: true,
        privacyLevel: 'public'
      }
    }
  ];
  
  private currentUser: User | null = this.users[0]; // For testing, we'll assume the user is logged in
  private pendingEmailChanges: Map<string, string> = new Map(); // userId -> newEmail
  
  async getCurrentUser(): Promise<User | null> {
    return this.currentUser;
  }
  
  async updateProfile(userId: string, data: ProfileUpdateData): Promise<User> {
    const user = this.users.find(u => u.id === userId);
    if (!user) {
      throw new Error('User not found');
    }
    
    // Update user profile
    Object.assign(user, data);
    
    // If this is the current user, update that reference too
    if (this.currentUser && this.currentUser.id === userId) {
      this.currentUser = user;
    }
    
    return user;
  }
  
  async uploadProfilePicture(userId: string, file: any): Promise<User> {
    const user = this.users.find(u => u.id === userId);
    if (!user) {
      throw new Error('User not found');
    }
    
    // In a real implementation, we would handle file upload
    // Here we just simulate updating the profile picture URL
    user.profilePicture = `https://example.com/profiles/${userId}/avatar.jpg`;
    
    // If this is the current user, update that reference too
    if (this.currentUser && this.currentUser.id === userId) {
      this.currentUser = user;
    }
    
    return user;
  }
  
  getProfileCompleteness(user: User): number {
    // Calculate profile completeness as a percentage
    let fields = 0;
    let completedFields = 0;
    
    // Basic fields (always counted)
    fields += 4; // id, email, firstName, lastName
    completedFields += 4; // These are required fields
    
    // Optional fields
    if (user.profilePicture) { fields++; completedFields++; }
    if (user.bio) { fields++; completedFields++; }
    if (user.phone) { fields++; completedFields++; }
    if (user.address) { fields++; completedFields++; }
    
    // Preferences
    if (user.preferences) {
      fields += 4; // theme, language, notifications, privacyLevel
      if (user.preferences.theme) completedFields++;
      if (user.preferences.language) completedFields++;
      if (user.preferences.notifications !== undefined) completedFields++;
      if (user.preferences.privacyLevel) completedFields++;
    }
    
    return Math.round((completedFields / fields) * 100);
  }
  
  async requestEmailChange(userId: string, data: EmailChangeRequest): Promise<boolean> {
    const user = this.users.find(u => u.id === userId);
    if (!user) {
      throw new Error('User not found');
    }
    
    // In a real implementation, we would verify the password
    // Here we just simulate the email change request
    this.pendingEmailChanges.set(userId, data.newEmail);
    
    return true;
  }
  
  async verifyEmailChange(userId: string, token: string): Promise<boolean> {
    const user = this.users.find(u => u.id === userId);
    if (!user) {
      throw new Error('User not found');
    }
    
    const newEmail = this.pendingEmailChanges.get(userId);
    if (!newEmail) {
      throw new Error('No pending email change');
    }
    
    // In a real implementation, we would verify the token
    // Here we just simulate the email change
    user.email = newEmail;
    this.pendingEmailChanges.delete(userId);
    
    // If this is the current user, update that reference too
    if (this.currentUser && this.currentUser.id === userId) {
      this.currentUser = user;
    }
    
    return true;
  }
  
  async updatePreferences(userId: string, preferences: Partial<User['preferences']>): Promise<User> {
    const user = this.users.find(u => u.id === userId);
    if (!user) {
      throw new Error('User not found');
    }
    
    // Ensure preferences object exists
    if (!user.preferences) {
      user.preferences = {
        theme: 'system',
        language: 'en',
        notifications: true,
        privacyLevel: 'public'
      };
    }
    
    // Update preferences
    user.preferences = {
      ...user.preferences,
      ...preferences
    };
    
    // If this is the current user, update that reference too
    if (this.currentUser && this.currentUser.id === userId) {
      this.currentUser = user;
    }
    
    return user;
  }
  
  async exportProfileData(userId: string, format: 'json' | 'csv' = 'json'): Promise<any> {
    const user = this.users.find(u => u.id === userId);
    if (!user) {
      throw new Error('User not found');
    }
    
    // In a real implementation, we would format the data based on the requested format
    // Here we just return the user object
    return user;
  }
}

// Mocked services for testing
const mockUserProfileService = new MockUserProfileService();

// State variables
let currentPage: string;
let currentUser: User | null = null;
let profileUpdateData: ProfileUpdateData = {};
let newProfilePicture: any = null;
let newEmail: string = '';
let emailChangeToken: string = '';
let profileCompleteness: number = 0;
let themePreference: 'light' | 'dark' | 'system' = 'system';
let exportFormat: 'json' | 'csv' = 'json';
let exportedData: any = null;
let success: boolean = false;
let error: string | null = null;

// Helper functions
async function getCurrentUser() {
  return await mockUserProfileService.getCurrentUser();
}

// Given steps
Given('I am logged in as a user', async function () {
  currentUser = await getCurrentUser();
  expect(currentUser).to.not.be.null;
});

// When steps
When('I navigate to the profile page', function () {
  currentPage = '/profile';
});

When('I navigate to the preferences page', function () {
  currentPage = '/profile/preferences';
});

When('I update my profile information', function () {
  profileUpdateData = {
    firstName: 'Updated',
    lastName: 'User',
    bio: 'This is an updated bio',
    phone: '987-654-3210'
  };
});

When('I save my changes', async function () {
  try {
    if (!currentUser) {
      throw new Error('User not logged in');
    }
    
    await mockUserProfileService.updateProfile(currentUser.id, profileUpdateData);
    success = true;
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to update profile';
    success = false;
  }
});

When('I upload a new profile picture', async function () {
  try {
    if (!currentUser) {
      throw new Error('User not logged in');
    }
    
    // Mock a file object
    newProfilePicture = {
      name: 'profile.jpg',
      type: 'image/jpeg',
      size: 1024 * 50 // 50KB
    };
    
    await mockUserProfileService.uploadProfilePicture(currentUser.id, newProfilePicture);
    success = true;
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to upload profile picture';
    success = false;
  }
});

When('I change my email address', async function () {
  try {
    if (!currentUser) {
      throw new Error('User not logged in');
    }
    
    newEmail = 'newemail@example.com';
    
    await mockUserProfileService.requestEmailChange(currentUser.id, {
      newEmail,
      password: 'Password123!' // Mock password
    });
    
    // Simulate receiving a verification token
    emailChangeToken = 'mock-email-change-token-12345';
    
    success = true;
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to request email change';
    success = false;
  }
});

When('I change my theme preference', async function () {
  try {
    if (!currentUser) {
      throw new Error('User not logged in');
    }
    
    // Toggle the theme preference
    themePreference = currentUser.preferences?.theme === 'dark' ? 'light' : 'dark';
    
    await mockUserProfileService.updatePreferences(currentUser.id, {
      theme: themePreference
    });
    
    success = true;
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to update theme preference';
    success = false;
  }
});

When('I request a profile data export', async function () {
  try {
    if (!currentUser) {
      throw new Error('User not logged in');
    }
    
    exportFormat = 'json'; // Default format
    exportedData = await mockUserProfileService.exportProfileData(currentUser.id, exportFormat);
    
    success = true;
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to export profile data';
    success = false;
  }
});

// Then steps
Then('I should see my profile information', async function () {
  const user = await getCurrentUser();
  expect(user).to.not.be.null;
  expect(user?.firstName).to.equal('Test');
  expect(user?.lastName).to.equal('User');
});

Then('my profile should be updated successfully', async function () {
  expect(success).to.be.true;
  
  const user = await getCurrentUser();
  expect(user?.firstName).to.equal(profileUpdateData.firstName);
  expect(user?.lastName).to.equal(profileUpdateData.lastName);
  expect(user?.bio).to.equal(profileUpdateData.bio);
  expect(user?.phone).to.equal(profileUpdateData.phone);
});

Then('my profile picture should be updated', async function () {
  expect(success).to.be.true;
  
  const user = await getCurrentUser();
  expect(user?.profilePicture).to.include('/avatar.jpg');
});

Then('I should see my profile completeness indicator', async function () {
  const user = await getCurrentUser();
  if (user) {
    profileCompleteness = mockUserProfileService.getProfileCompleteness(user);
    expect(profileCompleteness).to.be.a('number');
    expect(profileCompleteness).to.be.at.least(0);
    expect(profileCompleteness).to.be.at.most(100);
  }
});

Then('I should receive a profile email verification', function () {
  expect(success).to.be.true;
  expect(emailChangeToken).to.not.be.empty;
});

Then('my email should be updated after verification', async function () {
  try {
    if (!currentUser) {
      throw new Error('User not logged in');
    }
    
    await mockUserProfileService.verifyEmailChange(currentUser.id, emailChangeToken);
    
    const user = await getCurrentUser();
    expect(user?.email).to.equal(newEmail);
  } catch (err) {
    throw new Error(`Failed to verify email change: ${err instanceof Error ? err.message : err}`);
  }
});

Then('my theme settings should be updated', async function () {
  expect(success).to.be.true;
  
  const user = await getCurrentUser();
  expect(user?.preferences?.theme).to.equal(themePreference);
});

Then('I should receive my profile data in the requested format', function () {
  expect(success).to.be.true;
  expect(exportedData).to.not.be.null;
  
  // In a real test, we would check that the exported data matches the expected format
  // Here we just check that we have the basic user fields
  expect(exportedData.id).to.not.be.undefined;
  expect(exportedData.email).to.not.be.undefined;
  expect(exportedData.firstName).to.not.be.undefined;
  expect(exportedData.lastName).to.not.be.undefined;
}); 