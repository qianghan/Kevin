#!/bin/bash

# Define color codes for prettier output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"

# Function to check if MongoDB is running
check_mongodb() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        return 1
    }
    
    if docker ps | grep -q "kevin-ui-mongodb"; then
        echo -e "${GREEN}✓ MongoDB container is already running${NC}"
        return 0
    fi
    return 1
}

# Function to start MongoDB
start_mongodb() {
    echo -e "${YELLOW}Starting MongoDB container...${NC}"
    if ! check_mongodb; then
        cd ../ui/db
        docker-compose up -d
        cd ../../frontend
        
        # Wait for MongoDB to be ready
        echo -e "${YELLOW}Waiting for MongoDB to be ready...${NC}"
        sleep 5
        
        if check_mongodb; then
            echo -e "${GREEN}✓ MongoDB container started successfully${NC}"
        else
            echo -e "${RED}✗ Failed to start MongoDB container${NC}"
            exit 1
        fi
    fi
}

# Function to start the frontend application
start_frontend() {
    echo -e "${YELLOW}Starting frontend application...${NC}"
    local FRONTEND_PID_FILE="$LOG_DIR/frontend.pid"
    local FRONTEND_LOG_FILE="$LOG_DIR/frontend.log"
    
    # Check if frontend is already running
    if [ -f "$FRONTEND_PID_FILE" ] && ps -p $(cat "$FRONTEND_PID_FILE") > /dev/null; then
        echo -e "${YELLOW}Frontend is already running with PID $(cat "$FRONTEND_PID_FILE")${NC}"
        return 0
    fi
    
    # Start frontend in development mode
    echo -e "${BLUE}Frontend logs will be available at: $FRONTEND_LOG_FILE${NC}"
    (echo "Starting frontend at $(date)" >> "$FRONTEND_LOG_FILE"; \
     npm run dev >> "$FRONTEND_LOG_FILE" 2>&1) &
    
    # Store the process ID
    echo $! > "$FRONTEND_PID_FILE"
    echo -e "${GREEN}✓ Frontend started with PID $(cat "$FRONTEND_PID_FILE")${NC}"
}

# Function to start the chat service
start_chat_service() {
    echo -e "${YELLOW}Starting chat service...${NC}"
    local CHAT_PID_FILE="$LOG_DIR/chat.pid"
    local CHAT_LOG_FILE="$LOG_DIR/chat.log"
    
    # Check if chat service is already running
    if [ -f "$CHAT_PID_FILE" ] && ps -p $(cat "$CHAT_PID_FILE") > /dev/null; then
        echo -e "${YELLOW}Chat service is already running with PID $(cat "$CHAT_PID_FILE")${NC}"
        return 0
    fi
    
    # Start chat service
    echo -e "${BLUE}Chat service logs will be available at: $CHAT_LOG_FILE${NC}"
    (cd .. && \
     source kevin_venv/bin/activate && \
     echo "Starting chat service at $(date)" >> "frontend/$CHAT_LOG_FILE" && \
     PYTHONPATH=$(pwd) python -m src.api.main >> "frontend/$CHAT_LOG_FILE" 2>&1) &
    
    # Store the process ID
    echo $! > "$CHAT_PID_FILE"
    echo -e "${GREEN}✓ Chat service started with PID $(cat "$CHAT_PID_FILE")${NC}"
}

# Function to stop all services
stop_services() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    
    # Stop frontend
    if [ -f "$LOG_DIR/frontend.pid" ]; then
        kill $(cat "$LOG_DIR/frontend.pid") 2>/dev/null
        rm "$LOG_DIR/frontend.pid"
    fi
    
    # Stop chat service
    if [ -f "$LOG_DIR/chat.pid" ]; then
        kill $(cat "$LOG_DIR/chat.pid") 2>/dev/null
        rm "$LOG_DIR/chat.pid"
    fi
    
    # Stop MongoDB
    cd ../ui/db && docker-compose down && cd ../../frontend
    
    echo -e "${GREEN}✓ All services stopped${NC}"
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    stop_services
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Set up cleanup trap
trap cleanup EXIT

# Main execution
echo -e "${BLUE}Starting all services...${NC}"

# Start MongoDB first
start_mongodb

# Start chat service
start_chat_service

# Start frontend application
start_frontend

echo -e "\n${GREEN}All services started successfully!${NC}"
echo -e "${BLUE}Frontend URL: http://localhost:3001${NC}"
echo -e "${BLUE}Chat API URL: http://localhost:8000${NC}"
echo -e "\nPress Ctrl+C to stop all services\n"

# Keep script running
wait 