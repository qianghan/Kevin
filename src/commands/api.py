"""
API command for Kevin CLI.

This module provides commands for running the Kevin API server.
"""

import os
import sys
import uvicorn
import click

from src.utils.logger import get_logger

logger = get_logger(__name__)


@click.command("api")
@click.option("--host", default="127.0.0.1", help="Host to bind the server to")
@click.option("--port", default=8000, help="Port to bind the server to")
@click.option("--reload/--no-reload", default=False, help="Enable/disable auto-reload")
@click.option("--debug/--no-debug", default=False, help="Enable/disable debug mode")
def api_command(host: str, port: int, reload: bool, debug: bool):
    """
    Run the Kevin API server.
    
    This starts a FastAPI server that provides REST API access to Kevin's capabilities.
    Documentation is available at http://{host}:{port}/docs when the server is running.
    """
    try:
        # Configure logging level based on debug flag
        if debug:
            import logging
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        
        logger.info(f"Starting Kevin API server on {host}:{port}")
        logger.info(f"API documentation will be available at http://{host}:{port}/docs")
        
        # Configure server
        config = {
            "app": "src.api.main:app",
            "host": host,
            "port": port,
            "reload": reload,
            "workers": 1,
            "log_level": "debug" if debug else "info"
        }
        
        # Start server
        uvicorn.run(**config)
    except Exception as e:
        logger.error(f"Error starting API server: {e}", exc_info=True)
        sys.exit(1) 