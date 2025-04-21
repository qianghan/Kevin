"""
Tests for notification API endpoints.

This module contains tests for the notification API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from profiler.main import app
from profiler.services.notification.models import (
    Notification,
    NotificationType,
    NotificationStatus,
)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock the get_current_user dependency."""
    with patch("profiler.dependencies.get_current_user") as mock:
        mock.return_value = "test-user-id"
        yield mock


@pytest.fixture
def mock_notification_service():
    """Mock the notification service."""
    with patch("profiler.dependencies.get_notification_service") as mock:
        service_mock = AsyncMock()
        mock.return_value = service_mock
        yield service_mock


def create_test_notification(user_id="test-user-id", status=NotificationStatus.PENDING):
    """Create a test notification."""
    return Notification(
        id="test-notification-id",
        user_id=user_id,
        type=NotificationType.RECOMMENDATION,
        title="Test Notification",
        message="This is a test notification",
        status=status,
        created_at=datetime.utcnow(),
        delivered_at=None,
        read_at=None,
        metadata={"test": "metadata"},
        related_entity_id="test-entity-id",
        related_entity_type="recommendation",
    )


class TestNotificationAPI:
    """Tests for notification API endpoints."""

    def test_create_notification(self, client, mock_current_user, mock_notification_service):
        """Test creating a notification."""
        # Setup
        notification = create_test_notification()
        mock_notification_service.send_notification.return_value = notification
        
        # Execute
        response = client.post(
            "/api/notifications/",
            json={
                "user_id": "test-user-id",
                "type": "RECOMMENDATION",
                "title": "Test Notification",
                "message": "This is a test notification",
                "metadata": {"test": "metadata"},
                "related_entity_id": "test-entity-id",
                "related_entity_type": "recommendation",
            },
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["id"] == "test-notification-id"
        assert response.json()["user_id"] == "test-user-id"
        assert response.json()["title"] == "Test Notification"
        mock_notification_service.send_notification.assert_called_once()

    def test_create_notification_for_other_user_forbidden(self, client, mock_current_user, mock_notification_service):
        """Test that creating a notification for another user is forbidden."""
        # Execute
        response = client.post(
            "/api/notifications/",
            json={
                "user_id": "other-user-id",  # Different from the authenticated user
                "type": "RECOMMENDATION",
                "title": "Test Notification",
                "message": "This is a test notification",
            },
        )
        
        # Assert
        assert response.status_code == 403
        mock_notification_service.send_notification.assert_not_called()

    def test_get_my_notifications(self, client, mock_current_user, mock_notification_service):
        """Test getting notifications for the current user."""
        # Setup
        notifications = [create_test_notification() for _ in range(3)]
        mock_notification_service.get_user_notifications.return_value = notifications
        
        # Execute
        response = client.get("/api/notifications/me")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 3
        mock_notification_service.get_user_notifications.assert_called_once_with(
            user_id="test-user-id",
            limit=20,
            offset=0,
            include_read=False,
        )

    def test_get_notification(self, client, mock_current_user, mock_notification_service):
        """Test getting a specific notification."""
        # Setup
        notification = create_test_notification()
        mock_notification_service.get_user_notifications.return_value = [notification]
        
        # Execute
        response = client.get(f"/api/notifications/{notification.id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == notification.id
        assert response.json()["title"] == notification.title
        mock_notification_service.get_user_notifications.assert_called_once()

    def test_get_nonexistent_notification(self, client, mock_current_user, mock_notification_service):
        """Test getting a notification that doesn't exist."""
        # Setup
        mock_notification_service.get_user_notifications.return_value = []
        
        # Execute
        response = client.get("/api/notifications/nonexistent-id")
        
        # Assert
        assert response.status_code == 404
        mock_notification_service.get_user_notifications.assert_called_once()

    def test_mark_notification_as_read(self, client, mock_current_user, mock_notification_service):
        """Test marking a notification as read."""
        # Setup
        notification = create_test_notification()
        read_notification = create_test_notification(status=NotificationStatus.READ)
        read_notification.read_at = datetime.utcnow()
        
        mock_notification_service.get_user_notifications.return_value = [notification]
        mock_notification_service.mark_notification_as_read.return_value = read_notification
        
        # Execute
        response = client.put(f"/api/notifications/{notification.id}/read")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "READ"
        assert response.json()["read_at"] is not None
        mock_notification_service.mark_notification_as_read.assert_called_once_with(notification.id)

    def test_delete_notification(self, client, mock_current_user, mock_notification_service):
        """Test deleting a notification."""
        # Setup
        notification = create_test_notification()
        mock_notification_service.get_user_notifications.return_value = [notification]
        mock_notification_service.delete_notification.return_value = True
        
        # Execute
        response = client.delete(f"/api/notifications/{notification.id}")
        
        # Assert
        assert response.status_code == 204
        mock_notification_service.delete_notification.assert_called_once_with(notification.id) 