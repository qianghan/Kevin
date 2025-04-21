"""
Interface definition for notification service.

This module defines the interface that any notification service implementation must adhere to.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from profiler.services.notification.models import Notification, NotificationBatch


class INotificationService(ABC):
    """
    Interface for notification service implementations.
    """
    
    @abstractmethod
    async def send_notification(self, notification: Notification) -> Notification:
        """
        Send a notification to a user.
        
        Args:
            notification: The notification to send
            
        Returns:
            The sent notification with updated status and metadata
        """
        pass
    
    @abstractmethod
    async def send_batch_notifications(self, batch: NotificationBatch) -> List[Notification]:
        """
        Send multiple notifications at once.
        
        Args:
            batch: Batch of notifications to send
            
        Returns:
            List of sent notifications with updated statuses
        """
        pass
    
    @abstractmethod
    async def get_user_notifications(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0,
        include_read: bool = False
    ) -> List[Notification]:
        """
        Get notifications for a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            include_read: Whether to include notifications marked as read
            
        Returns:
            List of notifications for the user
        """
        pass
    
    @abstractmethod
    async def mark_notification_as_read(self, notification_id: str) -> Notification:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification
            
        Returns:
            Updated notification with READ status
        """
        pass
    
    @abstractmethod
    async def delete_notification(self, notification_id: str) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: ID of the notification
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
        
    @abstractmethod
    async def create_recommendation_notification(
        self, user_id: str, recommendation_id: str, title: str, description: str
    ) -> Notification:
        """
        Create a notification for a new recommendation.
        
        Args:
            user_id: ID of the user to notify
            recommendation_id: ID of the recommendation
            title: Title of the recommendation
            description: Description of the recommendation
            
        Returns:
            Created notification
        """
        pass 