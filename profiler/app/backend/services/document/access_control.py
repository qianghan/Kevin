"""
Document access control module.

This module provides functionality for controlling access to documents.
"""

from typing import Dict, Any, Optional, List

from ..auth import AuthenticationService
from ...utils.errors import AuthorizationError
from ...utils.logging import get_logger

logger = get_logger(__name__)


class DocumentAccessControl:
    """Controls access to documents."""
    
    def __init__(self, auth_service: AuthenticationService):
        """
        Initialize the document access control.
        
        Args:
            auth_service: Authentication service for authorization checks
        """
        self.auth_service = auth_service
    
    async def authorize_document_action(self, user_id: str, action: str, 
                                      document_id: Optional[str] = None, 
                                      profile_id: Optional[str] = None) -> bool:
        """
        Authorize a document action.
        
        Args:
            user_id: ID of the user attempting the action
            action: Action to authorize (read, write, delete)
            document_id: Optional document ID for document-specific actions
            profile_id: Optional profile ID for profile-specific document actions
            
        Returns:
            True if authorized, False otherwise
            
        Raises:
            AuthorizationError: If authorization fails
        """
        # Map action to permission format
        if action not in ["read", "write", "delete", "list"]:
            logger.error(f"Invalid document action: {action}")
            return False
        
        # Construct permission string
        permission = f"document:{action}"
        
        # For document-specific actions
        if document_id:
            scope = "own"  # Default scope
            permission = f"{permission}:{scope}"
            
            # Check authorization
            is_authorized = await self.auth_service.authorize(
                user_id=user_id,
                permission=permission,
                resource_id=document_id
            )
            
            if not is_authorized:
                logger.warning(f"User {user_id} not authorized for {permission} on document {document_id}")
                return False
                
            return True
        
        # For profile documents
        elif profile_id:
            # First check if user has access to the profile
            profile_permission = f"profile:read:own"
            is_authorized = await self.auth_service.authorize(
                user_id=user_id,
                permission=profile_permission,
                resource_id=profile_id
            )
            
            if not is_authorized:
                logger.warning(f"User {user_id} not authorized for {profile_permission} on profile {profile_id}")
                return False
            
            # Then check document permission
            permission = f"{permission}:own"
            is_authorized = await self.auth_service.authorize(
                user_id=user_id,
                permission=permission
            )
            
            if not is_authorized:
                logger.warning(f"User {user_id} not authorized for {permission} on profile {profile_id}")
                return False
                
            return True
            
        # For general document actions
        else:
            permission = f"{permission}:own"
            is_authorized = await self.auth_service.authorize(
                user_id=user_id,
                permission=permission
            )
            
            if not is_authorized:
                logger.warning(f"User {user_id} not authorized for {permission}")
                return False
                
            return True
    
    async def filter_accessible_documents(self, user_id: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter a list of documents to only those accessible by the user.
        
        Args:
            user_id: ID of the user
            documents: List of document dictionaries
            
        Returns:
            Filtered list of documents
        """
        authorized_documents = []
        
        for document in documents:
            document_id = document.get("document_id")
            
            if not document_id:
                continue
                
            try:
                # Check if user has read access
                is_authorized = await self.authorize_document_action(
                    user_id=user_id,
                    action="read",
                    document_id=document_id
                )
                
                if is_authorized:
                    authorized_documents.append(document)
                    
            except Exception as e:
                logger.error(f"Error authorizing document access: {str(e)}")
                # Skip this document
                continue
                
        return authorized_documents
    
    async def check_document_ownership(self, user_id: str, document_id: str) -> bool:
        """
        Check if a user owns a document.
        
        Args:
            user_id: ID of the user
            document_id: ID of the document
            
        Returns:
            True if the user owns the document, False otherwise
        """
        return await self.auth_service.authorize(
            user_id=user_id,
            permission="document:read:own",
            resource_id=document_id
        ) 