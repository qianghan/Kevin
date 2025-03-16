#!/bin/bash

# Define color codes for prettier output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
ACTION="start"
SERVICE="all"
LOG_DIR="./logs"
DEBUG=false

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Usage information
show_help() {
    echo -e "${CYAN}Kevin Application Management Script${NC}"
    echo ""
    echo -e "Usage: $0 [options]"
    echo ""
    echo -e "Options:"
    echo -e "  -h, --help                 Show this help message"
    echo -e "  -a, --action ACTION        Action to perform: ${GREEN}start${NC}, ${RED}stop${NC}, ${YELLOW}restart${NC} (default: start)"
    echo -e "  -s, --service SERVICE      Service to manage: ${BLUE}ui${NC}, ${BLUE}api${NC}, ${BLUE}db${NC}, ${BLUE}all${NC} (default: all)"
    echo -e "  -l, --logs                 Show logs for running services"
    echo -e "  -d, --debug                Enable debug output"
    echo ""
    echo -e "Examples:"
    echo -e "  $0                         Start all services"
    echo -e "  $0 -a stop -s db           Stop the MongoDB database"
    echo -e "  $0 -a restart -s api       Restart the FastAPI backend"
    echo -e "  $0 -a start -s ui          Start only the Next.js UI"
    echo -e "  $0 -l                      Show logs for running services"
    echo ""
}

# Parse command-line options
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -l|--logs)
            ACTION="logs"
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Validate action
if [[ ! "$ACTION" =~ ^(start|stop|restart|logs)$ ]]; then
    echo -e "${RED}Invalid action: $ACTION${NC}"
    show_help
    exit 1
fi

# Validate service
if [[ ! "$SERVICE" =~ ^(ui|api|db|all)$ ]]; then
    echo -e "${RED}Invalid service: $SERVICE${NC}"
    show_help
    exit 1
fi

# Debug information
if [ "$DEBUG" = true ]; then
    echo -e "${YELLOW}Debug mode enabled${NC}"
    echo -e "Action: $ACTION"
    echo -e "Service: $SERVICE"
    echo -e "Log directory: $LOG_DIR"
fi

# Function to start MongoDB
start_db() {
    echo -e "${YELLOW}Starting MongoDB container...${NC}"
    cd ui/db
    docker-compose up -d
    cd ../..

    # Check if MongoDB is running
    if docker ps | grep -q "kevin-ui-mongodb"; then
        echo -e "${GREEN}✓ MongoDB container is running${NC}"
    else
        echo -e "${RED}✗ Failed to start MongoDB container${NC}"
        return 1
    fi
    return 0
}

# Function to stop MongoDB
stop_db() {
    echo -e "${YELLOW}Stopping MongoDB container...${NC}"
    cd ui/db
    docker-compose down
    cd ../..

    # Check if MongoDB is stopped
    if docker ps | grep -q "kevin-ui-mongodb"; then
        echo -e "${RED}✗ Failed to stop MongoDB container${NC}"
        return 1
    else
        echo -e "${GREEN}✓ MongoDB container is stopped${NC}"
    fi
    return 0
}

# Function to restart MongoDB
restart_db() {
    stop_db
    start_db
}

# Function to show MongoDB logs
logs_db() {
    echo -e "${YELLOW}Showing MongoDB logs:${NC}"
    docker logs --tail=50 -f kevin-ui-mongodb
}

# Function to start FastAPI backend
start_api() {
    echo -e "${YELLOW}Starting FastAPI backend...${NC}"
    
    # Process ID file for the API
    local API_PID_FILE="$LOG_DIR/api.pid"
    local API_LOG_FILE="$LOG_DIR/api.log"
    
    # Check if API is already running
    if [ -f "$API_PID_FILE" ] && ps -p $(cat "$API_PID_FILE") > /dev/null; then
        echo -e "${YELLOW}API is already running with PID $(cat "$API_PID_FILE")${NC}"
        return 0
    fi
    
    # Start FastAPI in the background with output to log file
    echo -e "${BLUE}API logs will be available at: $API_LOG_FILE${NC}"
    
    # Activate the virtual environment and start the backend in the background
    (source kevin_venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null; \
     echo "Starting FastAPI backend at $(date)" >> "$API_LOG_FILE"; \
     PYTHONPATH=$(pwd) python -m src.api.main >> "$API_LOG_FILE" 2>&1) &
    
    # Store the process ID
    echo $! > "$API_PID_FILE"
    echo -e "${GREEN}✓ FastAPI backend started with PID $(cat "$API_PID_FILE")${NC}"
    
    return 0
}

# Function to stop FastAPI backend
stop_api() {
    echo -e "${YELLOW}Stopping FastAPI backend...${NC}"
    
    # Process ID file for the API
    local API_PID_FILE="$LOG_DIR/api.pid"
    
    # Check if API is running
    if [ ! -f "$API_PID_FILE" ]; then
        echo -e "${YELLOW}API is not running (PID file not found)${NC}"
        return 0
    fi
    
    local PID=$(cat "$API_PID_FILE")
    if ! ps -p $PID > /dev/null; then
        echo -e "${YELLOW}API is not running (process not found)${NC}"
        rm -f "$API_PID_FILE"
        return 0
    fi
    
    # Kill the process
    kill $PID
    sleep 2
    
    # Check if it's still running
    if ps -p $PID > /dev/null; then
        echo -e "${RED}Failed to gracefully stop API, forcing termination...${NC}"
        kill -9 $PID 2>/dev/null
        sleep 1
    fi
    
    # Clean up PID file
    rm -f "$API_PID_FILE"
    echo -e "${GREEN}✓ FastAPI backend stopped${NC}"
    
    return 0
}

# Function to restart FastAPI backend
restart_api() {
    stop_api
    start_api
}

# Function to show FastAPI logs
logs_api() {
    echo -e "${YELLOW}Showing FastAPI logs:${NC}"
    local API_LOG_FILE="$LOG_DIR/api.log"
    
    if [ ! -f "$API_LOG_FILE" ]; then
        echo -e "${RED}No API log file found at $API_LOG_FILE${NC}"
        return 1
    fi
    
    tail -f "$API_LOG_FILE"
}

# Function to start Next.js UI
start_ui() {
    echo -e "${YELLOW}Starting Next.js UI...${NC}"
    
    # Process ID file for the UI
    local UI_PID_FILE="$LOG_DIR/ui.pid"
    local UI_LOG_FILE="$LOG_DIR/ui.log"
    
    # Check if UI is already running
    if [ -f "$UI_PID_FILE" ] && ps -p $(cat "$UI_PID_FILE") > /dev/null; then
        echo -e "${YELLOW}UI is already running with PID $(cat "$UI_PID_FILE")${NC}"
        return 0
    fi
    
    # Start Next.js in the background with output to log file
    echo -e "${BLUE}UI logs will be available at: $UI_LOG_FILE${NC}"
    
    (cd ui && \
     echo "Starting Next.js UI at $(date)" >> "../$UI_LOG_FILE"; \
     npm run dev >> "../$UI_LOG_FILE" 2>&1) &
    
    # Store the process ID
    echo $! > "$UI_PID_FILE"
    echo -e "${GREEN}✓ Next.js UI started with PID $(cat "$UI_PID_FILE")${NC}"
    echo -e "${CYAN}Next.js UI is available at: http://localhost:3000${NC}"
    
    return 0
}

# Function to stop Next.js UI
stop_ui() {
    echo -e "${YELLOW}Stopping Next.js UI...${NC}"
    
    # Process ID file for the UI
    local UI_PID_FILE="$LOG_DIR/ui.pid"
    
    # Check if UI is running
    if [ ! -f "$UI_PID_FILE" ]; then
        echo -e "${YELLOW}UI is not running (PID file not found)${NC}"
        return 0
    fi
    
    local PID=$(cat "$UI_PID_FILE")
    if ! ps -p $PID > /dev/null; then
        echo -e "${YELLOW}UI is not running (process not found)${NC}"
        rm -f "$UI_PID_FILE"
        return 0
    fi
    
    # Kill the process (and child processes)
    pkill -P $PID
    kill $PID
    sleep 2
    
    # Check if it's still running
    if ps -p $PID > /dev/null; then
        echo -e "${RED}Failed to gracefully stop UI, forcing termination...${NC}"
        pkill -9 -P $PID 2>/dev/null
        kill -9 $PID 2>/dev/null
        sleep 1
    fi
    
    # Clean up PID file
    rm -f "$UI_PID_FILE"
    echo -e "${GREEN}✓ Next.js UI stopped${NC}"
    
    return 0
}

# Function to restart Next.js UI
restart_ui() {
    stop_ui
    start_ui
}

# Function to show Next.js UI logs
logs_ui() {
    echo -e "${YELLOW}Showing Next.js UI logs:${NC}"
    local UI_LOG_FILE="$LOG_DIR/ui.log"
    
    if [ ! -f "$UI_LOG_FILE" ]; then
        echo -e "${RED}No UI log file found at $UI_LOG_FILE${NC}"
        return 1
    fi
    
    tail -f "$UI_LOG_FILE"
}

# Main logic based on action and service
case "$ACTION" in
    start)
        echo -e "${GREEN}Starting Kevin Application...${NC}"
        
        if [[ "$SERVICE" == "all" || "$SERVICE" == "db" ]]; then
            start_db
        fi
        
        if [[ "$SERVICE" == "all" || "$SERVICE" == "api" ]]; then
            start_api
        fi
        
        if [[ "$SERVICE" == "all" || "$SERVICE" == "ui" ]]; then
            start_ui
        fi
        
        if [[ "$SERVICE" == "all" ]]; then
            echo -e "${GREEN}✅ All services started${NC}"
            echo -e "${CYAN}FastAPI backend is available at: http://localhost:8000${NC}"
            echo -e "${CYAN}Next.js UI is available at: http://localhost:3000${NC}"
            echo -e "${BLUE}Logs are available in: $LOG_DIR${NC}"
            echo -e "${YELLOW}Use '$0 -l' to view logs${NC}"
        fi
        ;;
        
    stop)
        echo -e "${RED}Stopping Kevin Application...${NC}"
        
        if [[ "$SERVICE" == "all" || "$SERVICE" == "ui" ]]; then
            stop_ui
        fi
        
        if [[ "$SERVICE" == "all" || "$SERVICE" == "api" ]]; then
            stop_api
        fi
        
        if [[ "$SERVICE" == "all" || "$SERVICE" == "db" ]]; then
            stop_db
        fi
        
        if [[ "$SERVICE" == "all" ]]; then
            echo -e "${GREEN}✅ All services stopped${NC}"
        fi
        ;;
        
    restart)
        echo -e "${YELLOW}Restarting Kevin Application...${NC}"
        
        if [[ "$SERVICE" == "all" || "$SERVICE" == "ui" ]]; then
            restart_ui
        fi
        
        if [[ "$SERVICE" == "all" || "$SERVICE" == "api" ]]; then
            restart_api
        fi
        
        if [[ "$SERVICE" == "all" || "$SERVICE" == "db" ]]; then
            restart_db
        fi
        
        if [[ "$SERVICE" == "all" ]]; then
            echo -e "${GREEN}✅ All services restarted${NC}"
            echo -e "${CYAN}FastAPI backend is available at: http://localhost:8000${NC}"
            echo -e "${CYAN}Next.js UI is available at: http://localhost:3000${NC}"
        fi
        ;;
        
    logs)
        echo -e "${BLUE}Showing logs for Kevin Application...${NC}"
        
        # Check which services are running and show their logs
        if [[ "$SERVICE" == "db" ]]; then
            logs_db
        elif [[ "$SERVICE" == "api" ]]; then
            logs_api
        elif [[ "$SERVICE" == "ui" ]]; then
            logs_ui
        elif [[ "$SERVICE" == "all" ]]; then
            # Show a menu to select which logs to view
            echo -e "Select which logs to view:"
            echo -e "1) MongoDB logs"
            echo -e "2) FastAPI backend logs"
            echo -e "3) Next.js UI logs"
            echo -e "q) Quit"
            
            read -p "Enter your choice: " LOG_CHOICE
            
            case "$LOG_CHOICE" in
                1) logs_db ;;
                2) logs_api ;;
                3) logs_ui ;;
                q|Q) exit 0 ;;
                *) echo -e "${RED}Invalid choice${NC}" ;;
            esac
        fi
        ;;
esac

echo -e "${GREEN}Done!${NC}" 