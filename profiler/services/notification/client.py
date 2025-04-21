"""
Client for interacting with the notification service.

This module provides a client interface for sending notifications.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from pydantic import ValidationError

from profiler.services.notification.models import (
    Notification, 
    NotificationType,
    NotificationPriority,
    NotificationStatus
)

logger = logging.getLogger(__name__)

class NotificationClient:
    """Client for sending notifications to users."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the notification client.
        
        Args:
            base_url: Base URL of the notification service
            api_key: API key for authentication with the notification service
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    async def send_notification(self, notification: Notification) -> Dict[str, Any]:
        """
        Send a notification to a user.
        
        Args:
            notification: The notification to send
            
        Returns:
            The response from the notification service
            
        Raises:
            httpx.HTTPStatusError: If the notification service returns an error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/notifications",
                    json=notification.dict(exclude_none=True),
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send notification: {e.response.text}")
            raise
        except ValidationError as e:
            logger.error(f"Invalid notification data: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            raise
    
    async def send_batch_notifications(self, notifications: List[Notification]) -> List[Dict[str, Any]]:
        """
        Send multiple notifications in a batch.
        
        Args:
            notifications: List of notifications to send
            
        Returns:
            List of responses from the notification service
            
        Raises:
            httpx.HTTPStatusError: If the notification service returns an error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/notifications/batch",
                    json=[n.dict(exclude_none=True) for n in notifications],
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send batch notifications: {e.response.text}")
            raise
        except ValidationError as e:
            logger.error(f"Invalid notification data in batch: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error sending batch notifications: {str(e)}")
            raise
    
    async def get_user_notifications(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get notifications for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            
        Returns:
            Dictionary containing notifications and pagination info
            
        Raises:
            httpx.HTTPStatusError: If the notification service returns an error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/users/{user_id}/notifications",
                    params={"limit": limit, "offset": offset},
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get user notifications: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting user notifications: {str(e)}")
            raise
            
    async def mark_notification_as_read(self, notification_id: str) -> Dict[str, Any]:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification to mark as read
            
        Returns:
            The updated notification data
            
        Raises:
            httpx.HTTPStatusError: If the notification service returns an error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/notifications/{notification_id}/read",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to mark notification as read: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            raise 