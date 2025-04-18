"""
SQLAlchemy models for Document database implementation.

This module defines SQLAlchemy ORM models for persisting document data to a relational database.
"""

from datetime import datetime
from typing import Dict, Any
import json

from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, BYTEA

Base = declarative_base()


class DocumentModel(Base):
    """SQLAlchemy model for Document table."""
    __tablename__ = "documents"

    document_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    profile_id = Column(String(36), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(20), default="processing", nullable=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata = Column(Text, nullable=True)  # JSON-serialized

    # Relationships
    chunks = relationship("DocumentChunkModel", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersionModel", back_populates="document", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_documents_user_id", user_id),
        Index("idx_documents_profile_id", profile_id),
        Index("idx_documents_status", status),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "document_id": self.document_id,
            "user_id": self.user_id,
            "profile_id": self.profile_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": json.loads(self.metadata) if self.metadata else {}
        }


class DocumentChunkModel(Base):
    """SQLAlchemy model for DocumentChunk table."""
    __tablename__ = "document_chunks"

    chunk_id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON-serialized
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(Text, nullable=True)  # JSON-serialized

    # Relationships
    document = relationship("DocumentModel", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index("idx_document_chunks_document_id", document_id),
        Index("idx_document_chunks_chunk_index", chunk_index),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
            "embedding": json.loads(self.embedding) if self.embedding else None,
            "created_at": self.created_at.isoformat(),
            "metadata": json.loads(self.metadata) if self.metadata else {}
        }


class DocumentVersionModel(Base):
    """SQLAlchemy model for DocumentVersion table."""
    __tablename__ = "document_versions"

    version_id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), nullable=True)  # User ID
    comment = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON-serialized

    # Relationships
    document = relationship("DocumentModel", back_populates="versions")

    # Indexes
    __table_args__ = (
        Index("idx_document_versions_document_id", document_id),
        Index("idx_document_versions_version_number", version_number),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "version_id": self.version_id,
            "document_id": self.document_id,
            "version_number": self.version_number,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "comment": self.comment,
            "metadata": json.loads(self.metadata) if self.metadata else {}
        } 