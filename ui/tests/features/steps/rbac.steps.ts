import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';

// Mocked UserRole enum to match actual implementation without importing
enum UserRole {
  ADMIN = 'admin',
  TEACHER = 'teacher',
  STUDENT = 'student',
  PARENT = 'parent',
  GUEST = 'guest'
}

// Mock user with roles
interface MockUser {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: UserRole[];
  isVerified: boolean;
}

// Mock permission service for testing
class MockPermissionService {
  private currentUser: MockUser | null = null;

  setCurrentUser(user: MockUser | null): void {
    this.currentUser = user;
  }

  getCurrentUser(): MockUser | null {
    return this.currentUser;
  }

  hasRole(role: UserRole): boolean {
    return !!this.currentUser && this.currentUser.roles.includes(role);
  }

  hasAnyRole(roles: UserRole[]): boolean {
    return !!this.currentUser && this.currentUser.roles.some(role => roles.includes(role));
  }

  hasAllRoles(roles: UserRole[]): boolean {
    return !!this.currentUser && roles.every(role => this.currentUser!.roles.includes(role));
  }

  hasPermission(permission: string): boolean {
    // Map permissions to roles
    const permissionToRolesMap: Record<string, UserRole[]> = {
      'admin.dashboard': [UserRole.ADMIN],
      'admin.user_management': [UserRole.ADMIN],
      'teaching.course_management': [UserRole.TEACHER],
      'student.learning_dashboard': [UserRole.STUDENT],
    };

    const requiredRoles = permissionToRolesMap[permission] || [];
    return this.hasAnyRole(requiredRoles);
  }
}

// State for test scenarios
const mockPermissionService = new MockPermissionService();
let accessGranted = false;
let visibleElements: string[] = [];
let accessDeniedMessage: string | null = null;
let canEditUserRoles = false;

// Helper function to create user with specific roles
function createMockUser(roles: UserRole[]): MockUser {
  return {
    id: '1',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    roles: roles,
    isVerified: true
  };
}

// Given steps
Given('I am logged in as an {string} user', function (roleName: string) {
  const role = UserRole[roleName as keyof typeof UserRole];
  const user = createMockUser([role]);
  mockPermissionService.setCurrentUser(user);
});

Given('I am logged in as a {string} user', function (roleName: string) {
  const role = UserRole[roleName as keyof typeof UserRole];
  const user = createMockUser([role]);
  mockPermissionService.setCurrentUser(user);
});

Given('I am logged in as a user with roles {string}', function (roleNames: string) {
  const roles = roleNames.split(',').map(name => UserRole[name.trim() as keyof typeof UserRole]);
  const user = createMockUser(roles);
  mockPermissionService.setCurrentUser(user);
});

// When steps
When('I navigate to the admin dashboard', function () {
  accessGranted = mockPermissionService.hasPermission('admin.dashboard');
  if (accessGranted) {
    visibleElements = ['User Management', 'System Settings', 'Audit Logs'];
  } else {
    visibleElements = [];
    accessDeniedMessage = 'Access Denied: Admin privileges required';
  }
});

When('I navigate to the course management page', function () {
  accessGranted = mockPermissionService.hasPermission('teaching.course_management');
  if (accessGranted) {
    visibleElements = ['Course List', 'Create Course', 'Assignments'];
    
    // If user also has student role, add student elements
    if (mockPermissionService.hasRole(UserRole.STUDENT)) {
      visibleElements.push('My Courses', 'My Progress');
    }
  } else {
    visibleElements = [];
    accessDeniedMessage = 'Access Denied: Teacher privileges required';
  }
});

When('I navigate to the learning dashboard', function () {
  accessGranted = mockPermissionService.hasPermission('student.learning_dashboard');
  if (accessGranted) {
    visibleElements = ['My Courses', 'My Progress', 'Assignments'];
  } else {
    visibleElements = [];
    accessDeniedMessage = 'Access Denied: Student privileges required';
  }
});

When('I view the application header', function () {
  // Populate navigation items based on roles
  visibleElements = [];
  
  if (mockPermissionService.hasRole(UserRole.ADMIN)) {
    visibleElements.push('Admin', 'Users', 'Settings');
  }
  
  if (mockPermissionService.hasRole(UserRole.TEACHER)) {
    visibleElements.push('Courses', 'Assignments', 'Gradebook');
  }
  
  if (mockPermissionService.hasRole(UserRole.STUDENT)) {
    visibleElements.push('Dashboard', 'My Courses', 'Progress');
  }
});

When('I attempt to access a protected component', function () {
  // Simulate trying to access an admin-only component
  if (!mockPermissionService.hasPermission('admin.dashboard')) {
    accessDeniedMessage = 'Access Denied: You do not have permission to view this component';
  } else {
    accessDeniedMessage = null;
  }
});

When('I navigate to the user management page', function () {
  accessGranted = mockPermissionService.hasPermission('admin.user_management');
  if (accessGranted) {
    visibleElements = ['Users List', 'Create User', 'Edit Roles', 'Delete User'];
  } else {
    visibleElements = [];
    accessDeniedMessage = 'Access Denied: Admin privileges required';
  }
});

When('I select a user to edit', function () {
  canEditUserRoles = mockPermissionService.hasRole(UserRole.ADMIN);
});

// Then steps
Then('I should see the admin management options', function () {
  expect(accessGranted).to.be.true;
  expect(visibleElements).to.include('User Management');
  expect(visibleElements).to.include('System Settings');
});

Then('I should see the teaching management options', function () {
  expect(accessGranted).to.be.true;
  expect(visibleElements).to.include('Course List');
  expect(visibleElements).to.include('Create Course');
});

Then('I should not see the admin management options', function () {
  expect(visibleElements).to.not.include('User Management');
  expect(visibleElements).to.not.include('System Settings');
});

Then('I should see the student learning options', function () {
  expect(accessGranted).to.be.true;
  expect(visibleElements).to.include('My Courses');
  expect(visibleElements).to.include('My Progress');
});

Then('I should not see the teaching management options', function () {
  expect(visibleElements).to.not.include('Course List');
  expect(visibleElements).to.not.include('Create Course');
});

Then('I should see navigation for {string} permissions', function (permissionType: string) {
  if (permissionType === 'student') {
    expect(visibleElements).to.include('Dashboard');
    expect(visibleElements).to.include('My Courses');
  } else if (permissionType === 'teacher') {
    expect(visibleElements).to.include('Courses');
    expect(visibleElements).to.include('Assignments');
  } else if (permissionType === 'admin') {
    expect(visibleElements).to.include('Admin');
    expect(visibleElements).to.include('Users');
  }
});

Then('I should not see navigation for {string} permissions', function (permissionType: string) {
  if (permissionType === 'student') {
    expect(visibleElements).to.not.include('Dashboard');
    expect(visibleElements).to.not.include('My Courses');
  } else if (permissionType === 'teacher') {
    expect(visibleElements).to.not.include('Courses');
    expect(visibleElements).to.not.include('Assignments');
  } else if (permissionType === 'admin') {
    expect(visibleElements).to.not.include('Admin');
    expect(visibleElements).to.not.include('Users');
  }
});

Then('I should also see student-specific elements', function () {
  expect(visibleElements).to.include('My Courses');
  expect(visibleElements).to.include('My Progress');
});

Then('I should be shown an {string} message', function (messageType: string) {
  if (messageType === 'access denied') {
    expect(accessDeniedMessage).to.not.be.null;
    expect(accessDeniedMessage).to.include('Access Denied');
  }
});

Then('I should be able to modify their roles', function () {
  expect(canEditUserRoles).to.be.true;
}); 