"""
Web API command for Kevin CLI.

This module provides commands for running the Streamlit web interface
that communicates with the Kevin API instead of directly using core modules.
"""

import os
import sys
import click
import subprocess
import socket
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port: int, max_attempts: int = 10) -> Optional[int]:
    """Find an available port starting from start_port."""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    return None

@click.command("webapi")
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=8501, help="Port to bind the server to")
@click.option("--api-url", default="http://localhost:8000", help="URL of the API server")
def webapi_command(host: str, port: int, api_url: str):
    """Run the Kevin web UI with API backend."""
    
    # Check if the specified port is in use and find an available one if needed
    if is_port_in_use(port):
        logger.warning(f"Port {port} is already in use.")
        new_port = find_available_port(port + 1)
        if new_port:
            logger.info(f"Using available port {new_port} instead.")
            port = new_port
        else:
            logger.error("Could not find an available port. Please free up port resources or specify a different port.")
            sys.exit(1)
    
    logger.info(f"Starting Kevin web UI on {host}:{port} using API at {api_url}")
    logger.info("Note: Make sure the API server is running with 'kevin --mode api'")
    
    # Get the path to the web app
    web_app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "api_app.py")
    
    # Check if the file exists
    if not os.path.exists(web_app_path):
        logger.error(f"Web app file not found: {web_app_path}")
        sys.exit(1)
    
    # Run streamlit with the correct arguments
    cmd = [
        "streamlit", "run", web_app_path,
        f"--server.address", host,
        f"--server.port", str(port),
        f"--browser.serverAddress", host,
        f"--browser.serverPort", str(port)
    ]
    
    # Set environment variable for API URL
    os.environ["KEVIN_API_URL"] = api_url
    
    logger.info(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd) 