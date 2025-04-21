"""
Dependency injection module for FastAPI.

This module provides dependency injection functions for FastAPI.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from profiler.services.qa.service import IQAService, QAService
from profiler.services.document.service import IDocumentService, DocumentService
from profiler.services.profile.service import IProfileService, ProfileService
from profiler.services.recommendation.service import IRecommendationService, RecommendationService
from profiler.services.recommendation.repository import IRecommendationRepository, InMemoryRecommendationRepository
from profiler.services.notification.service import INotificationService, NotificationService
from profiler.db.session import get_db, AsyncSession

# OAuth2 scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Validate JWT token and return current user.

    For simplicity, we're returning a mock user ID for now.
    In a real application, this would validate the token.

    Args:
        token: The OAuth2 token.

    Returns:
        The ID of the current user.
    """
    # This is a simplified example
    # In production, you'd validate the JWT and extract the user ID
    # If invalid, raise HTTPException with status_code=401
    
    # Mock implementation for development
    if token == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return mock user ID
    return "user123"


def get_qa_service() -> IQAService:
    """
    Get the QA service.

    Returns:
        An implementation of the QA service.
    """
    return QAService()


def get_document_service() -> IDocumentService:
    """
    Get the document service.

    Returns:
        An implementation of the document service.
    """
    return DocumentService()


def get_profile_service() -> IProfileService:
    """
    Get the profile service.

    Returns:
        An implementation of the profile service.
    """
    return ProfileService()


def get_notification_service(db: AsyncSession = Depends(get_db)) -> INotificationService:
    """
    Get the notification service.

    Args:
        db: Database session for accessing notification data

    Returns:
        An implementation of the notification service.
    """
    return NotificationService(db_session=db)


def get_recommendation_repository() -> IRecommendationRepository:
    """
    Get the recommendation repository.

    Returns:
        An implementation of the recommendation repository.
    """
    # For development, use the in-memory repository
    # In production, this would return a database-backed repository
    return InMemoryRecommendationRepository()


def get_recommendation_service(
    profile_service: IProfileService = Depends(get_profile_service),
    qa_service: IQAService = Depends(get_qa_service),
    document_service: IDocumentService = Depends(get_document_service),
    notification_service: INotificationService = Depends(get_notification_service),
    recommendation_repository: IRecommendationRepository = Depends(get_recommendation_repository),
) -> IRecommendationService:
    """
    Get the recommendation service.

    Args:
        profile_service: The profile service.
        qa_service: The QA service.
        document_service: The document service.
        notification_service: The notification service.
        recommendation_repository: The recommendation repository.

    Returns:
        An implementation of the recommendation service.
    """
    return RecommendationService(
        profile_service=profile_service,
        qa_service=qa_service,
        document_service=document_service,
        notification_service=notification_service,
        recommendation_repository=recommendation_repository,
    ) 