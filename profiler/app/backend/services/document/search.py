"""
Document Search Service.

This module provides functionality for searching documents using various criteria.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.orm import Session

from .models import Document, DocumentVersion
from .exceptions import SearchError
from ...utils.errors import ValidationError

logger = logging.getLogger(__name__)

class DocumentSearchService:
    """Service for searching documents."""
    
    def __init__(self, db_session: Session):
        """
        Initialize the document search service.
        
        Args:
            db_session: Database session for querying
        """
        self.db_session = db_session
    
    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Alias for search_documents to maintain backward compatibility.
        
        Args:
            query: Search query string
            **kwargs: Additional search parameters
            
        Returns:
            Search results
            
        Raises:
            SearchError: If search fails
        """
        return await self.search_documents(query, **kwargs)
    
    async def search_documents(
        self,
        query: str,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Search for documents based on query and filters.
        
        Args:
            query: Search query string
            user_id: Optional user ID to filter by owner
            filters: Optional dictionary of filters:
                - created_after: datetime
                - created_before: datetime
                - file_type: str
                - tags: List[str]
                - categories: List[str]
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            page: Page number
            page_size: Number of results per page
            
        Returns:
            Dictionary containing:
            - total: Total number of matching documents
            - page: Current page number
            - page_size: Number of results per page
            - documents: List of matching documents
            
        Raises:
            SearchError: If search fails
            ValidationError: If invalid parameters provided
        """
        try:
            # Validate parameters
            if page < 1:
                raise ValidationError("Page number must be >= 1")
            if page_size < 1:
                raise ValidationError("Page size must be >= 1")
            if sort_order not in ["asc", "desc"]:
                raise ValidationError("Sort order must be 'asc' or 'desc'")
            
            # Build base query
            stmt = select(Document)
            
            # Add search conditions
            if query:
                search_filter = or_(
                    Document.title.ilike(f"%{query}%"),
                    Document.metadata["description"].astext.ilike(f"%{query}%")
                )
                stmt = stmt.where(search_filter)
            
            # Add user filter
            if user_id:
                stmt = stmt.where(Document.owner_id == user_id)
            
            # Add additional filters
            if filters:
                if "created_after" in filters:
                    stmt = stmt.where(Document.created_at >= filters["created_after"])
                if "created_before" in filters:
                    stmt = stmt.where(Document.created_at <= filters["created_before"])
                if "file_type" in filters:
                    stmt = stmt.where(Document.mime_type == filters["file_type"])
                if "tags" in filters:
                    stmt = stmt.where(Document.metadata["tags"].contains(filters["tags"]))
                if "categories" in filters:
                    stmt = stmt.where(Document.metadata["categories"].contains(filters["categories"]))
            
            # Add sorting
            sort_column = getattr(Document, sort_by)
            if sort_order == "desc":
                stmt = stmt.order_by(desc(sort_column))
            else:
                stmt = stmt.order_by(sort_column)
            
            # Add pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)
            
            # Execute query
            result = await self.db_session.execute(stmt)
            documents = result.scalars().all()
            
            # Get total count
            count_stmt = select(Document).where(stmt.whereclause)
            count_result = await self.db_session.execute(count_stmt)
            total = len(count_result.scalars().all())
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            raise SearchError(f"Failed to search documents: {str(e)}")
    
    async def search_document_versions(
        self,
        document_id: str,
        query: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        created_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Search for versions of a specific document.
        
        Args:
            document_id: ID of the document
            query: Optional search query string
            created_after: Optional filter for versions created after this time
            created_before: Optional filter for versions created before this time
            created_by: Optional filter for versions created by specific user
            page: Page number
            page_size: Number of results per page
            
        Returns:
            Dictionary containing:
            - total: Total number of matching versions
            - page: Current page number
            - page_size: Number of results per page
            - versions: List of matching versions
            
        Raises:
            SearchError: If search fails
            ValidationError: If invalid parameters provided
        """
        try:
            # Validate parameters
            if page < 1:
                raise ValidationError("Page number must be >= 1")
            if page_size < 1:
                raise ValidationError("Page size must be >= 1")
            
            # Build base query
            stmt = select(DocumentVersion).where(DocumentVersion.document_id == document_id)
            
            # Add filters
            if query:
                stmt = stmt.where(DocumentVersion.metadata["comment"].astext.ilike(f"%{query}%"))
            if created_after:
                stmt = stmt.where(DocumentVersion.created_at >= created_after)
            if created_before:
                stmt = stmt.where(DocumentVersion.created_at <= created_before)
            if created_by:
                stmt = stmt.where(DocumentVersion.created_by == created_by)
            
            # Add sorting (always by version number descending)
            stmt = stmt.order_by(desc(DocumentVersion.version_number))
            
            # Add pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)
            
            # Execute query
            result = await self.db_session.execute(stmt)
            versions = result.scalars().all()
            
            # Get total count
            count_stmt = select(DocumentVersion).where(stmt.whereclause)
            count_result = await self.db_session.execute(count_stmt)
            total = len(count_result.scalars().all())
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "versions": versions
            }
            
        except Exception as e:
            logger.error(f"Version search error: {str(e)}", exc_info=True)
            raise SearchError(f"Failed to search document versions: {str(e)}") 