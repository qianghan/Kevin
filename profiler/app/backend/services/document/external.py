"""
External document storage integration.

This module provides functionality for integrating with external document storage
services like Google Drive, Dropbox, and OneDrive.
"""

import os
import io
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple, Union, BinaryIO
from enum import Enum
from datetime import datetime
import base64
from pathlib import Path
import aiohttp
from urllib.parse import urljoin, quote

from ...utils.logging import get_logger
from ...utils.errors import (
    ValidationError, 
    ResourceNotFoundError, 
    AuthenticationError, 
    IntegrationError
)

logger = get_logger(__name__)


class ExternalStorageType(Enum):
    """Types of external storage services."""
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"
    BOX = "box"
    CUSTOM = "custom"


class ExternalDocument:
    """Represents a document stored in an external storage service."""
    
    def __init__(self,
                 external_id: str,
                 storage_type: ExternalStorageType,
                 name: str,
                 mime_type: str,
                 size: int,
                 web_url: Optional[str] = None,
                 thumbnail_url: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 modified_at: Optional[datetime] = None,
                 parent_folder_id: Optional[str] = None,
                 owner_info: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an external document.
        
        Args:
            external_id: ID of the document in the external service
            storage_type: Type of external storage service
            name: Name of the document
            mime_type: MIME type of the document
            size: Size of the document in bytes
            web_url: URL to view the document in the browser
            thumbnail_url: URL to a thumbnail image of the document
            created_at: When the document was created
            modified_at: When the document was last modified
            parent_folder_id: ID of the parent folder in the external service
            owner_info: Information about the document owner
            metadata: Additional metadata about the document
        """
        self.external_id = external_id
        self.storage_type = storage_type
        self.name = name
        self.mime_type = mime_type
        self.size = size
        self.web_url = web_url
        self.thumbnail_url = thumbnail_url
        self.created_at = created_at or datetime.utcnow()
        self.modified_at = modified_at or self.created_at
        self.parent_folder_id = parent_folder_id
        self.owner_info = owner_info or {}
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert external document to dictionary for serialization."""
        return {
            "external_id": self.external_id,
            "storage_type": self.storage_type.value,
            "name": self.name,
            "mime_type": self.mime_type,
            "size": self.size,
            "web_url": self.web_url,
            "thumbnail_url": self.thumbnail_url,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "parent_folder_id": self.parent_folder_id,
            "owner_info": self.owner_info,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExternalDocument':
        """Create an external document from a dictionary."""
        storage_type = ExternalStorageType(data.get("storage_type"))
        created_at = datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else None
        modified_at = datetime.fromisoformat(data.get("modified_at")) if data.get("modified_at") else None
        
        return cls(
            external_id=data.get("external_id"),
            storage_type=storage_type,
            name=data.get("name", ""),
            mime_type=data.get("mime_type", ""),
            size=data.get("size", 0),
            web_url=data.get("web_url"),
            thumbnail_url=data.get("thumbnail_url"),
            created_at=created_at,
            modified_at=modified_at,
            parent_folder_id=data.get("parent_folder_id"),
            owner_info=data.get("owner_info", {}),
            metadata=data.get("metadata", {})
        )


class ExternalStorageProvider:
    """Base class for external storage providers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize external storage provider.
        
        Args:
            config: Configuration for the provider
        """
        self.config = config or {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the external storage provider."""
        self._initialized = True
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate with the external service.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            Authentication response with tokens
            
        Raises:
            AuthenticationError: If authentication fails
        """
        raise NotImplementedError("Subclasses must implement authenticate method")
    
    async def list_documents(self, 
                         folder_id: Optional[str] = None,
                         query: Optional[str] = None,
                         limit: int = 50,
                         page_token: Optional[str] = None) -> Tuple[List[ExternalDocument], Optional[str]]:
        """
        List documents in the external service.
        
        Args:
            folder_id: Optional folder ID to list documents from
            query: Optional search query
            limit: Maximum number of documents to return
            page_token: Optional token for pagination
            
        Returns:
            Tuple of (list of documents, next page token)
            
        Raises:
            IntegrationError: If listing documents fails
        """
        raise NotImplementedError("Subclasses must implement list_documents method")
    
    async def get_document(self, document_id: str) -> ExternalDocument:
        """
        Get a document from the external service.
        
        Args:
            document_id: ID of the document to get
            
        Returns:
            External document
            
        Raises:
            ResourceNotFoundError: If document is not found
            IntegrationError: If getting document fails
        """
        raise NotImplementedError("Subclasses must implement get_document method")
    
    async def download_document(self, document_id: str) -> Tuple[BinaryIO, str, int]:
        """
        Download a document from the external service.
        
        Args:
            document_id: ID of the document to download
            
        Returns:
            Tuple of (file content, filename, file size)
            
        Raises:
            ResourceNotFoundError: If document is not found
            IntegrationError: If downloading document fails
        """
        raise NotImplementedError("Subclasses must implement download_document method")
    
    async def upload_document(self, 
                          file_content: BinaryIO, 
                          filename: str,
                          mime_type: str,
                          folder_id: Optional[str] = None) -> ExternalDocument:
        """
        Upload a document to the external service.
        
        Args:
            file_content: Content of the file to upload
            filename: Name of the file
            mime_type: MIME type of the file
            folder_id: Optional folder ID to upload to
            
        Returns:
            Uploaded external document
            
        Raises:
            IntegrationError: If uploading document fails
        """
        raise NotImplementedError("Subclasses must implement upload_document method")


class GoogleDriveProvider(ExternalStorageProvider):
    """Provider for Google Drive integration."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Google Drive provider.
        
        Config options:
            client_id: Google API client ID
            client_secret: Google API client secret
            redirect_uri: OAuth redirect URI
            api_key: Google API key (optional)
            scopes: OAuth scopes (default: drive.readonly)
        """
        super().__init__(config)
        
        # Set defaults
        self.config.setdefault("api_url", "https://www.googleapis.com/drive/v3/")
        self.config.setdefault("auth_url", "https://accounts.google.com/o/oauth2/v2/auth")
        self.config.setdefault("token_url", "https://oauth2.googleapis.com/token")
        self.config.setdefault("scopes", ["https://www.googleapis.com/auth/drive.readonly"])
        
        # Validate required config
        required_keys = ["client_id", "client_secret", "redirect_uri"]
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            raise ValidationError(f"Missing required configuration: {', '.join(missing_keys)}")
        
        # Auth state
        self._access_token = None
        self._refresh_token = None
        self._token_expiry = None
    
    async def initialize(self) -> None:
        """Initialize the Google Drive provider."""
        await super().initialize()
        
        # Nothing specific to initialize for Google Drive
        logger.info("Google Drive provider initialized")
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate with Google Drive.
        
        Args:
            credentials: Authentication credentials
                - code: OAuth authorization code
                - refresh_token: OAuth refresh token (for refreshing access)
            
        Returns:
            Authentication response with tokens
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Check if we have a refresh token
            if "refresh_token" in credentials:
                return await self._refresh_access_token(credentials["refresh_token"])
            
            # Otherwise, exchange authorization code for tokens
            if "code" not in credentials:
                raise ValidationError("Authorization code is required")
            
            # Exchange code for tokens
            async with aiohttp.ClientSession() as session:
                token_data = {
                    "code": credentials["code"],
                    "client_id": self.config["client_id"],
                    "client_secret": self.config["client_secret"],
                    "redirect_uri": self.config["redirect_uri"],
                    "grant_type": "authorization_code"
                }
                
                async with session.post(self.config["token_url"], data=token_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Google Drive authentication failed: {error_text}")
                        raise AuthenticationError(f"Google Drive authentication failed: {error_text}")
                    
                    token_response = await response.json()
                    
                    # Store tokens
                    self._access_token = token_response.get("access_token")
                    self._refresh_token = token_response.get("refresh_token")
                    expires_in = token_response.get("expires_in", 3600)
                    self._token_expiry = datetime.utcnow().timestamp() + expires_in
                    
                    return {
                        "access_token": self._access_token,
                        "refresh_token": self._refresh_token,
                        "expires_in": expires_in,
                        "token_type": token_response.get("token_type", "Bearer")
                    }
        
        except aiohttp.ClientError as e:
            logger.error(f"Google Drive authentication error: {str(e)}")
            raise AuthenticationError(f"Google Drive authentication error: {str(e)}")
        except Exception as e:
            logger.error(f"Google Drive authentication error: {str(e)}")
            raise AuthenticationError(f"Google Drive authentication error: {str(e)}")
    
    async def _refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token using a refresh token."""
        try:
            async with aiohttp.ClientSession() as session:
                token_data = {
                    "refresh_token": refresh_token,
                    "client_id": self.config["client_id"],
                    "client_secret": self.config["client_secret"],
                    "grant_type": "refresh_token"
                }
                
                async with session.post(self.config["token_url"], data=token_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Google Drive token refresh failed: {error_text}")
                        raise AuthenticationError(f"Google Drive token refresh failed: {error_text}")
                    
                    token_response = await response.json()
                    
                    # Store tokens
                    self._access_token = token_response.get("access_token")
                    expires_in = token_response.get("expires_in", 3600)
                    self._token_expiry = datetime.utcnow().timestamp() + expires_in
                    
                    # Note: Refresh token might not be included in refresh response
                    if "refresh_token" in token_response:
                        self._refresh_token = token_response["refresh_token"]
                    
                    return {
                        "access_token": self._access_token,
                        "refresh_token": self._refresh_token,
                        "expires_in": expires_in,
                        "token_type": token_response.get("token_type", "Bearer")
                    }
                    
        except Exception as e:
            logger.error(f"Google Drive token refresh error: {str(e)}")
            raise AuthenticationError(f"Google Drive token refresh error: {str(e)}")
    
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid access token."""
        if not self._access_token:
            raise AuthenticationError("Not authenticated with Google Drive")
        
        # Check if token is expired
        if self._token_expiry and datetime.utcnow().timestamp() >= self._token_expiry:
            if not self._refresh_token:
                raise AuthenticationError("Access token expired and no refresh token available")
            
            # Refresh the token
            await self._refresh_access_token(self._refresh_token)
    
    async def list_documents(self, 
                         folder_id: Optional[str] = None,
                         query: Optional[str] = None,
                         limit: int = 50,
                         page_token: Optional[str] = None) -> Tuple[List[ExternalDocument], Optional[str]]:
        """
        List documents in Google Drive.
        
        Args:
            folder_id: Optional folder ID to list documents from
            query: Optional search query
            limit: Maximum number of documents to return
            page_token: Optional token for pagination
            
        Returns:
            Tuple of (list of documents, next page token)
            
        Raises:
            IntegrationError: If listing documents fails
        """
        await self._ensure_authenticated()
        
        try:
            # Build query
            q_parts = ["trashed = false"]
            if folder_id:
                q_parts.append(f"'{folder_id}' in parents")
            if query:
                q_parts.append(f"fullText contains '{query}'")
            
            q = " and ".join(q_parts)
            
            # Build request URL
            params = {
                "q": q,
                "pageSize": min(limit, 100),  # API maximum is 100
                "fields": "nextPageToken,files(id,name,mimeType,size,webViewLink,thumbnailLink,createdTime,modifiedTime,parents,owners,capabilities)",
            }
            
            if page_token:
                params["pageToken"] = page_token
            
            url = urljoin(self.config["api_url"], "files")
            
            # Make request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self._access_token}",
                    "Accept": "application/json"
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Google Drive list documents failed: {error_text}")
                        raise IntegrationError(f"Google Drive list documents failed: {error_text}")
                    
                    response_data = await response.json()
                    
                    # Parse response
                    documents = []
                    for file_data in response_data.get("files", []):
                        try:
                            doc = ExternalDocument(
                                external_id=file_data.get("id"),
                                storage_type=ExternalStorageType.GOOGLE_DRIVE,
                                name=file_data.get("name", ""),
                                mime_type=file_data.get("mimeType", ""),
                                size=int(file_data.get("size", 0)),
                                web_url=file_data.get("webViewLink"),
                                thumbnail_url=file_data.get("thumbnailLink"),
                                created_at=datetime.fromisoformat(file_data.get("createdTime").replace("Z", "+00:00")) if file_data.get("createdTime") else None,
                                modified_at=datetime.fromisoformat(file_data.get("modifiedTime").replace("Z", "+00:00")) if file_data.get("modifiedTime") else None,
                                parent_folder_id=file_data.get("parents", [""])[0] if file_data.get("parents") else None,
                                owner_info=file_data.get("owners", [{}])[0] if file_data.get("owners") else {},
                                metadata={
                                    "capabilities": file_data.get("capabilities", {})
                                }
                            )
                            documents.append(doc)
                        except Exception as e:
                            logger.error(f"Error parsing Google Drive file data: {str(e)}")
                    
                    return documents, response_data.get("nextPageToken")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Google Drive list documents error: {str(e)}")
            raise IntegrationError(f"Google Drive list documents error: {str(e)}")
        except Exception as e:
            logger.error(f"Google Drive list documents error: {str(e)}")
            raise IntegrationError(f"Google Drive list documents error: {str(e)}")
    
    async def get_document(self, document_id: str) -> ExternalDocument:
        """
        Get a document from Google Drive.
        
        Args:
            document_id: ID of the document to get
            
        Returns:
            External document
            
        Raises:
            ResourceNotFoundError: If document is not found
            IntegrationError: If getting document fails
        """
        await self._ensure_authenticated()
        
        try:
            # Build request URL
            url = urljoin(self.config["api_url"], f"files/{document_id}")
            params = {
                "fields": "id,name,mimeType,size,webViewLink,thumbnailLink,createdTime,modifiedTime,parents,owners,capabilities",
            }
            
            # Make request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self._access_token}",
                    "Accept": "application/json"
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 404:
                        raise ResourceNotFoundError(f"Google Drive document {document_id} not found")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Google Drive get document failed: {error_text}")
                        raise IntegrationError(f"Google Drive get document failed: {error_text}")
                    
                    file_data = await response.json()
                    
                    # Parse response
                    return ExternalDocument(
                        external_id=file_data.get("id"),
                        storage_type=ExternalStorageType.GOOGLE_DRIVE,
                        name=file_data.get("name", ""),
                        mime_type=file_data.get("mimeType", ""),
                        size=int(file_data.get("size", 0)),
                        web_url=file_data.get("webViewLink"),
                        thumbnail_url=file_data.get("thumbnailLink"),
                        created_at=datetime.fromisoformat(file_data.get("createdTime").replace("Z", "+00:00")) if file_data.get("createdTime") else None,
                        modified_at=datetime.fromisoformat(file_data.get("modifiedTime").replace("Z", "+00:00")) if file_data.get("modifiedTime") else None,
                        parent_folder_id=file_data.get("parents", [""])[0] if file_data.get("parents") else None,
                        owner_info=file_data.get("owners", [{}])[0] if file_data.get("owners") else {},
                        metadata={
                            "capabilities": file_data.get("capabilities", {})
                        }
                    )
                    
        except ResourceNotFoundError:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Google Drive get document error: {str(e)}")
            raise IntegrationError(f"Google Drive get document error: {str(e)}")
        except Exception as e:
            logger.error(f"Google Drive get document error: {str(e)}")
            raise IntegrationError(f"Google Drive get document error: {str(e)}")
    
    async def download_document(self, document_id: str) -> Tuple[BinaryIO, str, int]:
        """
        Download a document from Google Drive.
        
        Args:
            document_id: ID of the document to download
            
        Returns:
            Tuple of (file content, filename, file size)
            
        Raises:
            ResourceNotFoundError: If document is not found
            IntegrationError: If downloading document fails
        """
        await self._ensure_authenticated()
        
        try:
            # First, get document metadata
            document = await self.get_document(document_id)
            
            # Build download URL
            url = urljoin(self.config["api_url"], f"files/{document_id}")
            params = {
                "alt": "media"
            }
            
            # Make request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self._access_token}"
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 404:
                        raise ResourceNotFoundError(f"Google Drive document {document_id} not found")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Google Drive download document failed: {error_text}")
                        raise IntegrationError(f"Google Drive download document failed: {error_text}")
                    
                    # Read response data
                    content = await response.read()
                    file_obj = io.BytesIO(content)
                    
                    return file_obj, document.name, len(content)
                    
        except ResourceNotFoundError:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Google Drive download document error: {str(e)}")
            raise IntegrationError(f"Google Drive download document error: {str(e)}")
        except Exception as e:
            logger.error(f"Google Drive download document error: {str(e)}")
            raise IntegrationError(f"Google Drive download document error: {str(e)}")
    
    async def upload_document(self, 
                          file_content: BinaryIO, 
                          filename: str,
                          mime_type: str,
                          folder_id: Optional[str] = None) -> ExternalDocument:
        """
        Upload a document to Google Drive.
        
        Args:
            file_content: Content of the file to upload
            filename: Name of the file
            mime_type: MIME type of the file
            folder_id: Optional folder ID to upload to
            
        Returns:
            Uploaded external document
            
        Raises:
            IntegrationError: If uploading document fails
        """
        await self._ensure_authenticated()
        
        try:
            # Build upload URL
            url = urljoin(self.config["api_url"], "files")
            params = {
                "uploadType": "multipart",
                "fields": "id,name,mimeType,size,webViewLink,thumbnailLink,createdTime,modifiedTime,parents,owners"
            }
            
            # Create metadata
            metadata = {
                "name": filename,
                "mimeType": mime_type
            }
            
            if folder_id:
                metadata["parents"] = [folder_id]
            
            # Create multipart request
            boundary = "boundary"
            
            # Start multipart body
            body = io.BytesIO()
            
            # Metadata part
            body.write(f"--{boundary}\r\n".encode())
            body.write(b'Content-Type: application/json; charset=UTF-8\r\n\r\n')
            body.write(json.dumps(metadata).encode())
            body.write(b'\r\n')
            
            # File content part
            body.write(f"--{boundary}\r\n".encode())
            body.write(f"Content-Type: {mime_type}\r\n\r\n".encode())
            
            # Get current position and rewind
            pos = file_content.tell()
            file_content.seek(0)
            
            # Write file content
            body.write(file_content.read())
            
            # Restore position
            file_content.seek(pos)
            
            # End multipart body
            body.write(f"\r\n--{boundary}--".encode())
            
            # Rewind body
            body.seek(0)
            
            # Make request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": f"multipart/related; boundary={boundary}"
                }
                
                async with session.post(url, params=params, headers=headers, data=body) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Google Drive upload document failed: {error_text}")
                        raise IntegrationError(f"Google Drive upload document failed: {error_text}")
                    
                    file_data = await response.json()
                    
                    # Parse response
                    return ExternalDocument(
                        external_id=file_data.get("id"),
                        storage_type=ExternalStorageType.GOOGLE_DRIVE,
                        name=file_data.get("name", ""),
                        mime_type=file_data.get("mimeType", ""),
                        size=int(file_data.get("size", 0)),
                        web_url=file_data.get("webViewLink"),
                        thumbnail_url=file_data.get("thumbnailLink"),
                        created_at=datetime.fromisoformat(file_data.get("createdTime").replace("Z", "+00:00")) if file_data.get("createdTime") else None,
                        modified_at=datetime.fromisoformat(file_data.get("modifiedTime").replace("Z", "+00:00")) if file_data.get("modifiedTime") else None,
                        parent_folder_id=file_data.get("parents", [""])[0] if file_data.get("parents") else None,
                        owner_info=file_data.get("owners", [{}])[0] if file_data.get("owners") else {},
                        metadata={}
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"Google Drive upload document error: {str(e)}")
            raise IntegrationError(f"Google Drive upload document error: {str(e)}")
        except Exception as e:
            logger.error(f"Google Drive upload document error: {str(e)}")
            raise IntegrationError(f"Google Drive upload document error: {str(e)}")


class ExternalStorageService:
    """
    Service for integrating with external document storage services.
    
    This service provides a unified interface for interacting with different
    external storage services like Google Drive, Dropbox, and OneDrive.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the external storage service.
        
        Args:
            config: Configuration for the service
        """
        self.config = config or {}
        self._providers: Dict[ExternalStorageType, ExternalStorageProvider] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the external storage service."""
        if self._initialized:
            return
        
        # Initialize providers based on config
        for provider_name, provider_config in self.config.get("providers", {}).items():
            try:
                provider_type = provider_config.get("type", "").lower()
                
                if provider_type == "google_drive":
                    provider = GoogleDriveProvider(provider_config)
                    self._providers[ExternalStorageType.GOOGLE_DRIVE] = provider
                elif provider_type == "dropbox":
                    # Implement Dropbox provider here
                    pass
                elif provider_type == "onedrive":
                    # Implement OneDrive provider here
                    pass
                else:
                    logger.warning(f"Unknown provider type: {provider_type}")
                    continue
                
                await provider.initialize()
                logger.info(f"Initialized {provider_type} provider as '{provider_name}'")
                
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_name}: {str(e)}")
        
        self._initialized = True
        logger.info(f"External storage service initialized with {len(self._providers)} providers")
    
    def get_provider(self, storage_type: ExternalStorageType) -> ExternalStorageProvider:
        """
        Get a storage provider by type.
        
        Args:
            storage_type: Type of storage provider
            
        Returns:
            Storage provider
            
        Raises:
            ValidationError: If provider is not found
        """
        if not self._initialized:
            raise ValidationError("External storage service not initialized")
        
        if storage_type not in self._providers:
            raise ValidationError(f"Provider for {storage_type.value} not available")
        
        return self._providers[storage_type]
    
    async def authenticate(self, 
                       storage_type: ExternalStorageType,
                       credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate with an external storage service.
        
        Args:
            storage_type: Type of storage service
            credentials: Authentication credentials
            
        Returns:
            Authentication response with tokens
            
        Raises:
            ValidationError: If provider is not found
            AuthenticationError: If authentication fails
        """
        provider = self.get_provider(storage_type)
        return await provider.authenticate(credentials)
    
    async def list_documents(self, 
                         storage_type: ExternalStorageType,
                         folder_id: Optional[str] = None,
                         query: Optional[str] = None,
                         limit: int = 50,
                         page_token: Optional[str] = None) -> Tuple[List[ExternalDocument], Optional[str]]:
        """
        List documents in an external storage service.
        
        Args:
            storage_type: Type of storage service
            folder_id: Optional folder ID to list documents from
            query: Optional search query
            limit: Maximum number of documents to return
            page_token: Optional token for pagination
            
        Returns:
            Tuple of (list of documents, next page token)
            
        Raises:
            ValidationError: If provider is not found
            IntegrationError: If listing documents fails
        """
        provider = self.get_provider(storage_type)
        return await provider.list_documents(folder_id, query, limit, page_token)
    
    async def get_document(self, 
                       storage_type: ExternalStorageType,
                       document_id: str) -> ExternalDocument:
        """
        Get a document from an external storage service.
        
        Args:
            storage_type: Type of storage service
            document_id: ID of the document to get
            
        Returns:
            External document
            
        Raises:
            ValidationError: If provider is not found
            ResourceNotFoundError: If document is not found
            IntegrationError: If getting document fails
        """
        provider = self.get_provider(storage_type)
        return await provider.get_document(document_id)
    
    async def download_document(self, 
                            storage_type: ExternalStorageType,
                            document_id: str) -> Tuple[BinaryIO, str, int]:
        """
        Download a document from an external storage service.
        
        Args:
            storage_type: Type of storage service
            document_id: ID of the document to download
            
        Returns:
            Tuple of (file content, filename, file size)
            
        Raises:
            ValidationError: If provider is not found
            ResourceNotFoundError: If document is not found
            IntegrationError: If downloading document fails
        """
        provider = self.get_provider(storage_type)
        return await provider.download_document(document_id)
    
    async def upload_document(self, 
                         storage_type: ExternalStorageType,
                         file_content: BinaryIO, 
                         filename: str,
                         mime_type: str,
                         folder_id: Optional[str] = None) -> ExternalDocument:
        """
        Upload a document to an external storage service.
        
        Args:
            storage_type: Type of storage service
            file_content: Content of the file to upload
            filename: Name of the file
            mime_type: MIME type of the file
            folder_id: Optional folder ID to upload to
            
        Returns:
            Uploaded external document
            
        Raises:
            ValidationError: If provider is not found
            IntegrationError: If uploading document fails
        """
        provider = self.get_provider(storage_type)
        return await provider.upload_document(file_content, filename, mime_type, folder_id) 