"""
Document access control module.

This module provides functionality for controlling access to documents.
"""

from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
import uuid
import json
from enum import Enum
import logging
from sqlalchemy.orm import Session

from ..auth import AuthenticationService
from ...utils.errors import AuthorizationError, ValidationError, ResourceNotFoundError, SecurityError
from ...utils.logging import get_logger
from .models import Document
from .exceptions import AccessControlError

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Document permission types."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"
    ADMIN = "admin"  # Full control including permission management


class AccessLevel(Enum):
    """Document access levels."""
    NONE = "none"        # No access
    VIEWER = "viewer"    # Read only
    EDITOR = "editor"    # Read and write
    MANAGER = "manager"  # Read, write, delete, share
    OWNER = "owner"      # Full access


# Map access levels to permissions
ACCESS_LEVEL_PERMISSIONS = {
    AccessLevel.NONE: set(),
    AccessLevel.VIEWER: {Permission.READ},
    AccessLevel.EDITOR: {Permission.READ, Permission.WRITE},
    AccessLevel.MANAGER: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.SHARE},
    AccessLevel.OWNER: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.SHARE, Permission.ADMIN}
}


class DocumentPermissionEntry:
    """Represents a permission entry for a document."""
    
    def __init__(self, 
                 user_id: str,
                 document_id: str,
                 access_level: AccessLevel,
                 granted_by: Optional[str] = None,
                 granted_at: Optional[datetime] = None,
                 expires_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a document permission entry.
        
        Args:
            user_id: ID of the user with the permission
            document_id: ID of the document
            access_level: Access level for the user
            granted_by: ID of the user who granted the permission
            granted_at: When the permission was granted
            expires_at: When the permission expires
            metadata: Additional metadata
        """
        self.user_id = user_id
        self.document_id = document_id
        self.access_level = access_level
        self.granted_by = granted_by
        self.granted_at = granted_at or datetime.utcnow()
        self.expires_at = expires_at
        self.metadata = metadata or {}
    
    def is_expired(self) -> bool:
        """Check if the permission has expired."""
        return self.expires_at is not None and datetime.utcnow() > self.expires_at
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if this entry grants a specific permission."""
        if self.is_expired():
            return False
        
        # Get permissions for this access level
        permissions = ACCESS_LEVEL_PERMISSIONS.get(self.access_level, set())
        
        # Check if requested permission is included
        return permission in permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage and serialization."""
        return {
            "user_id": self.user_id,
            "document_id": self.document_id,
            "access_level": self.access_level.value,
            "granted_by": self.granted_by,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'DocumentPermissionEntry':
        """Create a permission entry from a dictionary."""
        access_level = AccessLevel(data.get("access_level"))
        granted_at = datetime.fromisoformat(data.get("granted_at")) if data.get("granted_at") else None
        expires_at = datetime.fromisoformat(data.get("expires_at")) if data.get("expires_at") else None
        
        return DocumentPermissionEntry(
            user_id=data.get("user_id"),
            document_id=data.get("document_id"),
            access_level=access_level,
            granted_by=data.get("granted_by"),
            granted_at=granted_at,
            expires_at=expires_at,
            metadata=data.get("metadata", {})
        )


class AuditLogEntry:
    """Represents an audit log entry for document operations."""
    
    def __init__(self,
                 user_id: str,
                 document_id: str,
                 action: str,
                 timestamp: Optional[datetime] = None,
                 details: Optional[Dict[str, Any]] = None,
                 success: bool = True,
                 ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None):
        """
        Initialize an audit log entry.
        
        Args:
            user_id: ID of the user performing the action
            document_id: ID of the document
            action: Action performed (e.g., "read", "write", "share")
            timestamp: When the action occurred
            details: Additional details about the action
            success: Whether the action was successful
            ip_address: IP address of the user
            user_agent: User agent of the client
        """
        self.log_id = str(uuid.uuid4())
        self.user_id = user_id
        self.document_id = document_id
        self.action = action
        self.timestamp = timestamp or datetime.utcnow()
        self.details = details or {}
        self.success = success
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage and serialization."""
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "success": self.success,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AuditLogEntry':
        """Create an audit log entry from a dictionary."""
        timestamp = datetime.fromisoformat(data.get("timestamp")) if data.get("timestamp") else None
        
        entry = AuditLogEntry(
            user_id=data.get("user_id"),
            document_id=data.get("document_id"),
            action=data.get("action"),
            timestamp=timestamp,
            details=data.get("details", {}),
            success=data.get("success", True),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent")
        )
        entry.log_id = data.get("log_id", entry.log_id)
        return entry


class DocumentAccessControl:
    """Controls access to documents."""
    
    def __init__(self, db_session: Session, auth_service: AuthenticationService):
        """
        Initialize the document access control.
        
        Args:
            db_session: Database session
            auth_service: Authentication service for authorization checks
        """
        self.db_session = db_session
        self.auth_service = auth_service
        
        # In-memory storage if no database repository is provided
        self._permissions: Dict[str, Dict[str, DocumentPermissionEntry]] = {}  # document_id -> {user_id -> entry}
        self._audit_logs: List[AuditLogEntry] = []
    
    async def initialize(self) -> None:
        """Initialize the document access control system."""
        # Load permissions from database if repository is available
        if self.db_session:
            try:
                await self.db_session.initialize()
                # Load permissions would happen here
            except Exception as e:
                logger.error(f"Failed to initialize document access control: {str(e)}")
        
        logger.info("Initialized document access control")
    
    async def authorize_document_action(self, 
                                      user_id: str, 
                                      action: str, 
                                      document_id: Optional[str] = None, 
                                      profile_id: Optional[str] = None,
                                      context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Authorize a document action.
        
        Args:
            user_id: ID of the user attempting the action
            action: Action to authorize (read, write, delete, share)
            document_id: Optional document ID for document-specific actions
            profile_id: Optional profile ID for profile-specific document actions
            context: Optional context information for audit logging
            
        Returns:
            True if authorized, False otherwise
            
        Raises:
            AuthorizationError: If authorization fails
        """
        # Map action to permission
        try:
            permission = Permission(action)
        except ValueError:
            logger.error(f"Invalid document action: {action}")
            return False
        
        authorized = False
        
        # For document-specific actions
        if document_id:
            # Check document-specific permissions first
            authorized = await self._check_document_permission(
                user_id=user_id,
                document_id=document_id,
                permission=permission
            )
            
            # If not authorized by document permissions, check if owner via general auth
            if not authorized:
                scope = "own"  # Default scope
                auth_permission = f"document:{action}:{scope}"
                
                authorized = await self.auth_service.authorize(
                    user_id=user_id,
                    permission=auth_permission,
                    resource_id=document_id
                )
        
        # For profile documents
        elif profile_id:
            # First check if user has access to the profile
            profile_permission = f"profile:read:own"
            authorized = await self.auth_service.authorize(
                user_id=user_id,
                permission=profile_permission,
                resource_id=profile_id
            )
            
            # Then check document permission if profile access is granted
            if authorized:
                auth_permission = f"document:{action}:own"
                authorized = await self.auth_service.authorize(
                    user_id=user_id,
                    permission=auth_permission
                )
        
        # For general document actions
        else:
            auth_permission = f"document:{action}:own"
            authorized = await self.auth_service.authorize(
                user_id=user_id,
                permission=auth_permission
            )
        
        # Log this authorization check
        await self._log_access_attempt(
            user_id=user_id,
            document_id=document_id or "general",
            action=f"authorize_{action}",
            success=authorized,
            details={
                "profile_id": profile_id,
                "context": context or {}
            }
        )
        
        if not authorized:
            logger.warning(f"User {user_id} not authorized for {action} on document {document_id or 'general'}")
        
        return authorized
    
    async def _check_document_permission(self, 
                                     user_id: str, 
                                     document_id: str, 
                                     permission: Permission) -> bool:
        """
        Check if a user has a specific permission for a document.
        
        Args:
            user_id: ID of the user
            document_id: ID of the document
            permission: Permission to check
            
        Returns:
            True if the user has the permission, False otherwise
        """
        # Check in database repository if available
        if self.db_session:
            try:
                # This would query the database for permissions
                return await self.db_session.query(Document).filter(Document.id == document_id).first().access_control.get(user_id)
            except Exception as e:
                logger.error(f"Database error checking document permission: {str(e)}")
                # Fall back to in-memory storage
        
        # Check in-memory permissions
        document_permissions = self._permissions.get(document_id, {})
        permission_entry = document_permissions.get(user_id)
        
        if permission_entry and permission_entry.has_permission(permission):
            return True
        
        return False
    
    async def set_document_permissions(self, 
                                    granter_user_id: str, 
                                    document_id: str, 
                                    user_id: str, 
                                    access_level: AccessLevel,
                                    expires_at: Optional[datetime] = None,
                                    metadata: Optional[Dict[str, Any]] = None) -> DocumentPermissionEntry:
        """
        Set permissions for a user on a document.
        
        Args:
            granter_user_id: ID of the user granting the permission
            document_id: ID of the document
            user_id: ID of the user to grant permission to
            access_level: Access level to grant
            expires_at: When the permission expires
            metadata: Additional metadata for the permission
            
        Returns:
            The created permission entry
            
        Raises:
            AuthorizationError: If the granter doesn't have permission to share
            ValidationError: If parameters are invalid
        """
        # Verify granter has share permission
        has_permission = await self._check_document_permission(
            user_id=granter_user_id,
            document_id=document_id,
            permission=Permission.SHARE
        )
        
        # If not found in document permissions, check if owner via general auth
        if not has_permission:
            has_permission = await self.auth_service.authorize(
                user_id=granter_user_id,
                permission="document:share:own",
                resource_id=document_id
            )
        
        if not has_permission:
            await self._log_access_attempt(
                user_id=granter_user_id,
                document_id=document_id,
                action="set_permissions",
                success=False,
                details={
                    "target_user_id": user_id,
                    "access_level": access_level.value
                }
            )
            raise AuthorizationError(f"User {granter_user_id} does not have permission to share document {document_id}")
        
        # Create permission entry
        entry = DocumentPermissionEntry(
            user_id=user_id,
            document_id=document_id,
            access_level=access_level,
            granted_by=granter_user_id,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        # Store in database if available
        if self.db_session:
            try:
                document = await self.db_session.get(Document, document_id)
                if not document:
                    raise AccessControlError(f"Document {document_id} not found")
                
                if not hasattr(document, 'access_control'):
                    document.access_control = {}
                
                document.access_control[user_id] = {
                    'level': access_level.value,
                    'granted_at': datetime.utcnow()
                }
                
                await self.db_session.commit()
            except Exception as e:
                logger.error(f"Database error saving document permission: {str(e)}")
                # Fall back to in-memory storage
        
        # Store in memory
        if document_id not in self._permissions:
            self._permissions[document_id] = {}
        
        self._permissions[document_id][user_id] = entry
        
        # Log the permission change
        await self._log_access_attempt(
            user_id=granter_user_id,
            document_id=document_id,
            action="set_permissions",
            success=True,
            details={
                "target_user_id": user_id,
                "access_level": access_level.value,
                "expires_at": expires_at.isoformat() if expires_at else None
            }
        )
        
        return entry
    
    async def get_document_permissions(self, 
                                    requester_user_id: str, 
                                    document_id: str) -> List[DocumentPermissionEntry]:
        """
        Get all permissions for a document.
        
        Args:
            requester_user_id: ID of the user requesting permissions
            document_id: ID of the document
            
        Returns:
            List of permission entries
            
        Raises:
            AuthorizationError: If requester doesn't have admin permission
        """
        # Verify requester has admin permission
        has_permission = await self._check_document_permission(
            user_id=requester_user_id,
            document_id=document_id,
            permission=Permission.ADMIN
        )
        
        # If not found in document permissions, check if owner via general auth
        if not has_permission:
            has_permission = await self.auth_service.authorize(
                user_id=requester_user_id,
                permission="document:admin:own",
                resource_id=document_id
            )
        
        if not has_permission:
            await self._log_access_attempt(
                user_id=requester_user_id,
                document_id=document_id,
                action="get_permissions",
                success=False
            )
            raise AuthorizationError(f"User {requester_user_id} does not have permission to view all permissions for document {document_id}")
        
        # Get from database if available
        if self.db_session:
            try:
                document = await self.db_session.get(Document, document_id)
                if not document:
                    raise AccessControlError(f"Document {document_id} not found")
                
                permissions = [DocumentPermissionEntry(
                    user_id=user_id,
                    document_id=document_id,
                    access_level=AccessLevel(access_control['level']),
                    granted_by=access_control.get('granted_by'),
                    granted_at=access_control.get('granted_at'),
                    expires_at=access_control.get('expires_at'),
                    metadata=access_control.get('metadata', {})
                ) for user_id, access_control in document.access_control.items()]
                
                # Log the access
                await self._log_access_attempt(
                    user_id=requester_user_id,
                    document_id=document_id,
                    action="get_permissions",
                    success=True,
                    details={"permission_count": len(permissions)}
                )
                
                return permissions
            except Exception as e:
                logger.error(f"Database error getting document permissions: {str(e)}")
                # Fall back to in-memory storage
        
        # Get from memory
        document_permissions = self._permissions.get(document_id, {})
        permissions = list(document_permissions.values())
        
        # Log the access
        await self._log_access_attempt(
            user_id=requester_user_id,
            document_id=document_id,
            action="get_permissions",
            success=True,
            details={"permission_count": len(permissions)}
        )
        
        return permissions
    
    async def remove_document_permission(self, 
                                       remover_user_id: str, 
                                       document_id: str, 
                                       user_id: str) -> bool:
        """
        Remove permissions for a user on a document.
        
        Args:
            remover_user_id: ID of the user removing the permission
            document_id: ID of the document
            user_id: ID of the user to remove permission from
            
        Returns:
            True if permission was removed, False if not found
            
        Raises:
            AuthorizationError: If remover doesn't have admin permission
        """
        # Verify remover has admin permission
        has_permission = await self._check_document_permission(
            user_id=remover_user_id,
            document_id=document_id,
            permission=Permission.ADMIN
        )
        
        # If not found in document permissions, check if owner via general auth
        if not has_permission:
            has_permission = await self.auth_service.authorize(
                user_id=remover_user_id,
                permission="document:admin:own",
                resource_id=document_id
            )
        
        if not has_permission:
            await self._log_access_attempt(
                user_id=remover_user_id,
                document_id=document_id,
                action="remove_permission",
                success=False,
                details={"target_user_id": user_id}
            )
            raise AuthorizationError(f"User {remover_user_id} does not have permission to remove access for document {document_id}")
        
        # Remove from database if available
        if self.db_session:
            try:
                document = await self.db_session.get(Document, document_id)
                if not document:
                    raise AccessControlError(f"Document {document_id} not found")
                
                if user_id in document.access_control:
                    del document.access_control[user_id]
                
                await self.db_session.commit()
                
                # Log the removal
                await self._log_access_attempt(
                    user_id=remover_user_id,
                    document_id=document_id,
                    action="remove_permission",
                    success=True,
                    details={"target_user_id": user_id}
                )
                
                # Also remove from memory if successful
                if document_id in self._permissions and user_id in self._permissions[document_id]:
                    del self._permissions[document_id][user_id]
                
                return True
            except Exception as e:
                logger.error(f"Database error removing document permission: {str(e)}")
                # Fall back to in-memory storage
        
        # Remove from memory
        removed = False
        if document_id in self._permissions and user_id in self._permissions[document_id]:
            del self._permissions[document_id][user_id]
            removed = True
        
        # Log the removal
        await self._log_access_attempt(
            user_id=remover_user_id,
            document_id=document_id,
            action="remove_permission",
            success=removed,
            details={"target_user_id": user_id}
        )
        
        return removed
    
    async def share_document(self, 
                         sharer_user_id: str, 
                         document_id: str, 
                         user_ids: List[str], 
                         access_level: AccessLevel,
                         message: Optional[str] = None,
                         expires_at: Optional[datetime] = None) -> List[Tuple[str, bool]]:
        """
        Share a document with multiple users.
        
        Args:
            sharer_user_id: ID of the user sharing the document
            document_id: ID of the document to share
            user_ids: List of user IDs to share with
            access_level: Access level to grant
            message: Optional message to include with the share
            expires_at: When the permissions expire
            
        Returns:
            List of (user_id, success) tuples
            
        Raises:
            AuthorizationError: If sharer doesn't have share permission
        """
        # Verify sharer has share permission
        has_permission = await self._check_document_permission(
            user_id=sharer_user_id,
            document_id=document_id,
            permission=Permission.SHARE
        )
        
        # If not found in document permissions, check if owner via general auth
        if not has_permission:
            has_permission = await self.auth_service.authorize(
                user_id=sharer_user_id,
                permission="document:share:own",
                resource_id=document_id
            )
        
        if not has_permission:
            await self._log_access_attempt(
                user_id=sharer_user_id,
                document_id=document_id,
                action="share_document",
                success=False,
                details={
                    "target_users": user_ids,
                    "access_level": access_level.value
                }
            )
            raise AuthorizationError(f"User {sharer_user_id} does not have permission to share document {document_id}")
        
        # Share with each user
        results = []
        for user_id in user_ids:
            try:
                # Prepare metadata with the share message
                metadata = {"share_message": message} if message else {}
                
                # Set permission for the user
                await self.set_document_permissions(
                    granter_user_id=sharer_user_id,
                    document_id=document_id,
                    user_id=user_id,
                    access_level=access_level,
                    expires_at=expires_at,
                    metadata=metadata
                )
                
                results.append((user_id, True))
            except Exception as e:
                logger.error(f"Error sharing document {document_id} with user {user_id}: {str(e)}")
                results.append((user_id, False))
        
        # Log the share
        await self._log_access_attempt(
            user_id=sharer_user_id,
            document_id=document_id,
            action="share_document",
            success=any(success for _, success in results),
            details={
                "target_users": user_ids,
                "access_level": access_level.value,
                "results": dict(results)
            }
        )
        
        return results
    
    async def filter_accessible_documents(self, 
                                       user_id: str, 
                                       documents: List[Dict[str, Any]],
                                       permission: Permission = Permission.READ) -> List[Dict[str, Any]]:
        """
        Filter a list of documents to only those accessible by the user.
        
        Args:
            user_id: ID of the user
            documents: List of document dictionaries
            permission: Permission required (default: READ)
            
        Returns:
            Filtered list of documents
        """
        authorized_documents = []
        
        for document in documents:
            document_id = document.get("document_id")
            
            if not document_id:
                continue
            
            try:
                # Check if user has required permission
                has_permission = await self._check_document_permission(
                    user_id=user_id,
                    document_id=document_id,
                    permission=permission
                )
                
                # If not found in document permissions, check if owner via general auth
                if not has_permission:
                    auth_permission = f"document:{permission.value}:own"
                    has_permission = await self.auth_service.authorize(
                        user_id=user_id,
                        permission=auth_permission,
                        resource_id=document_id
                    )
                
                if has_permission:
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
        # Check if user has ADMIN permission through document permissions
        has_admin = await self._check_document_permission(
            user_id=user_id,
            document_id=document_id,
            permission=Permission.ADMIN
        )
        
        if has_admin:
            return True
        
        # Check ownership through general auth
        return await self.auth_service.authorize(
            user_id=user_id,
            permission="document:admin:own",
            resource_id=document_id
        )
    
    async def _log_access_attempt(self, 
                             user_id: str, 
                             document_id: str, 
                             action: str, 
                             success: bool,
                             details: Optional[Dict[str, Any]] = None,
                             ip_address: Optional[str] = None,
                             user_agent: Optional[str] = None) -> AuditLogEntry:
        """
        Log an access attempt for audit purposes.
        
        Args:
            user_id: ID of the user attempting access
            document_id: ID of the document
            action: Action attempted
            success: Whether the access was successful
            details: Additional details about the access
            ip_address: IP address of the user
            user_agent: User agent of the client
            
        Returns:
            The created audit log entry
        """
        # Create audit log entry
        entry = AuditLogEntry(
            user_id=user_id,
            document_id=document_id,
            action=action,
            timestamp=datetime.utcnow(),
            details=details or {},
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store in database if available
        if self.db_session:
            try:
                await self.db_session.add(entry)
                await self.db_session.commit()
            except Exception as e:
                logger.error(f"Database error saving audit log: {str(e)}")
                # Fall back to in-memory storage
        
        # Store in memory
        self._audit_logs.append(entry)
        
        # Limit in-memory audit logs to last 1000 entries
        if len(self._audit_logs) > 1000:
            self._audit_logs = self._audit_logs[-1000:]
        
        return entry
    
    async def get_audit_logs(self, 
                         requester_user_id: str,
                         document_id: Optional[str] = None,
                         user_id: Optional[str] = None,
                         action: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[AuditLogEntry]:
        """
        Get audit logs with filtering.
        
        Args:
            requester_user_id: ID of the user requesting logs
            document_id: Optional document ID to filter by
            user_id: Optional user ID to filter by
            action: Optional action to filter by
            start_time: Optional start time for logs
            end_time: Optional end time for logs
            limit: Maximum number of logs to return
            offset: Offset for pagination
            
        Returns:
            List of audit log entries
            
        Raises:
            AuthorizationError: If requester doesn't have permission
        """
        # Verify requester has permission to view audit logs
        if document_id:
            # For document-specific logs, need admin permission for that document
            has_permission = await self._check_document_permission(
                user_id=requester_user_id,
                document_id=document_id,
                permission=Permission.ADMIN
            )
            
            # If not found in document permissions, check if owner via general auth
            if not has_permission:
                has_permission = await self.auth_service.authorize(
                    user_id=requester_user_id,
                    permission="document:admin:own",
                    resource_id=document_id
                )
        else:
            # For general audit logs, need system admin permission
            has_permission = await self.auth_service.authorize(
                user_id=requester_user_id,
                permission="system:audit_logs:read"
            )
        
        if not has_permission:
            logger.warning(f"User {requester_user_id} not authorized to view audit logs")
            return []
        
        # Get from database if available
        if self.db_session:
            try:
                query = self.db_session.query(AuditLogEntry)
                
                if document_id:
                    query = query.filter(AuditLogEntry.document_id == document_id)
                
                if user_id:
                    query = query.filter(AuditLogEntry.user_id == user_id)
                
                if action:
                    query = query.filter(AuditLogEntry.action == action)
                
                if start_time:
                    query = query.filter(AuditLogEntry.timestamp >= start_time)
                
                if end_time:
                    query = query.filter(AuditLogEntry.timestamp <= end_time)
                
                query = query.order_by(AuditLogEntry.timestamp.desc()).limit(limit).offset(offset)
                
                return await query.all()
            except Exception as e:
                logger.error(f"Database error getting audit logs: {str(e)}")
                # Fall back to in-memory storage
        
        # Filter in-memory logs
        filtered_logs = self._audit_logs
        
        if document_id:
            filtered_logs = [log for log in filtered_logs if log.document_id == document_id]
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        
        if action:
            filtered_logs = [log for log in filtered_logs if log.action == action]
        
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
        
        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda log: log.timestamp, reverse=True)
        
        # Apply pagination
        paginated_logs = filtered_logs[offset:offset + limit]
        
        return paginated_logs
    
    async def grant_access(self, document_id: str, user_id: str, permission_level: str = "read") -> None:
        """
        Grant access to a document for a specific user.
        
        Args:
            document_id: ID of the document
            user_id: ID of the user to grant access to
            permission_level: Level of permission to grant (read, write, admin)
            
        Raises:
            SecurityError: If access cannot be granted
            AccessControlError: If document or user does not exist
        """
        try:
            document = await self.db_session.get(Document, document_id)
            if not document:
                raise AccessControlError(f"Document {document_id} not found")
                
            # Verify user exists through auth service
            if not await self.auth_service.user_exists(user_id):
                raise AccessControlError(f"User {user_id} not found")
                
            # Add permission to document's access control list
            if not hasattr(document, 'access_control'):
                document.access_control = {}
            
            document.access_control[user_id] = {
                'level': permission_level,
                'granted_at': datetime.utcnow()
            }
            
            await self.db_session.commit()
            logger.info(f"Granted {permission_level} access to document {document_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to grant access: {str(e)}")
            raise SecurityError(f"Failed to grant access: {str(e)}") 