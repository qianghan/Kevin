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
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
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
            self._initialize_vectordb()
            
        # Initialize LLM
        self._initialize_llm()
        
        self.logger.info(f"RAG Engine initialized with config from {config_path}")

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
                try:
                    embedding_function = HuggingFaceEmbeddings(model_name=embedding_model)
                    logger.info(f"Successfully loaded HuggingFace embedding model: {embedding_model}")
                except Exception as e:
                    logger.warning(f"Could not load HuggingFace embeddings: {e}. Falling back to SimpleEmbeddings.")
                    embedding_function = SimpleEmbeddings()
            else:
                logger.warning("No metadata.json found. Using SimpleEmbeddings as fallback.")
                embedding_function = SimpleEmbeddings()
            
            # Load the FAISS index
            self.vectordb = FAISS.load_local(
                self.vectordb_dir, 
                embedding_function,
                allow_dangerous_deserialization=True  # We trust our own saved files
            )
            
            # Create a retriever with improved search parameters
            self.retriever = self.vectordb.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": self.top_k,
                    "score_threshold": 0.15,  # Lower threshold to find more diverse matches
                    "fetch_k": self.top_k * 4,  # Fetch even more candidates for better filtering
                    "filter": None  # No filtering to ensure comprehensive results
                }
            )
            
            logger.info(f"Vector database initialized successfully with retriever (k={self.top_k})")
            
            # Verify the database is working using direct similarity search
            test_query = "university"
            try:
                test_docs = self.vectordb.similarity_search(test_query, k=1)
                if test_docs:
                    logger.info(f"Vector database verification successful. Found {len(test_docs)} test documents.")
                    logger.debug(f"Sample document: {test_docs[0].page_content[:100]}...")
                else:
                    logger.warning("Vector database verification: No test documents found.")
            except Exception as e:
                logger.warning(f"Vector database verification failed: {e}")
                
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
            # Use direct vector similarity search instead of the retriever
            # This bypasses any potential issues with the retriever configuration
            docs = self.vectordb.similarity_search(
                query, 
                k=k,
                distance_threshold=None  # No threshold filtering to ensure we get results
            )
            
            # Log retrieval results
            self.logger.info(f"Retrieved {len(docs)} documents")
            for i, doc in enumerate(docs):
                self.logger.debug(f"Document {i+1}: {doc.metadata.get('source', 'Unknown source')}")
            
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
            # Create context from documents with metadata
            context_parts = []
            for doc in docs:
                # Add source information if available
                source = doc.metadata.get('source', 'Unknown source')
                content = doc.page_content
                context_parts.append(f"Source: {source}\n{content}")
            
            context = "\n\n".join(context_parts)
            
            # Create a more detailed prompt for the LLM tailored for university consultation
            prompt = f"""You are an experienced professional consultant specializing in Canadian university information, with extensive knowledge about admissions, programs, financial aid, campus life, and other aspects of higher education in Canada.

You're speaking with a student or parent who is seeking guidance about Canadian universities. Your goal is to provide accurate, helpful, and nuanced advice that addresses their specific needs.

Based on the following information sources, please answer the query in a professional yet approachable manner. Format important details like deadlines, requirements, or costs in a way that's easy to understand.

Context:
{context}

Question: {query}

In your response:
1. Directly address their specific question first
2. Provide relevant details, statistics, or requirements if available
3. Note any important deadlines or processes they should be aware of
4. Suggest additional considerations they might not have thought of
5. Cite your sources when possible (e.g., "According to UBC's website...")
6. If the information is incomplete or outdated, acknowledge this and suggest where they might find the most current information

If the context doesn't contain information to answer the question properly, be transparent about this limitation rather than making assumptions. You may suggest what information they should look for and where."""
            
            # Generate answer using the LLM
            answer = self.llm.invoke(prompt)
            
            # Log the generated answer
            self.logger.info("Successfully generated answer")
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
                # Retrieve relevant documents
                docs = self.retrieve_documents(query)
                
                if not docs:
                    print("⚠️ No relevant information found in the database.")
                    continue
                    
                # Generate answer
                answer = self.generate_answer(query, docs)
                
                # Display answer
                print("\n🔍 Answer:")
                print(answer)
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