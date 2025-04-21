"""
Unit tests for the recommendation service.

This module contains unit tests for the recommendation service.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock

from profiler.services.recommendation.models import Recommendation, RecommendationCategory
from profiler.services.recommendation.service import RecommendationService
from profiler.services.recommendation.repository import IRecommendationRepository


@pytest.fixture
def mock_profile_service():
    """Create a mock profile service."""
    mock = AsyncMock()
    
    # Mock get_profile
    mock.get_profile.return_value = {
        "id": "user123",
        "name": "Test User",
        "email": "test@example.com",
        "skills": ["Python", "FastAPI"],
        "certifications": []
    }
    
    # Mock get_similar_skill_profiles
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
    """Create a mock QA service."""
    mock = AsyncMock()
    
    # Mock get_recent_user_answers
    mock.get_recent_user_answers.return_value = [
        {"id": "answer1", "question_id": "q1", "content": "Short answer"}
    ]
    
    # Mock evaluate_answer_quality
    mock.evaluate_answer_quality.return_value = 0.5  # Low quality
    
    return mock


@pytest.fixture
def mock_document_service():
    """Create a mock document service."""
    mock = AsyncMock()
    
    # Mock get_user_documents
    mock.get_user_documents.return_value = [
        {"id": "doc1", "title": "Resume", "content": "..."}
    ]
    
    # Mock analyze_document
    mock.analyze_document.return_value = {
        "issues": [
            {"description": "Add more detail to your work experience"}
        ]
    }
    
    return mock


@pytest.fixture
def mock_recommendation_repository():
    """Create a mock recommendation repository."""
    mock = AsyncMock()
    
    # Mock save_recommendation
    mock.save_recommendation.side_effect = lambda rec: rec
    
    # Mock get_recommendations_for_user
    mock.get_recommendations_for_user.return_value = []
    
    return mock


@pytest.fixture
def recommendation_service(
    mock_profile_service, mock_qa_service, mock_document_service, mock_recommendation_repository
):
    """Create a recommendation service with mock dependencies."""
    return RecommendationService(
        profile_service=mock_profile_service,
        qa_service=mock_qa_service,
        document_service=mock_document_service,
        recommendation_repository=mock_recommendation_repository
    )


class TestRecommendationService:
    """Tests for the RecommendationService class."""
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_for_user(self, recommendation_service):
        """Test generating recommendations for a user."""
        # Test generating recommendations
        recommendations = await recommendation_service.generate_recommendations_for_user("user123")
        
        # Verify all dependencies were called
        recommendation_service.profile_service.get_profile.assert_called_once_with("user123")
        recommendation_service.profile_service.get_similar_skill_profiles.assert_called_once_with("user123")
        recommendation_service.document_service.get_user_documents.assert_called_once_with("user123")
        recommendation_service.qa_service.get_recent_user_answers.assert_called_once_with("user123", limit=10)
        
        # Verify at least one recommendation from each source
        assert len(recommendations) >= 3
        
        # Check that all recommendations have the correct user ID
        for rec in recommendations:
            assert rec.user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_get_recommendations_for_user(self, recommendation_service, mock_recommendation_repository):
        """Test getting recommendations for a user."""
        # Setup mock return value
        mock_recommendations = [
            Recommendation(
                id="rec1",
                user_id="user123",
                title="Test Recommendation",
                description="Description",
                category=RecommendationCategory.SKILL,
                status="active"
            )
        ]
        mock_recommendation_repository.get_recommendations_for_user.return_value = mock_recommendations
        
        # Test getting recommendations
        recommendations = await recommendation_service.get_recommendations_for_user("user123", status="active")
        
        # Verify repository was called correctly
        mock_recommendation_repository.get_recommendations_for_user.assert_called_once_with("user123", "active")
        
        # Verify recommendations were returned
        assert recommendations == mock_recommendations
    
    @pytest.mark.asyncio
    async def test_get_recommendation_by_id(self, recommendation_service, mock_recommendation_repository):
        """Test getting a recommendation by ID."""
        # Setup mock return value
        mock_recommendation = Recommendation(
            id="rec1",
            user_id="user123",
            title="Test Recommendation",
            description="Description",
            category=RecommendationCategory.SKILL
        )
        mock_recommendation_repository.get_recommendation_by_id.return_value = mock_recommendation
        
        # Test getting recommendation by ID
        recommendation = await recommendation_service.get_recommendation_by_id("rec1")
        
        # Verify repository was called correctly
        mock_recommendation_repository.get_recommendation_by_id.assert_called_once_with("rec1")
        
        # Verify recommendation was returned
        assert recommendation == mock_recommendation
    
    @pytest.mark.asyncio
    async def test_update_recommendation_status(self, recommendation_service, mock_recommendation_repository):
        """Test updating recommendation status."""
        # Setup mock return value
        mock_recommendation = Recommendation(
            id="rec1",
            user_id="user123",
            title="Test Recommendation",
            description="Description",
            category=RecommendationCategory.SKILL,
            status="active"
        )
        mock_recommendation_repository.update_recommendation_status.return_value = mock_recommendation
        
        # Test updating recommendation status
        recommendation = await recommendation_service.update_recommendation_status("rec1", "completed")
        
        # Verify repository was called correctly
        mock_recommendation_repository.update_recommendation_status.assert_called_once_with("rec1", "completed")
        
        # Verify recommendation was returned
        assert recommendation == mock_recommendation
    
    @pytest.mark.asyncio
    async def test_update_recommendation_progress(self, recommendation_service, mock_recommendation_repository):
        """Test updating recommendation progress."""
        # Setup mock return value
        mock_recommendation = Recommendation(
            id="rec1",
            user_id="user123",
            title="Test Recommendation",
            description="Description",
            category=RecommendationCategory.SKILL,
            progress=0.5
        )
        mock_recommendation_repository.update_recommendation_progress.return_value = mock_recommendation
        
        # Test updating recommendation progress
        recommendation = await recommendation_service.update_recommendation_progress("rec1", 0.5)
        
        # Verify repository was called correctly
        mock_recommendation_repository.update_recommendation_progress.assert_called_once_with("rec1", 0.5)
        
        # Verify recommendation was returned
        assert recommendation == mock_recommendation
    
    @pytest.mark.asyncio
    async def test_generate_profile_recommendations(self, recommendation_service):
        """Test generating profile-based recommendations."""
        # Test profile with missing skills
        profile = {
            "id": "user123",
            "name": "Test User",
            "skills": ["Python"],  # Less than 5 skills
            "summary": None  # Missing summary
        }
        
        recommendations = await recommendation_service._generate_profile_recommendations(profile)
        
        # Should generate 2 recommendations (skills and summary)
        assert len(recommendations) == 2
        
        # Check skill recommendation
        skill_rec = next((r for r in recommendations if r.category == RecommendationCategory.SKILL), None)
        assert skill_rec is not None
        assert "skills" in skill_rec.title.lower()
        
        # Check summary recommendation
        summary_rec = next((r for r in recommendations if r.category == RecommendationCategory.PROFILE), None)
        assert summary_rec is not None
        assert "summary" in summary_rec.title.lower()
    
    @pytest.mark.asyncio
    async def test_generate_peer_comparison_recommendations(self, recommendation_service):
        """Test generating peer comparison recommendations."""
        # Test profile with different certifications from peers
        profile = {
            "id": "user123",
            "name": "Test User",
            "skills": ["Python", "FastAPI"],
            "certifications": []  # No certifications
        }
        
        # Configure mock to return peers with certifications
        recommendation_service.profile_service.get_similar_skill_profiles.return_value = [
            {
                "id": "peer1",
                "skills": ["Python", "FastAPI"],
                "certifications": [{"name": "AWS Certified Developer"}]
            },
            {
                "id": "peer2",
                "skills": ["Python", "Django"],
                "certifications": [{"name": "AWS Certified Developer"}]
            }
        ]
        
        recommendations = await recommendation_service._generate_peer_comparison_recommendations(profile)
        
        # Should generate 1 recommendation for certification
        assert len(recommendations) == 1
        assert recommendations[0].category == RecommendationCategory.CERTIFICATION
        assert "AWS Certified Developer" in recommendations[0].title
    
    @pytest.mark.asyncio
    async def test_generate_document_recommendations_no_documents(self, recommendation_service):
        """Test generating document recommendations when no documents exist."""
        # Configure mock to return no documents
        recommendation_service.document_service.get_user_documents.return_value = []
        
        recommendations = await recommendation_service._generate_document_recommendations("user123")
        
        # Should generate 1 recommendation to upload documents
        assert len(recommendations) == 1
        assert recommendations[0].category == RecommendationCategory.DOCUMENT
        assert "upload" in recommendations[0].title.lower()
    
    @pytest.mark.asyncio
    async def test_generate_document_recommendations_with_issues(self, recommendation_service):
        """Test generating document recommendations when documents have issues."""
        # Configure mock to return documents with issues
        recommendation_service.document_service.get_user_documents.return_value = [
            {"id": "doc1", "title": "Resume", "content": "..."}
        ]
        recommendation_service.document_service.analyze_document.return_value = {
            "issues": [
                {"description": "Add more detail to your work experience"},
                {"description": "Include your education history"}
            ]
        }
        
        recommendations = await recommendation_service._generate_document_recommendations("user123")
        
        # Should generate 1 recommendation with steps for each issue
        assert len(recommendations) == 1
        assert recommendations[0].category == RecommendationCategory.DOCUMENT
        assert "improve" in recommendations[0].title.lower()
        assert len(recommendations[0].steps) == 2
    
    @pytest.mark.asyncio
    async def test_generate_qa_recommendations_low_quality(self, recommendation_service):
        """Test generating Q&A recommendations when answers are low quality."""
        # Configure mock to return low quality answers
        recommendation_service.qa_service.get_recent_user_answers.return_value = [
            {"id": "answer1", "content": "Yes"},
            {"id": "answer2", "content": "No"}
        ]
        recommendation_service.qa_service.evaluate_answer_quality.return_value = 0.4  # Low quality
        
        recommendations = await recommendation_service._generate_qa_recommendations("user123")
        
        # Should generate 1 recommendation to improve Q&A responses
        assert len(recommendations) == 1
        assert "improve" in recommendations[0].title.lower()
    
    @pytest.mark.asyncio
    async def test_generate_qa_recommendations_high_quality(self, recommendation_service):
        """Test generating Q&A recommendations when answers are high quality."""
        # Configure mock to return high quality answers
        recommendation_service.qa_service.get_recent_user_answers.return_value = [
            {"id": "answer1", "content": "Detailed answer with examples..."},
            {"id": "answer2", "content": "Another great answer..."}
        ]
        recommendation_service.qa_service.evaluate_answer_quality.return_value = 0.9  # High quality
        
        recommendations = await recommendation_service._generate_qa_recommendations("user123")
        
        # Should not generate any recommendations
        assert len(recommendations) == 0
    
    def test_filter_duplicate_recommendations(self, recommendation_service):
        """Test filtering duplicate recommendations."""
        # Create existing recommendations
        existing_recommendations = [
            Recommendation(
                id="rec1",
                user_id="user123",
                title="Add more skills to your profile",
                category=RecommendationCategory.SKILL
            ),
            Recommendation(
                id="rec2",
                user_id="user123",
                title="Get AWS certification",
                category=RecommendationCategory.CERTIFICATION
            )
        ]
        
        # Create new recommendations including duplicates and similar ones
        new_recommendations = [
            Recommendation(
                user_id="user123",
                title="Add more skills to your profile",  # Exact duplicate
                category=RecommendationCategory.SKILL
            ),
            Recommendation(
                user_id="user123",
                title="Add skills to your profile",  # Similar to existing
                category=RecommendationCategory.SKILL
            ),
            Recommendation(
                user_id="user123",
                title="Azure certification",  # New recommendation
                category=RecommendationCategory.CERTIFICATION
            )
        ]
        
        filtered = recommendation_service._filter_duplicate_recommendations(
            new_recommendations, existing_recommendations
        )
        
        # Should only keep the Azure certification recommendation
        assert len(filtered) == 1
        assert filtered[0].title == "Azure certification" 