"""
Factory for creating QA service instances.

This module provides factory methods to create instances of QA services.
"""

import os
from typing import Optional

from app.backend.interfaces.qa import IQAService
from app.backend.services.qa.service import QAService


class QAServiceFactory:
    """Factory for creating QA service instances."""
    
    @staticmethod
    def create_service(service_type: Optional[str] = None) -> IQAService:
        """
        Create a QA service instance.
        
        Args:
            service_type: The type of QA service to create (default: from environment)
            
        Returns:
            An instance of a QA service
        """
        # Get service type from environment if not provided
        if service_type is None:
            service_type = os.getenv("QA_SERVICE_TYPE", "default")
        
        # Create the appropriate service
        if service_type == "default":
            return QAService()
        else:
            raise ValueError(f"Unsupported QA service type: {service_type}")
    
    @staticmethod
    def create_mock_service() -> IQAService:
        """
        Create a mock QA service for testing.
        
        Returns:
            A mock QA service instance
        """
        # Create a service with mock configuration
        service = QAService()
        
        # Configure the service for testing
        service.configure({
            "model": "mock",
            "max_questions": 5,
            "use_cache": False
        })
        
        return service 