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
# Replace FakeEmbeddings with HuggingFaceOnnxEmbeddings
from langchain_community.embeddings import HuggingFaceOnnxEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Import related modules
from utils.logger import get_logger
from data.scraper import WebScraper
from core.document_processor import DocumentProcessor
from utils.file_utils import load_json_file, save_json_file

class EmbeddingTrainer:
    """
    Class for training embeddings and creating vector database 
    for university document retrieval.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the trainer with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        self.logger = get_logger("trainer")
        self.config_path = config_path
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get embedding model config
        self.embedding_config = self.config.get('embedding', {})
        self.model_name = self.embedding_config.get('model_name', 'all-MiniLM-L6-v2')
        
        # Initialize paths
        self.data_dir = Path(self.config.get('data', {}).get('data_dir', 'data'))
        self.vectordb_dir = self.data_dir / "vectordb"
        self.vectordb_dir.mkdir(exist_ok=True, parents=True)
        
        # Create backup directory for data
        self.backup_dir = self.data_dir / "backup"
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        
        self.logger.info(f"Trainer initialized with config from {config_path}")
        self.logger.info(f"Using embedding model: {self.model_name}")
        
    def load_documents(self) -> List[Document]:
        """
        Load documents from the scraper backup or create new ones if needed.
        
        Returns:
            List of Document objects
        """
        self.logger.info("Loading documents...")
        
        # Try to load from backup first
        backup_files = list(self.backup_dir.glob("scrape_backup_*.json"))
        
        if backup_files:
            # Use the most recent backup
            most_recent = max(backup_files, key=lambda x: x.stat().st_mtime)
            self.logger.info(f"Loading from backup: {most_recent}")
            
            with open(most_recent, 'r') as f:
                data = json.load(f)
                
            # Convert to Document objects
            documents = []
            for doc_data in data:
                doc = Document(
                    page_content=doc_data.get('page_content', ''),
                    metadata=doc_data.get('metadata', {})
                )
                documents.append(doc)
                
            self.logger.info(f"Loaded {len(documents)} documents from backup")
            return documents
        else:
            # No backup found, scrape documents
            self.logger.info("No backup found, scraping documents...")
            scraper = WebScraper(self.config_path)
            documents = scraper.scrape_all_universities()
            self.logger.info(f"Scraped {len(documents)} documents")
            return documents

    def create_vectordb(self, documents: List[Document]) -> None:
        """Create a vector database from documents."""
        logger = get_logger("trainer.create_vectordb")
        
        # Check for empty documents
        if not documents:
            logger.warning("No documents provided for vector database creation")
            return
            
        logger.info(f"Creating vector database from {len(documents)} documents")
        
        # Create the vectordb directory if it doesn't exist
        os.makedirs(self.vectordb_dir, exist_ok=True)
            
        # Use HuggingFaceOnnxEmbeddings for better semantic search
        logger.info("Initializing HuggingFaceOnnxEmbeddings")
        embedding_function = HuggingFaceOnnxEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create FAISS index with document embeddings
        logger.info("Creating FAISS index with document embeddings")
        vectordb = FAISS.from_documents(documents, embedding_function)
        
        # Save the vector database to disk
        logger.info(f"Saving FAISS index to {self.vectordb_dir / 'faiss_index'}")
        vectordb.save_local(str(self.vectordb_dir / "faiss_index"))
        
        # Create an index summary with metadata about the documents
        logger.info("Creating index summary")
        index_summary = {
            "created_at": datetime.now().isoformat(),
            "document_count": len(documents),
            "embedding_model": "HuggingFaceOnnxEmbeddings(all-MiniLM-L6-v2)",
            "sources": list(set([doc.metadata.get("source", "unknown") for doc in documents])),
            "vector_dimension": 384  # Dimension for "all-MiniLM-L6-v2"
        }
        
        # Save the index summary
        with open(self.vectordb_dir / "index_summary.json", "w") as f:
            json.dump(index_summary, f, indent=2)
        
        logger.info("Vector database created successfully")

    def create_index_summary(self, documents: List[Document]):
        """
        Create a summary of the indexed documents.
        
        Args:
            documents: List of Document objects
        """
        self.logger.info("Creating index summary...")
        
        # Group documents by university
        universities = {}
        for doc in documents:
            university = doc.metadata.get('university', 'Unknown')
            if university not in universities:
                universities[university] = {
                    'count': 0,
                    'pages': set()
                }
            universities[university]['count'] += 1
            universities[university]['pages'].add(doc.metadata.get('url', ''))
        
        # Convert sets to lists for JSON serialization
        for university in universities:
            universities[university]['pages'] = list(universities[university]['pages'])
            
        # Create summary
        summary = {
            'total_documents': len(documents),
            'embedding_model': "HuggingFaceOnnxEmbeddings(all-MiniLM-L6-v2)",
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'universities': universities
        }
        
        # Save summary
        summary_path = self.vectordb_dir / "index_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        self.logger.info(f"Index summary saved to {summary_path}")
            
    def train(self):
        """
        Train the embeddings and create vector database.
        """
        self.logger.info("Starting training process...")
        
        # Load documents
        documents = self.load_documents()
        
        # Create vector database directly first (skip processor.add_documents for now)
        self.logger.info("Creating vector database directly...")
        try:
            self.create_vectordb(documents)
            self.create_index_summary(documents)
            self.logger.info("Training completed successfully")
        except Exception as e:
            self.logger.error(f"Error creating vector database: {e}")
            # Fallback to document processor if direct creation fails
            self.logger.info("Attempting fallback to document processor...")
            processor = DocumentProcessor(self.config)
            processor.add_documents(documents) 