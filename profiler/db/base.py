"""
SQLAlchemy model base classes.

This module provides base classes for SQLAlchemy models.
"""

from sqlalchemy.ext.declarative import declarative_base


# Create a base class for SQLAlchemy models
Base = declarative_base()


# Import all models to ensure they're registered with SQLAlchemy
# This allows alembic to detect all models for migrations
from profiler.db.models.notification import NotificationDB  # noqa


# Base class for model definition
class BaseClass:
    """Base class for all SQLAlchemy models."""
    
    # You can add common functionality for all models here, such as:
    # - created_at, updated_at timestamps
    # - soft delete functionality
    # - audit logging
    # - etc.
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}({', '.join(f'{k}={v}' for k, v in self.__dict__.items() if not k.startswith('_'))})>" 