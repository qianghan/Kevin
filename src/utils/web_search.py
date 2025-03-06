"""
Web search utilities using the Tavily API.
"""

import os
import sys
import json
import requests
import yaml
import time
import random
import urllib.parse
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain.schema import Document
from tavily import TavilyClient
from fake_useragent import UserAgent

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from utils.logger import get_logger, api_logger

# Load environment variables
load_dotenv()

# Configure module logger
logger = get_logger(__name__)

def search_web(query: str, max_results: int = 5, search_depth: str = "basic") -> List[Document]:
    """
    Search the web using Tavily and return results as documents.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        search_depth: Search depth ('basic' or 'comprehensive')
        
    Returns:
        List of Document objects with search results
    """
    # Load config
    try:
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        web_search_config = config.get('web_search', {})
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        web_search_config = {}
    
    # Get API key from config or environment
    api_key = web_search_config.get('tavily_api_key', '')
    if not api_key:
        api_key = os.getenv('TAVILY_API_KEY', '')
    
    if not api_key:
        logger.error("No Tavily API key found")
        return []
    
    # Use configured values if provided
    max_results = web_search_config.get('max_results', max_results)
    search_depth = web_search_config.get('search_depth', search_depth)
    
    # Initialize Tavily client
    client = TavilyClient(api_key=api_key)
    
    logger.info(f"Searching web for: {query}")
    api_logger.info(f"Tavily search: {query[:100]}...")
    
    try:
        start_time = time.time()
        
        # Perform search
        response = client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Web search completed in {elapsed_time:.2f}s, found {len(response['results'])} results")
        
        # Convert results to documents
        documents = []
        for result in response.get('results', []):
            content = f"Title: {result.get('title', 'No Title')}\n\n{result.get('content', '')}"
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        'source': result.get('url', ''),
                        'title': result.get('title', 'No Title'),
                        'score': result.get('score', 0),
                        'search_query': query
                    }
                )
            )
        
        return documents
    
    except Exception as e:
        logger.error(f"Error searching the web: {e}", exc_info=True)
        api_logger.error(f"Tavily search failed: {str(e)}")
        return []

if __name__ == "__main__":
    # Example usage
    search_tool = WebSearchTool()
    query = "scholarship opportunities for international students at Canadian universities"
    results = search_tool.search(query)
    
    for i, doc in enumerate(results):
        print(f"Result {i+1}:")
        print(f"Source: {doc.metadata.get('source')}")
        print(f"Title: {doc.metadata.get('title')}")
        print(f"Content snippet: {doc.page_content[:200]}...")
        print("-" * 80) 