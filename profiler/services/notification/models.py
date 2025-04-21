"""
Data models for the notification service.

This module defines the data models for the notification service, including notification
status and content models.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel


class NotificationStatus(str, Enum):
    """Enum representing the status of a notification."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class NotificationType(str, Enum):
    """Enum representing the type of notification."""
    RECOMMENDATION = "recommendation"
    SKILL_UPDATE = "skill_update"
    PROFILE_COMPLETION = "profile_completion"
    SYSTEM = "system"
    CUSTOM = "custom"


class Notification(BaseModel):
    """
    Model representing a notification.
    """
    id: Optional[str] = None
    user_id: str
    type: NotificationType
    title: str
    message: str
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    related_entity_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        """Configuration for the model."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class NotificationBatch(BaseModel):
    """
    Model representing a batch of notifications to be sent.
    """
    notifications: List[Notification] 