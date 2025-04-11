"""
API dependencies and service factories.

This module provides dependency injection for FastAPI endpoints,
including service factories and security mechanisms.
"""

from typing import Dict, Optional, Callable, Any
from fastapi import Depends, Header, HTTPException, status, Request
from functools import lru_cache

from ..utils.config_manager import ConfigManager
from ..utils.errors import AuthenticationError
from ..core.deepseek.r1 import DeepSeekR1
from ..services.interfaces import IDocumentService, IRecommendationService, IQAService, IProfileService
from ..services.recommendation import RecommendationService
from ..services.document_service.document_service import DocumentService
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

async def verify_api_key(request: Request, x_api_key: str = Header(None)):
    """
    Verify that the API key is valid.
    
    Args:
        request: The FastAPI request
        x_api_key: API key from the request header
        
    Raises:
        HTTPException: If the API key is invalid
    """
    # Check if API key is provided
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing"
        )
    
    # Get valid keys from configuration
    security_config = get_security_config()
    valid_keys = security_config.get("api_keys", [])
    
    # Get API keys from app state
    app_state_keys = getattr(request.app.state, "api_keys", [])
    valid_keys.extend(app_state_keys)
    
    # Check if the provided key is valid
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
    def get_ai_client(cls) -> DeepSeekR1:
        """Get the AI client instance"""
        if "ai_client" not in cls._instances:
            config = ConfigManager()
            api_key = config.get_value(["ai_clients", "deepseek", "api_key"])
            base_url = config.get_value(["ai_clients", "deepseek", "url"])
            cls._instances["ai_client"] = DeepSeekR1(api_key=api_key, base_url=base_url)
        return cls._instances["ai_client"]
    
    @classmethod
    def get_document_service(cls) -> DocumentService:
        """Get the document service instance"""
        if "document" not in cls._instances:
            config = ConfigManager().get_all()
            cls._instances["document"] = DocumentService(config=config)
        return cls._instances["document"]
    
    @classmethod
    def get_recommendation_service(cls) -> IRecommendationService:
        """
        Get a RecommendationService instance.
        
        Returns:
            IRecommendationService: The recommendation service
        """
        if "recommendation" not in cls._instances:
            config = ConfigManager().get_all()
            cls._instances["recommendation"] = RecommendationService(config=config)
        return cls._instances["recommendation"]
    
    @classmethod
    async def get_qa_service(cls) -> QAService:
        """Get the QA service instance"""
        if "qa" not in cls._instances:
            config = ConfigManager()
            qa_config = config.get_value(["qa"], {})
            cls._instances["qa"] = await QAServiceFactory.create_qa_service(qa_config)
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