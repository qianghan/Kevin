import os
import sys
sys.path.append(os.path.abspath("."))
from api.services.cache.semantic_cache import SemanticCache
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("semantic_cache_test")

def test_semantic_cache():
    try:
        # Create a semantic cache instance directly with correct parameters
        cache = SemanticCache(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            similarity_threshold=0.8,
            max_cache_size=100,
            ttl_seconds=604800
        )
        logger.info(f'Cache created: {cache is not None}')
        
        # Test adding and retrieving from cache
        test_query = 'What are the tuition fees for McGill University?'
        test_response = {
            'answer': 'Test answer for McGill tuition fees',
            'thinking_steps': [],
            'documents': [],
            'duration_seconds': 0.5
        }
        
        # Add test data to cache using the actual method names
        cache.add(test_query, test_response)
        logger.info(f'Added query to cache: {test_query}')
        
        # Test retrieving the exact same query
        cached_response = cache.get(test_query)
        logger.info(f'Original query cached response: {cached_response}')
        
        # Test retrieving a semantically similar query
        similar_query = 'Tell me about tuition fees at McGill University'
        similar_cached = cache.get(similar_query)
        logger.info(f'Similar query cached response: {similar_cached}')
        
        # Get cache statistics
        stats = cache.get_stats()
        logger.info(f'Cache statistics: {stats}')
        
        logger.info('Cache test complete')
    except Exception as e:
        logger.error(f"Error testing semantic cache: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_semantic_cache() 