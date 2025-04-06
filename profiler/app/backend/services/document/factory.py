"""
Factory for creating document service instances.

This module provides factory methods to create instances of document services.
"""

import os
from typing import Optional

from app.backend.interfaces.document import IDocumentService
from app.backend.services.document.service import DocumentService


class DocumentServiceFactory:
    """Factory for creating document service instances."""
    
    @staticmethod
    def create_service(service_type: Optional[str] = None) -> IDocumentService:
        """
        Create a document service instance.
        
        Args:
            service_type: The type of document service to create (default: from environment)
            
        Returns:
            An instance of a document service
        """
        # Get service type from environment if not provided
        if service_type is None:
            service_type = os.getenv("DOCUMENT_SERVICE_TYPE", "default")
        
        # Create the appropriate service
        if service_type == "default":
            return DocumentService()
        else:
            raise ValueError(f"Unsupported document service type: {service_type}")
    
    @staticmethod
    def create_mock_service() -> IDocumentService:
        """
        Create a mock document service for testing.
        
        Returns:
            A mock document service instance
        """
        # Create a service with mock configuration
        service = DocumentService()
        
        # Configure the service for testing
        service.configure({
            "model": "mock",
            "max_document_size": 1024 * 1024,  # 1MB
            "supported_document_types": ["transcript", "essay", "resume", "letter"]
        })
        
        return service 