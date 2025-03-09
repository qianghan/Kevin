"""
Tests for the admin router endpoints.

This module contains tests for the admin router endpoints in the Kevin API.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import fixtures from conftest.py
from .conftest import test_client, mock_admin


def test_admin_rebuild_index(test_client):
    """Test the rebuild index admin action."""
    # Mock rebuild_index at the router level
    with patch('src.api.routers.admin.rebuild_index', autospec=True) as mock_rebuild:
        # Configure the mock with the exact expected message format
        mock_rebuild.return_value = {
            "message": "Index rebuilt successfully",
            "details": {
                "duration_seconds": 0.5
            }
        }
        
        # Define the request data
        request_data = {
            "action": "rebuild_index",
            "parameters": None
        }
        
        # Make the request
        response = test_client.post("/api/admin", json=request_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "message" in data
        assert "Index rebuilt" in data["message"]
        assert "details" in data
        assert "duration_seconds" in data
        
        # Verify the rebuild_index was called
        mock_rebuild.assert_called_once()


def test_admin_clear_caches(test_client):
    """Test the clear caches admin action."""
    # Mock clear_caches at the router level
    with patch('src.api.routers.admin.clear_caches', autospec=True) as mock_clear:
        # Configure the mock with the exact expected message format
        mock_clear.return_value = {
            "message": "Caches cleared successfully",
            "details": {
                "documents_cleared": 5,
                "agent_cache_cleared": True
            }
        }
        
        # Define the request data
        request_data = {
            "action": "clear_caches",
            "parameters": None
        }
        
        # Make the request
        response = test_client.post("/api/admin", json=request_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "message" in data
        assert "Caches cleared" in data["message"]
        assert "details" in data
        assert "documents_cleared" in data["details"]
        assert "agent_cache_cleared" in data["details"]
        assert "duration_seconds" in data
        
        # Verify the clear_caches was called
        mock_clear.assert_called_once()


def test_admin_get_system_status(test_client):
    """Test the get system status admin action."""
    # Mock get_system_status at the router level
    with patch('src.api.routers.admin.get_system_status', autospec=True) as mock_status:
        # Configure the mock with the exact expected message format
        mock_status.return_value = {
            "message": "System status retrieved",
            "details": {
                "cpu_usage": 10.5,
                "memory_usage": 50.2,
                "disk_usage": 30.8,
                "python_version": "3.9.0",
                "system": "darwin"
            }
        }
        
        # Define the request data
        request_data = {
            "action": "get_system_status",
            "parameters": None
        }
        
        # Make the request
        response = test_client.post("/api/admin", json=request_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "message" in data
        assert "System status" in data["message"]
        assert "details" in data
        assert "cpu_usage" in data["details"]
        assert "memory_usage" in data["details"]
        assert "disk_usage" in data["details"]
        assert "python_version" in data["details"]
        assert "system" in data["details"]
        assert "duration_seconds" in data
        
        # Verify the get_system_status was called
        mock_status.assert_called_once()


def test_admin_invalid_action(test_client, mock_admin):
    """Test an invalid admin action."""
    # Define the request data
    request_data = {
        "action": "invalid_action",
        "parameters": None
    }
    
    # Make the request
    response = test_client.post("/api/admin", json=request_data)
    
    # Check response
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # The validation error is a list
    assert isinstance(data["detail"], list)
    # Check the first error
    error = data["detail"][0]
    assert "loc" in error
    assert "msg" in error
    # The location should be ['body', 'action']
    assert error["loc"][0] == "body"
    assert error["loc"][1] == "action"


def test_admin_action_error(test_client):
    """Test handling of errors in admin actions."""
    # Mock rebuild_index at the router level to raise an exception
    with patch('src.api.routers.admin.rebuild_index', autospec=True) as mock_rebuild:
        # Set the side effect to raise an exception
        mock_rebuild.side_effect = Exception("Test error")
        
        # Define the request data
        request_data = {
            "action": "rebuild_index",
            "parameters": None
        }
        
        # Make the request
        response = test_client.post("/api/admin", json=request_data)
        
        # Check response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"] 