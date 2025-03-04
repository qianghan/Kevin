"""
Unit tests for the Trainer class.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from langchain.schema import Document
from src.models.trainer import Trainer, CustomHuggingFaceEmbeddings
from src.core.document_processor import DocumentProcessor

class MockDocumentProcessor:
    """Mock document processor for testing."""
    
    def __init__(self, documents: List[Document]):
        self.documents = documents
        
    def get_all_documents(self) -> List[Document]:
        return self.documents

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    # Create a long document that will be split into chunks
    long_text = "This is a test document about university programs. " * 50  # This will be split into chunks
    
    return [
        Document(
            metadata={"source": "test1.txt", "type": "program"},
            page_content=long_text
        ),
        Document(
            metadata={"source": "test2.txt", "type": "admission"},
            page_content="Another test document about admission requirements."
        ),
        Document(
            metadata={"source": "test3.txt", "type": "student_life"},
            page_content="A third document about campus life and student activities."
        )
    ]

@pytest.fixture
def trainer(temp_dir, sample_documents):
    """Create a Trainer instance for testing."""
    settings = {
        "VECTORDB_PATH": os.path.join(temp_dir, "vectordb"),
        "MODEL_PATH": os.path.join(temp_dir, "models"),
        "CHUNK_SIZE": 500,  # Smaller chunks for testing
        "CHUNK_OVERLAP": 50,
        "BATCH_SIZE": 2,
        "DEVICE": "cpu"  # Use CPU for testing
    }
    
    doc_processor = MockDocumentProcessor(sample_documents)
    return Trainer(doc_processor, settings)

def test_clean_documents(trainer, sample_documents):
    """Test document cleaning functionality."""
    cleaned_docs = trainer.clean_documents(sample_documents)
    
    assert len(cleaned_docs) == len(sample_documents)
    for doc in cleaned_docs:
        assert isinstance(doc, Document)
        assert "cleaned_at" in doc.metadata
        assert len(doc.page_content.split()) > 0

def test_create_chunks(trainer, sample_documents):
    """Test document chunking functionality."""
    chunks = trainer.create_chunks(sample_documents)
    
    assert len(chunks) > len(sample_documents)  # Should create multiple chunks
    for chunk in chunks:
        assert isinstance(chunk, Document)
        assert len(chunk.page_content) <= trainer.settings["CHUNK_SIZE"]

def test_create_vectordb(trainer, sample_documents):
    """Test vector database creation."""
    vectordb = trainer.create_vectordb(sample_documents)
    
    # Check if vector database was created
    assert os.path.exists(trainer.vectordb_path)
    assert os.path.exists(os.path.join(trainer.vectordb_path, "metadata.json"))
    assert os.path.exists(os.path.join(trainer.vectordb_path, "embeddings_cache.pkl"))
    
    # Check metadata
    with open(os.path.join(trainer.vectordb_path, "metadata.json"), "r") as f:
        metadata = f.read()
        assert "chunk_size" in metadata
        assert "embedding_model" in metadata
        assert "num_chunks" in metadata

def test_load_vectordb(trainer, sample_documents):
    """Test vector database loading."""
    # First create a vector database
    trainer.create_vectordb(sample_documents)
    
    # Then load it
    vectordb = trainer.load_vectordb()
    assert vectordb is not None

def test_train(trainer):
    """Test the complete training process."""
    trainer.train()
    
    # Check if vector database was created
    assert os.path.exists(trainer.vectordb_path)
    assert os.path.exists(os.path.join(trainer.vectordb_path, "metadata.json"))

def test_empty_documents(trainer):
    """Test handling of empty documents."""
    # Create a trainer with empty documents
    empty_processor = MockDocumentProcessor([])
    empty_trainer = Trainer(empty_processor, trainer.settings)
    
    # Should raise ValueError when trying to train with no documents
    with pytest.raises(ValueError, match="No documents found for training"):
        empty_trainer.train()

def test_custom_embeddings():
    """Test the CustomHuggingFaceEmbeddings class."""
    embeddings = CustomHuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        batch_size=2,
        device="cpu"
    )
    
    # Test document embedding
    texts = ["This is a test.", "Another test document."]
    doc_embeddings = embeddings.embed_documents(texts)
    assert len(doc_embeddings) == len(texts)
    assert len(doc_embeddings[0]) > 0
    
    # Test query embedding
    query = "Test query"
    query_embedding = embeddings.embed_query(query)
    assert len(query_embedding) > 0
    
    # Test caching
    cached_embeddings = embeddings.embed_documents(texts)
    assert cached_embeddings == doc_embeddings  # Should return cached results

def test_invalid_settings(trainer):
    """Test handling of invalid settings."""
    invalid_settings = {
        "CHUNK_SIZE": -1,  # Invalid chunk size
        "CHUNK_OVERLAP": 1000  # Overlap larger than chunk size
    }
    
    # Should raise ValueError when creating chunks with invalid settings
    with pytest.raises(ValueError):
        trainer.settings.update(invalid_settings)
        trainer.create_chunks(trainer.document_processor.get_all_documents()) 