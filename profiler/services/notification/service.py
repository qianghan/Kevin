"""
Notification service implementation.

This module provides a concrete implementation of the INotificationService interface.
"""

import uuid
import logging
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional

from profiler.db.session import AsyncSession
from profiler.db.models.notification import NotificationDB
from profiler.services.notification.interface import INotificationService
from profiler.services.notification.models import (
    Notification,
    NotificationBatch,
    NotificationStatus,
    NotificationType,
)

logger = logging.getLogger(__name__)


class NotificationService(INotificationService):
    """
    Implementation of the notification service.
    """
    
    def __init__(self, db_session: AsyncSession = None):
        """
        Initialize notification service with database session.
        
        Args:
            db_session: Database session for persistence
        """
        self.db = db_session
        # If no database is provided, store notifications in memory for testing
        self.in_memory_notifications = {} if db_session is None else None
    
    async def send_notification(self, notification: Notification) -> Notification:
        """
        Send a notification to a user.
        
        Args:
            notification: The notification to send
            
        Returns:
            The sent notification with updated status and metadata
        """
        # Generate ID if not provided
        if not notification.id:
            notification.id = str(uuid.uuid4())
        
        # Set creation time if not provided
        if not notification.created_at:
            notification.created_at = datetime.now(UTC)
        
        # Set initial status if not provided
        if not notification.status:
            notification.status = NotificationStatus.PENDING
        
        # For testing without a database, use in-memory storage
        if self.db is None:
            # Mark as sent immediately for testing
            notification.status = NotificationStatus.SENT
            self.in_memory_notifications[notification.id] = notification
            return notification
            
        # Create DB model
        db_notification = NotificationDB(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type.value,
            title=notification.title,
            message=notification.message,
            status=notification.status.value,
            created_at=notification.created_at,
            delivered_at=notification.delivered_at,
            read_at=notification.read_at,
            data=notification.metadata,
            related_entity_id=notification.related_entity_id,
            related_entity_type=notification.related_entity_type,
        )
        
        try:
            # TODO: Integrate with actual notification delivery service (email, push, etc.)
            # For now, just mark as sent immediately
            db_notification.status = NotificationStatus.SENT.value
            
            # Save to database
            self.db.add(db_notification)
            await self.db.commit()
            await self.db.refresh(db_notification)
            
            # Convert back to model and return
            return Notification(
                id=db_notification.id,
                user_id=db_notification.user_id,
                type=db_notification.type,
                title=db_notification.title,
                message=db_notification.message,
                status=db_notification.status,
                created_at=db_notification.created_at,
                delivered_at=db_notification.delivered_at,
                read_at=db_notification.read_at,
                metadata=db_notification.data,
                related_entity_id=db_notification.related_entity_id,
                related_entity_type=db_notification.related_entity_type,
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to send notification: {str(e)}")
            notification.status = NotificationStatus.FAILED
            return notification
    
    async def send_batch_notifications(self, batch: NotificationBatch) -> List[Notification]:
        """
        Send multiple notifications at once.
        
        Args:
            batch: Batch of notifications to send
            
        Returns:
            List of sent notifications with updated statuses
        """
        results = []
        for notification in batch.notifications:
            result = await self.send_notification(notification)
            results.append(result)
        return results
    
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
        # For testing without a database, use in-memory storage
        if self.db is None:
            user_notifications = [
                n for n in self.in_memory_notifications.values() 
                if n.user_id == user_id and (include_read or n.status != NotificationStatus.READ)
            ]
            # Sort by created_at (newest first) and apply pagination
            sorted_notifications = sorted(
                user_notifications, 
                key=lambda n: n.created_at or datetime.min, 
                reverse=True
            )
            return sorted_notifications[offset:offset+limit]
            
        query = self.db.query(NotificationDB).filter(NotificationDB.user_id == user_id)
        
        if not include_read:
            query = query.filter(NotificationDB.status != NotificationStatus.READ.value)
        
        db_notifications = await query.order_by(NotificationDB.created_at.desc()).offset(offset).limit(limit).all()
        
        return [
            Notification(
                id=db_notification.id,
                user_id=db_notification.user_id,
                type=db_notification.type,
                title=db_notification.title,
                message=db_notification.message,
                status=db_notification.status,
                created_at=db_notification.created_at,
                delivered_at=db_notification.delivered_at,
                read_at=db_notification.read_at,
                metadata=db_notification.data,
                related_entity_id=db_notification.related_entity_id,
                related_entity_type=db_notification.related_entity_type,
            )
            for db_notification in db_notifications
        ]
    
    async def mark_notification_as_read(self, notification_id: str) -> Notification:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification
            
        Returns:
            Updated notification with READ status
        """
        # For testing without a database, use in-memory storage
        if self.db is None:
            if notification_id not in self.in_memory_notifications:
                raise ValueError(f"Notification with ID {notification_id} not found")
                
            notification = self.in_memory_notifications[notification_id]
            notification.status = NotificationStatus.READ
            notification.read_at = datetime.now(UTC)
            return notification
            
        db_notification = await self.db.query(NotificationDB).filter(NotificationDB.id == notification_id).first()
        if not db_notification:
            raise ValueError(f"Notification with ID {notification_id} not found")
        
        db_notification.status = NotificationStatus.READ.value
        db_notification.read_at = datetime.now(UTC)
        
        await self.db.commit()
        await self.db.refresh(db_notification)
        
        return Notification(
            id=db_notification.id,
            user_id=db_notification.user_id,
            type=db_notification.type,
            title=db_notification.title,
            message=db_notification.message,
            status=db_notification.status,
            created_at=db_notification.created_at,
            delivered_at=db_notification.delivered_at,
            read_at=db_notification.read_at,
            metadata=db_notification.data,
            related_entity_id=db_notification.related_entity_id,
            related_entity_type=db_notification.related_entity_type,
        )
    
    async def delete_notification(self, notification_id: str) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: ID of the notification
            
        Returns:
            True if deleted successfully, False otherwise
        """
        # For testing without a database, use in-memory storage
        if self.db is None:
            if notification_id not in self.in_memory_notifications:
                return False
                
            del self.in_memory_notifications[notification_id]
            return True
            
        try:
            result = await self.db.query(NotificationDB).filter(NotificationDB.id == notification_id).delete()
            await self.db.commit()
            return result > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete notification: {str(e)}")
            return False
    
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
        notification = Notification(
            user_id=user_id,
            type=NotificationType.RECOMMENDATION,
            title=f"New Recommendation: {title}",
            message=description,
            status=NotificationStatus.PENDING,
            related_entity_id=recommendation_id,
            related_entity_type="recommendation",
            metadata={"recommendation_id": recommendation_id}
        )
        
        return await self.send_notification(notification) 