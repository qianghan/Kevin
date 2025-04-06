#!/usr/bin/env python
"""
Profiler application entry point.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.backend.utils.config_manager import ConfigManager

def main():
    """Run the profiler application."""
    # Load configuration
    config = ConfigManager()
    
    # Get API configuration
    api_config = config.get_all().get("api", {})
    host = api_config.get("host", "127.0.0.1")
    port = api_config.get("port", 8000)
    
    # Start the API server
    uvicorn.run(
        "app.backend.api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 