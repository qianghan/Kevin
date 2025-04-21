"""
Mock implementation of the notification service.

This module provides a mock implementation of the notification service for testing and development.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from profiler.services.notification.interface import INotificationService
from profiler.services.notification.models import (
    Notification, 
    NotificationBatch,
    NotificationStatus
)


class MockNotificationService(INotificationService):
    """
    Mock implementation of the notification service.
    
    Stores notifications in memory for testing purposes.
    """
    
    def __init__(self):
        """Initialize the mock notification service."""
        self._notifications: Dict[str, Notification] = {}
    
    async def send_notification(self, notification: Notification) -> Notification:
        """
        Send a notification to a user.
        
        Args:
            notification: The notification to send
            
        Returns:
            The sent notification with updated status and ID
        """
        notification_id = str(uuid.uuid4())
        sent_notification = notification.copy(
            update={
                "id": notification_id,
                "status": NotificationStatus.SENT,
                "created_at": datetime.utcnow(),
            }
        )
        self._notifications[notification_id] = sent_notification
        return sent_notification
    
    async def send_batch_notifications(self, batch: NotificationBatch) -> List[Notification]:
        """
        Send multiple notifications in a batch.
        
        Args:
            batch: A batch of notifications to send
            
        Returns:
            List of sent notifications with updated statuses and IDs
        """
        sent_notifications = []
        for notification in batch.notifications:
            sent_notification = await self.send_notification(notification)
            sent_notifications.append(sent_notification)
        return sent_notifications
    
    async def get_user_notifications(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        include_read: bool = False
    ) -> List[Notification]:
        """
        Get notifications for a specific user.
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            include_read: Whether to include notifications marked as read
            
        Returns:
            List of notifications for the user
        """
        user_notifications = [
            notification for notification in self._notifications.values()
            if notification.user_id == user_id 
            and (include_read or notification.status != NotificationStatus.READ)
        ]
        
        # Sort by created_at (newest first)
        user_notifications.sort(key=lambda n: n.created_at, reverse=True)
        
        # Apply pagination
        paginated_notifications = user_notifications[offset:offset + limit]
        
        return paginated_notifications
    
    async def mark_notification_as_read(self, notification_id: str) -> Notification:
        """
        Mark a notification as read.
        
        Args:
            notification_id: The ID of the notification to mark as read
            
        Returns:
            The updated notification
        """
        if notification_id not in self._notifications:
            raise ValueError(f"Notification with ID {notification_id} not found")
        
        notification = self._notifications[notification_id]
        updated_notification = notification.copy(
            update={"status": NotificationStatus.READ}
        )
        self._notifications[notification_id] = updated_notification
        
        return updated_notification
    
    async def delete_notification(self, notification_id: str) -> None:
        """
        Delete a notification.
        
        Args:
            notification_id: The ID of the notification to delete
        """
        if notification_id in self._notifications:
            del self._notifications[notification_id] 