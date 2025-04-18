"""
Document ownership model.

This module provides functionality for managing document ownership.
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError
from ..auth import AuthenticationService
from .database.repository import PostgreSQLDocumentRepository
from .models import Document

logger = get_logger(__name__)


class DocumentOwnershipManager:
    """Manages document ownership relations."""
    
    def __init__(self, 
                 auth_service: AuthenticationService,
                 document_repository: PostgreSQLDocumentRepository):
        """
        Initialize the document ownership manager.
        
        Args:
            auth_service: Authentication service for user validation
            document_repository: Repository for document operations
        """
        self.auth_service = auth_service
        self.document_repository = document_repository
    
    async def assign_document_to_user(self, document_id: str, user_id: str) -> Document:
        """
        Assign a document to a user.
        
        Args:
            document_id: ID of the document to assign
            user_id: ID of the user to assign the document to
            
        Returns:
            Updated document with new ownership
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            AuthorizationError: If the current user cannot perform this action
            ValidationError: If the user_id is invalid
        """
        try:
            # Validate user exists
            user = await self.auth_service.get_user_by_id(user_id)
            if not user:
                raise ValidationError(f"User {user_id} does not exist")
            
            # Get the document
            document = await self.document_repository.get_document(document_id)
            
            # Update document ownership
            document.user_id = user_id
            document.updated_at = datetime.utcnow().isoformat()
            
            # Save updated document
            updated_document = await self.document_repository.save_document(document)
            
            # Grant document permissions to the user
            await self.auth_service.grant_permission(
                user_id=user_id,
                permission="document:read:own",
                resource_id=document_id
            )
            
            await self.auth_service.grant_permission(
                user_id=user_id,
                permission="document:write:own",
                resource_id=document_id
            )
            
            await self.auth_service.grant_permission(
                user_id=user_id,
                permission="document:delete:own",
                resource_id=document_id
            )
            
            logger.info(f"Assigned document {document_id} to user {user_id}")
            return updated_document
            
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to assign document {document_id} to user {user_id}: {str(e)}")
            raise AuthorizationError(f"Failed to assign document: {str(e)}")
    
    async def transfer_document_ownership(self, 
                                         document_id: str, 
                                         from_user_id: str, 
                                         to_user_id: str) -> Document:
        """
        Transfer document ownership from one user to another.
        
        Args:
            document_id: ID of the document to transfer
            from_user_id: ID of the current document owner
            to_user_id: ID of the new document owner
            
        Returns:
            Updated document with new ownership
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            AuthorizationError: If the current user cannot perform this action
            ValidationError: If the user IDs are invalid
        """
        try:
            # Validate users exist
            from_user = await self.auth_service.get_user_by_id(from_user_id)
            if not from_user:
                raise ValidationError(f"User {from_user_id} does not exist")
                
            to_user = await self.auth_service.get_user_by_id(to_user_id)
            if not to_user:
                raise ValidationError(f"User {to_user_id} does not exist")
            
            # Get the document and verify ownership
            document = await self.document_repository.get_document(document_id)
            
            if document.user_id != from_user_id:
                raise AuthorizationError(f"User {from_user_id} does not own document {document_id}")
            
            # Update document ownership
            document.user_id = to_user_id
            document.updated_at = datetime.utcnow().isoformat()
            
            # Save updated document
            updated_document = await self.document_repository.save_document(document)
            
            # Revoke permissions from previous owner
            await self.auth_service.revoke_permission(
                user_id=from_user_id,
                permission="document:read:own",
                resource_id=document_id
            )
            
            await self.auth_service.revoke_permission(
                user_id=from_user_id,
                permission="document:write:own",
                resource_id=document_id
            )
            
            await self.auth_service.revoke_permission(
                user_id=from_user_id,
                permission="document:delete:own",
                resource_id=document_id
            )
            
            # Grant permissions to new owner
            await self.auth_service.grant_permission(
                user_id=to_user_id,
                permission="document:read:own",
                resource_id=document_id
            )
            
            await self.auth_service.grant_permission(
                user_id=to_user_id,
                permission="document:write:own",
                resource_id=document_id
            )
            
            await self.auth_service.grant_permission(
                user_id=to_user_id,
                permission="document:delete:own",
                resource_id=document_id
            )
            
            logger.info(f"Transferred document {document_id} from user {from_user_id} to user {to_user_id}")
            return updated_document
            
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except AuthorizationError as e:
            logger.error(f"Authorization error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to transfer document {document_id} ownership: {str(e)}")
            raise AuthorizationError(f"Failed to transfer document ownership: {str(e)}")
    
    async def share_document_with_user(self, 
                                     document_id: str, 
                                     owner_id: str, 
                                     shared_user_id: str,
                                     permissions: List[str] = ["read"]) -> Dict[str, Any]:
        """
        Share a document with another user.
        
        Args:
            document_id: ID of the document to share
            owner_id: ID of the document owner
            shared_user_id: ID of the user to share with
            permissions: List of permissions to grant (read, write, delete)
            
        Returns:
            Sharing metadata
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            AuthorizationError: If the current user cannot perform this action
            ValidationError: If the user IDs or permissions are invalid
        """
        try:
            # Validate permissions
            valid_permissions = ["read", "write", "delete"]
            for perm in permissions:
                if perm not in valid_permissions:
                    raise ValidationError(f"Invalid permission: {perm}")
            
            # Validate users exist
            owner = await self.auth_service.get_user_by_id(owner_id)
            if not owner:
                raise ValidationError(f"User {owner_id} does not exist")
                
            shared_user = await self.auth_service.get_user_by_id(shared_user_id)
            if not shared_user:
                raise ValidationError(f"User {shared_user_id} does not exist")
            
            # Get the document and verify ownership
            document = await self.document_repository.get_document(document_id)
            
            if document.user_id != owner_id:
                raise AuthorizationError(f"User {owner_id} does not own document {document_id}")
            
            # Generate sharing ID
            sharing_id = str(uuid.uuid4())
            
            # Grant permissions to shared user
            granted_permissions = []
            
            for perm in permissions:
                permission = f"document:{perm}:shared"
                await self.auth_service.grant_permission(
                    user_id=shared_user_id,
                    permission=permission,
                    resource_id=document_id
                )
                granted_permissions.append(permission)
            
            # Store sharing metadata in document metadata
            metadata = document.metadata or {}
            
            if "shared_with" not in metadata:
                metadata["shared_with"] = []
                
            sharing_metadata = {
                "sharing_id": sharing_id,
                "user_id": shared_user_id,
                "permissions": permissions,
                "shared_at": datetime.utcnow().isoformat(),
                "shared_by": owner_id
            }
            
            metadata["shared_with"].append(sharing_metadata)
            
            # Update document metadata
            await self.document_repository.update_document_metadata(document_id, metadata)
            
            logger.info(f"Shared document {document_id} with user {shared_user_id}")
            return {
                "document_id": document_id,
                "owner_id": owner_id,
                "shared_user_id": shared_user_id,
                "sharing_id": sharing_id,
                "permissions": permissions,
                "shared_at": sharing_metadata["shared_at"]
            }
            
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except AuthorizationError as e:
            logger.error(f"Authorization error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to share document {document_id} with user {shared_user_id}: {str(e)}")
            raise AuthorizationError(f"Failed to share document: {str(e)}")
    
    async def revoke_document_sharing(self, 
                                    document_id: str, 
                                    owner_id: str, 
                                    shared_user_id: str) -> Dict[str, Any]:
        """
        Revoke document sharing from a user.
        
        Args:
            document_id: ID of the document
            owner_id: ID of the document owner
            shared_user_id: ID of the user to revoke sharing from
            
        Returns:
            Result metadata
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            AuthorizationError: If the current user cannot perform this action
            ValidationError: If the user IDs are invalid
        """
        try:
            # Validate users exist
            owner = await self.auth_service.get_user_by_id(owner_id)
            if not owner:
                raise ValidationError(f"User {owner_id} does not exist")
            
            # Get the document and verify ownership
            document = await self.document_repository.get_document(document_id)
            
            if document.user_id != owner_id:
                raise AuthorizationError(f"User {owner_id} does not own document {document_id}")
            
            # Revoke all document permissions from shared user
            permissions = ["read", "write", "delete"]
            revoked_permissions = []
            
            for perm in permissions:
                permission = f"document:{perm}:shared"
                await self.auth_service.revoke_permission(
                    user_id=shared_user_id,
                    permission=permission,
                    resource_id=document_id
                )
                revoked_permissions.append(permission)
            
            # Update sharing metadata in document metadata
            metadata = document.metadata or {}
            
            if "shared_with" in metadata:
                # Remove sharing records for this user
                metadata["shared_with"] = [
                    sharing for sharing in metadata["shared_with"]
                    if sharing.get("user_id") != shared_user_id
                ]
                
                # Update document metadata
                await self.document_repository.update_document_metadata(document_id, metadata)
            
            logger.info(f"Revoked document {document_id} sharing from user {shared_user_id}")
            return {
                "document_id": document_id,
                "owner_id": owner_id,
                "shared_user_id": shared_user_id,
                "revoked_at": datetime.utcnow().isoformat(),
                "revoked_permissions": revoked_permissions
            }
            
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except AuthorizationError as e:
            logger.error(f"Authorization error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to revoke document {document_id} sharing from user {shared_user_id}: {str(e)}")
            raise AuthorizationError(f"Failed to revoke document sharing: {str(e)}")
    
    async def get_user_documents(self, user_id: str, include_shared: bool = False) -> List[Document]:
        """
        Get all documents owned by a user.
        
        Args:
            user_id: ID of the user
            include_shared: Whether to include documents shared with the user
            
        Returns:
            List of documents
            
        Raises:
            ValidationError: If the user ID is invalid
        """
        try:
            # Validate user exists
            user = await self.auth_service.get_user_by_id(user_id)
            if not user:
                raise ValidationError(f"User {user_id} does not exist")
            
            # Get documents owned by the user
            documents = await self.document_repository.list_documents(user_id=user_id)
            
            # If include_shared is True, also get documents shared with the user
            if include_shared:
                # Get resource IDs for which the user has document:read:shared permission
                resources = await self.auth_service.list_user_resources(
                    user_id=user_id,
                    permission="document:read:shared"
                )
                
                # Get shared documents
                for resource_id in resources:
                    try:
                        document = await self.document_repository.get_document(resource_id)
                        # Add shared flag
                        document.metadata = document.metadata or {}
                        document.metadata["is_shared"] = True
                        documents.append(document)
                    except ResourceNotFoundError:
                        # Document might have been deleted
                        continue
            
            logger.info(f"Retrieved {len(documents)} documents for user {user_id}")
            return documents
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to get documents for user {user_id}: {str(e)}")
            raise ValidationError(f"Failed to get user documents: {str(e)}") 