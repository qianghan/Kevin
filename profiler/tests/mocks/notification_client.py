"""
Mock implementation of the notification client for testing.

This module provides a mock implementation of the notification client
that can be used in tests without making real HTTP requests.
"""

from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

from profiler.services.notification.models import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationStatus
)

class MockNotificationClient:
    """Mock implementation of the notification client for testing."""
    
    def __init__(self):
        """Initialize the mock notification client."""
        self.notifications = {}
        self.user_notifications = {}
    
    async def send_notification(self, notification: Notification) -> Dict[str, Any]:
        """
        Mock sending a notification to a user.
        
        Args:
            notification: The notification to send
            
        Returns:
            The notification data with a generated ID
        """
        # Generate an ID if not provided
        if not notification.id:
            notification.id = str(uuid.uuid4())
        
        # Set status to SENT
        notification.status = NotificationStatus.SENT
        
        # Store the notification
        self.notifications[notification.id] = notification
        
        # Associate the notification with the user
        if notification.user_id not in self.user_notifications:
            self.user_notifications[notification.user_id] = []
        self.user_notifications[notification.user_id].append(notification.id)
        
        return notification.dict()
    
    async def send_batch_notifications(self, notifications: List[Notification]) -> List[Dict[str, Any]]:
        """
        Mock sending multiple notifications in a batch.
        
        Args:
            notifications: List of notifications to send
            
        Returns:
            List of notification data with generated IDs
        """
        results = []
        for notification in notifications:
            result = await self.send_notification(notification)
            results.append(result)
        return results
    
    async def get_user_notifications(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Mock getting notifications for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            
        Returns:
            Dictionary containing notifications and pagination info
        """
        if user_id not in self.user_notifications:
            return {
                "notifications": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
        
        notification_ids = self.user_notifications[user_id]
        total = len(notification_ids)
        
        # Apply pagination
        paginated_ids = notification_ids[offset:offset + limit]
        
        # Get the notification objects
        notifications = [
            self.notifications[notification_id].dict()
            for notification_id in paginated_ids
            if notification_id in self.notifications
        ]
        
        return {
            "notifications": notifications,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def mark_notification_as_read(self, notification_id: str) -> Dict[str, Any]:
        """
        Mock marking a notification as read.
        
        Args:
            notification_id: ID of the notification to mark as read
            
        Returns:
            The updated notification data
        """
        if notification_id not in self.notifications:
            raise ValueError(f"Notification with ID {notification_id} not found")
        
        notification = self.notifications[notification_id]
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.now()
        
        return notification.dict()
    
    def clear(self):
        """Clear all stored notifications and user associations."""
        self.notifications = {}
        self.user_notifications = {} 