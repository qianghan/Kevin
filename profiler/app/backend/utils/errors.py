"""
Error classes for the application.

This module defines custom error classes used throughout the application.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status

class BaseError(Exception):
    """Base error class for all application errors."""
    
    def __init__(self, message: str):
        """
        Initialize the error.
        
        Args:
            message: Error message
        """
        self.message = message
        super().__init__(message)


class ValidationError(BaseError):
    """Raised when input validation fails."""
    pass


class ResourceNotFoundError(BaseError):
    """Raised when a requested resource is not found."""
    pass


class StorageError(BaseError):
    """Raised when there is an error interacting with storage."""
    pass


class ServiceError(BaseError):
    """Raised when there is a general error in a service."""
    pass


class ConfigurationError(BaseError):
    """Raised when there is an error in configuration."""
    pass


class AuthenticationError(BaseError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(BaseError):
    """Raised when a user is not authorized to perform an action."""
    pass


class ExternalServiceError(BaseError):
    """Raised when an external service call fails."""
    pass


class RateLimitError(BaseError):
    """Raised when a rate limit is exceeded."""
    pass


class ConcurrencyError(BaseError):
    """Raised when there is a concurrency conflict."""
    pass

class ProfilerError(Exception):
    """Base exception class for all profiler errors."""
    code: str = "profiler_error"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )

class APIClientError(ProfilerError):
    """Error raised when external API calls fail."""
    code = "api_client_error"
    status_code = status.HTTP_502_BAD_GATEWAY

class DatabaseError(ProfilerError):
    """Error raised when database operations fail."""
    code = "database_error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR 