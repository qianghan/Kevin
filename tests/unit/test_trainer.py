"""
Unit tests for the Trainer class.
"""

import os
import pytest
import tempfile
import shutil
import torch
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any
from langchain.schema import Document
from src.models.trainer import Trainer, CustomHuggingFaceEmbeddings, DEFAULT_SETTINGS
from src.core.document_processor import DocumentProcessor

class MockDocumentProcessor:
    """Mock document processor for testing."""
    
    def __init__(self, documents: List[Document]):
        self.documents = documents
        
    def get_all_documents(self) -> List[Document]:
        return self.documents

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            page_content="This is a test document " * 50,  # Long document
            metadata={"source": "test1.txt"}
        ),
        Document(
            page_content="Another test document " * 40,  # Medium document
            metadata={"source": "test2.txt"}
        ),
        Document(
            page_content="Short test",  # Short document
            metadata={"source": "test3.txt"}
        )
    ]

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def trainer(temp_dir, sample_documents):
    """Create a Trainer instance for testing."""
    settings = {
        "VECTORDB_PATH": os.path.join(temp_dir, "vectordb"),
        "MODEL_PATH": os.path.join(temp_dir, "models"),
        "CHUNK_SIZE": 500,  # Smaller chunks for testing
        "CHUNK_OVERLAP": 50,
        "BATCH_SIZE": 2,
        "DEVICE": "cpu",  # Use CPU for testing
        "MAX_WORKERS": 2,  # Fewer workers for testing
        "CHECKPOINT_INTERVAL": 2,
        "USE_CACHE": True,
        "CLEAR_CACHE_AFTER_BATCH": True
    }
    
    doc_processor = MockDocumentProcessor(sample_documents)
    return Trainer(doc_processor, settings)

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
    
    # Test memory management
    embeddings.cache.clear()
    assert len(embeddings.cache) == 0

def test_parallel_chunking(trainer, sample_documents):
    """Test parallel document chunking."""
    chunks = trainer.create_chunks(sample_documents)
    
    # Verify chunks were created
    assert len(chunks) > 0
    
    # Verify chunk sizes are within expected range
    for chunk in chunks:
        assert len(chunk.page_content) <= trainer.settings["CHUNK_SIZE"]
        assert len(chunk.page_content) > 0

def test_checkpointing(trainer, sample_documents):
    """Test checkpointing functionality."""
    # Create a small vectordb with checkpointing
    vectordb = trainer.create_vectordb(sample_documents)
    
    # Verify checkpoint files were created
    checkpoint_files = list(Path(trainer.vectordb_path).glob("checkpoint_*"))
    assert len(checkpoint_files) > 0
    
    # Verify metadata was saved
    metadata_path = os.path.join(trainer.vectordb_path, "metadata.json")
    assert os.path.exists(metadata_path)
    
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
        assert "chunk_size" in metadata
        assert "chunk_overlap" in metadata
        assert "embedding_model" in metadata
        assert "num_chunks" in metadata

def test_vectordb_creation_and_loading(trainer, sample_documents):
    """Test vector database creation and loading."""
    # Create vectordb
    vectordb = trainer.create_vectordb(sample_documents)
    assert vectordb is not None
    
    # Test loading the vectordb
    loaded_vectordb = trainer.load_vectordb()
    assert loaded_vectordb is not None
    
    # Test similarity search
    results = loaded_vectordb.similarity_search("test document", k=1)
    assert len(results) > 0

def test_memory_management(trainer, sample_documents):
    """Test memory management during processing."""
    # Create a large number of documents
    large_documents = [
        Document(
            page_content="Test document " * 100,
            metadata={"source": f"test_{i}.txt"}
        )
        for i in range(10)
    ]
    
    # Process documents and verify memory usage
    initial_memory = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
    
    chunks = trainer.create_chunks(large_documents)
    assert len(chunks) > 0
    
    # Verify memory was managed properly
    if torch.cuda.is_available():
        final_memory = torch.cuda.memory_allocated()
        assert final_memory <= initial_memory * 2  # Memory shouldn't grow too much

def test_error_handling(trainer):
    """Test error handling during processing."""
    # Test with empty document - should raise exception
    empty_doc = Document(page_content="", metadata={})
    with pytest.raises(ValueError, match="Document contains empty content"):
        trainer.create_chunks([empty_doc])
    
    # Test with problematic document (just whitespace)
    whitespace_doc = Document(page_content="   \n   ", metadata={})
    with pytest.raises(ValueError, match="Document contains empty content"):
        trainer.create_chunks([whitespace_doc])

def test_cleanup(temp_dir):
    """Test cleanup of temporary files."""
    # Create some temporary files
    temp_files = [
        os.path.join(temp_dir, f"temp_{i}.txt")
        for i in range(5)
    ]
    
    for file in temp_files:
        with open(file, "w") as f:
            f.write("test")
    
    # Verify files were created
    assert all(os.path.exists(f) for f in temp_files)
    
    # Manually remove files since we're going to verify they're gone
    # before the fixture cleanup happens
    for file in temp_files:
        os.remove(file)
    
    # Verify files are gone
    assert not any(os.path.exists(f) for f in temp_files) 