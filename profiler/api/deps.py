"""
API dependencies module.

This module provides dependency functions for API endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from profiler.dependencies import get_current_user
from profiler.services.notification.interface import INotificationService
from profiler.dependencies import get_notification_service

# Re-export the notification service dependency
get_notification_service = get_notification_service


def get_current_user_id(user_id: str = Depends(get_current_user)) -> str:
    """
    Get the ID of the authenticated user.
    
    This is a convenience wrapper around get_current_user that just returns
    the user ID string rather than the full user object.
    
    Args:
        user_id: The ID of the current user from the token validation
        
    Returns:
        The user ID as a string
    """
    return user_id 