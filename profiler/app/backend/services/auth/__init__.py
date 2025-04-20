"""
Authentication service package.

This package provides authentication functionality for the application.
"""

from .auth_service import AuthenticationService
from .interfaces import AuthenticationServiceInterface
from .models import User, UserRole, Permission

__all__ = [
    'AuthenticationService',
    'AuthenticationServiceInterface',
    'User',
    'UserRole',
    'Permission'
] 