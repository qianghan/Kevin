#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$SCRIPT_DIR"

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is required but not installed.${NC}"
        exit 1
    fi
}

# Function to check if a port is in use
check_port() {
    if lsof -i :$1 &> /dev/null; then
        echo -e "${YELLOW}Port $1 is already in use.${NC}"
        return 1
    fi
    return 0
}

# Function to wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local max_attempts=$3
    local attempt=1

    echo -e "${YELLOW}Waiting for $host:$port to be ready...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port &> /dev/null; then
            echo -e "${GREEN}$host:$port is ready!${NC}"
            return 0
        fi
        echo -e "${YELLOW}Attempt $attempt/$max_attempts: Waiting for $host:$port...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    echo -e "${RED}Failed to connect to $host:$port after $max_attempts attempts${NC}"
    return 1
}

# Check required commands
check_command node
check_command npm
check_command docker
check_command docker-compose

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}Docker daemon is not running. Attempting to start Docker...${NC}"
    UNAME_OUT="$(uname -s)"
    case "${UNAME_OUT}" in
        Darwin*)
            # macOS
            if open -a Docker &> /dev/null; then
                echo -e "${YELLOW}Starting Docker Desktop...${NC}"
            else
                echo -e "${RED}Failed to start Docker Desktop automatically. Please start it from Applications folder.${NC}"
                exit 1
            fi
            ;;
        Linux*)
            # Linux
            if sudo systemctl start docker &> /dev/null; then
                echo -e "${YELLOW}Starting Docker service...${NC}"
            else
                echo -e "${RED}Failed to start Docker service automatically. Please run 'sudo systemctl start docker' manually.${NC}"
                exit 1
            fi
            ;;
        *)
            echo -e "${RED}Unsupported OS. Please start Docker manually and try again.${NC}"
            exit 1
            ;;
    esac
    # Wait for Docker to be ready
    echo -e "${YELLOW}Waiting for Docker daemon to be ready...${NC}"
    MAX_ATTEMPTS=30
    ATTEMPT=1
    while ! docker info &> /dev/null; do
        if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
            echo -e "${RED}Docker daemon did not start after $MAX_ATTEMPTS attempts. Please check Docker and try again.${NC}"
            exit 1
        fi
        echo -e "${YELLOW}Attempt $ATTEMPT/$MAX_ATTEMPTS: Waiting for Docker...${NC}"
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    done
    echo -e "${GREEN}Docker daemon is running!${NC}"
fi

# Start services using start-kevin.sh
echo -e "${GREEN}Starting services using start-kevin.sh...${NC}"
cd "$ROOT_DIR" || { echo -e "${RED}Root directory not found${NC}"; exit 1; }

# Start MongoDB if not running
if ! lsof -i :27018 &> /dev/null; then
    echo -e "${YELLOW}Starting MongoDB using Docker...${NC}"
    echo -e "${YELLOW}Starting MongoDB container...${NC}"
    
    if ./start-kevin.sh -a start -s db; then
        echo -e "${GREEN}MongoDB container started successfully.${NC}"
    else
        echo -e "${RED}Failed to start MongoDB container.${NC}"
        echo -e "${RED}Please check if Docker is properly configured and try again.${NC}"
        exit 1
    fi
fi

# Wait for MongoDB to be ready
echo -e "${YELLOW}Done!${NC}"
wait_for_service localhost 27018 30 || exit 1

# Start FastAPI backend if not running
if ! ps aux | grep -v grep | grep -q "python -m src.api.main"; then
    echo -e "${YELLOW}Starting FastAPI backend...${NC}"
    
    # Look for Python executable in different places
    PYTHON_CMD=""
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    fi
    
    if [ -z "$PYTHON_CMD" ]; then
        echo -e "${RED}Python not found. Please install Python 3.${NC}"
        exit 1
    fi
    
    # Check if we should use start-kevin.sh or start directly
    if [ -f "$ROOT_DIR/start-kevin.sh" ]; then
        ./start-kevin.sh -a start -s api
    else
        # Fallback to direct launch if start-kevin.sh isn't working
        cd "$ROOT_DIR" && $PYTHON_CMD -m src.api.main &
    fi
fi

# Wait for FastAPI to be ready
wait_for_service localhost 8000 30 || exit 1

# Start Next.js frontend
echo -e "${GREEN}Starting Next.js frontend...${NC}"

# Always start frontend from the ui directory with correct dependencies
cd "$ROOT_DIR/ui" || { echo -e "${RED}UI directory not found${NC}"; exit 1; }
echo "Installing frontend dependencies..."
npm install --legacy-peer-deps
echo "Starting frontend dev server..."
npx next dev &

# Wait for Next.js to be ready
wait_for_service localhost 3000 30 || exit 1

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Shutting down services...${NC}"
    pkill -f "npm run dev"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}All services are running!${NC}"
echo -e "${GREEN}Access the application at:${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}Backend: http://localhost:8000${NC}"

# Keep the script running
while true; do
    sleep 1
done 