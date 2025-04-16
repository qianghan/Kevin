"""
Test configuration and fixtures for the Profiler API tests.

This module provides fixtures for FastAPI testing clients and service mocks.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, Generator, AsyncGenerator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import MagicMock, AsyncMock
from httpx._transports.asgi import ASGITransport

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import API and services
from app.backend.api.main import app as api_app
from app.backend.interfaces.qa import IQAService
from app.backend.interfaces.document import IDocumentService
from app.backend.interfaces.recommendation import IRecommendationService
from app.backend.core.deepseek.r1 import DeepSeekR1

# Mock the DeepSeekR1 class
class DeepSeekR1:
    """Mock implementation of DeepSeekR1 for testing."""
    
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or "mock_api_key"
        self.base_url = base_url or "https://mock-api.example.com"
        self.model = model or "mock-model"
        self.max_batch_size = 5
        self.default_max_tokens = 2000
        self.default_temperature = 0.7
        self.timeout = 30
    
    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # Mock response based on endpoint
        if "generate" in endpoint:
            return {
                "outputs": ["This is a mock generated text"],
                "batch_size": 1
            }
        elif "analyze" in endpoint:
            return {
                "outputs": [{"analysis": "This is a mock analysis"}],
                "batch_size": 1
            }
        else:
            return {"outputs": ["Mock response"], "batch_size": 1}
    
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, *args):
        pass


@pytest.fixture
def app():
    """Fixture that provides the FastAPI app instance."""
    # Set test environment variables
    api_app.state.environment = "test"
    api_app.state.api_keys = ["test_api_key"]
    
    # Return configured app
    return api_app


@pytest.fixture
def client(app):
    """Fixture that provides a TestClient instance."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Fixture that provides an AsyncClient instance."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Add the app to the client object so it can be accessed
        client.app = app
        yield client


@pytest.fixture
def mock_qa_service():
    """Fixture that provides a mock IQAService implementation."""
    service = AsyncMock(spec=IQAService)
    
    # Create a question result
    question_result = [
        MagicMock(
            question_id="q1",
            category="academic",
            question_text="What is your GPA?",
            dict=lambda: {
                "question_id": "q1",
                "category": "academic",
                "question": "What is your GPA?",
                "expected_response_type": "number",
                "required": True
            }
        )
    ]
    
    # Set up the async mock
    # For the generate_questions method, we need to ensure it returns an awaitable
    # that resolves to the question_result
    async def mock_generate_questions(*args, **kwargs):
        return question_result
    
    service.generate_questions = mock_generate_questions
    
    # For evaluate_answer
    evaluation_result = MagicMock(
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
    
    async def mock_evaluate_answer(*args, **kwargs):
        return evaluation_result
    
    service.evaluate_answer = mock_evaluate_answer
    
    return service


@pytest.fixture
def mock_document_service():
    """Fixture that provides a mock IDocumentService implementation."""
    service = AsyncMock(spec=IDocumentService)
    
    # Create document analysis result
    doc_result = MagicMock(
        document_id="test_doc_123",
        content_type="transcript",
        text_content="GPA: 3.8",
        metadata={"source": "test"},
        confidence=0.95,
        analysis=[],
        extracted_data={"academic": {"gpa": 3.8}, "extracurricular": {"activities": ["Chess Club"]}},
        extracted_info={"academic": {"gpa": 3.8}, "extracurricular": {"activities": ["Chess Club"]}},
        sections=[],
        dict=lambda: {
            "document_id": "test_doc_123",
            "content_type": "transcript",
            "extracted_info": {
                "academic": {"gpa": 3.8},
                "extracurricular": {"activities": ["Chess Club"]}
            },
            "confidence": 0.95,
            "metadata": {"source": "test"}
        }
    )
    
    # Set up async method implementations
    async def mock_analyze_document(document_content, document_type, user_id, metadata=None):
        # Validate content is not empty
        if not document_content:
            from app.backend.utils.errors import ValidationError
            raise ValidationError("Document content cannot be empty")
        
        # Validate document type
        if document_type not in ["transcript", "essay", "resume", "letter"]:
            from app.backend.utils.errors import ValidationError
            raise ValidationError(f"Invalid document type: {document_type}")
            
        return doc_result
    
    async def mock_analyze(content, document_type, metadata=None):
        # Validate content is not empty
        if not content:
            from app.backend.utils.errors import ValidationError
            raise ValidationError("Document content cannot be empty")
            
        # Validate document type
        if document_type not in ["transcript", "essay", "resume", "letter"]:
            from app.backend.utils.errors import ValidationError
            raise ValidationError(f"Invalid document type: {document_type}")
            
        return {
            "content_type": document_type,
            "extracted_info": {"academic": {"gpa": 3.8}, "extracurricular": {"activities": ["Chess Club"]}},
            "insights": [],
            "confidence": 0.95,
            "metadata": metadata or {"source": "test"}
        }
    
    async def mock_detect_document_type(content):
        from app.backend.services.document_service import DocumentType
        return DocumentType.TRANSCRIPT
    
    async def mock_validate_document_type(doc_type):
        return doc_type in ["transcript", "essay", "resume", "letter"]
    
    async def mock_validate_document_format(*args, **kwargs):
        return True
    
    service.analyze_document = mock_analyze_document
    service.analyze = mock_analyze
    service.detect_document_type = mock_detect_document_type
    service.validate_document_type = mock_validate_document_type
    service.validate_document_format = mock_validate_document_format
    
    return service


@pytest.fixture
def mock_recommendation_service():
    """Fixture that provides a mock IRecommendationService implementation."""
    service = AsyncMock(spec=IRecommendationService)
    
    # Create recommendations result
    recommendations = [
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
    
    # Create profile summary result
    profile_summary = MagicMock(
        strengths=["Strong GPA", "Leadership experience"],
        areas_for_improvement=["More extracurricular activities"],
        unique_selling_points=["Founded a tech startup"],
        overall_quality=0.85,
        dict=lambda: {
            "strengths": ["Strong GPA", "Leadership experience"],
            "areas_for_improvement": ["More extracurricular activities"],
            "unique_selling_points": ["Founded a tech startup"],
            "overall_quality": 0.85,
            "last_updated": "2023-05-15T12:00:00Z"
        }
    )
    
    # Set up async method implementations
    async def mock_generate_recommendations(*args, **kwargs):
        return recommendations
    
    async def mock_get_profile_summary(*args, **kwargs):
        return profile_summary
    
    service.generate_recommendations = mock_generate_recommendations
    service.get_profile_summary = mock_get_profile_summary
    
    return service


# Mock deepseek client
@pytest.fixture
def mock_deepseek_client():
    """Return a mock DeepSeekR1 client instance."""
    return DeepSeekR1()


# Environment setup and teardown
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Save original env vars
    original_env = os.environ.copy()
    
    # Set test env vars
    os.environ["PROFILER_API__API_KEY"] = "test_api_key"
    os.environ["PROFILER_SERVICES__DEEPSEEK__API_KEY"] = "test_deepseek_key"
    
    yield
    
    # Restore original env vars
    os.environ.clear()
    os.environ.update(original_env)


# For asyncio tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_event_loop(event_loop):
    """Set up the event loop for each test."""
    asyncio.set_event_loop(event_loop)
    yield
    # Clean up after test
    await asyncio.sleep(0)  # Allow pending tasks to complete


@pytest.fixture
async def event_loop_instance(event_loop):
    """Ensure each test has a fresh event loop instance."""
    asyncio.set_event_loop(event_loop)
    yield event_loop
    # Clean up any remaining tasks
    pending = asyncio.all_tasks(event_loop)
    for task in pending:
        task.cancel()
    loop.close() 