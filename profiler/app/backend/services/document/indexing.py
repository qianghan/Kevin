"""
Document content indexing service.

This module provides functionality for indexing document content to support
full-text search capabilities across documents.
"""

import os
import re
import json
import tempfile
from typing import Dict, List, Any, Optional, BinaryIO, Tuple, Set, Union
from datetime import datetime
import asyncio
import aiosqlite
import logging
import uuid
from pathlib import Path

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import StorageError, ValidationError, ConfigurationError
from app.backend.utils.config_manager import ConfigManager
from .models import Document, DocumentChunk
from .extraction import DocumentMetadataExtractor

logger = get_logger(__name__)


class DocumentContentExtractor:
    """Extracts searchable text content from various document types."""
    
    @classmethod
    def get_extractor(cls, mime_type: str) -> 'DocumentContentExtractor':
        """
        Get an appropriate content extractor for the given MIME type.
        
        Args:
            mime_type: MIME type of the document
            
        Returns:
            DocumentContentExtractor instance
        """
        # Use the same mapping approach as metadata extractors
        extractors = {
            # PDF files
            "application/pdf": PDFContentExtractor,
            
            # Office documents
            "application/msword": OfficeContentExtractor,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": OfficeContentExtractor,
            "application/vnd.ms-excel": OfficeContentExtractor,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": OfficeContentExtractor,
            "application/vnd.ms-powerpoint": OfficeContentExtractor,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": OfficeContentExtractor,
            
            # Text files
            "text/plain": TextContentExtractor,
            "text/html": HTMLContentExtractor,
            "text/xml": TextContentExtractor,
            "application/json": TextContentExtractor,
            "text/markdown": TextContentExtractor,
        }
        
        # Get extractor for MIME type, or use default
        extractor_class = extractors.get(mime_type, DefaultContentExtractor)
        return extractor_class()
    
    async def extract_content(self, file_content: BinaryIO, filename: str) -> str:
        """
        Extract searchable text content from a document.
        
        Args:
            file_content: Document content
            filename: Original filename
            
        Returns:
            Extracted text content
            
        Raises:
            StorageError: If content cannot be extracted
        """
        # Default implementation that should be overridden
        return ""


class DefaultContentExtractor(DocumentContentExtractor):
    """Default content extractor for unsupported document types."""
    
    async def extract_content(self, file_content: BinaryIO, filename: str) -> str:
        """
        Extract basic text content if possible, otherwise return empty string.
        
        Args:
            file_content: Document content
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        # Get current position to restore later
        pos = file_content.tell()
        
        try:
            # Try to extract some text content
            file_content.seek(0)
            bytes_content = file_content.read(8192)  # Read first 8KB
            
            # Try to decode as UTF-8
            try:
                text = bytes_content.decode('utf-8')
                # Filter out non-printable characters
                text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]', ' ', text)
                return text
            except UnicodeDecodeError:
                # Not text content, return empty string
                return ""
                
        except Exception as e:
            logger.error(f"Failed to extract content from {filename}: {str(e)}")
            return ""
            
        finally:
            # Restore original position
            file_content.seek(pos)


class TextContentExtractor(DocumentContentExtractor):
    """Content extractor for plain text documents."""
    
    async def extract_content(self, file_content: BinaryIO, filename: str) -> str:
        """
        Extract text content from a text document.
        
        Args:
            file_content: Document content
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        # Get current position to restore later
        pos = file_content.tell()
        
        try:
            # Read content
            file_content.seek(0)
            content = file_content.read()
            
            try:
                # Try to decode as UTF-8
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                # Fall back to latin-1 for binary files
                try:
                    text = content.decode('latin-1')
                except UnicodeDecodeError:
                    # If still can't decode, return empty string
                    return ""
            
            # Filter out non-printable characters
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ' ', text)
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text content from {filename}: {str(e)}")
            return ""
            
        finally:
            # Restore original position
            file_content.seek(pos)


class HTMLContentExtractor(TextContentExtractor):
    """Content extractor for HTML documents."""
    
    async def extract_content(self, file_content: BinaryIO, filename: str) -> str:
        """
        Extract text content from an HTML document.
        
        Args:
            file_content: Document content
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        # Get current position to restore later
        pos = file_content.tell()
        
        try:
            try:
                # Try to import BeautifulSoup, fall back to text if not available
                from bs4 import BeautifulSoup
            except ImportError:
                logger.warning("BeautifulSoup not installed; using text content extraction.")
                return await super().extract_content(file_content, filename)
            
            # Read content
            file_content.seek(0)
            content = file_content.read()
            
            try:
                # Try to decode as UTF-8
                html_text = content.decode('utf-8')
            except UnicodeDecodeError:
                # Fall back to latin-1 for binary files
                try:
                    html_text = content.decode('latin-1')
                except UnicodeDecodeError:
                    # If still can't decode, return empty string
                    return ""
            
            # Parse HTML
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract HTML content from {filename}: {str(e)}")
            
            # Fall back to text extractor
            return await super().extract_content(file_content, filename)
            
        finally:
            # Restore original position
            file_content.seek(pos)


class PDFContentExtractor(DocumentContentExtractor):
    """Content extractor for PDF documents."""
    
    async def extract_content(self, file_content: BinaryIO, filename: str) -> str:
        """
        Extract text content from a PDF document.
        
        Args:
            file_content: Document content
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        # Get current position to restore later
        pos = file_content.tell()
        
        try:
            try:
                # Try to import PyPDF2, fall back to default if not available
                import PyPDF2
            except ImportError:
                logger.warning("PyPDF2 not installed; using default content extraction.")
                return await DefaultContentExtractor().extract_content(file_content, filename)
            
            # Create PDF reader
            pdf_reader = PyPDF2.PdfReader(file_content)
            
            # Extract text from all pages
            text_content = []
            for page in pdf_reader.pages:
                try:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from PDF page: {str(e)}")
            
            # Combine all text
            full_text = "\n\n".join(text_content)
            
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to extract PDF content from {filename}: {str(e)}")
            
            # Fall back to default extractor
            return await DefaultContentExtractor().extract_content(file_content, filename)
            
        finally:
            # Restore original position
            file_content.seek(pos)


class OfficeContentExtractor(DocumentContentExtractor):
    """Content extractor for Microsoft Office documents."""
    
    async def extract_content(self, file_content: BinaryIO, filename: str) -> str:
        """
        Extract text content from Office documents.
        
        Args:
            file_content: Document content
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        # Get current position to restore later
        pos = file_content.tell()
        
        try:
            # Get file extension
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            # Create temporary file to work with
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file_content.seek(0)
                temp_file.write(file_content.read())
                temp_path = temp_file.name
            
            try:
                text_content = ""
                
                if ext == '.docx':
                    try:
                        # Try to import python-docx for DOCX files
                        import docx
                        
                        # Extract text from DOCX
                        doc = docx.Document(temp_path)
                        paragraphs = [p.text for p in doc.paragraphs if p.text]
                        text_content = "\n".join(paragraphs)
                        
                    except ImportError:
                        logger.warning("python-docx not installed; using default content extraction.")
                        return await DefaultContentExtractor().extract_content(file_content, filename)
                        
                elif ext == '.xlsx':
                    try:
                        # Try to import openpyxl for XLSX files
                        import openpyxl
                        
                        # Extract text from XLSX
                        wb = openpyxl.load_workbook(temp_path, read_only=True)
                        sheet_texts = []
                        
                        for sheet in wb.worksheets:
                            cells = []
                            for row in sheet.iter_rows():
                                cell_values = [str(cell.value) if cell.value is not None else "" for cell in row]
                                cells.append(" ".join(cell_values))
                            sheet_texts.append("\n".join(cells))
                        
                        text_content = "\n\n".join(sheet_texts)
                        
                    except ImportError:
                        logger.warning("openpyxl not installed; using default content extraction.")
                        return await DefaultContentExtractor().extract_content(file_content, filename)
                        
                else:
                    # Unsupported Office format
                    return await DefaultContentExtractor().extract_content(file_content, filename)
                
                return text_content
                
            finally:
                # Delete temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"Failed to extract Office content from {filename}: {str(e)}")
            
            # Fall back to default extractor
            return await DefaultContentExtractor().extract_content(file_content, filename)
            
        finally:
            # Restore original position
            file_content.seek(pos)


class DocumentIndexingService:
    """Service for indexing document content to support search."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the document indexing service.
        
        Args:
            config: Optional configuration for indexing service
        """
        self.config = config or {}
        self.initialized = False
        
        # Set default values
        self.index_dir = self.config.get("index_dir", "data/search_index")
        self.db_path = os.path.join(self.index_dir, "document_index.db")
        self.chunk_size = self.config.get("chunk_size", 1000)  # Characters per chunk
        
        # Connection pool
        self._db = None
    
    async def initialize(self) -> None:
        """Initialize the indexing service."""
        if self.initialized:
            return
            
        try:
            # Create index directory if it doesn't exist
            os.makedirs(self.index_dir, exist_ok=True)
            
            # Initialize database
            async with self._get_db() as db:
                # Create tables if they don't exist
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS document_index (
                        id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT NOT NULL
                    )
                ''')
                
                # Create full-text search virtual table
                await db.execute('''
                    CREATE VIRTUAL TABLE IF NOT EXISTS document_fts 
                    USING fts5(
                        content, 
                        document_id, 
                        metadata,
                        content='document_index', 
                        content_rowid='rowid'
                    )
                ''')
                
                # Create triggers to keep FTS table in sync
                await db.execute('''
                    CREATE TRIGGER IF NOT EXISTS document_index_ai AFTER INSERT ON document_index
                    BEGIN
                        INSERT INTO document_fts(rowid, content, document_id, metadata)
                        VALUES (new.rowid, new.content, new.document_id, new.metadata);
                    END
                ''')
                
                await db.execute('''
                    CREATE TRIGGER IF NOT EXISTS document_index_ad AFTER DELETE ON document_index
                    BEGIN
                        INSERT INTO document_fts(document_fts, rowid, content, document_id, metadata)
                        VALUES ('delete', old.rowid, old.content, old.document_id, old.metadata);
                    END
                ''')
                
                await db.execute('''
                    CREATE TRIGGER IF NOT EXISTS document_index_au AFTER UPDATE ON document_index
                    BEGIN
                        INSERT INTO document_fts(document_fts, rowid, content, document_id, metadata)
                        VALUES ('delete', old.rowid, old.content, old.document_id, old.metadata);
                        INSERT INTO document_fts(rowid, content, document_id, metadata)
                        VALUES (new.rowid, new.content, new.document_id, new.metadata);
                    END
                ''')
                
                await db.commit()
            
            self.initialized = True
            logger.info(f"Initialized document indexing service with index at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize document indexing service: {str(e)}")
            raise ConfigurationError(f"Failed to initialize document indexing: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the indexing service."""
        if self._db:
            await self._db.close()
            self._db = None
        self.initialized = False
        logger.info("Shutdown document indexing service")
    
    async def _get_db(self) -> aiosqlite.Connection:
        """Get database connection."""
        if not self._db:
            self._db = await aiosqlite.connect(self.db_path)
            self._db.row_factory = aiosqlite.Row
        return self._db
    
    async def index_document(self, document: Document, file_content: BinaryIO) -> List[Dict[str, Any]]:
        """
        Index a document for search.
        
        Args:
            document: Document to index
            file_content: Document content
            
        Returns:
            List of indexed chunks with IDs
            
        Raises:
            StorageError: If document cannot be indexed
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get appropriate content extractor based on MIME type
            extractor = DocumentContentExtractor.get_extractor(document.mime_type)
            
            # Extract text content
            content = await extractor.extract_content(file_content, document.filename)
            
            # If no content was extracted, return empty list
            if not content:
                logger.warning(f"No content extracted from document {document.document_id}")
                return []
            
            # Split content into chunks
            chunks = self._split_content_into_chunks(content, self.chunk_size)
            
            # Prepare metadata JSON
            metadata_json = json.dumps({
                "document_id": document.document_id,
                "filename": document.filename,
                "mime_type": document.mime_type,
                "user_id": document.user_id,
                "profile_id": document.profile_id,
                "created_at": document.created_at,
                "updated_at": document.updated_at
            })
            
            # Delete existing index entries for this document
            await self.remove_document_from_index(document.document_id)
            
            # Index each chunk
            indexed_chunks = []
            async with self._get_db() as db:
                for i, chunk_content in enumerate(chunks):
                    chunk_id = str(uuid.uuid4())
                    created_at = datetime.utcnow().isoformat()
                    
                    # Insert into document_index table
                    await db.execute(
                        """
                        INSERT INTO document_index 
                        (id, document_id, chunk_index, content, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (chunk_id, document.document_id, i, chunk_content, metadata_json, created_at)
                    )
                    
                    indexed_chunks.append({
                        "id": chunk_id,
                        "document_id": document.document_id,
                        "chunk_index": i,
                        "content_length": len(chunk_content),
                        "created_at": created_at
                    })
                
                await db.commit()
            
            logger.info(f"Indexed document {document.document_id} with {len(chunks)} chunks")
            return indexed_chunks
            
        except Exception as e:
            logger.error(f"Failed to index document {document.document_id}: {str(e)}")
            raise StorageError(f"Failed to index document: {str(e)}")
    
    async def reindex_document(self, document: Document, file_content: BinaryIO) -> List[Dict[str, Any]]:
        """
        Reindex a document for search, removing previous index entries.
        
        Args:
            document: Document to reindex
            file_content: Document content
            
        Returns:
            List of indexed chunks with IDs
            
        Raises:
            StorageError: If document cannot be reindexed
        """
        # Delete existing index entries
        await self.remove_document_from_index(document.document_id)
        
        # Index document
        return await self.index_document(document, file_content)
    
    async def remove_document_from_index(self, document_id: str) -> None:
        """
        Remove a document from the search index.
        
        Args:
            document_id: ID of the document to remove
            
        Raises:
            StorageError: If document cannot be removed from index
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            async with self._get_db() as db:
                # Delete from document_index table
                await db.execute(
                    "DELETE FROM document_index WHERE document_id = ?",
                    (document_id,)
                )
                await db.commit()
            
            logger.info(f"Removed document {document_id} from index")
            
        except Exception as e:
            logger.error(f"Failed to remove document {document_id} from index: {str(e)}")
            raise StorageError(f"Failed to remove document from index: {str(e)}")
    
    async def search_documents(self, 
                             query: str, 
                             user_id: Optional[str] = None, 
                             profile_id: Optional[str] = None,
                             limit: int = 20,
                             offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search documents by content.
        
        Args:
            query: Search query
            user_id: Optional user ID to filter results
            profile_id: Optional profile ID to filter results
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            Tuple of (search_results, total_count)
            
        Raises:
            StorageError: If search fails
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Build search query
            search_query = f"{query}"
            
            # Build filter conditions
            filter_conditions = []
            filter_params = []
            
            if user_id:
                filter_conditions.append("json_extract(i.metadata, '$.user_id') = ?")
                filter_params.append(user_id)
            
            if profile_id:
                filter_conditions.append("json_extract(i.metadata, '$.profile_id') = ?")
                filter_params.append(profile_id)
            
            filter_sql = ""
            if filter_conditions:
                filter_sql = "AND " + " AND ".join(filter_conditions)
            
            # Execute search query
            async with self._get_db() as db:
                # Get total count
                total_query = f"""
                    SELECT COUNT(DISTINCT i.document_id) as total
                    FROM document_fts AS f
                    JOIN document_index AS i ON f.rowid = i.rowid
                    WHERE document_fts MATCH ?
                    {filter_sql}
                """
                cursor = await db.execute(total_query, [search_query] + filter_params)
                row = await cursor.fetchone()
                total_count = row['total'] if row else 0
                
                # Execute search with pagination
                result_query = f"""
                    SELECT 
                        i.document_id,
                        json_extract(i.metadata, '$.filename') AS filename,
                        json_extract(i.metadata, '$.mime_type') AS mime_type,
                        json_extract(i.metadata, '$.user_id') AS user_id,
                        json_extract(i.metadata, '$.profile_id') AS profile_id,
                        json_extract(i.metadata, '$.created_at') AS created_at,
                        i.id AS chunk_id,
                        i.chunk_index,
                        snippet(document_fts, 0, '<b>', '</b>', '...', 10) AS snippet,
                        rank
                    FROM (
                        SELECT 
                            rowid,
                            rank
                        FROM document_fts
                        WHERE document_fts MATCH ?
                        ORDER BY rank
                    ) AS r
                    JOIN document_index AS i ON r.rowid = i.rowid
                    WHERE 1=1 {filter_sql}
                    GROUP BY i.document_id
                    ORDER BY rank
                    LIMIT ? OFFSET ?
                """
                
                cursor = await db.execute(
                    result_query, 
                    [search_query] + filter_params + [limit, offset]
                )
                
                results = []
                async for row in cursor:
                    result = {
                        "document_id": row['document_id'],
                        "filename": row['filename'],
                        "mime_type": row['mime_type'],
                        "user_id": row['user_id'],
                        "profile_id": row['profile_id'],
                        "created_at": row['created_at'],
                        "chunk_id": row['chunk_id'],
                        "chunk_index": row['chunk_index'],
                        "snippet": row['snippet'],
                        "rank": row['rank']
                    }
                    results.append(result)
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}")
            raise StorageError(f"Failed to search documents: {str(e)}")
    
    def _split_content_into_chunks(self, content: str, chunk_size: int) -> List[str]:
        """
        Split content into chunks of approximately equal size.
        
        Args:
            content: Text content to split
            chunk_size: Approximate size of each chunk in characters
            
        Returns:
            List of content chunks
        """
        # If content is small enough, return as single chunk
        if len(content) <= chunk_size:
            return [content]
        
        # Split by paragraphs first
        paragraphs = content.split("\n\n")
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk and start new one
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add any remaining content
        if current_chunk:
            chunks.append(current_chunk)
        
        # If any chunks are still too large, split them further
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= chunk_size:
                final_chunks.append(chunk)
            else:
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', chunk)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                        final_chunks.append(current_chunk)
                        current_chunk = sentence
                    else:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
                
                if current_chunk:
                    final_chunks.append(current_chunk)
        
        return final_chunks 