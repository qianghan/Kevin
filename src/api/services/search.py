"""
Search service for Kevin API.

This module provides functions for searching documents and the web.
"""

import time
from typing import Dict, Any, List, Optional

from src.utils.logger import get_logger
from src.api.services.documents import cache_document

logger = get_logger(__name__)


def search_documents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for documents in the vector store.
    
    Args:
        query: The search query.
        limit: Maximum number of results to return.
        
    Returns:
        A list of document dictionaries.
    """
    try:
        # Import here to avoid circular imports
        from src.core.vectorstore import get_vectorstore
        
        logger.info(f"Searching documents for query: {query} (limit: {limit})")
        
        # Get the vector store
        vectorstore = get_vectorstore()
        
        # Perform the search
        raw_docs = vectorstore.similarity_search(query, k=limit)
        
        # Convert to dictionaries and cache the documents
        documents = []
        for doc in raw_docs:
            # Create a document dictionary
            document = {
                "id": doc.metadata.get("id", ""),
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            
            # Cache the document
            cache_document(document)
            
            # Add to the results
            documents.append(document)
        
        logger.info(f"Found {len(documents)} documents for query: {query}")
        return documents
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise


def search_web(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web for information.
    
    Args:
        query: The search query.
        limit: Maximum number of results to return.
        
    Returns:
        A list of document dictionaries.
    """
    try:
        # Import here to avoid circular imports
        from src.core.web_search import web_search
        
        logger.info(f"Searching web for query: {query} (limit: {limit})")
        
        # Perform the search
        raw_docs = web_search(query, num_results=limit)
        
        # Convert to dictionaries and cache the documents
        documents = []
        for doc in raw_docs:
            # Check if the doc is already a dictionary
            if isinstance(doc, dict):
                document = doc
            else:
                # Create a document dictionary
                document = {
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
            
            # Cache the document
            cache_document(document)
            
            # Add to the results
            documents.append(document)
        
        logger.info(f"Found {len(documents)} web results for query: {query}")
        return documents
        
    except Exception as e:
        logger.error(f"Error searching web: {e}")
        raise 