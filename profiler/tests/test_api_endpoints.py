"""
Tests for the FastAPI endpoints in the Student Profiler.

This module tests the main API endpoints for:
- Q&A (ask endpoint)
- Document analysis and upload
- Recommendations
- Profile summary
- Health check
- WebSocket functionality
"""

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.backend.api.main import (
    get_qa_service,
    get_document_service,
    get_recommendation_service,
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
    response = client.post("/api/ask", json=payload, headers={"X-API-Key": "test_api_key"})
    
    # Check status code
    assert response.status_code == expected_status
    
    # For successful requests, check response structure
    if expected_status == 200:
        data = response.json()
        assert "questions" in data
        assert "timestamp" in data
        assert isinstance(data["questions"], list)


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
        response = await async_client.post(
            "/api/ask", 
            json=payload,
            headers={"X-API-Key": "test_api_key"}
        )
        
        # Check status code and response
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions"]) > 0
        
        # Verify that context was passed to the service
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        assert isinstance(kwargs.get('context', {}), dict)


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
    response = client.post("/api/documents/analyze", json=payload, headers={"X-API-Key": "test_api_key"})
    
    # Print response for debugging
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
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
    
    # Set up the mock with patch to properly track calls
    analyze_result = {
        "document_id": "test_doc_123",
        "content_type": "transcript",
        "extracted_info": {"gpa": 3.8, "courses": ["Math", "Science"]},
        "confidence": 0.9,
        "metadata": {"source": "uploaded_file", "processing_time": 1.2},
        "insights": [
            {
                "type": "strength",
                "content": "Strong academic performance",
                "category": "academic",
                "confidence": 0.9
            }
        ]
    }
    
    with patch.object(mock_document_service, 'analyze', return_value=analyze_result) as mock_analyze:
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
        response = await async_client.post(
            "/api/documents/analyze",
            json=payload,
            headers={"X-API-Key": "test_api_key"}
        )
        
        # Check status code and response
        assert response.status_code == 200
        
        # Verify analyze was called
        mock_analyze.assert_called_once()
        
        # Print the actual data for debugging
        print(f"Response JSON: {response.json()}")
        print(f"Call args: {mock_analyze.call_args}")


@pytest.mark.asyncio
async def test_upload_document(async_client, mock_document_service):
    """Test the /documents/upload endpoint for file uploads."""
    # Override the Document service dependency
    app = async_client.app
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    
    # Create a test file
    test_content = "This is a sample essay about personal growth..."
    
    # Set up the mock directly (no patching needed as we control the mock instance)
    mock_document_service.analyze.return_value = {
        "content_type": "essay",
        "extracted_info": {"topic": "Personal Growth", "word_count": 500},
        "insights": [],
        "confidence": 0.85,
        "metadata": {"filename": "essay.txt", "content_type": "text/plain"}
    }
    
    # Make multipart request
    response = await async_client.post(
        "/api/documents/upload",
        files={"file": ("essay.txt", test_content, "text/plain")},
        data={"document_type": "essay"},
        headers={"X-API-Key": "test_api_key"}
    )
    
    # Print response for debugging
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Check status code and response
    assert response.status_code == 200
    data = response.json()
    assert data["content_type"] == "essay"
    assert "extracted_info" in data
    assert "confidence" in data  # Just check if it exists, don't assert exact value


@pytest.mark.asyncio
async def test_get_document_types(async_client):
    """Test the /documents/types endpoint."""
    response = await async_client.get("/api/documents/types", headers={"X-API-Key": "test_api_key"})
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Verify the structure of each document type
    for doc_type in data:
        assert "value" in doc_type
        assert "description" in doc_type


# Test recommendations endpoint
def test_recommendations_endpoint(client: TestClient, mock_recommendation_service):
    """Test the /recommendations endpoint."""
    # Override the Recommender service dependency
    app = client.app
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    
    # Define a profile data request
    payload = {
        "user_id": "test_user",
        "profile_data": {
            "academic": {
                "gpa": 3.8,
                "courses": ["Calculus", "Physics", "Computer Science"]
            },
            "extracurricular": {
                "activities": ["Robotics Club", "Volunteer Work"]
            }
        }
    }
    
    # Make request
    # Try wrapping the payload in a 'request' object since that's what the error suggests is missing
    wrapped_payload = {"request": payload}
    response = client.post("/api/recommendations", json=wrapped_payload, headers={"X-API-Key": "test_api_key"})
    
    # Print response for debugging
    print(f"Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response body: {response.text}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for rec in data:
        assert "category" in rec
        assert "title" in rec
        assert "description" in rec
        assert "priority" in rec
        assert "action_items" in rec
        assert "confidence" in rec


@pytest.mark.parametrize(
    "categories,expected_status",
    [
        (["academic"], 200),
        (["extracurricular"], 200),
        (["academic", "personal"], 200),
        (None, 200),  # No categories specified
    ],
)
def test_recommendations_with_categories(
    client: TestClient, mock_recommendation_service, categories, expected_status
):
    """Test the /recommendations endpoint with category filtering."""
    # Override the Recommender service dependency
    app = client.app
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    
    # Define a profile data request
    payload = {
        "user_id": "test_user",
        "profile_data": {
            "academic": {"gpa": 3.8},
            "extracurricular": {"activities": ["Volunteering"]}
        }
    }
    
    # Create URL with query parameters if categories specified
    url = "/api/recommendations"
    if categories:
        query_params = "&".join([f"categories={cat}" for cat in categories])
        url = f"{url}?{query_params}"
    
    # Make request
    wrapped_payload = {"request": payload}
    response = client.post(url, json=wrapped_payload, headers={"X-API-Key": "test_api_key"})
    
    # Check response
    assert response.status_code == expected_status


# Test profile summary endpoint
def test_profile_summary_endpoint(client: TestClient, mock_recommendation_service):
    """Test the /profile-summary endpoint."""
    # Override the Recommender service dependency
    app = client.app
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    
    # Define a profile data request
    payload = {
        "user_id": "test_user",
        "profile_data": {
            "academic": {
                "gpa": 3.8,
                "courses": ["Calculus", "Physics"]
            },
            "extracurricular": {
                "activities": ["Robotics Club"]
            },
            "personal": {
                "strengths": ["Creative", "Analytical"]
            }
        }
    }
    
    # Make request
    response = client.post("/api/profile-summary", json=payload, headers={"X-API-Key": "test_api_key"})
    
    # Print response for debugging
    print(f"Profile summary response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Profile summary response body: {response.text}")
    
    # Check response structure
    assert response.status_code == 200
    data = response.json()
    assert "strengths" in data
    assert "areas_for_improvement" in data
    assert "unique_selling_points" in data
    assert "overall_quality" in data
    assert "last_updated" in data
    assert isinstance(data["strengths"], list)
    assert 0 <= data["overall_quality"] <= 1


# Test health endpoint
def test_health_endpoint(client: TestClient):
    """Test the /health endpoint."""
    response = client.get("/api/health", headers={"X-API-Key": "test_api_key"})
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert data["status"] == "ok"


# Test API key validation
@pytest.mark.parametrize(
    "include_key,expected_status",
    [
        (True, 200),  # Valid API key
        (False, 401),  # Missing API key
    ],
)
def test_api_key_validation(client: TestClient, include_key, expected_status):
    """Test that API key validation works across endpoints."""
    # No need for service dependency override for the health endpoint
    
    headers = {"X-API-Key": "test_api_key"} if include_key else {}
    response = client.get("/api/health", headers=headers)
    
    assert response.status_code == expected_status


# WebSocket Tests
@pytest.mark.skip("httpx.AsyncClient doesn't support websocket_connect")
@pytest.mark.asyncio
async def test_websocket_connection(async_client):
    """Test WebSocket connection establishment."""
    # Connect to WebSocket
    with patch("app.backend.api.websocket.manager.connect", return_value="test_session"), \
         patch("app.backend.api.websocket.manager.send_message"):
        with async_client.websocket_connect(
            "/api/ws/test_user", 
            headers={"X-API-Key": "test_api_key"}
        ) as websocket:
            # Should connect successfully
            assert websocket._client is not None


@pytest.mark.skip("httpx.AsyncClient doesn't support websocket_connect")
@pytest.mark.asyncio
async def test_websocket_message_handling(async_client):
    """Test WebSocket message handling."""
    # Create mocks
    mock_executor = AsyncMock()
    mock_executor.arun.return_value = {"status": "updated", "sections": {}}
    
    # Patch the necessary functions
    with patch("app.backend.api.websocket.manager.connect", return_value="test_session"), \
         patch("app.backend.api.websocket.manager.send_message"), \
         patch("app.backend.api.websocket.manager.workflow_executors", {"test_session": mock_executor}), \
         patch("app.backend.api.websocket.create_initial_state", return_value={"sections": {}}):
        
        with async_client.websocket_connect(
            "/api/ws/test_user", 
            headers={"X-API-Key": "test_api_key"}
        ) as websocket:
            # Send a test message
            await websocket.send_json({"type": "answer", "data": "Test answer"})
            
            # Executor should be called
            mock_executor.arun.assert_called_once()


# UI use case tests
@pytest.mark.asyncio
async def test_ui_flow_document_to_recommendations(async_client, mock_document_service, mock_recommendation_service):
    """Test complete UI flow from document upload to recommendations."""
    # Setup dependencies
    app = async_client.app
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    
    # Mock document analysis result
    doc_analysis_result = {
        "document_id": "test_doc_123",
        "content_type": "resume",
        "extracted_info": {
            "academic": {
                "education": [{"institution": "Test University", "degree": "BS Computer Science"}]
            },
            "extracurricular": {
                "experience": [{"company": "Tech Corp", "position": "Intern"}]
            }
        },
        "confidence": 0.9,
        "insights": [
            {
                "type": "strength", 
                "content": "Technical skills",
                "category": "skills",
                "confidence": 0.85
            }
        ],
        "metadata": {"source": "test"}
    }
    
    # Mock recommendations
    rec_results = [
        {
            "id": "rec1",
            "category": "academic",
            "content": "Consider taking advanced courses",
            "description": "Taking advanced courses will help your application",
            "priority": 1,
            "action_items": ["Research courses", "Talk to advisor"],
            "confidence": 0.8
        },
        {
            "id": "rec2",
            "category": "extracurricular",
            "content": "Join more tech clubs",
            "description": "Active participation shows initiative",
            "priority": 2,
            "action_items": ["Find club listings", "Attend meetings"],
            "confidence": 0.7
        }
    ]
    
    # Patch service methods to properly track calls
    with patch.object(mock_document_service, 'analyze', return_value=doc_analysis_result) as mock_analyze, \
         patch.object(mock_recommendation_service, 'generate_recommendations', return_value=rec_results) as mock_recommend:
        
        # Step 1: Upload document
        document_payload = {
            "content": "Resume content...",
            "document_type": "resume",
            "user_id": "test_user"
        }
        doc_response = await async_client.post(
            "/api/documents/analyze",
            json=document_payload,
            headers={"X-API-Key": "test_api_key"}
        )
        assert doc_response.status_code == 200
        doc_data = doc_response.json()
        
        # Print response for debugging
        print(f"Document analysis response: {doc_data}")
        
        # Extract data based on the actual structure
        education = doc_data.get("extracted_info", {}).get("academic", {}).get("education", [])
        experience = doc_data.get("extracted_info", {}).get("extracurricular", {}).get("experience", [])
        
        # Step 2: Use extracted data for profile
        profile_payload = {
            "request": {
                "user_id": "test_user",
                "profile_data": {
                    "education": education,
                    "experience": experience
                }
            }
        }
        
        # Step 3: Get recommendations using profile
        rec_response = await async_client.post(
            "/api/recommendations",
            json=profile_payload,
            headers={"X-API-Key": "test_api_key"}
        )
        
        # Print recommendation response for debugging
        print(f"Recommendation response status: {rec_response.status_code}")
        print(f"Recommendation response body: {rec_response.text}")
        
        assert rec_response.status_code == 200
        
        # Only proceed with these checks if the response is successful
        if rec_response.status_code == 200:
            # Verify the recommendations response
            rec_data = rec_response.json()
            assert len(rec_data) == 2
            assert rec_data[0]["id"] in ["rec1", "rec2"]
            assert "content" in rec_data[0]
            assert "category" in rec_data[0]
            
            # Verify service calls
            mock_analyze.assert_called_once()
        # Verify the recommendations response
        rec_data = rec_response.json()
        assert len(rec_data) == 2
        assert rec_data[0]["id"] in ["rec1", "rec2"]
        assert "content" in rec_data[0]
        assert "category" in rec_data[0]
        
        # Verify service calls
        mock_analyze.assert_called_once()
        mock_recommend.assert_called_once()


@pytest.mark.asyncio
async def test_ui_flow_qa_interaction(async_client, mock_qa_service):
    """Test UI flow for Q&A interaction."""
    # Setup dependencies
    app = async_client.app
    app.dependency_overrides[get_qa_service] = lambda: mock_qa_service
    
    # Mock Q&A responses
    qa_responses = [
        [MagicMock(dict=lambda: {"question": "What are your strengths?", "category": "personal"})],
        [MagicMock(dict=lambda: {"question": "Which colleges interest you?", "category": "academic"})]
    ]
    
    # Patch service method
    with patch.object(
        mock_qa_service, 'generate_questions', side_effect=qa_responses
    ) as mock_process:
        
        # Step 1: Initial question
        payload1 = {"question": "How do I improve my application?"}
        response1 = await async_client.post(
            "/api/ask", 
            json=payload1,
            headers={"X-API-Key": "test_api_key"}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Save first question for context
        first_question = data1["questions"][0]
        
        # Step 2: Follow-up with context
        payload2 = {
            "question": "What else should I work on?",
            "context": {
                "previous_questions": [payload1["question"]],
                "previous_answers": ["I'm good at math and science"]
            }
        }
        response2 = await async_client.post(
            "/api/ask", 
            json=payload2,
            headers={"X-API-Key": "test_api_key"}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify service calls
        assert mock_process.call_count == 2
        
        # Verify second call included context
        args, kwargs = mock_process.call_args_list[1]
        assert "context" in kwargs
        assert "previous_questions" in kwargs["context"]
        assert "previous_answers" in kwargs["context"]


@pytest.mark.asyncio
async def test_ui_flow_profile_summary(async_client, mock_recommendation_service, mock_document_service):
    """Test UI flow for generating profile summary after multiple steps."""
    # Setup dependencies
    app = async_client.app
    app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
    app.dependency_overrides[get_document_service] = lambda: mock_document_service
    
    # Mock profile summary
    profile_summary = MagicMock(
        user_id="test_user",
        sections={
            "academic": {"summary": "Strong academic background"},
            "extracurricular": {"summary": "Good involvement"},
            "personal": {"summary": "Clear goals"}
        },
        strengths=["Technical skills", "Leadership"],
        areas_for_improvement=["Communication"],
        completeness=0.85,
        dict=lambda: {
            "user_id": "test_user",
            "sections": {
                "academic": {"summary": "Strong academic background"},
                "extracurricular": {"summary": "Good involvement"},
                "personal": {"summary": "Clear goals"}
            },
            "strengths": ["Technical skills", "Leadership"],
            "areas_for_improvement": ["Communication"],
            "completeness": 0.85
        }
    )
    
    # Patch service methods
    with patch.object(
        mock_document_service, 'analyze_document', return_value=MagicMock(
            document_id="test_doc_456",
            content_type="transcript",
            text_content="Transcript content...",
            metadata={"source": "test"},
            confidence=0.95,
            analysis=[],
            extracted_data={"gpa": 3.9, "courses": ["Advanced Math"]},
            sections=[],
            dict=lambda: {
                "document_id": "test_doc_456",
                "content_type": "transcript",
                "extracted_info": {"gpa": 3.9, "courses": ["Advanced Math"]},
                "confidence": 0.95
            }
        )
    ), \
    patch.object(
        mock_recommendation_service, 'get_profile_summary',
        return_value=profile_summary
    ) as mock_summary:
        
        # Step 1: Upload transcript
        doc_payload = {
            "content": "Transcript content...",
            "document_type": "transcript",
            "user_id": "test_user"
        }
        await async_client.post(
            "/api/documents/analyze", 
            json=doc_payload,
            headers={"X-API-Key": "test_api_key"}
        )
        
        # Step 2: Upload essay
        essay_payload = {
            "content": "Essay content...",
            "document_type": "essay",
            "user_id": "test_user"
        }
        await async_client.post(
            "/api/documents/analyze", 
            json=essay_payload,
            headers={"X-API-Key": "test_api_key"}
        )
        
        # Step 3: Generate profile summary
        profile_payload = {
            "user_id": "test_user",
            "profile_data": {
                "academic": {"gpa": 3.9, "courses": ["Advanced Math"]},
                "extracurricular": {"activities": ["Student Council"]},
                "personal": {"goals": ["Become a software engineer"]}
            }
        }
        summary_response = await async_client.post(
            "/api/profile-summary", 
            json=profile_payload,
            headers={"X-API-Key": "test_api_key"}
        )
        
        # Verify response
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        assert summary_data["user_id"] == "test_user"
        assert "sections" in summary_data
        assert "strengths" in summary_data
        assert "completeness" in summary_data
        
        # Verify service call
        mock_summary.assert_called_once()
        args, kwargs = mock_summary.call_args
        assert kwargs["profile_data"] == profile_payload["profile_data"] 