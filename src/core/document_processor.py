#!/usr/bin/env python3
"""
Document processor for handling university documents.
"""

import os
import re
import sys
import json
import yaml
import time
import copy
import logging
import random
import hashlib
import tempfile
import glob
import shutil
import platform
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Union
from datetime import datetime
from collections import defaultdict, Counter
from tqdm import tqdm
import uuid
import sqlite3
import numpy as np

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.logger import get_logger
from src.models.embeddings import SimpleEmbeddings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Class for processing university documents, chunking them, and 
    storing them in a vector database.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the document processor with config.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = get_logger("document_processor")
        self.config = config
        
        # Get embedding model config
        self.embedding_config = config.get('embedding', {})
        self.embedding_model = self.embedding_config.get('model_name', 'all-MiniLM-L6-v2')
        self.fallback_embedding_models = self.embedding_config.get('fallback_models', [
            'all-MiniLM-L6-v2', 
            'paraphrase-MiniLM-L3-v2', 
            'all-mpnet-base-v2'
        ])
        
        # Get chunking config
        self.chunking_config = config.get('chunking', {})
        self.chunk_size = self.chunking_config.get('chunk_size', 1000)
        self.chunk_overlap = self.chunking_config.get('chunk_overlap', 200)
        
        # Initialize paths
        self.data_dir = Path(config.get('data', {}).get('data_dir', 'data'))
        self.vectordb_dir = self.data_dir / "vectordb"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.vectordb_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
            
    def get_or_create_vectorstore(self, documents: Optional[List[Document]] = None) -> FAISS:
        """Get an existing vector store or create a new one with the provided documents."""
        logger = get_logger("doc_processor.vectorstore")
        
        # Define the path to the FAISS index
        faiss_index_path = os.path.join(self.data_dir, "vectordb", "faiss_index")
        
        # Use HuggingFaceEmbeddings for better semantic search
        logger.info(f"Initializing HuggingFaceEmbeddings with model {self.embedding_model}")
        embedding_function = HuggingFaceEmbeddings(
            model_name=self.embedding_model
        )
        
        # Check if FAISS index exists
        if os.path.exists(faiss_index_path):
            try:
                logger.info(f"Loading existing FAISS index from {faiss_index_path}")
                return FAISS.load_local(faiss_index_path, embedding_function)
            except Exception as e:
                logger.error(f"Error loading existing FAISS index: {e}")
                logger.info("Will create a new FAISS index")
        
        # Require documents to create a new vectorstore
        if not documents:
            raise ValueError("Documents must be provided to create a new vector store")
        
        # Create the vectordb directory if it doesn't exist
        os.makedirs(os.path.join(self.data_dir, "vectordb"), exist_ok=True)
        
        # Create a new FAISS index
        logger.info(f"Creating new FAISS index from {len(documents)} documents")
        vectorstore = FAISS.from_documents(documents, embedding_function)
        
        # Save the index
        vectorstore.save_local(faiss_index_path)
        logger.info(f"FAISS index saved to {faiss_index_path}")
        
        return vectorstore
                
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks for better retrieval.
        
        Args:
            documents: List of documents to chunk
            
        Returns:
            List of chunked documents
        """
        logger = get_logger("core.document_processor")
        logger.info(f"Chunking {len(documents)} documents")
        
        start_time = time.time()
        chunked_docs = []
        
        # Stats tracking
        total_chunks = 0
        successful = 0
        failed = 0
        
        # Progress bar for chunking
        with tqdm(total=len(documents), desc="Chunking documents") as pbar:
            for i, doc in enumerate(documents):
                try:
                    # Skip empty documents
                    if not doc.page_content or len(doc.page_content.strip()) == 0:
                        logger.warning(f"Skipping empty document")
                        pbar.update(1)
                        continue
                    
                    # Chunk the document
                    chunks = self.text_splitter.split_documents([doc])
                    
                    # Add to our collection
                    chunked_docs.extend(chunks)
                    total_chunks += len(chunks)
                    successful += 1
                    
                    pbar.set_postfix({"Chunks": total_chunks, "Success": successful})
                except Exception as e:
                    logger.error(f"Error chunking document: {e}")
                    failed += 1
                
                pbar.update(1)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Chunked {successful}/{len(documents)} documents into {total_chunks} chunks in {elapsed_time:.2f}s")
        
        return chunked_docs
                
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector database.
        
        Args:
            documents: List of documents to add
        """
        logger = get_logger("core.document_processor")
        
        if not documents:
            logger.warning("No documents to add to vector database")
            return
        
        try:
            # Get or create the vector database
            vectorstore = self.get_or_create_vectorstore(documents)
            
            # Add documents to the vector database
            logger.info(f"Adding {len(documents)} documents to vector database")
            
            # Add documents in batches to avoid memory issues
            batch_size = 100
            total_added = 0
            
            # Progress bar for adding documents
            with tqdm(total=len(documents), desc="Adding documents to vector store") as pbar:
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i+batch_size]
                    try:
                        # Extract texts and metadatas from documents
                        texts = [doc.page_content for doc in batch]
                        metadatas = [doc.metadata for doc in batch]
                        
                        # Add batch to FAISS index
                        vectorstore.add_texts(
                            texts=texts,
                            metadatas=metadatas
                        )
                        
                        total_added += len(batch)
                        logger.info(f"Added batch of {len(batch)} documents (total: {total_added}/{len(documents)})")
                    except Exception as e:
                        logger.error(f"Error adding batch to vector database: {str(e)}")
                        # Try smaller batches if a batch fails
                        smaller_batch_size = 10
                        logger.info(f"Trying smaller batch size of {smaller_batch_size}")
                        for j in range(i, min(i+batch_size, len(documents)), smaller_batch_size):
                            smaller_batch = documents[j:j+smaller_batch_size]
                            try:
                                # Extract texts and metadatas from documents
                                texts = [doc.page_content for doc in smaller_batch]
                                metadatas = [doc.metadata for doc in smaller_batch]
                                
                                # Add smaller batch to FAISS index
                                vectorstore.add_texts(
                                    texts=texts,
                                    metadatas=metadatas
                                )
                                total_added += len(smaller_batch)
                                logger.info(f"Added smaller batch of {len(smaller_batch)} documents")
                            except Exception as e2:
                                logger.error(f"Error adding smaller batch: {str(e2)}")
                    
                    pbar.update(len(batch))
            
            # Save the updated index
            faiss_index_path = str(self.vectordb_dir / "faiss_index")
            logger.info(f"Saving updated FAISS index to {faiss_index_path}")
            vectorstore.save_local(faiss_index_path)
            
            logger.info(f"Successfully added {total_added} documents to vector database")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise e

    def get_all_documents(self) -> List[Document]:
        """
        Get all documents from the data directory.
        
        Returns:
            List of documents
        """
        logger = get_logger("core.document_processor")
        documents = []
        
        # Define the data path to scan for documents
        data_path = os.path.join(self.data_dir, "raw")
        
        # Create data path if it doesn't exist
        os.makedirs(data_path, exist_ok=True)
        
        # Create a sample document if there are no documents
        if not os.listdir(data_path):
            logger.warning("No documents found in data directory, creating a sample document")
            sample_content = """# Sample Document
This is a sample document created because no documents were found in the data directory.
You should add more documents to improve the quality of the search.

## Topics
- Canadian universities
- Programs and courses
- Admission requirements
- Tuition fees
- Campus life
"""
            sample_file = os.path.join(data_path, "sample.md")
            with open(sample_file, "w") as f:
                f.write(sample_content)
        
        # Define loaders for different file types
        loaders = {
            ".txt": self._load_text_file,
            ".md": self._load_markdown_file,
            ".pdf": self._load_pdf_file,
            ".csv": self._load_csv_file,
            ".json": self._load_json_file,
            ".html": self._load_html_file,
        }
        
        # Find all files in the data directory
        file_count = 0
        loaded_count = 0
        
        logger.info(f"Scanning directory {data_path} for documents")
        for root, _, files in os.walk(data_path):
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                file_count += 1
                
                # Get file extension
                ext = os.path.splitext(file)[1].lower()
                
                if ext in loaders:
                    try:
                        logger.info(f"Loading {file_path}")
                        docs = loaders[ext](file_path)
                        
                        # Add source metadata to each document
                        for doc in docs:
                            if "source" not in doc.metadata:
                                doc.metadata["source"] = file_path
                        
                        documents.extend(docs)
                        loaded_count += 1
                        logger.info(f"Loaded {len(docs)} documents from {file_path}")
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
                else:
                    logger.warning(f"Unsupported file type: {file_path}")
        
        logger.info(f"Loaded {loaded_count}/{file_count} files, total documents: {len(documents)}")
        
        return documents

    def _load_text_file(self, file_path: str) -> List[Document]:
        """
        Load a text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            List of documents
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            return [Document(page_content=text, metadata={"source": file_path})]
        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {e}")
            return []
    
    def _load_markdown_file(self, file_path: str) -> List[Document]:
        """
        Load a markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            List of documents
        """
        # For this simple implementation, we'll treat markdown as plain text
        return self._load_text_file(file_path)
    
    def _load_pdf_file(self, file_path: str) -> List[Document]:
        """
        Load a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of documents
        """
        try:
            # Use a placeholder for PDF loading
            logger.warning(f"PDF loading not fully implemented for {file_path}")
            return [Document(page_content=f"PDF content from {file_path}", metadata={"source": file_path})]
        except Exception as e:
            logger.error(f"Error loading PDF file {file_path}: {e}")
            return []
    
    def _load_csv_file(self, file_path: str) -> List[Document]:
        """
        Load a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of documents
        """
        try:
            # Use a placeholder for CSV loading
            logger.warning(f"CSV loading not fully implemented for {file_path}")
            return [Document(page_content=f"CSV content from {file_path}", metadata={"source": file_path})]
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return []
    
    def _load_json_file(self, file_path: str) -> List[Document]:
        """
        Load a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of documents
        """
        try:
            # Use a placeholder for JSON loading
            logger.warning(f"JSON loading not fully implemented for {file_path}")
            return [Document(page_content=f"JSON content from {file_path}", metadata={"source": file_path})]
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {e}")
            return []
    
    def _load_html_file(self, file_path: str) -> List[Document]:
        """
        Load an HTML file.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            List of documents
        """
        try:
            # Use a placeholder for HTML loading
            logger.warning(f"HTML loading not fully implemented for {file_path}")
            return [Document(page_content=f"HTML content from {file_path}", metadata={"source": file_path})]
        except Exception as e:
            logger.error(f"Error loading HTML file {file_path}: {e}")
            return []

if __name__ == "__main__":
    # Simple test code
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    processor = DocumentProcessor(config)
    test_doc = Document(page_content="This is a test document.", metadata={"source": "test"})
    processor.add_documents([test_doc]) 