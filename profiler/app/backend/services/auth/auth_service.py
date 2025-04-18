"""
Authentication and Authorization Service for the Profiler application.

This module provides user authentication, authorization, and data ownership management.
"""

import logging
import uuid
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

import jwt
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..profile.database.connection import DatabaseManager
from ...utils.errors import AuthenticationError, AuthorizationError, ResourceNotFoundError
from ...utils.config_manager import ConfigManager
from .models import User, Role, Permission, UserRole

logger = logging.getLogger(__name__)

class AuthenticationService:
    """Service for user authentication and authorization."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the authentication service.
        
        Args:
            config: Optional configuration dictionary. If not provided,
                   configuration will be loaded from the config manager.
        """
        self._config = config or ConfigManager().get_value(["security"], {})
        self._db_manager = DatabaseManager(config)
        self._initialized = False
        self._jwt_secret = self._config.get("jwt_secret", "default-secret-key")
        self._jwt_expires_seconds = int(self._config.get("jwt_expires_seconds", 86400))  # 24 hours by default
        
    async def initialize(self) -> None:
        """Initialize the authentication service."""
        if self._initialized:
            return
            
        await self._db_manager.initialize()
        
        # Create default roles if they don't exist
        await self._create_default_roles()
        
        self._initialized = True
        logger.info("Authentication service initialized")
        
    async def shutdown(self) -> None:
        """Shutdown the authentication service."""
        if self._db_manager:
            await self._db_manager.shutdown()
        self._initialized = False
        logger.info("Authentication service shut down")
        
    async def _create_default_roles(self) -> None:
        """Create default roles and permissions if they don't exist."""
        default_roles = [
            {
                "name": "admin",
                "description": "Administrator with full access",
                "permissions": ["*"]
            },
            {
                "name": "user",
                "description": "Standard user with basic access",
                "permissions": [
                    "profile:read:own", 
                    "profile:write:own",
                    "document:read:own",
                    "document:write:own"
                ]
            },
            {
                "name": "guest",
                "description": "Guest with limited access",
                "permissions": [
                    "profile:read:shared"
                ]
            }
        ]
        
        async with self._db_manager.get_session() as session:
            async with session.begin():
                for role_data in default_roles:
                    # Check if role exists
                    stmt = select(Role).where(Role.name == role_data["name"])
                    result = await session.execute(stmt)
                    role = result.scalar_one_or_none()
                    
                    if not role:
                        # Create role
                        role = Role(
                            role_id=str(uuid.uuid4()),
                            name=role_data["name"],
                            description=role_data["description"],
                            created_at=datetime.utcnow()
                        )
                        session.add(role)
                        
                        # Create permissions
                        for perm_str in role_data["permissions"]:
                            permission = Permission(
                                permission_id=str(uuid.uuid4()),
                                role_id=role.role_id,
                                permission=perm_str,
                                created_at=datetime.utcnow()
                            )
                            session.add(permission)
        
    async def register_user(self, username: str, password: str, email: str, 
                           full_name: Optional[str] = None, role: str = "user") -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: Username for the new user
            password: Password for the new user
            email: Email address for the new user
            full_name: Optional full name for the new user
            role: Role for the new user (default: "user")
            
        Returns:
            Newly created user information (without password)
            
        Raises:
            AuthenticationError: If registration fails
        """
        # Validate inputs
        if not username or not password or not email:
            raise AuthenticationError("Username, password, and email are required")
            
        # Check if username or email already exists
        async with self._db_manager.get_session() as session:
            stmt = select(User).where(
                (User.username == username) | (User.email == email)
            )
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise AuthenticationError("Username or email already exists")
            
            # Get role ID
            stmt = select(Role).where(Role.name == role)
            result = await session.execute(stmt)
            role_obj = result.scalar_one_or_none()
            
            if not role_obj:
                logger.warning(f"Role '{role}' not found, using default 'user' role")
                # Get user role instead
                stmt = select(Role).where(Role.name == "user")
                result = await session.execute(stmt)
                role_obj = result.scalar_one_or_none()
                
                if not role_obj:
                    raise AuthenticationError("Default role not found")
            
            # Generate password hash and salt
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            # Create user
            user_id = str(uuid.uuid4())
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                password_hash=password_hash,
                password_salt=salt,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                status="active"
            )
            
            # Create user role association
            user_role = UserRole(
                user_id=user_id,
                role_id=role_obj.role_id,
                created_at=datetime.utcnow()
            )
            
            # Save to database
            async with session.begin():
                session.add(user)
                session.add(user_role)
            
            # Return user info (without password)
            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat(),
                "status": user.status,
                "role": role
            }
    
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user and return a JWT token.
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            Dictionary with token, expiration and user info
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Find user by username or email
        async with self._db_manager.get_session() as session:
            stmt = select(User).where(
                (User.username == username) | (User.email == username)
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or user.status != "active":
                raise AuthenticationError("Invalid username or password")
            
            # Verify password
            password_hash = self._hash_password(password, user.password_salt)
            if password_hash != user.password_hash:
                raise AuthenticationError("Invalid username or password")
            
            # Get user roles and permissions
            roles, permissions = await self._get_user_roles_and_permissions(session, user.user_id)
            
            # Generate JWT token
            now = int(time.time())
            expires_at = now + self._jwt_expires_seconds
            
            token_data = {
                "sub": user.user_id,
                "username": user.username,
                "email": user.email,
                "roles": roles,
                "permissions": permissions,
                "iat": now,
                "exp": expires_at
            }
            
            token = jwt.encode(token_data, self._jwt_secret, algorithm="HS256")
            
            return {
                "token": token,
                "expires_at": expires_at,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "roles": roles
                }
            }
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a JWT token and return user info.
        
        Args:
            token: JWT token
            
        Returns:
            Dictionary with user info
            
        Raises:
            AuthenticationError: If the token is invalid or expired
        """
        try:
            # Decode token
            payload = jwt.decode(token, self._jwt_secret, algorithms=["HS256"])
            
            # Check if token is expired
            now = int(time.time())
            if payload["exp"] < now:
                raise AuthenticationError("Token has expired")
            
            # Verify user exists and is active
            async with self._db_manager.get_session() as session:
                stmt = select(User).where(
                    (User.user_id == payload["sub"]) & (User.status == "active")
                )
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    raise AuthenticationError("User not found or inactive")
            
            return payload
            
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    async def authorize(self, user_id: str, permission: str, resource_id: Optional[str] = None) -> bool:
        """
        Check if a user has the specified permission.
        
        Args:
            user_id: User ID
            permission: Permission to check (e.g., "profile:read")
            resource_id: Optional resource ID (for ownership checks)
            
        Returns:
            True if authorized, False otherwise
        """
        async with self._db_manager.get_session() as session:
            # Get user permissions
            _, permissions = await self._get_user_roles_and_permissions(session, user_id)
            
            # Check for wildcard permission
            if "*" in permissions:
                return True
            
            # Parse permission string
            parts = permission.split(":")
            if len(parts) < 2:
                return False
                
            resource_type, action = parts[0], parts[1]
            scope = parts[2] if len(parts) > 2 else None
            
            # Check for exact permission match
            if permission in permissions:
                return True
            
            # Check for resource type wildcard
            if f"{resource_type}:*" in permissions:
                return True
                
            # Check for action wildcard
            if f"{resource_type}:{action}:*" in permissions:
                return True
            
            # Check ownership if scope is "own"
            if scope == "own" and resource_id:
                # Check if user owns the resource
                if await self._check_resource_ownership(session, user_id, resource_type, resource_id):
                    # Check if user has permission for owned resources
                    if f"{resource_type}:{action}:own" in permissions:
                        return True
            
            # Check for shared resources
            if scope == "shared" and resource_id:
                # Check if resource is shared with the user
                if await self._check_resource_shared(session, user_id, resource_type, resource_id):
                    # Check if user has permission for shared resources
                    if f"{resource_type}:{action}:shared" in permissions:
                        return True
            
            return False
    
    async def _get_user_roles_and_permissions(self, session: AsyncSession, user_id: str) -> Tuple[List[str], List[str]]:
        """
        Get a user's roles and permissions.
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            Tuple of (roles, permissions)
        """
        # Get user roles
        stmt = select(Role).join(UserRole).where(UserRole.user_id == user_id)
        result = await session.execute(stmt)
        roles = [role.name for role in result.scalars().all()]
        
        # Get role IDs
        stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
        result = await session.execute(stmt)
        role_ids = [r[0] for r in result.all()]
        
        # Get permissions for these roles
        stmt = select(Permission.permission).where(Permission.role_id.in_(role_ids))
        result = await session.execute(stmt)
        permissions = [perm[0] for perm in result.all()]
        
        return roles, permissions
    
    async def _check_resource_ownership(self, session: AsyncSession, user_id: str, 
                                       resource_type: str, resource_id: str) -> bool:
        """
        Check if a user owns a resource.
        
        Args:
            session: Database session
            user_id: User ID
            resource_type: Resource type (e.g., "profile")
            resource_id: Resource ID
            
        Returns:
            True if the user owns the resource, False otherwise
        """
        if resource_type == "profile":
            from ..profile.database.models import ProfileModel
            stmt = select(ProfileModel).where(
                (ProfileModel.profile_id == resource_id) & 
                (ProfileModel.user_id == user_id)
            )
            result = await session.execute(stmt)
            profile = result.scalar_one_or_none()
            return profile is not None
            
        elif resource_type == "document":
            from ..document.database.models import DocumentModel
            stmt = select(DocumentModel).where(
                (DocumentModel.document_id == resource_id) & 
                (DocumentModel.user_id == user_id)
            )
            result = await session.execute(stmt)
            document = result.scalar_one_or_none()
            return document is not None
        
        # Default to False for unknown resource types
        return False
    
    async def _check_resource_shared(self, session: AsyncSession, user_id: str, 
                                    resource_type: str, resource_id: str) -> bool:
        """
        Check if a resource is shared with a user.
        
        Args:
            session: Database session
            user_id: User ID
            resource_type: Resource type (e.g., "profile")
            resource_id: Resource ID
            
        Returns:
            True if the resource is shared with the user, False otherwise
        """
        # Implementation for shared resources would go here
        # This would typically involve a sharing table that records which
        # resources are shared with which users
        
        # For now, return False
        return False
        
    def _hash_password(self, password: str, salt: str) -> str:
        """
        Hash a password with the given salt.
        
        Args:
            password: Password to hash
            salt: Salt to use
            
        Returns:
            Hashed password
        """
        # Combine password and salt
        salted = (password + salt).encode('utf-8')
        
        # Hash using SHA-256
        hash_obj = hashlib.sha256(salted)
        
        # Return hex digest
        return hash_obj.hexdigest()
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if password was changed successfully
            
        Raises:
            AuthenticationError: If the current password is incorrect
            ResourceNotFoundError: If the user doesn't exist
        """
        if not new_password or len(new_password) < 8:
            raise AuthenticationError("New password must be at least 8 characters")
            
        async with self._db_manager.get_session() as session:
            # Get user
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise ResourceNotFoundError(f"User {user_id} not found")
                
            # Verify current password
            current_hash = self._hash_password(current_password, user.password_salt)
            if current_hash != user.password_hash:
                raise AuthenticationError("Current password is incorrect")
                
            # Hash new password
            new_salt = secrets.token_hex(16)
            new_hash = self._hash_password(new_password, new_salt)
            
            # Update password
            user.password_hash = new_hash
            user.password_salt = new_salt
            user.last_updated = datetime.utcnow()
            
            # Save to database
            async with session.begin():
                session.add(user)
                
            return True
            
    async def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            data: Dictionary with fields to update
            
        Returns:
            Updated user information
            
        Raises:
            ResourceNotFoundError: If the user doesn't exist
        """
        allowed_fields = ["email", "full_name", "status"]
        
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        if not update_data:
            return {}
            
        async with self._db_manager.get_session() as session:
            # Get user
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise ResourceNotFoundError(f"User {user_id} not found")
                
            # Update fields
            for key, value in update_data.items():
                setattr(user, key, value)
                
            user.last_updated = datetime.utcnow()
            
            # Save to database
            async with session.begin():
                session.add(user)
                
            # Return updated user info
            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat(),
                "last_updated": user.last_updated.isoformat(),
                "status": user.status
            }
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information.
        
        Args:
            user_id: User ID
            
        Returns:
            User information
            
        Raises:
            ResourceNotFoundError: If the user doesn't exist
        """
        async with self._db_manager.get_session() as session:
            # Get user
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise ResourceNotFoundError(f"User {user_id} not found")
                
            # Get roles
            roles, _ = await self._get_user_roles_and_permissions(session, user_id)
                
            # Return user info
            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat(),
                "last_updated": user.last_updated.isoformat(),
                "status": user.status,
                "roles": roles
            }
    
    async def list_users(self) -> List[Dict[str, Any]]:
        """
        List all users.
        
        Returns:
            List of user information dictionaries
        """
        async with self._db_manager.get_session() as session:
            # Get all users
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            # Build user info list
            user_list = []
            for user in users:
                roles, _ = await self._get_user_roles_and_permissions(session, user.user_id)
                user_list.append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "created_at": user.created_at.isoformat(),
                    "last_updated": user.last_updated.isoformat(),
                    "status": user.status,
                    "roles": roles
                })
                
            return user_list 