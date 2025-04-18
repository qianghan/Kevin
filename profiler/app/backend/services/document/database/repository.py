"""
PostgreSQL repository implementation for Document Service.

This module provides a concrete implementation of the DocumentRepositoryInterface using PostgreSQL.
"""

import json
import uuid
import os
import io
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, BinaryIO, cast

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from app.backend.utils.errors import ResourceNotFoundError, StorageError
from app.backend.utils.logging import get_logger
from ..interfaces import DocumentRepositoryInterface
from ..models import Document, DocumentChunk, DocumentVersion
from .connection import DatabaseManager
from .models import DocumentModel, DocumentChunkModel, DocumentVersionModel

logger = get_logger(__name__)


class PostgreSQLDocumentRepository(DocumentRepositoryInterface):
    """Document repository implementation using PostgreSQL."""
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None, file_storage_path: Optional[str] = None):
        """
        Initialize the repository.
        
        Args:
            db_config: Optional database configuration dictionary
            file_storage_path: Optional path to store document files. Defaults to 'data/documents'
        """
        self.db_manager = DatabaseManager(db_config)
        self.file_storage_path = file_storage_path or os.path.join(os.getcwd(), 'data', 'documents')
    
    async def initialize(self) -> None:
        """Initialize the repository, setting up database connection and storage."""
        try:
            await self.db_manager.initialize()
            
            # Ensure file storage path exists
            os.makedirs(self.file_storage_path, exist_ok=True)
            
            logger.info(f"Initialized PostgreSQLDocumentRepository with storage path: {self.file_storage_path}")
        except Exception as e:
            logger.error(f"Failed to initialize document repository: {str(e)}")
            raise StorageError(f"Failed to initialize document repository: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the repository, closing database connection."""
        await self.db_manager.shutdown()
        logger.info("Shutdown PostgreSQLDocumentRepository")
    
    async def save_document(self, document: Document, file_content: Optional[BinaryIO] = None) -> Document:
        """
        Save a document to the repository.
        
        Args:
            document: The document to save
            file_content: Optional file content stream
            
        Returns:
            The saved document
            
        Raises:
            StorageError: If the document cannot be saved
        """
        try:
            # Update timestamps
            current_time = datetime.utcnow()
            document.updated_at = current_time.isoformat()
            
            # Generate document_id if not exists
            if not document.document_id:
                document.document_id = str(uuid.uuid4())
            
            # Store file if provided
            if file_content:
                # Create user directory if it doesn't exist
                user_dir = os.path.join(self.file_storage_path, document.user_id)
                os.makedirs(user_dir, exist_ok=True)
                
                # Define file path
                file_ext = os.path.splitext(document.filename)[1]
                file_name = f"{document.document_id}{file_ext}"
                rel_file_path = os.path.join(document.user_id, file_name)
                abs_file_path = os.path.join(self.file_storage_path, rel_file_path)
                
                # Save file
                with open(abs_file_path, 'wb') as f:
                    shutil.copyfileobj(file_content, f)
                
                # Update document with file path
                document.file_path = rel_file_path
                document.status = "ready"
            
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Check if document exists
                    stmt = select(DocumentModel).where(DocumentModel.document_id == document.document_id)
                    result = await session.execute(stmt)
                    document_model = result.scalar_one_or_none()
                    
                    if document_model:
                        # Update existing document
                        document_model.user_id = document.user_id
                        document_model.profile_id = document.profile_id
                        document_model.filename = document.filename
                        document_model.file_path = document.file_path
                        document_model.file_size = document.file_size
                        document_model.mime_type = document.mime_type
                        document_model.status = document.status
                        document_model.processed_at = datetime.fromisoformat(document.processed_at) if document.processed_at else None
                        document_model.metadata = json.dumps(document.metadata)
                        document_model.updated_at = current_time
                    else:
                        # Create new document
                        document_model = DocumentModel(
                            document_id=document.document_id,
                            user_id=document.user_id,
                            profile_id=document.profile_id,
                            filename=document.filename,
                            file_path=document.file_path,
                            file_size=document.file_size,
                            mime_type=document.mime_type,
                            status=document.status,
                            processed_at=datetime.fromisoformat(document.processed_at) if document.processed_at else None,
                            created_at=current_time,
                            updated_at=current_time,
                            metadata=json.dumps(document.metadata)
                        )
                        session.add(document_model)
            
            logger.info(f"Saved document {document.document_id} for user {document.user_id}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to save document: {str(e)}")
            raise StorageError(f"Failed to save document: {str(e)}")
    
    async def get_document(self, document_id: str) -> Document:
        """
        Get a document by ID.
        
        Args:
            document_id: The ID of the document to get
            
        Returns:
            The document
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document cannot be retrieved
        """
        try:
            async with self.db_manager.get_session() as session:
                # Get document
                stmt = select(DocumentModel).where(DocumentModel.document_id == document_id)
                result = await session.execute(stmt)
                document_model = result.scalar_one_or_none()
                
                if not document_model:
                    raise ResourceNotFoundError(f"Document {document_id} not found")
                
                # Build Document object
                document = Document(
                    document_id=document_model.document_id,
                    user_id=document_model.user_id,
                    profile_id=document_model.profile_id,
                    filename=document_model.filename,
                    file_path=document_model.file_path,
                    file_size=document_model.file_size,
                    mime_type=document_model.mime_type,
                    status=document_model.status,
                    processed_at=document_model.processed_at.isoformat() if document_model.processed_at else None,
                    created_at=document_model.created_at.isoformat(),
                    updated_at=document_model.updated_at.isoformat(),
                    metadata=json.loads(document_model.metadata) if document_model.metadata else {}
                )
                
                logger.info(f"Retrieved document {document_id}")
                return document
                
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve document {document_id}: {str(e)}")
            raise StorageError(f"Failed to retrieve document: {str(e)}")
    
    async def delete_document(self, document_id: str) -> None:
        """
        Delete a document by ID.
        
        Args:
            document_id: The ID of the document to delete
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document cannot be deleted
        """
        try:
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Get document to check it exists and to get file path
                    stmt = select(DocumentModel).where(DocumentModel.document_id == document_id)
                    result = await session.execute(stmt)
                    document_model = result.scalar_one_or_none()
                    
                    if not document_model:
                        raise ResourceNotFoundError(f"Document {document_id} not found")
                    
                    # Get file path to delete
                    file_path = document_model.file_path
                    abs_file_path = os.path.join(self.file_storage_path, file_path)
                    
                    # Delete the document record
                    stmt = delete(DocumentModel).where(DocumentModel.document_id == document_id)
                    await session.execute(stmt)
            
            # Delete file if it exists
            if os.path.exists(abs_file_path):
                os.remove(abs_file_path)
            
            # Delete version files
            stmt = select(DocumentVersionModel).where(DocumentVersionModel.document_id == document_id)
            async with self.db_manager.get_session() as session:
                result = await session.execute(stmt)
                version_models = result.scalars().all()
                
                for version in version_models:
                    version_path = os.path.join(self.file_storage_path, version.file_path)
                    if os.path.exists(version_path):
                        os.remove(version_path)
            
            logger.info(f"Deleted document {document_id}")
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise StorageError(f"Failed to delete document: {str(e)}")
    
    async def list_documents(self, user_id: Optional[str] = None, profile_id: Optional[str] = None) -> List[Document]:
        """
        List documents, optionally filtered by user ID or profile ID.
        
        Args:
            user_id: Optional user ID to filter by
            profile_id: Optional profile ID to filter by
            
        Returns:
            List of documents
            
        Raises:
            StorageError: If the documents cannot be listed
        """
        try:
            async with self.db_manager.get_session() as session:
                # Build query
                query = select(DocumentModel)
                
                if user_id:
                    query = query.where(DocumentModel.user_id == user_id)
                
                if profile_id:
                    query = query.where(DocumentModel.profile_id == profile_id)
                
                # Execute query
                result = await session.execute(query)
                document_models = result.scalars().all()
                
                # Convert to domain models
                documents = []
                for model in document_models:
                    document = Document(
                        document_id=model.document_id,
                        user_id=model.user_id,
                        profile_id=model.profile_id,
                        filename=model.filename,
                        file_path=model.file_path,
                        file_size=model.file_size,
                        mime_type=model.mime_type,
                        status=model.status,
                        processed_at=model.processed_at.isoformat() if model.processed_at else None,
                        created_at=model.created_at.isoformat(),
                        updated_at=model.updated_at.isoformat(),
                        metadata=json.loads(model.metadata) if model.metadata else {}
                    )
                    documents.append(document)
                
                filter_info = []
                if user_id:
                    filter_info.append(f"user_id={user_id}")
                if profile_id:
                    filter_info.append(f"profile_id={profile_id}")
                
                filter_str = ", ".join(filter_info) if filter_info else "no filters"
                logger.info(f"Listed {len(documents)} documents with {filter_str}")
                return documents
                
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            raise StorageError(f"Failed to list documents: {str(e)}")
    
    async def get_document_content(self, document_id: str) -> BinaryIO:
        """
        Get the binary content of a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            File-like object with document content
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document content cannot be retrieved
        """
        try:
            # Get document to get file path
            document = await self.get_document(document_id)
            
            # Get absolute file path
            abs_file_path = os.path.join(self.file_storage_path, document.file_path)
            
            # Check if file exists
            if not os.path.exists(abs_file_path):
                raise ResourceNotFoundError(f"Document file for {document_id} not found at {abs_file_path}")
            
            # Open file and return
            file_content = open(abs_file_path, 'rb')
            return cast(BinaryIO, file_content)
            
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to get document content for {document_id}: {str(e)}")
            raise StorageError(f"Failed to get document content: {str(e)}")
    
    async def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> Document:
        """
        Update the metadata of a document.
        
        Args:
            document_id: The ID of the document
            metadata: New metadata to update or add
            
        Returns:
            The updated document
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document metadata cannot be updated
        """
        try:
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Get document to check it exists
                    stmt = select(DocumentModel).where(DocumentModel.document_id == document_id)
                    result = await session.execute(stmt)
                    document_model = result.scalar_one_or_none()
                    
                    if not document_model:
                        raise ResourceNotFoundError(f"Document {document_id} not found")
                    
                    # Update metadata
                    current_metadata = json.loads(document_model.metadata) if document_model.metadata else {}
                    current_metadata.update(metadata)
                    
                    # Save updated metadata
                    document_model.metadata = json.dumps(current_metadata)
                    document_model.updated_at = datetime.utcnow()
            
            # Get updated document
            return await self.get_document(document_id)
            
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to update document metadata for {document_id}: {str(e)}")
            raise StorageError(f"Failed to update document metadata: {str(e)}")
    
    async def save_document_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """
        Save a document chunk to the repository.
        
        Args:
            chunk: The document chunk to save
            
        Returns:
            The saved document chunk
            
        Raises:
            StorageError: If the document chunk cannot be saved
        """
        try:
            # Generate chunk_id if not exists
            if not chunk.chunk_id:
                chunk.chunk_id = str(uuid.uuid4())
            
            # Verify document exists
            try:
                await self.get_document(chunk.document_id)
            except ResourceNotFoundError:
                raise ResourceNotFoundError(f"Document {chunk.document_id} not found for chunk")
            
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Check if chunk exists
                    stmt = select(DocumentChunkModel).where(
                        DocumentChunkModel.chunk_id == chunk.chunk_id
                    )
                    result = await session.execute(stmt)
                    chunk_model = result.scalar_one_or_none()
                    
                    if chunk_model:
                        # Update existing chunk
                        chunk_model.document_id = chunk.document_id
                        chunk_model.chunk_index = chunk.chunk_index
                        chunk_model.chunk_text = chunk.chunk_text
                        chunk_model.embedding = json.dumps(chunk.embedding) if chunk.embedding else None
                        chunk_model.metadata = json.dumps(chunk.metadata)
                    else:
                        # Create new chunk
                        chunk_model = DocumentChunkModel(
                            chunk_id=chunk.chunk_id,
                            document_id=chunk.document_id,
                            chunk_index=chunk.chunk_index,
                            chunk_text=chunk.chunk_text,
                            embedding=json.dumps(chunk.embedding) if chunk.embedding else None,
                            created_at=datetime.utcnow(),
                            metadata=json.dumps(chunk.metadata)
                        )
                        session.add(chunk_model)
            
            logger.info(f"Saved document chunk {chunk.chunk_id} for document {chunk.document_id}")
            return chunk
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to save document chunk: {str(e)}")
            raise StorageError(f"Failed to save document chunk: {str(e)}")
    
    async def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """
        Get all chunks for a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            List of document chunks
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document chunks cannot be retrieved
        """
        try:
            # Verify document exists
            await self.get_document(document_id)
            
            async with self.db_manager.get_session() as session:
                # Get chunks
                stmt = select(DocumentChunkModel).where(
                    DocumentChunkModel.document_id == document_id
                ).order_by(DocumentChunkModel.chunk_index)
                
                result = await session.execute(stmt)
                chunk_models = result.scalars().all()
                
                # Convert to domain models
                chunks = []
                for model in chunk_models:
                    embedding = json.loads(model.embedding) if model.embedding else None
                    chunk = DocumentChunk(
                        chunk_id=model.chunk_id,
                        document_id=model.document_id,
                        chunk_index=model.chunk_index,
                        chunk_text=model.chunk_text,
                        embedding=embedding,
                        created_at=model.created_at.isoformat(),
                        metadata=json.loads(model.metadata) if model.metadata else {}
                    )
                    chunks.append(chunk)
                
                logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
                return chunks
                
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve document chunks for {document_id}: {str(e)}")
            raise StorageError(f"Failed to retrieve document chunks: {str(e)}")
    
    async def create_document_version(self, version: DocumentVersion, file_content: BinaryIO) -> DocumentVersion:
        """
        Create a new version of a document.
        
        Args:
            version: The document version to create
            file_content: File content stream for the new version
            
        Returns:
            The created document version
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document version cannot be created
        """
        try:
            # Get document to verify it exists and get information
            document = await self.get_document(version.document_id)
            
            # Generate version_id if not exists
            if not version.version_id:
                version.version_id = str(uuid.uuid4())
            
            # Create user directory if it doesn't exist
            user_dir = os.path.join(self.file_storage_path, document.user_id, 'versions')
            os.makedirs(user_dir, exist_ok=True)
            
            # Define file path
            file_ext = os.path.splitext(document.filename)[1]
            file_name = f"{version.document_id}_v{version.version_number}{file_ext}"
            rel_file_path = os.path.join(document.user_id, 'versions', file_name)
            abs_file_path = os.path.join(self.file_storage_path, rel_file_path)
            
            # Save file
            with open(abs_file_path, 'wb') as f:
                shutil.copyfileobj(file_content, f)
            
            # Set file path and size
            version.file_path = rel_file_path
            file_size = os.path.getsize(abs_file_path)
            version.file_size = file_size
            
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Create new version
                    version_model = DocumentVersionModel(
                        version_id=version.version_id,
                        document_id=version.document_id,
                        version_number=version.version_number,
                        file_path=version.file_path,
                        file_size=version.file_size,
                        created_at=datetime.utcnow(),
                        created_by=version.created_by,
                        comment=version.comment,
                        metadata=json.dumps(version.metadata)
                    )
                    session.add(version_model)
            
            logger.info(f"Created version {version.version_number} for document {version.document_id}")
            return version
            
        except ResourceNotFoundError:
            logger.error(f"Document {version.document_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to create document version: {str(e)}")
            raise StorageError(f"Failed to create document version: {str(e)}")
    
    async def get_document_versions(self, document_id: str) -> List[DocumentVersion]:
        """
        Get all versions of a document.
        
        Args:
            document_id: The ID of the document
            
        Returns:
            List of document versions
            
        Raises:
            ResourceNotFoundError: If the document does not exist
            StorageError: If the document versions cannot be retrieved
        """
        try:
            # Verify document exists
            await self.get_document(document_id)
            
            async with self.db_manager.get_session() as session:
                # Get versions
                stmt = select(DocumentVersionModel).where(
                    DocumentVersionModel.document_id == document_id
                ).order_by(DocumentVersionModel.version_number)
                
                result = await session.execute(stmt)
                version_models = result.scalars().all()
                
                # Convert to domain models
                versions = []
                for model in version_models:
                    version = DocumentVersion(
                        version_id=model.version_id,
                        document_id=model.document_id,
                        version_number=model.version_number,
                        file_path=model.file_path,
                        file_size=model.file_size,
                        created_at=model.created_at.isoformat(),
                        created_by=model.created_by,
                        comment=model.comment,
                        metadata=json.loads(model.metadata) if model.metadata else {}
                    )
                    versions.append(version)
                
                logger.info(f"Retrieved {len(versions)} versions for document {document_id}")
                return versions
                
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve document versions for {document_id}: {str(e)}")
            raise StorageError(f"Failed to retrieve document versions: {str(e)}")
    
    async def get_document_version_content(self, document_id: str, version_id: str) -> BinaryIO:
        """
        Get the binary content of a document version.
        
        Args:
            document_id: The ID of the document
            version_id: The ID of the version
            
        Returns:
            File-like object with document version content
            
        Raises:
            ResourceNotFoundError: If the document or version does not exist
            StorageError: If the document version content cannot be retrieved
        """
        try:
            # Verify document exists
            await self.get_document(document_id)
            
            async with self.db_manager.get_session() as session:
                # Get version
                stmt = select(DocumentVersionModel).where(
                    DocumentVersionModel.document_id == document_id,
                    DocumentVersionModel.version_id == version_id
                )
                result = await session.execute(stmt)
                version_model = result.scalar_one_or_none()
                
                if not version_model:
                    raise ResourceNotFoundError(f"Version {version_id} not found for document {document_id}")
                
                # Get absolute file path
                abs_file_path = os.path.join(self.file_storage_path, version_model.file_path)
                
                # Check if file exists
                if not os.path.exists(abs_file_path):
                    raise ResourceNotFoundError(f"Version file not found at {abs_file_path}")
                
                # Open file and return
                file_content = open(abs_file_path, 'rb')
                return cast(BinaryIO, file_content)
                
        except ResourceNotFoundError:
            logger.error(f"Document {document_id} or version {version_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to get document version content for {document_id}, version {version_id}: {str(e)}")
            raise StorageError(f"Failed to get document version content: {str(e)}") 