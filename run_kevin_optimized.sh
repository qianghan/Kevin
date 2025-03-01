#!/bin/bash

# Check for help parameter
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: ./run_kevin_optimized.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-prep, -s    Skip training steps and start web interface directly"
    echo "  --help, -h         Show this help message"
    exit 0
fi

# Check for skip parameter
SKIP_PREP=false
if [[ "$1" == "--skip-prep" || "$1" == "-s" ]]; then
    SKIP_PREP=true
fi

echo "============================================="
echo "Kevin University Information System - Optimized"
echo "============================================="
source kevin/bin/activate
echo ""

if [ "$SKIP_PREP" = false ]; then
    echo "Step 1: Training Vector Database (includes scraping)..."
    echo "This will scrape university websites and update the vector database"
    kevin --mode train
    echo ""
else
    echo "Skipping training step as requested..."
    echo ""
fi

echo "Step 2: Starting Web Interface..."
echo "Now you can access the web interface in your browser"

# Set environment variables to avoid PyTorch/Streamlit conflicts
export TORCH_WARN_ONCE=1
export USE_DEEPSEEK_ONLY=1
export PYTHONPATH=$PYTHONPATH:$(pwd)
# Disable asyncio debug to prevent event loop errors
export PYTHONDEVMODE=0
export PYTHONASYNCIODEBUG=0

# Use env to ensure variables are properly isolated for the Streamlit process
PYTHONPATH=$PYTHONPATH:$(pwd) TORCH_WARN_ONCE=1 USE_DEEPSEEK_ONLY=1 PYTHONDEVMODE=0 PYTHONASYNCIODEBUG=0 streamlit run src/web/app.py --server.port=8502 --server.fileWatcherType=none --server.runOnSave=false
