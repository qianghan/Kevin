from typing import Optional
import logging
from .providers.university_provider import UniversityProvider
from .providers.kevin_university_adapter import KevinUniversityAdapter

class UniversityProviderFactory:
    """Factory for creating university provider instances"""
    
    @staticmethod
    async def create_provider(config) -> Optional[UniversityProvider]:
        """Create and return a university provider if configured"""
        logger = logging.getLogger(__name__)
        
        # Check if Kevin integration is enabled
        if config.get("external_services.kevin.enabled", False):
            logger.info("Creating Kevin University Adapter")
            provider = KevinUniversityAdapter(config)
            await provider.initialize()
            return provider
            
        logger.info("No university provider configured")
        return None
