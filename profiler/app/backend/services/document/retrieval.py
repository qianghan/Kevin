"""
Document retrieval API implementation.

This module provides functionality for retrieving documents and their metadata.
"""

import os
from typing import Dict, List, Any, Optional, Union, BinaryIO, Tuple
from datetime import datetime

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import StorageError, ResourceNotFoundError, ValidationError
from .database.repository import PostgreSQLDocumentRepository
from .storage import DocumentStorageService
from .models import Document, DocumentChunk, DocumentVersion
from .transaction import DocumentTransactionManager
from .indexing import DocumentIndexingService

logger = get_logger(__name__)


class DocumentRetrievalService:
    """Service for retrieving documents and their metadata."""
    
    def __init__(self,
                document_repository: PostgreSQLDocumentRepository,
                storage_service: DocumentStorageService,
                transaction_manager: DocumentTransactionManager,
                indexing_service: Optional[DocumentIndexingService] = None):
        """
        Initialize the document retrieval service.
        
        Args:
            document_repository: Repository for document operations
            storage_service: Service for document storage operations
            transaction_manager: Manager for document transactions
            indexing_service: Optional service for document content indexing
        """
        self.document_repository = document_repository
        self.storage_service = storage_service
        self.transaction_manager = transaction_manager
        self.indexing_service = indexing_service or DocumentIndexingService()
    
    async def initialize(self) -> None:
        """Initialize the document retrieval service."""
        if self.indexing_service:
            await self.indexing_service.initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the document retrieval service."""
        if self.indexing_service:
            await self.indexing_service.shutdown()
    
    async def get_document_by_id(self, document_id: str) -> Document:
        """
        Get a document by ID.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            The document
            
        Raises:
            ResourceNotFoundError: If the document does not exist
        """
        try:
            return await self.document_repository.get_document(document_id)
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            raise ResourceNotFoundError(f"Document not found: {document_id}")
    
    async def get_document_content(self, document_id: str) -> BinaryIO:
        """
        Get the content of a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            The document content
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document content cannot be retrieved
        """
        try:
            # Get document to get file path
            document = await self.get_document_by_id(document_id)
            
            # Check document status
            if document.status != "ready":
                logger.warning(f"Document {document_id} is not ready (status: {document.status})")
                raise StorageError(f"Document not ready for retrieval (status: {document.status})")
            
            # Get document content
            return await self.storage_service.get_document(document.file_path)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document content {document_id}: {str(e)}")
            raise StorageError(f"Failed to get document content: {str(e)}")
    
    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """
        Get the metadata of a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            The document metadata
            
        Raises:
            ResourceNotFoundError: If the document does not exist
        """
        try:
            document = await self.get_document_by_id(document_id)
            return document.metadata or {}
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document metadata {document_id}: {str(e)}")
            raise StorageError(f"Failed to get document metadata: {str(e)}")
    
    async def list_documents(self, 
                           user_id: Optional[str] = None, 
                           profile_id: Optional[str] = None,
                           status: Optional[str] = None,
                           mime_type: Optional[str] = None,
                           sort_by: str = "created_at",
                           sort_order: str = "desc",
                           offset: int = 0,
                           limit: int = 50) -> Tuple[List[Document], int]:
        """
        List documents with pagination and filtering.
        
        Args:
            user_id: Optional user ID filter
            profile_id: Optional profile ID filter
            status: Optional status filter
            mime_type: Optional MIME type filter
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)
            offset: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of (documents, total_count)
            
        Raises:
            ValidationError: If the parameters are invalid
        """
        try:
            # Validate sort parameters
            valid_sort_fields = ["created_at", "updated_at", "filename", "file_size"]
            if sort_by not in valid_sort_fields:
                raise ValidationError(f"Invalid sort field: {sort_by}. Valid fields: {', '.join(valid_sort_fields)}")
            
            valid_sort_orders = ["asc", "desc"]
            if sort_order.lower() not in valid_sort_orders:
                raise ValidationError(f"Invalid sort order: {sort_order}. Valid orders: {', '.join(valid_sort_orders)}")
            
            # Get documents with filtering
            async with self.transaction_manager.transaction() as session:
                documents, total_count = await self.document_repository.list_documents_paginated(
                    session=session,
                    user_id=user_id,
                    profile_id=profile_id,
                    status=status,
                    mime_type=mime_type,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    offset=offset,
                    limit=limit
                )
                
                return documents, total_count
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            raise StorageError(f"Failed to list documents: {str(e)}")
    
    async def search_documents(self, 
                             query: str,
                             user_id: Optional[str] = None,
                             profile_id: Optional[str] = None,
                             offset: int = 0,
                             limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search documents by full-text query.
        
        Args:
            query: Search query
            user_id: Optional user ID filter
            profile_id: Optional profile ID filter
            offset: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple of (search_results, total_count)
            
        Raises:
            ValidationError: If the parameters are invalid
        """
        try:
            # Validate query
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")
            
            # Use indexing service for content search if available and initialized
            if self.indexing_service and hasattr(self.indexing_service, 'initialized') and self.indexing_service.initialized:
                logger.info(f"Using content indexing service for search: {query}")
                results, total_count = await self.indexing_service.search_documents(
                    query=query,
                    user_id=user_id,
                    profile_id=profile_id,
                    limit=limit,
                    offset=offset
                )
                
                # Fetch full document metadata for each result
                enhanced_results = []
                for result in results:
                    try:
                        # Get the full document
                        document = await self.get_document_by_id(result['document_id'])
                        
                        # Add full document data to result
                        enhanced_result = {
                            **result,
                            "title": document.title,
                            "description": document.description,
                            "status": document.status,
                            "file_size": document.file_size,
                            "full_metadata": document.metadata
                        }
                        enhanced_results.append(enhanced_result)
                    except ResourceNotFoundError:
                        # Document might have been deleted, skip it
                        logger.warning(f"Skipping deleted document in search results: {result['document_id']}")
                        continue
                
                return enhanced_results, total_count
                
            else:
                # Fall back to database search
                logger.info(f"Using database search for query: {query}")
                async with self.transaction_manager.transaction() as session:
                    results, total_count = await self.document_repository.search_documents(
                        session=session,
                        query=query,
                        user_id=user_id,
                        profile_id=profile_id,
                        offset=offset,
                        limit=limit
                    )
                    
                    return results, total_count
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}")
            raise StorageError(f"Failed to search documents: {str(e)}")
    
    async def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """
        Get chunks for a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            List of document chunks
            
        Raises:
            ResourceNotFoundError: If the document does not exist
        """
        try:
            # First verify document exists
            await self.get_document_by_id(document_id)
            
            # Get document chunks
            return await self.document_repository.get_document_chunks(document_id)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document chunks {document_id}: {str(e)}")
            raise StorageError(f"Failed to get document chunks: {str(e)}")
    
    async def get_document_versions(self, document_id: str) -> List[DocumentVersion]:
        """
        Get versions for a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            List of document versions
            
        Raises:
            ResourceNotFoundError: If the document does not exist
        """
        try:
            # First verify document exists
            await self.get_document_by_id(document_id)
            
            # Get document versions
            return await self.document_repository.get_document_versions(document_id)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document versions {document_id}: {str(e)}")
            raise StorageError(f"Failed to get document versions: {str(e)}")
    
    async def get_document_version_content(self, document_id: str, version_id: str) -> BinaryIO:
        """
        Get the content of a document version.
        
        Args:
            document_id: The ID of the document
            version_id: The ID of the version
            
        Returns:
            The document version content
            
        Raises:
            ResourceNotFoundError: If the document or version does not exist
            StorageError: If the document version content cannot be retrieved
        """
        try:
            # First verify document exists
            await self.get_document_by_id(document_id)
            
            # Get document version content
            return await self.document_repository.get_document_version_content(document_id, version_id)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document version content {document_id}/{version_id}: {str(e)}")
            raise StorageError(f"Failed to get document version content: {str(e)}")
    
    async def get_document_summary(self, document_id: str) -> Dict[str, Any]:
        """
        Get a summary of a document with metadata and basic statistics.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            Document summary
            
        Raises:
            ResourceNotFoundError: If the document does not exist
        """
        try:
            # Get basic document info
            document = await self.get_document_by_id(document_id)
            
            # Count chunks
            chunks = await self.get_document_chunks(document_id)
            chunk_count = len(chunks)
            
            # Count versions
            versions = await self.get_document_versions(document_id)
            version_count = len(versions)
            
            # Build summary
            summary = {
                "document_id": document.document_id,
                "filename": document.filename,
                "file_size": document.file_size,
                "mime_type": document.mime_type,
                "status": document.status,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "processed_at": document.processed_at,
                "user_id": document.user_id,
                "profile_id": document.profile_id,
                "metadata": document.metadata,
                "chunk_count": chunk_count,
                "version_count": version_count,
                "latest_version": versions[0].version_number if versions else None,
                "latest_version_at": versions[0].created_at if versions else None
            }
            
            return summary
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document summary {document_id}: {str(e)}")
            raise StorageError(f"Failed to get document summary: {str(e)}")
    
    async def generate_document_url(self, document_id: str, expires_in: int = 3600) -> str:
        """
        Generate a temporary URL for accessing a document.
        
        Args:
            document_id: The ID of the document
            expires_in: Expiry time in seconds (default: 1 hour)
            
        Returns:
            Temporary URL for the document
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the URL cannot be generated
        """
        try:
            # Get document to get file path
            document = await self.get_document_by_id(document_id)
            
            # Check document status
            if document.status != "ready":
                logger.warning(f"Document {document_id} is not ready (status: {document.status})")
                raise StorageError(f"Document not ready for retrieval (status: {document.status})")
            
            # Generate temporary URL (not implemented for local storage)
            # This would be implemented for S3 or other cloud storage
            # For now, return a placeholder
            return f"/api/documents/{document_id}/download?token=temp_{document_id}_{int(datetime.utcnow().timestamp())}"
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate document URL {document_id}: {str(e)}")
            raise StorageError(f"Failed to generate document URL: {str(e)}") 