"""
Document backup and restore functionality.

This module provides functionality for backing up and restoring document data.
"""

import os
import json
import shutil
import zipfile
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, BinaryIO, Tuple

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import StorageError
from .database.repository import PostgreSQLDocumentRepository
from .models import Document

logger = get_logger(__name__)


class DocumentBackupService:
    """Service for backing up and restoring document data."""
    
    def __init__(self, document_repository: PostgreSQLDocumentRepository):
        """
        Initialize the document backup service.
        
        Args:
            document_repository: Repository for document operations
        """
        self.document_repository = document_repository
    
    async def backup_user_documents(self, user_id: str, backup_file: BinaryIO) -> Dict[str, Any]:
        """
        Backup all documents for a user.
        
        Args:
            user_id: ID of the user whose documents to backup
            backup_file: File-like object to write the backup to
            
        Returns:
            Backup metadata
            
        Raises:
            StorageError: If the backup fails
        """
        try:
            # Get all documents for the user
            documents = await self.document_repository.list_documents(user_id=user_id)
            
            if not documents:
                logger.info(f"No documents found for user {user_id}")
                return {
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "document_count": 0,
                    "status": "success",
                    "message": "No documents to backup"
                }
            
            # Create temporary directory for backup files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create metadata file
                metadata = {
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "document_count": len(documents),
                    "documents": []
                }
                
                # Create a ZIP file
                with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add metadata file
                    metadata_path = os.path.join(temp_dir, "metadata.json")
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f)
                    zipf.write(metadata_path, "metadata.json")
                    
                    # Add documents
                    for document in documents:
                        document_metadata = document.dict()
                        document_id = document.document_id
                        
                        try:
                            # Get document content
                            document_content = await self.document_repository.get_document_content(document_id)
                            
                            # Save document content to temp file
                            document_path = os.path.join(temp_dir, f"{document_id}.bin")
                            with open(document_path, 'wb') as f:
                                shutil.copyfileobj(document_content, f)
                            
                            # Add document to ZIP
                            zipf.write(document_path, f"documents/{document_id}.bin")
                            
                            # Get document chunks
                            chunks = await self.document_repository.get_document_chunks(document_id)
                            
                            # Save chunks metadata
                            if chunks:
                                chunks_metadata = [chunk.dict() for chunk in chunks]
                                chunks_path = os.path.join(temp_dir, f"{document_id}_chunks.json")
                                with open(chunks_path, 'w') as f:
                                    json.dump(chunks_metadata, f)
                                zipf.write(chunks_path, f"chunks/{document_id}_chunks.json")
                            
                            # Get document versions
                            versions = await self.document_repository.get_document_versions(document_id)
                            
                            # Save versions metadata and content
                            if versions:
                                versions_metadata = []
                                for version in versions:
                                    version_metadata = version.dict()
                                    version_id = version.version_id
                                    versions_metadata.append(version_metadata)
                                    
                                    # Get version content
                                    version_content = await self.document_repository.get_document_version_content(
                                        document_id, version_id
                                    )
                                    
                                    # Save version content to temp file
                                    version_path = os.path.join(temp_dir, f"{version_id}.bin")
                                    with open(version_path, 'wb') as f:
                                        shutil.copyfileobj(version_content, f)
                                    
                                    # Add version to ZIP
                                    zipf.write(version_path, f"versions/{version_id}.bin")
                                
                                # Save versions metadata
                                versions_path = os.path.join(temp_dir, f"{document_id}_versions.json")
                                with open(versions_path, 'w') as f:
                                    json.dump(versions_metadata, f)
                                zipf.write(versions_path, f"versions/{document_id}_versions.json")
                            
                            # Add document metadata to overall metadata
                            document_metadata["chunks_count"] = len(chunks)
                            document_metadata["versions_count"] = len(versions)
                            metadata["documents"].append(document_metadata)
                            
                        except Exception as e:
                            logger.error(f"Error backing up document {document_id}: {str(e)}")
                            continue
                    
                    # Update metadata file with complete information
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f)
                    zipf.write(metadata_path, "metadata.json")
            
            logger.info(f"Successfully backed up {len(metadata['documents'])} documents for user {user_id}")
            
            return {
                "user_id": user_id,
                "timestamp": metadata["timestamp"],
                "document_count": len(metadata["documents"]),
                "status": "success",
                "message": f"Successfully backed up {len(metadata['documents'])} documents"
            }
            
        except Exception as e:
            logger.error(f"Failed to backup documents for user {user_id}: {str(e)}")
            raise StorageError(f"Failed to backup documents: {str(e)}")
    
    async def restore_user_documents(self, user_id: str, backup_file: BinaryIO) -> Dict[str, Any]:
        """
        Restore documents from a backup file.
        
        Args:
            user_id: ID of the user to restore documents for
            backup_file: File-like object containing the backup
            
        Returns:
            Restoration metadata
            
        Raises:
            StorageError: If the restoration fails
        """
        try:
            # Create temporary directory for extracted files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract ZIP file
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Read metadata
                metadata_path = os.path.join(temp_dir, "metadata.json")
                if not os.path.exists(metadata_path):
                    raise StorageError("Invalid backup file: metadata.json not found")
                
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Verify user ID
                backup_user_id = metadata.get("user_id")
                if backup_user_id != user_id:
                    logger.warning(f"Backup user ID {backup_user_id} does not match target user ID {user_id}")
                
                # Restore documents
                restored_documents = []
                skipped_documents = []
                
                for document_metadata in metadata.get("documents", []):
                    document_id = document_metadata.get("document_id")
                    
                    try:
                        # Check if document already exists
                        try:
                            existing_document = await self.document_repository.get_document(document_id)
                            logger.info(f"Document {document_id} already exists, skipping")
                            skipped_documents.append(document_id)
                            continue
                        except:
                            # Document doesn't exist, proceed with restore
                            pass
                        
                        # Create document object
                        document = Document(**document_metadata)
                        
                        # Get document content
                        document_path = os.path.join(temp_dir, f"documents/{document_id}.bin")
                        if not os.path.exists(document_path):
                            logger.warning(f"Document content not found for {document_id}, skipping")
                            skipped_documents.append(document_id)
                            continue
                        
                        with open(document_path, 'rb') as f:
                            # Save document
                            await self.document_repository.save_document(document, f)
                        
                        # Restore chunks if they exist
                        chunks_path = os.path.join(temp_dir, f"chunks/{document_id}_chunks.json")
                        if os.path.exists(chunks_path):
                            with open(chunks_path, 'r') as f:
                                chunks_metadata = json.load(f)
                                
                                for chunk_metadata in chunks_metadata:
                                    chunk = DocumentChunk(**chunk_metadata)
                                    await self.document_repository.save_document_chunk(chunk)
                        
                        # Restore versions if they exist
                        versions_path = os.path.join(temp_dir, f"versions/{document_id}_versions.json")
                        if os.path.exists(versions_path):
                            with open(versions_path, 'r') as f:
                                versions_metadata = json.load(f)
                                
                                for version_metadata in versions_metadata:
                                    version_id = version_metadata.get("version_id")
                                    version_path = os.path.join(temp_dir, f"versions/{version_id}.bin")
                                    
                                    if os.path.exists(version_path):
                                        version = DocumentVersion(**version_metadata)
                                        with open(version_path, 'rb') as vf:
                                            await self.document_repository.create_document_version(version, vf)
                        
                        restored_documents.append(document_id)
                        
                    except Exception as e:
                        logger.error(f"Error restoring document {document_id}: {str(e)}")
                        skipped_documents.append(document_id)
                        continue
                
                logger.info(f"Successfully restored {len(restored_documents)} documents for user {user_id}")
                logger.info(f"Skipped {len(skipped_documents)} documents")
                
                return {
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "restored_count": len(restored_documents),
                    "skipped_count": len(skipped_documents),
                    "status": "success",
                    "message": f"Successfully restored {len(restored_documents)} documents, skipped {len(skipped_documents)}"
                }
                
        except Exception as e:
            logger.error(f"Failed to restore documents for user {user_id}: {str(e)}")
            raise StorageError(f"Failed to restore documents: {str(e)}") 