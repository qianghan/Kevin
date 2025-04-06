"""
Complete test suite for all Profiler API endpoints.

This module provides a comprehensive test suite for all OpenAPI endpoints
in the Profiler service, ensuring that all endpoints are thoroughly tested
with various input scenarios and edge cases.
"""

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
import io
import os
from datetime import datetime, timezone

from app.backend.api.main import (
    get_qa_service,
    get_document_service,
    get_recommendation_service,
)

# ============================
# Ask Endpoint Tests
# ============================

@pytest.mark.parametrize(
    "question,expected_status",
    [
        ("What are your academic achievements?", 200),
        ("How should I structure my essay?", 200),
        ("", 422),  # Empty question should fail validation
        (None, 422),  # None as question should fail validation
    ],
)
def test_ask_endpoint(client: TestClient, mock_qa_service, question, expected_status):
    """Test the /ask endpoint with various questions."""
    # Override the QA service dependency
    app = client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Make request
    payload = {"question": question} if question else {}
    response = client.post("/api/ask", json=payload)
    
    # Check status code
    assert response.status_code == expected_status
    
    # For successful requests, check response structure
    if expected_status == 200:
        data = response.json()
        assert "questions" in data
        assert "timestamp" in data
        assert isinstance(data["questions"], list)
        assert len(data["questions"]) > 0


@pytest.mark.asyncio
async def test_ask_endpoint_with_context(async_client, mock_qa_service):
    """Test the /ask endpoint with conversation context."""
    # Override the QA service dependency
    app = async_client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Patch the generate_questions method to check context handling
    with patch.object(
        mock_qa_service, 'generate_questions', return_value=[
            MagicMock(dict=lambda: {
                "question": "What are your strengths?",
                "category": "personal"
            })
        ]
    ) as mock_process:
        # Make request with context
        payload = {
            "question": "Tell me more about that",
            "context": {
                "previous_questions": ["What are your hobbies?"],
                "profile_data": {"interests": ["reading", "coding"]}
            }
        }
        response = await async_client.post("/api/ask", json=payload)
        
        # Check status code and response
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions"]) > 0
        
        # Verify that context was passed to the service
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        assert isinstance(kwargs.get('profile_data', {}).get('context', {}), dict)


@pytest.mark.parametrize(
    "invalid_json,expected_status,expected_detail",
    [
        ({"not_question": "invalid field"}, 422, "question"),  # Missing required field
        ({"question": 123}, 422, "str type"),  # Invalid type for question field
        ({"question": "valid", "context": "not a dict"}, 422, "dict"),  # Invalid context type
    ],
)
def test_ask_endpoint_validation(client: TestClient, mock_qa_service, invalid_json, expected_status, expected_detail):
    """Test validation for the /ask endpoint."""
    # Override the QA service dependency
    app = client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Make request with invalid payload
    response = client.post("/api/ask", json=invalid_json)
    
    # Check status code and error details
    assert response.status_code == expected_status
    assert expected_detail in response.text.lower()


# ============================
# Document Analysis Tests
# ============================

@pytest.mark.parametrize(
    "document_type,content,expected_status",
    [
        ("transcript", "Student: John Doe\nGPA: 3.8\nCourses: Math, Science", 200),
        ("essay", "My journey through high school has been...", 200),
        ("resume", "Experience: Internship at Tech Company", 200),
        ("letter", "Dear Admissions Committee...", 200),
        ("invalid_type", "Some content", 422),  # Invalid doc type
        ("transcript", "", 422),  # Empty content
    ],
)
def test_analyze_document_endpoint(
    client: TestClient, mock_document_service, document_type, content, expected_status
):
    """Test the /documents/analyze endpoint with different document types."""
    # Override the Document service dependency
    app = client.app
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    
    # Make request
    payload = {
        "document_type": document_type, 
        "content": content,
        "user_id": "test_user"
    }
    response = client.post("/api/documents/analyze", json=payload)
    
    # Check status code
    assert response.status_code == expected_status
    
    # For successful requests, check response structure
    if expected_status == 200:
        data = response.json()
        assert "content_type" in data
        assert "extracted_info" in data
        assert "confidence" in data


@pytest.mark.asyncio
async def test_analyze_document_with_metadata(async_client, mock_document_service):
    """Test the /documents/analyze endpoint with additional metadata."""
    # Override the Document service dependency
    app = async_client.app
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    
    # Patch the analyze_document method to verify metadata handling
    with patch.object(
        mock_document_service, 'analyze_document', return_value=MagicMock(
            document_id="test_doc_123",
            text_content="GPA: 3.8\nCourses: Math, Science",
            metadata={"source": "uploaded_file", "processing_time": 1.2},
            sections=[{"title": "Grades", "content": "GPA: 3.8"}],
            analysis={"overall_quality": 0.85},
            extracted_data={"gpa": 3.8, "courses": ["Math", "Science"]},
            dict=lambda: {
                "content_type": "transcript",
                "extracted_info": {"gpa": 3.8, "courses": ["Math", "Science"]},
                "confidence": 0.9,
                "metadata": {"source": "uploaded_file", "processing_time": 1.2}
            }
        )
    ) as mock_analyze:
        # Make request with metadata
        payload = {
            "document_type": "transcript",
            "content": "GPA: 3.8\nCourses: Math, Science",
            "user_id": "test_user",
            "metadata": {
                "filename": "transcript.pdf",
                "upload_date": "2023-05-15"
            }
        }
        response = await async_client.post("/api/documents/analyze", json=payload)
        
        # Check status code and response
        assert response.status_code == 200
        
        # Verify metadata was passed to the service
        mock_analyze.assert_called_once()
        args, kwargs = mock_analyze.call_args
        assert "metadata" in kwargs
        assert kwargs["metadata"]["filename"] == "transcript.pdf"


@pytest.mark.asyncio
async def test_upload_document(async_client, mock_document_service):
    """Test the /documents/upload endpoint for file uploads."""
    # Override the Document service dependency
    app = async_client.app
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    
    # Mock the analyze_document method
    with patch.object(
        mock_document_service, 'analyze_document', return_value=MagicMock(
            document_id="test_doc_123",
            text_content="This is a sample essay about personal growth...",
            metadata={"filename": "essay.txt", "content_type": "text/plain"},
            sections=[{"title": "Introduction", "content": "This is a sample essay..."}],
            analysis={"overall_quality": 0.85},
            extracted_data={"topic": "Personal Growth", "word_count": 500},
            dict=lambda: {
                "content_type": "essay",
                "extracted_info": {"topic": "Personal Growth", "word_count": 500},
                "confidence": 0.85,
                "metadata": {"filename": "essay.txt", "content_type": "text/plain"}
            }
        )
    ), patch.object(
        mock_document_service, 'validate_document_type', return_value=True
    ):
        # Create a test file
        test_content = "This is a sample essay about personal growth..."
        
        # Make multipart request
        response = await async_client.post(
            "/api/documents/upload",
            files={"file": ("essay.txt", test_content, "text/plain")},
            data={"document_type": "essay", "user_id": "test_user"}
        )
        
        # Check status code and response
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "essay"
        assert "word_count" in data["extracted_info"]


@pytest.mark.asyncio
async def test_get_document_types(async_client, mock_document_service):
    """Test the /documents/types endpoint."""
    # Override the Document service dependency
    app = async_client.app
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    
    # Mock the validate_document_type method to control test behavior
    with patch.object(
        mock_document_service, 'validate_document_type', 
        side_effect=lambda doc_type: doc_type in ["transcript", "essay", "resume", "letter"]
    ):
        # Make request
        response = await async_client.get("/api/documents/types")
        
        # Check status code and response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "transcript" in data
        assert "essay" in data


# ============================
# Recommendations Tests
# ============================

def test_recommendations_endpoint(client: TestClient, mock_recommendation_service):
    """Test the /recommendations endpoint."""
    # Override the Recommendation service dependency
    app = client.app
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    
    # Mock the generate_recommendations method
    with patch.object(
        mock_recommendation_service, 'generate_recommendations', 
        return_value=[
            MagicMock(
                category="academic",
                title="Improve GPA",
                description="Focus on improving your GPA",
                priority=1,
                action_items=["Study more", "Get tutoring"],
                confidence=0.8,
                dict=lambda: {
                    "category": "academic",
                    "title": "Improve GPA",
                    "description": "Focus on improving your GPA",
                    "priority": 1,
                    "action_items": ["Study more", "Get tutoring"],
                    "confidence": 0.8
                }
            )
        ]
    ):
        # Make request
        payload = {
            "user_id": "test_user",
            "profile_data": {
                "academic": {"gpa": 3.2},
                "extracurricular": {"activities": ["Chess Club"]}
            }
        }
        response = client.post("/api/recommendations", json=payload)
        
        # Check status code and response
        assert response.status_code == 200
        recommendations = response.json()
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert recommendations[0]["category"] == "academic"
        assert recommendations[0]["title"] == "Improve GPA"


@pytest.mark.parametrize(
    "categories,expected_status",
    [
        (["academic"], 200),
        (["extracurricular"], 200),
        (["academic", "personal"], 200),
        (None, 200),  # No categories specified
        (["invalid_category"], 200),  # Service should handle validation
    ],
)
def test_recommendations_with_categories(
    client: TestClient, mock_recommendation_service, categories, expected_status
):
    """Test the /recommendations endpoint with category filtering."""
    # Override the Recommendation service dependency
    app = client.app
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    
    # Mock the generate_recommendations method
    with patch.object(
        mock_recommendation_service, 'generate_recommendations', 
        return_value=[
            MagicMock(
                category=categories[0] if categories else "academic",
                title=f"Recommendation for {categories[0] if categories else 'academic'}",
                description="Sample recommendation",
                priority=1,
                action_items=["Action 1", "Action 2"],
                confidence=0.8,
                dict=lambda: {
                    "category": categories[0] if categories else "academic",
                    "title": f"Recommendation for {categories[0] if categories else 'academic'}",
                    "description": "Sample recommendation",
                    "priority": 1,
                    "action_items": ["Action 1", "Action 2"],
                    "confidence": 0.8
                }
            )
        ]
    ) as mock_generate:
        # Prepare request URL with categories if specified
        url = "/api/recommendations"
        if categories:
            url += f"?categories={','.join(categories)}"
        
        # Make request
        payload = {
            "user_id": "test_user",
            "profile_data": {
                "academic": {"gpa": 3.5},
                "extracurricular": {"activities": ["Debate Team"]}
            }
        }
        response = client.post(url, json=payload)
        
        # Check status code and response
        assert response.status_code == expected_status
        
        # For successful requests, verify categories were passed to service
        if expected_status == 200:
            mock_generate.assert_called_once()
            args, kwargs = mock_generate.call_args
            passed_categories = kwargs.get('categories')
            if categories:
                assert passed_categories == categories
            else:
                assert passed_categories is None


def test_profile_summary_endpoint(client: TestClient, mock_recommendation_service):
    """Test the /profile-summary endpoint."""
    # Override the Recommendation service dependency
    app = client.app
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    
    # Mock the get_profile_summary method
    with patch.object(
        mock_recommendation_service, 'get_profile_summary', 
        return_value=MagicMock(
            strengths=["Strong GPA", "Leadership experience"],
            areas_for_improvement=["More extracurricular activities"],
            unique_selling_points=["Founded a tech startup"],
            overall_quality=0.85,
            last_updated=datetime.now(timezone.utc).isoformat(),
            dict=lambda: {
                "strengths": ["Strong GPA", "Leadership experience"],
                "areas_for_improvement": ["More extracurricular activities"],
                "unique_selling_points": ["Founded a tech startup"],
                "overall_quality": 0.85,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        )
    ):
        # Make request
        payload = {
            "user_id": "test_user",
            "profile_data": {
                "academic": {"gpa": 3.8},
                "extracurricular": {"activities": ["Chess Club", "Student Council"]},
                "personal": {"achievements": ["Founded a tech startup"]}
            }
        }
        response = client.post("/api/profile-summary", json=payload)
        
        # Check status code and response
        assert response.status_code == 200
        summary = response.json()
        assert "strengths" in summary
        assert "areas_for_improvement" in summary
        assert "unique_selling_points" in summary
        assert "overall_quality" in summary
        assert "last_updated" in summary
        assert len(summary["strengths"]) > 0
        assert isinstance(summary["overall_quality"], float)


# ============================
# Health and Utilities Tests
# ============================

def test_health_endpoint(client: TestClient):
    """Test the /health endpoint."""
    response = client.get("/api/health")
    
    # Check status code and response
    assert response.status_code == 200
    health_info = response.json()
    assert "status" in health_info
    assert health_info["status"] == "ok"
    assert "timestamp" in health_info
    assert "version" in health_info
    assert "api" in health_info


@pytest.mark.parametrize(
    "include_key,expected_status",
    [
        (True, 200),  # Valid API key
        (False, 401),  # Missing API key
    ],
)
def test_api_key_validation(client: TestClient, mock_qa_service, include_key, expected_status):
    """Test API key validation middleware."""
    # Override the QA service dependency
    app = client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Prepare headers based on test case
    headers = {}
    if include_key:
        headers["X-API-Key"] = "test_api_key"  # The mock key is configured in conftest.py
    
    # Make request to a protected endpoint
    payload = {"question": "How are you?"}
    response = client.post("/api/ask", json=payload, headers=headers)
    
    # Check status code
    assert response.status_code == expected_status
    
    # For failed requests, check error message
    if expected_status == 401:
        error_data = response.json()
        assert "detail" in error_data
        assert "api key" in error_data["detail"].lower()


# ============================
# End-to-End Flow Tests
# ============================

@pytest.mark.asyncio
async def test_ui_flow_document_to_recommendations(async_client, mock_document_service, mock_recommendation_service):
    """Test a complete UI flow from document upload to recommendations."""
    # Override service dependencies
    app = async_client.app
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    
    # Mock the document analysis
    with patch.object(
        mock_document_service, 'analyze_document', 
        return_value=MagicMock(
            document_id="test_doc_123",
            text_content="I'm a student with a 3.8 GPA...",
            metadata={"filename": "essay.txt"},
            sections=[{"title": "Academic", "content": "GPA: 3.8"}],
            analysis={"overall_quality": 0.9},
            extracted_data={
                "academic": {"gpa": 3.8, "courses": ["AP Calculus", "AP Physics"]},
                "extracurricular": {"activities": ["Debate Team", "Science Olympiad"]}
            },
            dict=lambda: {
                "document_id": "test_doc_123",
                "content_type": "essay",
                "extracted_info": {
                    "academic": {"gpa": 3.8, "courses": ["AP Calculus", "AP Physics"]},
                    "extracurricular": {"activities": ["Debate Team", "Science Olympiad"]}
                },
                "confidence": 0.9,
                "metadata": {"filename": "essay.txt"}
            }
        )
    ), patch.object(
        mock_recommendation_service, 'generate_recommendations',
        return_value=[
            MagicMock(
                category="academic",
                title="Enhance Your Academic Profile",
                description="Consider taking more AP courses",
                priority=1,
                action_items=["Take AP Biology", "Consider a summer program"],
                confidence=0.85,
                dict=lambda: {
                    "category": "academic",
                    "title": "Enhance Your Academic Profile",
                    "description": "Consider taking more AP courses",
                    "priority": 1,
                    "action_items": ["Take AP Biology", "Consider a summer program"],
                    "confidence": 0.85
                }
            )
        ]
    ):
        # Step 1: Upload and analyze document
        test_content = "I'm a student with a 3.8 GPA..."
        
        document_response = await async_client.post(
            "/api/documents/analyze",
            json={
                "document_type": "essay",
                "content": test_content,
                "user_id": "test_user"
            }
        )
        
        assert document_response.status_code == 200
        document_data = document_response.json()
        
        # Step 2: Extract profile data from the document
        profile_data = {
            "academic": document_data["extracted_info"]["academic"],
            "extracurricular": document_data["extracted_info"]["extracurricular"]
        }
        
        # Step 3: Generate recommendations based on profile data
        recommendations_response = await async_client.post(
            "/api/recommendations",
            json={
                "user_id": "test_user",
                "profile_data": profile_data
            }
        )
        
        assert recommendations_response.status_code == 200
        recommendations = recommendations_response.json()
        assert len(recommendations) > 0
        assert recommendations[0]["category"] == "academic"


@pytest.mark.asyncio
async def test_ui_flow_qa_interaction(async_client, mock_qa_service):
    """Test a complete UI flow for Q&A interaction."""
    # Override service dependencies
    app = async_client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Mock the QA service methods
    with patch.object(
        mock_qa_service, 'generate_questions', 
        side_effect=[
            # First call returns initial questions
            [
                MagicMock(
                    question_id="q1",
                    category="academic",
                    question_text="What is your GPA?",
                    expected_response_type="number",
                    required=True,
                    dict=lambda: {
                        "question_id": "q1",
                        "category": "academic",
                        "question": "What is your GPA?",
                        "expected_response_type": "number",
                        "required": True
                    }
                )
            ],
            # Second call returns follow-up questions
            [
                MagicMock(
                    question_id="q2",
                    category="academic",
                    question_text="What are your favorite subjects?",
                    expected_response_type="text",
                    required=True,
                    dict=lambda: {
                        "question_id": "q2",
                        "category": "academic",
                        "question": "What are your favorite subjects?",
                        "expected_response_type": "text",
                        "required": True
                    }
                )
            ]
        ]
    ), patch.object(
        mock_qa_service, 'evaluate_answer',
        return_value=MagicMock(
            question_id="q1",
            response="3.8",
            confidence=0.9,
            quality_score=0.95,
            dict=lambda: {
                "question_id": "q1",
                "response": "3.8",
                "confidence": 0.9,
                "quality_score": 0.95
            }
        )
    ):
        # Step 1: Ask initial question
        initial_response = await async_client.post(
            "/api/ask",
            json={
                "question": "I want to build my profile",
                "context": {"user_id": "test_user"}
            }
        )
        
        assert initial_response.status_code == 200
        initial_data = initial_response.json()
        assert len(initial_data["questions"]) > 0
        question_id = initial_data["questions"][0]["question_id"]
        
        # Step 2: Answer the question
        answer_response = await async_client.post(
            "/api/ask",
            json={
                "question": "My GPA is 3.8",
                "context": {
                    "user_id": "test_user",
                    "question_id": question_id,
                    "previous_questions": [initial_data["questions"][0]]
                }
            }
        )
        
        assert answer_response.status_code == 200
        answer_data = answer_response.json()
        assert len(answer_data["questions"]) > 0
        assert answer_data["questions"][0]["question_id"] != question_id  # Should be a new question


@pytest.mark.asyncio
async def test_ui_flow_profile_summary(async_client, mock_recommendation_service, mock_document_service):
    """Test a complete UI flow for generating a profile summary."""
    # Override service dependencies
    app = async_client.app
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    
    # Mock the document analysis and profile summary
    with patch.object(
        mock_document_service, 'analyze_document', 
        return_value=MagicMock(
            document_id="test_doc_123",
            text_content="Resume content...",
            metadata={"filename": "resume.pdf"},
            extracted_data={
                "education": {"school": "Stanford", "gpa": 3.9},
                "experience": [{"title": "Intern", "company": "Google"}]
            },
            dict=lambda: {
                "document_id": "test_doc_123",
                "content_type": "resume",
                "extracted_info": {
                    "education": {"school": "Stanford", "gpa": 3.9},
                    "experience": [{"title": "Intern", "company": "Google"}]
                },
                "confidence": 0.95
            }
        )
    ), patch.object(
        mock_recommendation_service, 'get_profile_summary',
        return_value=MagicMock(
            strengths=["Strong academic record", "Top-tier internship"],
            areas_for_improvement=["Add more leadership experience"],
            unique_selling_points=["Stanford education", "Google internship"],
            overall_quality=0.9,
            last_updated=datetime.now(timezone.utc).isoformat(),
            dict=lambda: {
                "strengths": ["Strong academic record", "Top-tier internship"],
                "areas_for_improvement": ["Add more leadership experience"],
                "unique_selling_points": ["Stanford education", "Google internship"],
                "overall_quality": 0.9,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        )
    ):
        # Step 1: Analyze document
        document_response = await async_client.post(
            "/api/documents/analyze",
            json={
                "document_type": "resume",
                "content": "Resume content...",
                "user_id": "test_user"
            }
        )
        
        assert document_response.status_code == 200
        document_data = document_response.json()
        
        # Step 2: Generate profile summary
        profile_data = {
            "education": document_data["extracted_info"]["education"],
            "experience": document_data["extracted_info"]["experience"]
        }
        
        summary_response = await async_client.post(
            "/api/profile-summary",
            json={
                "user_id": "test_user",
                "profile_data": profile_data
            }
        )
        
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        assert "strengths" in summary_data
        assert "areas_for_improvement" in summary_data
        assert "overall_quality" in summary_data
        assert summary_data["overall_quality"] > 0.0


# ============================
# Error Handling Tests
# ============================

@pytest.mark.asyncio
async def test_error_handling_service_error(async_client, mock_qa_service):
    """Test error handling for service errors."""
    # Override service dependencies
    app = async_client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Mock the generate_questions method to raise an error
    with patch.object(
        mock_qa_service, 'generate_questions', 
        side_effect=Exception("Service error occurred")
    ):
        # Make request
        response = await async_client.post(
            "/api/ask",
            json={
                "question": "What is your GPA?",
                "context": {"user_id": "test_user"}
            }
        )
        
        # Check status code and error response
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "error" in error_data["detail"].lower()


@pytest.mark.asyncio
async def test_error_handling_rate_limit(async_client, mock_qa_service):
    """Test error handling for rate limiting."""
    # Override service dependencies
    app = async_client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Patch the rate limiter to always reject
    with patch('app.backend.api.main.rate_limiter.is_allowed', return_value=False):
        # Make request
        response = await async_client.post(
            "/api/ask",
            json={
                "question": "What is your GPA?",
                "context": {"user_id": "test_user"}
            }
        )
        
        # Check status code and error response
        assert response.status_code == 429
        error_data = response.json()
        assert "detail" in error_data
        assert "rate limit" in error_data["detail"].lower()


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 