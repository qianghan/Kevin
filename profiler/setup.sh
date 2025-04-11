#!/bin/bash
# Student Profiler Setup Script
# Creates virtual environment and installs dependencies

set -e  # Exit on error

VENV_NAME="profiler"
REQUIREMENTS_FILE="requirements.txt"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Student Profiler Setup ===${NC}"

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_VERSION_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_VERSION_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_VERSION_MAJOR" -lt 3 ] || ([ "$PYTHON_VERSION_MAJOR" -eq 3 ] && [ "$PYTHON_VERSION_MINOR" -lt 8 ]); then
    echo -e "${RED}Error: Python 3.8 or higher is required. Found $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}Python version $PYTHON_VERSION detected.${NC}"

# Create requirements.txt if it doesn't exist
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${YELLOW}Creating requirements.txt file...${NC}"
    cat > "$REQUIREMENTS_FILE" << EOF
# API Framework
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
websockets>=11.0.3
pydantic>=2.0.0

# HTTP Client
httpx>=0.24.1

# Configuration
pyyaml>=6.0

# Database
chromadb>=0.4.0
sentence-transformers>=2.2.2

# LangGraph
langgraph>=0.0.17

# Document Processing
PyPDF2>=3.0.0
python-docx>=0.8.11
python-multipart>=0.0.6

# Utilities
python-dotenv>=1.0.0
tenacity>=8.2.2
colorlog>=6.7.0

# Testing
pytest>=7.3.1
pytest-asyncio>=0.21.0
EOF
    echo -e "${GREEN}Created requirements.txt${NC}"
fi

# Check if virtual environment exists
if [ -d "$VENV_NAME" ]; then
    echo -e "${YELLOW}Virtual environment '$VENV_NAME' already exists.${NC}"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf "$VENV_NAME"
    else
        echo -e "${YELLOW}Using existing virtual environment.${NC}"
        source "$VENV_NAME/bin/activate"
        echo -e "${GREEN}Virtual environment activated.${NC}"
        
        echo -e "${YELLOW}Updating dependencies...${NC}"
        pip install --upgrade pip
        pip install -r "$REQUIREMENTS_FILE"
        echo -e "${GREEN}Dependencies updated.${NC}"
        
        echo -e "${GREEN}Setup complete! The virtual environment is activated.${NC}"
        echo -e "To deactivate the virtual environment, run: ${YELLOW}deactivate${NC}"
        exit 0
    fi
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment '$VENV_NAME'...${NC}"
python3 -m venv "$VENV_NAME"
echo -e "${GREEN}Virtual environment created.${NC}"

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_NAME/bin/activate"
echo -e "${GREEN}Virtual environment activated.${NC}"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r "$REQUIREMENTS_FILE"
echo -e "${GREEN}Dependencies installed.${NC}"

# Create subdirectories if they don't exist
mkdir -p profiler/app/backend/logs

# Finish
echo -e "${GREEN}Setup complete! The virtual environment is now activated.${NC}"
echo -e "To deactivate the virtual environment, run: ${YELLOW}deactivate${NC}"
echo -e "To activate the virtual environment later, run: ${YELLOW}source $VENV_NAME/bin/activate${NC}"
echo -e "To run the profiler, use: ${YELLOW}python profiler.py <command>${NC}" 