"""
SQLAlchemy models for Document Service.

This module defines SQLAlchemy models used by the document service.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DocumentModel(Base):
    """SQLAlchemy model for documents."""
    __tablename__ = "documents"

    document_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    profile_id = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    mime_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="processing")
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    document_metadata = Column(JSON, nullable=False, default={})
    access_control = Column(JSON, nullable=False, default={})

    # Relationships
    chunks = relationship("DocumentChunkModel", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersionModel", back_populates="document", cascade="all, delete-orphan")
    shares = relationship("DocumentShareModel", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for serialization."""
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.document_metadata,
            "access_control": self.access_control
        }

class DocumentChunkModel(Base):
    """SQLAlchemy model for document chunks."""
    __tablename__ = "document_chunks"

    chunk_id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    document_metadata = Column(JSON, nullable=False, default={})

    # Relationships
    document = relationship("DocumentModel", back_populates="chunks")

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for serialization."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.document_metadata
        }

class DocumentVersionModel(Base):
    """SQLAlchemy model for document versions."""
    __tablename__ = "document_versions"

    version_id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    document_metadata = Column(JSON, nullable=False, default={})

    # Relationships
    document = relationship("DocumentModel", back_populates="versions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary for serialization."""
        return {
            "version_id": self.version_id,
            "document_id": self.document_id,
            "version_number": self.version_number,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "comment": self.comment,
            "metadata": self.document_metadata
        }

class DocumentShareModel(Base):
    """SQLAlchemy model for document shares."""
    __tablename__ = "document_shares"

    share_id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=False)
    shared_by = Column(String, nullable=False)
    shared_with = Column(String, nullable=False)
    permissions = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    document_metadata = Column(JSON, nullable=False, default={})

    # Relationships
    document = relationship("DocumentModel", back_populates="shares")

    def to_dict(self) -> Dict[str, Any]:
        """Convert share to dictionary for serialization."""
        return {
            "share_id": self.share_id,
            "document_id": self.document_id,
            "shared_by": self.shared_by,
            "shared_with": self.shared_with,
            "permissions": self.permissions,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.document_metadata
        } 