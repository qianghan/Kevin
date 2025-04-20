"""
Document notification system.

This module provides functionality for sending notifications about document
updates and shares to users.
"""

import asyncio
import logging
from typing import Dict, Set, Any, Optional, Callable, Awaitable, List, Union, Protocol
from enum import Enum
from datetime import datetime

from ...utils.logging import get_logger
from ...utils.errors import ValidationError

logger = get_logger(__name__)


class NotificationType(Enum):
    """Types of document notifications."""
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_SHARED = "document_shared"
    DOCUMENT_UNSHARED = "document_unshared"
    DOCUMENT_ACCESS_GRANTED = "document_access_granted"
    DOCUMENT_ACCESS_REVOKED = "document_access_revoked"
    DOCUMENT_VERSION_ADDED = "document_version_added"
    DOCUMENT_COMMENT_ADDED = "document_comment_added"


class DocumentNotification:
    """Represents a notification about a document event."""
    
    def __init__(self,
                 notification_type: NotificationType,
                 document_id: str,
                 user_id: str,
                 timestamp: Optional[datetime] = None,
                 document_name: Optional[str] = None,
                 initiator_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a document notification.
        
        Args:
            notification_type: Type of notification
            document_id: ID of the document
            user_id: ID of the user to notify
            timestamp: When the notification was created
            document_name: Name of the document
            initiator_id: ID of the user who initiated the action
            details: Additional details about the notification
        """
        self.notification_type = notification_type
        self.document_id = document_id
        self.user_id = user_id
        self.timestamp = timestamp or datetime.utcnow()
        self.document_name = document_name
        self.initiator_id = initiator_id
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary for storage or serialization."""
        return {
            "notification_type": self.notification_type.value,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "document_name": self.document_name,
            "initiator_id": self.initiator_id,
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentNotification':
        """Create a notification from a dictionary."""
        notification_type = NotificationType(data.get("notification_type"))
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else None
        
        return cls(
            notification_type=notification_type,
            document_id=data.get("document_id"),
            user_id=data.get("user_id"),
            timestamp=timestamp,
            document_name=data.get("document_name"),
            initiator_id=data.get("initiator_id"),
            details=data.get("details", {})
        )


class NotificationChannel(Protocol):
    """Interface for notification delivery channels."""
    
    async def send_notification(self, notification: DocumentNotification) -> bool:
        """
        Send a notification through this channel.
        
        Args:
            notification: The notification to send
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        ...


class WebSocketNotificationChannel:
    """Notification channel that sends notifications via WebSockets."""
    
    def __init__(self, 
                websocket_send_callback: Callable[[str, Dict[str, Any]], Awaitable[None]]):
        """
        Initialize the WebSocket notification channel.
        
        Args:
            websocket_send_callback: Callback function to send messages via WebSocket
        """
        self.websocket_send_callback = websocket_send_callback
        logger.info("Initialized WebSocketNotificationChannel")
    
    async def send_notification(self, notification: DocumentNotification) -> bool:
        """
        Send a notification via WebSocket.
        
        Args:
            notification: The notification to send
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            # Convert notification to dictionary
            notification_data = notification.to_dict()
            
            # Send notification to the user
            await self.websocket_send_callback(notification.user_id, notification_data)
            
            logger.info(f"Sent document notification to user {notification.user_id} via WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to send document notification via WebSocket: {str(e)}")
            return False


class EmailNotificationChannel:
    """Notification channel that sends notifications via email."""
    
    def __init__(self, email_service=None):
        """
        Initialize the email notification channel.
        
        Args:
            email_service: Service for sending emails
        """
        self.email_service = email_service
        logger.info("Initialized EmailNotificationChannel")
    
    async def send_notification(self, notification: DocumentNotification) -> bool:
        """
        Send a notification via email.
        
        Args:
            notification: The notification to send
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        # Skip if email service is not provided
        if not self.email_service:
            logger.warning("Email service not provided, skipping email notification")
            return False
        
        try:
            # Generate email subject based on notification type
            subject_map = {
                NotificationType.DOCUMENT_CREATED: "New document created",
                NotificationType.DOCUMENT_UPDATED: "Document updated",
                NotificationType.DOCUMENT_DELETED: "Document deleted",
                NotificationType.DOCUMENT_SHARED: "Document shared with you",
                NotificationType.DOCUMENT_UNSHARED: "Document access removed",
                NotificationType.DOCUMENT_ACCESS_GRANTED: "Document access granted",
                NotificationType.DOCUMENT_ACCESS_REVOKED: "Document access revoked",
                NotificationType.DOCUMENT_VERSION_ADDED: "New document version available",
                NotificationType.DOCUMENT_COMMENT_ADDED: "New comment on document"
            }
            
            subject = subject_map.get(notification.notification_type, "Document notification")
            
            if notification.document_name:
                subject = f"{subject}: {notification.document_name}"
            
            # Generate email body
            body = self._generate_email_body(notification)
            
            # Send email
            await self.email_service.send_email(
                to=notification.user_id,  # Assuming user_id is an email address
                subject=subject,
                body=body
            )
            
            logger.info(f"Sent document notification to user {notification.user_id} via email")
            return True
        except Exception as e:
            logger.error(f"Failed to send document notification via email: {str(e)}")
            return False
    
    def _generate_email_body(self, notification: DocumentNotification) -> str:
        """Generate the email body for a notification."""
        body_parts = []
        
        # Add greeting
        body_parts.append("Hello,\n")
        
        # Add main message based on notification type
        if notification.notification_type == NotificationType.DOCUMENT_SHARED:
            body_parts.append(f"A document has been shared with you.")
        elif notification.notification_type == NotificationType.DOCUMENT_UPDATED:
            body_parts.append(f"A document you have access to has been updated.")
        elif notification.notification_type == NotificationType.DOCUMENT_VERSION_ADDED:
            body_parts.append(f"A new version has been added to a document you have access to.")
        elif notification.notification_type == NotificationType.DOCUMENT_COMMENT_ADDED:
            body_parts.append(f"A new comment has been added to a document you have access to.")
        else:
            body_parts.append(f"There has been an update to a document you have access to.")
        
        # Add document details
        if notification.document_name:
            body_parts.append(f"\nDocument: {notification.document_name}")
        
        # Add action details if available
        if notification.initiator_id:
            body_parts.append(f"Action by: {notification.initiator_id}")
        
        body_parts.append(f"Date: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add any additional details
        if notification.details:
            body_parts.append("\nAdditional Information:")
            for key, value in notification.details.items():
                if isinstance(value, str) and len(value) < 100:  # Only include reasonably sized string values
                    body_parts.append(f"- {key}: {value}")
        
        # Add action instructions based on notification type
        body_parts.append("\nYou can view this document by logging into the system.")
        
        # Add footer
        body_parts.append("\nThank you,")
        body_parts.append("Document Management System")
        
        return "\n".join(body_parts)


class DocumentNotificationManager:
    """
    Manages notifications for document events.
    
    This service sends notifications to users about document updates,
    shares, and other events through multiple channels.
    """
    
    def __init__(self, 
                 document_repository=None,
                 user_repository=None):
        """
        Initialize the document notification manager.
        
        Args:
            document_repository: Repository for document information
            user_repository: Repository for user information
        """
        self.document_repository = document_repository
        self.user_repository = user_repository
        self.notification_channels: List[NotificationChannel] = []
        self._notification_history: Dict[str, List[DocumentNotification]] = {}  # user_id -> notifications
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the notification manager."""
        if self._initialized:
            return
        
        # Initialize repositories if provided
        if self.document_repository:
            await self.document_repository.initialize()
        
        if self.user_repository:
            await self.user_repository.initialize()
        
        self._initialized = True
        logger.info("Document notification manager initialized")
    
    def add_notification_channel(self, channel: NotificationChannel) -> None:
        """
        Add a notification channel.
        
        Args:
            channel: The notification channel to add
        """
        self.notification_channels.append(channel)
        logger.info(f"Added notification channel: {type(channel).__name__}")
    
    async def notify_document_update(self,
                                   document_id: str,
                                   user_ids: List[str],
                                   update_type: NotificationType,
                                   initiator_id: Optional[str] = None,
                                   details: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Send notifications about a document update.
        
        Args:
            document_id: ID of the document
            user_ids: IDs of users to notify
            update_type: Type of update
            initiator_id: ID of the user who initiated the update
            details: Additional details about the update
            
        Returns:
            List of user IDs who were successfully notified
        """
        if not self._initialized:
            await self.initialize()
        
        # Get document name if repository is available
        document_name = None
        if self.document_repository:
            try:
                document = await self.document_repository.get_document(document_id)
                if document:
                    document_name = document.get("name") or document.get("title")
            except Exception as e:
                logger.error(f"Error getting document name: {str(e)}")
        
        # Create notifications
        notifications = []
        for user_id in user_ids:
            # Skip sending notification to the initiator
            if user_id == initiator_id:
                continue
                
            notification = DocumentNotification(
                notification_type=update_type,
                document_id=document_id,
                user_id=user_id,
                document_name=document_name,
                initiator_id=initiator_id,
                details=details
            )
            notifications.append(notification)
            
            # Add to history
            if user_id not in self._notification_history:
                self._notification_history[user_id] = []
            self._notification_history[user_id].append(notification)
        
        # Send notifications through all channels
        successful_users = set()
        
        for notification in notifications:
            # Try all channels until one succeeds
            success = False
            for channel in self.notification_channels:
                try:
                    channel_success = await channel.send_notification(notification)
                    if channel_success:
                        success = True
                        break
                except Exception as e:
                    logger.error(f"Error sending notification through channel {type(channel).__name__}: {str(e)}")
            
            if success:
                successful_users.add(notification.user_id)
        
        logger.info(f"Notified {len(successful_users)} users about document update {update_type.value}")
        return list(successful_users)
    
    async def notify_document_share(self,
                                  document_id: str,
                                  sharer_id: str,
                                  shared_user_ids: List[str],
                                  details: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Send notifications about a document being shared.
        
        Args:
            document_id: ID of the document
            sharer_id: ID of the user sharing the document
            shared_user_ids: IDs of users the document is shared with
            details: Additional details about the share
            
        Returns:
            List of user IDs who were successfully notified
        """
        return await self.notify_document_update(
            document_id=document_id,
            user_ids=shared_user_ids,
            update_type=NotificationType.DOCUMENT_SHARED,
            initiator_id=sharer_id,
            details=details
        )
    
    async def notify_document_unshare(self,
                                   document_id: str,
                                   unsharer_id: str,
                                   unshared_user_ids: List[str],
                                   details: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Send notifications about a document being unshared.
        
        Args:
            document_id: ID of the document
            unsharer_id: ID of the user unsharing the document
            unshared_user_ids: IDs of users the document is unshared from
            details: Additional details about the unshare
            
        Returns:
            List of user IDs who were successfully notified
        """
        return await self.notify_document_update(
            document_id=document_id,
            user_ids=unshared_user_ids,
            update_type=NotificationType.DOCUMENT_UNSHARED,
            initiator_id=unsharer_id,
            details=details
        )
    
    async def notify_document_modification(self,
                                        document_id: str,
                                        modifier_id: str,
                                        details: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Send notifications about a document being modified.
        
        Args:
            document_id: ID of the document
            modifier_id: ID of the user modifying the document
            details: Additional details about the modification
            
        Returns:
            List of user IDs who were successfully notified
        """
        # Get all users with access to the document
        user_ids = []
        
        if self.document_repository:
            try:
                # This assumes document_repository has a method to get users with access
                users_with_access = await self.document_repository.get_document_users(document_id)
                user_ids = [user["user_id"] for user in users_with_access]
            except Exception as e:
                logger.error(f"Error getting users with document access: {str(e)}")
        
        return await self.notify_document_update(
            document_id=document_id,
            user_ids=user_ids,
            update_type=NotificationType.DOCUMENT_UPDATED,
            initiator_id=modifier_id,
            details=details
        )
    
    async def notify_document_version_added(self,
                                         document_id: str,
                                         version_creator_id: str,
                                         version_number: Union[int, str],
                                         details: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Send notifications about a new document version.
        
        Args:
            document_id: ID of the document
            version_creator_id: ID of the user creating the version
            version_number: Version number
            details: Additional details about the version
            
        Returns:
            List of user IDs who were successfully notified
        """
        # Get all users with access to the document
        user_ids = []
        
        if self.document_repository:
            try:
                # This assumes document_repository has a method to get users with access
                users_with_access = await self.document_repository.get_document_users(document_id)
                user_ids = [user["user_id"] for user in users_with_access]
            except Exception as e:
                logger.error(f"Error getting users with document access: {str(e)}")
        
        # Add version info to details
        version_details = details or {}
        version_details["version_number"] = version_number
        
        return await self.notify_document_update(
            document_id=document_id,
            user_ids=user_ids,
            update_type=NotificationType.DOCUMENT_VERSION_ADDED,
            initiator_id=version_creator_id,
            details=version_details
        )
    
    async def get_user_notifications(self,
                                  user_id: str,
                                  limit: int = 50,
                                  offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get recent notifications for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            
        Returns:
            List of notification dictionaries
        """
        if not self._initialized:
            await self.initialize()
        
        # Get notifications from history
        notifications = self._notification_history.get(user_id, [])
        
        # Sort by timestamp (newest first)
        notifications.sort(key=lambda n: n.timestamp, reverse=True)
        
        # Apply pagination
        paginated = notifications[offset:offset+limit]
        
        # Convert to dictionaries
        return [notification.to_dict() for notification in paginated]
    
    async def mark_notifications_as_read(self,
                                      user_id: str,
                                      notification_ids: Optional[List[str]] = None) -> int:
        """
        Mark notifications as read.
        
        Args:
            user_id: ID of the user
            notification_ids: IDs of notifications to mark as read (all if None)
            
        Returns:
            Number of notifications marked as read
        """
        if not self._initialized:
            await self.initialize()
        
        # In a real implementation, this would update a database
        # For now, we'll just track it in the notification details
        
        notifications = self._notification_history.get(user_id, [])
        marked_count = 0
        
        for notification in notifications:
            if notification_ids is None or notification.document_id in notification_ids:
                notification.details["read"] = True
                notification.details["read_at"] = datetime.utcnow().isoformat()
                marked_count += 1
        
        return marked_count 