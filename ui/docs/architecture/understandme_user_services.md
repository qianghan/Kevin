# User Management Service Architecture

This document outlines the user management service architecture for the Kevin application. The architecture follows SOLID principles and demonstrates clean separation of concerns.

## Overview

The user management system is designed to provide a complete set of services for handling authentication, user profiles, and user relationships. It integrates with the backend `/userman` service while providing a clean, interface-based architecture that follows the principles of dependency inversion.

### Key Design Principles

1. **Interface Segregation Principle (ISP)** - Services are divided into focused interfaces
2. **Dependency Inversion Principle (DIP)** - High-level modules depend on abstractions
3. **Single Responsibility Principle (SRP)** - Each component has one reason to change
4. **Open/Closed Principle (OCP)** - Architecture is open for extension but closed for modification
5. **Liskov Substitution Principle (LSP)** - Different implementations can be substituted seamlessly

## Architecture Components

### Core Interfaces

The core of the architecture is a set of interfaces that define the contracts for user management services:

- `IAuthenticationService` - Handles user authentication operations
- `IUserProfileService` - Manages user profile operations
- `IUserRelationshipService` - Manages relationships between users
- `IUserService` - Combines all user service interfaces into one comprehensive interface

These interfaces follow the Interface Segregation Principle by dividing functionality into smaller, focused interfaces.

### Service Factory

The `UserServiceFactory` implements the factory pattern and provides methods to create various user service implementations:

- Factory creates services based on a specified strategy
- Supports different strategies: userman-adapter, ui-native, mock, auto-detect
- Implements Dependency Inversion by depending on abstractions (interfaces) rather than concrete implementations
- Provides singleton pattern for global access to services

### Adapter for Backend Integration

The `UsermanAdapterService` adapts the backend `/userman` REST API to the user service interfaces:

- Implements all required interfaces
- Translates between UI data models and backend API responses
- Provides error handling and logging for API interactions
- Handles authentication token management

### Service Proxy for Cross-Cutting Concerns

The `UserServiceProxy` implements the proxy pattern to add cross-cutting concerns:

- Caching for improved performance
- Error handling and logging
- Performance monitoring
- Consistent behavior across all service implementations

### Mock Implementation for Testing

The `MockUserService` provides an in-memory implementation for testing:

- Simulates backend behavior without requiring a running backend
- Contains sample data for development and testing
- Can be used in isolation mode when backend is unavailable
- Simulates network delays for realistic testing

## Data Flow

1. UI components use the `UserServiceFactory` to get an instance of `IUserService`
2. The factory returns a proxied instance of the appropriate service implementation
3. The proxy adds caching, logging, and error handling
4. The service implementation (adapter or mock) handles the actual business logic
5. For the adapter, it communicates with the backend API
6. Changes are propagated back through the layers to update the UI

## Usage Examples

### Authentication

```typescript
// Get a user service instance
const userService = userServiceFactory.getUserService();

// Login
const authResponse = await userService.login({
  email: 'user@example.com',
  password: 'password123',
  rememberMe: true
});

// Access the authenticated user
const user = authResponse.user;
```

### Profile Management

```typescript
// Get a user profile service instance
const profileService = userServiceFactory.createProfileService();

// Get the current user profile
const profile = await profileService.getCurrentProfile();

// Update user profile
const updatedProfile = await profileService.updateProfile({
  displayName: 'New Display Name',
  firstName: 'New First Name'
});

// Update user preferences
const preferences = await profileService.updatePreferences({
  theme: 'dark',
  language: 'fr'
});
```

### Relationship Management

```typescript
// Get a relationship service instance
const relationshipService = userServiceFactory.createRelationshipService();

// Create a relationship invitation
const relationship = await relationshipService.createRelationship(
  'target-user-id',
  'parent-child'
);

// Get all relationships for the current user
const relationships = await relationshipService.getRelationships();

// Get users related to the current user (e.g., a parent's children)
const relatedUsers = await relationshipService.getRelatedUsers('parent-child');
```

## Testing Strategy

The architecture supports multiple testing strategies:

1. **Unit Testing** - Test individual service implementations in isolation
2. **Integration Testing** - Test services with the backend API 
3. **Mock Testing** - Use the mock service implementation for testing UI components
4. **E2E Testing** - Test the entire system from UI to backend

## Future Extensions

The architecture is designed to be extensible and can be enhanced with:

1. **Additional Service Implementations** - Adding new service implementations is simple
2. **Enhanced Proxy Features** - Add features like retry policies, circuit breakers, etc.
3. **Expanded Interfaces** - Add new methods to the interfaces as needed
4. **Integration with Other Systems** - Connect to different authentication providers (OAuth, SAML, etc.)

## Migration Path

When migrating from existing user management code to this new architecture:

1. Create adapters or wrappers for existing code
2. Use the factory to gradually replace implementations
3. Update components to use the new interfaces
4. Eventually remove the old code once all components have been migrated 