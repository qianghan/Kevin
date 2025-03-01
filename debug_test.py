#!/usr/bin/env python3
"""
Simple debug script to verify that logging and command execution work properly.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime

def setup_basic_logging():
    """Set up very basic logging with direct console output."""
    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Test the logger
    logging.info("Basic logging test - should appear in console")
    
    return logging.getLogger()

def test_file_paths():
    """Test if critical file paths exist."""
    logger = logging.getLogger()
    
    # Check current directory
    current_dir = os.getcwd()
    logger.info(f"Current working directory: {current_dir}")
    
    # Check if src/main.py exists
    main_path = Path("src/main.py")
    if main_path.exists():
        logger.info(f"✅ Found main.py at {main_path}")
    else:
        logger.error(f"❌ Could not find {main_path}. Wrong working directory?")
        
        # Try to locate it by going up directories
        for parent in Path(".").resolve().parents:
            potential_path = parent / "src" / "main.py"
            if potential_path.exists():
                logger.info(f"Found main.py at {potential_path}")
                logger.info(f"Try running from: {parent}")
                break
    
    # Check if directories exist or can be created
    data_dir = Path("data/backup")
    if not data_dir.exists():
        logger.info(f"Creating directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    test_dir = Path("test_logs")
    if not test_dir.exists():
        logger.info(f"Creating directory: {test_dir}")
        test_dir.mkdir(parents=True, exist_ok=True)

def test_command_execution():
    """Test if running a basic command works."""
    logger = logging.getLogger()
    
    logger.info("Testing basic command execution...")
    
    try:
        # Try running a simple Python command
        cmd = [sys.executable, "-c", "print('Command execution works!')"]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Command executed successfully!")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"❌ Command failed with exit code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
    
    except Exception as e:
        logger.error(f"❌ Exception during command execution: {e}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """Run basic diagnostic tests."""
    print("Starting diagnostic tests...")  # Direct print for immediate feedback
    
    # Set up logging
    logger = setup_basic_logging()
    
    # Print a clear separation
    logger.info("=" * 50)
    logger.info("DIAGNOSTIC TEST STARTED")
    logger.info("=" * 50)
    
    # Run tests
    test_file_paths()
    test_command_execution()
    
    # Try importing required modules
    logger.info("Testing imports...")
    try:
        import json
        import argparse
        logger.info("✅ Basic imports successful")
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
    
    logger.info("=" * 50)
    logger.info("DIAGNOSTIC TEST COMPLETED")
    logger.info("=" * 50)
    
    # Direct output for good measure
    print("Diagnostic tests completed! Check logs for details.")

if __name__ == "__main__":
    main() 