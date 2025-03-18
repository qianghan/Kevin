from api.services.cache.cache_service import get_semantic_cache

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
    test_semantic_cache() 