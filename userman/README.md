# User Management System

A comprehensive user management solution for the Kevin application, providing user authentication, profile management, and relationship functionality. Built with TypeScript and MongoDB integration.

## Features

- **Authentication**: User registration, login, password reset, and email verification
- **Profile Management**: Update profiles and user preferences 
- **Account Relationships**: Link parent and student accounts
- **Search Functionality**: Search for users with relevant filtering
- **Secure Implementation**: Password hashing with bcrypt, proper validation
- **SOLID Principles**: Follows best practices like dependency injection, interface segregation
- **Tested**: Comprehensive BDD tests to ensure functionality

## Architecture

The user management system follows a modern architecture with a focus on SOLID design principles:

```
┌───────────────────────────────────────────────────┐
│                                                   │
│                  Express Routers                  │
│  ┌────────────────────┬───────────────────────┐   │
│  │  Authentication    │      User Management   │   │
│  └────────────────────┴───────────────────────┘   │
└───────────────────────┬───────────────────────────┘
                        │
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                                                   │
│                  User Service                     │
│   (Implements IUserService, IAuthService, etc.)   │
│                                                   │
└───────────────────────┬───────────────────────────┘
                        │
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                                                   │
│               User Repository                     │
│                                                   │
└───────────────────────┬───────────────────────────┘
                        │
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                                                   │
│              MongoDB / Mongoose                   │
│                                                   │
└───────────────────────────────────────────────────┘
```

### Key Components

- **Models**: Mongoose schemas and TypeScript interfaces
- **Services**: Business logic implementation following interface contracts
- **Repository**: Data access layer with MongoDB implementation
- **API Routes**: Express routers for REST endpoints

## Installation

```bash
# Install dependencies
npm install

# Build the package
npm run build

# Run tests
npm test

# Run BDD tests
npm run test:bdd
```

## Usage

### Standalone Usage

```typescript
import { createUserManagementSystem } from 'kevin-userman';
import express from 'express';
import { connectToDatabase } from 'kevin-userman/src/utils/db';

// Initialize Express app
const app = express();
app.use(express.json());

// Connect to database
connectToDatabase({ uri: 'mongodb://localhost:27017/kevin' });

// Create user management system
const { userRouter, authRouter } = createUserManagementSystem();

// Mount routers
app.use('/api/auth', authRouter);
app.use('/api/user', userRouter);

// Start server
app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

### Integration with Existing Express App

```typescript
import express from 'express';
import { createUserManagementSystem } from 'kevin-userman';

// Existing Express app
const app = express();
app.use(express.json());

// Create user management system
const { userRouter, authRouter } = createUserManagementSystem();

// Mount routers
app.use('/api/auth', authRouter);
app.use('/api/user', userRouter);
```

### Using Individual Components

```typescript
import { 
  UserService, 
  MongoUserRepository, 
  createUserRouter
} from 'kevin-userman';

// Initialize repository and service
const userRepository = new MongoUserRepository();
const userService = new UserService(userRepository);

// Create a custom router
const customRouter = createUserRouter(userService);
```

## API Documentation

### Authentication Endpoints

- `POST /api/auth/register`: Register a new user
  - Request: `{ name, email, password, role }`
  - Response: `{ data: UserProfile }`

- `POST /api/auth/login`: Authenticate a user
  - Request: `{ email, password }`
  - Response: `{ data: { user: UserProfile } }`

- `POST /api/auth/forgot-password`: Request password reset
  - Request: `{ email }`
  - Response: `{ message: string }`

- `POST /api/auth/reset-password`: Reset password with token
  - Request: `{ token, newPassword }`
  - Response: `{ message: string }`

- `GET /api/auth/verify-email/:token`: Verify email address
  - Response: `{ message: string }`

### User Management Endpoints

- `GET /api/user/profile`: Get current user profile
  - Response: `{ data: UserProfile }`

- `PUT /api/user/profile`: Update user profile
  - Request: `{ name, image, ... }`
  - Response: `{ data: UserProfile }`

- `GET /api/user/preferences`: Get user preferences
  - Response: `{ data: UserPreferences }`

- `PUT /api/user/preferences`: Update user preferences
  - Request: `{ theme, emailNotifications, language, ... }`
  - Response: `{ data: UserPreferences }`

- `POST /api/user/password`: Change password
  - Request: `{ currentPassword, newPassword }`
  - Response: `{ data: { success: boolean } }`

- `POST /api/user/email`: Change email address
  - Request: `{ newEmail, password }`
  - Response: `{ data: { success: boolean } }`

- `GET /api/user/search`: Search for users
  - Query: `?q=searchterm`
  - Response: `{ data: UserProfile[] }`

- `POST /api/user/link`: Link accounts
  - Request: `{ targetUserId, relationship }`
  - Response: `{ data: boolean }`

- `DELETE /api/user/link`: Unlink accounts
  - Request: `{ targetUserId, relationship }`
  - Response: `{ data: boolean }`

- `GET /api/user/linked/:relationship`: Get linked users
  - Params: `relationship = 'students' | 'parents' | 'partners'`
  - Response: `{ data: UserProfile[] }`

## Data Models

### User Model

```typescript
interface User {
  id?: string;
  email: string;
  name: string;
  password?: string;
  role: 'student' | 'parent' | 'admin';
  studentIds?: string[];  // For parent accounts
  parentIds?: string[];   // For student accounts
  partnerIds?: string[];  // For parent accounts
  preferences?: {
    theme?: 'light' | 'dark' | 'system';
    emailNotifications?: boolean;
    language?: string;
    [key: string]: any;
  };
  image?: string;
  emailVerified?: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

## Testing

The system includes comprehensive tests:

```bash
# Run unit tests
npm test

# Run BDD feature tests
npm run test:bdd
```

BDD tests cover the full range of functionality including:
- User registration
- Authentication
- Profile management
- Password and email changes
- Account linking
- User search

## Security Considerations

- Passwords are hashed using bcrypt
- Input validation on all endpoints
- Route protection with authentication middleware
- Separate interfaces for different concerns
- Error handling with appropriate HTTP status codes

## License

MIT 