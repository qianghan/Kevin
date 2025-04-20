"""
Document versioning system.

This module provides functionality for managing document versions.
"""

import uuid
from typing import Dict, List, Any, Optional, BinaryIO, Tuple
from datetime import datetime

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import StorageError, ResourceNotFoundError, ValidationError
from .database.repository import PostgreSQLDocumentRepository
from .storage import DocumentStorageService
from .models import Document, DocumentVersion
from .transaction import DocumentTransactionManager

logger = get_logger(__name__)


class DocumentVersioningService:
    """Service for managing document versions."""
    
    def __init__(self,
                document_repository: PostgreSQLDocumentRepository,
                storage_service: DocumentStorageService,
                transaction_manager: DocumentTransactionManager):
        """
        Initialize the document versioning service.
        
        Args:
            document_repository: Repository for document operations
            storage_service: Service for document storage operations
            transaction_manager: Manager for document transactions
        """
        self.document_repository = document_repository
        self.storage_service = storage_service
        self.transaction_manager = transaction_manager
    
    async def create_version(self, 
                           document_id: str, 
                           file_content: BinaryIO, 
                           created_by: Optional[str] = None,
                           comment: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> DocumentVersion:
        """
        Create a new version of a document.
        
        Args:
            document_id: ID of the document
            file_content: Content of the new version
            created_by: ID of the user creating the version
            comment: Optional comment about the version
            metadata: Optional metadata for the version
            
        Returns:
            The created document version
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the version cannot be created
        """
        async with self.transaction_manager.locked_transaction(document_id) as session:
            try:
                # Get document to verify it exists
                document = await self.document_repository.get_document(document_id)
                
                # Get existing versions to determine next version number
                versions = await self.document_repository.get_document_versions(document_id)
                next_version = 1
                if versions:
                    # Find highest version number and increment
                    highest_version = max(v.version_number for v in versions)
                    next_version = highest_version + 1
                
                # Create new version object
                version_id = str(uuid.uuid4())
                version = DocumentVersion(
                    version_id=version_id,
                    document_id=document_id,
                    version_number=next_version,
                    file_path="",  # Will be set by create_document_version
                    file_size=0,   # Will be set by create_document_version
                    created_at=datetime.utcnow().isoformat(),
                    created_by=created_by,
                    comment=comment,
                    metadata=metadata or {}
                )
                
                # Create version in repository
                created_version = await self.document_repository.create_document_version(version, file_content)
                
                # Update document metadata to include version info
                doc_metadata = document.metadata or {}
                if "versions" not in doc_metadata:
                    doc_metadata["versions"] = []
                
                # Add version info to document metadata
                version_info = {
                    "version_id": version_id,
                    "version_number": next_version,
                    "created_at": created_version.created_at,
                    "created_by": created_by,
                    "comment": comment
                }
                doc_metadata["versions"].append(version_info)
                doc_metadata["latest_version"] = next_version
                
                # Update document metadata
                await self.document_repository.update_document_metadata(document_id, doc_metadata)
                
                logger.info(f"Created version {next_version} for document {document_id}")
                return created_version
                
            except ResourceNotFoundError:
                logger.error(f"Document {document_id} not found")
                raise
            except Exception as e:
                logger.error(f"Failed to create document version: {str(e)}")
                raise StorageError(f"Failed to create document version: {str(e)}")
    
    async def get_version(self, document_id: str, version_id: str) -> DocumentVersion:
        """
        Get a specific version of a document.
        
        Args:
            document_id: ID of the document
            version_id: ID of the version
            
        Returns:
            The document version
            
        Raises:
            ResourceNotFoundError: If the document or version does not exist
        """
        try:
            # Get all versions for the document
            versions = await self.document_repository.get_document_versions(document_id)
            
            # Find the requested version
            for version in versions:
                if version.version_id == version_id:
                    return version
            
            raise ResourceNotFoundError(f"Version {version_id} not found for document {document_id}")
                
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document version {document_id}/{version_id}: {str(e)}")
            raise StorageError(f"Failed to get document version: {str(e)}")
    
    async def get_version_by_number(self, document_id: str, version_number: int) -> DocumentVersion:
        """
        Get a version of a document by its version number.
        
        Args:
            document_id: ID of the document
            version_number: Number of the version
            
        Returns:
            The document version
            
        Raises:
            ResourceNotFoundError: If the document or version does not exist
        """
        try:
            # Get all versions for the document
            versions = await self.document_repository.get_document_versions(document_id)
            
            # Find the requested version by number
            for version in versions:
                if version.version_number == version_number:
                    return version
            
            raise ResourceNotFoundError(f"Version {version_number} not found for document {document_id}")
                
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document version {document_id}/{version_number}: {str(e)}")
            raise StorageError(f"Failed to get document version: {str(e)}")
    
    async def get_version_content(self, document_id: str, version_id: str) -> BinaryIO:
        """
        Get the content of a document version.
        
        Args:
            document_id: ID of the document
            version_id: ID of the version
            
        Returns:
            The version content
            
        Raises:
            ResourceNotFoundError: If the document or version does not exist
            StorageError: If the version content cannot be retrieved
        """
        try:
            return await self.document_repository.get_document_version_content(document_id, version_id)
                
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document version content {document_id}/{version_id}: {str(e)}")
            raise StorageError(f"Failed to get document version content: {str(e)}")
    
    async def delete_version(self, document_id: str, version_id: str) -> None:
        """
        Delete a document version.
        
        Args:
            document_id: ID of the document
            version_id: ID of the version
            
        Raises:
            ResourceNotFoundError: If the document or version does not exist
            StorageError: If the version cannot be deleted
        """
        async with self.transaction_manager.locked_transaction(document_id) as session:
            try:
                # Get document to verify it exists and get metadata
                document = await self.document_repository.get_document(document_id)
                
                # Get version to check if it exists and get file path
                version = await self.get_version(document_id, version_id)
                
                # Don't allow deleting the latest version if it's the only version
                versions = await self.document_repository.get_document_versions(document_id)
                if len(versions) == 1 and versions[0].version_id == version_id:
                    raise ValidationError("Cannot delete the only version of a document")
                
                # Delete version file from storage
                if version.file_path:
                    await self.storage_service.delete_document(version.file_path)
                
                # Delete version from database
                await session.execute(
                    f"DELETE FROM profiler_schema.document_versions WHERE version_id = '{version_id}'"
                )
                
                # Update document metadata to remove version info
                doc_metadata = document.metadata or {}
                if "versions" in doc_metadata:
                    doc_metadata["versions"] = [
                        v for v in doc_metadata["versions"] 
                        if v.get("version_id") != version_id
                    ]
                    
                    # Update latest version if necessary
                    if doc_metadata.get("latest_version") == version.version_number:
                        remaining_versions = await self.document_repository.get_document_versions(document_id)
                        if remaining_versions:
                            doc_metadata["latest_version"] = max(v.version_number for v in remaining_versions)
                        else:
                            doc_metadata["latest_version"] = None
                    
                    # Update document metadata
                    await self.document_repository.update_document_metadata(document_id, doc_metadata)
                
                logger.info(f"Deleted version {version.version_number} for document {document_id}")
                
            except ResourceNotFoundError:
                raise
            except ValidationError:
                raise
            except Exception as e:
                logger.error(f"Failed to delete document version {document_id}/{version_id}: {str(e)}")
                raise StorageError(f"Failed to delete document version: {str(e)}")
    
    async def restore_version(self, document_id: str, version_id: str, created_by: Optional[str] = None) -> Document:
        """
        Restore a document to a previous version.
        
        Args:
            document_id: ID of the document
            version_id: ID of the version to restore
            created_by: ID of the user performing the restore
            
        Returns:
            The updated document
            
        Raises:
            ResourceNotFoundError: If the document or version does not exist
            StorageError: If the version cannot be restored
        """
        async with self.transaction_manager.locked_transaction(document_id) as session:
            try:
                # Get document to verify it exists
                document = await self.document_repository.get_document(document_id)
                
                # Get version to restore
                version = await self.get_version(document_id, version_id)
                
                # Get version content
                version_content = await self.get_version_content(document_id, version_id)
                
                # Create new version with content from old version
                new_version = await self.create_version(
                    document_id=document_id,
                    file_content=version_content,
                    created_by=created_by,
                    comment=f"Restored from version {version.version_number}",
                    metadata={
                        "restored_from": {
                            "version_id": version_id,
                            "version_number": version.version_number,
                            "created_at": version.created_at
                        }
                    }
                )
                
                # Update document file path to point to new version
                document.file_path = new_version.file_path
                document.updated_at = datetime.utcnow().isoformat()
                
                # Save updated document
                updated_document = await self.document_repository.save_document(document)
                
                logger.info(f"Restored document {document_id} to version {version.version_number}")
                return updated_document
                
            except ResourceNotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to restore document version {document_id}/{version_id}: {str(e)}")
                raise StorageError(f"Failed to restore document version: {str(e)}")
    
    async def compare_versions(self, 
                             document_id: str, 
                             version_id_1: str, 
                             version_id_2: str) -> Dict[str, Any]:
        """
        Compare two versions of a document.
        
        Args:
            document_id: ID of the document
            version_id_1: ID of the first version
            version_id_2: ID of the second version
            
        Returns:
            Comparison results
            
        Raises:
            ResourceNotFoundError: If the document or versions do not exist
            StorageError: If the versions cannot be compared
        """
        try:
            # Get document to verify it exists
            await self.document_repository.get_document(document_id)
            
            # Get versions to compare
            version1 = await self.get_version(document_id, version_id_1)
            version2 = await self.get_version(document_id, version_id_2)
            
            # Compare metadata
            metadata_diffs = {}
            if version1.metadata or version2.metadata:
                v1_meta = version1.metadata or {}
                v2_meta = version2.metadata or {}
                
                # Find added keys
                added = {k: v for k, v in v2_meta.items() if k not in v1_meta}
                
                # Find removed keys
                removed = {k: v for k, v in v1_meta.items() if k not in v2_meta}
                
                # Find changed keys
                changed = {k: {"old": v1_meta[k], "new": v2_meta[k]} 
                         for k in v1_meta 
                         if k in v2_meta and v1_meta[k] != v2_meta[k]}
                
                metadata_diffs = {
                    "added": added,
                    "removed": removed,
                    "changed": changed
                }
            
            # Build comparison results
            # Note: For a real implementation, you would need to compare the actual file contents
            # This would typically involve diff algorithms or content-specific comparison tools
            comparison = {
                "document_id": document_id,
                "version1": {
                    "version_id": version1.version_id,
                    "version_number": version1.version_number,
                    "created_at": version1.created_at,
                    "created_by": version1.created_by,
                    "comment": version1.comment,
                    "file_size": version1.file_size
                },
                "version2": {
                    "version_id": version2.version_id,
                    "version_number": version2.version_number,
                    "created_at": version2.created_at,
                    "created_by": version2.created_by,
                    "comment": version2.comment,
                    "file_size": version2.file_size
                },
                "size_difference": version2.file_size - version1.file_size,
                "metadata_differences": metadata_diffs,
                "newer_version": version1 if version1.version_number > version2.version_number else version2
            }
            
            return comparison
                
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to compare document versions {document_id}/{version_id_1}/{version_id_2}: {str(e)}")
            raise StorageError(f"Failed to compare document versions: {str(e)}")
    
    async def get_version_history(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get the version history of a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of version history entries
            
        Raises:
            ResourceNotFoundError: If the document does not exist
        """
        try:
            # Get document to verify it exists
            document = await self.document_repository.get_document(document_id)
            
            # Get all versions
            versions = await self.document_repository.get_document_versions(document_id)
            
            # Build version history
            history = []
            for version in versions:
                entry = {
                    "version_id": version.version_id,
                    "version_number": version.version_number,
                    "created_at": version.created_at,
                    "created_by": version.created_by,
                    "comment": version.comment,
                    "file_size": version.file_size,
                    "metadata": version.metadata,
                    "is_current": document.file_path == version.file_path
                }
                history.append(entry)
            
            # Sort by version number (descending)
            history.sort(key=lambda x: x["version_number"], reverse=True)
            
            return history
                
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get document version history {document_id}: {str(e)}")
            raise StorageError(f"Failed to get document version history: {str(e)}") 