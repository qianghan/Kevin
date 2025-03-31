"""
API dependencies and service factories.

This module provides dependency injection for FastAPI endpoints,
including service factories and security mechanisms.
"""

from typing import Dict, Optional, Callable, Any
from fastapi import Depends, Header, HTTPException, status
from functools import lru_cache

from ..utils.config_manager import ConfigManager
from ..utils.errors import AuthenticationError
from ..core.deepseek.r1 import DeepSeekR1
from ..services.interfaces import IDocumentService, IRecommendationService, IQAService, IProfileService
from ..services.recommendation import RecommendationService
from ..services.document_service import DocumentService
from ..services.qa_service import QAServiceFactory
from ..services.qa_service.service import QAService

@lru_cache()
def get_config_manager() -> ConfigManager:
    """
    Get the ConfigManager instance (cached).
    
    Returns:
        ConfigManager: The configuration manager instance
    """
    return ConfigManager()

def get_security_config():
    """
    Get security configuration from the config manager.
    
    Returns:
        Dict: Security configuration
    """
    return get_config_manager().get_security_config()

async def verify_api_key(x_api_key: str = Header(None)):
    """
    Verify that the API key is valid.
    
    Args:
        x_api_key: API key from the request header
        
    Raises:
        HTTPException: If the API key is invalid
    """
    security_config = get_security_config()
    valid_keys = security_config.get("api_keys", [])
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing"
        )
    
    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return x_api_key

class ClientFactory:
    """Factory for creating AI clients."""
    
    _instances = {}
    
    @classmethod
    def get_deepseek_client(cls) -> DeepSeekR1:
        """
        Get a DeepSeekR1 client instance.
        
        Returns:
            DeepSeekR1: The DeepSeek client
        """
        if "deepseek" not in cls._instances:
            cls._instances["deepseek"] = DeepSeekR1()
        return cls._instances["deepseek"]

class ServiceFactory:
    """Factory for creating service instances."""
    
    _instances: Dict[str, Any] = {}
    
    @classmethod
    def get_document_service(cls) -> IDocumentService:
        """
        Get a DocumentService instance.
        
        Returns:
            IDocumentService: The document service
        """
        if "document" not in cls._instances:
            client = ClientFactory.get_deepseek_client()
            cls._instances["document"] = DocumentService(client=client)
        return cls._instances["document"]
    
    @classmethod
    def get_recommendation_service(cls) -> IRecommendationService:
        """
        Get a RecommendationService instance.
        
        Returns:
            IRecommendationService: The recommendation service
        """
        if "recommendation" not in cls._instances:
            client = ClientFactory.get_deepseek_client()
            cls._instances["recommendation"] = RecommendationService(ai_client=client)
        return cls._instances["recommendation"]
    
    @classmethod
    async def get_qa_service(cls) -> IQAService:
        """
        Get a QAService instance.
        
        Returns:
            IQAService: The QA service
        """
        if "qa" not in cls._instances:
            client = ClientFactory.get_deepseek_client()
            
            # Get configuration
            config = get_config_manager().get_config()
            qa_config = config.get("qa_service", {})
            
            # Determine if persistent storage should be used
            use_persistent_storage = qa_config.get("use_persistent_storage", False)
            storage_path = qa_config.get("storage_path", "./data/conversations")
            
            # Create QA service using factory
            service = await QAServiceFactory.create_qa_service(
                ai_client=client,
                use_persistent_storage=use_persistent_storage,
                storage_path=storage_path
            )
            
            cls._instances["qa"] = service
            
        return cls._instances["qa"]
    
    @classmethod
    async def initialize_services(cls):
        """Initialize all services."""
        # Create instances if they don't exist
        document_service = cls.get_document_service()
        recommendation_service = cls.get_recommendation_service()
        qa_service = await cls.get_qa_service()
        
        # Initialize each service
        await document_service.initialize()
        await recommendation_service.initialize()
        # QA service is already initialized by the factory
    
    @classmethod
    async def shutdown_services(cls):
        """Shutdown all services."""
        for service_name, service in cls._instances.items():
            if hasattr(service, "shutdown"):
                await service.shutdown()

# Dependency functions for FastAPI
def get_document_service(api_key: str = Depends(verify_api_key)) -> IDocumentService:
    """Dependency function for DocumentService."""
    return ServiceFactory.get_document_service()

def get_recommendation_service(api_key: str = Depends(verify_api_key)) -> IRecommendationService:
    """Dependency function for RecommendationService."""
    return ServiceFactory.get_recommendation_service()

async def get_qa_service(api_key: str = Depends(verify_api_key)) -> IQAService:
    """Dependency function for QAService."""
    return await ServiceFactory.get_qa_service() 