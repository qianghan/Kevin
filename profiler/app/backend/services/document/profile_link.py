"""
Document-profile linking service.

This module provides functionality for linking documents to user profiles,
enabling profile-based document organization and recommendations.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Union
from enum import Enum
from datetime import datetime
import uuid

from ...utils.logging import get_logger
from ...utils.errors import ValidationError, ResourceNotFoundError

logger = get_logger(__name__)


class LinkType(Enum):
    """Types of links between documents and profiles."""
    OWNED = "owned"               # Document created/owned by profile
    REFERENCED = "referenced"     # Document referenced by profile
    SHARED = "shared"             # Document shared with profile
    RECOMMENDATION = "recommendation"  # Document recommended for profile
    GENERATED = "generated"       # Document generated from profile data
    CUSTOM = "custom"             # Custom relationship type


class ProfileDocumentLink:
    """Represents a link between a document and a profile."""
    
    def __init__(self,
                 document_id: str,
                 profile_id: str,
                 user_id: str,
                 link_type: LinkType,
                 created_at: Optional[datetime] = None,
                 expires_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 link_id: Optional[str] = None):
        """
        Initialize a profile-document link.
        
        Args:
            document_id: ID of the linked document
            profile_id: ID of the linked profile
            user_id: ID of the user who created the link
            link_type: Type of link between document and profile
            created_at: When the link was created
            expires_at: When the link expires (if temporary)
            metadata: Additional metadata about the link
            link_id: Unique ID for this link (generated if not provided)
        """
        self.document_id = document_id
        self.profile_id = profile_id
        self.user_id = user_id
        self.link_type = link_type
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at
        self.metadata = metadata or {}
        self.link_id = link_id or str(uuid.uuid4())
    
    def is_expired(self) -> bool:
        """Check if the link has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert link to dictionary for storage or serialization."""
        return {
            "link_id": self.link_id,
            "document_id": self.document_id,
            "profile_id": self.profile_id,
            "user_id": self.user_id,
            "link_type": self.link_type.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileDocumentLink':
        """Create a link from a dictionary."""
        link_type = LinkType(data.get("link_type"))
        created_at = datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else None
        expires_at = datetime.fromisoformat(data.get("expires_at")) if data.get("expires_at") else None
        
        return cls(
            document_id=data.get("document_id"),
            profile_id=data.get("profile_id"),
            user_id=data.get("user_id"),
            link_type=link_type,
            created_at=created_at,
            expires_at=expires_at,
            metadata=data.get("metadata", {}),
            link_id=data.get("link_id")
        )


class DocumentProfileLink:
    """
    Service for managing links between documents and user profiles.
    
    This service enables associating documents with profiles in different ways,
    supporting document organization, sharing, and recommendations based on profiles.
    """
    
    def __init__(self, database_repository=None):
        """
        Initialize the document-profile linking service.
        
        Args:
            database_repository: Repository for storing links
        """
        self.db_repository = database_repository
        self._links: Dict[str, ProfileDocumentLink] = {}  # In-memory cache of links by link_id
        self._doc_links: Dict[str, Set[str]] = {}  # Document ID -> Set of link IDs
        self._profile_links: Dict[str, Set[str]] = {}  # Profile ID -> Set of link IDs
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the document-profile link service."""
        if self._initialized:
            return
        
        # Load links from database if repository is available
        if self.db_repository:
            try:
                await self.db_repository.initialize()
                links = await self.db_repository.get_all_profile_document_links()
                
                # Populate cache
                for link in links:
                    self._add_link_to_cache(link)
                
                logger.info(f"Loaded {len(links)} profile-document links from database")
            except Exception as e:
                logger.error(f"Failed to initialize document-profile link service: {str(e)}")
        
        self._initialized = True
        logger.info("Document-profile link service initialized")
    
    def _add_link_to_cache(self, link: ProfileDocumentLink) -> None:
        """Add a link to the in-memory cache."""
        self._links[link.link_id] = link
        
        # Add to document links index
        if link.document_id not in self._doc_links:
            self._doc_links[link.document_id] = set()
        self._doc_links[link.document_id].add(link.link_id)
        
        # Add to profile links index
        if link.profile_id not in self._profile_links:
            self._profile_links[link.profile_id] = set()
        self._profile_links[link.profile_id].add(link.link_id)
    
    def _remove_link_from_cache(self, link_id: str) -> None:
        """Remove a link from the in-memory cache."""
        if link_id not in self._links:
            return
        
        link = self._links[link_id]
        
        # Remove from document links index
        if link.document_id in self._doc_links:
            self._doc_links[link.document_id].discard(link_id)
            if not self._doc_links[link.document_id]:
                del self._doc_links[link.document_id]
        
        # Remove from profile links index
        if link.profile_id in self._profile_links:
            self._profile_links[link.profile_id].discard(link_id)
            if not self._profile_links[link.profile_id]:
                del self._profile_links[link.profile_id]
        
        # Remove from main links cache
        del self._links[link_id]
    
    async def link_document_to_profile(self,
                                     document_id: str,
                                     profile_id: str,
                                     user_id: str,
                                     link_type: LinkType = LinkType.OWNED,
                                     expires_at: Optional[datetime] = None,
                                     metadata: Optional[Dict[str, Any]] = None) -> ProfileDocumentLink:
        """
        Create a link between a document and a profile.
        
        Args:
            document_id: ID of the document to link
            profile_id: ID of the profile to link to
            user_id: ID of the user creating the link
            link_type: Type of link to create
            expires_at: When the link expires (if temporary)
            metadata: Additional metadata about the link
            
        Returns:
            The created link
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate parameters
        if not document_id:
            raise ValidationError("Document ID is required")
        if not profile_id:
            raise ValidationError("Profile ID is required")
        if not user_id:
            raise ValidationError("User ID is required")
        
        # Create link
        link = ProfileDocumentLink(
            document_id=document_id,
            profile_id=profile_id,
            user_id=user_id,
            link_type=link_type,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        # Store in database if available
        if self.db_repository:
            try:
                await self.db_repository.save_profile_document_link(link)
            except Exception as e:
                logger.error(f"Failed to save profile-document link to database: {str(e)}")
                # Continue to store in memory
        
        # Store in memory
        self._add_link_to_cache(link)
        
        logger.info(f"Created {link_type.value} link between document {document_id} and profile {profile_id}")
        return link
    
    async def get_profile_documents(self, 
                                  profile_id: str,
                                  link_types: Optional[List[LinkType]] = None,
                                  include_expired: bool = False) -> List[ProfileDocumentLink]:
        """
        Get all documents linked to a profile.
        
        Args:
            profile_id: ID of the profile
            link_types: Optional filter for specific link types
            include_expired: Whether to include expired links
            
        Returns:
            List of profile-document links
        """
        if not self._initialized:
            await self.initialize()
        
        # Get links from memory
        link_ids = self._profile_links.get(profile_id, set())
        links = []
        
        for link_id in link_ids:
            link = self._links.get(link_id)
            if not link:
                continue
            
            # Check if expired
            if not include_expired and link.is_expired():
                continue
            
            # Filter by link type if specified
            if link_types and link.link_type not in link_types:
                continue
            
            links.append(link)
        
        return links
    
    async def get_document_profiles(self, 
                                  document_id: str,
                                  link_types: Optional[List[LinkType]] = None,
                                  include_expired: bool = False) -> List[ProfileDocumentLink]:
        """
        Get all profiles linked to a document.
        
        Args:
            document_id: ID of the document
            link_types: Optional filter for specific link types
            include_expired: Whether to include expired links
            
        Returns:
            List of profile-document links
        """
        if not self._initialized:
            await self.initialize()
        
        # Get links from memory
        link_ids = self._doc_links.get(document_id, set())
        links = []
        
        for link_id in link_ids:
            link = self._links.get(link_id)
            if not link:
                continue
            
            # Check if expired
            if not include_expired and link.is_expired():
                continue
            
            # Filter by link type if specified
            if link_types and link.link_type not in link_types:
                continue
            
            links.append(link)
        
        return links
    
    async def remove_link(self, link_id: str) -> bool:
        """
        Remove a profile-document link.
        
        Args:
            link_id: ID of the link to remove
            
        Returns:
            True if link was removed, False if not found
            
        Raises:
            ResourceNotFoundError: If link is not found
        """
        if not self._initialized:
            await self.initialize()
        
        # Check if link exists
        if link_id not in self._links:
            raise ResourceNotFoundError(f"Link {link_id} not found")
        
        # Remove from database if available
        if self.db_repository:
            try:
                await self.db_repository.delete_profile_document_link(link_id)
            except Exception as e:
                logger.error(f"Failed to delete profile-document link from database: {str(e)}")
                # Continue to remove from memory
        
        # Remove from memory
        self._remove_link_from_cache(link_id)
        
        logger.info(f"Removed profile-document link {link_id}")
        return True
    
    async def remove_document_profile_links(self, 
                                         document_id: str, 
                                         profile_id: str,
                                         link_types: Optional[List[LinkType]] = None) -> int:
        """
        Remove all links between a document and a profile.
        
        Args:
            document_id: ID of the document
            profile_id: ID of the profile
            link_types: Optional filter for specific link types
            
        Returns:
            Number of links removed
        """
        if not self._initialized:
            await self.initialize()
        
        # Get links to remove
        link_ids = self._doc_links.get(document_id, set()).intersection(
            self._profile_links.get(profile_id, set())
        )
        
        if not link_ids:
            return 0
        
        links_to_remove = []
        for link_id in link_ids:
            link = self._links.get(link_id)
            if not link:
                continue
            
            # Filter by link type if specified
            if link_types and link.link_type not in link_types:
                continue
            
            links_to_remove.append(link_id)
        
        # Remove links
        for link_id in links_to_remove:
            # Remove from database if available
            if self.db_repository:
                try:
                    await self.db_repository.delete_profile_document_link(link_id)
                except Exception as e:
                    logger.error(f"Failed to delete profile-document link from database: {str(e)}")
                    # Continue to remove from memory
            
            # Remove from memory
            self._remove_link_from_cache(link_id)
        
        if links_to_remove:
            logger.info(f"Removed {len(links_to_remove)} links between document {document_id} and profile {profile_id}")
        
        return len(links_to_remove)
    
    async def get_document_owners(self, document_id: str) -> List[str]:
        """
        Get all profiles that own a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of profile IDs that own the document
        """
        if not self._initialized:
            await self.initialize()
        
        # Get links from memory
        links = await self.get_document_profiles(
            document_id, 
            link_types=[LinkType.OWNED],
            include_expired=False
        )
        
        return [link.profile_id for link in links]
    
    async def is_document_owned_by_profile(self, document_id: str, profile_id: str) -> bool:
        """
        Check if a document is owned by a profile.
        
        Args:
            document_id: ID of the document
            profile_id: ID of the profile
            
        Returns:
            True if the profile owns the document, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        # Get links from memory
        link_ids = self._doc_links.get(document_id, set()).intersection(
            self._profile_links.get(profile_id, set())
        )
        
        for link_id in link_ids:
            link = self._links.get(link_id)
            if not link:
                continue
            
            if link.link_type == LinkType.OWNED and not link.is_expired():
                return True
        
        return False 