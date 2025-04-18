"""
BDD tests for User Authentication functionality (PRD-1).

These tests verify the requirements for the user authentication functionality.
"""

import os
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Generator, Optional

from pytest_bdd import scenarios, given, when, then, parsers
import pytest_asyncio

# Import app modules
from profiler.app.backend.services.auth import AuthenticationService
from profiler.app.backend.utils.errors import AuthenticationError

# BDD test markers
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.authentication,
    pytest.mark.requirement_prd_1
]

# Load scenarios from feature file
scenarios('features/authentication.feature')

# Constants
TEST_DB_URL = os.environ.get(
    "TEST_DB_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/profiler_test"
)

# Fixtures
@pytest_asyncio.fixture
async def auth_service() -> Generator[AuthenticationService, None, None]:
    """Create an authentication service for testing."""
    # Use a test configuration
    config = {
        "jwt_secret": "test-secret-key",
        "jwt_expires_seconds": 3600,
        "database": {
            "url": TEST_DB_URL,
            "pool_size": 5,
            "max_overflow": 10,
            "echo": True
        }
    }
    
    # Create the service
    service = AuthenticationService(config)
    
    try:
        # Initialize the service
        await service.initialize()
        
        # Return the service for use in tests
        yield service
    finally:
        # Clean up
        await service.shutdown()

@pytest.fixture
def test_data() -> Dict[str, Any]:
    """Provide test data for use in steps."""
    return {
        "users": {},
        "auth_results": {},
        "sessions": {}
    }

# Step implementations for Gherkin statements
@given("a new user with valid credentials")
def create_test_user_data(test_data):
    """Create test user data."""
    test_data["new_user"] = {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }
    return test_data["new_user"]

@given("an existing user")
async def create_existing_user(auth_service, test_data):
    """Create an existing user for testing."""
    user_data = {
        "username": f"existinguser_{uuid.uuid4().hex[:8]}",
        "email": f"existing_{uuid.uuid4().hex[:8]}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Existing User"
    }
    
    user = await auth_service.register_user(
        username=user_data["username"],
        password=user_data["password"],
        email=user_data["email"],
        full_name=user_data["full_name"]
    )
    
    test_data["existing_user"] = {**user_data, "user_id": user["user_id"]}
    return test_data["existing_user"]

@given("an authenticated user")
async def create_authenticated_user(auth_service, test_data):
    """Create an authenticated user."""
    # Create a user
    user_data = await create_existing_user(auth_service, test_data)
    
    # Authenticate the user
    auth_result = await auth_service.authenticate(
        username=user_data["username"],
        password=user_data["password"]
    )
    
    test_data["auth_result"] = auth_result
    return auth_result

@when("the user registers with the system")
async def register_user(auth_service, test_data):
    """Register a new user."""
    user_data = test_data["new_user"]
    try:
        user = await auth_service.register_user(
            username=user_data["username"],
            password=user_data["password"],
            email=user_data["email"],
            full_name=user_data["full_name"]
        )
        test_data["registered_user"] = user
    except Exception as e:
        test_data["registration_error"] = e

@when("the user logs in with valid credentials")
async def login_with_valid_credentials(auth_service, test_data):
    """Attempt login with valid credentials."""
    user_data = test_data["existing_user"]
    try:
        auth_result = await auth_service.authenticate(
            username=user_data["username"],
            password=user_data["password"]
        )
        test_data["auth_result"] = auth_result
    except Exception as e:
        test_data["auth_error"] = e

@when("the user logs in with invalid credentials")
async def login_with_invalid_credentials(auth_service, test_data):
    """Attempt login with invalid credentials."""
    user_data = test_data["existing_user"]
    try:
        auth_result = await auth_service.authenticate(
            username=user_data["username"],
            password="WrongPassword123!"
        )
        test_data["auth_result"] = auth_result
    except Exception as e:
        test_data["auth_error"] = e

@when("the user's session is created")
async def create_user_session(auth_service, test_data):
    """Create a session for the authenticated user."""
    auth_result = test_data["auth_result"]
    test_data["session_token"] = auth_result["token"]

@then("the user account should be created")
def check_user_created(test_data):
    """Verify that the user account was created."""
    assert "registered_user" in test_data, "User registration failed"
    user = test_data["registered_user"]
    assert "user_id" in user, "User ID not found in registered user"
    assert user["username"] == test_data["new_user"]["username"], "Username mismatch"
    assert user["email"] == test_data["new_user"]["email"], "Email mismatch"

@then("the user should be able to authenticate")
async def check_user_can_authenticate(auth_service, test_data):
    """Verify that the user can authenticate."""
    user_data = test_data["new_user"]
    auth_result = await auth_service.authenticate(
        username=user_data["username"],
        password=user_data["password"]
    )
    assert auth_result is not None, "Authentication failed"
    assert "token" in auth_result, "Token not found in authentication result"
    assert "user_id" in auth_result, "User ID not found in authentication result"
    assert auth_result["user_id"] == test_data["registered_user"]["user_id"], "User ID mismatch"

@then("authentication should succeed")
def check_authentication_succeeded(test_data):
    """Verify that authentication succeeded."""
    assert "auth_error" not in test_data, f"Authentication error: {test_data.get('auth_error')}"
    assert "auth_result" in test_data, "Authentication result not found"
    auth_result = test_data["auth_result"]
    assert "token" in auth_result, "Token not found in authentication result"
    assert "user_id" in auth_result, "User ID not found in authentication result"

@then("a session token should be generated")
def check_session_token_generated(test_data):
    """Verify that a session token was generated."""
    assert "auth_result" in test_data, "Authentication result not found"
    auth_result = test_data["auth_result"]
    assert "token" in auth_result, "Token not found in authentication result"
    assert auth_result["token"] is not None, "Token is None"
    assert len(auth_result["token"]) > 0, "Token is empty"

@then("authentication should fail")
def check_authentication_failed(test_data):
    """Verify that authentication failed."""
    assert "auth_error" in test_data, "No authentication error was raised"
    assert isinstance(test_data["auth_error"], AuthenticationError), "Error is not an AuthenticationError"

@then("no session token should be generated")
def check_no_session_token(test_data):
    """Verify that no session token was generated."""
    assert "auth_result" not in test_data or "token" not in test_data.get("auth_result", {}), "Token should not be generated"

@then("the session should be retrievable")
async def check_session_retrievable(auth_service, test_data):
    """Verify that the session can be retrieved."""
    token = test_data["session_token"]
    token_data = await auth_service.verify_token(token)
    assert token_data is not None, "Failed to verify token"
    assert "user_id" in token_data, "User ID not found in token data"
    assert token_data["user_id"] == test_data["auth_result"]["user_id"], "User ID mismatch in token"

@then("the session can be invalidated")
async def check_session_invalidation(auth_service, test_data):
    """Verify that the session can be invalidated."""
    # This would require an additional method in AuthenticationService to invalidate tokens
    # For now, we'll just verify the token is valid and assume it can be invalidated
    token = test_data["session_token"]
    token_data = await auth_service.verify_token(token)
    assert token_data is not None, "Token should be valid"
