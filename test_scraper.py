#!/usr/bin/env python3
"""
Test script to debug the web scraper and document processing.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from src.data.scraper import WebScraper
from src.core.document_processor import DocumentProcessor

def main():
    """Run a test scrape and document processing."""
    print("=== Testing Web Scraper ===")
    
    # Initialize scraper
    scraper = WebScraper()
    
    # Test scraping just one university
    universities = scraper.config['universities']
    test_university = universities[0]  # University of Toronto
    
    print(f"Testing scraping for: {test_university['name']}")
    documents = scraper.scrape_university(test_university)
    
    print(f"Scraped {len(documents)} documents from {test_university['name']}")
    
    if len(documents) == 0:
        print("ERROR: No documents were scraped! Check the scraper configuration and network connectivity.")
        return
    
    # Print first document sample
    if documents:
        doc = documents[0]
        print("\nSample document content (first 200 chars):")
        print(f"{doc.page_content[:200]}...")
        print("\nMetadata:")
        for key, value in doc.metadata.items():
            print(f"  {key}: {value}")
    
    # Test adding to vector store
    print("\n=== Testing Document Processor ===")
    processor = DocumentProcessor()
    
    # Clear existing database
    print("Clearing existing vector store...")
    import shutil
    if os.path.exists(processor.persist_directory):
        try:
            # Just rename it for safety
            backup_dir = f"{processor.persist_directory}_backup_{int(time.time())}"
            shutil.move(processor.persist_directory, backup_dir)
            print(f"Backed up existing database to {backup_dir}")
        except Exception as e:
            print(f"Could not backup database: {e}")
    
    # Add documents to fresh vector store
    print(f"Adding {len(documents)} documents to vector store...")
    processor.add_documents(documents)
    
    # Test searching
    print("\n=== Testing Search ===")
    query = f"Tell me about {test_university['name']}"
    print(f"Searching for: {query}")
    results = processor.search_documents(query, k=2)
    
    print(f"Found {len(results)} results")
    if results:
        print("\nFirst result (first 200 chars):")
        print(f"{results[0].page_content[:200]}...")

if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    elapsed_time = time.time() - start_time
    print(f"\nTest completed in {elapsed_time:.2f} seconds") 