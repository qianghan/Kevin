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

# Update imports - Remove ChromaDB and add FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import FAISS
# Replace HuggingFaceOnnxEmbeddings with SentenceTransformerEmbeddings
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# Import related modules
from utils.logger import get_logger
from models.deepseek_client import DeepSeekAPI
from core.document_processor import DocumentProcessor

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
        
        # Check if vector database exists
        faiss_index_path = self.vectordb_dir / "faiss_index"
        if not faiss_index_path.exists():
            self.logger.warning(f"FAISS index not found at {faiss_index_path}")
            self.logger.warning("Please run the 'train' mode first to create the vector database")
            self.has_vectordb = False
        else:
            self.has_vectordb = True
            self.logger.info(f"Found FAISS index at {faiss_index_path}")
            
            # Initialize vector database
            self._initialize_vectordb()
            
        # Initialize LLM
        self._initialize_llm()
        
        self.logger.info(f"RAG Engine initialized with config from {config_path}")

    def _initialize_vectordb(self) -> None:
        """Initialize the vector database."""
        logger = get_logger("rag.engine")
        try:
            # Use SentenceTransformerEmbeddings instead
            logger.info("Initializing SentenceTransformerEmbeddings")
            embedding_function = SentenceTransformerEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )
            
            # Load FAISS index from disk
            faiss_index_path = str(self.vectordb_dir / "faiss_index")
            logger.info(f"Loading FAISS index from {faiss_index_path}")
            
            try:
                self.vectordb = FAISS.load_local(
                    folder_path=faiss_index_path,
                    embeddings=embedding_function
                )
                
                # Set up retriever
                logger.info("Setting up retriever")
                self.retriever = self.vectordb.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": self.top_k}
                )
                
                logger.info("Vector database initialized successfully")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                # If loading fails, try creating a new one with a placeholder
                logger.warning("Creating new placeholder FAISS index")
                
                # Create a new empty FAISS index with a placeholder document
                texts = ["Placeholder document"]
                metadatas = [{"source": "initialization"}]
                
                self.vectordb = FAISS.from_texts(
                    texts=texts,
                    embedding=embedding_function,
                    metadatas=metadatas
                )
                
                # Set up retriever
                logger.info("Setting up retriever with placeholder index")
                self.retriever = self.vectordb.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 1}  # Use 1 since there's only one document
                )
                
                # Save the placeholder index
                self.vectordb.save_local(faiss_index_path)
                logger.warning("Created and saved placeholder FAISS index")
            
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
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
        
        # Search for similar documents
        docs = self.vectordb.similarity_search(query, k=k)
        
        self.logger.info(f"Retrieved {len(docs)} documents")
        return docs
        
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
        
        # Create context from documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Create a prompt for the LLM
        prompt = f"""Answer the following question based on the provided context. 
If the context doesn't contain relevant information, acknowledge that you don't know.

Context:
{context}

Question: {query}

Please provide a detailed answer with the most relevant information from the context:"""
        
        # Generate answer using invoke instead of completion
        answer = self.llm.invoke(prompt)
        
        return answer
        
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