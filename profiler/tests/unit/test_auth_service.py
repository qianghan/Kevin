"""
Unit tests for the Authentication Service.

This module tests the functionality of the authentication and authorization service.
"""

import pytest
import asyncio
import jwt
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from profiler.app.backend.services.auth import AuthenticationService
from profiler.app.backend.utils.errors import AuthenticationError, ResourceNotFoundError

# Mock models and database manager
class MockUser:
    def __init__(self, user_id, username, email, password_hash, password_salt, status="active"):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.password_salt = password_salt
        self.full_name = f"{username.capitalize()} User"
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.status = status


class MockRole:
    def __init__(self, role_id, name, description=""):
        self.role_id = role_id
        self.name = name
        self.description = description
        self.created_at = datetime.now()


class MockUserRole:
    def __init__(self, user_id, role_id):
        self.user_id = user_id
        self.role_id = role_id
        self.created_at = datetime.now()


class MockPermission:
    def __init__(self, permission_id, role_id, permission):
        self.permission_id = permission_id
        self.role_id = role_id
        self.permission = permission
        self.created_at = datetime.now()


class MockResult:
    def __init__(self, scalar_result=None, all_result=None):
        self._scalar_result = scalar_result
        self._all_result = all_result
        
    def scalar_one_or_none(self):
        return self._scalar_result
        
    def scalars(self):
        return self
        
    def all(self):
        return self._all_result or []


class MockSession:
    def __init__(self):
        self.add_calls = []
        self.execute_results = {}
        self.commit_called = False
        
    def add(self, obj):
        self.add_calls.append(obj)
        
    async def execute(self, stmt):
        # Simple mock for select statements
        if stmt in self.execute_results:
            return self.execute_results[stmt]
        return MockResult()
        
    async def commit(self):
        self.commit_called = True
        
    async def begin(self):
        return self
        
    async def begin_nested(self):
        return self
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, *args):
        pass


class MockDatabaseManager:
    def __init__(self):
        self.session = MockSession()
        self.initialized = False
        
    async def initialize(self):
        self.initialized = True
        
    async def shutdown(self):
        self.initialized = False
        
    async def get_session(self):
        return self.session


@pytest.fixture
def mock_db_manager():
    return MockDatabaseManager()


@pytest.fixture
def auth_service(mock_db_manager):
    with patch('profiler.app.backend.services.auth.auth_service.DatabaseManager', return_value=mock_db_manager):
        service = AuthenticationService({
            "jwt_secret": "test-secret-key",
            "jwt_expires_seconds": 3600
        })
        return service


@pytest.mark.asyncio
async def test_initialize(auth_service, mock_db_manager):
    """Test that the service initializes correctly."""
    await auth_service.initialize()
    
    assert auth_service._initialized is True
    assert mock_db_manager.initialized is True


@pytest.mark.asyncio
async def test_register_user(auth_service, mock_db_manager):
    """Test registering a new user."""
    # Mock role query
    user_role = MockRole("role123", "user")
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(scalar_result=user_role)
    
    # Register user
    result = await auth_service.register_user(
        username="testuser",
        password="password123",
        email="test@example.com",
        full_name="Test User"
    )
    
    # Check result
    assert result["username"] == "testuser"
    assert result["email"] == "test@example.com"
    assert result["full_name"] == "Test User"
    assert "user_id" in result
    assert "role" in result
    
    # Check that user was added to database
    assert len(mock_db_manager.session.add_calls) == 2  # User and UserRole


@pytest.mark.asyncio
async def test_register_user_existing_username(auth_service, mock_db_manager):
    """Test registering a user with an existing username."""
    # Mock existing user query
    existing_user = MockUser("user123", "testuser", "test@example.com", "hash", "salt")
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(scalar_result=existing_user)
    
    # Try to register user with existing username
    with pytest.raises(AuthenticationError) as excinfo:
        await auth_service.register_user(
            username="testuser",
            password="password123",
            email="new@example.com",
            full_name="Test User"
        )
    
    assert "already exists" in str(excinfo.value)


@pytest.mark.asyncio
async def test_authenticate_success(auth_service, mock_db_manager):
    """Test successful authentication."""
    # Mock password hashing
    password = "password123"
    salt = "testsalt"
    password_hash = auth_service._hash_password(password, salt)
    
    # Mock user query
    user = MockUser("user123", "testuser", "test@example.com", password_hash, salt)
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(scalar_result=user)
    
    # Mock roles and permissions query
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(all_result=[("role123",)])
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(all_result=[
        MockRole("role123", "user"),
    ])
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(all_result=[
        ("profile:read:own",),
        ("profile:write:own",)
    ])
    
    # Authenticate
    result = await auth_service.authenticate("testuser", password)
    
    # Check result
    assert "token" in result
    assert "expires_at" in result
    assert "user" in result
    assert result["user"]["username"] == "testuser"
    
    # Verify token
    token = result["token"]
    decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
    assert decoded["sub"] == "user123"
    assert decoded["username"] == "testuser"
    assert "permissions" in decoded
    assert "exp" in decoded


@pytest.mark.asyncio
async def test_authenticate_invalid_password(auth_service, mock_db_manager):
    """Test authentication with invalid password."""
    # Mock password hashing
    password = "password123"
    salt = "testsalt"
    password_hash = auth_service._hash_password(password, salt)
    
    # Mock user query
    user = MockUser("user123", "testuser", "test@example.com", password_hash, salt)
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(scalar_result=user)
    
    # Try to authenticate with wrong password
    with pytest.raises(AuthenticationError) as excinfo:
        await auth_service.authenticate("testuser", "wrongpassword")
    
    assert "Invalid username or password" in str(excinfo.value)


@pytest.mark.asyncio
async def test_authenticate_inactive_user(auth_service, mock_db_manager):
    """Test authentication with inactive user."""
    # Mock password hashing
    password = "password123"
    salt = "testsalt"
    password_hash = auth_service._hash_password(password, salt)
    
    # Mock user query with inactive user
    user = MockUser("user123", "testuser", "test@example.com", password_hash, salt, status="inactive")
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(scalar_result=user)
    
    # Try to authenticate inactive user
    with pytest.raises(AuthenticationError) as excinfo:
        await auth_service.authenticate("testuser", password)
    
    assert "Invalid username or password" in str(excinfo.value)


@pytest.mark.asyncio
async def test_verify_token_valid(auth_service, mock_db_manager):
    """Test verifying a valid token."""
    # Create a token
    user_id = "user123"
    now = int(time.time())
    expires_at = now + 3600
    
    token_data = {
        "sub": user_id,
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["profile:read:own", "profile:write:own"],
        "iat": now,
        "exp": expires_at
    }
    
    token = jwt.encode(token_data, "test-secret-key", algorithm="HS256")
    
    # Mock user query
    user = MockUser(user_id, "testuser", "test@example.com", "hash", "salt")
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(scalar_result=user)
    
    # Verify token
    result = await auth_service.verify_token(token)
    
    # Check result
    assert result["sub"] == user_id
    assert result["username"] == "testuser"
    assert result["roles"] == ["user"]


@pytest.mark.asyncio
async def test_verify_token_expired(auth_service, mock_db_manager):
    """Test verifying an expired token."""
    # Create an expired token
    user_id = "user123"
    now = int(time.time())
    expired_at = now - 3600  # Expired 1 hour ago
    
    token_data = {
        "sub": user_id,
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["profile:read:own", "profile:write:own"],
        "iat": now - 7200,  # Issued 2 hours ago
        "exp": expired_at
    }
    
    token = jwt.encode(token_data, "test-secret-key", algorithm="HS256")
    
    # Verify expired token
    with pytest.raises(AuthenticationError) as excinfo:
        await auth_service.verify_token(token)
    
    assert "expired" in str(excinfo.value)


@pytest.mark.asyncio
async def test_verify_token_invalid_user(auth_service, mock_db_manager):
    """Test verifying a token for a non-existent user."""
    # Create a token
    user_id = "user123"
    now = int(time.time())
    expires_at = now + 3600
    
    token_data = {
        "sub": user_id,
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["profile:read:own", "profile:write:own"],
        "iat": now,
        "exp": expires_at
    }
    
    token = jwt.encode(token_data, "test-secret-key", algorithm="HS256")
    
    # Mock user query (no user found)
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(scalar_result=None)
    
    # Verify token with non-existent user
    with pytest.raises(AuthenticationError) as excinfo:
        await auth_service.verify_token(token)
    
    assert "not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_authorize_wildcard_permission(auth_service, mock_db_manager):
    """Test authorization with wildcard permission."""
    user_id = "user123"
    
    # Mock permissions query
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[("role123",)]
    )
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[MockRole("role123", "admin")]
    )
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[("*",)]  # Wildcard permission
    )
    
    # Check authorization
    result = await auth_service.authorize(user_id, "profile:read:own", "profile123")
    
    # User with wildcard permission should be authorized
    assert result is True


@pytest.mark.asyncio
async def test_authorize_exact_permission(auth_service, mock_db_manager):
    """Test authorization with exact permission match."""
    user_id = "user123"
    
    # Mock permissions query
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[("role123",)]
    )
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[MockRole("role123", "user")]
    )
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[("profile:read:own",)]
    )
    
    # Check authorization
    result = await auth_service.authorize(user_id, "profile:read:own", "profile123")
    
    # User with exact permission should be authorized
    assert result is True


@pytest.mark.asyncio
async def test_authorize_owned_resource(auth_service, mock_db_manager):
    """Test authorization for an owned resource."""
    user_id = "user123"
    resource_id = "profile123"
    
    # Mock permissions query
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[("role123",)]
    )
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[MockRole("role123", "user")]
    )
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[("profile:read:own",)]
    )
    
    # Mock resource ownership check (user owns resource)
    with patch('profiler.app.backend.services.auth.auth_service.AuthenticationService._check_resource_ownership', 
               new_callable=AsyncMock, return_value=True):
        
        # Check authorization
        result = await auth_service.authorize(user_id, "profile:read:own", resource_id)
        
        # User should be authorized for their own resource
        assert result is True


@pytest.mark.asyncio
async def test_authorize_non_owned_resource(auth_service, mock_db_manager):
    """Test authorization for a non-owned resource."""
    user_id = "user123"
    resource_id = "profile456"  # Belongs to another user
    
    # Mock permissions query
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[("role123",)]
    )
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[MockRole("role123", "user")]
    )
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(
        all_result=[("profile:read:own",)]  # Only own resources
    )
    
    # Mock resource ownership check (user doesn't own resource)
    with patch('profiler.app.backend.services.auth.auth_service.AuthenticationService._check_resource_ownership', 
               new_callable=AsyncMock, return_value=False):
        
        # Check authorization
        result = await auth_service.authorize(user_id, "profile:read:own", resource_id)
        
        # User should not be authorized for another user's resource
        assert result is False


@pytest.mark.asyncio
async def test_change_password(auth_service, mock_db_manager):
    """Test changing a user's password."""
    user_id = "user123"
    current_password = "oldpassword"
    new_password = "newpassword"
    
    # Mock password hashing
    salt = "testsalt"
    password_hash = auth_service._hash_password(current_password, salt)
    
    # Mock user query
    user = MockUser(user_id, "testuser", "test@example.com", password_hash, salt)
    mock_db_manager.session.execute_results[MagicMock()] = MockResult(scalar_result=user)
    
    # Change password
    result = await auth_service.change_password(user_id, current_password, new_password)
    
    # Password change should succeed
    assert result is True
    
    # User should have been updated with new password hash
    assert mock_db_manager.session.add_calls[0].password_hash != password_hash
    assert mock_db_manager.session.add_calls[0].password_salt != salt 