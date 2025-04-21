"""
Base class for SQLAlchemy models.

This module provides the base class for all SQLAlchemy models in the application.
"""

from typing import Any
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """
    Base class for all SQLAlchemy models.
    
    Provides common functionality like automatic __tablename__ generation
    and common columns like created_at and updated_at.
    """
    
    # Make SQLAlchemy know these are not columns
    __name__: str
    
    # Generate __tablename__ automatically based on class name
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    # Common columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        attributes = []
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, datetime):
                    value = value.isoformat()
                attributes.append(f"{key}={value}")
        return f"<{self.__class__.__name__}({', '.join(attributes)})>" 