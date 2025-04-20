"""
Models for Document Service.

This module defines data models used by the document service.
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

if TYPE_CHECKING:
    from .database.models import DocumentModel


class Document:
    """Document model for the document service."""
    
    def __init__(
        self,
        document_id: UUID,
        user_id: UUID,
        profile_id: Optional[UUID] = None,
        filename: str = "",
        file_path: str = "",
        file_size: int = 0,
        mime_type: str = "",
        status: str = "pending",
        processed_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ):
        """Initialize a document."""
        self.document_id = document_id
        self.user_id = user_id
        self.profile_id = profile_id
        self.filename = filename
        self.file_path = file_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.status = status
        self.processed_at = processed_at
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        """Convert the document to a dictionary."""
        return {
            "document_id": str(self.document_id),
            "user_id": str(self.user_id),
            "profile_id": str(self.profile_id) if self.profile_id else None,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Document":
        """Create a document from a dictionary."""
        return cls(
            document_id=UUID(data["document_id"]),
            user_id=UUID(data["user_id"]),
            profile_id=UUID(data["profile_id"]) if data.get("profile_id") else None,
            filename=data.get("filename", ""),
            file_path=data.get("file_path", ""),
            file_size=data.get("file_size", 0),
            mime_type=data.get("mime_type", ""),
            status=data.get("status", "pending"),
            processed_at=datetime.fromisoformat(data["processed_at"]) if data.get("processed_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )
    
    def to_sqlalchemy(self) -> "DocumentModel":
        """Convert to SQLAlchemy model."""
        from .database.models import DocumentModel
        return DocumentModel(
            document_id=self.document_id,
            user_id=self.user_id,
            profile_id=self.profile_id,
            filename=self.filename,
            file_path=self.file_path,
            file_size=self.file_size,
            mime_type=self.mime_type,
            status=self.status,
            processed_at=self.processed_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata
        )
    
    @classmethod
    def from_sqlalchemy(cls, model: "DocumentModel") -> "Document":
        """Create from SQLAlchemy model."""
        return cls(
            document_id=model.document_id,
            user_id=model.user_id,
            profile_id=model.profile_id,
            filename=model.filename,
            file_path=model.file_path,
            file_size=model.file_size,
            mime_type=model.mime_type,
            status=model.status,
            processed_at=model.processed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata
        )


class DocumentChunk:
    """Document chunk data model for text chunks."""
    
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
            chunk_index: Index of this chunk in the document
            chunk_text: Text content of this chunk
            embedding: Optional vector embedding of this chunk
            created_at: Timestamp when this chunk was created
            metadata: Additional metadata for this chunk
        """
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.chunk_text = chunk_text
        self.embedding = embedding
        self.created_at = created_at
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for serialization."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
            "embedding": self.embedding,
            "created_at": self.created_at,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentChunk':
        """Create a chunk from a dictionary."""
        return cls(
            chunk_id=data.get("chunk_id"),
            document_id=data.get("document_id"),
            chunk_index=data.get("chunk_index", 0),
            chunk_text=data.get("chunk_text", ""),
            embedding=data.get("embedding"),
            created_at=data.get("created_at"),
            metadata=data.get("metadata", {})
        )


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
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary for serialization."""
        return {
            "version_id": self.version_id,
            "document_id": self.document_id,
            "version_number": self.version_number,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "comment": self.comment,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentVersion':
        """Create a version from a dictionary."""
        return cls(
            version_id=data.get("version_id"),
            document_id=data.get("document_id"),
            version_number=data.get("version_number", 0),
            file_path=data.get("file_path", ""),
            file_size=data.get("file_size", 0),
            created_at=data.get("created_at"),
            created_by=data.get("created_by"),
            comment=data.get("comment"),
            metadata=data.get("metadata", {})
        )


class DocumentShare:
    """Document share data model for tracking document shares."""
    
    def __init__(
        self,
        share_id: str,
        document_id: str,
        shared_by: str,
        shared_with: str,
        permissions: List[str],
        expires_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a document share instance.
        
        Args:
            share_id: Unique identifier for the share
            document_id: ID of the document being shared
            shared_by: ID of the user sharing the document
            shared_with: ID of the user receiving access
            permissions: List of permissions granted
            expires_at: Optional expiration timestamp
            created_at: Timestamp when the share was created
            updated_at: Timestamp when the share was last updated
            metadata: Additional metadata for the share
        """
        self.share_id = share_id
        self.document_id = document_id
        self.shared_by = shared_by
        self.shared_with = shared_with
        self.permissions = permissions
        self.expires_at = expires_at
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert share to dictionary for serialization."""
        return {
            "share_id": self.share_id,
            "document_id": self.document_id,
            "shared_by": self.shared_by,
            "shared_with": self.shared_with,
            "permissions": self.permissions,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentShare':
        """Create a share from a dictionary."""
        expires_at = datetime.fromisoformat(data.get("expires_at")) if data.get("expires_at") else None
        created_at = datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else None
        updated_at = datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") else None
        
        return cls(
            share_id=data.get("share_id"),
            document_id=data.get("document_id"),
            shared_by=data.get("shared_by"),
            shared_with=data.get("shared_with"),
            permissions=data.get("permissions", []),
            expires_at=expires_at,
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        ) 