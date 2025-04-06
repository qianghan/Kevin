"""
Basic unittest for API health endpoint.

This test uses unittest instead of pytest to avoid conftest import issues.
"""

import unittest
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestHealthEndpoint(unittest.TestCase):
    """Test the API health endpoint."""
    
    def setUp(self):
        """Set up the test app and client."""
        # Import the health router
        from app.backend.api.health import router
        
        # Create a test FastAPI app with just the health router
        self.app = FastAPI()
        self.app.include_router(router)
        self.app.state.api_keys = ["test_api_key"]
        
        # Create a test client
        self.client = TestClient(self.app)
    
    def test_health_with_valid_key(self):
        """Test that the health endpoint returns 200 with a valid API key."""
        response = self.client.get("/api/health", headers={"X-API-Key": "test_api_key"})
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response content
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("timestamp", data)
        self.assertIn("version", data)
        self.assertIn("api", data)
    
    def test_health_without_key(self):
        """Test that the health endpoint returns 401 without an API key."""
        response = self.client.get("/api/health")
        
        # Check status code
        self.assertEqual(response.status_code, 401)
        
        # Check error message
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("api key", data["detail"].lower())


if __name__ == "__main__":
    unittest.main() 