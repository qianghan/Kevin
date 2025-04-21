# Understanding the User Management System

This document provides an overview of the User Management system implemented in Kevin, including architecture decisions, model design, interfaces, and integration with other services.

## Architecture Overview

The User Management system follows a modern web application architecture with separation of concerns across the backend and frontend. The system is built on:

- **Backend**: FastAPI for API endpoints
- **Frontend**: Next.js with Next-Auth for authentication
- **Database**: MongoDB for user data storage

The architecture follows this layered approach:

```
┌───────────────────────────────────────────────────┐
│                                                   │
│         Next.js Frontend (UI components)          │
│                                                   │
└───────────────────────┬───────────────────────────┘
                        │
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                                                   │
│             Next-Auth Authentication              │
│                                                   │
└───────────────────────┬───────────────────────────┘
                        │
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                                                   │
│               User Service Layer                  │
│                                                   │
└─────────┬─────────────────────────────┬───────────┘
          │                             │
          │                             │
          ▼                             ▼
┌─────────────────────┐       ┌─────────────────────┐
│                     │       │                     │
│  User API Endpoints │       │  MongoDB Database   │
│                     │       │                     │
└─────────────────────┘       └─────────────────────┘
```

## User Model Design

The User model is designed to capture essential information for authentication, authorization, and profile management:

```typescript
// Base User Interface
interface BaseUser {
  email: string;
  name: string;
  image?: string;
  password?: string;
  emailVerified?: Date;
  preferences?: UserPreferences;
  createdAt: Date;
  updatedAt: Date;
}

// Mongoose Document Interface
interface UserDocument extends Document, BaseUser {
  role: 'student' | 'parent';
  password?: string;
  preferences?: UserPreferences;
}

// User Preferences
interface UserPreferences {
  theme?: 'light' | 'dark' | 'system';
  emailNotifications?: boolean;
  language?: string;
  [key: string]: any;
}
```

The system uses Mongoose Schema for the MongoDB database:

```typescript
const UserSchema = new Schema<UserDocument>(
  {
    email: {
      type: String,
      required: true,
      unique: true,
    },
    name: {
      type: String,
      required: true,
    },
    password: {
      type: String,
    },
    image: {
      type: String,
    },
    emailVerified: {
      type: Date,
    },
    role: {
      type: String,
      enum: ['student', 'parent'],
      required: true,
    },
    preferences: {
      type: Schema.Types.Mixed,
      default: {
        theme: 'system',
        emailNotifications: true,
        language: 'en'
      }
    }
  },
  {
    timestamps: true,
  }
);
```

## Authentication Implementation

The system uses Next-Auth for authentication with multiple provider options:

1. **Credentials Provider**: Email/password authentication
2. **Google Provider**: OAuth authentication with Google
3. **Facebook Provider**: OAuth authentication with Facebook

JWT (JSON Web Tokens) are used for session management with appropriate security measures:

```typescript
session: {
  strategy: "jwt",
  maxAge: 30 * 24 * 60 * 60, // 30 days
  updateAge: 24 * 60 * 60, // 24 hours - refresh token if older
},
```

## User Service Implementation

The User Service provides a comprehensive interface for user management operations:

```typescript
class UserService {
  // User profile management
  async getCurrentUser(): Promise<UserProfile | null>;
  async updateProfile(profile: Partial<UserProfile>): Promise<UserProfile>;
  
  // User preferences
  async updatePreferences(preferences: UserPreferences): Promise<UserPreferences>;
  async getPreferences(): Promise<UserPreferences>;
  
  // Account linking (for student-parent relationships)
  async linkAccounts(targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean>;
  async unlinkAccount(targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean>;
  async getLinkedUsers(relationship: 'students' | 'parents' | 'partners'): Promise<UserProfile[]>;
  
  // User search
  async searchUsers(query: string): Promise<UserProfile[]>;
  
  // Security features
  async changeEmail(newEmail: string, password: string): Promise<boolean>;
  async changePassword(currentPassword: string, newPassword: string): Promise<boolean>;
}
```

## API Endpoints

The User Management system exposes several REST endpoints:

- `POST /api/auth/register`: Create a new user
- `POST /api/auth/login`: Authenticate and create session
- `GET /api/user/profile`: Get current user profile
- `PUT /api/user/profile`: Update user profile
- `GET /api/user/preferences`: Get user preferences
- `PUT /api/user/preferences`: Update user preferences
- `POST /api/user/link`: Link accounts (student-parent relationship)
- `DELETE /api/user/link`: Unlink accounts
- `GET /api/user/search`: Search for users

## Integration with Other Services

The User Management system integrates with several other components:

1. **Chat Service**: Users are linked to their chat sessions
2. **Authentication**: Provides authentication for the entire application
3. **Profile Management**: Handles user profile data and preferences

The Chat Service integration is particularly important as it associates chat sessions with specific users:

```typescript
// Chat Session Schema integration with User
const ChatSessionSchema = new Schema<ChatSessionDocument>(
  {
    title: {
      type: String,
      required: true
    },
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true
    },
    // Other fields...
  }
);
```

## Security Considerations

The User Management system implements several security best practices:

1. **Password Hashing**: Passwords are hashed using bcrypt before storage
2. **JWT with Secure Settings**: Access tokens with appropriate security settings
3. **HTTPS Only in Production**: Secure cookies in production environments
4. **Role-Based Access Control**: Different user roles have different permissions
5. **Input Validation**: All user inputs are validated before processing

## Error Handling

The system implements comprehensive error handling:

```typescript
// Error types for detailed error handling
export class ServiceError extends Error {
  details?: any;
  
  constructor(message: string, details?: any) {
    super(message);
    this.name = 'ServiceError';
    this.details = details;
  }
}

export class DatabaseError extends ServiceError {}
export class ApiRequestError extends ServiceError {}
export class AuthError extends ServiceError {}
```

With retries for API operations:

```typescript
const retry = async <T>(
  operation: () => Promise<T>,
  methodName: string,
  retries = MAX_RETRIES,
  delay = RETRY_DELAY
): Promise<T> => {
  try {
    return await operation();
  } catch (error) {
    if (retries <= 0) {
      return handleError(error, methodName);
    }
    
    await new Promise(resolve => setTimeout(resolve, delay));
    return retry(operation, methodName, retries - 1, delay * 1.5);
  }
};
```

## Conclusion

The User Management system provides a robust foundation for user authentication, authorization, and profile management in the Kevin application. By leveraging Next-Auth, MongoDB, and a service-oriented architecture, it maintains clear separation of concerns and facilitates testing and extension. 