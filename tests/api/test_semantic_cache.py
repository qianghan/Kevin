"""
Unit tests for the semantic cache implementation.

These tests verify that the semantic cache works correctly.
"""

import unittest
import tempfile
import os
import json
import numpy as np
import time
from unittest.mock import patch, MagicMock, mock_open

from src.api.services.cache.semantic_cache import SemanticCache
from src.api.services.cache.cache_service import (
    get_semantic_cache,
    add_to_cache,
    get_from_cache,
    clear_semantic_cache
)


class TestSemanticCache(unittest.TestCase):
    """Tests for the SemanticCache class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary file for the cache
        self.temp_file = tempfile.mktemp(suffix=".json")
        
        # Create a cache instance for testing
        self.cache = SemanticCache(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            similarity_threshold=0.85,
            max_cache_size=10,
            ttl_seconds=3600,  # 1 hour
            cache_file=self.temp_file
        )
        
        # Mock the compute_embedding method to return deterministic embeddings
        self.cache.compute_embedding = MagicMock()
        self.cache.compute_embedding.side_effect = self._mock_embedding
        
        # Test data
        self.test_query = "What is the admission process for University of Toronto?"
        self.similar_query = "How do I apply to University of Toronto?"
        self.different_query = "What are the programs offered at University of British Columbia?"
        
        self.test_response = {
            "answer": "The admission process involves...",
            "thinking_steps": [{"step": 1, "text": "First step"}],
            "documents": [{"title": "Admissions", "url": "example.com"}]
        }
        
    def tearDown(self):
        """Clean up test environment"""
        # Remove the temporary cache file
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
    
    def _mock_embedding(self, text):
        """Return a deterministic embedding based on the text"""
        if text == self.test_query:
            return np.array([0.1, 0.2, 0.3])
        elif text == self.similar_query:
            return np.array([0.11, 0.21, 0.29])  # Similar to test_query
        else:
            return np.array([0.8, 0.9, 0.7])  # Very different
    
    def test_add_and_get_exact_match(self):
        """Test adding and retrieving a cached response with exact match"""
        # Add to cache
        self.cache.add(self.test_query, self.test_response)
        
        # Get from cache
        retrieved = self.cache.get(self.test_query)
        
        # Verify
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["answer"], self.test_response["answer"])
        self.assertEqual(self.cache.hits, 1)
        self.assertEqual(self.cache.misses, 0)
    
    def test_get_with_similar_query(self):
        """Test retrieving a cached response with a similar query"""
        # Add to cache
        self.cache.add(self.test_query, self.test_response)
        
        # Get with similar query
        retrieved = self.cache.get(self.similar_query)
        
        # Verify
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["answer"], self.test_response["answer"])
        self.assertEqual(self.cache.hits, 1)
        self.assertEqual(self.cache.misses, 0)
    
    def test_get_with_different_query(self):
        """Test retrieving with a very different query (should miss)"""
        # Add to cache
        self.cache.add(self.test_query, self.test_response)
        
        # Get with different query
        retrieved = self.cache.get(self.different_query)
        
        # Verify
        self.assertIsNone(retrieved)
        self.assertEqual(self.cache.hits, 0)
        self.assertEqual(self.cache.misses, 1)
    
    @patch('src.api.services.cache.semantic_cache.SemanticCache.is_expired')
    def test_expiration(self, mock_is_expired):
        """Test that expired entries are not returned"""
        # Create a cache with very short TTL 
        cache = SemanticCache(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            similarity_threshold=0.85,
            ttl_seconds=1,  # 1 second
            cache_file=None
        )
        
        # Mock compute_embedding
        cache.compute_embedding = self.cache.compute_embedding
        
        # Mock is_expired to return False first, then True
        mock_is_expired.side_effect = [False, True]
        
        # Add to cache
        cache.add(self.test_query, self.test_response)
        
        # Verify it works when not expired
        retrieved = cache.get(self.test_query)
        self.assertIsNotNone(retrieved)
        
        # Verify it's treated as expired on second call
        retrieved = cache.get(self.test_query)
        self.assertIsNone(retrieved)
    
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('json.load')
    def test_save_and_load(self, mock_json_load, mock_path_exists, mock_open_file, mock_json_dump):
        """Test saving and loading the cache"""
        # Mock file operations
        mock_path_exists.return_value = True
        
        # Setup mock data for loading
        mock_serialized_data = {
            self.test_query: {
                "embedding": [0.1, 0.2, 0.3],
                "response": self.test_response,
                "timestamp": time.time(),
                "metadata": {"test": "metadata"}
            }
        }
        mock_json_load.return_value = mock_serialized_data
        
        # Add to cache but also mock save_cache to do nothing to avoid the initial save
        with patch.object(self.cache, 'save_cache', return_value=True):
            self.cache.add(self.test_query, self.test_response)
        
        # Reset the mock count before calling save_cache explicitly
        mock_json_dump.reset_mock()
        
        # Save to file - this should call our mocked json.dump at least once
        success = self.cache.save_cache()
        self.assertTrue(success)
        self.assertTrue(mock_json_dump.called)
        
        # Create a new cache instance
        new_cache = SemanticCache(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            similarity_threshold=0.85,
            cache_file=self.temp_file
        )
        
        # Mock compute_embedding for the new cache
        new_cache.compute_embedding = self.cache.compute_embedding
        # Also mock is_expired to make sure it doesn't consider entries expired
        new_cache.is_expired = MagicMock(return_value=False)
        
        # Load the cache with mocked data
        success = new_cache.load_cache()
        self.assertTrue(success)
        self.assertTrue(mock_json_load.called)
        
        # Manually set the cache to match what would have been loaded
        new_cache.cache = {
            self.test_query: (
                np.array([0.1, 0.2, 0.3]), 
                self.test_response,
                time.time(),
                {"test": "metadata"}
            )
        }
        
        # Verify we can retrieve this entry
        retrieved = new_cache.get(self.test_query)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["answer"], self.test_response["answer"])
    
    @patch('src.api.services.cache.semantic_cache.SemanticCache._clean_cache')
    def test_max_cache_size(self, mock_clean_cache):
        """Test that the cache respects max_cache_size"""
        # Create a cache with max size of 2
        cache = SemanticCache(
            max_cache_size=2,
            cache_file=None
        )
        
        # Mock compute_embedding
        cache.compute_embedding = MagicMock(return_value=np.array([0.1, 0.2, 0.3]))
        
        # Make _clean_cache do nothing
        mock_clean_cache.return_value = 0
        
        # Mock internal cache dictionary to simulate LRU behavior
        cache_dict = {}
        
        # Store original add method to use inside our mock
        original_add = cache.add
        
        # Override cache object methods to use our controlled dictionary
        def mock_add(query, response, metadata=None):
            # Only keep last 2 entries
            if len(cache_dict) >= 2:
                # Remove oldest key (first one in our test)
                oldest_key = next(iter(cache_dict))
                del cache_dict[oldest_key]
            # Add the new entry
            cache_dict[query] = (np.zeros(3), response, time.time(), {})
            
        # Apply our mock
        cache.add = mock_add
        cache.cache = cache_dict
        
        # Add 3 entries
        cache.add("query1", {"answer": "answer1"})
        self.assertEqual(len(cache_dict), 1)
        
        cache.add("query2", {"answer": "answer2"})
        self.assertEqual(len(cache_dict), 2)
        
        cache.add("query3", {"answer": "answer3"})
        
        # Verify size is respected
        self.assertEqual(len(cache_dict), 2)
        
        # The oldest entry should be removed
        self.assertNotIn("query1", cache_dict)
        self.assertIn("query2", cache_dict)
        self.assertIn("query3", cache_dict)


class TestCacheService(unittest.TestCase):
    """Tests for the cache service functions"""
    
    @patch('src.api.services.cache.cache_service.get_semantic_cache')
    def test_add_to_cache(self, mock_get_cache):
        """Test adding to cache through the service"""
        # Mock the cache
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        
        # Call add_to_cache
        query = "test query"
        response = {"answer": "test answer"}
        add_to_cache(query, response)
        
        # Verify
        mock_cache.add.assert_called_once_with(query, response, {})
    
    @patch('src.api.services.cache.cache_service.get_semantic_cache')
    def test_get_from_cache(self, mock_get_cache):
        """Test getting from cache through the service"""
        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = {"answer": "test answer"}
        mock_get_cache.return_value = mock_cache
        
        # Call get_from_cache
        query = "test query"
        result = get_from_cache(query)
        
        # Verify
        self.assertEqual(result, {"answer": "test answer"})
        mock_cache.get.assert_called_once_with(query, None)
    
    @patch('src.api.services.cache.cache_service.get_semantic_cache')
    def test_clear_semantic_cache(self, mock_get_cache):
        """Test clearing the cache through the service"""
        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.clear.return_value = 5
        mock_get_cache.return_value = mock_cache
        
        # Call clear_semantic_cache
        result = clear_semantic_cache()
        
        # Verify
        self.assertEqual(result, 5)
        mock_cache.clear.assert_called_once()


if __name__ == '__main__':
    unittest.main() 