"""
API middleware for request/response logging and error handling.

This module provides middleware components for FastAPI applications
to handle cross-cutting concerns like logging and error handling.
"""

import time
import uuid
from typing import Callable, Dict, Tuple, List, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from ..utils.logging import get_logger
from ..utils.errors import ProfilerError

logger = get_logger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging API requests and responses.
    
    This middleware logs information about incoming requests and outgoing
    responses, including timing information and status codes.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, logging details before and after.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware or endpoint
            
        Returns:
            The response from the endpoint
        """
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state for use in endpoints
        request.state.request_id = request_id
        
        # Log request details
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": client_host,
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Track timing
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response details
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "processing_time": f"{process_time:.3f}s"
                }
            )
            
            # Add timing header to response
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate processing time even for errors
            process_time = time.time() - start_time
            
            # Log error details
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "processing_time": f"{process_time:.3f}s",
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            # Re-raise the exception for the exception handler to process
            raise

class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging unhandled exceptions.
    
    This middleware catches and logs unhandled exceptions that may occur
    during request processing, ensuring they are properly recorded.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, catching and logging any unhandled exceptions.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware or endpoint
            
        Returns:
            The response from the endpoint
        """
        try:
            # Process the request
            return await call_next(request)
            
        except ProfilerError as e:
            # Log application-specific errors
            logger.error(
                f"Application error: {e.code} - {e.message}",
                extra={
                    "error_code": e.code,
                    "error_details": e.details,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            # Convert to HTTP exception and let FastAPI handle it
            raise e.to_http_exception()
            
        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unhandled exception: {str(e)}",
                extra={
                    "error_type": type(e).__name__,
                    "path": request.url.path,
                    "method": request.method
                },
                exc_info=True
            )
            # Re-raise for FastAPI's exception handlers
            raise 

class RateLimiter:
    """
    Rate limiter middleware for the API.
    
    This class implements a simple token bucket algorithm for rate limiting.
    It limits the number of requests that can be made by a client within
    a specific time window.
    """
    
    def __init__(
        self,
        rate: int = 10,
        per: int = 60,
        burst: int = 15,
        trusted_ips: Optional[List[str]] = None
    ):
        """
        Initialize the rate limiter.
        
        Args:
            rate: The number of requests allowed per time window
            per: The time window in seconds
            burst: The maximum burst size (tokens that can be accumulated)
            trusted_ips: List of IP addresses that bypass rate limiting
        """
        self.rate = rate  # requests per window
        self.per = per  # window size in seconds
        self.burst = burst  # max token bucket size
        self.buckets: Dict[str, Tuple[float, float]] = {}  # client_id -> (tokens, last_refill)
        self.trusted_ips = trusted_ips or []
    
    def get_client_id(self, request: Request) -> str:
        """
        Get a unique identifier for the client making the request.
        
        Args:
            request: The incoming request
            
        Returns:
            A unique identifier for the client (e.g., IP address or API key)
        """
        # Try to get API key from header first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"
        
        # Fall back to client IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def refill_tokens(self, client_id: str) -> Tuple[float, float]:
        """
        Refill the token bucket for a client based on elapsed time.
        
        Args:
            client_id: The unique identifier for the client
            
        Returns:
            A tuple of (tokens, last_refill)
        """
        now = time.time()
        
        # Get current bucket or create a new one
        if client_id in self.buckets:
            tokens, last_refill = self.buckets[client_id]
        else:
            # New client starts with a full bucket
            return (float(self.burst), now)
        
        # Calculate token refill based on time elapsed
        elapsed = now - last_refill
        refill = elapsed * (self.rate / self.per)
        tokens = min(float(self.burst), tokens + refill)
        
        return (tokens, now)
    
    def is_allowed(self, request: Request) -> bool:
        """
        Check if a request is allowed based on rate limits.
        
        Args:
            request: The incoming request
            
        Returns:
            True if the request is allowed, False otherwise
        """
        # Check if client is in trusted IPs
        client_ip = request.client.host if request.client else "unknown"
        if client_ip in self.trusted_ips:
            return True
        
        # Get client identifier
        client_id = self.get_client_id(request)
        
        # Refill tokens based on time elapsed
        tokens, last_refill = self.refill_tokens(client_id)
        
        # Check if request can be allowed
        if tokens >= 1.0:
            # Consume a token
            tokens -= 1.0
            self.buckets[client_id] = (tokens, last_refill)
            return True
        else:
            # No tokens available
            return False
    
    async def process_request(self, request: Request) -> None:
        """
        Process an incoming request and apply rate limiting.
        
        Args:
            request: The incoming request
            
        Raises:
            HTTPException: If the request exceeds the rate limit
        """
        if not self.is_allowed(request):
            retry_after = int(self.per / self.rate)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )


# Global rate limiter instance
rate_limiter = RateLimiter(
    rate=30,       # 30 requests
    per=60,        # per minute
    burst=50,      # burst up to 50
    trusted_ips=["127.0.0.1", "::1"]  # localhost IPs bypass rate limiting
) 