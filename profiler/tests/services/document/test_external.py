"""
Tests for external storage integration.
"""

import unittest
import io
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import pytest

from profiler.app.backend.services.document.external import (
    ExternalStorageType,
    ExternalDocument,
    ExternalStorageProvider,
    GoogleDriveProvider,
    ExternalStorageService
)
from profiler.app.backend.utils.errors import (
    ValidationError,
    ResourceNotFoundError,
    AuthenticationError,
    IntegrationError
)


class TestExternalDocument(unittest.TestCase):
    """Tests for the ExternalDocument class."""
    
    def test_init(self):
        """Test initializing an external document."""
        doc = ExternalDocument(
            external_id="12345",
            storage_type=ExternalStorageType.GOOGLE_DRIVE,
            name="test.pdf",
            mime_type="application/pdf",
            size=1024,
            web_url="https://drive.google.com/file/d/12345",
            thumbnail_url="https://drive.google.com/thumbnail/12345",
            created_at=datetime(2023, 1, 1),
            modified_at=datetime(2023, 1, 2),
            parent_folder_id="folder1",
            owner_info={"name": "Test User"},
            metadata={"tags": ["important"]}
        )
        
        self.assertEqual(doc.external_id, "12345")
        self.assertEqual(doc.storage_type, ExternalStorageType.GOOGLE_DRIVE)
        self.assertEqual(doc.name, "test.pdf")
        self.assertEqual(doc.mime_type, "application/pdf")
        self.assertEqual(doc.size, 1024)
        self.assertEqual(doc.web_url, "https://drive.google.com/file/d/12345")
        self.assertEqual(doc.thumbnail_url, "https://drive.google.com/thumbnail/12345")
        self.assertEqual(doc.created_at, datetime(2023, 1, 1))
        self.assertEqual(doc.modified_at, datetime(2023, 1, 2))
        self.assertEqual(doc.parent_folder_id, "folder1")
        self.assertEqual(doc.owner_info, {"name": "Test User"})
        self.assertEqual(doc.metadata, {"tags": ["important"]})
    
    def test_to_dict(self):
        """Test converting an external document to a dictionary."""
        doc = ExternalDocument(
            external_id="12345",
            storage_type=ExternalStorageType.GOOGLE_DRIVE,
            name="test.pdf",
            mime_type="application/pdf",
            size=1024,
            web_url="https://drive.google.com/file/d/12345",
            thumbnail_url="https://drive.google.com/thumbnail/12345",
            created_at=datetime(2023, 1, 1),
            modified_at=datetime(2023, 1, 2),
            parent_folder_id="folder1",
            owner_info={"name": "Test User"},
            metadata={"tags": ["important"]}
        )
        
        doc_dict = doc.to_dict()
        
        self.assertEqual(doc_dict["external_id"], "12345")
        self.assertEqual(doc_dict["storage_type"], "google_drive")
        self.assertEqual(doc_dict["name"], "test.pdf")
        self.assertEqual(doc_dict["mime_type"], "application/pdf")
        self.assertEqual(doc_dict["size"], 1024)
        self.assertEqual(doc_dict["web_url"], "https://drive.google.com/file/d/12345")
        self.assertEqual(doc_dict["thumbnail_url"], "https://drive.google.com/thumbnail/12345")
        self.assertEqual(doc_dict["created_at"], "2023-01-01T00:00:00")
        self.assertEqual(doc_dict["modified_at"], "2023-01-02T00:00:00")
        self.assertEqual(doc_dict["parent_folder_id"], "folder1")
        self.assertEqual(doc_dict["owner_info"], {"name": "Test User"})
        self.assertEqual(doc_dict["metadata"], {"tags": ["important"]})
    
    def test_from_dict(self):
        """Test creating an external document from a dictionary."""
        doc_dict = {
            "external_id": "12345",
            "storage_type": "google_drive",
            "name": "test.pdf",
            "mime_type": "application/pdf",
            "size": 1024,
            "web_url": "https://drive.google.com/file/d/12345",
            "thumbnail_url": "https://drive.google.com/thumbnail/12345",
            "created_at": "2023-01-01T00:00:00",
            "modified_at": "2023-01-02T00:00:00",
            "parent_folder_id": "folder1",
            "owner_info": {"name": "Test User"},
            "metadata": {"tags": ["important"]}
        }
        
        doc = ExternalDocument.from_dict(doc_dict)
        
        self.assertEqual(doc.external_id, "12345")
        self.assertEqual(doc.storage_type, ExternalStorageType.GOOGLE_DRIVE)
        self.assertEqual(doc.name, "test.pdf")
        self.assertEqual(doc.mime_type, "application/pdf")
        self.assertEqual(doc.size, 1024)
        self.assertEqual(doc.web_url, "https://drive.google.com/file/d/12345")
        self.assertEqual(doc.thumbnail_url, "https://drive.google.com/thumbnail/12345")
        self.assertEqual(doc.created_at, datetime(2023, 1, 1))
        self.assertEqual(doc.modified_at, datetime(2023, 1, 2))
        self.assertEqual(doc.parent_folder_id, "folder1")
        self.assertEqual(doc.owner_info, {"name": "Test User"})
        self.assertEqual(doc.metadata, {"tags": ["important"]})


@pytest.mark.asyncio
class TestGoogleDriveProvider:
    """Tests for the GoogleDriveProvider class."""
    
    @pytest.fixture
    def provider(self):
        """Fixture for creating a Google Drive provider."""
        config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "redirect_uri": "https://example.com/callback",
            "api_url": "https://www.googleapis.com/drive/v3/",
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scopes": ["https://www.googleapis.com/auth/drive.readonly"]
        }
        return GoogleDriveProvider(config)
    
    async def test_missing_config(self):
        """Test provider with missing config."""
        with pytest.raises(ValidationError):
            GoogleDriveProvider({})
    
    async def test_initialize(self, provider):
        """Test initializing the provider."""
        await provider.initialize()
        assert provider._initialized is True
    
    @patch("aiohttp.ClientSession.post")
    async def test_authenticate_with_code(self, mock_post, provider):
        """Test authenticating with authorization code."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Call authenticate
        result = await provider.authenticate({"code": "test_code"})
        
        # Check result
        assert result["access_token"] == "test_access_token"
        assert result["refresh_token"] == "test_refresh_token"
        assert result["expires_in"] == 3600
        assert result["token_type"] == "Bearer"
        
        # Check provider state
        assert provider._access_token == "test_access_token"
        assert provider._refresh_token == "test_refresh_token"
    
    @patch("aiohttp.ClientSession.post")
    async def test_authenticate_with_refresh_token(self, mock_post, provider):
        """Test authenticating with refresh token."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Call authenticate
        result = await provider.authenticate({"refresh_token": "test_refresh_token"})
        
        # Check result
        assert result["access_token"] == "new_access_token"
        assert result["expires_in"] == 3600
        assert result["token_type"] == "Bearer"
        
        # Check provider state
        assert provider._access_token == "new_access_token"
    
    @patch("aiohttp.ClientSession.post")
    async def test_authenticate_error(self, mock_post, provider):
        """Test authentication error."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Invalid grant"
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Call authenticate
        with pytest.raises(AuthenticationError):
            await provider.authenticate({"code": "test_code"})
    
    @patch("aiohttp.ClientSession.get")
    async def test_list_documents(self, mock_get, provider):
        """Test listing documents."""
        # Set access token
        provider._access_token = "test_access_token"
        provider._token_expiry = datetime.utcnow().timestamp() + 3600
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "files": [
                {
                    "id": "file1",
                    "name": "test.pdf",
                    "mimeType": "application/pdf",
                    "size": "1024",
                    "webViewLink": "https://drive.google.com/file/d/file1",
                    "thumbnailLink": "https://drive.google.com/thumbnail/file1",
                    "createdTime": "2023-01-01T00:00:00Z",
                    "modifiedTime": "2023-01-02T00:00:00Z",
                    "parents": ["folder1"],
                    "owners": [{"displayName": "Test User", "emailAddress": "test@example.com"}],
                    "capabilities": {"canEdit": True}
                }
            ],
            "nextPageToken": "next_page_token"
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Call list_documents
        documents, next_page_token = await provider.list_documents(folder_id="folder1", query="test")
        
        # Check result
        assert len(documents) == 1
        assert documents[0].external_id == "file1"
        assert documents[0].name == "test.pdf"
        assert documents[0].mime_type == "application/pdf"
        assert documents[0].size == 1024
        assert documents[0].web_url == "https://drive.google.com/file/d/file1"
        assert documents[0].thumbnail_url == "https://drive.google.com/thumbnail/file1"
        assert documents[0].created_at == datetime(2023, 1, 1, 0, 0, 0)
        assert documents[0].modified_at == datetime(2023, 1, 2, 0, 0, 0)
        assert documents[0].parent_folder_id == "folder1"
        assert documents[0].owner_info == {"displayName": "Test User", "emailAddress": "test@example.com"}
        assert documents[0].metadata == {"capabilities": {"canEdit": True}}
        assert next_page_token == "next_page_token"
    
    @patch("aiohttp.ClientSession.get")
    async def test_get_document(self, mock_get, provider):
        """Test getting a document."""
        # Set access token
        provider._access_token = "test_access_token"
        provider._token_expiry = datetime.utcnow().timestamp() + 3600
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "id": "file1",
            "name": "test.pdf",
            "mimeType": "application/pdf",
            "size": "1024",
            "webViewLink": "https://drive.google.com/file/d/file1",
            "thumbnailLink": "https://drive.google.com/thumbnail/file1",
            "createdTime": "2023-01-01T00:00:00Z",
            "modifiedTime": "2023-01-02T00:00:00Z",
            "parents": ["folder1"],
            "owners": [{"displayName": "Test User", "emailAddress": "test@example.com"}],
            "capabilities": {"canEdit": True}
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Call get_document
        document = await provider.get_document("file1")
        
        # Check result
        assert document.external_id == "file1"
        assert document.name == "test.pdf"
        assert document.mime_type == "application/pdf"
        assert document.size == 1024
        assert document.web_url == "https://drive.google.com/file/d/file1"
        assert document.thumbnail_url == "https://drive.google.com/thumbnail/file1"
        assert document.created_at == datetime(2023, 1, 1, 0, 0, 0)
        assert document.modified_at == datetime(2023, 1, 2, 0, 0, 0)
        assert document.parent_folder_id == "folder1"
        assert document.owner_info == {"displayName": "Test User", "emailAddress": "test@example.com"}
        assert document.metadata == {"capabilities": {"canEdit": True}}
    
    @patch("aiohttp.ClientSession.get")
    async def test_download_document(self, mock_get, provider):
        """Test downloading a document."""
        # Set access token
        provider._access_token = "test_access_token"
        provider._token_expiry = datetime.utcnow().timestamp() + 3600
        
        # Mock get_document
        provider.get_document = AsyncMock(return_value=ExternalDocument(
            external_id="file1",
            storage_type=ExternalStorageType.GOOGLE_DRIVE,
            name="test.pdf",
            mime_type="application/pdf",
            size=1024,
            web_url="https://drive.google.com/file/d/file1",
            thumbnail_url="https://drive.google.com/thumbnail/file1",
            created_at=datetime(2023, 1, 1),
            modified_at=datetime(2023, 1, 2),
            parent_folder_id="folder1",
            owner_info={"displayName": "Test User", "emailAddress": "test@example.com"},
            metadata={"capabilities": {"canEdit": True}}
        ))
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read.return_value = b"test content"
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Call download_document
        file_obj, filename, size = await provider.download_document("file1")
        
        # Check result
        assert filename == "test.pdf"
        assert size == 12
        assert file_obj.read() == b"test content"


@pytest.mark.asyncio
class TestExternalStorageService:
    """Tests for the ExternalStorageService class."""
    
    @pytest.fixture
    def service(self):
        """Fixture for creating an external storage service."""
        config = {
            "providers": {
                "google_drive": {
                    "type": "google_drive",
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "redirect_uri": "https://example.com/callback"
                }
            }
        }
        return ExternalStorageService(config)
    
    async def test_initialize(self, service):
        """Test initializing the service."""
        with patch.object(GoogleDriveProvider, "initialize", AsyncMock()):
            await service.initialize()
            assert service._initialized is True
            assert ExternalStorageType.GOOGLE_DRIVE in service._providers
    
    async def test_get_provider(self, service):
        """Test getting a provider."""
        # Initialize service
        with patch.object(GoogleDriveProvider, "initialize", AsyncMock()):
            await service.initialize()
        
        # Get provider
        provider = service.get_provider(ExternalStorageType.GOOGLE_DRIVE)
        assert isinstance(provider, GoogleDriveProvider)
    
    async def test_get_provider_not_initialized(self, service):
        """Test getting a provider when not initialized."""
        with pytest.raises(ValidationError):
            service.get_provider(ExternalStorageType.GOOGLE_DRIVE)
    
    async def test_get_provider_not_found(self, service):
        """Test getting a provider that doesn't exist."""
        # Initialize service
        with patch.object(GoogleDriveProvider, "initialize", AsyncMock()):
            await service.initialize()
        
        # Get provider
        with pytest.raises(ValidationError):
            service.get_provider(ExternalStorageType.DROPBOX)
    
    async def test_authenticate(self, service):
        """Test authenticating with a provider."""
        # Initialize service
        with patch.object(GoogleDriveProvider, "initialize", AsyncMock()):
            await service.initialize()
        
        # Mock provider.authenticate
        mock_authenticate = AsyncMock(return_value={"access_token": "test_token"})
        with patch.object(GoogleDriveProvider, "authenticate", mock_authenticate):
            result = await service.authenticate(
                ExternalStorageType.GOOGLE_DRIVE,
                {"code": "test_code"}
            )
            assert result == {"access_token": "test_token"}
            mock_authenticate.assert_called_once_with({"code": "test_code"})
    
    async def test_list_documents(self, service):
        """Test listing documents."""
        # Initialize service
        with patch.object(GoogleDriveProvider, "initialize", AsyncMock()):
            await service.initialize()
        
        # Mock provider.list_documents
        mock_list_documents = AsyncMock(return_value=(["doc1", "doc2"], "next_page"))
        with patch.object(GoogleDriveProvider, "list_documents", mock_list_documents):
            result, next_page = await service.list_documents(
                ExternalStorageType.GOOGLE_DRIVE,
                folder_id="folder1",
                query="test",
                limit=10,
                page_token="page1"
            )
            assert result == ["doc1", "doc2"]
            assert next_page == "next_page"
            mock_list_documents.assert_called_once_with("folder1", "test", 10, "page1")
    
    async def test_get_document(self, service):
        """Test getting a document."""
        # Initialize service
        with patch.object(GoogleDriveProvider, "initialize", AsyncMock()):
            await service.initialize()
        
        # Mock provider.get_document
        mock_doc = ExternalDocument(
            external_id="file1",
            storage_type=ExternalStorageType.GOOGLE_DRIVE,
            name="test.pdf",
            mime_type="application/pdf",
            size=1024,
            web_url="https://drive.google.com/file/d/file1",
            thumbnail_url="https://drive.google.com/thumbnail/file1"
        )
        mock_get_document = AsyncMock(return_value=mock_doc)
        with patch.object(GoogleDriveProvider, "get_document", mock_get_document):
            result = await service.get_document(
                ExternalStorageType.GOOGLE_DRIVE,
                "file1"
            )
            assert result == mock_doc
            mock_get_document.assert_called_once_with("file1")
    
    async def test_download_document(self, service):
        """Test downloading a document."""
        # Initialize service
        with patch.object(GoogleDriveProvider, "initialize", AsyncMock()):
            await service.initialize()
        
        # Mock provider.download_document
        file_obj = io.BytesIO(b"test content")
        mock_download_document = AsyncMock(return_value=(file_obj, "test.pdf", 12))
        with patch.object(GoogleDriveProvider, "download_document", mock_download_document):
            result_file, result_name, result_size = await service.download_document(
                ExternalStorageType.GOOGLE_DRIVE,
                "file1"
            )
            assert result_file == file_obj
            assert result_name == "test.pdf"
            assert result_size == 12
            mock_download_document.assert_called_once_with("file1")
    
    async def test_upload_document(self, service):
        """Test uploading a document."""
        # Initialize service
        with patch.object(GoogleDriveProvider, "initialize", AsyncMock()):
            await service.initialize()
        
        # Mock provider.upload_document
        mock_doc = ExternalDocument(
            external_id="file1",
            storage_type=ExternalStorageType.GOOGLE_DRIVE,
            name="test.pdf",
            mime_type="application/pdf",
            size=1024,
            web_url="https://drive.google.com/file/d/file1",
            thumbnail_url="https://drive.google.com/thumbnail/file1"
        )
        mock_upload_document = AsyncMock(return_value=mock_doc)
        with patch.object(GoogleDriveProvider, "upload_document", mock_upload_document):
            file_obj = io.BytesIO(b"test content")
            result = await service.upload_document(
                ExternalStorageType.GOOGLE_DRIVE,
                file_obj,
                "test.pdf",
                "application/pdf",
                "folder1"
            )
            assert result == mock_doc
            mock_upload_document.assert_called_once_with(
                file_obj, "test.pdf", "application/pdf", "folder1"
            ) 