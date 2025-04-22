# Authentication and Authorization Guide

This guide explains how authentication and authorization work in the User Management System, as well as best practices for integrating with the system.

## Authentication

The User Management System uses JWT (JSON Web Tokens) for authentication. This section covers the different authentication methods and flows.

### User Authentication

#### Registration and Login Flow

1. **User Registration**: 
   - Users register with email, password, and name
   - Email verification may be required depending on configuration
   - Account is created with a default role (usually 'student')

2. **Login**:
   - User provides email and password credentials
   - System verifies credentials and returns JWT token
   - Token contains encoded user information and permissions
   - Token has a configurable expiration time (default: 24 hours)

3. **Token Validation**:
   - All protected endpoints validate the token
   - Token is passed in the Authorization header: `Authorization: Bearer <token>`
   - Invalid or expired tokens result in 401 Unauthorized responses

#### Password Management

The system provides several password management features:

- **Password Reset**: Users can request a password reset link sent to their email
- **Password Change**: Authenticated users can change their password (requires current password)
- **Password Security**: Passwords are hashed using bcrypt with appropriate salt rounds

#### Email Verification

Email verification ensures users provide valid email addresses:

- Upon registration, a verification email is sent to the user's email address
- The email contains a unique token for verification
- Users must verify their email to access certain features (configurable)
- Verified status is tracked in the user's profile

### Service Authentication

Services can authenticate with the User Management System using API keys:

1. **Service Registration**:
   - Services are registered in the admin dashboard
   - System generates API key and secret for the service
   - Service credentials should be stored securely

2. **Service Token**:
   - Services authenticate using their API key and secret
   - System returns a service token for subsequent requests
   - Service tokens have different permissions than user tokens

3. **Service-to-Service Communication**:
   - Services use their token to access User Management APIs
   - Service tokens can validate user tokens
   - Service tokens can check user permissions

## Authorization

The User Management System implements a role-based access control (RBAC) system with fine-grained permissions.

### Roles

The system has four predefined roles:

1. **Student**:
   - Basic access to own profile and preferences
   - Access to entitled services for their learning
   - Limited visibility of parent relationships

2. **Parent**:
   - Access to own profile and preferences
   - Access to linked student accounts
   - Ability to view/manage student entitlements
   - Parent-specific service access

3. **Admin**:
   - Full access to user management
   - Ability to assign roles
   - Service registration and management
   - System configuration

4. **Support**:
   - Read-only access to user information
   - Limited ability to help users with account issues
   - Cannot modify roles or sensitive settings

### Permissions

Each role has a set of permissions that determine what actions they can perform:

- Permissions are grouped into categories (user, service, admin)
- Permissions follow the format: `[resource]:[action]`
- Examples: `user:read`, `service:create`, `admin:manage-roles`
- Permissions can be assigned or revoked for specific roles
- Custom permissions can be defined for specific services

### Service Access Control

The system controls access to integrated services:

1. **Service Access Types**:
   - **Public**: Available to all authenticated users
   - **Role-Based**: Available to specific roles
   - **Restricted**: Requires explicit entitlement

2. **Entitlements**:
   - Users can be granted entitlements to specific services
   - Entitlements can have expiration dates
   - Entitlements can include specific permissions within the service

3. **Access Verification**:
   - Services can verify user access through the User Management API
   - Access checks validate the user's role, entitlements, and permissions
   - Parent users can access services on behalf of their linked students

## Best Practices

### Security Best Practices

1. **Token Handling**:
   - Store tokens securely (avoid localStorage in browser environments)
   - Never expose tokens in URLs or logs
   - Implement token refresh to maintain sessions
   - Verify token signature and expiration

2. **Password Security**:
   - Enforce strong password policies
   - Implement rate limiting for login attempts
   - Use secure password reset flows

3. **Service Authentication**:
   - Store API keys and secrets securely (environment variables or secret manager)
   - Rotate API keys periodically
   - Use HTTPS for all API communications

### Implementation Recommendations

1. **Frontend Applications**:
   - Implement secure token storage
   - Add interceptors for automated token handling
   - Handle authentication state consistently
   - Implement permission-based UI rendering

2. **Backend Services**:
   - Use the service client libraries for authentication
   - Cache service tokens for performance
   - Implement appropriate error handling
   - Log authentication failures for security monitoring

3. **Parent-Student Access**:
   - Always verify parent-student relationships
   - Include relationship verification in access control
   - Clearly indicate when acting on behalf of a student

## Common Scenarios

### Single Sign-On (SSO)

The User Management System can function as an authentication provider for other services:

1. **Redirecting to Login**:
   - Services redirect unauthenticated users to the login page
   - Login page redirects back with token after successful authentication

2. **Token Validation**:
   - Services validate tokens using the token validation endpoint
   - Validation returns user profile and permissions

3. **Session Management**:
   - Services can check session status
   - Single logout can terminate all service sessions

### Service Authorization

Services need to verify user authorization for specific actions:

1. **Role Checking**:
   - Services can check user roles from the token or by making an API call
   - Role-based access control should be implemented at the service level

2. **Permission Checking**:
   - Services can check specific permissions
   - Permission checks should be granular and specific to the action

3. **Parent-Student Access**:
   - Services should check if a parent has access to student resources
   - Relationship verification is essential for secure access

## Troubleshooting

### Common Authentication Issues

1. **Token Expired**:
   - Error: 401 Unauthorized with "Token expired" message
   - Solution: Refresh the token or redirect to login

2. **Invalid Token**:
   - Error: 401 Unauthorized with "Invalid token" message
   - Solution: Redirect to login for a new token

3. **Token Validation Failure**:
   - Error: 401 Unauthorized with "Token validation failed" message
   - Solution: Check token format and integrity

### Authorization Errors

1. **Insufficient Permissions**:
   - Error: 403 Forbidden with "Insufficient permissions" message
   - Solution: Request necessary permissions or change user role

2. **Service Access Denied**:
   - Error: 403 Forbidden with "Service access denied" message
   - Solution: Check service entitlements and request access if needed

3. **Account Issues**:
   - Error: 403 Forbidden with "Account locked" or "Email not verified" message
   - Solution: Verify account status and complete required actions

## API Reference

For detailed API information, refer to the [OpenAPI documentation](./openapi.yaml).

Key authentication and authorization endpoints:

- `/auth/login`: Authenticate user and receive a token
- `/auth/logout`: Invalidate current token
- `/auth/register`: Create a new user account
- `/auth/verify-email/{token}`: Verify user email
- `/auth/reset-password`: Initiate password reset
- `/auth/reset-password/{token}`: Reset password with token
- `/auth/validate-token`: Validate a JWT token
- `/auth/service-token`: Get a service token (service auth)
- `/services/access`: Check service access for a user 