#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "kevin_venv" ]; then
    echo "Virtual environment 'kevin_venv' not found. Creating it..."
    python3 -m venv kevin_venv
fi

# Activate the virtual environment
source kevin_venv/bin/activate

# Print confirmation
echo "Virtual environment activated. Current Python path:"
which python

# Print installed packages
echo -e "\nInstalled packages:"
pip list 