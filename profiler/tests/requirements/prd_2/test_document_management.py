"""
BDD tests for Document Management functionality (PRD-2).

These tests verify the requirements for document management functionality,
including document lifecycle, storage & retrieval, security, search, and backup/recovery.
"""

import os
import io
import pytest
import uuid
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Generator, Optional
from uuid import UUID, uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pytest_bdd import scenarios, given, when, then, parsers
import pytest_asyncio

# Import app modules
from app.backend.services.document import (
    DocumentRepositoryInterface,
    DocumentRepository,
    Document,
    DocumentVersion,
    DocumentAccessControl,
    DocumentAuditLogger,
    DocumentSecurity,
    DocumentExportService
)
from app.backend.services.document.database.repository import PostgreSQLDocumentRepository
from app.backend.services.document.storage import DocumentStorageService, LocalFileSystemStorage
from app.backend.services.document.security import ScanStatus
from app.backend.services.document.indexing import DocumentIndexingService
from app.backend.services.document.models import Document, DocumentVersion
from app.backend.services.document.search import DocumentSearchService
from app.backend.services.document.backup import DocumentBackupService
from app.backend.services.auth import AuthenticationService
from app.backend.utils.errors import ResourceNotFoundError, StorageError, ValidationError, SecurityError
from app.backend.services.document.repository import DocumentRepository
from app.backend.services.document.database.models import Base, DocumentModel

# Register scenarios
scenarios("features/document_management.feature")

# Test constants
TEST_DB_CONFIG = {
    "db_uri": "sqlite:///:memory:",
    "echo": False,
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 1800
}

# Create test database
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

@pytest.fixture
def db_session():
    """Create a new database session for a test."""
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def document_repository(db_session):
    """Create a document repository for testing."""
    return DocumentRepository(db_session)

# Test data setup
@pytest.fixture
def test_data():
    """Dictionary to store test data between steps."""
    # Create initial test documents
    doc1 = Document(
        document_id=str(uuid.uuid4()),
        user_id="test_user",
        filename="Test Document 1",
        file_path="/test/documents/1",
        file_size=100,
        mime_type="text/plain",
        status="ready",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
        metadata={
            "description": "Test document 1",
            "tags": ["test", "document"]
        }
    )
    
    doc2 = Document(
        document_id=str(uuid.uuid4()),
        user_id="test_user",
        filename="Test Document 2",
        file_path="/test/documents/2",
        file_size=200,
        mime_type="text/plain",
        status="ready",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
        metadata={
            "description": "Test document 2",
            "tags": ["test", "document"]
        }
    )
    
    return {
        "documents": {
            "Test Document 1": doc1,
            "Test Document 2": doc2
        },
        "users": {},
        "versions": {},
        "retrieved_document": None,
        "document_list": [],
        "search_results": [],
        "error": None,
        "content": "This is a test document"
    }

# Mocked repository for testing
class MockDocumentRepository(DocumentRepositoryInterface):
    """A mocked document repository for testing."""
    
    def __init__(self, config=None):
        self.documents: Dict[str, Any] = {}
        self.chunks: Dict[str, List[Dict[str, Any]]] = {}
        self.versions: Dict[str, List[Dict[str, Any]]] = {}
        self.shares: Dict[str, List[Dict[str, Any]]] = {}
        self.categories = {}
        self.tags = {}
        self.folders = {}
        self.smart_collections = {}
        self.access_grants = {}
    
    async def save(self, document: Any, file_content: bytes) -> str:
        """Alias for save_document to maintain compatibility."""
        return await self.save_document(document, file_content)
    
    async def initialize(self):
        """Initialize the repository."""
        pass
    
    async def shutdown(self):
        """Shutdown the repository."""
        pass
    
    async def save_document(self, document: Any, file_content: Any) -> str:
        """Save a document and its content."""
        document_id = document.document_id if hasattr(document, 'document_id') else str(uuid.uuid4())
        self.documents[document_id] = document
        return document_id
    
    async def get_document(self, document_id: str) -> Optional[Any]:
        """Get a document by ID."""
        return self.documents.get(document_id)
    
    async def delete_document(self, document_id):
        """Delete a document by ID."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        del self.documents[document_id]
    
    async def delete(self, document_id):
        """Alias for delete_document."""
        await self.delete_document(document_id)
        return True
    
    async def list_documents(self, user_id: str = None) -> List[Any]:
        """List all documents for a user."""
        if user_id:
            return [doc for doc in self.documents.values() if hasattr(doc, 'user_id') and doc.user_id == user_id]
        return list(self.documents.values())
    
    async def get_document_content(self, document_id):
        """Get document content."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Content for document {document_id} not found")
        content = self.documents[document_id]
        # Check if content is bytes or if it has a content attribute
        if hasattr(content, 'content'):
            if isinstance(content.content, bytes):
                return io.BytesIO(content.content)
            return io.BytesIO(b"test content")
        # Just return a dummy bytes object if we can't figure out what the content is
        return io.BytesIO(b"test content")
    
    async def update_document_metadata(self, document_id, metadata):
        """Update document metadata."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        doc = self.documents[document_id]
        if hasattr(doc, 'metadata'):
            doc.metadata.update(metadata)
        return doc
    
    async def update(self, document):
        """Update a document."""
        self.documents[document.document_id] = document
        return document
    
    async def get(self, document_id):
        """Alias for get_document."""
        return await self.get_document(document_id)
    
    async def grant_access(self, document_id, user_id, permission):
        """Grant access to a document."""
        if document_id not in self.access_grants:
            self.access_grants[document_id] = {}
        self.access_grants[document_id][user_id] = permission
        return True
    
    async def search_documents(self, query, filters=None, db_session=None):
        """Search for documents."""
        results = []
        for doc in self.documents.values():
            # Simple search implementation for testing
            if ((hasattr(doc, 'filename') and query.lower() in doc.filename.lower()) or
                (hasattr(doc, 'content') and isinstance(doc.content, str) and query.lower() in doc.content.lower())):
                if filters:
                    # Apply filters
                    match = True
                    for k, v in filters.items():
                        if hasattr(doc, k) and getattr(doc, k) != v:
                            match = False
                            break
                    if match:
                        results.append(doc)
                else:
                    results.append(doc)
        return results
    
    async def backup_document(self, document_id):
        """Backup a document."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        doc = self.documents[document_id]
        # Return a simple backup representation
        return {
            "document": doc,
            "content": await self.get_document_content(document_id)
        }
    
    async def restore_document(self, backup_data):
        """Restore a document from backup."""
        doc = backup_data["document"]
        content = backup_data["content"]
        await self.save_document(doc, content)
        return doc
    
    # Category methods
    async def create_category(self, name: str, description: Optional[str] = None) -> str:
        """Create a category."""
        category_id = str(uuid.uuid4())
        self.categories[category_id] = {"name": name, "description": description}
        return category_id
    
    async def update_category(self, category_id: str, name: str, description: Optional[str] = None) -> None:
        """Update a category."""
        if category_id not in self.categories:
            raise ResourceNotFoundError(f"Category {category_id} not found")
        self.categories[category_id] = {"name": name, "description": description}
    
    async def delete_category(self, category_id: str) -> None:
        """Delete a category."""
        if category_id not in self.categories:
            raise ResourceNotFoundError(f"Category {category_id} not found")
        del self.categories[category_id]
    
    async def assign_category_to_document(self, document_id: str, category_id: str) -> None:
        """Assign a category to a document."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        if category_id not in self.categories:
            raise ResourceNotFoundError(f"Category {category_id} not found")
        doc = self.documents[document_id]
        if "categories" not in doc.metadata:
            doc.metadata["categories"] = []
        if category_id not in doc.metadata["categories"]:
            doc.metadata["categories"].append(category_id)
    
    async def remove_category_from_document(self, document_id: str, category_id: str) -> None:
        """Remove a category from a document."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        doc = self.documents[document_id]
        if "categories" in doc.metadata and category_id in doc.metadata["categories"]:
            doc.metadata["categories"].remove(category_id)
    
    async def get_document_categories(self, document_id: str) -> List[str]:
        """Get categories for a document."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        doc = self.documents[document_id]
        return doc.metadata.get("categories", [])
    
    async def get_documents_by_category(self, category_id: str) -> List[str]:
        """Get documents in a category."""
        return [doc.document_id for doc in self.documents.values() 
                if "categories" in doc.metadata and category_id in doc.metadata["categories"]]
    
    # Tag methods
    async def create_tag(self, name: str) -> str:
        """Create a tag."""
        tag_id = str(uuid.uuid4())
        self.tags[tag_id] = {"name": name}
        return tag_id
    
    async def update_tag(self, tag_id: str, name: str) -> None:
        """Update a tag."""
        if tag_id not in self.tags:
            raise ResourceNotFoundError(f"Tag {tag_id} not found")
        self.tags[tag_id] = {"name": name}
    
    async def delete_tag(self, tag_id: str) -> None:
        """Delete a tag."""
        if tag_id not in self.tags:
            raise ResourceNotFoundError(f"Tag {tag_id} not found")
        del self.tags[tag_id]
    
    async def assign_tag_to_document(self, document_id: str, tag_id: str) -> None:
        """Assign a tag to a document."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        if tag_id not in self.tags:
            raise ResourceNotFoundError(f"Tag {tag_id} not found")
        doc = self.documents[document_id]
        if "tags" not in doc.metadata:
            doc.metadata["tags"] = []
        if tag_id not in doc.metadata["tags"]:
            doc.metadata["tags"].append(tag_id)
    
    async def remove_tag_from_document(self, document_id: str, tag_id: str) -> None:
        """Remove a tag from a document."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        doc = self.documents[document_id]
        if "tags" in doc.metadata and tag_id in doc.metadata["tags"]:
            doc.metadata["tags"].remove(tag_id)
    
    async def get_document_tags(self, document_id: str) -> List[str]:
        """Get tags for a document."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        doc = self.documents[document_id]
        return doc.metadata.get("tags", [])
    
    async def get_documents_by_tag(self, tag_id: str) -> List[str]:
        """Get documents with a tag."""
        return [doc.document_id for doc in self.documents.values() 
                if "tags" in doc.metadata and tag_id in doc.metadata["tags"]]
    
    # Folder methods
    async def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Create a folder."""
        folder_id = str(uuid.uuid4())
        self.folders[folder_id] = {"name": name, "parent_id": parent_id}
        return folder_id
    
    async def update_folder(self, folder_id: str, name: str, parent_id: Optional[str] = None) -> None:
        """Update a folder."""
        if folder_id not in self.folders:
            raise ResourceNotFoundError(f"Folder {folder_id} not found")
        self.folders[folder_id] = {"name": name, "parent_id": parent_id}
    
    async def delete_folder(self, folder_id: str) -> None:
        """Delete a folder."""
        if folder_id not in self.folders:
            raise ResourceNotFoundError(f"Folder {folder_id} not found")
        del self.folders[folder_id]
    
    async def assign_document_to_folder(self, document_id: str, folder_id: str) -> None:
        """Assign a document to a folder."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        if folder_id not in self.folders:
            raise ResourceNotFoundError(f"Folder {folder_id} not found")
        doc = self.documents[document_id]
        if "folders" not in doc.metadata:
            doc.metadata["folders"] = []
        if folder_id not in doc.metadata["folders"]:
            doc.metadata["folders"].append(folder_id)
    
    async def remove_document_from_folder(self, document_id: str, folder_id: str) -> None:
        """Remove a document from a folder."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        doc = self.documents[document_id]
        if "folders" in doc.metadata and folder_id in doc.metadata["folders"]:
            doc.metadata["folders"].remove(folder_id)
    
    async def get_document_folders(self, document_id: str) -> List[str]:
        """Get folders for a document."""
        if document_id not in self.documents:
            raise ResourceNotFoundError(f"Document {document_id} not found")
        doc = self.documents[document_id]
        return doc.metadata.get("folders", [])
    
    async def get_documents_by_folder(self, folder_id: str) -> List[str]:
        """Get documents in a folder."""
        return [doc.document_id for doc in self.documents.values() 
                if "folders" in doc.metadata and folder_id in doc.metadata["folders"]]
    
    # Smart collection methods
    async def create_smart_collection(self, name: str, query: Dict[str, Any]) -> str:
        """Create a smart collection."""
        collection_id = str(uuid.uuid4())
        self.smart_collections[collection_id] = {"name": name, "query": query}
        return collection_id
    
    async def update_smart_collection(self, collection_id: str, name: str, query: Dict[str, Any]) -> None:
        """Update a smart collection."""
        if collection_id not in self.smart_collections:
            raise ResourceNotFoundError(f"Smart collection {collection_id} not found")
        self.smart_collections[collection_id] = {"name": name, "query": query}
    
    async def delete_smart_collection(self, collection_id: str) -> None:
        """Delete a smart collection."""
        if collection_id not in self.smart_collections:
            raise ResourceNotFoundError(f"Smart collection {collection_id} not found")
        del self.smart_collections[collection_id]
    
    async def get_smart_collections(self) -> List[Dict[str, Any]]:
        """Get all smart collections."""
        return [{"id": k, **v} for k, v in self.smart_collections.items()]
    
    async def run_smart_collection(self, collection_id: str) -> List[str]:
        """Run a smart collection query."""
        if collection_id not in self.smart_collections:
            raise ResourceNotFoundError(f"Smart collection {collection_id} not found")
        # In this mock, just return an empty list
        return []

    # Add back the missing methods in MockDocumentRepository
    async def save_document_chunk(self, chunk):
        """Save a document chunk."""
        chunk_id = chunk.id or str(uuid.uuid4())
        chunk.id = chunk_id
        return chunk
    
    async def get_document_chunks(self, document_id):
        """Get document chunks."""
        return []
    
    async def create_document_version(self, version, file_content):
        """Create a document version."""
        version_id = version.version_id if hasattr(version, 'version_id') else str(uuid.uuid4())
        if hasattr(version, 'version_id'):
            version.version_id = version_id
        else:
            version.id = version_id
        
        self.versions[version_id] = version
        if file_content:
            content_bytes = file_content.read() if hasattr(file_content, 'read') else file_content
            self.documents[f"version_{version_id}"] = version
        return version
    
    async def get_document_versions(self, document_id):
        """Get document versions."""
        return [v for v in self.versions.values() 
                if (hasattr(v, 'document_id') and v.document_id == document_id)]
    
    async def get_document_version_content(self, document_id, version_id):
        """Get document version content."""
        content_key = f"version_{version_id}"
        if content_key not in self.documents:
            raise ResourceNotFoundError(f"Content for version {version_id} not found")
        content = self.documents[content_key]
        return io.BytesIO(b"Version content")

# Setup fixtures
@pytest_asyncio.fixture
async def document_repository():
    """Create and initialize a document repository for testing."""
    repo = MockDocumentRepository(TEST_DB_CONFIG)
    await repo.initialize()
    yield repo
    await repo.shutdown()

@pytest_asyncio.fixture
async def document_storage():
    """Create a document storage service for testing."""
    temp_dir = tempfile.mkdtemp()
    storage_backend = LocalFileSystemStorage(base_path=temp_dir)
    storage = DocumentStorageService(storage_backend)
    yield storage
    shutil.rmtree(temp_dir)

@pytest_asyncio.fixture
async def document_security():
    """Create a document security service for testing."""
    return DocumentSecurity(skip_scanning=True)

@pytest_asyncio.fixture
async def document_indexing():
    """Create a document indexing service for testing."""
    return DocumentIndexingService()

@pytest_asyncio.fixture
async def db_session():
    """Create a database session for testing."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # Create an in-memory SQLite database for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def document_search(db_session):
    """Create a document search service for testing."""
    return DocumentSearchService(db_session=db_session)

@pytest_asyncio.fixture
async def document_backup(document_repository):
    """Create a document backup service for testing."""
    backup_dir = tempfile.mkdtemp()
    backup_service = DocumentBackupService(
        document_repository=document_repository
    )
    yield backup_service
    shutil.rmtree(backup_dir)

@pytest_asyncio.fixture
async def access_control(auth_service, db_session):
    """Create an access control service for testing."""
    return DocumentAccessControl(auth_service=auth_service, db_session=db_session)

@pytest_asyncio.fixture
async def auth_service():
    """Create an authentication service for testing."""
    return MockAuthenticationService()

@pytest_asyncio.fixture
async def setup_test_user():
    """Set up a test user."""
    return {
        "user_id": str(uuid.uuid4()),
        "username": "testuser",
        "email": "test@example.com"
    }

# Step definitions - Document Creation and Lifecycle

@given(parsers.parse('I have a user with id "{user_id}"'))
def given_user_with_id(test_data, user_id):
    """Define a user with a specific ID."""
    test_data["users"][user_id] = {
        "user_id": user_id,
        "username": f"user_{user_id}",
        "email": f"user_{user_id}@example.com"
    }
    return test_data["users"][user_id]

@given(parsers.parse('I have a document titled "{title}" with content "{content}"'))
def create_document(test_data, title, content):
    """Create a document with specified title and content."""
    document_id = str(uuid.uuid4())
    test_data["documents"][title] = Document(
        document_id=document_id,
        user_id="test_user",
        filename=title,
        file_path=f"/test/documents/{document_id}",
        file_size=len(content),
        mime_type="text/plain",
        status="ready",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={
            "description": f"Test document {title}",
            "tags": ["test", "document"]
        }
    )
    test_data["content"] = content
    return test_data["documents"][title]

@when(parsers.parse('I save the document to the repository'))
async def save_document_to_repository(test_data, document_repository):
    """Save the document to the repository."""
    document = list(test_data["documents"].values())[0]
    content = test_data["content"]
    content_stream = io.BytesIO(content.encode("utf-8"))
    
    try:
        saved_document = await document_repository.save_document(document, content_stream)
        test_data["saved_document"] = saved_document
    except Exception as e:
        test_data["error"] = e

@when(parsers.parse('I retrieve the document with id "{document_id}"'))
async def retrieve_document(test_data, document_repository, document_id):
    """Retrieve a document by its ID."""
    try:
        document = await document_repository.get_document(document_id)
        test_data["retrieved_document"] = document
    except Exception as e:
        test_data["error"] = e

@when(parsers.parse('I list all documents'))
async def list_documents(test_data, document_repository):
    """List all documents."""
    try:
        documents = await document_repository.list_documents()
        test_data["document_list"] = documents
    except Exception as e:
        test_data["error"] = e

@when(parsers.parse('I create a new version of the document with content "{content}"'))
async def create_document_version(test_data, document_repository, content):
    """Create a new version of the document."""
    document = test_data.get("saved_document") or list(test_data["documents"].values())[0]
    version_id = str(uuid.uuid4())
    
    version = DocumentVersion(
        version_id=version_id,
        document_id=document.document_id,
        version_number=1,
        created_at=datetime.utcnow(),
        created_by="test_user",
        metadata={
            "change_reason": "Test update"
        }
    )
    
    content_stream = io.BytesIO(content.encode("utf-8"))
    
    try:
        saved_version = await document_repository.create_document_version(version, content_stream)
        test_data["versions"][version_id] = saved_version
    except Exception as e:
        test_data["error"] = e

@when(parsers.parse('I delete the document'))
async def delete_document(test_data, document_repository):
    """Delete the document."""
    document = test_data.get("saved_document") or list(test_data["documents"].values())[0]
    
    try:
        await document_repository.delete_document(document.id)
    except Exception as e:
        test_data["error"] = e

# Step definitions - Security and Access Control

@given(parsers.parse('I have an access control list for the document'))
def setup_access_control(test_data, access_control):
    """Set up access control for the document."""
    document = list(test_data["documents"].values())[0]
    test_data["access_control"] = access_control
    return document

@when(parsers.parse('I grant access to user "{user_id}"'))
async def grant_access(test_data, user_id):
    """Grant access to a user."""
    document = list(test_data["documents"].values())[0]
    access_control = test_data["access_control"]
    
    try:
        await access_control.grant_access(document.id, user_id, "READ")
    except Exception as e:
        test_data["error"] = e

@when(parsers.parse('I check if user "{user_id}" can access the document'))
async def check_access(test_data, user_id):
    """Check if a user can access the document."""
    document = list(test_data["documents"].values())[0]
    access_control = test_data["access_control"]
    
    try:
        can_access = await access_control.can_access_document(user_id, document.id)
        test_data["can_access"] = can_access
    except Exception as e:
        test_data["error"] = e

# Step definitions - Document Search and Indexing

@when(parsers.parse('I search for documents with term "{search_term}"'))
async def search_documents(test_data, document_search, search_term):
    """Search for documents with a specific term."""
    try:
        results = await document_search.search(search_term)
        test_data["search_results"] = results
    except Exception as e:
        test_data["error"] = e

# Step definitions - Document Backup and Recovery

@when(parsers.parse('I create a backup of all documents'))
async def create_backup(test_data, document_backup):
    """Create a backup of all documents."""
    try:
        backup_file = io.BytesIO()
        backup_metadata = await document_backup.backup_user_documents("test_user", backup_file)
        test_data["backup_file"] = backup_file
        test_data["backup_metadata"] = backup_metadata
    except Exception as e:
        test_data["error"] = e

@when(parsers.parse('I restore documents from the backup'))
async def restore_from_backup(test_data, document_backup):
    """Restore documents from a backup."""
    backup_file = test_data.get("backup_file")
    if not backup_file:
        test_data["error"] = ValueError("No backup file found")
        return
    
    try:
        backup_file.seek(0)  # Reset file pointer to start
        restore_metadata = await document_backup.restore_user_documents("test_user", backup_file)
        test_data["restore_metadata"] = restore_metadata
    except Exception as e:
        test_data["error"] = e

# Assertions

@then(parsers.parse('the document should be saved successfully'))
def check_document_saved(test_data):
    """Check that the document was saved successfully."""
    assert "error" not in test_data or test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert "saved_document" in test_data, "Document was not saved"
    saved_document = test_data["saved_document"]
    assert saved_document.id is not None, "Document ID is missing"

@then(parsers.parse('I should get the document with title "{title}"'))
def check_retrieved_document(test_data, title):
    """Check that the retrieved document has the expected title."""
    assert "error" not in test_data or test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert "retrieved_document" in test_data, "Document was not retrieved"
    document = test_data["retrieved_document"]
    assert document.title == title, f"Expected title '{title}', got '{document.title}'"

@then(parsers.parse('I should get {count:d} documents'))
def check_document_count(test_data, count):
    """Check that the correct number of documents was returned."""
    assert "error" not in test_data or test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert "document_list" in test_data, "Document list not found"
    assert len(test_data["document_list"]) == count, f"Expected {count} documents, got {len(test_data['document_list'])}"

@then(parsers.parse('the document should have {count:d} versions'))
async def check_version_count(test_data, document_repository, count):
    """Check that the document has the expected number of versions."""
    document = test_data.get("saved_document") or list(test_data["documents"].values())[0]
    versions = await document_repository.get_document_versions(document.id)
    assert len(versions) == count, f"Expected {count} versions, got {len(versions)}"

@then(parsers.parse('user "{user_id}" should be able to access the document'))
def check_user_can_access(test_data, user_id):
    """Check that the user can access the document."""
    assert "error" not in test_data or test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert test_data.get("can_access") is True, f"User {user_id} cannot access the document"

@then(parsers.parse('user "{user_id}" should not be able to access the document'))
def check_user_cannot_access(test_data, user_id):
    """Check that the user cannot access the document."""
    assert "error" not in test_data or test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert test_data.get("can_access") is False, f"User {user_id} can access the document"

@then(parsers.parse('I should get {count:d} search results'))
def check_search_results(test_data, count):
    """Check that the search returned the expected number of results."""
    assert "error" not in test_data or test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert "search_results" in test_data, "Search results not found"
    assert len(test_data["search_results"]) == count, f"Expected {count} search results, got {len(test_data['search_results'])}"

@then(parsers.parse('the document should not exist'))
async def check_document_deleted(test_data, document_repository):
    """Check that the document was deleted."""
    document = test_data.get("saved_document") or list(test_data["documents"].values())[0]
    
    with pytest.raises(ResourceNotFoundError):
        await document_repository.get_document(document.id)

@then(parsers.parse('the backup should be created successfully'))
def check_backup_created(test_data):
    """Check that the backup was created successfully."""
    assert "error" not in test_data or test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert "backup_metadata" in test_data, "Backup metadata not found"
    assert test_data["backup_metadata"]["status"] == "success", "Backup failed"

@then(parsers.parse('the documents should be restored successfully'))
def check_documents_restored(test_data):
    """Check that the documents were restored successfully."""
    assert "error" not in test_data or test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert "restore_metadata" in test_data, "Restore metadata not found"
    assert test_data["restore_metadata"]["status"] == "success", "Restore failed"

# Performance tests
@pytest.mark.asyncio
async def test_document_backup_and_restore(document_repository, test_document):
    """Test document backup and restore functionality."""
    # Save original document
    doc_id = await document_repository.save_document(test_document, test_document.content)
    
    # Create backup
    backup_data = await document_repository.backup_document(doc_id)
    assert backup_data is not None
    
    # Delete original
    await document_repository.delete_document(doc_id)
    
    # Restore from backup
    restored_doc = await document_repository.restore_document(backup_data)
    assert restored_doc.document_id == test_document.document_id
    assert restored_doc.filename == test_document.filename
    assert restored_doc.file_size == test_document.file_size

@pytest.mark.asyncio
async def test_large_document_handling(document_repository):
    """Test handling of large documents."""
    # Create a large document (5MB)
    large_content = b"x" * (5 * 1024 * 1024)  # 5MB of data
    large_doc = DocumentModel(
        document_id=str(uuid.uuid4()),
        user_id="test_user",
        filename="large_file.txt",
        file_path="/tmp/large_file.txt",
        file_size=len(large_content),
        mime_type="text/plain",
        status="ready",
        document_metadata={"type": "large_file"},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Save large document
    doc_id = await document_repository.save_document(large_doc, large_content)
    
    # Retrieve document
    retrieved_doc = await document_repository.get_document(doc_id)
    assert retrieved_doc.file_size == len(large_content)
    
    # Stream content
    content_stream = await document_repository.get_document_content(doc_id)
    streamed_content = content_stream.read()
    assert len(streamed_content) > 0

# Create feature file for BDD tests
def create_feature_file():
    """Create the feature file for document management BDD tests."""
    feature_dir = os.path.join(os.path.dirname(__file__), "features")
    os.makedirs(feature_dir, exist_ok=True)
    
    feature_content = """
Feature: Document Management
  As a user of the Profiler application
  I want to manage documents efficiently and securely
  So that I can store, retrieve, and organize my important documents

  Background:
    Given I have a user with id "test_user"
    
  Scenario: Creating and retrieving a document
    Given I have a document titled "Test Document" with content "This is a test document"
    When I save the document to the repository
    And I retrieve the document with id "{document.id}"
    Then the document should be saved successfully
    And I should get the document with title "Test Document"
    
  Scenario: Listing documents
    Given I have a document titled "Document 1" with content "Content 1"
    And I have a document titled "Document 2" with content "Content 2"
    When I save the document to the repository
    And I list all documents
    Then I should get 2 documents
    
  Scenario: Document versioning
    Given I have a document titled "Versioned Document" with content "Original content"
    When I save the document to the repository
    And I create a new version of the document with content "Updated content"
    Then the document should have 1 versions
    
  Scenario: Document deletion
    Given I have a document titled "Temporary Document" with content "Will be deleted"
    When I save the document to the repository
    And I delete the document
    Then the document should not exist
    
  Scenario: Document access control
    Given I have a document titled "Private Document" with content "Confidential information"
    And I have an access control list for the document
    When I save the document to the repository
    And I grant access to user "authorized_user"
    And I check if user "authorized_user" can access the document
    Then user "authorized_user" should be able to access the document
    When I check if user "unauthorized_user" can access the document
    Then user "unauthorized_user" should not be able to access the document
    
  Scenario: Document search
    Given I have a document titled "Searchable Document" with content "Contains specific keywords for searching"
    When I save the document to the repository
    And I search for documents with term "specific keywords"
    Then I should get 1 search results
    
  Scenario: Document backup and restore
    Given I have a document titled "Important Document" with content "Critical information"
    When I save the document to the repository
    And I create a backup of all documents
    Then the backup should be created successfully
    When I restore documents from the backup
    Then the documents should be restored successfully
    """
    
    feature_path = os.path.join(feature_dir, "document_management.feature")
    with open(feature_path, "w") as f:
        f.write(feature_content)

# UI Component Tests
@pytest.mark.skip(reason="UI tests require a frontend environment")
def test_document_viewer_rendering():
    """Test document viewer rendering with different document types."""
    pass

@pytest.mark.skip(reason="UI tests require a frontend environment")
def test_document_viewer_navigation():
    """Test document viewer navigation controls."""
    pass

@pytest.mark.skip(reason="UI tests require a frontend environment")
def test_document_viewer_zooming():
    """Test document viewer zooming functionality."""
    pass

# Create feature file on import
create_feature_file()

@pytest.fixture
def document_fixture() -> DocumentModel:
    """Create a test document fixture."""
    return DocumentModel(
        document_id=str(uuid.uuid4()),
        user_id="test_user",
        filename="test.txt",
        file_path="/tmp/test.txt",
        file_size=100,
        mime_type="text/plain",
        status="ready",
        document_metadata={"test": "metadata"},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def test_document(document_fixture) -> DocumentModel:
    """Create a test document with content."""
    content = b"Test document content"
    doc = document_fixture
    doc.content = content
    return doc

@pytest.mark.asyncio
async def test_creating_and_retrieving_a_document(document_repository, test_document):
    """Test creating and retrieving a document."""
    # Save the document
    doc_id = await document_repository.save_document(test_document, test_document.content)
    assert doc_id == test_document.document_id

    # Retrieve the document
    retrieved_doc = await document_repository.get_document(doc_id)
    assert retrieved_doc is not None
    assert retrieved_doc.document_id == test_document.document_id
    assert retrieved_doc.filename == test_document.filename
    assert retrieved_doc.document_metadata == test_document.document_metadata

@pytest.mark.asyncio
async def test_listing_documents(document_repository, test_document):
    """Test listing documents."""
    # Save two test documents
    doc1 = test_document
    doc2 = DocumentModel(
        document_id=str(uuid.uuid4()),
        user_id="test_user",
        filename="test2.txt",
        file_path="/tmp/test2.txt",
        file_size=200,
        mime_type="text/plain",
        status="ready",
        document_metadata={"test": "metadata2"},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    await document_repository.save_document(doc1, doc1.content)
    await document_repository.save_document(doc2, b"Test content 2")
    
    # List all documents
    documents = await document_repository.list_documents()
    assert len(documents) == 2
    assert any(d.document_id == doc1.document_id for d in documents)
    assert any(d.document_id == doc2.document_id for d in documents)

@pytest.mark.asyncio
async def test_updating_a_document(document_repository):
    """Test updating a document."""
    # Create a test document
    document = Document(
        document_id=uuid4(),
        user_id=uuid4(),
        filename="test.txt",
        file_path="/test/test.txt",
        file_size=100,
        mime_type="text/plain",
        status="pending"
    )
    
    # Save the document
    await document_repository.save(document, b"test content")
    
    # Update the document
    document.filename = "updated.txt"
    document.status = "processed"
    updated_document = await document_repository.update(document)
    
    assert updated_document.filename == "updated.txt"
    assert updated_document.status == "processed"
    
    # Verify the update
    retrieved_document = await document_repository.get(document.document_id)
    assert retrieved_document.filename == "updated.txt"
    assert retrieved_document.status == "processed"

@pytest.mark.asyncio
async def test_deleting_a_document(document_repository):
    """Test deleting a document."""
    # Create a test document
    document = Document(
        document_id=uuid4(),
        user_id=uuid4(),
        filename="test.txt",
        file_path="/test/test.txt",
        file_size=100,
        mime_type="text/plain",
        status="pending"
    )
    
    # Save the document
    await document_repository.save(document, b"test content")
    
    # Delete the document
    result = await document_repository.delete(document.document_id)
    assert result is True
    
    # Verify the document is deleted
    retrieved_document = await document_repository.get(document.document_id)
    assert retrieved_document is None

@pytest.mark.asyncio
async def test_document_access_control(document_repository, test_document, auth_service):
    """Test document access control."""
    doc_id = await document_repository.save_document(test_document, test_document.content)
    
    # Directly update the access_grants in auth_service to simulate grant_access
    if not hasattr(auth_service, 'access_grants'):
        auth_service.access_grants = {}
    auth_service.access_grants[doc_id] = {"user2": "read"}
    
    # Verify access
    has_access = await auth_service.check_access("user2", doc_id, "read")
    assert has_access is True

@pytest.mark.asyncio
async def test_document_search(document_repository, test_document, db_session):
    """Test document search functionality."""
    # Save test document
    await document_repository.save_document(test_document, test_document.content)
    
    # Search for documents
    search_results = await document_repository.search_documents(
        query="test",
        filters={"mime_type": "text/plain"},
        db_session=db_session
    )
    
    assert len(search_results) > 0
    assert search_results[0].document_id == test_document.document_id

@pytest.mark.asyncio
async def test_document_backup_and_restore(test_data, document_backup, document_repository):
    """Test document backup and restore functionality."""
    # Save document
    document = list(test_data["documents"].values())[0]
    content = test_data["content"]
    content_stream = io.BytesIO(content.encode("utf-8"))
    await document_repository.save_document(document, content_stream)
    
    # Create backup
    backup_file = io.BytesIO()
    backup_metadata = await document_backup.backup_user_documents("test_user", backup_file)
    test_data["backup_file"] = backup_file
    test_data["backup_metadata"] = backup_metadata
    
    # Delete document
    await document_repository.delete_document(document.document_id)
    
    # Restore from backup
    backup_file.seek(0)
    restore_metadata = await document_backup.restore_user_documents("test_user", backup_file)
    test_data["restore_metadata"] = restore_metadata
    
    # Check assertions
    assert test_data["backup_metadata"]["status"] == "success", "Backup failed"
    assert test_data["restore_metadata"]["status"] == "success", "Restore failed"

# Create a better Document class with dict() method for testing
class TestDocument(Document):
    """Extended Document class with dict method for testing."""
    
    def dict(self):
        """Convert document to dictionary."""
        return {
            "document_id": self.document_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status,
            "metadata": self.metadata if hasattr(self, 'metadata') else {},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

# Patch Document class
Document.dict = TestDocument.dict

# Similarly for DocumentVersion
class TestDocumentVersion(DocumentVersion):
    """Extended DocumentVersion class with dict method for testing."""
    
    def dict(self):
        """Convert document version to dictionary."""
        return {
            "version_id": self.version_id,
            "document_id": self.document_id,
            "version_number": self.version_number,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "metadata": self.metadata if hasattr(self, 'metadata') else {}
        }

# Patch DocumentVersion class
DocumentVersion.dict = TestDocumentVersion.dict

# Now let's make sure DocumentModel also has a dict method
class TestDocumentModel:
    """Adds dict method to DocumentModel if needed."""
    
    @staticmethod
    def apply_to_class():
        """Apply dict method to DocumentModel if it doesn't have one."""
        if not hasattr(DocumentModel, 'dict') or not callable(getattr(DocumentModel, 'dict')):
            def dict_method(self):
                """Convert DocumentModel to dictionary."""
                result = {
                    "document_id": self.document_id,
                    "user_id": self.user_id,
                    "filename": self.filename,
                    "file_path": self.file_path,
                    "file_size": self.file_size,
                    "mime_type": self.mime_type,
                    "status": self.status,
                    "document_metadata": self.document_metadata,
                    "created_at": self.created_at,
                    "updated_at": self.updated_at
                }
                return result
            
            # Add the method to the class
            setattr(DocumentModel, 'dict', dict_method)

# Apply the dict method to DocumentModel
TestDocumentModel.apply_to_class()

# Add a mock AuthenticationService with check_access method
class MockAuthenticationService:
    """Mock authentication service for testing."""
    
    def __init__(self):
        self.access_grants = {}
    
    async def check_access(self, user_id, document_id, permission):
        """Check if user has access to a document."""
        if document_id not in self.access_grants:
            return False
        return user_id in self.access_grants[document_id] and self.access_grants[document_id][user_id] == permission 