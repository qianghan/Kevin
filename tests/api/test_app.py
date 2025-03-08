"""
Tests for the main app endpoints.

This module contains tests for the main app endpoints in the Kevin API.
"""

import pytest

# Import fixtures from conftest.py
from .conftest import test_client


def test_root_endpoint(test_client):
    """Test the root endpoint."""
    # Make the request
    response = test_client.get("/")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "Kevin API" in data["name"]
    assert "version" in data
    assert "description" in data
    assert "docs_url" in data
    assert "/docs" in data["docs_url"]


def test_health_check(test_client):
    """Test the health check endpoint."""
    # Make the request
    response = test_client.get("/api/health")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert isinstance(data["timestamp"], (int, float))


def test_middleware_adds_timing_header(test_client):
    """Test that the middleware adds a timing header."""
    # Make the request
    response = test_client.get("/api/health")
    
    # Check for timing header
    assert "x-process-time" in response.headers
    # Timing should be a float value
    timing = float(response.headers["x-process-time"])
    assert timing >= 0


def test_nonexistent_endpoint(test_client):
    """Test a request to a non-existent endpoint."""
    # Make the request to a non-existent endpoint
    response = test_client.get("/api/nonexistent")
    
    # Check response
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Not Found" in data["detail"]


def test_method_not_allowed(test_client):
    """Test a request with a method that is not allowed."""
    # Make a POST request to the health check endpoint, which only allows GET
    response = test_client.post("/api/health")
    
    # Check response
    assert response.status_code == 405
    data = response.json()
    assert "detail" in data
    assert "Method Not Allowed" in data["detail"] 