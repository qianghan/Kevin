"""
Main FastAPI application for Kevin API.

This module creates the FastAPI application and configures routes and middleware.
"""

import time
import os
import logging
from typing import Dict, Any, Optional
import yaml
from pathlib import Path
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from .routers import chat, search, admin, documents
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.logger import get_logger

logger = get_logger(__name__)

def create_app() -> FastAPI:
    """Create a FastAPI application with all routes configured"""
    app = FastAPI(
        title="Kevin API",
        description="API for Kevin, a university-focused AI assistant",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
    app.include_router(search.router, prefix="/api/search", tags=["search"])

    # Exception handling middleware
    @app.middleware("http")
    async def exception_handling(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": f"An error occurred: {str(e)}"},
            )

    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # Root endpoint
    @app.get("/", tags=["utility"])
    async def root() -> Dict[str, Any]:
        return {
            "name": "Kevin API",
            "version": "1.0.0",
            "description": "API for Kevin, a university-focused AI assistant",
            "docs_url": "/docs"
        }

    # Health check endpoint
    @app.get("/api/health", tags=["utility"])
    async def health_check() -> Dict[str, Any]:
        return {
            "status": "ok",
            "timestamp": time.time()
        }
        
    # Custom OpenAPI schema
    def custom_openapi():
        openapi_path = Path(__file__).parent / "openapi.yaml"
        if openapi_path.exists():
            try:
                with open(openapi_path, "r") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading custom OpenAPI schema: {str(e)}", exc_info=True)
                
        # Fallback to default schema if YAML file not found or has errors
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema
        
    app.openapi = custom_openapi
    
    return app

# Create the FastAPI application
app = create_app()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request details and timing."""
    start_time = time.time()
    
    # Generate a request ID
    request_id = os.urandom(8).hex()
    
    # Log the request
    logger.info(f"[{request_id}] Request: {request.method} {request.url.path}")
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Calculate and log the duration
        duration = time.time() - start_time
        logger.info(f"[{request_id}] Response: {response.status_code} ({duration:.2f}s)")
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        return response
    except Exception as e:
        # Log and handle exceptions
        logger.error(f"[{request_id}] Error: {str(e)}")
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Return a JSON error response
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
            headers={"X-Process-Time": str(duration)},
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": time.time()}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Kevin API",
        "version": app.version,
        "description": app.description,
        "docs_url": "/docs",
    } 