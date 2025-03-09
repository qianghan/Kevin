#!/usr/bin/env python3
"""
FastAPI application for Kevin.
This provides a RESTful and streaming API interface to all Kevin's capabilities.
"""

import os
import sys
import argparse
from typing import Optional
from pathlib import Path

# Add the project root to the Python path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.append(str(project_root))

# Import the application factory
from src.api.app import create_app
from src.utils.logger import get_logger

# Setup logging
logger = get_logger(__name__)

# Create FastAPI application
app = create_app()

def main():
    """
    Run the FastAPI application with uvicorn.
    Parse command line arguments for host, port, and other options.
    """
    parser = argparse.ArgumentParser(description="Run Kevin API server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind server to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on file changes")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Configure logging level based on debug flag
    if args.debug:
        import logging
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Log the server configuration
    logger.info(f"Starting Kevin API server on {args.host}:{args.port}")
    logger.info(f"Auto-reload: {args.reload}")
    
    # Import uvicorn here to avoid affecting module imports
    import uvicorn
    
    # Run the FastAPI application with uvicorn
    uvicorn.run(
        "src.api.main:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )

if __name__ == "__main__":
    main() 