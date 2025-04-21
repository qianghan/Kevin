"""
API endpoints for notifications.

This module provides REST API endpoints for creating, retrieving, and managing notifications.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from profiler.api.deps import get_notification_service, get_current_user_id
from profiler.services.notification.interface import INotificationService
from profiler.services.notification.models import (
    Notification,
    NotificationStatus,
    NotificationType,
)

router = APIRouter()


@router.post("/", response_model=Notification, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: Notification,
    service: INotificationService = Depends(get_notification_service),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Create a new notification.
    
    Only admin users should be able to create arbitrary notifications.
    Regular users can only create notifications for themselves.
    """
    # Ensure user can only create notifications for themselves unless they're admin
    # Admin check would be implemented in get_current_user_id dependency
    if notification.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create notifications for yourself",
        )
    
    return await service.send_notification(notification)


@router.get("/me", response_model=List[Notification])
async def get_my_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_read: bool = Query(False),
    service: INotificationService = Depends(get_notification_service),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Get notifications for the current user.
    """
    return await service.get_user_notifications(
        user_id=current_user_id,
        limit=limit,
        offset=offset,
        include_read=include_read,
    )


@router.get("/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: str = Path(...),
    service: INotificationService = Depends(get_notification_service),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Get a specific notification by ID.
    """
    notifications = await service.get_user_notifications(
        user_id=current_user_id,
        limit=1,
        offset=0,
        include_read=True,
    )
    
    for notification in notifications:
        if notification.id == notification_id:
            return notification
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Notification with ID {notification_id} not found",
    )


@router.put("/{notification_id}/read", response_model=Notification)
async def mark_notification_as_read(
    notification_id: str = Path(...),
    service: INotificationService = Depends(get_notification_service),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Mark a notification as read.
    """
    try:
        # First check if notification belongs to current user
        notification = await get_notification(
            notification_id=notification_id,
            service=service,
            current_user_id=current_user_id,
        )
        
        # Mark as read
        return await service.mark_notification_as_read(notification_id)
    except HTTPException:
        # Re-raise the 404 exception from get_notification
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}",
        )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str = Path(...),
    service: INotificationService = Depends(get_notification_service),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Delete a notification.
    """
    try:
        # First check if notification belongs to current user
        notification = await get_notification(
            notification_id=notification_id,
            service=service,
            current_user_id=current_user_id,
        )
        
        # Delete notification
        success = await service.delete_notification(notification_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete notification",
            )
    except HTTPException:
        # Re-raise the 404 exception from get_notification
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}",
        ) 