"""
Test for the API health endpoint.

This test verifies that the health endpoint works correctly.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI


def test_health_endpoint():
    """Test that the health endpoint returns a valid response."""
    from app.backend.api.health import router
    
    # Create a test FastAPI app with just the health router
    app = FastAPI()
    app.include_router(router)
    app.state.api_keys = ["test_api_key"]
    
    # Create a test client
    client = TestClient(app)
    
    # Make request with valid API key
    response = client.get("/api/health", headers={"X-API-Key": "test_api_key"})
    
    # Check status code and response structure
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data
    assert "api" in data


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 