"""
Factory for creating recommendation service instances.

This module provides factory methods to create instances of recommendation services.
"""

import os
from typing import Optional

from app.backend.interfaces.recommendation import IRecommendationService
from app.backend.services.recommendation.service import RecommendationService


class RecommendationServiceFactory:
    """Factory for creating recommendation service instances."""
    
    @staticmethod
    def create_service(service_type: Optional[str] = None) -> IRecommendationService:
        """
        Create a recommendation service instance.
        
        Args:
            service_type: The type of recommendation service to create (default: from environment)
            
        Returns:
            An instance of a recommendation service
        """
        # Get service type from environment if not provided
        if service_type is None:
            service_type = os.getenv("RECOMMENDATION_SERVICE_TYPE", "default")
        
        # Create the appropriate service
        if service_type == "default":
            return RecommendationService()
        else:
            raise ValueError(f"Unsupported recommendation service type: {service_type}")
    
    @staticmethod
    def create_mock_service() -> IRecommendationService:
        """
        Create a mock recommendation service for testing.
        
        Returns:
            A mock recommendation service instance
        """
        # Create a service with mock configuration
        service = RecommendationService()
        
        # Configure the service for testing
        service.configure({
            "model": "mock",
            "categories": ["academic", "extracurricular", "personal"],
            "max_recommendations": 10
        })
        
        return service 