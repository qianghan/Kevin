"""
Recommendation repository interfaces and implementations.

This module provides repositories for storing and retrieving recommendations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
import uuid

from profiler.services.recommendation.models import Recommendation


class IRecommendationRepository(ABC):
    """Interface for recommendation repositories."""
    
    @abstractmethod
    async def save_recommendation(self, recommendation: Recommendation) -> Recommendation:
        """
        Save a recommendation.
        
        Args:
            recommendation: The recommendation to save
            
        Returns:
            The saved recommendation with updated ID
        """
        pass
    
    @abstractmethod
    async def get_recommendations_for_user(self, user_id: str, status: Optional[str] = None) -> List[Recommendation]:
        """
        Get recommendations for a user.
        
        Args:
            user_id: The ID of the user
            status: Optional status to filter by
            
        Returns:
            A list of recommendations for the user
        """
        pass
    
    @abstractmethod
    async def get_recommendation_by_id(self, recommendation_id: str) -> Optional[Recommendation]:
        """
        Get a recommendation by ID.
        
        Args:
            recommendation_id: The ID of the recommendation
            
        Returns:
            The recommendation, or None if not found
        """
        pass
    
    @abstractmethod
    async def update_recommendation_status(self, recommendation_id: str, status: str) -> Optional[Recommendation]:
        """
        Update the status of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation
            status: The new status
            
        Returns:
            The updated recommendation, or None if not found
        """
        pass
    
    @abstractmethod
    async def update_recommendation_progress(self, recommendation_id: str, progress: float) -> Optional[Recommendation]:
        """
        Update the progress of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation
            progress: The new progress value (0.0 to 1.0)
            
        Returns:
            The updated recommendation, or None if not found
        """
        pass
    
    @abstractmethod
    async def get_recommendation_history(
        self, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Recommendation]:
        """
        Get recommendation history for a user.
        
        Args:
            user_id: The ID of the user
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            A list of recommendations for the user within the date range
        """
        pass


class InMemoryRecommendationRepository(IRecommendationRepository):
    """In-memory implementation of the recommendation repository."""
    
    def __init__(self):
        """Initialize the in-memory repository."""
        self.recommendations: Dict[str, Recommendation] = {}
    
    async def save_recommendation(self, recommendation: Recommendation) -> Recommendation:
        """
        Save a recommendation.
        
        Args:
            recommendation: The recommendation to save
            
        Returns:
            The saved recommendation with updated ID
        """
        # Generate ID if not provided
        if not recommendation.id:
            recommendation.id = str(uuid.uuid4())
        
        # Set created_at if not provided
        if not recommendation.created_at:
            recommendation.created_at = datetime.now(UTC)
        
        # Save the recommendation
        self.recommendations[recommendation.id] = recommendation
        
        return recommendation
    
    async def get_recommendations_for_user(self, user_id: str, status: Optional[str] = None) -> List[Recommendation]:
        """
        Get recommendations for a user.
        
        Args:
            user_id: The ID of the user
            status: Optional status to filter by
            
        Returns:
            A list of recommendations for the user
        """
        user_recommendations = [
            r for r in self.recommendations.values()
            if r.user_id == user_id
        ]
        
        if status:
            user_recommendations = [
                r for r in user_recommendations 
                if r.status == status
            ]
        
        # Sort by priority (descending)
        return sorted(user_recommendations, key=lambda r: r.priority or 0, reverse=True)
    
    async def get_recommendation_by_id(self, recommendation_id: str) -> Optional[Recommendation]:
        """
        Get a recommendation by ID.
        
        Args:
            recommendation_id: The ID of the recommendation
            
        Returns:
            The recommendation, or None if not found
        """
        return self.recommendations.get(recommendation_id)
    
    async def update_recommendation_status(self, recommendation_id: str, status: str) -> Optional[Recommendation]:
        """
        Update the status of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation
            status: The new status
            
        Returns:
            The updated recommendation, or None if not found
        """
        recommendation = await self.get_recommendation_by_id(recommendation_id)
        if not recommendation:
            return None
        
        # Create a copy with updated status
        updated = recommendation.model_copy(update={"status": status})
        
        # Update completed_at if status is "completed"
        if status == "completed" and not updated.completed_at:
            updated = updated.model_copy(update={"completed_at": datetime.now(UTC)})
        
        # Save the updated recommendation
        self.recommendations[recommendation_id] = updated
        
        return updated
    
    async def update_recommendation_progress(self, recommendation_id: str, progress: float) -> Optional[Recommendation]:
        """
        Update the progress of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation
            progress: The new progress value (0.0 to 1.0)
            
        Returns:
            The updated recommendation, or None if not found
        """
        recommendation = await self.get_recommendation_by_id(recommendation_id)
        if not recommendation:
            return None
        
        # Ensure progress is between 0 and 1
        progress = max(0.0, min(1.0, progress))
        
        # Create a copy with updated progress
        updated = recommendation.model_copy(update={"progress": progress})
        
        # If progress is 100%, mark as completed
        if progress >= 1.0 and updated.status != "completed":
            updated = updated.model_copy(update={
                "status": "completed",
                "completed_at": datetime.now(UTC)
            })
        
        # Save the updated recommendation
        self.recommendations[recommendation_id] = updated
        
        return updated
    
    async def get_recommendation_history(
        self, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Recommendation]:
        """
        Get recommendation history for a user.
        
        Args:
            user_id: The ID of the user
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            A list of recommendations for the user within the date range
        """
        user_recommendations = [
            r for r in self.recommendations.values()
            if r.user_id == user_id
        ]
        
        if start_date:
            user_recommendations = [
                r for r in user_recommendations 
                if r.created_at and r.created_at >= start_date
            ]
        
        if end_date:
            user_recommendations = [
                r for r in user_recommendations 
                if r.created_at and r.created_at <= end_date
            ]
        
        # Sort by created_at (descending)
        return sorted(user_recommendations, key=lambda r: r.created_at or datetime.min, reverse=True)


class SqlAlchemyRecommendationRepository(IRecommendationRepository):
    """SQLAlchemy implementation of the recommendation repository."""
    
    def __init__(self, session_factory):
        """Initialize the SQLAlchemy repository.
        
        Args:
            session_factory: Factory for creating database sessions.
        """
        self.session_factory = session_factory
    
    async def save_recommendation(self, recommendation: Recommendation) -> Optional[Recommendation]:
        """Save a recommendation.
        
        Args:
            recommendation: The recommendation to save.
            
        Returns:
            The saved recommendation, or None if the save failed.
        """
        # In a real implementation, this would save to a database using SQLAlchemy
        # For now, we'll return a mock implementation
        if not recommendation.id:
            recommendation.id = str(uuid.uuid4())
        
        if not recommendation.created_at:
            recommendation.created_at = datetime.now(UTC)
        
        return recommendation
    
    async def get_recommendations_for_user(self, user_id: str, status: Optional[str] = None) -> List[Recommendation]:
        """Get recommendations for a user.
        
        Args:
            user_id: The ID of the user to get recommendations for.
            status: Filter by recommendation status (active, completed, dismissed).
            
        Returns:
            A list of recommendations for the user.
        """
        # In a real implementation, this would query the database
        # For now, return an empty list
        return []
    
    async def get_recommendation_by_id(self, recommendation_id: str) -> Optional[Recommendation]:
        """Get a recommendation by ID.
        
        Args:
            recommendation_id: The ID of the recommendation to get.
            
        Returns:
            The recommendation, or None if not found.
        """
        # In a real implementation, this would query the database
        # For now, return None
        return None
    
    async def update_recommendation_status(self, recommendation_id: str, status: str) -> Optional[Recommendation]:
        """Update the status of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation to update.
            status: The new status (active, completed, dismissed).
            
        Returns:
            The updated recommendation, or None if not found.
        """
        # In a real implementation, this would update the database
        # For now, return None
        return None
    
    async def update_recommendation_progress(self, recommendation_id: str, progress: float) -> Optional[Recommendation]:
        """Update the progress of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation to update.
            progress: The new progress value (0.0 to 1.0).
            
        Returns:
            The updated recommendation, or None if not found.
        """
        # In a real implementation, this would update the database
        # For now, return None
        return None
    
    async def get_recommendation_history(self, user_id: str, start_date: Optional[datetime] = None, 
                                      end_date: Optional[datetime] = None) -> List[Recommendation]:
        """Get recommendation history for a user.
        
        Args:
            user_id: The ID of the user to get recommendation history for.
            start_date: The start date for filtering recommendations.
            end_date: The end date for filtering recommendations.
            
        Returns:
            A list of recommendations for the user within the specified date range.
        """
        # In a real implementation, this would query the database
        # For now, return an empty list
        return [] 