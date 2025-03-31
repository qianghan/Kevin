"""
Notifier implementation for the Profile Service.

This module provides concrete implementations of the ProfileNotifierInterface.
"""

from typing import Dict, Set, Any, Optional, Callable, Awaitable
import asyncio

from ...utils.logging import get_logger
from .interfaces import ProfileNotifierInterface
from .models import ProfileState

logger = get_logger(__name__)


class WebSocketProfileNotifier(ProfileNotifierInterface):
    """
    Profile notifier implementation using WebSockets.
    
    This notifier uses a callback function to send notifications through WebSockets.
    """
    
    def __init__(self, 
                websocket_send_callback: Callable[[str, Dict[str, Any]], Awaitable[None]]):
        """
        Initialize the notifier.
        
        Args:
            websocket_send_callback: Callback function to send messages via WebSocket
        """
        self.websocket_send_callback = websocket_send_callback
        logger.info("Initialized WebSocketProfileNotifier")
    
    async def notify_profile_updated(self, profile_id: str, profile_state: ProfileState) -> None:
        """
        Notify subscribers that a profile has been updated.
        
        Args:
            profile_id: ID of the updated profile
            profile_state: Current state of the profile
        """
        try:
            # Prepare notification data
            notification = {
                "event": "profile_updated",
                "profile_id": profile_id,
                "profile_state": profile_state.dict()
            }
            
            # Send notification
            await self.websocket_send_callback(profile_id, notification)
            
            logger.info(f"Sent profile update notification for profile {profile_id}")
        except Exception as e:
            logger.error(f"Failed to send profile update notification: {str(e)}")
    
    async def notify_profile_deleted(self, profile_id: str) -> None:
        """
        Notify subscribers that a profile has been deleted.
        
        Args:
            profile_id: ID of the deleted profile
        """
        try:
            # Prepare notification data
            notification = {
                "event": "profile_deleted",
                "profile_id": profile_id
            }
            
            # Send notification
            await self.websocket_send_callback(profile_id, notification)
            
            logger.info(f"Sent profile deletion notification for profile {profile_id}")
        except Exception as e:
            logger.error(f"Failed to send profile deletion notification: {str(e)}")


class MultiChannelProfileNotifier(ProfileNotifierInterface):
    """
    Profile notifier that sends notifications through multiple channels.
    
    This notifier supports multiple notification channels (WebSocket, email, etc.).
    """
    
    def __init__(self):
        """Initialize the notifier with empty channel list."""
        self.notifiers: Set[ProfileNotifierInterface] = set()
        logger.info("Initialized MultiChannelProfileNotifier")
    
    def add_notifier(self, notifier: ProfileNotifierInterface) -> None:
        """
        Add a notifier to the notification channels.
        
        Args:
            notifier: Notifier implementation to add
        """
        self.notifiers.add(notifier)
        logger.info(f"Added notifier: {type(notifier).__name__}")
    
    def remove_notifier(self, notifier: ProfileNotifierInterface) -> None:
        """
        Remove a notifier from the notification channels.
        
        Args:
            notifier: Notifier implementation to remove
        """
        if notifier in self.notifiers:
            self.notifiers.remove(notifier)
            logger.info(f"Removed notifier: {type(notifier).__name__}")
    
    async def notify_profile_updated(self, profile_id: str, profile_state: ProfileState) -> None:
        """
        Notify subscribers through all channels that a profile has been updated.
        
        Args:
            profile_id: ID of the updated profile
            profile_state: Current state of the profile
        """
        tasks = []
        for notifier in self.notifiers:
            tasks.append(notifier.notify_profile_updated(profile_id, profile_state))
        
        if tasks:
            # Wait for all notifications to be sent
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Profile update notifications sent through {len(tasks)} channels")
    
    async def notify_profile_deleted(self, profile_id: str) -> None:
        """
        Notify subscribers through all channels that a profile has been deleted.
        
        Args:
            profile_id: ID of the deleted profile
        """
        tasks = []
        for notifier in self.notifiers:
            tasks.append(notifier.notify_profile_deleted(profile_id))
        
        if tasks:
            # Wait for all notifications to be sent
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Profile deletion notifications sent through {len(tasks)} channels") 