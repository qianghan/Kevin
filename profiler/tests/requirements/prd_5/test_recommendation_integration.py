"""
Integration tests for the recommendation engine with real services.

This module tests the integration between the recommendation service and other services
such as notification, profile, document, and QA services.
"""

import asyncio
import pytest
from datetime import datetime, timedelta, UTC
import uuid

from profiler.services.recommendation.service import RecommendationService
from profiler.services.recommendation.models import Recommendation, RecommendationCategory
from profiler.services.notification.service import NotificationService
from profiler.services.notification.models import Notification, NotificationType, NotificationStatus
from profiler.services.profile.service import IProfileService
from profiler.services.document.service import IDocumentService
from profiler.services.qa.service import IQAService


class TestRecommendationIntegration:
    """Test integration between recommendation service and other real services."""

    @pytest.fixture
    async def recommendation_service(self):
        """Fixture for creating a recommendation service with real dependencies."""
        return RecommendationService()
    
    @pytest.fixture
    async def notification_service(self):
        """Fixture for creating a notification service."""
        return NotificationService()
    
    @pytest.mark.asyncio
    async def test_create_recommendation_with_notification(self, recommendation_service, notification_service):
        """Test creating a recommendation and sending a notification."""
        # Create a test user ID
        user_id = str(uuid.uuid4())
        
        # Create a recommendation
        recommendation = Recommendation(
            user_id=user_id,
            title="Test Recommendation",
            description="This is a test recommendation",
            category=RecommendationCategory.SKILL,
            priority=0.8,
            steps=["Step 1: Do this", "Step 2: Do that"],
            status="active"
        )
        
        # Create the recommendation using the service
        saved_recommendation = await recommendation_service.create_recommendation(recommendation)
        
        # Verify the recommendation was created
        assert saved_recommendation.id is not None
        assert saved_recommendation.user_id == user_id
        assert saved_recommendation.title == "Test Recommendation"
        
        # Create a notification for the recommendation
        notification = await notification_service.create_recommendation_notification(
            user_id=user_id,
            recommendation_id=saved_recommendation.id,
            title=saved_recommendation.title,
            description=saved_recommendation.description
        )
        
        # Verify the notification was created
        assert notification.id is not None
        assert notification.user_id == user_id
        assert notification.type == NotificationType.RECOMMENDATION
        assert notification.related_entity_id == saved_recommendation.id
        assert notification.status in [NotificationStatus.PENDING, NotificationStatus.SENT]
        
        # Get the user's recommendations
        user_recommendations = await recommendation_service.get_recommendations_for_user(user_id)
        
        # Verify the recommendation is in the user's list
        assert len(user_recommendations) > 0
        assert any(r.id == saved_recommendation.id for r in user_recommendations)
        
        # Mark the recommendation as completed
        updated_recommendation = await recommendation_service.update_recommendation_status(
            saved_recommendation.id, "completed"
        )
        
        # Verify the status was updated
        assert updated_recommendation.status == "completed"
        assert updated_recommendation.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_recommendation_lifecycle(self, recommendation_service, notification_service):
        """Test the full lifecycle of a recommendation with real services."""
        # Create a test user ID
        user_id = str(uuid.uuid4())
        
        # Create a recommendation
        recommendation = Recommendation(
            user_id=user_id,
            title="Improve Python Skills",
            description="Enhance your Python programming skills",
            category=RecommendationCategory.SKILL,
            priority=0.9,
            steps=[
                "Step 1: Complete Python basics course",
                "Step 2: Build a small project",
                "Step 3: Contribute to open source"
            ],
            detailed_steps="Follow detailed instructions to improve your Python skills",
            expires_at=datetime.now(UTC) + timedelta(days=30),
            status="active"
        )
        
        # Save the recommendation
        saved_recommendation = await recommendation_service.create_recommendation(recommendation)
        
        # Create notification
        notification = await notification_service.create_recommendation_notification(
            user_id=user_id,
            recommendation_id=saved_recommendation.id,
            title=saved_recommendation.title,
            description=saved_recommendation.description
        )
        
        # Update recommendation progress
        updated_recommendation = await recommendation_service.update_recommendation_progress(
            saved_recommendation.id, 0.33
        )
        assert updated_recommendation.progress == 0.33
        
        # Get user notifications
        user_notifications = await notification_service.get_user_notifications(user_id)
        assert len(user_notifications) > 0
        assert any(n.id == notification.id for n in user_notifications)
        
        # Mark notification as read
        read_notification = await notification_service.mark_notification_as_read(notification.id)
        assert read_notification.status == NotificationStatus.READ
        assert read_notification.read_at is not None
        
        # Complete recommendation
        completed_recommendation = await recommendation_service.update_recommendation_progress(
            saved_recommendation.id, 1.0
        )
        assert completed_recommendation.progress == 1.0
        assert completed_recommendation.status == "completed"
        assert completed_recommendation.completed_at is not None
        
        # Verify recommendation history
        history = await recommendation_service.get_recommendation_history(user_id)
        assert len(history) > 0
        assert any(r.id == saved_recommendation.id for r in history) 