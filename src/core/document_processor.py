"""
Document processor module for chunking, embedding, and storing documents.
"""

import os
import sys
import yaml
import time
import json
import shutil
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
import chromadb
import logging
import hashlib
import re
from collections import defaultdict
try:
    from tqdm import tqdm
except ImportError:
    # Simple tqdm fallback if it's not installed
    def tqdm(iterable=None, desc=None, total=None, leave=True):
        if iterable is not None:
            # Just return the original iterable if tqdm is not available
            return iterable
        else:
            # Return a range if total is provided (for manual updates)
            return range(total) if total is not None else range(0)

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import project modules
from src.utils.logger import get_logger, doc_logger

# Configure module logger
logger = get_logger(__name__)

class FakeEmbeddings(Embeddings):
    """Fake embeddings that return random vectors for testing purposes."""
    
    def __init__(self, size: int = 384):
        """Initialize with embedding dimension."""
        self.size = size
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate fake embeddings for documents."""
        return [self.embed_query(text) for text in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Generate a fake embedding for a query."""
        # Use hash of text to generate a deterministic but random-looking vector
        np.random.seed(int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % 2**32)
        return list(np.random.uniform(-1, 1, self.size))

class DocumentProcessor:
    """Process documents for RAG: chunk, embed, and store."""
    
    # Add a constant for maximum batch size (slightly under Chroma's limit of 41666)
    MAX_BATCH_SIZE = 10000  # Conservative value to ensure we're well under the limit
    
    def __init__(
        self, 
        config=None,
        chunk_size=None,
        chunk_overlap=None,
        batch_size=None
    ):
        """Initialize the document processor.
        
        Args:
            config: Configuration dictionary
            chunk_size: Size of chunks to split documents into
            chunk_overlap: Overlap between chunks
            batch_size: Number of documents to process in a batch
        """
        # Set up logger
        self.logger = logger
        
        # Load configuration
        self.config = config or {}
        
        # Set default values if not provided
        self.chunk_size = chunk_size or self.config.get('chunking', {}).get('chunk_size', 1000)
        self.chunk_overlap = chunk_overlap or self.config.get('chunking', {}).get('chunk_overlap', 200)
        self.batch_size = batch_size or self.config.get('processing', {}).get('batch_size', 64)
        
        # Vector DB configuration
        self.collection_name = self.config.get('vector_db', {}).get('collection_name', 'documents')
        self.persist_directory = self.config.get('vector_db', {}).get('persist_directory', './chroma_db')
        self.embedding_model = self.config.get('vector_db', {}).get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
        
        # Convert relative path to absolute if needed
        if not os.path.isabs(self.persist_directory):
            self.persist_directory = os.path.abspath(os.path.join(os.getcwd(), self.persist_directory))
            
        self.logger.info(f"Document processor initialized with persist_directory={self.persist_directory}")
        
        # Initialize embeddings
        self.embeddings = self._initialize_embeddings()
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.logger.debug("Text splitter initialized with chunk size 1000 and overlap 200")
        
        # Initialize vector store
        self.vectorstore = None
        self.logger.info("DocumentProcessor initialized successfully")
    
    def _initialize_embeddings(self) -> Embeddings:
        """Initialize embedding model with fallbacks."""
        # List of models to try in order
        fallback_models = [
            self.embedding_model,
            "all-MiniLM-L6-v2",
            "paraphrase-MiniLM-L3-v2",
            "all-mpnet-base-v2"
        ]
        
        # Try each model in sequence
        for model_name in fallback_models:
            try:
                self.logger.info(f"Initializing embedding model: {model_name}")
                return HuggingFaceEmbeddings(model_name=model_name)
            except Exception as e:
                self.logger.warning(f"Failed to initialize embedding model {model_name}: {e}")
                if model_name != fallback_models[-1]:
                    self.logger.warning(f"Trying fallback embedding model: {fallback_models[fallback_models.index(model_name) + 1]}")
        
        # If all models fail, use fake embeddings as a last resort
        self.logger.warning("Using FakeEmbeddings as a last resort fallback")
        return FakeEmbeddings()
    
    def chunk_documents(self, documents: List[Document]) -> Tuple[List[Document], Dict[str, int]]:
        """Split documents into smaller chunks for better retrieval.
        
        Returns:
            Tuple of (chunked_documents, stats_dict)
        """
        self.logger.info(f"Chunking {len(documents)} documents")
        doc_logger.info(f"Starting document chunking process for {len(documents)} documents")
        
        start_time = time.time()
        chunked_documents = []
        
        # Stats tracking
        stats = {
            "total_documents": len(documents),
            "successfully_chunked": 0,
            "failed_chunking": 0,
            "total_chunks_created": 0,
            "empty_documents": 0,
            "avg_chunks_per_document": 0,
            "largest_document_chunks": 0,
            "smallest_document_chunks": float('inf')
        }
        
        # Track document sources for reporting
        source_stats = defaultdict(int)
        
        # Create progress bar for chunking
        with tqdm(total=len(documents), desc="Chunking documents", leave=True) as pbar:
            for i, doc in enumerate(documents):
                try:
                    # Skip empty documents
                    if not doc.page_content or len(doc.page_content.strip()) == 0:
                        self.logger.warning(f"Skipping empty document {i+1}")
                        stats["empty_documents"] += 1
                        pbar.update(1)
                        continue
                    
                    # Get document source for tracking
                    source = doc.metadata.get("source", "unknown")
                    if isinstance(source, str) and len(source) > 0:
                        # Extract domain for grouping
                        domain = source
                        if source.startswith(('http://', 'https://')):
                            try:
                                from urllib.parse import urlparse
                                parsed_url = urlparse(source)
                                domain = parsed_url.netloc
                            except:
                                pass
                        source_stats[domain] += 1
                    
                    # Chunk the document
                    chunks = self.text_splitter.split_documents([doc])
                    
                    # Track statistics
                    chunk_count = len(chunks)
                    stats["total_chunks_created"] += chunk_count
                    
                    # Track min/max chunks per document
                    if chunk_count > 0:
                        stats["largest_document_chunks"] = max(stats["largest_document_chunks"], chunk_count)
                        stats["smallest_document_chunks"] = min(stats["smallest_document_chunks"], chunk_count)
                    
                    # Add chunks to our collection
                    chunked_documents.extend(chunks)
                    
                    # Update stats
                    stats["successfully_chunked"] += 1
                    
                    # Update progress bar with additional info
                    pbar.set_postfix({"Chunks": stats["total_chunks_created"], "Success": stats["successfully_chunked"]})
                    pbar.update(1)
                    
                    # Log progress for larger document sets (less frequently due to progress bar)
                    if (i + 1) % 50 == 0 or i == len(documents) - 1:
                        self.logger.debug(f"Processed {i+1}/{len(documents)} documents")
                except Exception as e:
                    source = doc.metadata.get("source", "unknown source")
                    self.logger.error(f"Error chunking document from {source}: {e}")
                    # Update stats
                    stats["failed_chunking"] += 1
                    # Update progress bar
                    pbar.update(1)
                    # Continue with next document
        
        # Calculate average chunks per document
        if stats["successfully_chunked"] > 0:
            stats["avg_chunks_per_document"] = stats["total_chunks_created"] / stats["successfully_chunked"]
        
        # If smallest_document_chunks is still infinity, set it to 0
        if stats["smallest_document_chunks"] == float('inf'):
            stats["smallest_document_chunks"] = 0
        
        # Add source statistics
        stats["sources"] = dict(source_stats)
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Split {stats['successfully_chunked']}/{stats['total_documents']} documents into {stats['total_chunks_created']} chunks in {elapsed_time:.2f} seconds")
        doc_logger.info(f"Document chunking complete: {stats['total_chunks_created']} chunks created, {stats['failed_chunking']} documents failed")
        
        # Print chunking summary
        print(f"\n--- Document Chunking Summary ---")
        print(f"Total documents processed: {stats['total_documents']}")
        print(f"Successfully chunked: {stats['successfully_chunked']} ({stats['successfully_chunked']/stats['total_documents']*100:.1f}%)")
        print(f"Failed to chunk: {stats['failed_chunking']} ({stats['failed_chunking']/stats['total_documents']*100:.1f}%)")
        print(f"Empty documents skipped: {stats['empty_documents']}")
        print(f"Total chunks created: {stats['total_chunks_created']}")
        
        if stats["successfully_chunked"] > 0:
            print(f"Average chunks per document: {stats['avg_chunks_per_document']:.1f}")
            print(f"Largest document: {stats['largest_document_chunks']} chunks")
            print(f"Smallest document: {stats['smallest_document_chunks']} chunks")
        
        # Print top sources if available
        if source_stats:
            print(f"\nTop sources:")
            sorted_sources = sorted(source_stats.items(), key=lambda x: x[1], reverse=True)
            for source, count in sorted_sources[:5]:  # Show top 5 sources
                print(f"  - {source}: {count} documents")
        
        print(f"Time taken: {elapsed_time:.2f} seconds")
        print(f"-------------------------------")
        
        return chunked_documents, stats
    
    def _cleanup_chroma_directory(self):
        """Clean up the Chroma directory to ensure it's in a usable state"""
        import os
        import shutil
        
        # Track if we found any problems that need fixing
        found_problems = False
        
        try:
            # Check the directory exists
            if os.path.exists(self.persist_directory):
                self.logger.info(f"Checking Chroma directory: {self.persist_directory}")
                
                # Walk through directory looking for hidden files
                for root, dirs, files in os.walk(self.persist_directory):
                    # Check for hidden files that could cause issues (like .DS_Store)
                    for file in files:
                        if file.startswith('._') or file == '.DS_Store':
                            file_path = os.path.join(root, file)
                            self.logger.warning(f"Found problematic hidden file: {file_path}")
                            try:
                                os.remove(file_path)
                                self.logger.info(f"Removed problematic file: {file_path}")
                                found_problems = True
                            except Exception as e:
                                self.logger.error(f"Failed to remove hidden file {file_path}: {e}")
                    
                    # Check for database files and update permissions
                    for file in files:
                        if file.endswith('.sqlite3') or file.endswith('.bin') or file.endswith('.pickle'):
                            file_path = os.path.join(root, file)
                            try:
                                # Make sure files are writable
                                current_mode = os.stat(file_path).st_mode
                                if not (current_mode & 0o200):  # Check for write permission
                                    os.chmod(file_path, current_mode | 0o200)  # Add write permission
                                    self.logger.info(f"Fixed permissions for: {file_path}")
                                    found_problems = True
                            except Exception as e:
                                self.logger.error(f"Failed to update permissions for {file_path}: {e}")
                                found_problems = True  # Consider this a problem too
                
                # If we found problematic files or permissions, better to rebuild the directory
                if found_problems:
                    self.logger.warning(f"Found problems with Chroma directory. Rebuilding it.")
                    shutil.rmtree(self.persist_directory, ignore_errors=True)
                    os.makedirs(self.persist_directory, exist_ok=True)
                    # Ensure the directory has the right permissions
                    os.chmod(self.persist_directory, 0o755)  # rwxr-xr-x
                else:
                    self.logger.info(f"Chroma directory looks good.")
            else:
                # Create the directory if it doesn't exist
                self.logger.info(f"Creating Chroma directory: {self.persist_directory}")
                os.makedirs(self.persist_directory, exist_ok=True)
                # Ensure the directory has the right permissions
                os.chmod(self.persist_directory, 0o755)  # rwxr-xr-x
            
            return True
        except Exception as e:
            self.logger.error(f"Error cleaning up Chroma directory: {str(e)}")
            # If there was an error, try to recreate the directory
            try:
                if os.path.exists(self.persist_directory):
                    shutil.rmtree(self.persist_directory, ignore_errors=True)
                os.makedirs(self.persist_directory, exist_ok=True)
                os.chmod(self.persist_directory, 0o755)  # rwxr-xr-x
                self.logger.info(f"Recreated Chroma directory after error")
                return True
            except Exception as e2:
                self.logger.error(f"Failed to recreate Chroma directory: {str(e2)}")
                return False
            
    def get_or_create_vectorstore(self):
        """Get or create a vector store for document storage and retrieval"""
        from langchain_chroma import Chroma
        import chromadb
        
        # Always clean up the directory first for a fresh start
        self._cleanup_chroma_directory()
        
        try:
            # Create client settings
            client_settings = chromadb.Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            )
            
            # Create a new client
            client = chromadb.Client(client_settings)
            
            # Ensure the default tenant exists
            try:
                client.get_or_create_tenant("default_tenant")
                client.get_or_create_database("default_database", tenant="default_tenant")
            except Exception as tenant_error:
                self.logger.warning(f"Error creating tenant/database: {str(tenant_error)}")
            
            # Create the vector store
            vectorstore = Chroma(
                collection_name="documents",
                embedding_function=self._get_embedding_function(),
                persist_directory=self.persist_directory,
                client=client
            )
            
            self.logger.info(f"Successfully created/loaded vector store at {self.persist_directory}")
            return vectorstore
            
        except Exception as e:
            self.logger.error(f"Error loading vector store: {str(e)}")
            
            # Create a completely fresh vector store with minimal settings
            try:
                self.logger.warning("Creating new vector store due to loading error")
                
                # Try with a completely fresh approach
                client_settings = chromadb.Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.persist_directory,
                    anonymized_telemetry=False
                )
                
                client = chromadb.Client(client_settings)
                
                # Ensure tenant exists
                client.get_or_create_tenant("default_tenant")
                client.get_or_create_database("default_database", tenant="default_tenant")
                
                vectorstore = Chroma(
                    collection_name="documents",
                    embedding_function=self._get_embedding_function(),
                    persist_directory=self.persist_directory,
                    client=client
                )
                
                return vectorstore
            except Exception as fallback_error:
                self.logger.error(f"Fallback vector store creation also failed: {str(fallback_error)}")
                raise
    
    def add_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """Add documents to the vector store.
        
        Returns:
            Dictionary with processing statistics
        """
        # Initialize stats dictionary
        stats = {
            "total_documents": len(documents) if documents else 0,
            "chunking": {},
            "vector_db": {
                "docs_added": 0,
                "batches_processed": 0,
                "batches_failed": 0,
                "fallback_used": False
            },
            "timing": {
                "start_time": time.time(),
                "chunking_time": 0,
                "filtering_time": 0,
                "db_add_time": 0,
                "total_time": 0
            }
        }
        
        if not documents:
            self.logger.warning("No documents provided to add_documents")
            stats["error"] = "No documents provided"
            return stats
            
        self.logger.info(f"Adding {len(documents)} documents to vector store")
        doc_logger.info(f"Starting document addition process for {len(documents)} documents")
        
        print(f"\n=== Starting Document Processing ===")
        print(f"Total documents to process: {len(documents)}")
        
        # Chunk documents
        chunking_start_time = time.time()
        chunked_docs, chunking_stats = self.chunk_documents(documents)
        stats["chunking"] = chunking_stats
        stats["timing"]["chunking_time"] = time.time() - chunking_start_time
        
        if not chunked_docs:
            self.logger.warning("No chunks were created from the documents")
            doc_logger.warning("Document addition aborted: No chunks created")
            stats["error"] = "No chunks created from documents"
            stats["timing"]["total_time"] = time.time() - stats["timing"]["start_time"]
            return stats
        
        # Filter complex metadata
        filtering_start_time = time.time()
        filtered_docs_count = 0
        filtering_success = False
        
        try:
            self.logger.info("Filtering complex metadata from documents")
            print(f"Filtering metadata for {len(chunked_docs)} chunks...")
            
            filtered_docs = []
            metadata_errors = 0
            
            # Use progress bar
            with tqdm(total=len(chunked_docs), desc="Filtering metadata", leave=True) as pbar:
                for doc in chunked_docs:
                    try:
                        if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                            # Filter metadata to only include primitive types
                            filtered_metadata = {}
                            for key, value in doc.metadata.items():
                                if isinstance(value, (str, bool, int, float)):
                                    filtered_metadata[key] = value
                                else:
                                    # Convert complex types to strings
                                    try:
                                        filtered_metadata[key] = str(value)
                                    except Exception as e:
                                        # If conversion fails, remove the key
                                        self.logger.warning(f"Could not convert metadata value for key {key}: {e}")
                                        metadata_errors += 1
                            
                            # Create a new document with filtered metadata
                            filtered_doc = Document(page_content=doc.page_content, metadata=filtered_metadata)
                            filtered_docs.append(filtered_doc)
                        else:
                            # If no metadata or not a dict, just add the original document
                            filtered_docs.append(doc)
                            
                        filtered_docs_count += 1
                    except Exception as filter_error:
                        metadata_errors += 1
                        self.logger.warning(f"Error filtering document metadata: {filter_error}")
                    
                    pbar.update(1)
                    
            chunked_docs = filtered_docs
            filtering_success = True
            self.logger.info(f"Filtered metadata for {filtered_docs_count} documents, with {metadata_errors} errors")
            
            # Track in stats
            stats["filtering"] = {
                "total_chunks": len(filtered_docs) + metadata_errors,
                "successful": filtered_docs_count,
                "failed": metadata_errors
            }
            
        except Exception as e:
            self.logger.warning(f"Error filtering metadata: {e}. Will try to proceed anyway.")
            stats["filtering"] = {
                "error": str(e),
                "total_chunks": len(chunked_docs),
                "successful": 0,
                "failed": len(chunked_docs)
            }
            
            # Fallback: create new documents with minimal metadata
            try:
                self.logger.info("Attempting fallback metadata filtering")
                print("Using fallback metadata filtering method...")
                minimal_docs = []
                
                # Use progress bar for fallback filtering
                with tqdm(total=len(chunked_docs), desc="Fallback filtering", leave=True) as pbar:
                    for doc in chunked_docs:
                        try:
                            # Create minimal metadata with just the source and title if available
                            minimal_metadata = {}
                            if hasattr(doc, 'metadata'):
                                if isinstance(doc.metadata.get('source'), str):
                                    minimal_metadata['source'] = doc.metadata['source']
                                if isinstance(doc.metadata.get('title'), str):
                                    minimal_metadata['title'] = doc.metadata['title']
                            
                            # Create a new document with minimal metadata
                            minimal_doc = Document(page_content=doc.page_content, metadata=minimal_metadata)
                            minimal_docs.append(minimal_doc)
                            filtered_docs_count += 1
                        except Exception as fallback_filter_error:
                            self.logger.warning(f"Error in fallback filtering: {fallback_filter_error}")
                            metadata_errors += 1
                        pbar.update(1)
                
                chunked_docs = minimal_docs
                filtering_success = True
                self.logger.info(f"Created {len(minimal_docs)} documents with minimal metadata")
                
                # Update stats with fallback information
                stats["filtering"] = {
                    "total_chunks": len(chunked_docs) + metadata_errors,
                    "successful": filtered_docs_count,
                    "failed": metadata_errors,
                    "used_fallback": True
                }
                
            except Exception as e2:
                self.logger.error(f"Fallback metadata filtering also failed: {e2}")
                stats["filtering"] = {
                    "error": f"Primary filtering: {str(e)}; Fallback filtering: {str(e2)}",
                    "total_chunks": len(chunked_docs),
                    "successful": 0,
                    "failed": len(chunked_docs),
                    "used_fallback": True
                }
        
        stats["timing"]["filtering_time"] = time.time() - filtering_start_time
        
        if not filtering_success or len(chunked_docs) == 0:
            print("⚠️ Metadata filtering failed or no documents remained after filtering")
            stats["error"] = "Metadata filtering failed or no documents remained"
            stats["timing"]["total_time"] = time.time() - stats["timing"]["start_time"]
            return stats
        
        # Print filtering summary
        print(f"\n--- Metadata Filtering Summary ---")
        print(f"Total chunks processed: {stats['filtering'].get('total_chunks', len(chunked_docs))}")
        print(f"Successfully filtered: {stats['filtering'].get('successful', filtered_docs_count)}")
        print(f"Failed to filter: {stats['filtering'].get('failed', metadata_errors)}")
        if stats['filtering'].get('used_fallback', False):
            print("⚠️ Used fallback filtering method")
        print(f"Time taken: {stats['timing']['filtering_time']:.2f} seconds")
        print(f"-----------------------------")
        
        # Get vector store
        fallback_used = False
        stats["vector_db"]["fallback_used"] = False
        db_add_start_time = time.time()
        
        try:
            vectorstore = self.get_or_create_vectorstore()
            
            # Split documents into smaller batches to avoid exceeding Chroma's batch size limit
            total_docs = len(chunked_docs)
            total_batches = (total_docs + self.MAX_BATCH_SIZE - 1) // self.MAX_BATCH_SIZE  # Ceiling division
            
            self.logger.info(f"Processing {total_docs} chunks in {total_batches} batches of max {self.MAX_BATCH_SIZE} documents each")
            print(f"\nAdding documents to vector database...")
            print(f"Total chunks to add: {total_docs}")
            print(f"Number of batches: {total_batches}")
            
            docs_added = 0
            batch_successes = 0
            batch_failures = 0
            
            # Process in batches with progress bar
            with tqdm(total=total_batches, desc="Processing batches", leave=True) as pbar:
                for batch_idx in range(total_batches):
                    start_idx = batch_idx * self.MAX_BATCH_SIZE
                    end_idx = min(start_idx + self.MAX_BATCH_SIZE, total_docs)
                    batch_docs = chunked_docs[start_idx:end_idx]
                    batch_size = len(batch_docs)
                    
                    try:
                        self.logger.info(f"Adding batch {batch_idx+1}/{total_batches} with {batch_size} documents (docs {start_idx+1}-{end_idx} of {total_docs})")
                        
                        # Add the batch to vector store
                        vectorstore.add_documents(batch_docs)
                        docs_added += batch_size
                        batch_successes += 1
                        
                        self.logger.info(f"Completed batch {batch_idx+1}/{total_batches} - {docs_added}/{total_docs} documents processed")
                    except Exception as batch_error:
                        self.logger.error(f"Error processing batch {batch_idx+1}: {batch_error}")
                        batch_failures += 1
                        
                    pbar.update(1)
                    pbar.set_postfix({"Added": docs_added, "Failed Batches": batch_failures})
            
            # Calculate timing
            stats["timing"]["db_add_time"] = time.time() - db_add_start_time
            stats["timing"]["total_time"] = time.time() - stats["timing"]["start_time"]
            
            # Update stats
            stats["vector_db"]["docs_added"] = docs_added
            stats["vector_db"]["batches_processed"] = batch_successes
            stats["vector_db"]["batches_failed"] = batch_failures
            
            self.logger.info(f"All documents added to vector store in {stats['timing']['total_time']:.2f} seconds")
            self.logger.debug(f"  - Chunking time: {stats['timing']['chunking_time']:.2f}s")
            self.logger.debug(f"  - Filtering time: {stats['timing']['filtering_time']:.2f}s")
            self.logger.debug(f"  - Adding time: {stats['timing']['db_add_time']:.2f}s")
            
            doc_logger.info(f"Successfully added {docs_added} chunks to vector store")
            
            # Store success status
            stats["success"] = batch_failures == 0
            
        except Exception as e:
            self.logger.error(f"Error adding documents to vector store: {e}", exc_info=True)
            doc_logger.error(f"Document addition failed: {str(e)}")
            
            # Update stats
            stats["vector_db"]["error"] = str(e)
            stats["success"] = False
            
            # Try with fallback to temporary storage
            if not fallback_used:
                fallback_used = True
                stats["vector_db"]["fallback_used"] = True
                self.logger.warning("Attempting to add documents with fallback storage")
                print("\n⚠️ Primary vector store failed. Attempting to use fallback storage...")
                
                try:
                    # Use in-memory vector store as fallback
                    import tempfile
                    fallback_dir = os.path.join(tempfile.gettempdir(), f'kevin_chroma_fallback_{int(time.time())}')
                    self.logger.info(f"Using fallback directory: {fallback_dir}")
                    print(f"Fallback directory: {fallback_dir}")
                    
                    # Ensure it exists
                    os.makedirs(fallback_dir, exist_ok=True)
                    
                    # Create fallback vector store
                    fallback_vs = Chroma(
                        collection_name=self.collection_name,
                        embedding_function=self.embeddings,
                        persist_directory=fallback_dir
                    )
                    
                    # Process in batches with the fallback vector store too
                    total_docs = len(chunked_docs)
                    total_batches = (total_docs + self.MAX_BATCH_SIZE - 1) // self.MAX_BATCH_SIZE
                    
                    self.logger.info(f"Processing {total_docs} chunks in {total_batches} batches using fallback storage")
                    
                    docs_added = 0
                    batch_successes = 0
                    batch_failures = 0
                    
                    # Process in batches with progress bar
                    with tqdm(total=total_batches, desc="Fallback processing", leave=True) as pbar:
                        for batch_idx in range(total_batches):
                            start_idx = batch_idx * self.MAX_BATCH_SIZE
                            end_idx = min(start_idx + self.MAX_BATCH_SIZE, total_docs)
                            batch_docs = chunked_docs[start_idx:end_idx]
                            batch_size = len(batch_docs)
                            
                            try:
                                self.logger.info(f"Adding batch {batch_idx+1}/{total_batches} with {batch_size} documents to fallback store")
                                fallback_vs.add_documents(batch_docs)
                                docs_added += batch_size
                                batch_successes += 1
                            except Exception as fallback_batch_error:
                                self.logger.error(f"Error processing fallback batch {batch_idx+1}: {fallback_batch_error}")
                                batch_failures += 1
                                
                            pbar.update(1)
                            pbar.set_postfix({"Added": docs_added, "Failed Batches": batch_failures})
                    
                    self.logger.info(f"Successfully added {docs_added} documents to fallback vector store at {fallback_dir}")
                    
                    # Update our reference
                    self.vectorstore = fallback_vs
                    self.persist_directory = fallback_dir
                    
                    # Update stats with fallback success
                    stats["vector_db"]["fallback_docs_added"] = docs_added
                    stats["vector_db"]["fallback_batches_processed"] = batch_successes
                    stats["vector_db"]["fallback_batches_failed"] = batch_failures
                    stats["vector_db"]["fallback_directory"] = fallback_dir
                    stats["success"] = batch_failures == 0
                    
                    doc_logger.info(f"Documents added to fallback vector store at {fallback_dir}")
                except Exception as fallback_error:
                    self.logger.error(f"Fallback storage also failed: {fallback_error}", exc_info=True)
                    doc_logger.error(f"Both primary and fallback document addition failed")
                    
                    # Update stats with fallback failure
                    stats["vector_db"]["fallback_error"] = str(fallback_error)
                    stats["success"] = False
                    
                    # Re-raise the original exception
                    raise e
            else:
                # We already tried the fallback, so just raise the exception
                raise
        
        finally:
            # Always print a summary, even if there were errors
            stats["timing"]["total_time"] = time.time() - stats["timing"]["start_time"]
            
            print(f"\n=== Document Processing Summary ===")
            print(f"Total documents processed: {stats['total_documents']}")
            print(f"Documents successfully chunked: {stats['chunking'].get('successfully_chunked', 0)}")
            print(f"Total chunks created: {stats['chunking'].get('total_chunks_created', 0)}")
            print(f"Chunks successfully added to database: {stats['vector_db'].get('docs_added', 0)}")
            
            if stats["vector_db"].get("batches_failed", 0) > 0:
                print(f"⚠️ {stats['vector_db']['batches_failed']} batch(es) failed to add to database")
            
            if stats["vector_db"].get("fallback_used", False):
                print(f"⚠️ Used fallback vector storage")
                print(f"Chunks added to fallback storage: {stats['vector_db'].get('fallback_docs_added', 0)}")
            
            print(f"\nTiming:")
            print(f"  - Chunking: {stats['timing']['chunking_time']:.2f}s")
            print(f"  - Metadata filtering: {stats['timing']['filtering_time']:.2f}s")
            print(f"  - Database addition: {stats['timing']['db_add_time']:.2f}s")
            print(f"  - Total time: {stats['timing']['total_time']:.2f}s")
            
            if stats.get("success", False):
                print(f"\n✅ Document processing completed successfully")
            else:
                print(f"\n❌ Document processing completed with errors")
                if "error" in stats:
                    print(f"Error: {stats['error']}")
                elif "vector_db" in stats and "error" in stats["vector_db"]:
                    print(f"Vector DB Error: {stats['vector_db']['error']}")
            
            print(f"=====================================")
            
        return stats
    
    def search_documents(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Search for documents similar to query."""
        self.logger.info(f"Searching for documents matching query: '{query}'")
        doc_logger.info(f"Vector search request: k={k}, filter={filter is not None}")
        
        start_time = time.time()
        
        try:
            vectorstore = self.get_or_create_vectorstore()
            
            # Execute search
            if filter:
                self.logger.debug(f"Searching with filter: {filter}")
                results = vectorstore.similarity_search(query, k=k, filter=filter)
            else:
                results = vectorstore.similarity_search(query, k=k)
            
            elapsed_time = time.time() - start_time
            
            # Log search results and timing
            self.logger.info(f"Retrieved {len(results)} results in {elapsed_time:.2f}s")
            
            # Log metadata about the results
            for i, doc in enumerate(results):
                source = doc.metadata.get("source", "Unknown")
                self.logger.debug(f"Result {i+1}: {source}")
            
            doc_logger.info(f"Vector search complete: {len(results)} results in {elapsed_time:.2f}s")
            return results
        except Exception as e:
            self.logger.error(f"Error searching documents: {e}", exc_info=True)
            doc_logger.error(f"Vector search failed: {str(e)}")
            # Return empty results on error
            return []
    
    def get_retriever(self):
        """Get a retriever for the vector store."""
        try:
            # Get or create vector store
            vectorstore = self.get_or_create_vectorstore()
            
            # Create retriever
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}  # Return top 3 most similar documents
            )
            
            self.logger.info("Created retriever from vector store")
            return retriever
        except Exception as e:
            self.logger.error(f"Error creating retriever: {e}")
            raise

    def _get_embedding_function(self) -> Embeddings:
        """Get an embedding function for document embedding.
        
        Returns:
            An embedding function compatible with LangChain
        """
        # For now, just use fake embeddings to avoid external dependencies
        self.logger.info("Using FakeEmbeddings for document processing")
        return FakeEmbeddings(size=384)

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
        stats = processor.add_documents(documents)
        
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