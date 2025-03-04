#!/usr/bin/env python3
"""
Trainer module for embedding documents and creating vector database.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import yaml
import shutil
import glob
from datetime import datetime
import tempfile
import sqlite3

# Update imports - Remove ChromaDB and add FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import FAISS
# Use FakeEmbeddings
from langchain_core.embeddings import FakeEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Import related modules
from utils.logger import get_logger
from data.scraper import WebScraper
from core.document_processor import DocumentProcessor

# Remove problematic import
# from src.core.config import settings
# from src.utils.logging_utils import setup_logger

# Set up logging
# setup_logger("trainer")
logger = get_logger("trainer")

# Define default settings
DEFAULT_SETTINGS = {
    "VECTORDB_PATH": os.path.join("data", "vectordb"),
    "DATA_DIR": "data",
    "MODEL_PATH": os.path.join("models", "embeddings"),
    "CHUNK_SIZE": 1000,
    "CHUNK_OVERLAP": 200
}

class Trainer:
    def __init__(self, document_processor):
        """
        Initialize the Trainer with a document processor.

        Args:
            document_processor: The DocumentProcessor instance to process documents.
        """
        self.document_processor = document_processor
        
        # Use default settings instead of importing from config
        self.vectordb_path = DEFAULT_SETTINGS["VECTORDB_PATH"]
        self.data_path = DEFAULT_SETTINGS["DATA_DIR"]
        self.model_path = DEFAULT_SETTINGS["MODEL_PATH"]
        self.chunk_size = DEFAULT_SETTINGS["CHUNK_SIZE"]
        self.chunk_overlap = DEFAULT_SETTINGS["CHUNK_OVERLAP"]
        self.vectordb = None

    def clean_documents(self, documents: List[Document]) -> List[Document]:
        """
        Clean and validate documents.

        Args:
            documents: List of documents to clean.

        Returns:
            List of cleaned documents.
        """
        # Remove any documents with empty content
        cleaned_docs = [doc for doc in documents if doc.page_content.strip()]
        
        if not cleaned_docs:
            logger.warning("No valid documents found after cleaning.")
        
        return cleaned_docs

    def create_chunks(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.

        Args:
            documents: List of documents to split.

        Returns:
            List of document chunks.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents.")
        
        return chunks

    def create_vectordb(self, documents: List[Document]) -> None:
        """
        Create a vector database from documents.

        Args:
            documents: Documents to add to the vector database.
        """
        try:
            # Use FakeEmbeddings for simplicity and to avoid transformers issues
            embedding_function = FakeEmbeddings(size=384)
            
            logger.info(f"Using FakeEmbeddings")
            
            # Check if vectordb directory exists, create if not
            os.makedirs(os.path.dirname(self.vectordb_path), exist_ok=True)
            
            # Create FAISS index from documents
            self.vectordb = FAISS.from_documents(
                documents, embedding_function
            )
            
            # Save the FAISS index
            self.vectordb.save_local(self.vectordb_path)
            
            # Save index creation metadata
            metadata = {
                "created_at": datetime.now().isoformat(),
                "documents_count": len(documents),
                "embedding_model": "FakeEmbeddings",
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            }
            
            with open(os.path.join(self.vectordb_path, "metadata.json"), "w") as f:
                json.dump(metadata, f)
            
            logger.info(f"Vector database created successfully at {self.vectordb_path}")
            logger.info(f"Index summary: {metadata}")
            
        except Exception as e:
            logger.error(f"Error creating vector database: {str(e)}")
            raise e

    def load_vectordb(self) -> None:
        """
        Load the existing vector database.
        """
        try:
            # Check if vectordb exists
            if not os.path.exists(self.vectordb_path) or not os.listdir(self.vectordb_path):
                logger.error(f"Vector database does not exist at {self.vectordb_path}")
                return None
            
            # Use FakeEmbeddings for simplicity and to avoid transformers issues
            embedding_function = FakeEmbeddings(size=384)
            
            # Load the FAISS index
            self.vectordb = FAISS.load_local(self.vectordb_path, embedding_function)
            
            # Load metadata if available
            metadata_path = os.path.join(self.vectordb_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                logger.info(f"Loaded vector database with metadata: {metadata}")
            else:
                logger.info(f"Loaded vector database without metadata")
                
            return self.vectordb
            
        except Exception as e:
            logger.error(f"Error loading vector database: {str(e)}")
            return None

    def train(self) -> None:
        """
        Train the model by processing documents and creating a vector database.
        """
        try:
            # Get all documents from document processor
            documents = self.document_processor.get_all_documents()
            
            if not documents:
                logger.error("No documents to process.")
                return
            
            logger.info(f"Processing {len(documents)} documents.")
            
            # Clean documents
            documents = self.clean_documents(documents)
            
            # Split documents into chunks
            documents = self.create_chunks(documents)
            
            # Create vector database
            self.create_vectordb(documents)
            
            # Add documents to processor's storage
            self.document_processor.add_documents(documents)
            
            logger.info("Training completed successfully.")
            
        except Exception as e:
            logger.error(f"Error during training: {str(e)}")
            raise e 