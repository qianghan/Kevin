"""
Document processor module for chunking, embedding, and storing documents.
"""

import os
import sys
import yaml
import time
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from src.utils.logger import get_logger, doc_logger

# Configure module logger
logger = get_logger(__name__)

class DocumentProcessor:
    """Process documents for RAG: chunk, embed, and store."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the document processor with configuration."""
        logger.info("Initializing DocumentProcessor")
        
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            logger.debug(f"Configuration loaded from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}", exc_info=True)
            # Set default configuration
            self.config = {
                'vector_db': {
                    'collection_name': 'canadian_universities',
                    'persist_directory': './chroma_db',
                    'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2'
                }
            }
            logger.warning("Using default configuration due to config loading error")
        
        # Vector DB configuration
        self.collection_name = self.config['vector_db'].get('collection_name', 'canadian_universities')
        self.persist_directory = self.config['vector_db'].get('persist_directory', './chroma_db')
        self.embedding_model_name = self.config['vector_db'].get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
        
        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        logger.debug(f"Persistent directory ensured: {self.persist_directory}")
        
        # Initialize embeddings
        logger.info(f"Initializing embedding model: {self.embedding_model_name}")
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize embedding model: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize embedding model: {e}")
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        logger.debug("Text splitter initialized with chunk size 1000 and overlap 200")
        
        # Initialize vector store
        self.vectorstore = None
        logger.info("DocumentProcessor initialized successfully")
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks for better retrieval."""
        logger.info(f"Chunking {len(documents)} documents")
        doc_logger.info(f"Starting document chunking process for {len(documents)} documents")
        
        start_time = time.time()
        chunked_documents = []
        
        for i, doc in enumerate(documents):
            try:
                chunks = self.text_splitter.split_documents([doc])
                chunked_documents.extend(chunks)
                
                # Log progress for larger document sets
                if (i + 1) % 20 == 0 or i == len(documents) - 1:
                    logger.debug(f"Processed {i+1}/{len(documents)} documents")
            except Exception as e:
                source = doc.metadata.get("source", "unknown source")
                logger.error(f"Error chunking document from {source}: {e}")
                # Continue with next document
        
        elapsed_time = time.time() - start_time
        logger.info(f"Split {len(documents)} documents into {len(chunked_documents)} chunks in {elapsed_time:.2f} seconds")
        doc_logger.info(f"Document chunking complete: {len(chunked_documents)} chunks created")
        
        return chunked_documents
    
    def get_or_create_vectorstore(self) -> Chroma:
        """Get existing vector store or create a new one."""
        if self.vectorstore:
            return self.vectorstore
        
        # Check if vector store exists
        if os.path.exists(self.persist_directory) and len(os.listdir(self.persist_directory)) > 0:
            logger.info(f"Loading existing vector store from {self.persist_directory}")
            try:
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory
                )
                
                # Get collection stats if available
                collection_size = 0
                try:
                    collection = self.vectorstore._collection
                    collection_size = collection.count()
                    logger.info(f"Vector store loaded with {collection_size} documents")
                except:
                    logger.debug("Could not retrieve collection size")
                
                doc_logger.info(f"Loaded existing vector store with {collection_size} documents")
            except Exception as e:
                logger.error(f"Error loading vector store: {e}", exc_info=True)
                # Create new vector store as fallback
                logger.warning("Creating new vector store due to loading error")
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory
                )
        else:
            logger.info(f"Creating new vector store at {self.persist_directory}")
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            doc_logger.info(f"Created new vector store at {self.persist_directory}")
        
        return self.vectorstore
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        if not documents:
            logger.warning("No documents provided to add_documents")
            return
            
        logger.info(f"Adding {len(documents)} documents to vector store")
        doc_logger.info(f"Starting document addition process for {len(documents)} documents")
        
        start_time = time.time()
        
        # Chunk documents
        chunked_docs = self.chunk_documents(documents)
        
        if not chunked_docs:
            logger.warning("No chunks were created from the documents")
            doc_logger.warning("Document addition aborted: No chunks created")
            return
        
        # Get vector store
        try:
            vectorstore = self.get_or_create_vectorstore()
            
            # Add documents to vector store
            chunk_add_start = time.time()
            logger.info(f"Adding {len(chunked_docs)} chunks to vector store")
            vectorstore.add_documents(chunked_docs)
            chunk_add_time = time.time() - chunk_add_start
            
            # Persist changes
            persist_start = time.time()
            vectorstore.persist()
            persist_time = time.time() - persist_start
            
            total_time = time.time() - start_time
            
            logger.info(f"Documents added and vector store persisted in {total_time:.2f} seconds")
            logger.debug(f"  - Chunking time: {chunk_add_time - (total_time - chunk_add_time):.2f}s")
            logger.debug(f"  - Adding time: {chunk_add_time:.2f}s")
            logger.debug(f"  - Persist time: {persist_time:.2f}s")
            
            doc_logger.info(f"Document addition complete: {len(chunked_docs)} chunks added in {total_time:.2f}s")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}", exc_info=True)
            doc_logger.error(f"Document addition failed: {str(e)}")
            raise
    
    def search_documents(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Search for documents similar to query."""
        logger.info(f"Searching for documents matching query: '{query}'")
        doc_logger.info(f"Vector search request: k={k}, filter={filter is not None}")
        
        start_time = time.time()
        
        try:
            vectorstore = self.get_or_create_vectorstore()
            
            # Execute search
            if filter:
                logger.debug(f"Searching with filter: {filter}")
                results = vectorstore.similarity_search(query, k=k, filter=filter)
            else:
                results = vectorstore.similarity_search(query, k=k)
            
            elapsed_time = time.time() - start_time
            
            # Log search results and timing
            logger.info(f"Retrieved {len(results)} results in {elapsed_time:.2f}s")
            
            # Log metadata about the results
            for i, doc in enumerate(results):
                source = doc.metadata.get("source", "Unknown")
                logger.debug(f"Result {i+1}: {source}")
            
            doc_logger.info(f"Vector search complete: {len(results)} results in {elapsed_time:.2f}s")
            return results
        except Exception as e:
            logger.error(f"Error searching documents: {e}", exc_info=True)
            doc_logger.error(f"Vector search failed: {str(e)}")
            # Return empty results on error
            return []
    
    def get_retriever(self, search_kwargs: Optional[Dict[str, Any]] = None):
        """Get a retriever for the vector store."""
        logger.info("Creating retriever from vector store")
        
        try:
            vectorstore = self.get_or_create_vectorstore()
            
            if search_kwargs:
                logger.debug(f"Creating retriever with search arguments: {search_kwargs}")
                return vectorstore.as_retriever(search_kwargs=search_kwargs)
            else:
                return vectorstore.as_retriever()
        except Exception as e:
            logger.error(f"Error creating retriever: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    # Example usage
    from scraper import WebScraper
    
    logger.info("Running document processor example")
    
    try:
        # Scrape documents
        logger.info("Initializing web scraper")
        scraper = WebScraper()
        
        logger.info("Scraping university websites")
        documents = scraper.scrape_all_universities()
        logger.info(f"Scraped {len(documents)} documents")
        
        # Process and store documents
        logger.info("Initializing document processor")
        processor = DocumentProcessor()
        
        logger.info("Adding documents to vector store")
        processor.add_documents(documents)
        
        # Example search
        logger.info("Performing example search")
        results = processor.search_documents("scholarship requirements for international students")
        
        logger.info(f"Retrieved {len(results)} results")
        for i, doc in enumerate(results):
            print(f"Result {i+1}:")
            print(f"Source: {doc.metadata.get('source')}")
            print(f"Title: {doc.metadata.get('title')}")
            print(f"Content snippet: {doc.page_content[:200]}...")
            print("-" * 80)
        
        logger.info("Document processor example completed successfully")
    except Exception as e:
        logger.error(f"Error in document processor example: {e}", exc_info=True)
        print(f"Error: {e}") 