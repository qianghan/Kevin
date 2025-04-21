# Understanding the User Management System

This document provides a comprehensive overview of the User Management system implementation, including architecture decisions, model design, interfaces, and key components.

## Architecture Overview

The User Management system follows SOLID principles with a service-oriented architecture. Like other components in the Profiler system, it uses a layered approach:

```
┌───────────────────────────────────────────────────┐
│                                                   │
│                  API Layer                        │
│       (FastAPI Router /api/profiler/users)        │
│                                                   │
└───────────────────────┬───────────────────────────┘
                        │
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                                                   │
│             User Service Interface                │
│              (IUserService)                       │
│                                                   │
└───────────────────────┬───────────────────────────┘
                        │
                        │
                        ▼
┌───────────────────────────────────────────────────┐
│                                                   │
│           User Service Implementation             │
│              (UserService)                        │
│                                                   │
└─────────┬─────────────────────────────┬───────────┘
          │                             │
          │                             │
          ▼                             ▼
┌─────────────────────┐       ┌─────────────────────┐
│                     │       │                     │
│  User Repository    │       │ Authentication      │
│    Interface        │       │    Service          │
│                     │       │                     │
└────────┬────────────┘       └─────────┬───────────┘
         │                              │
         │                              │
         ▼                              ▼
┌─────────────────────┐       ┌─────────────────────┐
│                     │       │                     │
│ PostgreSQL/JSON     │       │  JWT/OAuth          │
│    Repository       │       │  Implementation     │
│                     │       │                     │
└─────────────────────┘       └─────────────────────┘
```

## User Model Design

The User model is designed to capture essential information for authentication, authorization, and profile association:

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    EDUCATOR = "educator"
    INSTITUTION = "institution"
    EMPLOYER = "employer"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class User(BaseModel):
    id: Optional[str] = None
    username: str
    email: str
    hashed_password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    profile_id: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
```

## Major Interfaces

### IUserService

The `IUserService` interface defines the contract for user management operations:

```python
class IUserService(ABC):
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user in the system"""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID"""
        pass
        
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by their username"""
        pass
        
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email"""
        pass
        
    @abstractmethod
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> User:
        """Update user information"""
        pass
        
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user from the system"""
        pass
        
    @abstractmethod
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username/password"""
        pass
        
    @abstractmethod
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change a user's password"""
        pass
        
    @abstractmethod
    async def update_last_login(self, user_id: str) -> None:
        """Update the last login timestamp for a user"""
        pass
        
    @abstractmethod
    async def assign_profile(self, user_id: str, profile_id: str) -> User:
        """Associate a profile with a user"""
        pass
```

### IUserRepository

The `IUserRepository` interface defines the data access contract:

```python
class IUserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user in the repository"""
        pass
        
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        pass
        
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        pass
        
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        pass
        
    @abstractmethod
    async def update(self, user_id: str, user_data: Dict[str, Any]) -> User:
        """Update a user's information"""
        pass
        
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user"""
        pass
        
    @abstractmethod
    async def list_users(self, offset: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination"""
        pass
```

### IAuthenticationService

The `IAuthenticationService` interface handles authentication and token management:

```python
class IAuthenticationService(ABC):
    @abstractmethod
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username/password"""
        pass
        
    @abstractmethod
    async def generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate access and refresh tokens for a user"""
        pass
        
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a token and return payload if valid"""
        pass
        
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Generate new tokens using a refresh token"""
        pass
        
    @abstractmethod
    async def invalidate_tokens(self, user_id: str) -> None:
        """Invalidate all tokens for a user"""
        pass
```

## Implementation Details

### UserService

The UserService implements IUserService and provides the core business logic:

```python
class UserService(IUserService):
    def __init__(self, user_repository: IUserRepository, auth_service: IAuthenticationService):
        self.repository = user_repository
        self.auth_service = auth_service
        self.password_hasher = PasswordHasher()
        
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        # Validate input data
        if await self.repository.get_by_username(user_data["username"]):
            raise DuplicateUsernameError("Username already exists")
            
        if await self.repository.get_by_email(user_data["email"]):
            raise DuplicateEmailError("Email already exists")
            
        # Hash the password
        user_data["hashed_password"] = self.password_hasher.hash(user_data.pop("password"))
        
        # Set timestamps
        current_time = datetime.now(UTC)
        user_data["created_at"] = current_time
        user_data["updated_at"] = current_time
        
        # Create the user
        user = User(**user_data)
        return await self.repository.create(user)
        
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        # Delegate to auth service
        user = await self.auth_service.authenticate(username, password)
        
        if user:
            # Update last login time
            await self.update_last_login(user.id)
            
        return user
```

### Authentication Implementation

The system uses JWT (JSON Web Tokens) for authentication:

```python
class JWTAuthenticationService(IAuthenticationService):
    def __init__(self, user_repository: IUserRepository, config: Dict[str, Any]):
        self.repository = user_repository
        self.secret_key = config["security"]["jwt_secret"]
        self.algorithm = config["security"]["jwt_algorithm"]
        self.access_token_expire_minutes = config["security"]["access_token_expire_minutes"]
        self.refresh_token_expire_days = config["security"]["refresh_token_expire_days"]
        self.password_hasher = PasswordHasher()
        
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        user = await self.repository.get_by_username(username)
        
        if not user:
            # Try with email
            user = await self.repository.get_by_email(username)
            
        if not user:
            return None
            
        # Verify password
        try:
            self.password_hasher.verify(user.hashed_password, password)
            return user
        except VerifyMismatchError:
            return None
```

## Integration with Other Services

The User Management system integrates with several other components:

1. **Profile Service**: Users are linked to their profiles for personalized experiences
2. **Recommendation Service**: User preferences influence recommendation generation
3. **Document Service**: Users have access control for their documents
4. **Q&A Service**: User responses are tracked for personalized interactions
5. **Notification Service**: Users receive notifications about various system events

## Security Considerations

The User Management system implements several security best practices:

1. **Password Hashing**: Passwords are hashed using Argon2 before storage
2. **Rate Limiting**: API endpoints have rate limiting to prevent brute force attacks
3. **JWT with Short Expiry**: Access tokens have short expiry times with refresh token rotation
4. **Role-Based Access Control**: Different user roles have different permissions
5. **Input Validation**: All user inputs are validated before processing
6. **Audit Logging**: Security-relevant events are logged for audit purposes

## Repository Implementation

The system supports both PostgreSQL and JSON file-based repositories:

```python
class PostgreSQLUserRepository(IUserRepository):
    def __init__(self, database_connection):
        self.db = database_connection
        
    async def create(self, user: User) -> User:
        # Generate UUID if not provided
        if not user.id:
            user.id = str(uuid.uuid4())
            
        query = """
        INSERT INTO users (id, username, email, hashed_password, first_name, last_name, 
                         role, status, created_at, updated_at, last_login, profile_id,
                         preferences, settings, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        RETURNING *
        """
        
        values = (user.id, user.username, user.email, user.hashed_password,
                 user.first_name, user.last_name, user.role, user.status,
                 user.created_at, user.updated_at, user.last_login, user.profile_id,
                 json.dumps(user.preferences or {}), json.dumps(user.settings or {}),
                 json.dumps(user.metadata or {}))
                 
        result = await self.db.fetchrow(query, *values)
        return User(**dict(result))
```

## API Endpoints

The User Management system exposes several REST endpoints:

- `POST /api/profiler/users`: Create a new user
- `GET /api/profiler/users/{user_id}`: Get user details
- `PUT /api/profiler/users/{user_id}`: Update user information
- `DELETE /api/profiler/users/{user_id}`: Delete a user
- `POST /api/profiler/auth/login`: Authenticate and get tokens
- `POST /api/profiler/auth/refresh`: Refresh access token
- `POST /api/profiler/auth/logout`: Invalidate tokens
- `POST /api/profiler/auth/password`: Change password

## Conclusion

The User Management system provides a robust foundation for user authentication, authorization, and profile management in the Profiler application. By following SOLID principles and a layered architecture, it maintains clear separation of concerns and facilitates testing and extension. 