#!/usr/bin/env python3
"""
RAG Engine module for retrieving information and answering questions.
"""

import os
import sys
import yaml
import json
import logging
import glob
import tempfile
import shutil
import time
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import sqlite3
import numpy as np
import hashlib

# Update imports - Remove ChromaDB and add FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import FAISS
# Use HuggingFaceEmbeddings from langchain_huggingface
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# Import related modules with correct paths
from utils.logger import get_logger
from models.deepseek_client import DeepSeekAPI
from core.document_processor import DocumentProcessor

# Local imports
from models.embeddings import SimpleEmbeddings
from langchain_core.retrievers import BaseRetriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.prompts import PromptTemplate
from langchain_community.llms import LlamaCpp, OpenAI

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Retrieval-Augmented Generation Engine for answering university-related questions.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the RAG engine with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        self.logger = get_logger("rag_engine")
        self.config_path = config_path
        self.has_vectordb = False
        self.vectordb = None
        self.retriever = None
        
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.config = {}
        
        # Get embedding model config
        self.embedding_config = self.config.get('embedding', {})
        self.embedding_model = self.embedding_config.get('model_name', 'all-MiniLM-L6-v2')
        
        # Initialize paths
        self.data_dir = Path(self.config.get('data', {}).get('data_dir', 'data'))
        self.vectordb_dir = self.data_dir / "vectordb"
        
        # Set top K parameter for retriever
        self.top_k = self.config.get('retrieval', {}).get('top_k', 5)
        
        # Check if vector database exists by looking for the index.faiss file
        index_file_path = self.vectordb_dir / "index.faiss"
        if not index_file_path.exists():
            self.logger.warning(f"Vector database not found at {self.vectordb_dir}")
            self.logger.warning("Please run the 'train' mode first to create the vector database")
            self.has_vectordb = False
        else:
            self.has_vectordb = True
            self.logger.info(f"Found vector database at {self.vectordb_dir}")
            
            # Initialize vector database
            try:
                self._initialize_vectordb()
            except Exception as e:
                self.logger.error(f"Failed to initialize vector database: {e}")
                self.has_vectordb = False
                self.vectordb = None
                self.retriever = None
            
        # Initialize LLM
        try:
            self._initialize_llm()
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            raise RuntimeError(f"Failed to initialize the LLM component: {e}")
        
        self.logger.info(f"RAG Engine initialized with config from {config_path}")
        
        # Initialize document cache
        self._doc_cache = {}

    def _initialize_vectordb(self) -> None:
        """Initialize the vector database."""
        logger.info(f"Initializing vector database from {self.vectordb_dir}")
        
        try:
            # Load metadata to determine which embedding model was used during training
            metadata_path = self.vectordb_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                embedding_model = metadata.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
                logger.info(f"Using embedding model from metadata: {embedding_model}")
                
                # Create embeddings instance matching the one used in training
                use_simple_embeddings = True  # Default to simple embeddings
                
                try:
                    # First check if transformers has encoding issues
                    try:
                        import transformers
                        use_simple_embeddings = False
                    except UnicodeDecodeError:
                        logger.warning("Detected UTF-8 encoding issues with transformers library. Using SimpleEmbeddings instead.")
                        use_simple_embeddings = True
                    
                    if not use_simple_embeddings:
                        # Add caching to embedding function
                        class CachedHuggingFaceEmbeddings(HuggingFaceEmbeddings):
                            """HuggingFaceEmbeddings with caching to improve performance"""
                            def __init__(self, *args, **kwargs):
                                super().__init__(*args, **kwargs)
                                self._cache = {}
                                
                            def embed_documents(self, texts):
                                """Embed documents with caching"""
                                results = []
                                texts_to_embed = []
                                indices = []
                                
                                # Check cache for each text
                                for i, text in enumerate(texts):
                                    text_hash = hashlib.md5(text.encode()).hexdigest()
                                    if text_hash in self._cache:
                                        results.append(self._cache[text_hash])
                                    else:
                                        texts_to_embed.append(text)
                                        indices.append(i)
                                
                                # If any texts need embedding, compute them
                                if texts_to_embed:
                                    new_embeddings = super().embed_documents(texts_to_embed)
                                    
                                    # Update cache with new embeddings
                                    for j, embedding in enumerate(new_embeddings):
                                        text = texts_to_embed[j]
                                        text_hash = hashlib.md5(text.encode()).hexdigest()
                                        self._cache[text_hash] = embedding
                                        
                                    # Insert new embeddings at the correct positions
                                    for j, idx in enumerate(indices):
                                        if idx >= len(results):
                                            results.append(new_embeddings[j])
                                        else:
                                            results.insert(idx, new_embeddings[j])
                                
                                return results
                        
                        # Use cached embeddings for better performance
                        embedding_function = CachedHuggingFaceEmbeddings(model_name=embedding_model)
                        logger.info(f"Successfully loaded HuggingFace embedding model with caching: {embedding_model}")
                    else:
                        # Use simple embeddings if transformers has issues
                        from models.embeddings import SimpleEmbeddings
                        embedding_function = SimpleEmbeddings()
                        logger.info("Using SimpleEmbeddings due to transformers library encoding issues")
                except Exception as e:
                    logger.warning(f"Could not load HuggingFace embeddings: {e}. Falling back to SimpleEmbeddings.")
                    from models.embeddings import SimpleEmbeddings
                    embedding_function = SimpleEmbeddings()
            else:
                logger.warning("No metadata.json found. Using SimpleEmbeddings as fallback.")
                from models.embeddings import SimpleEmbeddings
                embedding_function = SimpleEmbeddings()
            
            # Load the FAISS index
            self.vectordb = FAISS.load_local(
                self.vectordb_dir, 
                embedding_function,
                allow_dangerous_deserialization=True  # We trust our own saved files
            )
            
            # Get retrieval parameters from config
            top_k = self.config.get('retrieval', {}).get('top_k', self.top_k)
            fetch_k = self.config.get('retrieval', {}).get('fetch_k', top_k * 2)
            score_threshold = self.config.get('retrieval', {}).get('score_threshold', 0.15)
            
            # Get vector DB specific parameters
            search_type = self.config.get('vector_db', {}).get('search_type', "similarity")
            similarity_top_k = self.config.get('vector_db', {}).get('similarity_top_k', top_k)
            
            # Create a retriever with improved search parameters
            self.retriever = self.vectordb.as_retriever(
                search_type=search_type,
                search_kwargs={
                    "k": similarity_top_k,
                    "score_threshold": score_threshold,
                    "fetch_k": fetch_k,
                }
            )
            
            logger.info(f"Vector database initialized successfully with retriever (k={top_k}, search_type={search_type})")
            
            # Skip verification to save time - only do minimal check
            # Safe check that doesn't rely on internal attributes like _index
            try:
                # Simple check to see if the vectordb works - query with an empty string
                self.vectordb.similarity_search("test", k=1)
                logger.info("Vector database verification passed")
            except Exception as e:
                logger.warning(f"Vector database may not be properly initialized: {e}")
                
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            self.has_vectordb = False
            raise
    
    def _initialize_llm(self):
        """Initialize the language model for generation."""
        self.logger.info("Initializing language model...")
        
        # Initialize DeepSeek API
        self.llm = DeepSeekAPI()
        
    def retrieve_documents(self, query: str, k: int = 5) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The query to search for
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        self.logger.info(f"Retrieving documents for query: {query}")
        
        if not self.has_vectordb:
            self.logger.error("Vector database not available")
            return []
        
        try:
            # Check if we have a cache and if this query is cached
            cache_key = f"query_cache_{hashlib.md5(query.encode()).hexdigest()}"
            
            # Try to get from cache first
            if hasattr(self, '_doc_cache') and cache_key in self._doc_cache:
                self.logger.info("Using cached document results")
                return self._doc_cache[cache_key]
            
            # Initialize cache if not exists
            if not hasattr(self, '_doc_cache'):
                self._doc_cache = {}
            
            # Get retrieval parameters from config
            top_k = self.config.get('retrieval', {}).get('top_k', k)
            score_threshold = self.config.get('retrieval', {}).get('score_threshold', 0.25)
            
            # Check if vectordb is available
            if not hasattr(self, 'vectordb') or self.vectordb is None:
                self.logger.error("Vector database not properly initialized")
                return []
                
            # Use direct vector similarity search with optimized parameters
            docs = self.vectordb.similarity_search(
                query, 
                k=top_k,
                distance_threshold=score_threshold  # Higher threshold for better relevance
            )
            
            # Log retrieval results
            self.logger.info(f"Retrieved {len(docs)} documents")
            for i, doc in enumerate(docs):
                self.logger.debug(f"Document {i+1}: {doc.metadata.get('source', 'Unknown source')}")
            
            # Limit document length to reduce processing time
            for doc in docs:
                if len(doc.page_content) > 2000:  # Limit to 2000 chars
                    doc.page_content = doc.page_content[:2000] + "..."
            
            # Cache the results
            self._doc_cache[cache_key] = docs
            
            # Limit cache size
            if len(self._doc_cache) > 100:
                # Remove oldest items (first 20 items)
                for old_key in list(self._doc_cache.keys())[:20]:
                    del self._doc_cache[old_key]
            
            return docs
            
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []
        
    def generate_answer(self, query: str, docs: List[Document]) -> str:
        """
        Generate an answer based on the query and retrieved documents.
        
        Args:
            query: The query to answer
            docs: List of relevant documents
            
        Returns:
            Generated answer
        """
        self.logger.info(f"Generating answer for query: {query}")
        
        try:
            # Create context from documents with length limits and better formatting
            context_parts = []
            total_context_length = 0
            max_context_length = 6000  # Maximum context length to send to LLM
            
            for doc in docs:
                # Add source information if available
                source = doc.metadata.get('source', 'Unknown source')
                # Use shorter content to reduce token count
                content = doc.page_content
                
                # Calculate how much more context we can add
                part = f"Source: {source}\n{content}"
                if total_context_length + len(part) > max_context_length:
                    # If adding this document would exceed our limit, truncate it
                    available_length = max_context_length - total_context_length
                    if available_length > 200:  # Only add if we can include a meaningful chunk
                        part = f"Source: {source}\n{content[:available_length-100]}..."
                        context_parts.append(part)
                        total_context_length += len(part)
                    break
                else:
                    context_parts.append(part)
                    total_context_length += len(part)
            
            context = "\n\n".join(context_parts)
            
            # Create a more concise prompt for faster processing
            prompt = f"""You are a knowledgeable Canadian university consultant answering a question based only on the provided information.

Context:
{context}

Question: {query}

Answer concisely but accurately, mentioning sources when relevant. If the information is not in the context, simply state that you don't have enough information to answer."""
            
            # Track start time for performance monitoring
            start_time = time.time()
            
            # Generate answer using the LLM
            answer = self.llm.invoke(prompt)
            
            # Log performance metrics
            duration = time.time() - start_time
            self.logger.info(f"Answer generated in {duration:.2f} seconds")
            
            return answer
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            return f"I apologize, but I encountered an error while generating the answer: {str(e)}"
        
    def interactive_session(self):
        """Start an interactive question-answering session."""
        self.logger.info("Starting interactive session")
        
        if not self.has_vectordb:
            print("⚠️ Vector database not available. Please run 'train' mode first.")
            return
        
        print("\n" + "="*80)
        print("🎓 Canadian University Information Assistant")
        print("="*80)
        print("Ask any question about Canadian universities.")
        print("Type 'exit' or 'quit' to end the session.")
        print("="*80 + "\n")
        
        while True:
            # Get user query
            query = input("📝 Question: ")
            
            if query.lower() in ['exit', 'quit']:
                print("\nThank you for using the Canadian University Information Assistant! Goodbye.")
                break
                
            if not query.strip():
                continue
                
            try:
                # Start timing
                start_time = time.time()
                retrieval_start = time.time()
                
                # Retrieve relevant documents
                docs = self.retrieve_documents(query)
                
                retrieval_time = time.time() - retrieval_start
                
                if not docs:
                    print("⚠️ No relevant information found in the database.")
                    continue
                
                print(f"📊 Retrieved {len(docs)} relevant documents in {retrieval_time:.2f} seconds")
                
                # Start generation timing
                generation_start = time.time()
                
                # Generate answer
                answer = self.generate_answer(query, docs)
                
                generation_time = time.time() - generation_start
                total_time = time.time() - start_time
                
                # Display answer
                print("\n🔍 Answer:")
                print(answer)
                
                # Display performance metrics
                print(f"\n⏱️ Performance metrics:")
                print(f"  • Document retrieval: {retrieval_time:.2f}s")
                print(f"  • Answer generation: {generation_time:.2f}s")
                print(f"  • Total processing time: {total_time:.2f}s")
                print("\n" + "-"*80 + "\n")
                
            except Exception as e:
                self.logger.error(f"Error processing query: {e}")
                print(f"❌ Error: {e}")
                
    def process_query(self, query: str) -> str:
        """
        Process a single query and return the answer.
        
        Args:
            query: The query to answer
            
        Returns:
            Generated answer
        """
        self.logger.info(f"Processing query: {query}")
        
        if not self.has_vectordb:
            return "Vector database not available. Please run 'train' mode first."
        
        try:
            # Retrieve relevant documents
            docs = self.retrieve_documents(query)
            
            if not docs:
                return "No relevant information found in the database."
                
            # Generate answer
            answer = self.generate_answer(query, docs)
            
            return answer
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return f"Error: {e}"

    def _initialize_chain(self) -> None:
        """
        Initialize the RAG chain.
        """
        try:
            logger.info("Initializing RAG chain")
            
            # Create a prompt template
            prompt_template = """
            Answer the question based on the provided context. If the context doesn't contain relevant information, 
            admit that you don't know rather than making up an answer.
            
            Context:
            {context}
            
            Question: {input}
            
            Answer:
            """
            
            prompt = PromptTemplate.from_template(prompt_template)
            
            # Create a document chain
            doc_chain = create_stuff_documents_chain(self.llm, prompt)
            
            # Create a retrieval chain
            self.chain = create_retrieval_chain(self.retriever, doc_chain)
            
            logger.info("RAG chain initialized")
            
        except Exception as e:
            logger.error(f"Error initializing RAG chain: {e}")
            raise e
    
    def query(self, query: str) -> Dict[str, Any]:
        """
        Query the RAG engine.
        
        Args:
            query: Query string
            
        Returns:
            Dictionary with response and source documents
        """
        try:
            logger.info(f"Querying RAG engine: {query}")
            
            if not self.chain:
                raise ValueError("RAG chain not initialized")
            
            # Run the chain
            response = self.chain.invoke({"input": query})
            
            # Extract the answer and source documents
            answer = response.get("answer", "")
            source_documents = response.get("context", [])
            
            logger.info(f"RAG engine response: {answer[:100]}...")
            
            return {
                "answer": answer,
                "source_documents": source_documents
            }
            
        except Exception as e:
            logger.error(f"Error querying RAG engine: {e}")
            raise e
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Get relevant documents for a query without generating an answer.
        
        Args:
            query: Query string
            
        Returns:
            List of relevant documents
        """
        try:
            logger.info(f"Getting relevant documents for: {query}")
            
            if not self.retriever:
                raise ValueError("Retriever not initialized")
            
            # Get relevant documents
            documents = self.retriever.get_relevant_documents(query)
            
            logger.info(f"Found {len(documents)} relevant documents")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting relevant documents: {e}")
            raise e 