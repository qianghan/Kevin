"""
Document service implementation.

This module provides the main DocumentService class that orchestrates document-related operations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from app.backend.interfaces.document import IDocumentService
from app.backend.services.document.repository import DocumentRepository
from app.backend.services.document.storage import DocumentStorageService
from app.backend.services.document.versioning import DocumentVersioningService
from app.backend.services.document.access_control import DocumentAccessControl
from app.backend.services.document.audit import DocumentAuditLogger
from app.backend.services.document.security import DocumentSecurity
from app.backend.services.document.ocr import DocumentOCR
from app.backend.services.document.watermark import DocumentWatermark
from app.backend.services.document.extraction import DocumentMetadataExtractor
from app.backend.services.document.external import ExternalStorageService
from app.backend.services.document.notification import DocumentNotificationManager
from app.backend.services.document.export_service import DocumentExportService
from app.backend.utils.errors import SecurityError, StorageError, ValidationError


class DocumentService(IDocumentService):
    """Main service class for document management."""
    
    def __init__(self):
        """Initialize the document service."""
        self.repository = DocumentRepository()
        self.storage = DocumentStorageService()
        self.version_manager = DocumentVersioningService()
        self.access_control = DocumentAccessControl()
        self.audit_logger = DocumentAuditLogger()
        self.security = DocumentSecurity()
        self.ocr = DocumentOCR()
        self.watermark = DocumentWatermark()
        self.metadata_extractor = DocumentMetadataExtractor()
        self.external_storage = ExternalStorageService()
        self.notification_manager = DocumentNotificationManager()
        self.export_service = DocumentExportService()
        self._config: Dict[str, Any] = {}
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the document service.
        
        Args:
            config: Configuration dictionary
        """
        self._config = config
        # Configure sub-services
        self.repository.configure(config.get("repository", {}))
        self.storage.configure(config.get("storage", {}))
        self.version_manager.configure(config.get("versioning", {}))
        self.access_control.configure(config.get("access_control", {}))
        self.audit_logger.configure(config.get("audit", {}))
        self.security.configure(config.get("security", {}))
        self.ocr.configure(config.get("ocr", {}))
        self.watermark.configure(config.get("watermark", {}))
        self.metadata_extractor.configure(config.get("metadata", {}))
        self.external_storage.configure(config.get("external_storage", {}))
        self.notification_manager.configure(config.get("notification", {}))
        self.export_service.configure(config.get("export", {}))
    
    async def initialize(self) -> None:
        """Initialize the document service and its components."""
        await self.repository.initialize()
        await self.storage.initialize()
        await self.version_manager.initialize()
        await self.access_control.initialize()
        await self.audit_logger.initialize()
        await self.security.initialize()
        await self.ocr.initialize()
        await self.watermark.initialize()
        await self.metadata_extractor.initialize()
        await self.external_storage.initialize()
        await self.notification_manager.initialize()
        await self.export_service.initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the document service and its components."""
        await self.repository.shutdown()
        await self.storage.shutdown()
        await self.version_manager.shutdown()
        await self.access_control.shutdown()
        await self.audit_logger.shutdown()
        await self.security.shutdown()
        await self.ocr.shutdown()
        await self.watermark.shutdown()
        await self.metadata_extractor.shutdown()
        await self.external_storage.shutdown()
        await self.notification_manager.shutdown()
        await self.export_service.shutdown()
    
    async def create_document(self, 
                            user_id: str,
                            file_path: str,
                            metadata: Optional[Dict[str, Any]] = None,
                            tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new document.
        
        Args:
            user_id: ID of the user creating the document
            file_path: Path to the document file
            metadata: Optional document metadata
            tags: Optional list of tags for the document
            
        Returns:
            Document information
            
        Raises:
            SecurityError: If the user is not authorized
            StorageError: If the document cannot be stored
            ValidationError: If the document is invalid
        """
        # Check user authorization
        if not await self.access_control.can_create_document(user_id):
            raise SecurityError("User not authorized to create documents")
        
        # Validate document
        if not await self.security.validate_document(file_path):
            raise ValidationError("Document validation failed")
        
        # Extract metadata
        if metadata is None:
            metadata = {}
        extracted_metadata = await self.metadata_extractor.extract_metadata(file_path)
        metadata.update(extracted_metadata)
        
        # Store document
        storage_info = await self.storage.save_document(file_path, metadata)
        
        # Create document record
        document = await self.repository.create_document(
            user_id=user_id,
            storage_info=storage_info,
            metadata=metadata,
            tags=tags
        )
        
        # Log audit event
        await self.audit_logger.log_document_creation(
            user_id=user_id,
            document_id=document["document_id"],
            metadata=metadata
        )
        
        # Notify about document creation
        await self.notification_manager.notify_document_created(
            user_id=user_id,
            document_id=document["document_id"]
        )
        
        return document
    
    async def get_document(self, 
                         user_id: str,
                         document_id: str) -> Dict[str, Any]:
        """
        Get a document by ID.
        
        Args:
            user_id: ID of the user requesting the document
            document_id: ID of the document to get
            
        Returns:
            Document information
            
        Raises:
            SecurityError: If the user is not authorized
            StorageError: If the document cannot be retrieved
        """
        # Check user authorization
        if not await self.access_control.can_access_document(user_id, document_id):
            raise SecurityError("User not authorized to access document")
        
        # Get document record
        document = await self.repository.get_document(document_id)
        
        # Get document content
        content = await self.storage.get_document(document["storage_path"])
        
        # Log audit event
        await self.audit_logger.log_document_access(
            user_id=user_id,
            document_id=document_id
        )
        
        return {
            **document,
            "content": content
        }
    
    async def update_document(self,
                            user_id: str,
                            document_id: str,
                            updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a document.
        
        Args:
            user_id: ID of the user updating the document
            document_id: ID of the document to update
            updates: Document updates
            
        Returns:
            Updated document information
            
        Raises:
            SecurityError: If the user is not authorized
            StorageError: If the document cannot be updated
        """
        # Check user authorization
        if not await self.access_control.can_update_document(user_id, document_id):
            raise SecurityError("User not authorized to update document")
        
        # Create new version
        version = await self.version_manager.create_version(
            document_id=document_id,
            user_id=user_id,
            changes=updates
        )
        
        # Update document record
        document = await self.repository.update_document(
            document_id=document_id,
            updates=updates,
            version_id=version["version_id"]
        )
        
        # Log audit event
        await self.audit_logger.log_document_update(
            user_id=user_id,
            document_id=document_id,
            version_id=version["version_id"],
            changes=updates
        )
        
        # Notify about document update
        await self.notification_manager.notify_document_updated(
            user_id=user_id,
            document_id=document_id,
            version_id=version["version_id"]
        )
        
        return document
    
    async def delete_document(self,
                            user_id: str,
                            document_id: str) -> None:
        """
        Delete a document.
        
        Args:
            user_id: ID of the user deleting the document
            document_id: ID of the document to delete
            
        Raises:
            SecurityError: If the user is not authorized
            StorageError: If the document cannot be deleted
        """
        # Check user authorization
        if not await self.access_control.can_delete_document(user_id, document_id):
            raise SecurityError("User not authorized to delete document")
        
        # Get document record
        document = await self.repository.get_document(document_id)
        
        # Delete document from storage
        await self.storage.delete_document(document["storage_path"])
        
        # Delete document record
        await self.repository.delete_document(document_id)
        
        # Log audit event
        await self.audit_logger.log_document_deletion(
            user_id=user_id,
            document_id=document_id
        )
        
        # Notify about document deletion
        await self.notification_manager.notify_document_deleted(
            user_id=user_id,
            document_id=document_id
        )
    
    async def list_documents(self,
                           user_id: str,
                           filters: Optional[Dict[str, Any]] = None,
                           page: int = 1,
                           page_size: int = 10) -> Dict[str, Any]:
        """
        List documents for a user.
        
        Args:
            user_id: ID of the user
            filters: Optional filters to apply
            page: Page number
            page_size: Number of items per page
            
        Returns:
            Paginated list of documents
        """
        # Apply access control filters
        if filters is None:
            filters = {}
        filters["user_id"] = user_id
        
        # Get documents
        documents = await self.repository.list_documents(
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        return documents
    
    async def export_document(self,
                            user_id: str,
                            document_id: str,
                            format: str = "pdf") -> bytes:
        """
        Export a document in the specified format.
        
        Args:
            user_id: ID of the user exporting the document
            document_id: ID of the document to export
            format: Export format (pdf, html, txt)
            
        Returns:
            Exported document content
            
        Raises:
            SecurityError: If the user is not authorized
            StorageError: If the document cannot be exported
        """
        # Check user authorization
        if not await self.access_control.can_export_document(user_id, document_id):
            raise SecurityError("User not authorized to export document")
        
        # Get document
        document = await self.get_document(user_id, document_id)
        
        # Export document
        content = await self.export_service.export_document(
            document=document,
            format=format
        )
        
        # Log audit event
        await self.audit_logger.log_document_export(
            user_id=user_id,
            document_id=document_id,
            format=format
        )
        
        return content
    
    async def share_document(self,
                           user_id: str,
                           document_id: str,
                           recipient_id: str,
                           permissions: List[str]) -> Dict[str, Any]:
        """
        Share a document with another user.
        
        Args:
            user_id: ID of the user sharing the document
            document_id: ID of the document to share
            recipient_id: ID of the recipient user
            permissions: List of permissions to grant
            
        Returns:
            Sharing information
            
        Raises:
            SecurityError: If the user is not authorized
        """
        # Check user authorization
        if not await self.access_control.can_share_document(user_id, document_id):
            raise SecurityError("User not authorized to share document")
        
        # Share document
        sharing = await self.access_control.share_document(
            document_id=document_id,
            recipient_id=recipient_id,
            permissions=permissions
        )
        
        # Log audit event
        await self.audit_logger.log_document_sharing(
            user_id=user_id,
            document_id=document_id,
            recipient_id=recipient_id,
            permissions=permissions
        )
        
        # Notify recipient
        await self.notification_manager.notify_document_shared(
            user_id=recipient_id,
            document_id=document_id,
            shared_by=user_id,
            permissions=permissions
        )
        
        return sharing 