"""
Unit tests for the API rate limiter.

This test verifies that the rate limiter functions correctly.
"""

import unittest
import asyncio
import time
from fastapi import Request, HTTPException
from app.backend.api.middleware import RateLimiter


class MockRequest:
    """Mock implementation of a FastAPI Request object."""
    
    def __init__(self, client_ip="127.0.0.1", headers=None):
        """Initialize the mock request with client IP and headers."""
        self.client = type('obj', (object,), {
            'host': client_ip
        })
        self.headers = headers or {}


class TestRateLimiter(unittest.TestCase):
    """Test the RateLimiter class."""
    
    def setUp(self):
        """Set up the test case."""
        # Create a rate limiter with a low limit for testing
        self.rate_limiter = RateLimiter(
            rate=3,        # 3 requests per window
            per=5,         # 5 second window
            burst=4,       # Burst up to 4
            trusted_ips=["192.168.1.1"]  # Trusted IP
        )
    
    def test_new_client_allowed(self):
        """Test that a new client is initially allowed."""
        request = MockRequest(client_ip="10.0.0.1")
        self.assertTrue(self.rate_limiter.is_allowed(request))
    
    def test_rate_limiting(self):
        """Test that requests are limited after exceeding the limit."""
        request = MockRequest(client_ip="10.0.0.2")
        
        # First few requests should be allowed (up to burst limit)
        for _ in range(4):
            self.assertTrue(self.rate_limiter.is_allowed(request))
        
        # Next request should be denied
        self.assertFalse(self.rate_limiter.is_allowed(request))
    
    def test_token_refill(self):
        """Test that tokens are refilled over time."""
        request = MockRequest(client_ip="10.0.0.3")
        
        # Use up all tokens
        for _ in range(4):
            self.assertTrue(self.rate_limiter.is_allowed(request))
        
        # Next request should be denied
        self.assertFalse(self.rate_limiter.is_allowed(request))
        
        # Wait for tokens to refill (at least 1 token, which takes ~1.67 seconds)
        time.sleep(2)
        
        # Should be allowed again
        self.assertTrue(self.rate_limiter.is_allowed(request))
    
    def test_trusted_ip_bypass(self):
        """Test that trusted IPs bypass rate limiting."""
        request = MockRequest(client_ip="192.168.1.1")  # Trusted IP
        
        # Make many requests, more than the limit
        for _ in range(10):
            self.assertTrue(self.rate_limiter.is_allowed(request))
    
    def test_api_key_identification(self):
        """Test that clients are identified by API key when available."""
        # Two "different" clients with the same API key
        request1 = MockRequest(
            client_ip="10.0.0.4",
            headers={"X-API-Key": "test-key-1"}
        )
        request2 = MockRequest(
            client_ip="10.0.0.5",  # Different IP
            headers={"X-API-Key": "test-key-1"}  # Same API key
        )
        
        # Use up all tokens for the first client
        for _ in range(4):
            self.assertTrue(self.rate_limiter.is_allowed(request1))
        
        # Next request should be denied, even from a different IP
        # because they share the same API key
        self.assertFalse(self.rate_limiter.is_allowed(request2))
    
    def test_process_request_exception(self):
        """Test that process_request raises HTTPException when rate limited."""
        request = MockRequest(client_ip="10.0.0.6")
        
        # Use up all tokens
        for _ in range(4):
            self.rate_limiter.is_allowed(request)
        
        # Define a function to run the coroutine and check for exceptions
        async def run_test():
            with self.assertRaises(HTTPException) as context:
                await self.rate_limiter.process_request(request)
            
            # Check the exception details
            exception = context.exception
            self.assertEqual(exception.status_code, 429)
            self.assertIn("Rate limit exceeded", exception.detail)
        
        # Run the coroutine
        if hasattr(asyncio, 'run'):
            # Python 3.7+
            asyncio.run(run_test())
        else:
            # Python 3.6 or earlier
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main() 