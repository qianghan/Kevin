"""
Web API command for Kevin CLI.

This module provides commands for running the Streamlit web interface
that communicates with the Kevin API instead of directly using core modules.
"""

import os
import sys
import click
import subprocess
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

@click.command("webapi")
@click.option("--host", default="localhost", help="Host for the Streamlit server")
@click.option("--port", default=8501, help="Port for the Streamlit server")
@click.option("--api-url", default="http://localhost:8000", help="URL of the Kevin API")
def webapi_command(host: str, port: int, api_url: str):
    """
    Run the Kevin web interface using the API backend.
    
    This starts a Streamlit server that communicates with the FastAPI backend
    instead of directly using the core modules. The API server must be running
    separately using 'kevin --mode api'.
    """
    try:
        logger.info(f"Starting Kevin web UI on {host}:{port} using API at {api_url}")
        logger.info(f"Note: Make sure the API server is running with 'kevin --mode api'")
        
        # Find the web/api_app.py path
        current_file = Path(__file__).resolve()
        web_app_path = current_file.parent.parent / "web" / "api_app.py"
        
        if not web_app_path.exists():
            logger.error(f"Web UI app not found at {web_app_path}")
            sys.exit(1)
        
        # Set environment variables for the process
        env = os.environ.copy()
        env["KEVIN_API_URL"] = api_url
        
        # Build the Streamlit command
        cmd = [
            "streamlit", "run", str(web_app_path),
            "--server.address", host,
            "--server.port", str(port),
            "--browser.serverAddress", host,
            "--browser.serverPort", str(port),
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run Streamlit with the API URL set
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        logger.info("Web UI stopped by user")
    except Exception as e:
        logger.error(f"Error starting web UI: {e}")
        sys.exit(1) 