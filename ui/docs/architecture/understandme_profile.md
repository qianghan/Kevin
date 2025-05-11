# User Profile Management

This document outlines the architecture and implementation of the user profile management system in the Kevin application.

## Architecture Overview

The profile management system follows SOLID principles and is built around the following key components:

1. **IUserProfileService Interface**: Defines the contract for profile operations
2. **UserProfileAdapter**: Adapter implementation connecting to backend /userman API
3. **MockUserProfileService**: Mock implementation for testing and development
4. **UserProfileContext & useUserProfile Hook**: React context and hooks for component access
5. **Profile UI Components**: Reusable UI components for profile management

## Components

### IUserProfileService Interface

Located in `ui/lib/interfaces/services/userProfile.service.ts`, this interface follows the Interface Segregation Principle (ISP) to define specific profile-related operations:

- `getCurrentProfile()`: Retrieves the current user's profile
- `updateProfile()`: Updates profile information
- `uploadProfilePicture()`: Handles profile picture uploads
- `getProfileCompleteness()`: Calculates profile completeness percentage
- `requestEmailChange()`: Initiates email change process
- `verifyEmailChange()`: Completes email change with verification token
- `updatePreferences()`: Updates user preferences
- `exportProfileData()`: Exports user data in different formats

### UserProfileAdapter

Located in `ui/lib/services/user/UserProfileAdapter.service.ts`, this adapter connects to the backend /userman API, implementing the IUserProfileService interface. It follows the Adapter pattern to translate between the application and the backend service.

### MockUserProfileService

Located in `ui/lib/services/user/mock/MockUserProfile.service.ts`, this provides a fully functional in-memory implementation for testing and development without requiring the backend service.

### Factory Integration

The existing UserServiceFactory has been extended to support the profile service, following the Factory and Strategy patterns:

```typescript
// In UserServiceFactory.ts
public createUserProfileService(strategy: UserServiceStrategy = this.defaultStrategy): IUserProfileService {
  // Determine which profile service implementation to create based on strategy
}
```

### UserProfileContext & Hook

Located in `ui/hooks/useUserProfile.ts`, the context and hook provide React components with access to profile operations:

```typescript
// Example usage in components
const { 
  user, 
  updateProfile, 
  uploadProfilePicture, 
  completeness,
  isLoading,
  error 
} = useUserProfile();
```

This follows the React Context pattern for global state management and implements the Dependency Inversion Principle (DIP) by depending on abstractions rather than concrete implementations.

### Profile UI Components

Located in `ui/components/profile/`, these components provide a user-friendly interface for profile management:

- `ProfileForm.tsx`: Form for editing basic profile information
- `ProfilePicture.tsx`: Component for uploading and previewing profile pictures
- `ProfileCompleteness.tsx`: Visual indicator of profile completeness with suggestions
- `EmailChangeForm.tsx`: Secure form for changing email addresses

## Data Flow

1. User interacts with UI components
2. Components use the useUserProfile hook to access profile operations
3. Hook delegates to the appropriate IUserProfileService implementation
4. Service processes the request and communicates with the backend
5. Results are returned to the hook and update the React state
6. UI components re-render with updated data

## Security Considerations

1. Email changes require password verification
2. Profile updates are validated before submission
3. File uploads are restricted to image types and reasonable sizes
4. All API calls use authentication tokens

## Development and Testing

During development, the MockUserProfileService provides realistic data and behavior without requiring the backend service. This implementation can be selected using the UserServiceFactory:

```typescript
// Force mock implementation during development/testing
userServiceFactory.setDefaultStrategy('mock');
```

For production, the adapter implementation is used by default, connecting to the actual backend services.

## Future Enhancements

1. Add support for more profile data fields
2. Implement multi-factor authentication
3. Add profile data portability features
4. Integrate with identity federation services 