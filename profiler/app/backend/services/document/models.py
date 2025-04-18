"""
Models for Document Service.

This module defines data models used by the document service.
"""

from typing import Dict, List, Any, Optional


class Document:
    """Document data model."""
    
    def __init__(
        self,
        document_id: str,
        user_id: str,
        profile_id: Optional[str] = None,
        filename: str = "",
        file_path: str = "",
        file_size: int = 0,
        mime_type: str = "",
        status: str = "processing",
        processed_at: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a document instance.
        
        Args:
            document_id: Unique identifier for the document
            user_id: ID of the user who owns this document
            profile_id: Optional ID of the profile this document is linked to
            filename: Original filename
            file_path: Path where the document is stored
            file_size: Size of the document in bytes
            mime_type: MIME type of the document
            status: Document processing status (processing, ready, error)
            processed_at: Timestamp when document processing completed
            created_at: Timestamp when the document was created
            updated_at: Timestamp when the document was last updated
            metadata: Additional metadata for the document
        """
        self.document_id = document_id
        self.user_id = user_id
        self.profile_id = profile_id
        self.filename = filename
        self.file_path = file_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.status = status
        self.processed_at = processed_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.metadata = metadata or {}


class DocumentChunk:
    """Document chunk data model for storing processed document segments."""
    
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        chunk_index: int,
        chunk_text: str,
        embedding: Optional[List[float]] = None,
        created_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a document chunk instance.
        
        Args:
            chunk_id: Unique identifier for the chunk
            document_id: ID of the document this chunk belongs to
            chunk_index: Index position of this chunk within the document
            chunk_text: Text content of the chunk
            embedding: Vector embedding of the chunk for semantic search
            created_at: Timestamp when the chunk was created
            metadata: Additional metadata for the chunk
        """
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.chunk_text = chunk_text
        self.embedding = embedding
        self.created_at = created_at
        self.metadata = metadata or {}


class DocumentVersion:
    """Document version data model for versioning."""
    
    def __init__(
        self,
        version_id: str,
        document_id: str,
        version_number: int,
        file_path: str,
        file_size: int,
        created_at: Optional[str] = None,
        created_by: Optional[str] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a document version instance.
        
        Args:
            version_id: Unique identifier for the version
            document_id: ID of the document this version belongs to
            version_number: Sequential version number
            file_path: Path where this version is stored
            file_size: Size of this version in bytes
            created_at: Timestamp when this version was created
            created_by: ID of the user who created this version
            comment: Optional comment about this version
            metadata: Additional metadata for this version
        """
        self.version_id = version_id
        self.document_id = document_id
        self.version_number = version_number
        self.file_path = file_path
        self.file_size = file_size
        self.created_at = created_at
        self.created_by = created_by
        self.comment = comment
        self.metadata = metadata or {} 