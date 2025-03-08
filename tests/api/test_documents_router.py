"""
Tests for the documents router endpoints.

This module contains tests for the documents router endpoints in the Kevin API.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import fixtures from conftest.py
from .conftest import test_client, mock_documents


def test_get_document_by_id_success(test_client):
    """Test retrieving a document by ID."""
    # Mock get_document at the router level
    with patch('src.api.routers.documents.get_document', autospec=True) as mock_get_doc:
        # Configure the mock response
        document_id = "doc1"
        mock_document = {
            "id": document_id,
            "content": "Test document content 1",
            "metadata": {
                "source": "test_source_1",
                "title": "Test Document 1"
            }
        }
        mock_get_doc.return_value = mock_document
        
        # Make the request
        response = test_client.get(f"/api/documents/get/{document_id}")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == document_id
        assert "metadata" in data
        assert "content" in data
        
        # Verify the get_document was called with the correct ID
        mock_get_doc.assert_called_once_with(document_id)


def test_get_document_by_id_without_content(test_client):
    """Test retrieving a document by ID without content."""
    # Mock get_document at the router level
    with patch('src.api.routers.documents.get_document', autospec=True) as mock_get_doc:
        # Configure the mock response
        document_id = "doc1"
        mock_document = {
            "id": document_id,
            "content": "Test document content 1",
            "metadata": {
                "source": "test_source_1",
                "title": "Test Document 1"
            }
        }
        mock_get_doc.return_value = mock_document
        
        # Make the request
        response = test_client.get(f"/api/documents/get/{document_id}?include_content=false")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == document_id
        assert "metadata" in data
        assert "content" not in data


def test_get_document_by_id_not_found(test_client):
    """Test retrieving a non-existent document by ID."""
    # Configure the mock to raise a ValueError (document not found)
    with patch('src.api.routers.documents.get_document', autospec=True) as mock_get_doc:
        mock_get_doc.side_effect = ValueError("Document not found")
        
        # Make the request
        document_id = "non-existent-id"
        response = test_client.get(f"/api/documents/get/{document_id}")
        
        # Check response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


def test_get_document_by_id_error(test_client):
    """Test handling of errors when retrieving a document by ID."""
    # Configure the mock to raise an exception
    with patch('src.api.routers.documents.get_document', autospec=True) as mock_get_doc:
        mock_get_doc.side_effect = Exception("Test error")
        
        # Make the request
        document_id = "doc1"
        response = test_client.get(f"/api/documents/get/{document_id}")
        
        # Check response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"]


def test_get_document_by_url_success(test_client):
    """Test retrieving a document by URL."""
    # Mock get_document_by_url at the router level
    with patch('src.api.routers.documents.get_document_by_url', autospec=True) as mock_get_doc_url:
        # Configure the mock response
        url = "https://example.com"
        mock_document = {
            "id": "doc2",
            "content": "Test document content 2",
            "metadata": {
                "source": url,
                "title": "Test Document 2"
            }
        }
        mock_get_doc_url.return_value = mock_document
        
        # Make the request
        response = test_client.get(f"/api/documents/url?url={url}")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["url"] == url
        assert "id" in data
        assert "metadata" in data
        assert "content" in data
        
        # Verify the get_document_by_url was called with the correct URL
        mock_get_doc_url.assert_called_once_with(url)


def test_get_document_by_url_without_content(test_client):
    """Test retrieving a document by URL without content."""
    # Mock get_document_by_url at the router level
    with patch('src.api.routers.documents.get_document_by_url', autospec=True) as mock_get_doc_url:
        # Configure the mock response
        url = "https://example.com"
        mock_document = {
            "id": "doc2",
            "content": "Test document content 2",
            "metadata": {
                "source": url,
                "title": "Test Document 2"
            }
        }
        mock_get_doc_url.return_value = mock_document
        
        # Make the request
        response = test_client.get(f"/api/documents/url?url={url}&include_content=false")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["url"] == url
        assert "id" in data
        assert "metadata" in data
        assert "content" not in data


def test_get_document_by_url_not_found(test_client):
    """Test retrieving a non-existent document by URL."""
    # Configure the mock to raise a ValueError (document not found)
    with patch('src.api.routers.documents.get_document_by_url', autospec=True) as mock_get_doc_url:
        mock_get_doc_url.side_effect = ValueError("Document not found")
        
        # Make the request
        url = "https://non-existent-url.com"
        response = test_client.get(f"/api/documents/url?url={url}")
        
        # Check response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


def test_get_document_by_url_error(test_client):
    """Test handling of errors when retrieving a document by URL."""
    # Configure the mock to raise an exception
    with patch('src.api.routers.documents.get_document_by_url', autospec=True) as mock_get_doc_url:
        mock_get_doc_url.side_effect = Exception("Test error")
        
        # Make the request
        url = "https://example.com"
        response = test_client.get(f"/api/documents/url?url={url}")
        
        # Check response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"] 