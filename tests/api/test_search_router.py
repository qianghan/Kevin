"""
Tests for the search router endpoints.

This module contains tests for the search router endpoints in the Kevin API.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import fixtures from conftest.py
from .conftest import test_client, mock_search


def test_search_documents_success(test_client):
    """Test a successful document search."""
    # Mock search_documents at the router level
    with patch('src.api.routers.search.search_documents', autospec=True) as mock_search_docs:
        # Configure the mock to return sample documents
        mock_docs = [
            {
                "id": "doc1",
                "content": "Test document content 1",
                "metadata": {
                    "source": "test_source_1",
                    "title": "Test Document 1"
                }
            },
            {
                "id": "doc2",
                "content": "Test document content 2",
                "metadata": {
                    "source": "test_source_2",
                    "title": "Test Document 2"
                }
            }
        ]
        mock_search_docs.return_value = mock_docs
        
        # Make the request
        response = test_client.get("/api/search/documents?query=University")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert data["query"] == "University"
        assert "documents" in data
        assert len(data["documents"]) == 2
        assert "count" in data
        assert data["count"] == 2
        assert "duration_seconds" in data
        
        # Verify that each document has the expected structure
        for doc in data["documents"]:
            assert "id" in doc
            assert "metadata" in doc
            assert "content" in doc
        
        # Verify the search function was called
        mock_search_docs.assert_called_once_with("University", 5)


def test_search_documents_without_content(test_client):
    """Test a document search without including content."""
    # Mock search_documents at the router level
    with patch('src.api.routers.search.search_documents', autospec=True) as mock_search_docs:
        # Configure the mock to return sample documents
        mock_docs = [
            {
                "id": "doc1",
                "content": "Test document content 1",
                "metadata": {
                    "source": "test_source_1",
                    "title": "Test Document 1"
                }
            },
            {
                "id": "doc2",
                "content": "Test document content 2",
                "metadata": {
                    "source": "test_source_2",
                    "title": "Test Document 2"
                }
            }
        ]
        mock_search_docs.return_value = mock_docs
        
        # Make the request
        response = test_client.get("/api/search/documents?query=University&include_content=false")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) == 2
        
        # Verify that each document does not have content
        for doc in data["documents"]:
            assert "id" in doc
            assert "metadata" in doc
            assert "content" not in doc


def test_search_documents_with_limit(test_client):
    """Test a document search with a custom limit."""
    # Mock search_documents at the router level
    with patch('src.api.routers.search.search_documents', autospec=True) as mock_search_docs:
        # Configure the mock to return sample documents
        mock_docs = [
            {
                "id": "doc1",
                "content": "Test document content 1",
                "metadata": {
                    "source": "test_source_1",
                    "title": "Test Document 1"
                }
            }
        ]
        mock_search_docs.return_value = mock_docs
        
        # Make the request
        response = test_client.get("/api/search/documents?query=University&limit=1")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 1
        
        # Verify search_documents was called with the correct limit
        mock_search_docs.assert_called_once_with("University", 1)


def test_search_documents_error(test_client):
    """Test handling of errors in document search."""
    # Mock search_documents at the router level to raise an exception
    with patch('src.api.routers.search.search_documents', autospec=True) as mock_search_docs:
        # Configure the mock to raise an exception
        mock_search_docs.side_effect = Exception("Test error")
        
        # Make the request
        response = test_client.get("/api/search/documents?query=University")
        
        # Check response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"]


def test_search_web_success(test_client):
    """Test a successful web search."""
    # Mock search_web at the router level
    with patch('src.api.routers.search.search_web', autospec=True) as mock_search_web:
        # Configure the mock to return sample web documents
        mock_web_docs = [
            {
                "id": "web1",
                "content": "Test web content 1",
                "metadata": {
                    "source": "test_web_source_1",
                    "title": "Test Web Page 1"
                }
            }
        ]
        mock_search_web.return_value = mock_web_docs
        
        # Make the request
        response = test_client.get("/api/search/web?query=University")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert data["query"] == "University"
        assert "documents" in data
        assert len(data["documents"]) == 1
        assert "count" in data
        assert data["count"] == 1
        assert "duration_seconds" in data
        
        # Verify that the document has the expected structure
        doc = data["documents"][0]
        assert "id" in doc
        assert "content" in doc
        assert "metadata" in doc
        
        # Verify search_web was called with the correct parameters
        mock_search_web.assert_called_once_with("University", 5)


def test_search_web_with_limit(test_client):
    """Test a web search with a custom limit."""
    # Mock search_web at the router level
    with patch('src.api.routers.search.search_web', autospec=True) as mock_search_web:
        # Configure the mock to return sample web documents
        mock_web_docs = [
            {
                "id": "web1",
                "content": "Test web content 1",
                "metadata": {
                    "source": "test_web_source_1",
                    "title": "Test Web Page 1"
                }
            }
        ]
        mock_search_web.return_value = mock_web_docs
        
        # Make the request
        response = test_client.get("/api/search/web?query=University&limit=3")
        
        # Check response
        assert response.status_code == 200
        
        # Verify search_web was called with the correct limit
        mock_search_web.assert_called_once_with("University", 3)


def test_search_web_error(test_client):
    """Test handling of errors in web search."""
    # Mock search_web at the router level to raise an exception
    with patch('src.api.routers.search.search_web', autospec=True) as mock_search_web:
        # Configure the mock to raise an exception
        mock_search_web.side_effect = Exception("Test error")
        
        # Make the request
        response = test_client.get("/api/search/web?query=University")
        
        # Check response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"] 