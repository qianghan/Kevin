"""
Authentication and Authorization models for the Profiler application.

This module defines SQLAlchemy ORM models for users, roles, and permissions.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..profile.database.models import Base

class User(Base):
    """SQLAlchemy model for User table."""
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    full_name = Column(String(100), nullable=True)
    password_hash = Column(String(64), nullable=False)
    password_salt = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)
    
    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_users_username", username),
        Index("idx_users_email", email),
        Index("idx_users_status", status),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "status": self.status
        }


class Role(Base):
    """SQLAlchemy model for Role table."""
    __tablename__ = "roles"

    role_id = Column(String(36), primary_key=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    permissions = relationship("Permission", back_populates="role", cascade="all, delete-orphan")
    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_roles_name", name),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "permissions": [perm.permission for perm in self.permissions]
        }


class Permission(Base):
    """SQLAlchemy model for Permission table."""
    __tablename__ = "permissions"

    permission_id = Column(String(36), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False, index=True)
    permission = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    
    # Indexes
    __table_args__ = (
        Index("idx_permissions_role_id", role_id),
        Index("idx_permissions_permission", permission),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "permission_id": self.permission_id,
            "role_id": self.role_id,
            "permission": self.permission,
            "created_at": self.created_at.isoformat()
        }


class UserRole(Base):
    """SQLAlchemy model for UserRole table (many-to-many relation)."""
    __tablename__ = "user_roles"

    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_roles_user_id", user_id),
        Index("idx_user_roles_role_id", role_id),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "user_id": self.user_id,
            "role_id": self.role_id,
            "created_at": self.created_at.isoformat()
        }


# Resource sharing model for implementing "shared" permissions
class ResourceShare(Base):
    """SQLAlchemy model for ResourceShare table."""
    __tablename__ = "resource_shares"

    share_id = Column(String(36), primary_key=True)
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., "profile", "document"
    resource_id = Column(String(36), nullable=False, index=True)
    owner_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    shared_with_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    permissions = Column(String(100), nullable=False)  # comma-separated permissions, e.g., "read,comment"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_resource_shares_resource", resource_type, resource_id),
        Index("idx_resource_shares_owner", owner_id),
        Index("idx_resource_shares_shared_with", shared_with_id),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "share_id": self.share_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "owner_id": self.owner_id,
            "shared_with_id": self.shared_with_id,
            "permissions": self.permissions.split(","),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        } 