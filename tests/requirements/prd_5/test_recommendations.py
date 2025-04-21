"""
BDD tests for recommendation engine functionality.

This module contains BDD-style tests for the recommendation engine that generates
personalized recommendations for users based on their profiles and activities.
"""

import pytest
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from profiler.services.recommendation.models import Recommendation, RecommendationCategory
from profiler.services.recommendation.repository import IRecommendationRepository, InMemoryRecommendationRepository
from profiler.services.recommendation.service import RecommendationService
from profiler.services.notification.service import NotificationService

# BDD-style test scenarios using pytest
# These tests validate the recommendation engine's functionality from a user perspective


@pytest.fixture
def mock_profile_service():
    """Create a mock profile service for testing."""
    mock = AsyncMock()
    
    # Mock profile data
    mock.get_profile.return_value = {
        "id": "user123",
        "name": "Test User",
        "email": "test@example.com",
        "skills": ["Python", "FastAPI"],
        "certifications": []
    }
    
    # Mock similar profiles data
    mock.get_similar_skill_profiles.return_value = [
        {
            "id": "user456",
            "name": "Similar User",
            "skills": ["Python", "FastAPI", "Django"],
            "certifications": [{"name": "AWS Certified Developer"}]
        }
    ]
    
    return mock


@pytest.fixture
def mock_qa_service():
    """Create a mock QA service for testing."""
    mock = AsyncMock()
    
    # Mock Q&A data
    mock.get_recent_user_answers.return_value = [
        {"id": "answer1", "question_id": "q1", "content": "Short answer"}
    ]
    
    # Mock answer quality evaluation
    mock.evaluate_answer_quality.return_value = 0.5  # Low quality
    
    return mock


@pytest.fixture
def mock_document_service():
    """Create a mock document service for testing."""
    mock = AsyncMock()
    
    # Mock document data
    mock.get_user_documents.return_value = [
        {"id": "doc1", "title": "Resume", "content": "..."}
    ]
    
    # Mock document analysis
    mock.analyze_document.return_value = {
        "issues": [
            {"description": "Add more detail to your work experience"}
        ]
    }
    
    return mock


@pytest.fixture
def notification_service():
    """Create a notification service for testing."""
    return NotificationService()


@pytest.fixture
def recommendation_repository():
    """Create an in-memory recommendation repository for testing."""
    return InMemoryRecommendationRepository()


@pytest.fixture
def recommendation_service(
    mock_profile_service, mock_qa_service, mock_document_service, 
    notification_service, recommendation_repository
):
    """Create a recommendation service with mock dependencies for testing."""
    return RecommendationService(
        profile_service=mock_profile_service,
        qa_service=mock_qa_service,
        document_service=mock_document_service,
        notification_service=notification_service,
        recommendation_repository=recommendation_repository
    )


# Scenario 1: User receives personalized recommendations
@pytest.mark.asyncio
async def test_user_receives_personalized_recommendations(recommendation_service):
    """
    Given a user with a profile
    When the system generates recommendations
    Then the user should receive personalized recommendations
    And the recommendations should match their profile
    """
    # Act: Generate recommendations
    user_id = "user123"
    recommendations = await recommendation_service.generate_recommendations_for_user(user_id)
    
    # Assert: User receives personalized recommendations
    assert recommendations is not None
    assert len(recommendations) > 0
    
    # Assert: All recommendations belong to the user
    for rec in recommendations:
        assert rec.user_id == user_id
    
    # Assert: Recommendations match the user's profile (check specific types)
    categories = [rec.category for rec in recommendations]
    assert RecommendationCategory.SKILL in categories or RecommendationCategory.CERTIFICATION in categories


# Scenario 2: User receives document improvement recommendations
@pytest.mark.asyncio
async def test_user_receives_document_recommendations(recommendation_service, mock_document_service):
    """
    Given a user with documents
    When the system analyzes the documents
    Then the user should receive document improvement recommendations
    """
    # Act: Generate document recommendations
    user_id = "user123"
    recommendations = await recommendation_service._generate_document_recommendations(user_id)
    
    # Assert: Document recommendations were generated
    assert recommendations is not None
    assert len(recommendations) > 0
    
    # Assert: Recommendations are of document category
    for rec in recommendations:
        assert rec.category == RecommendationCategory.DOCUMENT
    
    # Assert: Document service was called
    mock_document_service.get_user_documents.assert_called_once_with(user_id)
    mock_document_service.analyze_document.assert_called_once()


# Scenario 3: User without documents receives recommendation to upload resume
@pytest.mark.asyncio
async def test_user_without_documents_receives_upload_recommendation(recommendation_service, mock_document_service):
    """
    Given a user without documents
    When the system generates recommendations
    Then the user should receive a recommendation to upload their resume
    """
    # Arrange: Configure mock to return no documents
    mock_document_service.get_user_documents.return_value = []
    
    # Act: Generate document recommendations
    user_id = "user123"
    recommendations = await recommendation_service._generate_document_recommendations(user_id)
    
    # Assert: One recommendation was generated
    assert len(recommendations) == 1
    
    # Assert: Recommendation is to upload resume
    assert recommendations[0].category == RecommendationCategory.DOCUMENT
    assert "upload" in recommendations[0].title.lower()


# Scenario 4: User with incomplete profile receives profile recommendations
@pytest.mark.asyncio
async def test_user_with_incomplete_profile_receives_profile_recommendations(recommendation_service):
    """
    Given a user with an incomplete profile
    When the system analyzes their profile
    Then the user should receive recommendations to improve their profile
    """
    # Arrange: Incomplete profile with few skills and no summary
    profile = {
        "id": "user123",
        "name": "Test User",
        "skills": ["Python"],  # Less than 5 skills
        "summary": None  # Missing summary
    }
    
    # Act: Generate profile recommendations
    recommendations = await recommendation_service._generate_profile_recommendations(profile)
    
    # Assert: Multiple recommendations were generated
    assert len(recommendations) == 2
    
    # Assert: Recommendations include adding skills and a summary
    rec_titles = [rec.title.lower() for rec in recommendations]
    assert any("skill" in title for title in rec_titles)
    assert any("summary" in title for title in rec_titles)


# Scenario 5: System sends notifications for new recommendations
@pytest.mark.asyncio
async def test_system_sends_notifications_for_new_recommendations(
    recommendation_service, notification_service, mock_profile_service, recommendation_repository
):
    """
    Given a user with a profile
    When new recommendations are generated
    Then the system should send notifications for each new recommendation
    """
    # Spy on notification service
    original_create_notification = notification_service.create_recommendation_notification
    notification_calls = []
    
    async def spy_create_notification(*args, **kwargs):
        notification_calls.append((args, kwargs))
        return await original_create_notification(*args, **kwargs)
    
    notification_service.create_recommendation_notification = spy_create_notification
    
    # Act: Generate recommendations
    user_id = "user123"
    recommendations = await recommendation_service.generate_recommendations_for_user(user_id)
    
    # Assert: Notifications were sent for each recommendation
    assert len(notification_calls) == len(recommendations)


# Scenario 6: User can view their recommendation history
@pytest.mark.asyncio
async def test_user_can_view_recommendation_history(recommendation_service, recommendation_repository):
    """
    Given a user with past recommendations
    When the user requests their recommendation history
    Then they should see all their past recommendations
    """
    # Arrange: Add some historical recommendations
    user_id = "user123"
    today = datetime.now()
    
    historical_recs = [
        Recommendation(
            id="rec1",
            user_id=user_id,
            title="Old Recommendation 1",
            description="This is an old recommendation",
            category=RecommendationCategory.SKILL,
            created_at=today - timedelta(days=30),
            status="completed"
        ),
        Recommendation(
            id="rec2",
            user_id=user_id,
            title="Old Recommendation 2",
            description="This is another old recommendation",
            category=RecommendationCategory.DOCUMENT,
            created_at=today - timedelta(days=15),
            status="dismissed"
        )
    ]
    
    for rec in historical_recs:
        await recommendation_repository.save_recommendation(rec)
    
    # Act: Get recommendation history
    start_date = today - timedelta(days=60)
    end_date = today
    history = await recommendation_service.get_recommendation_history(user_id, start_date, end_date)
    
    # Assert: History contains the added recommendations
    assert len(history) == 2
    assert all(rec.user_id == user_id for rec in history)
    assert all(rec.created_at >= start_date for rec in history)
    assert all(rec.created_at <= end_date for rec in history)


# Scenario 7: User can track progress on recommendations
@pytest.mark.asyncio
async def test_user_can_track_recommendation_progress(recommendation_service, recommendation_repository):
    """
    Given a user with active recommendations
    When the user updates progress on a recommendation
    Then the recommendation should reflect the updated progress
    """
    # Arrange: Create an active recommendation
    user_id = "user123"
    rec = Recommendation(
        id="rec1",
        user_id=user_id,
        title="Active Recommendation",
        description="This is an active recommendation",
        category=RecommendationCategory.SKILL,
        status="active",
        progress=0.0
    )
    
    await recommendation_repository.save_recommendation(rec)
    
    # Act: Update progress
    progress = 0.5
    updated_rec = await recommendation_service.update_recommendation_progress("rec1", progress)
    
    # Assert: Progress was updated
    assert updated_rec is not None
    assert updated_rec.progress == progress
    
    # Verify from repository
    stored_rec = await recommendation_repository.get_recommendation_by_id("rec1")
    assert stored_rec.progress == progress


# Scenario 8: Recommendation performance benchmark
@pytest.mark.asyncio
async def test_recommendation_generation_performance(recommendation_service):
    """
    Given a recommendation engine
    When generating recommendations for multiple users
    Then the generation process should complete within acceptable time limits
    """
    # Arrange: Parameters for benchmark
    user_id = "user123"
    num_iterations = 5
    max_allowed_time_per_operation = 0.5  # seconds
    
    # Act: Measure time to generate recommendations
    start_time = time.time()
    
    for _ in range(num_iterations):
        await recommendation_service.generate_recommendations_for_user(user_id)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / num_iterations
    
    # Assert: Performance is within acceptable limits
    assert avg_time < max_allowed_time_per_operation, f"Recommendation generation took too long ({avg_time:.3f}s per operation)"
    
    # Output performance data
    print(f"\nPerformance benchmark:")
    print(f"- Generated recommendations {num_iterations} times")
    print(f"- Total time: {total_time:.3f}s")
    print(f"- Average time per operation: {avg_time:.3f}s") 