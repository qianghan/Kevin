"""
API middleware for request/response logging and error handling.

This module provides middleware components for FastAPI applications
to handle cross-cutting concerns like logging and error handling.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
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