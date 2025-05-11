#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is required but not installed.${NC}"
        exit 1
    fi
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

# Function to fix Docker connection issues
fix_docker_connection() {
    echo -e "${YELLOW}Fixing Docker connection...${NC}"
    
    # Unset potentially interfering environment variable
    unset DOCKER_HOST
    
    # Set Docker context to ensure correct socket connection
    echo -e "${YELLOW}Setting Docker context...${NC}"
    docker context use default > /dev/null 2>&1
    
    # Verify that Docker is running and accessible
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Cannot connect to Docker daemon.${NC}"
        echo -e "${YELLOW}Please make sure Docker Desktop is running.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Docker connection established.${NC}"
    return 0
}

# Function to start MongoDB
start_mongodb() {
    echo -e "${YELLOW}Starting MongoDB container...${NC}"
    
    # First fix any Docker connection issues
    fix_docker_connection || return 1
    
    # Check if MongoDB is already running
    if docker ps | grep -q "kevin-ui-mongodb"; then
        echo -e "${GREEN}MongoDB container is already running.${NC}"
        return 0
    fi
    
    # Check for stale container
    if docker ps -a | grep -q "kevin-ui-mongodb"; then
        echo -e "${YELLOW}Removing stale MongoDB container...${NC}"
        docker rm kevin-ui-mongodb > /dev/null 2>&1
    fi
    
    # Start MongoDB container
    cd "$ROOT_DIR/ui/db"
    docker-compose up -d
    cd "$ROOT_DIR"
    
    # Verify container is running
    if docker ps | grep -q "kevin-ui-mongodb"; then
        echo -e "${GREEN}✓ MongoDB container started successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to start MongoDB container${NC}"
        return 1
    fi
}

# Check required commands
check_command node
check_command npm
check_command docker
check_command docker-compose

# Start MongoDB if not already running
if ! nc -z localhost 27018 &> /dev/null; then
    echo -e "${YELLOW}Starting MongoDB...${NC}"
    start_mongodb || {
        echo -e "${RED}Failed to start MongoDB. Make sure Docker Desktop is running.${NC}"
        exit 1
    }
fi

# Wait for MongoDB to be ready
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
    
    # Use start-kevin.sh for API
    cd "$ROOT_DIR"
    ./start-kevin.sh -a start -s api
fi

# Wait for FastAPI to be ready
wait_for_service localhost 8000 30 || exit 1

# Start Next.js frontend
echo -e "${GREEN}Starting Next.js frontend...${NC}"
cd "$SCRIPT_DIR" || { echo -e "${RED}Frontend directory not found${NC}"; exit 1; }
npm install
npm run dev &

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