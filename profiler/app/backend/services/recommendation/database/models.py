"""
SQLAlchemy models for Recommendation database implementation.

This module defines SQLAlchemy ORM models for persisting recommendation data to a relational database.
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class RecommendationModel(Base):
    """SQLAlchemy model for recommendations table."""
    __tablename__ = "recommendations"

    id = Column(String(60), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    action_items = relationship("ActionItemModel", back_populates="recommendation", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_recommendations_user_id", user_id),
        Index("idx_recommendations_category", category),
        Index("idx_recommendations_priority", priority),
    )


class ActionItemModel(Base):
    """SQLAlchemy model for recommendation action items."""
    __tablename__ = "action_items"

    id = Column(String(60), primary_key=True)
    recommendation_id = Column(String(60), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    
    # Relationships
    recommendation = relationship("RecommendationModel", back_populates="action_items")

    # Indexes
    __table_args__ = (
        Index("idx_action_items_recommendation_id", recommendation_id),
    )


class ProfileSummaryModel(Base):
    """SQLAlchemy model for profile summaries."""
    __tablename__ = "profile_summaries"

    id = Column(String(60), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True, unique=True)
    overall_quality = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    strengths = relationship("ProfileStrengthModel", back_populates="profile_summary", cascade="all, delete-orphan")
    improvements = relationship("ProfileImprovementModel", back_populates="profile_summary", cascade="all, delete-orphan")
    selling_points = relationship("ProfileSellingPointModel", back_populates="profile_summary", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_profile_summaries_user_id", user_id),
    )


class ProfileStrengthModel(Base):
    """SQLAlchemy model for profile strengths."""
    __tablename__ = "profile_strengths"

    id = Column(String(60), primary_key=True)
    summary_id = Column(String(60), ForeignKey("profile_summaries.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    
    # Relationships
    profile_summary = relationship("ProfileSummaryModel", back_populates="strengths")

    # Indexes
    __table_args__ = (
        Index("idx_profile_strengths_summary_id", summary_id),
    )


class ProfileImprovementModel(Base):
    """SQLAlchemy model for profile improvement areas."""
    __tablename__ = "profile_improvements"

    id = Column(String(60), primary_key=True)
    summary_id = Column(String(60), ForeignKey("profile_summaries.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    
    # Relationships
    profile_summary = relationship("ProfileSummaryModel", back_populates="improvements")

    # Indexes
    __table_args__ = (
        Index("idx_profile_improvements_summary_id", summary_id),
    )


class ProfileSellingPointModel(Base):
    """SQLAlchemy model for profile unique selling points."""
    __tablename__ = "profile_selling_points"

    id = Column(String(60), primary_key=True)
    summary_id = Column(String(60), ForeignKey("profile_summaries.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    
    # Relationships
    profile_summary = relationship("ProfileSummaryModel", back_populates="selling_points")

    # Indexes
    __table_args__ = (
        Index("idx_profile_selling_points_summary_id", summary_id),
    ) 