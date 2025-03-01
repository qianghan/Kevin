#!/bin/bash

echo "Installing dependencies for enhanced web scraper using spider-py..."

# Check if we're in a virtual environment, activate if it exists
if [ -d "kevin" ]; then
    echo "Virtual environment 'kevin' found, activating..."
    source kevin/bin/activate
    echo "Virtual environment activated."
else
    echo "Warning: No virtual environment found, installing packages globally."
fi

# Install spider-py and other required packages
echo "Installing required packages..."
pip install spider-py bs4 tqdm pyyaml langchain requests

# Check if spider-py was installed correctly
if python -c "import spider" 2>/dev/null; then
    echo "✅ spider-py successfully installed"
else
    echo "❌ Failed to install spider-py. Please check for errors above."
    exit 1
fi

echo "Done! You can now run the enhanced web scraper."
echo "To test the scraper, run: python test_scraper.py" 