"""
Interfaces for Document Service.

This module defines interfaces used by the document service,
following the SOLID principles, particularly Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Protocol, BinaryIO, Union

from .models import Document, DocumentChunk, DocumentVersion


class DocumentRepositoryInterface(ABC):
    """Interface for document data storage operations."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the repository and release resources."""
        pass
    
    @abstractmethod
    async def save_document(self, document: Document, file_content: Optional[BinaryIO] = None) -> Document:
        """
        Save a document to the repository.
        
        Args:
            document: The document to save
            file_content: Optional file content stream
            
        Returns:
            The saved document
            
        Raises:
            StorageError: If the document cannot be saved
        """
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Document:
        """
        Get a document by ID.
        
        Args:
            document_id: The ID of the document to get
            
        Returns:
            The document
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> None:
        """
        Delete a document by ID.
        
        Args:
            document_id: The ID of the document to delete
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document cannot be deleted
        """
        pass
    
    @abstractmethod
    async def list_documents(self, 
                           user_id: Optional[str] = None, 
                           profile_id: Optional[str] = None) -> List[Document]:
        """
        List documents, optionally filtered by user ID or profile ID.
        
        Args:
            user_id: Optional user ID to filter by
            profile_id: Optional profile ID to filter by
            
        Returns:
            List of documents
            
        Raises:
            StorageError: If the documents cannot be listed
        """
        pass
    
    @abstractmethod
    async def get_document_content(self, document_id: str) -> BinaryIO:
        """
        Get the binary content of a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            File-like object with document content
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document content cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> Document:
        """
        Update the metadata of a document.
        
        Args:
            document_id: The ID of the document
            metadata: New metadata to update or add
            
        Returns:
            The updated document
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document metadata cannot be updated
        """
        pass
    
    @abstractmethod
    async def save_document_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """
        Save a document chunk to the repository.
        
        Args:
            chunk: The document chunk to save
            
        Returns:
            The saved document chunk
            
        Raises:
            StorageError: If the document chunk cannot be saved
        """
        pass
    
    @abstractmethod
    async def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            List of document chunks
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document chunks cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def create_document_version(self, version: DocumentVersion, file_content: BinaryIO) -> DocumentVersion:
        """
        Create a new version of a document.
        
        Args:
            version: The document version to create
            file_content: File content stream for the new version
            
        Returns:
            The created document version
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document version cannot be created
        """
        pass
    
    @abstractmethod
    async def get_document_versions(self, document_id: str) -> List[DocumentVersion]:
        """
        Get all versions of a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            List of document versions
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document versions cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def get_document_version_content(self, document_id: str, version_id: str) -> BinaryIO:
        """
        Get the binary content of a document version.
        
        Args:
            document_id: The ID of the document
            version_id: The ID of the version
            
        Returns:
            File-like object with document version content
            
        Raises:
            ResourceNotFoundError: If the document or version does not exist
            StorageError: If the document version content cannot be retrieved
        """
        pass

class DocumentExportServiceInterface(ABC):
    """Interface for document export and sharing services."""
    
    @abstractmethod
    async def export_document(
        self, 
        document_id: str, 
        format_type: str,
        user_id: Optional[str] = None
    ) -> BinaryIO:
        """
        Export a document in the specified format.
        
        Args:
            document_id: ID of the document to export
            format_type: Format to export to (pdf, docx, html, txt, json)
            user_id: Optional user ID for access control
            
        Returns:
            File-like object containing the exported document
        """
        pass
    
    @abstractmethod
    async def share_document(
        self,
        document_id: str,
        share_method: str,
        user_id: str,
        recipients: Optional[List[str]] = None,
        expiry_hours: Optional[int] = None
    ) -> str:
        """
        Share a document using the specified method.
        
        Args:
            document_id: ID of the document to share
            share_method: Method to share (email, link)
            user_id: ID of the user sharing the document
            recipients: Optional list of email recipients
            expiry_hours: Optional hours until link expires
            
        Returns:
            Share URL or confirmation message
        """
        pass
    
    @abstractmethod
    async def generate_embed_code(
        self,
        document_id: str,
        user_id: str,
        settings: Dict[str, Any]
    ) -> str:
        """
        Generate HTML embed code for a document.
        
        Args:
            document_id: ID of the document to embed
            user_id: ID of the user embedding the document
            settings: Embedding settings (width, height, etc.)
            
        Returns:
            HTML embed code
        """
        pass 