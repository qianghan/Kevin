"""
PostgreSQL repository implementation for Recommendation Service.

This module provides a concrete implementation of the recommendation repository using PostgreSQL.
"""

import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.backend.utils.errors import DatabaseError
from app.backend.utils.logging import get_logger
from ..models import Recommendation, ProfileSummary
from .connection import DatabaseManager
from .models import (
    RecommendationModel, ActionItemModel, 
    ProfileSummaryModel, ProfileStrengthModel, 
    ProfileImprovementModel, ProfileSellingPointModel
)

logger = get_logger(__name__)


class PostgreSQLRecommendationRepository:
    """Repository for storing and retrieving recommendations using PostgreSQL."""
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the repository.
        
        Args:
            db_config: Optional database configuration dictionary
        """
        self.db_manager = DatabaseManager(db_config)
    
    async def initialize(self) -> None:
        """
        Initialize the repository, setting up database connection.
        
        Raises:
            DatabaseError: If the database cannot be initialized.
        """
        try:
            await self.db_manager.initialize()
            logger.info("Initialized PostgreSQLRecommendationRepository")
        except Exception as e:
            logger.error(f"Failed to initialize recommendation repository: {str(e)}")
            raise DatabaseError(f"Failed to initialize recommendation repository: {str(e)}")
    
    async def shutdown(self) -> None:
        """
        Shutdown the repository, closing database connection.
        """
        await self.db_manager.shutdown()
        logger.info("Shutdown PostgreSQLRecommendationRepository")
    
    async def store_recommendations(self, user_id: str, recommendations: List[Recommendation]) -> None:
        """
        Store recommendations for a user.
        
        Args:
            user_id: The ID of the user.
            recommendations: List of recommendations to store.
            
        Raises:
            DatabaseError: If recommendations cannot be stored.
        """
        try:
            logger.info(f"Storing {len(recommendations)} recommendations for user: {user_id}")
            
            timestamp = datetime.now(timezone.utc)
            
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Delete existing recommendations for the user (optional, depends on your use case)
                    await session.execute(
                        delete(RecommendationModel).where(
                            RecommendationModel.user_id == user_id
                        )
                    )
                    
                    # Store each recommendation
                    for rec in recommendations:
                        rec_id = str(uuid.uuid4())
                        
                        # Create recommendation model
                        rec_model = RecommendationModel(
                            id=rec_id,
                            user_id=user_id,
                            category=rec.category,
                            title=rec.title,
                            description=rec.description,
                            priority=rec.priority,
                            confidence=rec.confidence,
                            created_at=timestamp
                        )
                        session.add(rec_model)
                        
                        # Create action item models
                        for i, action_item in enumerate(rec.action_items):
                            action_model = ActionItemModel(
                                id=str(uuid.uuid4()),
                                recommendation_id=rec_id,
                                description=action_item,
                                order=i
                            )
                            session.add(action_model)
            
            logger.info(f"Successfully stored recommendations for user: {user_id}")
        except Exception as e:
            logger.exception(f"Failed to store recommendations for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to store recommendations: {str(e)}")
    
    async def get_recommendations(self, user_id: str, category: Optional[str] = None, 
                                limit: int = 10) -> List[Recommendation]:
        """
        Retrieve recommendations for a user.
        
        Args:
            user_id: The ID of the user.
            category: Optional category to filter by.
            limit: Maximum number of recommendations to return.
            
        Returns:
            List of Recommendation objects.
            
        Raises:
            DatabaseError: If recommendations cannot be retrieved.
        """
        try:
            logger.info(f"Retrieving recommendations for user: {user_id}")
            
            async with self.db_manager.get_session() as session:
                # Build query
                query = select(RecommendationModel).where(
                    RecommendationModel.user_id == user_id
                )
                
                # Add category filter if provided
                if category:
                    query = query.where(RecommendationModel.category == category)
                
                # Add ordering and limit
                query = query.order_by(
                    RecommendationModel.priority.desc(),
                    RecommendationModel.created_at.desc()
                ).limit(limit)
                
                # Execute query
                result = await session.execute(query)
                recommendation_models = result.scalars().all()
                
                # Build Recommendation objects
                recommendations = []
                for rec_model in recommendation_models:
                    # Get action items for this recommendation
                    action_query = select(ActionItemModel).where(
                        ActionItemModel.recommendation_id == rec_model.id
                    ).order_by(ActionItemModel.order)
                    
                    action_result = await session.execute(action_query)
                    action_models = action_result.scalars().all()
                    
                    # Extract action items
                    action_items = [action.description for action in action_models]
                    
                    # Create Recommendation object
                    recommendation = Recommendation(
                        category=rec_model.category,
                        title=rec_model.title,
                        description=rec_model.description,
                        priority=rec_model.priority,
                        action_items=action_items,
                        confidence=rec_model.confidence
                    )
                    
                    recommendations.append(recommendation)
            
            logger.info(f"Retrieved {len(recommendations)} recommendations for user: {user_id}")
            return recommendations
            
        except Exception as e:
            logger.exception(f"Failed to retrieve recommendations for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve recommendations: {str(e)}")
    
    async def delete_user_recommendations(self, user_id: str) -> None:
        """
        Delete all recommendations for a user.
        
        Args:
            user_id: The ID of the user.
            
        Raises:
            DatabaseError: If recommendations cannot be deleted.
        """
        try:
            logger.info(f"Deleting recommendations for user: {user_id}")
            
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Delete all recommendations for user (cascades to action items)
                    await session.execute(
                        delete(RecommendationModel).where(
                            RecommendationModel.user_id == user_id
                        )
                    )
            
            logger.info(f"Successfully deleted recommendations for user: {user_id}")
        except Exception as e:
            logger.exception(f"Failed to delete recommendations for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete recommendations: {str(e)}")
    
    async def store_profile_summary(self, user_id: str, summary: ProfileSummary) -> None:
        """
        Store a profile summary for a user.
        
        Args:
            user_id: The ID of the user.
            summary: The profile summary to store.
            
        Raises:
            DatabaseError: If the summary cannot be stored.
        """
        try:
            logger.info(f"Storing profile summary for user: {user_id}")
            
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Check if a summary already exists for this user
                    existing_query = select(ProfileSummaryModel).where(
                        ProfileSummaryModel.user_id == user_id
                    )
                    result = await session.execute(existing_query)
                    existing_summary = result.scalar_one_or_none()
                    
                    if existing_summary:
                        # Update existing summary
                        summary_id = existing_summary.id
                        existing_summary.overall_quality = summary.overall_quality
                        existing_summary.last_updated = datetime.now(timezone.utc)
                        
                        # Delete existing strengths, improvements, and selling points
                        await session.execute(
                            delete(ProfileStrengthModel).where(
                                ProfileStrengthModel.summary_id == summary_id
                            )
                        )
                        await session.execute(
                            delete(ProfileImprovementModel).where(
                                ProfileImprovementModel.summary_id == summary_id
                            )
                        )
                        await session.execute(
                            delete(ProfileSellingPointModel).where(
                                ProfileSellingPointModel.summary_id == summary_id
                            )
                        )
                    else:
                        # Create new summary
                        summary_id = str(uuid.uuid4())
                        summary_model = ProfileSummaryModel(
                            id=summary_id,
                            user_id=user_id,
                            overall_quality=summary.overall_quality,
                            created_at=datetime.now(timezone.utc),
                            last_updated=datetime.now(timezone.utc)
                        )
                        session.add(summary_model)
                    
                    # Add strengths
                    for i, strength in enumerate(summary.strengths):
                        strength_model = ProfileStrengthModel(
                            id=str(uuid.uuid4()),
                            summary_id=summary_id,
                            description=strength,
                            order=i
                        )
                        session.add(strength_model)
                    
                    # Add areas for improvement
                    for i, improvement in enumerate(summary.areas_for_improvement):
                        improvement_model = ProfileImprovementModel(
                            id=str(uuid.uuid4()),
                            summary_id=summary_id,
                            description=improvement,
                            order=i
                        )
                        session.add(improvement_model)
                    
                    # Add unique selling points
                    for i, selling_point in enumerate(summary.unique_selling_points):
                        selling_point_model = ProfileSellingPointModel(
                            id=str(uuid.uuid4()),
                            summary_id=summary_id,
                            description=selling_point,
                            order=i
                        )
                        session.add(selling_point_model)
            
            logger.info(f"Successfully stored profile summary for user: {user_id}")
        except Exception as e:
            logger.exception(f"Failed to store profile summary for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to store profile summary: {str(e)}")
    
    async def get_profile_summary(self, user_id: str) -> Optional[ProfileSummary]:
        """
        Retrieve a profile summary for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The profile summary or None if not found.
            
        Raises:
            DatabaseError: If the summary cannot be retrieved.
        """
        try:
            logger.info(f"Retrieving profile summary for user: {user_id}")
            
            async with self.db_manager.get_session() as session:
                # Query for summary
                summary_query = select(ProfileSummaryModel).where(
                    ProfileSummaryModel.user_id == user_id
                )
                result = await session.execute(summary_query)
                summary_model = result.scalar_one_or_none()
                
                if not summary_model:
                    logger.info(f"No profile summary found for user: {user_id}")
                    return None
                
                # Query for strengths
                strengths_query = select(ProfileStrengthModel).where(
                    ProfileStrengthModel.summary_id == summary_model.id
                ).order_by(ProfileStrengthModel.order)
                strengths_result = await session.execute(strengths_query)
                strength_models = strengths_result.scalars().all()
                
                # Query for improvements
                improvements_query = select(ProfileImprovementModel).where(
                    ProfileImprovementModel.summary_id == summary_model.id
                ).order_by(ProfileImprovementModel.order)
                improvements_result = await session.execute(improvements_query)
                improvement_models = improvements_result.scalars().all()
                
                # Query for selling points
                selling_points_query = select(ProfileSellingPointModel).where(
                    ProfileSellingPointModel.summary_id == summary_model.id
                ).order_by(ProfileSellingPointModel.order)
                selling_points_result = await session.execute(selling_points_query)
                selling_point_models = selling_points_result.scalars().all()
                
                # Build ProfileSummary object
                summary = ProfileSummary(
                    strengths=[s.description for s in strength_models],
                    areas_for_improvement=[i.description for i in improvement_models],
                    unique_selling_points=[p.description for p in selling_point_models],
                    overall_quality=summary_model.overall_quality,
                    last_updated=summary_model.last_updated.isoformat()
                )
                
                logger.info(f"Retrieved profile summary for user: {user_id}")
                return summary
                
        except Exception as e:
            logger.exception(f"Failed to retrieve profile summary for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve profile summary: {str(e)}")
    
    async def delete_user_summary(self, user_id: str) -> None:
        """
        Delete a profile summary for a user.
        
        Args:
            user_id: The ID of the user.
            
        Raises:
            DatabaseError: If the summary cannot be deleted.
        """
        try:
            logger.info(f"Deleting profile summary for user: {user_id}")
            
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Find summary ID
                    summary_query = select(ProfileSummaryModel).where(
                        ProfileSummaryModel.user_id == user_id
                    )
                    result = await session.execute(summary_query)
                    summary_model = result.scalar_one_or_none()
                    
                    if not summary_model:
                        logger.info(f"No profile summary found for user: {user_id}")
                        return
                    
                    # Delete summary (cascades to related entries)
                    await session.delete(summary_model)
            
            logger.info(f"Successfully deleted profile summary for user: {user_id}")
        except Exception as e:
            logger.exception(f"Failed to delete profile summary for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete profile summary: {str(e)}") 