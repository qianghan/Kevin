#!/usr/bin/env python3
"""
Launcher script for Kevin web interface that handles PyTorch/Streamlit compatibility.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the Kevin web interface."""
    # Set environment variables to avoid PyTorch/Streamlit conflicts
    os.environ['TORCH_WARN_ONCE'] = '1'
    os.environ['USE_DEEPSEEK_ONLY'] = '1'
    
    # Get the path to the app.py file
    current_dir = Path(__file__).parent
    app_path = current_dir / "src" / "web" / "app.py"
    
    # Ensure the path exists
    if not app_path.exists():
        print(f"Error: Could not find {app_path}")
        sys.exit(1)
    
    print("Starting Kevin web interface...")
    
    # Run Streamlit with the app.py file
    try:
        subprocess.run(
            ["streamlit", "run", str(app_path), "--server.port=8502"],
            check=True,
            env=os.environ
        )
    except KeyboardInterrupt:
        print("\nShutting down Kevin web interface...")
    except Exception as e:
        print(f"Error running Kevin web interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 