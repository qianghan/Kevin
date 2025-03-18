#!/usr/bin/env python3
"""
Simple test script to verify the semantic cache functionality.
"""

import time
from api.services.cache.cache_service import (
    get_semantic_cache, add_to_cache, get_from_cache, get_cache_stats
)

def test_cache():
    """Test basic cache functionality."""
    print("Testing semantic cache...")
    
    # Get the cache instance
    cache = get_semantic_cache()
    if not cache:
        print("Error: Failed to get semantic cache instance")
        return False
    
    print(f"Cache initialized: {cache is not None}")
    
    # Test adding to cache
    test_query = "What is the admission process for University of Toronto?"
    test_response = {
        "answer": "The admission process involves...",
        "thinking_steps": [{"step": 1, "content": "Thinking about admission process"}],
        "documents": [{"title": "UofT Admissions", "url": "https://example.com"}]
    }
    
    success = add_to_cache(test_query, test_response)
    print(f"Added to cache: {success}")
    
    # Get stats after adding
    stats = get_cache_stats()
    print(f"Cache stats after adding: {stats}")
    
    # Test retrieving from cache (exact match)
    retrieved = get_from_cache(test_query)
    if retrieved:
        print("Cache hit for exact match!")
        print(f"Retrieved answer: {retrieved.get('answer', '')[:50]}...")
    else:
        print("Cache miss for exact match!")
    
    # Test retrieving with similar query
    similar_query = "How do I apply to University of Toronto?"
    similar_retrieved = get_from_cache(similar_query)
    if similar_retrieved:
        print("Cache hit for similar query!")
        print(f"Retrieved answer for similar query: {similar_retrieved.get('answer', '')[:50]}...")
    else:
        print("Cache miss for similar query!")
    
    # Test retrieving with different query
    different_query = "What courses are offered at University of British Columbia?"
    different_retrieved = get_from_cache(different_query)
    if different_retrieved:
        print("Cache hit for different query!")
    else:
        print("Cache miss for different query (expected)")
    
    # Get final stats
    stats = get_cache_stats()
    print(f"Final cache stats: {stats}")
    
    return True

def test_semantic_cache():
    # Get the semantic cache instance
    cache = get_semantic_cache()
    print(f'Cache enabled: {cache is not None}')
    
    if not cache:
        print("Cache is not enabled or failed to initialize")
        return
    
    # Test adding and retrieving from cache
    test_query = 'What are the tuition fees for McGill University?'
    test_response = {
        'answer': 'Test answer for McGill tuition fees',
        'thinking_steps': [],
        'documents': [],
        'duration_seconds': 0.5
    }
    
    # Add test data to cache
    cache.add_to_cache(test_query, test_response)
    print(f'Added query to cache: {test_query}')
    
    # Test retrieving the exact same query
    cached_response = cache.get_from_cache(test_query)
    print(f'Original query cached response: {cached_response}')
    
    # Test retrieving a semantically similar query
    similar_query = 'Tell me about tuition fees at McGill University'
    similar_cached = cache.get_from_cache(similar_query)
    print(f'Similar query cached response: {similar_cached}')
    
    print('Cache test complete')

if __name__ == "__main__":
    print("Starting cache test...")
    success = test_cache()
    if success:
        print("Cache test completed successfully!")
    else:
        print("Cache test failed!")

    test_semantic_cache() 