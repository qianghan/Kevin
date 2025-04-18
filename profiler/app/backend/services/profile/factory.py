"""
Factory implementation for the Profile Service.

This module provides a factory for creating profile service components,
following the Dependency Inversion Principle and Abstract Factory pattern.
"""

from typing import Dict, Any, Optional, Callable, Awaitable

from ...utils.config_manager import ConfigManager
from ...utils.logging import get_logger
from .interfaces import (
    ProfileFactoryInterface,
    ProfileRepositoryInterface,
    ProfileValidatorInterface,
    ProfileStateCalculatorInterface,
    ProfileNotifierInterface
)
from .repository import JSONFileProfileRepository, DatabaseProfileRepository
from .validator import BasicProfileValidator
from .state import DefaultProfileStateCalculator
from .notifier import WebSocketProfileNotifier, MultiChannelProfileNotifier

logger = get_logger(__name__)


class ProfileServiceFactory(ProfileFactoryInterface):
    """Factory for creating profile service components."""
    
    def __init__(self, config_manager: ConfigManager, 
                websocket_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None):
        """
        Initialize the factory.
        
        Args:
            config_manager: Configuration manager
            websocket_callback: Optional callback for WebSocket notifications
        """
        self.config_manager = config_manager
        self.websocket_callback = websocket_callback
        self._components: Dict[str, Any] = {}
        
        # Get profile service configuration
        self.config = self.config_manager.get_config().get("profile_service", {})
        logger.info("Initialized ProfileServiceFactory")
    
    def get_repository(self) -> ProfileRepositoryInterface:
        """
        Get a profile repository instance.
        
        Returns:
            Profile repository instance
        """
        if "repository" not in self._components:
            # Determine repository type from config
            repository_type = self.config.get("repository_type", "json_file")
            
            if repository_type == "json_file":
                # Use JSON file repository
                storage_dir = self.config.get("storage_dir", "./data/profiles")
                self._components["repository"] = JSONFileProfileRepository(storage_dir=storage_dir)
                logger.info(f"Created JSONFileProfileRepository with storage_dir={storage_dir}")
            elif repository_type == "database" or repository_type == "postgresql":
                # Use PostgreSQL database repository
                db_config = self.config_manager.get_config().get("database", {})
                self._components["repository"] = DatabaseProfileRepository(config=db_config)
                logger.info("Created PostgreSQL DatabaseProfileRepository")
            else:
                # Default to JSON file repository
                storage_dir = "./data/profiles"
                self._components["repository"] = JSONFileProfileRepository(storage_dir=storage_dir)
                logger.warning(f"Unknown repository type: {repository_type}, defaulting to JSONFileProfileRepository")
        
        return self._components["repository"]
    
    def get_validator(self) -> ProfileValidatorInterface:
        """
        Get a profile validator instance.
        
        Returns:
            Profile validator instance
        """
        if "validator" not in self._components:
            # For now, only one validator implementation
            self._components["validator"] = BasicProfileValidator()
            logger.info("Created BasicProfileValidator")
        
        return self._components["validator"]
    
    def get_state_calculator(self) -> ProfileStateCalculatorInterface:
        """
        Get a profile state calculator instance.
        
        Returns:
            Profile state calculator instance
        """
        if "state_calculator" not in self._components:
            # For now, only one state calculator implementation
            self._components["state_calculator"] = DefaultProfileStateCalculator()
            logger.info("Created DefaultProfileStateCalculator")
        
        return self._components["state_calculator"]
    
    def get_notifier(self) -> ProfileNotifierInterface:
        """
        Get a profile notifier instance.
        
        Returns:
            Profile notifier instance
        """
        if "notifier" not in self._components:
            # Determine if multi-channel notifications are enabled
            use_multi_channel = self.config.get("use_multi_channel_notifications", False)
            
            if use_multi_channel:
                # Create multi-channel notifier
                notifier = MultiChannelProfileNotifier()
                
                # Add WebSocket notifier if callback is provided
                if self.websocket_callback:
                    ws_notifier = WebSocketProfileNotifier(
                        websocket_send_callback=self.websocket_callback
                    )
                    notifier.add_notifier(ws_notifier)
                
                # Add other notifiers as needed...
                
                self._components["notifier"] = notifier
                logger.info("Created MultiChannelProfileNotifier")
            elif self.websocket_callback:
                # Use WebSocket notifier directly
                self._components["notifier"] = WebSocketProfileNotifier(
                    websocket_send_callback=self.websocket_callback
                )
                logger.info("Created WebSocketProfileNotifier")
            else:
                # Create a dummy notifier if no callback is provided
                self._components["notifier"] = MultiChannelProfileNotifier()
                logger.warning("No WebSocket callback provided, using empty MultiChannelProfileNotifier")
        
        return self._components["notifier"]
    
    async def initialize_components(self) -> None:
        """Initialize all components."""
        # Create all components to ensure they exist
        repository = self.get_repository()
        self.get_validator()
        self.get_state_calculator()
        self.get_notifier()
        
        # Initialize repository
        await repository.initialize()
        logger.info("Initialized all profile service components")
    
    async def shutdown_components(self) -> None:
        """Shutdown all components."""
        # Shutdown repository if it exists
        if "repository" in self._components:
            await self._components["repository"].shutdown()
            logger.info("Shutdown profile service components") 