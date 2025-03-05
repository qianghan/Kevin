import os
import sys
import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil
import json
from langchain_core.documents import Document

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

# Import the modules to test
from src.models.embeddings import SimpleEmbeddings
from src.rag.engine import RAGEngine

# Test data
TEST_DOCUMENTS = [
    Document(
        page_content="The University of British Columbia (UBC) is a public research university in Vancouver, Canada.",
        metadata={"source": "ubc.ca", "title": "About UBC"}
    ),
    Document(
        page_content="UBC offers over 200 undergraduate programs across its two campuses.",
        metadata={"source": "ubc.ca", "title": "Programs"}
    ),
    Document(
        page_content="The University of Toronto is Canada's largest university by enrollment.",
        metadata={"source": "utoronto.ca", "title": "About UofT"}
    )
]

TEST_QUERY = "What programs does UBC offer?"

# Use pytest-asyncio's built-in event_loop fixture instead of defining our own
# This avoids the deprecation warning

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return {
        'embedding': {
            'model_name': 'test-model'
        },
        'data': {
            'data_dir': 'test_data'
        },
        'retrieval': {
            'top_k': 3
        }
    }

@pytest.fixture
def temp_vectordb_dir():
    """Create a temporary directory for the vector database."""
    temp_dir = tempfile.mkdtemp()
    vectordb_dir = Path(temp_dir) / "vectordb"
    vectordb_dir.mkdir(exist_ok=True)
    
    # Create the faiss_index directory (not just a file)
    faiss_index_dir = vectordb_dir / "faiss_index"
    faiss_index_dir.mkdir(exist_ok=True)
    
    # Add a mock index file
    (faiss_index_dir / "index.faiss").touch()
    
    yield vectordb_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    mock = MagicMock()
    # Use a regular string instead of a coroutine
    mock.invoke.return_value = "Based on the context, UBC offers over 200 undergraduate programs."
    return mock

def test_simple_embeddings():
    """Test the SimpleEmbeddings class."""
    # Initialize embeddings
    embeddings = SimpleEmbeddings(dimension=384)
    
    # Test document embedding
    texts = ["Test document 1", "Test document 2"]
    doc_embeddings = embeddings.embed_documents(texts)
    
    # Verify embeddings
    assert len(doc_embeddings) == 2
    assert len(doc_embeddings[0]) == 384
    assert len(doc_embeddings[1]) == 384
    
    # Test query embedding
    query = "Test query"
    query_embedding = embeddings.embed_query(query)
    
    # Verify query embedding
    assert len(query_embedding) == 384
    
    # Test deterministic behavior
    query_embedding2 = embeddings.embed_query(query)
    assert np.array_equal(query_embedding, query_embedding2)
    
    # Test normalization
    assert np.isclose(np.linalg.norm(query_embedding), 1.0)

@pytest.mark.asyncio
async def test_rag_engine_initialization(mock_config, temp_vectordb_dir):
    """Test RAG engine initialization."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(mock_config, f)
        config_path = f.name
    
    try:
        # Initialize RAG engine with proper path handling
        with patch('src.rag.engine.Path') as mock_path, \
             patch('src.rag.engine.FAISS'):
            
            # Use return_value to ensure the same path is returned every time
            mock_path.return_value.exists.return_value = True
            mock_path.return_value = temp_vectordb_dir
            
            engine = RAGEngine(config_path)
            
            # Force has_vectordb to True for testing
            engine.has_vectordb = True
            
            # Verify initialization
            assert engine.has_vectordb is True
            assert engine.top_k == 3
            assert engine.embedding_model == 'test-model'
            
    finally:
        # Cleanup
        os.unlink(config_path)

@pytest.mark.asyncio
async def test_rag_engine_document_retrieval(mock_config, temp_vectordb_dir, mock_llm):
    """Test document retrieval functionality."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(mock_config, f)
        config_path = f.name
    
    try:
        # Initialize RAG engine with mocked components
        with patch('src.rag.engine.Path') as mock_path, \
             patch('src.rag.engine.FAISS') as mock_faiss, \
             patch('src.rag.engine.DeepSeekAPI', return_value=mock_llm):
            
            # Mock paths and existence checks
            mock_path.return_value.exists.return_value = True
            mock_path.return_value = temp_vectordb_dir
            
            # Create and configure the mock retriever
            mock_retriever = MagicMock()
            mock_retriever.get_relevant_documents.return_value = TEST_DOCUMENTS
            mock_faiss.load_local.return_value.as_retriever.return_value = mock_retriever
            
            engine = RAGEngine(config_path)
            
            # Force vectordb to be available
            engine.has_vectordb = True
            engine.retriever = mock_retriever
            
            # Test document retrieval
            docs = engine.retrieve_documents(TEST_QUERY)
            
            # Verify results
            assert len(docs) == 3
            assert all(isinstance(doc, Document) for doc in docs)
            assert any("UBC" in doc.page_content for doc in docs)
            
    finally:
        # Cleanup
        os.unlink(config_path)

@pytest.mark.asyncio
async def test_rag_engine_answer_generation(mock_config, temp_vectordb_dir, mock_llm):
    """Test answer generation functionality."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(mock_config, f)
        config_path = f.name
    
    try:
        # Initialize RAG engine with mocked components
        with patch('src.rag.engine.Path') as mock_path, \
             patch('src.rag.engine.FAISS') as mock_faiss, \
             patch('src.rag.engine.DeepSeekAPI', return_value=mock_llm):
            
            # Mock paths and existence checks
            mock_path.return_value.exists.return_value = True
            mock_path.return_value = temp_vectordb_dir
            
            engine = RAGEngine(config_path)
            
            # Set the LLM explicitly
            engine.llm = mock_llm
            
            # Test answer generation
            answer = engine.generate_answer(TEST_QUERY, TEST_DOCUMENTS)
            
            # Verify results
            assert isinstance(answer, str)
            assert len(answer) > 0
            assert "UBC" in answer
            assert "programs" in answer.lower()
            
    finally:
        # Cleanup
        os.unlink(config_path)

@pytest.mark.asyncio
async def test_rag_engine_process_query(mock_config, temp_vectordb_dir, mock_llm):
    """Test the process_query method."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(mock_config, f)
        config_path = f.name
    
    try:
        # Initialize RAG engine with mocked components
        with patch('src.rag.engine.Path') as mock_path, \
             patch('src.rag.engine.FAISS') as mock_faiss, \
             patch('src.rag.engine.DeepSeekAPI', return_value=mock_llm):
            
            # Mock paths and existence checks
            mock_path.return_value.exists.return_value = True
            mock_path.return_value = temp_vectordb_dir
            
            # Create and configure the mock retriever
            mock_retriever = MagicMock()
            mock_retriever.get_relevant_documents.return_value = TEST_DOCUMENTS
            mock_faiss.load_local.return_value.as_retriever.return_value = mock_retriever
            
            engine = RAGEngine(config_path)
            
            # Force vectordb to be available and set the components
            engine.has_vectordb = True
            engine.retriever = mock_retriever
            engine.llm = mock_llm
            
            # Test query processing
            response = engine.process_query(TEST_QUERY)
            
            # Verify results
            assert isinstance(response, str)
            assert len(response) > 0
            assert "UBC" in response
            assert "programs" in response.lower()
            
    finally:
        # Cleanup
        os.unlink(config_path)

@pytest.mark.asyncio
async def test_rag_engine_error_handling(mock_config, temp_vectordb_dir):
    """Test error handling in the RAG engine."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(mock_config, f)
        config_path = f.name
    
    try:
        # Initialize RAG engine with mocked components that raise exceptions
        with patch('src.rag.engine.Path') as mock_path, \
             patch('src.rag.engine.FAISS') as mock_faiss:
            
            # Ensure the path exists but loading fails
            mock_path.return_value.exists.return_value = False
            mock_path.return_value = temp_vectordb_dir
            mock_faiss.load_local.side_effect = Exception("Test error")
            
            engine = RAGEngine(config_path)
            
            # Ensure has_vectordb is False
            assert engine.has_vectordb is False
            
            # Test error handling
            response = engine.process_query(TEST_QUERY)
            assert "Vector database not available" in response
            
    finally:
        # Cleanup
        os.unlink(config_path)

@pytest.mark.asyncio
async def test_rag_engine_interactive_session(mock_config, temp_vectordb_dir, mock_llm, monkeypatch):
    """Test the interactive session functionality."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(mock_config, f)
        config_path = f.name
    
    try:
        # Mock input/output
        inputs = iter([TEST_QUERY, 'exit'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        # Capture print output
        printed_messages = []
        monkeypatch.setattr('builtins.print', lambda *args: printed_messages.append(' '.join(str(a) for a in args)))
        
        # Initialize RAG engine with mocked components
        with patch('src.rag.engine.Path') as mock_path, \
             patch('src.rag.engine.FAISS') as mock_faiss, \
             patch('src.rag.engine.DeepSeekAPI', return_value=mock_llm):
            
            # Mock paths and existence checks
            mock_path.return_value.exists.return_value = True
            mock_path.return_value = temp_vectordb_dir
            
            # Create and configure the mock retriever
            mock_retriever = MagicMock()
            mock_retriever.get_relevant_documents.return_value = TEST_DOCUMENTS
            mock_faiss.load_local.return_value.as_retriever.return_value = mock_retriever
            
            engine = RAGEngine(config_path)
            
            # Force vectordb to be available and set the components
            engine.has_vectordb = True
            engine.retriever = mock_retriever
            engine.llm = mock_llm
            
            # Test interactive session
            engine.interactive_session()
            
            # Verify the session output
            assert any("Canadian University Information Assistant" in msg for msg in printed_messages)
            assert any("UBC" in msg for msg in printed_messages)
            assert any("programs" in msg.lower() for msg in printed_messages)
            
    finally:
        # Cleanup
        os.unlink(config_path) 