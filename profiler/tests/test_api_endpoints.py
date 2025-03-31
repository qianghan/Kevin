"""
Tests for the FastAPI endpoints in the Student Profiler.

This module tests the main API endpoints for:
- Q&A (ask endpoint)
- Document analysis
- Recommendations
- Profile summary
- Health check
"""

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from profiler.app.backend.api.main import (
    get_qa_service,
    get_document_service,
    get_recommender_service,
)


# Test Q&A endpoint
@pytest.mark.parametrize(
    "question,expected_status",
    [
        ("What are your academic achievements?", 200),
        ("", 422),  # Empty question should fail validation
    ],
)
def test_ask_endpoint(client: TestClient, mock_qa_service, question, expected_status):
    """Test the /ask endpoint with various questions."""
    # Override the QA service dependency
    app = client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Make request
    payload = {"question": question} if question else {}
    response = client.post("/ask", json=payload)
    
    # Check status code
    assert response.status_code == expected_status
    
    # For successful requests, check response structure
    if expected_status == 200:
        data = response.json()
        assert "answer" in data
        assert "follow_up_questions" in data
        assert "confidence" in data
        assert isinstance(data["follow_up_questions"], list)
        assert 0 <= data["confidence"] <= 1


@pytest.mark.asyncio
async def test_ask_endpoint_with_context(async_client, mock_qa_service):
    """Test the /ask endpoint with conversation context."""
    # Override the QA service dependency
    app = async_client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Patch the process_input method to check context handling
    with patch.object(
        mock_qa_service, 'process_input', return_value={
            "answer": "This is a response with context",
            "follow_up_questions": ["What next?"],
            "confidence": 0.9,
            "extracted_info": {"key": "value"}
        }
    ) as mock_process:
        # Make request with context
        payload = {
            "question": "Tell me more about that",
            "context": {
                "previous_questions": ["What are your hobbies?"],
                "profile_data": {"interests": ["reading", "coding"]}
            }
        }
        response = await async_client.post("/ask", json=payload)
        
        # Check status code and response
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a response with context"
        
        # Verify that context was passed to the service
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        assert "context" in kwargs
        assert kwargs["context"]["profile_data"]["interests"] == ["reading", "coding"]


# Test document analysis endpoint
@pytest.mark.parametrize(
    "document_type,content,expected_status",
    [
        ("transcript", "Student: John Doe\nGPA: 3.8\nCourses: Math, Science", 200),
        ("essay", "My journey through high school has been...", 200),
        ("resume", "Experience: Internship at Tech Company", 200),
        ("invalid_type", "Some content", 422),  # Invalid doc type
        ("transcript", "", 422),  # Empty content
    ],
)
def test_analyze_document_endpoint(
    client: TestClient, mock_document_service, document_type, content, expected_status
):
    """Test the /analyze-document endpoint with different document types."""
    # Override the Document service dependency
    app = client.app
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    
    # Make request
    payload = {"document_type": document_type, "content": content}
    response = client.post("/analyze-document", json=payload)
    
    # Check status code
    assert response.status_code == expected_status
    
    # For successful requests, check response structure
    if expected_status == 200:
        data = response.json()
        assert "analysis" in data
        assert "document_type" in data
        assert "confidence" in data
        assert data["document_type"] == document_type


@pytest.mark.asyncio
async def test_analyze_document_with_metadata(async_client, mock_document_service):
    """Test the /analyze-document endpoint with additional metadata."""
    # Override the Document service dependency
    app = async_client.app
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    
    # Patch the analyze method to verify metadata handling
    with patch.object(
        mock_document_service, 'analyze', return_value={
            "content_type": "transcript",
            "extracted_info": {"gpa": 3.8, "courses": ["Math", "Science"]},
            "confidence": 0.9,
            "metadata": {"source": "uploaded_file", "processing_time": 1.2}
        }
    ) as mock_analyze:
        # Make request with metadata
        payload = {
            "document_type": "transcript",
            "content": "GPA: 3.8\nCourses: Math, Science",
            "metadata": {
                "filename": "transcript.pdf",
                "upload_date": "2023-05-15"
            }
        }
        response = await async_client.post("/analyze-document", json=payload)
        
        # Check status code and response
        assert response.status_code == 200
        
        # Verify metadata was passed to the service
        mock_analyze.assert_called_once()
        args, kwargs = mock_analyze.call_args
        assert "metadata" in kwargs
        assert kwargs["metadata"]["filename"] == "transcript.pdf"


# Test recommendations endpoint
def test_recommendations_endpoint(client: TestClient, mock_recommendation_service):
    """Test the /recommendations endpoint."""
    # Override the Recommender service dependency
    app = client.app
    app.dependency_overrides[get_recommender_service] = lambda: mock_recommendation_service
    
    # Define a user profile
    user_profile = {
        "user_id": "test_user",
        "academic": {
            "gpa": 3.8,
            "courses": ["Calculus", "Physics", "Computer Science"]
        },
        "extracurricular": {
            "activities": ["Robotics Club", "Volunteer Work"]
        }
    }
    
    # Make request
    response = client.post("/recommendations", json=user_profile)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "academic" in data["recommendations"]
    assert "extracurricular" in data["recommendations"]


@pytest.mark.parametrize(
    "section,expected_status",
    [
        ("academic", 200),
        ("extracurricular", 200),
        ("personal", 200),
        ("invalid_section", 422),  # Invalid section
    ],
)
def test_section_recommendations_endpoint(
    client: TestClient, mock_recommendation_service, section, expected_status
):
    """Test the /recommendations/{section} endpoint for specific profile sections."""
    # Override the Recommender service dependency
    app = client.app
    app.dependency_overrides[get_recommender_service] = lambda: mock_recommendation_service
    
    # Define a section profile
    section_data = {
        "user_id": "test_user",
        "data": {
            "field1": "value1",
            "field2": "value2"
        }
    }
    
    # Make request
    if section == "invalid_section":
        response = client.post(f"/recommendations/{section}", json=section_data)
        assert response.status_code == expected_status
    else:
        with patch.object(
            mock_recommendation_service, 'get_section_recommendations',
            return_value={"recommendations": ["Rec 1", "Rec 2"], "quality_score": 0.75}
        ):
            response = client.post(f"/recommendations/{section}", json=section_data)
            assert response.status_code == expected_status
            
            if expected_status == 200:
                data = response.json()
                assert "recommendations" in data
                assert "quality_score" in data


# Test profile summary endpoint
def test_profile_summary_endpoint(client: TestClient, mock_recommendation_service):
    """Test the /profile-summary endpoint."""
    # Override the Recommender service dependency
    app = client.app
    app.dependency_overrides[get_recommender_service] = lambda: mock_recommendation_service
    
    # Define a user profile for summary
    user_profile = {
        "user_id": "test_user",
        "sections": {
            "academic": {"gpa": 3.8, "courses": ["Calculus", "Physics"]},
            "extracurricular": {"activities": ["Robotics Club"]},
            "personal": {"strengths": ["Leadership", "Communication"]}
        }
    }
    
    # Mock the get_profile_summary method
    with patch.object(
        mock_recommendation_service, 'get_profile_summary',
        return_value={
            "strengths": ["Strong academic record", "Leadership experience"],
            "areas_for_improvement": ["More international exposure"],
            "unique_selling_points": ["Combination of technical and soft skills"],
            "overall_quality": 0.85
        }
    ):
        # Make request
        response = client.post("/profile-summary", json=user_profile)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "strengths" in data["summary"]
        assert "areas_for_improvement" in data["summary"]
        assert "unique_selling_points" in data["summary"]
        assert "overall_quality" in data["summary"]


# Test health check endpoint
def test_health_endpoint(client: TestClient):
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


# Test API key validation
def test_api_key_validation(client: TestClient, mock_qa_service):
    """Test that API endpoints require a valid API key."""
    # Override the QA service dependency
    app = client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Test without API key
    response = client.post("/ask", json={"question": "Test question"})
    assert response.status_code == 401
    
    # Test with invalid API key
    headers = {"X-API-Key": "invalid_key"}
    response = client.post("/ask", json={"question": "Test question"}, headers=headers)
    assert response.status_code == 401
    
    # Test with valid API key
    headers = {"X-API-Key": "test_api_key"}  # Set in fixture
    response = client.post("/ask", json={"question": "Test question"}, headers=headers)
    assert response.status_code == 200 