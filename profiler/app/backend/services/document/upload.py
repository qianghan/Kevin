"""
Document upload handling with support for chunked uploads.

This module provides functionality for handling large file uploads with chunked processing.
"""

import os
import io
import json
import time
import asyncio
import tempfile
from typing import Dict, List, Any, Optional, BinaryIO, Tuple, Union
from datetime import datetime, timedelta
import hashlib
import uuid
import shutil

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import StorageError, ValidationError, ResourceNotFoundError
from .models import Document

logger = get_logger(__name__)


class UploadSession:
    """Represents an upload session for a chunked file upload."""
    
    def __init__(self, 
                 session_id: str, 
                 filename: str, 
                 file_size: int, 
                 mime_type: str, 
                 chunk_size: int,
                 user_id: Optional[str] = None,
                 profile_id: Optional[str] = None,
                 expires_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an upload session.
        
        Args:
            session_id: Unique ID for the upload session
            filename: Original filename
            file_size: Total file size in bytes
            mime_type: MIME type of the file
            chunk_size: Size of each chunk in bytes
            user_id: ID of the user uploading the file
            profile_id: ID of the profile the file is associated with
            expires_at: When the session expires
            metadata: Additional metadata for the file
        """
        self.session_id = session_id
        self.filename = filename
        self.file_size = file_size
        self.mime_type = mime_type
        self.chunk_size = chunk_size
        self.user_id = user_id
        self.profile_id = profile_id
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(hours=24))
        self.metadata = metadata or {}
        
        # Upload status
        self.chunks_received: Dict[int, bool] = {}
        self.chunks_total = self._calculate_total_chunks()
        self.temp_file_path: Optional[str] = None
        self.completed = False
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            self.temp_file_path = temp_file.name
    
    def _calculate_total_chunks(self) -> int:
        """Calculate the total number of chunks needed for the file."""
        return (self.file_size + self.chunk_size - 1) // self.chunk_size
    
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_complete(self) -> bool:
        """Check if all chunks have been received."""
        return len(self.chunks_received) == self.chunks_total and all(self.chunks_received.values())
    
    def get_missing_chunks(self) -> List[int]:
        """Get a list of chunk indices that have not been received yet."""
        missing = []
        for i in range(self.chunks_total):
            if i not in self.chunks_received or not self.chunks_received[i]:
                missing.append(i)
        return missing
    
    def get_progress(self) -> float:
        """Get upload progress as a percentage."""
        if self.chunks_total == 0:
            return 0.0
        chunks_completed = sum(1 for chunk in self.chunks_received.values() if chunk)
        return (chunks_completed / self.chunks_total) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the session to a dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "chunk_size": self.chunk_size,
            "user_id": self.user_id,
            "profile_id": self.profile_id,
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata,
            "chunks_total": self.chunks_total,
            "chunks_received": len(self.chunks_received),
            "progress": self.get_progress(),
            "completed": self.completed,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class ChunkedUploadService:
    """Service for handling chunked file uploads."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the chunked upload service.
        
        Args:
            config: Optional configuration for the service
        """
        self.config = config or {}
        self.sessions: Dict[str, UploadSession] = {}
        self.temp_dir = self.config.get("temp_dir", tempfile.gettempdir())
        self.default_chunk_size = self.config.get("default_chunk_size", 1024 * 1024)  # 1MB
        self.session_timeout = self.config.get("session_timeout", 24)  # hours
        
        # Create cleanup task
        self._cleanup_task = None
    
    async def initialize(self) -> None:
        """Initialize the chunked upload service."""
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        logger.info("Initialized chunked upload service")
    
    async def shutdown(self) -> None:
        """Shutdown the chunked upload service."""
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clean up all temporary files
        for session_id, session in list(self.sessions.items()):
            await self._cleanup_session(session_id)
        
        logger.info("Shutdown chunked upload service")
    
    async def create_upload_session(self,
                                   filename: str,
                                   file_size: int,
                                   mime_type: str,
                                   chunk_size: Optional[int] = None,
                                   user_id: Optional[str] = None,
                                   profile_id: Optional[str] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> UploadSession:
        """
        Create a new upload session for a chunked file upload.
        
        Args:
            filename: Original filename
            file_size: Total file size in bytes
            mime_type: MIME type of the file
            chunk_size: Size of each chunk in bytes
            user_id: ID of the user uploading the file
            profile_id: ID of the profile the file is associated with
            metadata: Additional metadata for the file
            
        Returns:
            The created upload session
            
        Raises:
            ValidationError: If the parameters are invalid
        """
        # Validate parameters
        if not filename or not filename.strip():
            raise ValidationError("Filename is required")
        
        if file_size <= 0:
            raise ValidationError("File size must be greater than 0")
        
        if not mime_type or not mime_type.strip():
            raise ValidationError("MIME type is required")
        
        # Set defaults
        chunk_size = chunk_size or self.default_chunk_size
        
        # Create upload session
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=self.session_timeout)
        
        session = UploadSession(
            session_id=session_id,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            chunk_size=chunk_size,
            user_id=user_id,
            profile_id=profile_id,
            expires_at=expires_at,
            metadata=metadata
        )
        
        # Save session
        self.sessions[session_id] = session
        
        logger.info(f"Created upload session {session_id} for {filename} ({file_size} bytes)")
        return session
    
    async def upload_chunk(self,
                         session_id: str,
                         chunk_index: int,
                         chunk_content: BinaryIO) -> Dict[str, Any]:
        """
        Upload a chunk for an upload session.
        
        Args:
            session_id: ID of the upload session
            chunk_index: Index of the chunk
            chunk_content: Content of the chunk
            
        Returns:
            Status of the upload session
            
        Raises:
            ResourceNotFoundError: If the session does not exist
            ValidationError: If the chunk index is invalid
            StorageError: If the chunk cannot be saved
        """
        # Get upload session
        session = self.sessions.get(session_id)
        if not session:
            raise ResourceNotFoundError(f"Upload session not found: {session_id}")
        
        # Check if session has expired
        if session.is_expired():
            await self._cleanup_session(session_id)
            raise ResourceNotFoundError(f"Upload session has expired: {session_id}")
        
        # Validate chunk index
        if chunk_index < 0 or chunk_index >= session.chunks_total:
            raise ValidationError(f"Invalid chunk index: {chunk_index}. Expected 0-{session.chunks_total-1}")
        
        try:
            # Open temporary file
            with open(session.temp_file_path, 'r+b') as temp_file:
                # Seek to position for this chunk
                position = chunk_index * session.chunk_size
                temp_file.seek(position)
                
                # Write chunk content
                shutil.copyfileobj(chunk_content, temp_file)
            
            # Mark chunk as received
            session.chunks_received[chunk_index] = True
            
            # Update session
            session.updated_at = datetime.utcnow().isoformat()
            
            # Check if upload is complete
            if session.is_complete():
                session.completed = True
                logger.info(f"Upload session {session_id} completed")
            
            # Return session status
            return {
                "session_id": session_id,
                "chunk_index": chunk_index,
                "received": True,
                "progress": session.get_progress(),
                "completed": session.completed
            }
            
        except Exception as e:
            logger.error(f"Failed to upload chunk {chunk_index} for session {session_id}: {str(e)}")
            raise StorageError(f"Failed to upload chunk: {str(e)}")
    
    async def get_upload_session(self, session_id: str) -> UploadSession:
        """
        Get an upload session by ID.
        
        Args:
            session_id: ID of the upload session
            
        Returns:
            The upload session
            
        Raises:
            ResourceNotFoundError: If the session does not exist
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ResourceNotFoundError(f"Upload session not found: {session_id}")
        
        # Check if session has expired
        if session.is_expired():
            await self._cleanup_session(session_id)
            raise ResourceNotFoundError(f"Upload session has expired: {session_id}")
        
        return session
    
    async def complete_upload(self, session_id: str) -> Tuple[BinaryIO, UploadSession]:
        """
        Complete an upload session and get the uploaded file.
        
        Args:
            session_id: ID of the upload session
            
        Returns:
            Tuple of (file_content, session)
            
        Raises:
            ResourceNotFoundError: If the session does not exist
            ValidationError: If the upload is not complete
            StorageError: If the file cannot be processed
        """
        # Get upload session
        session = await self.get_upload_session(session_id)
        
        # Check if upload is complete
        if not session.is_complete():
            missing_chunks = session.get_missing_chunks()
            raise ValidationError(f"Upload is not complete. Missing chunks: {missing_chunks}")
        
        try:
            # Open the completed file
            file_content = open(session.temp_file_path, 'rb')
            
            # Return file content and session
            # Note: The caller is responsible for closing the file
            return file_content, session
            
        except Exception as e:
            logger.error(f"Failed to complete upload for session {session_id}: {str(e)}")
            raise StorageError(f"Failed to complete upload: {str(e)}")
    
    async def cancel_upload(self, session_id: str) -> None:
        """
        Cancel an upload session.
        
        Args:
            session_id: ID of the upload session
            
        Raises:
            ResourceNotFoundError: If the session does not exist
        """
        # Check if session exists
        if session_id not in self.sessions:
            raise ResourceNotFoundError(f"Upload session not found: {session_id}")
        
        # Cleanup session
        await self._cleanup_session(session_id)
        logger.info(f"Cancelled upload session {session_id}")
    
    async def _cleanup_session(self, session_id: str) -> None:
        """Clean up resources for an upload session."""
        session = self.sessions.pop(session_id, None)
        if not session:
            return
        
        # Remove temporary file
        if session.temp_file_path and os.path.exists(session.temp_file_path):
            try:
                os.unlink(session.temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file for session {session_id}: {str(e)}")
    
    async def _cleanup_expired_sessions(self) -> None:
        """Periodically clean up expired upload sessions."""
        try:
            while True:
                # Wait for a while
                await asyncio.sleep(3600)  # Check every hour
                
                # Find expired sessions
                now = datetime.utcnow()
                expired_sessions = [
                    session_id for session_id, session in self.sessions.items()
                    if now > session.expires_at
                ]
                
                # Clean up expired sessions
                for session_id in expired_sessions:
                    await self._cleanup_session(session_id)
                    logger.info(f"Cleaned up expired upload session {session_id}")
        
        except asyncio.CancelledError:
            logger.info("Upload session cleanup task cancelled")
            raise 