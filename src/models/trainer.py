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
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import VectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, AutoModel
import torch
from tqdm import tqdm
import hashlib
import pickle
import concurrent.futures
from contextlib import nullcontext

# Import related modules
from src.utils.logger import get_logger
from src.data.scraper import WebScraper
from src.core.document_processor import DocumentProcessor

# Set up logging
logger = get_logger("trainer")

# Define default settings
DEFAULT_SETTINGS = {
    "VECTORDB_PATH": os.path.join("data", "vectordb"),
    "DATA_DIR": "data",
    "MODEL_PATH": os.path.join("models", "embeddings"),
    "CHUNK_SIZE": 1500,
    "CHUNK_OVERLAP": 150,
    "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    "BATCH_SIZE": 64,
    "MAX_RETRIES": 3,
    "DEVICE": "cuda" if torch.cuda.is_available() else "cpu",
    "CHECKPOINT_INTERVAL": 500,
    "MAX_WORKERS": 4,
    "CACHE_DIR": os.path.join("data", "cache"),
    "USE_CACHE": True,
    "CLEAR_CACHE_AFTER_BATCH": True
}

class CustomHuggingFaceEmbeddings:
    """Custom embeddings class using HuggingFace models with batching and caching."""
    
    def __init__(self, model_name: str = DEFAULT_SETTINGS["EMBEDDING_MODEL"], 
                 batch_size: int = DEFAULT_SETTINGS["BATCH_SIZE"],
                 device: str = DEFAULT_SETTINGS["DEVICE"]):
        """Initialize the embeddings model."""
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self.tokenizer = None
        self.model = None
        self.cache = {}
        self._load_model()
        
    def _load_model(self):
        """Load the model and tokenizer."""
        try:
            logger.info(f"Loading model {self.model_name} on {self.device}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
            self.model.eval()
            
            # Enable memory efficient attention if available
            if hasattr(self.model, 'enable_memory_efficient_attention'):
                self.model.enable_memory_efficient_attention()
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
            
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts with optimized caching."""
        try:
            # Check cache first
            cache_key = hashlib.md5("".join(texts).encode()).hexdigest()
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Tokenize texts with optimized settings
            encoded = self.tokenizer(
                texts, 
                padding=True, 
                truncation=True, 
                max_length=512, 
                return_tensors="pt",
                return_attention_mask=True
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            
            # Get embeddings with memory optimization
            with torch.no_grad():
                with torch.cuda.amp.autocast() if self.device == "cuda" else nullcontext():
                    outputs = self.model(**encoded)
                    embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            # Normalize embeddings
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Cache results if enabled
            if DEFAULT_SETTINGS["USE_CACHE"]:
                self.cache[cache_key] = embeddings.tolist()
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise
            
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents with optimized batching."""
        try:
            all_embeddings = []
            
            # Process in optimized batches
            for i in tqdm(range(0, len(texts), self.batch_size), desc="Embedding documents"):
                batch = texts[i:i + self.batch_size]
                batch_embeddings = self._get_embeddings(batch)
                all_embeddings.extend(batch_embeddings)
                
                # Clear GPU cache if using CUDA
                if self.device == "cuda":
                    torch.cuda.empty_cache()
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            raise
            
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        try:
            return self._get_embeddings([text])[0]
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise
            
    def __call__(self, text: str) -> List[float]:
        """Make the embeddings class callable.
        
        This allows the class to be used directly as an embedding function
        when passed to FAISS or other vector stores.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding for the text
        """
        return self.embed_query(text)

class Trainer:
    """
    Class for training a model, including document processing and vector database creation.
    """
    def __init__(self, document_processor, settings: Dict[str, Any] = None):
        """
        Initialize the trainer with a document processor.
        
        Args:
            document_processor: Instance of DocumentProcessor for handling documents
            settings: Optional dictionary of settings to override defaults
        """
        self.document_processor = document_processor
        self.settings = {**DEFAULT_SETTINGS, **(settings or {})}
        
        # Initialize paths
        self.vectordb_path = self.settings["VECTORDB_PATH"]
        self.model_path = self.settings["MODEL_PATH"]
        
        # Create necessary directories
        os.makedirs(self.vectordb_path, exist_ok=True)
        os.makedirs(self.model_path, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = CustomHuggingFaceEmbeddings(
            model_name=self.settings["EMBEDDING_MODEL"],
            batch_size=self.settings["BATCH_SIZE"],
            device=self.settings["DEVICE"]
        )
        
    def clean_documents(self, documents: List[Document]) -> List[Document]:
        """
        Clean the raw documents.
        
        Args:
            documents: List of raw documents
            
        Returns:
            List of cleaned documents
        """
        logger.info(f"Cleaning {len(documents)} documents")
        cleaned_docs = []
        
        for doc in documents:
            if not isinstance(doc, Document):
                doc = Document(page_content=str(doc))
                
            # Clean text
            text = doc.page_content
            text = " ".join(text.split())  # Remove excess whitespace
            
            # Clean metadata
            metadata = doc.metadata.copy()
            metadata["cleaned_at"] = datetime.now().isoformat()
            
            cleaned_docs.append(Document(page_content=text, metadata=metadata))
            
        return cleaned_docs
    
    def create_chunks(self, documents: List[Document]) -> List[Document]:
        """
        Create chunks from documents using parallel processing.
        
        Args:
            documents: List of documents
            
        Returns:
            List of document chunks
        """
        logger.info(f"Creating chunks from {len(documents)} documents")
        
        # Validate documents before processing
        for doc in documents:
            if doc.page_content is None:
                raise ValueError("Document contains None content")
            if not doc.page_content or len(doc.page_content.strip()) == 0:
                raise ValueError("Document contains empty content")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings["CHUNK_SIZE"],
            chunk_overlap=self.settings["CHUNK_OVERLAP"],
            length_function=len,
            is_separator_regex=False,
        )
        
        # Create chunks in parallel
        chunks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.settings["MAX_WORKERS"]) as executor:
            # Submit chunking tasks
            future_to_doc = {
                executor.submit(text_splitter.split_documents, [doc]): doc 
                for doc in documents
            }
            
            # Process results as they complete
            with tqdm(total=len(documents), desc="Creating chunks") as pbar:
                for future in concurrent.futures.as_completed(future_to_doc):
                    doc = future_to_doc[future]
                    try:
                        doc_chunks = future.result()
                        chunks.extend(doc_chunks)
                        pbar.update(1)
                    except Exception as e:
                        logger.error(f"Error chunking document: {e}")
                        pbar.update(1)
                        # Re-raise the exception to propagate it
                        raise ValueError(f"Error chunking document: {e}")
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def create_vectordb(self, documents: List[Document]) -> VectorStore:
        """
        Create a vector database from documents with checkpointing.
        
        Args:
            documents: List of documents
            
        Returns:
            Vector database
        """
        try:
            logger.info("Creating vector database")
            
            # Clean the documents
            cleaned_docs = self.clean_documents(documents)
            
            # Create chunks
            chunks = self.create_chunks(cleaned_docs)
            
            if not chunks:
                raise ValueError("No chunks found after processing documents")
            
            # Initialize FAISS index
            logger.info(f"Creating FAISS index with {len(chunks)} chunks")
            
            # Process chunks in batches with checkpointing
            batch_size = self.settings["BATCH_SIZE"]
            total_chunks = len(chunks)
            processed_chunks = []
            
            for i in tqdm(range(0, total_chunks, batch_size), desc="Processing chunks"):
                batch = chunks[i:i + batch_size]
                
                # Create or load FAISS index
                if i == 0:
                    vectordb = FAISS.from_documents(batch, self.embeddings)
                else:
                    vectordb.add_documents(batch)
                
                processed_chunks.extend(batch)
                
                # Save checkpoint if needed
                if (i + batch_size) % self.settings["CHECKPOINT_INTERVAL"] == 0:
                    checkpoint_path = os.path.join(self.vectordb_path, f"checkpoint_{i + batch_size}")
                    vectordb.save_local(checkpoint_path)
                    logger.info(f"Saved checkpoint at {i + batch_size} chunks")
                
                # Clear cache if configured
                if self.settings["CLEAR_CACHE_AFTER_BATCH"]:
                    self.embeddings.cache.clear()
            
            # Save the final index
            logger.info(f"Saving FAISS index to {self.vectordb_path}")
            vectordb.save_local(self.vectordb_path)
            
            # Save metadata about the vector database
            metadata = {
                "chunk_size": self.settings["CHUNK_SIZE"],
                "chunk_overlap": self.settings["CHUNK_OVERLAP"],
                "embedding_model": self.settings["EMBEDDING_MODEL"],
                "num_chunks": len(chunks),
                "created_at": datetime.now().isoformat(),
                "settings": self.settings
            }
            
            with open(os.path.join(self.vectordb_path, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)
            
            # Save embeddings cache if enabled
            if self.settings["USE_CACHE"]:
                cache_path = os.path.join(self.vectordb_path, "embeddings_cache.pkl")
                with open(cache_path, "wb") as f:
                    pickle.dump(self.embeddings.cache, f)
            
            logger.info(f"Vector database creation complete with {len(chunks)} chunks")
            return vectordb
        
        except Exception as e:
            logger.error(f"Error creating vector database: {e}")
            raise
    
    def load_vectordb(self) -> VectorStore:
        """
        Load a vector database.
        
        Returns:
            Vector database
        """
        try:
            logger.info(f"Loading vector database from {self.vectordb_path}")
            
            # Load metadata
            metadata_path = os.path.join(self.vectordb_path, "metadata.json")
            if not os.path.exists(metadata_path):
                raise FileNotFoundError(f"Metadata file not found at {metadata_path}")
                
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            # Load embeddings cache if available
            cache_path = os.path.join(self.vectordb_path, "embeddings_cache.pkl")
            if os.path.exists(cache_path):
                with open(cache_path, "rb") as f:
                    self.embeddings.cache = pickle.load(f)
            
            # Load the FAISS index
            vectordb = FAISS.load_local(
                self.vectordb_path,
                self.embeddings,
                allow_dangerous_deserialization=True  # We trust our own saved files
            )
            
            logger.info(f"Vector database loaded successfully")
            return vectordb
        
        except Exception as e:
            logger.error(f"Error loading vector database: {e}")
            raise
    
    def train(self):
        """
        Train the model by creating a vector database.
        """
        try:
            logger.info("Starting training")
            
            # Get all documents
            documents = self.document_processor.get_all_documents()
            if not documents:
                raise ValueError("No documents found for training")
            
            # Create the vector database
            self.create_vectordb(documents)
            
            logger.info("Training complete")
        
        except Exception as e:
            logger.error(f"Error during training: {e}")
            raise 