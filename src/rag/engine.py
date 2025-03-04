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

# Import related modules
from utils.logger import get_logger
from models.deepseek_client import DeepSeekAPI
from core.document_processor import DocumentProcessor

# Local imports
from src.models.embeddings import SimpleEmbeddings
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
        logger.info(f"Initializing vector database from {self.vectordb_dir}")
        
        # Create simple embeddings class instance (matches what's in trainer.py)
        embedding_function = SimpleEmbeddings()
        
        # Load the FAISS index
        self.vectordb = FAISS.load_local(self.vectordb_dir, embedding_function)
        
        # Create a retriever
        self.retriever = self.vectordb.as_retriever(search_kwargs={"k": self.top_k})
        
        logger.info(f"Vector database initialized with retriever (k={self.top_k})")
    
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