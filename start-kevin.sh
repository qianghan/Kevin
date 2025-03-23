#!/bin/bash

# =====================================================================
# Kevin AI Startup Script with Service Logging
# =====================================================================
# Features:
# - Real-time combined service logs with color coding
# - Service-specific log prefixes
# - Log preservation in separate files
# - Full service visibility
# =====================================================================

# Configuration
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# Reset log files
> "$LOG_DIR/mongodb.log"
> "$LOG_DIR/frontend.log"
> "$LOG_DIR/backend.log"

# Color definitions
COLOR_RESET="\033[0m"
COLOR_BOLD="\033[1m"
COLOR_RED="\033[31m"
COLOR_GREEN="\033[32m"
COLOR_YELLOW="\033[33m"
COLOR_BLUE="\033[34m"
COLOR_PURPLE="\033[35m"
COLOR_CYAN="\033[36m"
COLOR_WHITE="\033[37m"

# Print colored message with timestamp
print_log() {
    local color=$1
    local prefix=$2
    local message=$3
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${COLOR_BOLD}${color}[${prefix}] ${timestamp} ${message}${COLOR_RESET}"
}

# Service management functions
start_mongodb() {
    if ! docker ps | grep -q kevin-ui-mongodb; then
        print_log "$COLOR_PURPLE" "MONGODB" "Starting MongoDB..."
        cd ui/db && docker-compose up -d
        sleep 5
        cd ../..
        print_log "$COLOR_PURPLE" "MONGODB" "MongoDB started"
    else
        print_log "$COLOR_PURPLE" "MONGODB" "MongoDB already running"
    fi
}

start_frontend() {
    print_log "$COLOR_CYAN" "FRONTEND" "Starting Frontend..."
    cd ui
    npm run dev > "../$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    cd ..
    print_log "$COLOR_CYAN" "FRONTEND" "Frontend started with PID: $FRONTEND_PID"
}

start_backend() {
    if [ -d "backend" ]; then
        print_log "$COLOR_YELLOW" "BACKEND" "Starting Backend..."
        cd backend
        if [ -d "../.venv" ]; then
            source ../.venv/bin/activate
        fi
        
        if [ -f "main.py" ]; then
            uvicorn main:app --host 0.0.0.0 --port 8000 > "../$LOG_DIR/backend.log" 2>&1 &
            BACKEND_PID=$!
            print_log "$COLOR_YELLOW" "BACKEND" "Backend started with PID: $BACKEND_PID"
        elif [ -f "app.py" ]; then
            uvicorn app:app --host 0.0.0.0 --port 8000 > "../$LOG_DIR/backend.log" 2>&1 &
            BACKEND_PID=$!
            print_log "$COLOR_YELLOW" "BACKEND" "Backend started with PID: $BACKEND_PID"
        else
            print_log "$COLOR_RED" "BACKEND" "Cannot find main.py or app.py. Backend not started."
        fi
        
        cd ..
    else
        print_log "$COLOR_YELLOW" "BACKEND" "Backend directory not found. Skipping."
    fi
}

# Follow logs from files
follow_logs() {
    print_log "$COLOR_BLUE" "SYSTEM" "Starting log streaming..."
    
    # Start tailing logs in background
    tail -f "$LOG_DIR/frontend.log" | sed "s/^/${COLOR_CYAN}[FRONTEND] /" &
    FRONTEND_TAIL_PID=$!
    
    if [ -d "backend" ]; then
        tail -f "$LOG_DIR/backend.log" | sed "s/^/${COLOR_YELLOW}[BACKEND] /" &
        BACKEND_TAIL_PID=$!
    fi
    
    # Add MongoDB logs if needed
    docker logs -f kevin-ui-mongodb 2>&1 | sed "s/^/${COLOR_PURPLE}[MONGODB] /" &
    MONGO_TAIL_PID=$!
}

# Shutdown handler
graceful_shutdown() {
    echo ""
    print_log "$COLOR_BLUE" "SYSTEM" "Shutting down services..."
    
    # Kill log tails
    kill $FRONTEND_TAIL_PID $BACKEND_TAIL_PID $MONGO_TAIL_PID 2>/dev/null || true
    
    # Kill services
    if [ ! -z "$FRONTEND_PID" ]; then
        print_log "$COLOR_CYAN" "FRONTEND" "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_log "$COLOR_YELLOW" "BACKEND" "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    print_log "$COLOR_PURPLE" "MONGODB" "Stopping MongoDB..."
    cd ui/db && docker-compose down
    cd ../..
    
    # Find and kill any remaining child processes
    pkill -P $$ 2>/dev/null || true
    
    print_log "$COLOR_GREEN" "SYSTEM" "All services stopped"
    exit 0
}

# Set up graceful shutdown
trap graceful_shutdown INT TERM

# Start all services
print_log "$COLOR_BLUE" "SYSTEM" "Starting Kevin AI services..."
start_mongodb
start_frontend
start_backend

# Print service status
echo -e "\n${COLOR_BOLD}${COLOR_WHITE}Service Status:${COLOR_RESET}"

# Check MongoDB
if docker ps | grep -q kevin-ui-mongodb; then
    echo -e "${COLOR_PURPLE}●${COLOR_RESET} ${COLOR_BOLD}MONGODB${COLOR_RESET}: ${COLOR_GREEN}RUNNING${COLOR_RESET}"
else
    echo -e "${COLOR_PURPLE}●${COLOR_RESET} ${COLOR_BOLD}MONGODB${COLOR_RESET}: ${COLOR_RED}NOT RUNNING${COLOR_RESET}"
fi

# Check Frontend
if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${COLOR_CYAN}●${COLOR_RESET} ${COLOR_BOLD}FRONTEND${COLOR_RESET}: ${COLOR_GREEN}RUNNING (PID: $FRONTEND_PID)${COLOR_RESET}"
else
    echo -e "${COLOR_CYAN}●${COLOR_RESET} ${COLOR_BOLD}FRONTEND${COLOR_RESET}: ${COLOR_RED}NOT RUNNING${COLOR_RESET}"
fi

# Check Backend
if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${COLOR_YELLOW}●${COLOR_RESET} ${COLOR_BOLD}BACKEND${COLOR_RESET}: ${COLOR_GREEN}RUNNING (PID: $BACKEND_PID)${COLOR_RESET}"
elif [ -d "backend" ]; then
    echo -e "${COLOR_YELLOW}●${COLOR_RESET} ${COLOR_BOLD}BACKEND${COLOR_RESET}: ${COLOR_RED}NOT RUNNING${COLOR_RESET}"
fi

echo -e "\n${COLOR_BOLD}${COLOR_WHITE}Access URLs:${COLOR_RESET}"
echo -e "Frontend:  ${COLOR_CYAN}http://localhost:3000${COLOR_RESET}"
[ -d "backend" ] && echo -e "Backend:   ${COLOR_YELLOW}http://localhost:8000${COLOR_RESET}"
echo -e "MongoDB:   ${COLOR_PURPLE}mongodb://localhost:27017${COLOR_RESET}"
echo -e "\n${COLOR_BOLD}${COLOR_WHITE}Press Ctrl+C to stop all services${COLOR_RESET}"

# Start following logs
follow_logs

# Keep script running
wait 