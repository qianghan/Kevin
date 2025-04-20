"""
Tests for document search functionality.
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

from app.backend.services.document.search import DocumentSearchService
from app.backend.services.document.models import Document
from app.backend.services.document.indexing import DocumentIndexingService


@pytest.fixture
def mock_document_repository():
    """Create a mock document repository."""
    repository = MagicMock()
    
    # Mock documents data
    documents = [
        Document(
            id=f"doc{i}",
            title=f"Test Document {i}",
            owner_id="test-user",
            content_type="text/plain",
            size=100 * i,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                "description": f"This is test document {i}",
                "tags": ["test", f"tag{i}"],
                "keywords": ["document", "search", f"keyword{i}"]
            }
        )
        for i in range(1, 6)
    ]
    
    async def list_documents(*args, **kwargs):
        return documents
    
    async def get_document(document_id):
        for doc in documents:
            if doc.id == document_id:
                return doc
        return None
    
    async def get_document_content(document_id):
        # Simulate document content
        contents = {
            "doc1": "This is document 1 content with specific search terms.",
            "doc2": "Document 2 contains information about search algorithms.",
            "doc3": "Document 3 has advanced search filtering features.",
            "doc4": "This document explains how to implement document similarity.",
            "doc5": "The final document shows examples of full-text search."
        }
        if document_id in contents:
            from io import BytesIO
            return BytesIO(contents[document_id].encode('utf-8'))
        return BytesIO(b"")
    
    repository.list_documents = AsyncMock(side_effect=list_documents)
    repository.get_document = AsyncMock(side_effect=get_document)
    repository.get_document_content = AsyncMock(side_effect=get_document_content)
    
    return repository


@pytest.fixture
def mock_document_indexing():
    """Create a mock document indexing service."""
    indexing_service = MagicMock(spec=DocumentIndexingService)
    
    # Simulate the indexing process
    async def index_document(document, content):
        return {
            "document_id": document.id,
            "indexed": True,
            "token_count": len(content.split())
        }
    
    async def extract_content(document, content_stream):
        content = content_stream.read().decode('utf-8')
        return content
    
    indexing_service.index_document = AsyncMock(side_effect=index_document)
    indexing_service.extract_content = AsyncMock(side_effect=extract_content)
    
    return indexing_service


@pytest.fixture
def search_service(mock_document_repository, mock_document_indexing):
    """Create a document search service with mocked dependencies."""
    service = DocumentSearchService(
        document_repository=mock_document_repository,
        indexing_service=mock_document_indexing
    )
    return service


class TestDocumentSearch:
    """Tests for document search functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_search(self, search_service):
        """Test basic document search."""
        # Perform search
        results = await search_service.search("search")
        
        # Verify results
        assert len(results) >= 3, "Should find at least 3 documents related to search"
        assert any(doc.id == "doc2" for doc in results), "Should find document 2"
        assert any(doc.id == "doc3" for doc in results), "Should find document 3"
        assert any(doc.id == "doc5" for doc in results), "Should find document 5"
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_service):
        """Test document search with metadata filters."""
        # Perform search with filters
        results = await search_service.search(
            "document",
            filters={
                "tags": ["tag3"],
                "size_min": 200,
                "size_max": 400
            }
        )
        
        # Verify results
        assert len(results) == 1, "Should find exactly 1 document"
        assert results[0].id == "doc3", "Should find document 3"
    
    @pytest.mark.asyncio
    async def test_search_with_date_range(self, search_service):
        """Test document search with date range filter."""
        # Get current date for testing
        now = datetime.utcnow()
        
        # Perform search with date range
        results = await search_service.search(
            "document",
            filters={
                "created_after": now.replace(hour=0, minute=0, second=0),
                "created_before": now
            }
        )
        
        # Verify results - all test documents should be created today
        assert len(results) > 0, "Should find documents created today"
    
    @pytest.mark.asyncio
    async def test_search_by_document_type(self, search_service):
        """Test document search by document type."""
        # Perform search with document type filter
        results = await search_service.search(
            "document",
            filters={
                "content_type": "text/plain"
            }
        )
        
        # Verify results - all test documents have content_type text/plain
        assert len(results) == 5, "Should find all 5 text documents"
    
    @pytest.mark.asyncio
    async def test_search_with_pagination(self, search_service):
        """Test document search with pagination."""
        # Perform search with pagination
        page1 = await search_service.search(
            "document",
            page=1,
            page_size=2
        )
        
        page2 = await search_service.search(
            "document",
            page=2,
            page_size=2
        )
        
        # Verify pagination
        assert len(page1) == 2, "First page should have 2 documents"
        assert len(page2) == 2, "Second page should have 2 documents"
        assert page1[0].id != page2[0].id, "Pages should have different documents"
        assert page1[1].id != page2[0].id, "Pages should have different documents"
    
    @pytest.mark.asyncio
    async def test_search_by_owner(self, search_service):
        """Test document search by owner."""
        # Perform search with owner filter
        results = await search_service.search(
            "document",
            filters={
                "owner_id": "test-user"
            }
        )
        
        # Verify results - all test documents have the same owner
        assert len(results) == 5, "Should find all 5 documents owned by test-user"
    
    @pytest.mark.asyncio
    async def test_search_with_sorting(self, search_service):
        """Test document search with sorting."""
        # Perform search with sorting by size (ascending)
        results_asc = await search_service.search(
            "document",
            sort_field="size",
            sort_order="asc"
        )
        
        # Perform search with sorting by size (descending)
        results_desc = await search_service.search(
            "document",
            sort_field="size",
            sort_order="desc"
        )
        
        # Verify sorting
        assert results_asc[0].size < results_asc[-1].size, "Documents should be sorted by size (ascending)"
        assert results_desc[0].size > results_desc[-1].size, "Documents should be sorted by size (descending)"
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, search_service):
        """Test document similarity search."""
        # Mock the similarity search implementation
        with patch.object(search_service, '_perform_similarity_search') as mock_similarity:
            # Set up mock to return doc1 and doc4 as similar
            async def mock_similarity_search(query, **kwargs):
                return [doc for doc in await search_service._document_repository.list_documents() 
                        if doc.id in ["doc1", "doc4"]]
            
            mock_similarity.side_effect = mock_similarity_search
            
            # Perform similarity search
            results = await search_service.similarity_search(
                "document search implementation examples"
            )
            
            # Verify results
            assert len(results) == 2, "Should find 2 similar documents"
            assert {doc.id for doc in results} == {"doc1", "doc4"}, "Should find doc1 and doc4"
    
    @pytest.mark.asyncio
    async def test_search_performance(self, search_service):
        """Test document search performance."""
        # Generate a large number of search terms
        search_terms = ["document", "search", "content", "metadata", "filter"] * 10
        
        # Measure the time to perform searches
        import time
        start_time = time.time()
        
        # Run multiple searches
        for term in search_terms:
            await search_service.search(term)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify performance
        assert duration < 5.0, f"Multiple searches should complete in under 5 seconds, took {duration} seconds"
    
    @pytest.mark.asyncio
    async def test_index_management(self, search_service):
        """Test document index management."""
        # Mock the reindex methods
        with patch.object(search_service, '_index_document') as mock_index:
            # Initialize the index
            await search_service.initialize_index()
            
            # Verify all documents were indexed
            assert mock_index.call_count == 5, "All 5 documents should be indexed"


# Integration tests (require actual database and indexing service)
@pytest.mark.integration
class TestDocumentSearchIntegration:
    """Integration tests for document search functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Integration test requires real database and indexing service")
    async def test_full_text_search(self):
        """Test full text search on actual documents."""
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Integration test requires real database and indexing service")
    async def test_advanced_filtering(self):
        """Test advanced filtering capabilities on actual documents."""
        pass 