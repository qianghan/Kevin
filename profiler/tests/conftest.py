"""
Pytest configuration for Student Profiler tests.

This module contains shared fixtures and configuration for testing
the Student Profiler API and services.
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

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import API and services
from profiler.app.backend.api.main import app as fastapi_app
from profiler.app.backend.services.qa_service import QAService
from profiler.app.backend.services.document_service import DocumentService
from profiler.app.backend.services.recommender_service import RecommendationService
from profiler.app.backend.core.deepseek.r1 import DeepSeekR1


# Fixtures for API tests
@pytest.fixture
def app() -> FastAPI:
    """Return FastAPI app instance for testing."""
    # Configure app for testing
    fastapi_app.dependency_overrides = {}
    return fastapi_app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Return a TestClient instance for synchronous API tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Return an AsyncClient instance for asynchronous API tests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Mock service fixtures
@pytest.fixture
def mock_qa_service() -> QAService:
    """Return a mock QAService instance."""
    class MockDeepSeekClient:
        async def generate(self, prompt: str, **kwargs):
            return {
                "text": "This is a mock response from DeepSeek",
                "confidence": 0.95,
                "raw_response": {"outputs": ["This is a mock response from DeepSeek"]}
            }
        
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
    
    # Create a QAService with the mock client
    mock_client = MockDeepSeekClient()
    return QAService(client=mock_client)


@pytest.fixture
def mock_document_service() -> DocumentService:
    """Return a mock DocumentService instance."""
    class MockDeepSeekClient:
        async def analyze(self, text: str, analysis_type: str = "general", **kwargs):
            return {
                "analysis": {
                    "document_type": "transcript",
                    "content_summary": "This is a mock document analysis",
                    "key_points": ["Point 1", "Point 2"],
                    "metadata": {"confidence": 0.9}
                },
                "confidence": 0.9,
                "raw_response": {}
            }
        
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
    
    # Create a DocumentService with the mock client
    mock_client = MockDeepSeekClient()
    return DocumentService(client=mock_client)


@pytest.fixture
def mock_recommendation_service() -> RecommendationService:
    """Return a mock RecommendationService instance."""
    class MockDeepSeekClient:
        async def generate(self, prompt: str, **kwargs):
            return {
                "text": "This is a mock recommendation",
                "confidence": 0.85,
                "raw_response": {}
            }
        
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
    
    # Create a RecommendationService with the mock client
    mock_client = MockDeepSeekClient()
    return RecommendationService(client=mock_client)


# Mock deepseek client
@pytest.fixture
def mock_deepseek_client() -> DeepSeekR1:
    """Return a mock DeepSeekR1 client instance."""
    class MockResponse:
        def __init__(self, data: Dict[str, Any]):
            self.data = data
            
        def json(self):
            return self.data
        
        def raise_for_status(self):
            pass
    
    class MockDeepSeekR1(DeepSeekR1):
        def __init__(self):
            # Skip the actual initialization
            self.api_key = "mock_api_key"
            self.base_url = "https://mock-api.example.com"
            self.model = "mock-model"
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
    
    return MockDeepSeekR1()


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