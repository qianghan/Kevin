"""
SQLAlchemy models for Profile database implementation.

This module defines SQLAlchemy ORM models for persisting profile data to a relational database.
"""

from datetime import datetime
from typing import Dict, Any
import json

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ProfileModel(Base):
    """SQLAlchemy model for Profile table."""
    __tablename__ = "profiles"

    profile_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    current_section = Column(String(50), nullable=False)
    profile_metadata = Column(Text, nullable=True)  # JSON-serialized
    config = Column(Text, nullable=False)  # JSON-serialized
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    status = Column(String(20), default="active", nullable=False)

    # Relationships
    sections = relationship("ProfileSectionModel", back_populates="profile", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_profiles_user_id", user_id),
        Index("idx_profiles_status", status),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "profile_id": self.profile_id,
            "user_id": self.user_id,
            "current_section": self.current_section,
            "metadata": json.loads(self.profile_metadata) if self.profile_metadata else {},
            "config": json.loads(self.config),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "status": self.status,
            "sections": {section.section_id: section.to_dict() for section in self.sections}
        }


class ProfileSectionModel(Base):
    """SQLAlchemy model for ProfileSection table."""
    __tablename__ = "profile_sections"

    id = Column(String(36), primary_key=True)
    profile_id = Column(String(36), ForeignKey("profiles.profile_id", ondelete="CASCADE"), nullable=False)
    section_id = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False)
    data = Column(Text, nullable=True)  # JSON-serialized
    section_metadata = Column(Text, nullable=True)  # JSON-serialized
    completed = Column(Boolean, default=False, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    profile = relationship("ProfileModel", back_populates="sections")

    # Indexes
    __table_args__ = (
        Index("idx_profile_sections_profile_id", profile_id),
        Index("idx_profile_sections_section_id", section_id),
        Index("idx_profile_sections_completed", completed),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "section_id": self.section_id,
            "title": self.title,
            "data": json.loads(self.data) if self.data else {},
            "metadata": json.loads(self.section_metadata) if self.section_metadata else {},
            "completed": self.completed,
            "last_updated": self.last_updated.isoformat(),
        } 