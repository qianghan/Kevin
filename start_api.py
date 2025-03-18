#!/usr/bin/env python3
"""
Script to start the Kevin API server with the correct Python path.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

# Import and run uvicorn
if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8001"))
    
    print(f"Starting API server on {host}:{port}")
    uvicorn.run("src.api.app:app", host=host, port=port, reload=True) 