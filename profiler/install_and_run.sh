#!/bin/bash
# Script to install and run the profiler service independently

# Exit on error
set -e

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install the package in development mode
echo "Installing profiler package..."
pip install -e .

# Install additional dependencies
echo "Installing dependencies..."
pip install -r requirements.txt || pip install fastapi uvicorn pyyaml pytest httpx chromadb

# Run the service
echo "Starting profiler service..."
python run.py 