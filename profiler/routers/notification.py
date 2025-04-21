"""
Router for notification endpoints.

This module includes the FastAPI router for notification-related endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from profiler.services.notification.models import Notification
from profiler.services.notification.service import INotificationService
from profiler.dependencies import get_notification_service, get_current_user
from profiler.api.endpoints import notifications

# Create router
router = APIRouter(
    prefix="/api/notifications",
    tags=["notifications"],
    responses={404: {"description": "Not found"}},
)

# Include the endpoints defined in the endpoints module
router.include_router(notifications.router)


@router.get("", response_model=List[Notification])
async def get_notifications(
    unread_only: bool = False,
    current_user_id: str = Depends(get_current_user),
    notification_service: INotificationService = Depends(get_notification_service),
):
    """
    Get notifications for the current user.

    Args:
        unread_only: Whether to get only unread notifications.
        current_user_id: The ID of the current user.
        notification_service: The notification service.

    Returns:
        A list of notifications for the user.
    """
    return await notification_service.get_notifications_for_user(current_user_id, unread_only)


@router.patch("/{notification_id}/read", response_model=Notification)
async def mark_as_read(
    notification_id: str,
    current_user_id: str = Depends(get_current_user),
    notification_service: INotificationService = Depends(get_notification_service),
):
    """
    Mark a notification as read.

    Args:
        notification_id: The ID of the notification to mark as read.
        current_user_id: The ID of the current user.
        notification_service: The notification service.

    Returns:
        The updated notification.
    """
    # Get the notification to verify ownership
    notifications = await notification_service.get_notifications_for_user(current_user_id)
    notification_ids = [notification.id for notification in notifications]
    
    if notification_id not in notification_ids:
        raise HTTPException(status_code=404, detail="Notification not found or access denied")
    
    updated_notification = await notification_service.mark_notification_as_read(notification_id)
    if not updated_notification:
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")
    
    return updated_notification 