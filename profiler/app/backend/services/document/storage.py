"""
Document storage implementation.

This module provides functionality for storing and retrieving document files with support
for multiple storage backends.
"""

import os
import shutil
import asyncio
import mimetypes
import tempfile
from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Optional, List, Any, Union, Tuple
from urllib.parse import urlparse

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import StorageError, ValidationError, ConfigurationError
from app.backend.utils.config_manager import ConfigManager
from .validation import DocumentValidator
from .indexing import DocumentIndexingService
from .models import Document

logger = get_logger(__name__)


class DocumentStorageBackend(ABC):
    """Abstract base class for document storage backends."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the storage backend and release resources."""
        pass
    
    @abstractmethod
    async def save_file(self, file_path: str, file_content: BinaryIO, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a file to the storage backend.
        
        Args:
            file_path: Path where the file should be saved
            file_content: File content to save
            metadata: Optional metadata for the file
            
        Returns:
            The path or URL where the file was saved
            
        Raises:
            StorageError: If the file cannot be saved
        """
        pass
    
    @abstractmethod
    async def get_file(self, file_path: str) -> BinaryIO:
        """
        Get a file from the storage backend.
        
        Args:
            file_path: Path of the file to get
            
        Returns:
            File content
            
        Raises:
            StorageError: If the file cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> None:
        """
        Delete a file from the storage backend.
        
        Args:
            file_path: Path of the file to delete
            
        Raises:
            StorageError: If the file cannot be deleted
        """
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in the storage backend.
        
        Args:
            file_path: Path of the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a file in the storage backend.
        
        Args:
            file_path: Path of the file
            
        Returns:
            File metadata
            
        Raises:
            StorageError: If the file metadata cannot be retrieved
        """
        pass


class LocalFileSystemStorage(DocumentStorageBackend):
    """Document storage backend using the local file system."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the local file system storage backend.
        
        Args:
            base_path: Base path for file storage. If not provided, defaults to 'data/documents'.
        """
        self.base_path = base_path or os.path.join(os.getcwd(), 'data', 'documents')
    
    async def initialize(self) -> None:
        """Initialize the storage backend by creating the base directory."""
        try:
            os.makedirs(self.base_path, exist_ok=True)
            logger.info(f"Initialized local file system storage at {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to initialize local file system storage: {str(e)}")
            raise StorageError(f"Failed to initialize storage: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the storage backend (no-op for local file system)."""
        logger.info("Shutdown local file system storage")
    
    async def save_file(self, file_path: str, file_content: BinaryIO, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a file to the local file system.
        
        Args:
            file_path: Relative path where the file should be saved
            file_content: File content to save
            metadata: Optional metadata for the file (ignored for local file system)
            
        Returns:
            The relative path where the file was saved
            
        Raises:
            StorageError: If the file cannot be saved
        """
        try:
            # Ensure the directory exists
            full_path = os.path.join(self.base_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Save the file
            with open(full_path, 'wb') as f:
                shutil.copyfileobj(file_content, f)
            
            logger.debug(f"Saved file to {full_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {str(e)}")
            raise StorageError(f"Failed to save file: {str(e)}")
    
    async def get_file(self, file_path: str) -> BinaryIO:
        """
        Get a file from the local file system.
        
        Args:
            file_path: Relative path of the file to get
            
        Returns:
            File content
            
        Raises:
            StorageError: If the file cannot be retrieved
        """
        try:
            full_path = os.path.join(self.base_path, file_path)
            
            if not os.path.exists(full_path):
                raise StorageError(f"File not found: {file_path}")
            
            return open(full_path, 'rb')
            
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to get file {file_path}: {str(e)}")
            raise StorageError(f"Failed to get file: {str(e)}")
    
    async def delete_file(self, file_path: str) -> None:
        """
        Delete a file from the local file system.
        
        Args:
            file_path: Relative path of the file to delete
            
        Raises:
            StorageError: If the file cannot be deleted
        """
        try:
            full_path = os.path.join(self.base_path, file_path)
            
            if not os.path.exists(full_path):
                logger.warning(f"File not found for deletion: {file_path}")
                return
            
            os.remove(full_path)
            logger.debug(f"Deleted file {full_path}")
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            raise StorageError(f"Failed to delete file: {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in the local file system.
        
        Args:
            file_path: Relative path of the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        full_path = os.path.join(self.base_path, file_path)
        return os.path.exists(full_path) and os.path.isfile(full_path)
    
    async def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a file in the local file system.
        
        Args:
            file_path: Relative path of the file
            
        Returns:
            File metadata
            
        Raises:
            StorageError: If the file metadata cannot be retrieved
        """
        try:
            full_path = os.path.join(self.base_path, file_path)
            
            if not os.path.exists(full_path):
                raise StorageError(f"File not found: {file_path}")
            
            stat = os.stat(full_path)
            
            return {
                "path": file_path,
                "size": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "accessed_at": stat.st_atime
            }
            
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to get file metadata for {file_path}: {str(e)}")
            raise StorageError(f"Failed to get file metadata: {str(e)}")


class S3Storage(DocumentStorageBackend):
    """Document storage backend using Amazon S3 or compatible services."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the S3 storage backend.
        
        Args:
            config: Configuration for S3 storage
        """
        self.config = config
        self.bucket = config.get("bucket")
        self.client = None
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the S3 client."""
        try:
            # Import boto3 here to make it an optional dependency
            import boto3
            from botocore.exceptions import NoCredentialsError, ClientError
            
            if not self.bucket:
                raise ConfigurationError("S3 bucket name not specified")
            
            # Create S3 client
            self.client = boto3.client(
                's3',
                region_name=self.config.get("region"),
                aws_access_key_id=self.config.get("access_key"),
                aws_secret_access_key=self.config.get("secret_key"),
                endpoint_url=self.config.get("endpoint_url")
            )
            
            # Check if bucket exists and is accessible
            try:
                self.client.head_bucket(Bucket=self.bucket)
            except (NoCredentialsError, ClientError) as e:
                error_code = getattr(e, 'response', {}).get('Error', {}).get('Code')
                if error_code == '404':
                    raise ConfigurationError(f"S3 bucket '{self.bucket}' not found")
                elif error_code == '403':
                    raise ConfigurationError(f"Access denied to S3 bucket '{self.bucket}'")
                else:
                    raise ConfigurationError(f"Error accessing S3 bucket '{self.bucket}': {str(e)}")
            
            self.initialized = True
            logger.info(f"Initialized S3 storage with bucket {self.bucket}")
            
        except ImportError:
            logger.error("Failed to import boto3. Please install it with 'pip install boto3'")
            raise ConfigurationError("boto3 package is required for S3 storage")
        except Exception as e:
            logger.error(f"Failed to initialize S3 storage: {str(e)}")
            raise StorageError(f"Failed to initialize S3 storage: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the S3 client (no-op for boto3)."""
        self.initialized = False
        self.client = None
        logger.info("Shutdown S3 storage")
    
    async def save_file(self, file_path: str, file_content: BinaryIO, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a file to S3.
        
        Args:
            file_path: Path where the file should be saved
            file_content: File content to save
            metadata: Optional metadata for the file
            
        Returns:
            The path where the file was saved
            
        Raises:
            StorageError: If the file cannot be saved
        """
        if not self.initialized or not self.client:
            await self.initialize()
        
        try:
            # Ensure the file path doesn't start with a slash
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            # Use a runner to run blocking S3 operations in a thread pool
            def _upload():
                extra_args = {}
                
                # Set content type if not in metadata
                content_type = None
                if metadata and 'content_type' in metadata:
                    content_type = metadata['content_type']
                else:
                    content_type, _ = mimetypes.guess_type(file_path)
                
                if content_type:
                    extra_args['ContentType'] = content_type
                
                # Convert metadata to S3 format if provided
                if metadata:
                    s3_metadata = {}
                    for key, value in metadata.items():
                        if key != 'content_type':
                            # S3 metadata keys must be strings
                            s3_metadata[key] = str(value)
                    
                    if s3_metadata:
                        extra_args['Metadata'] = s3_metadata
                
                self.client.upload_fileobj(
                    file_content,
                    self.bucket,
                    file_path,
                    ExtraArgs=extra_args
                )
            
            # Run in a thread pool
            await asyncio.get_event_loop().run_in_executor(None, _upload)
            
            logger.debug(f"Saved file to S3 bucket {self.bucket}, path: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save file to S3 {file_path}: {str(e)}")
            raise StorageError(f"Failed to save file to S3: {str(e)}")
    
    async def get_file(self, file_path: str) -> BinaryIO:
        """
        Get a file from S3.
        
        Args:
            file_path: Path of the file to get
            
        Returns:
            File content
            
        Raises:
            StorageError: If the file cannot be retrieved
        """
        if not self.initialized or not self.client:
            await self.initialize()
        
        try:
            # Ensure the file path doesn't start with a slash
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            # Create a temporary file to store the S3 object
            temp_file = tempfile.TemporaryFile()
            
            # Use a runner to run blocking S3 operations in a thread pool
            def _download():
                self.client.download_fileobj(
                    self.bucket,
                    file_path,
                    temp_file
                )
                
                # Reset file pointer to beginning of file
                temp_file.seek(0)
            
            # Run in a thread pool
            await asyncio.get_event_loop().run_in_executor(None, _download)
            
            return temp_file
            
        except Exception as e:
            logger.error(f"Failed to get file from S3 {file_path}: {str(e)}")
            raise StorageError(f"Failed to get file from S3: {str(e)}")
    
    async def delete_file(self, file_path: str) -> None:
        """
        Delete a file from S3.
        
        Args:
            file_path: Path of the file to delete
            
        Raises:
            StorageError: If the file cannot be deleted
        """
        if not self.initialized or not self.client:
            await self.initialize()
        
        try:
            # Ensure the file path doesn't start with a slash
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            # Use a runner to run blocking S3 operations in a thread pool
            def _delete():
                self.client.delete_object(
                    Bucket=self.bucket,
                    Key=file_path
                )
            
            # Run in a thread pool
            await asyncio.get_event_loop().run_in_executor(None, _delete)
            
            logger.debug(f"Deleted file from S3 bucket {self.bucket}, path: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to delete file from S3 {file_path}: {str(e)}")
            raise StorageError(f"Failed to delete file from S3: {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            file_path: Path of the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        if not self.initialized or not self.client:
            await self.initialize()
        
        try:
            # Ensure the file path doesn't start with a slash
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            # Use a runner to run blocking S3 operations in a thread pool
            def _exists():
                try:
                    self.client.head_object(
                        Bucket=self.bucket,
                        Key=file_path
                    )
                    return True
                except Exception:
                    return False
            
            # Run in a thread pool
            return await asyncio.get_event_loop().run_in_executor(None, _exists)
            
        except Exception as e:
            logger.error(f"Failed to check if file exists in S3 {file_path}: {str(e)}")
            return False
    
    async def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a file in S3.
        
        Args:
            file_path: Path of the file
            
        Returns:
            File metadata
            
        Raises:
            StorageError: If the file metadata cannot be retrieved
        """
        if not self.initialized or not self.client:
            await self.initialize()
        
        try:
            # Ensure the file path doesn't start with a slash
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            # Use a runner to run blocking S3 operations in a thread pool
            def _get_metadata():
                response = self.client.head_object(
                    Bucket=self.bucket,
                    Key=file_path
                )
                
                metadata = {
                    "path": file_path,
                    "size": response.get('ContentLength', 0),
                    "content_type": response.get('ContentType', ''),
                    "last_modified": response.get('LastModified', '').isoformat() if response.get('LastModified') else None,
                    "etag": response.get('ETag', '').strip('"')
                }
                
                # Add S3 metadata
                if 'Metadata' in response:
                    for key, value in response['Metadata'].items():
                        metadata[key] = value
                
                return metadata
            
            # Run in a thread pool
            return await asyncio.get_event_loop().run_in_executor(None, _get_metadata)
            
        except Exception as e:
            logger.error(f"Failed to get file metadata from S3 {file_path}: {str(e)}")
            raise StorageError(f"Failed to get file metadata from S3: {str(e)}")


class DocumentStorageService:
    """Service for managing document storage across different backends."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, indexing_service: Optional[DocumentIndexingService] = None):
        """
        Initialize the document storage service.
        
        Args:
            config: Optional configuration for storage backends
            indexing_service: Optional service for document content indexing
        """
        self.config = config or {}
        self.storage_backend: Optional[DocumentStorageBackend] = None
        self.indexing_service = indexing_service
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the document storage service."""
        if self._initialized:
            logger.info("Document storage service already initialized")
            return
        
        try:
            # Get storage backend configuration
            storage_type = self.config.get("type", "local")
            
            if storage_type == "local":
                base_path = self.config.get("local", {}).get("base_path")
                self.storage_backend = LocalFileSystemStorage(base_path)
            elif storage_type == "s3":
                s3_config = self.config.get("s3", {})
                self.storage_backend = S3Storage(s3_config)
            else:
                raise ConfigurationError(f"Unsupported storage backend type: {storage_type}")
            
            await self.storage_backend.initialize()
            
            # Initialize indexing service if provided
            if self.indexing_service:
                await self.indexing_service.initialize()
            
            self._initialized = True
            logger.info(f"Initialized document storage service with {storage_type} backend")
            
        except Exception as e:
            logger.error(f"Failed to initialize document storage service: {str(e)}")
            raise StorageError(f"Failed to initialize document storage: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the document storage service."""
        if self.storage_backend:
            await self.storage_backend.shutdown()
            self.storage_backend = None
        
        # Shutdown indexing service if provided
        if self.indexing_service:
            await self.indexing_service.shutdown()
            
        self._initialized = False
        logger.info("Shutdown document storage service")
    
    async def save_document(self, 
                          file_path: str, 
                          file_content: BinaryIO, 
                          filename: str,
                          file_size: Optional[int] = None,
                          mime_type: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          document: Optional[Document] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Save a document file.
        
        Args:
            file_path: Path where the file should be saved
            file_content: File content to save
            filename: Original filename
            file_size: Size of the file in bytes
            mime_type: MIME type of the file
            metadata: Optional metadata for the file
            document: Optional document object for indexing
            
        Returns:
            Tuple of (storage_path, file_metadata)
            
        Raises:
            StorageError: If the file cannot be saved
            ValidationError: If the file validation fails
        """
        if not self._initialized or not self.storage_backend:
            await self.initialize()
        
        try:
            # Validate file if size and mime_type are provided
            if file_size is not None and mime_type is not None:
                is_valid, errors = DocumentValidator.validate_document_file(
                    filename=filename,
                    file_size=file_size,
                    mime_type=mime_type
                )
                
                if not is_valid:
                    raise ValidationError(f"Document validation failed: {', '.join(errors)}")
            
            # Prepare storage metadata
            storage_metadata = {
                "filename": filename
            }
            
            if mime_type:
                storage_metadata["content_type"] = mime_type
            
            # Add custom metadata if provided
            if metadata:
                storage_metadata.update(metadata)
            
            # Save the file
            storage_path = await self.storage_backend.save_file(
                file_path=file_path,
                file_content=file_content,
                metadata=storage_metadata
            )
            
            # Get file metadata
            file_metadata = await self.storage_backend.get_file_metadata(storage_path)
            
            # Index document if indexing service is provided and document object is available
            if self.indexing_service and document:
                try:
                    # Rewind file content for indexing
                    file_content.seek(0)
                    
                    # Index document content
                    await self.indexing_service.index_document(document, file_content)
                except Exception as e:
                    logger.warning(f"Failed to index document content: {str(e)}")
                    # Don't fail the document save operation if indexing fails
            
            return storage_path, file_metadata
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to save document: {str(e)}")
            raise StorageError(f"Failed to save document: {str(e)}")
    
    async def get_document(self, file_path: str) -> BinaryIO:
        """
        Get a document file.
        
        Args:
            file_path: Path of the file to get
            
        Returns:
            File content
            
        Raises:
            StorageError: If the file cannot be retrieved
        """
        if not self._initialized or not self.storage_backend:
            await self.initialize()
        
        try:
            return await self.storage_backend.get_file(file_path)
            
        except Exception as e:
            logger.error(f"Failed to get document {file_path}: {str(e)}")
            raise StorageError(f"Failed to get document: {str(e)}")
    
    async def delete_document(self, file_path: str) -> None:
        """
        Delete a document file.
        
        Args:
            file_path: Path of the file to delete
            
        Raises:
            StorageError: If the file cannot be deleted
        """
        if not self._initialized or not self.storage_backend:
            await self.initialize()
        
        try:
            await self.storage_backend.delete_file(file_path)
            
        except Exception as e:
            logger.error(f"Failed to delete document {file_path}: {str(e)}")
            raise StorageError(f"Failed to delete document: {str(e)}")
    
    async def document_exists(self, file_path: str) -> bool:
        """
        Check if a document file exists.
        
        Args:
            file_path: Path of the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        if not self._initialized or not self.storage_backend:
            await self.initialize()
        
        try:
            return await self.storage_backend.file_exists(file_path)
            
        except Exception as e:
            logger.error(f"Failed to check if document exists {file_path}: {str(e)}")
            return False 