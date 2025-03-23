#!/bin/bash

# =====================================================================
# Kevin AI Startup Script with Enhanced Visual Logging
# =====================================================================
# Features:
# - Real-time combined service logs with distinctive color coding
# - Service-specific log prefixes with background colors
# - Visual separators between different services
# - Emoji indicators for different log types
# - Log preservation in separate files
# - Keyboard shortcuts for operations (q = quit)
# =====================================================================

# Configuration
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# Reset log files
> "$LOG_DIR/mongodb.log"
> "$LOG_DIR/frontend.log"
> "$LOG_DIR/backend.log"

# Color definitions - text colors
COLOR_RESET="\033[0m"
COLOR_BOLD="\033[1m"
COLOR_RED="\033[31m"
COLOR_GREEN="\033[32m"
COLOR_YELLOW="\033[33m"
COLOR_BLUE="\033[34m"
COLOR_PURPLE="\033[35m"
COLOR_CYAN="\033[36m"
COLOR_WHITE="\033[37m"

# Background colors for services
BG_MONGODB="\033[45m"    # Purple background
BG_FRONTEND="\033[46m"   # Cyan background
BG_BACKEND="\033[43m"    # Yellow background
BG_SYSTEM="\033[44m"     # Blue background
BG_ERROR="\033[41m"      # Red background

# Log indicators (emojis)
EMOJI_INFO="ℹ️ "
EMOJI_SUCCESS="✅ "
EMOJI_WARNING="⚠️ "
EMOJI_ERROR="❌ "
EMOJI_MONGODB="🍃 "
EMOJI_FRONTEND="🖥️ "
EMOJI_BACKEND="⚙️ "
EMOJI_SYSTEM="🔄 "

# Print colored message with timestamp and service-specific styling
print_log() {
    local bg_color=$1
    local fg_color=$2
    local emoji=$3
    local prefix=$4
    local message=$5
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${bg_color}${COLOR_BOLD}${fg_color} ${emoji}[${prefix}] ${timestamp} ${message}${COLOR_RESET}"
}

# Print a separator line
print_separator() {
    local color=$1
    local title=$2
    echo -e "\n${color}${COLOR_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
    if [ ! -z "$title" ]; then
        echo -e "${color}${COLOR_BOLD}  ${title}  ${COLOR_RESET}"
        echo -e "${color}${COLOR_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
    fi
}

# Service management functions
start_mongodb() {
    if ! docker ps | grep -q kevin-ui-mongodb; then
        print_log "$BG_MONGODB" "$COLOR_WHITE" "$EMOJI_MONGODB" "MONGODB" "Starting MongoDB..."
        cd ui/db && docker-compose up -d
        sleep 5
        cd ../..
        print_log "$BG_MONGODB" "$COLOR_WHITE" "$EMOJI_SUCCESS" "MONGODB" "MongoDB started successfully"
    else
        print_log "$BG_MONGODB" "$COLOR_WHITE" "$EMOJI_MONGODB" "MONGODB" "MongoDB already running"
    fi
}

start_frontend() {
    print_log "$BG_FRONTEND" "$COLOR_WHITE" "$EMOJI_FRONTEND" "FRONTEND" "Starting Next.js frontend..."
    cd ui
    npm run dev > "../$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    cd ..
    print_log "$BG_FRONTEND" "$COLOR_WHITE" "$EMOJI_SUCCESS" "FRONTEND" "Frontend started with PID: $FRONTEND_PID"
}

start_backend() {
    if [ -d "backend" ]; then
        print_log "$BG_BACKEND" "$COLOR_WHITE" "$EMOJI_BACKEND" "BACKEND" "Starting FastAPI backend..."
        cd backend
        if [ -d "../.venv" ]; then
            source ../.venv/bin/activate
        fi
        
        if [ -f "main.py" ]; then
            uvicorn main:app --host 0.0.0.0 --port 8000 > "../$LOG_DIR/backend.log" 2>&1 &
            BACKEND_PID=$!
            print_log "$BG_BACKEND" "$COLOR_WHITE" "$EMOJI_SUCCESS" "BACKEND" "Backend started with PID: $BACKEND_PID"
        elif [ -f "app.py" ]; then
            uvicorn app:app --host 0.0.0.0 --port 8000 > "../$LOG_DIR/backend.log" 2>&1 &
            BACKEND_PID=$!
            print_log "$BG_BACKEND" "$COLOR_WHITE" "$EMOJI_SUCCESS" "BACKEND" "Backend started with PID: $BACKEND_PID"
        else
            print_log "$BG_ERROR" "$COLOR_WHITE" "$EMOJI_ERROR" "BACKEND" "Cannot find main.py or app.py. Backend not started."
        fi
        
        cd ..
    else
        print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_INFO" "SYSTEM" "Backend directory not found. Skipping backend startup."
    fi
}

# Follow logs from files with enhanced visual formatting
follow_logs() {
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_SYSTEM" "SYSTEM" "Starting log streaming..."
    
    # Create a named pipe for combining logs
    PIPE_DIR="/tmp/kevin-logs"
    mkdir -p $PIPE_DIR
    COMBINED_PIPE="$PIPE_DIR/combined_logs"
    [ -p "$COMBINED_PIPE" ] || mkfifo "$COMBINED_PIPE"
    
    # Background process to format and output combined logs
    cat "$COMBINED_PIPE" &
    LOG_CAT_PID=$!
    
    # Start tailing logs with distinct formatting for each service
    # MongoDB logs - Purple background
    docker logs -f kevin-ui-mongodb 2>&1 | while read line; do
        echo -e "${BG_MONGODB}${COLOR_BOLD}${COLOR_WHITE} ${EMOJI_MONGODB}[MONGODB] $(date +"%Y-%m-%d %H:%M:%S") ${line}${COLOR_RESET}" >> "$COMBINED_PIPE"
    done &
    MONGO_TAIL_PID=$!
    
    # Frontend logs - Cyan background
    tail -f "$LOG_DIR/frontend.log" | while read line; do
        echo -e "${BG_FRONTEND}${COLOR_BOLD}${COLOR_WHITE} ${EMOJI_FRONTEND}[FRONTEND] $(date +"%Y-%m-%d %H:%M:%S") ${line}${COLOR_RESET}" >> "$COMBINED_PIPE"
    done &
    FRONTEND_TAIL_PID=$!
    
    # Backend logs - Yellow background
    if [ -d "backend" ]; then
        tail -f "$LOG_DIR/backend.log" | while read line; do
            echo -e "${BG_BACKEND}${COLOR_BOLD}${COLOR_WHITE} ${EMOJI_BACKEND}[BACKEND] $(date +"%Y-%m-%d %H:%M:%S") ${line}${COLOR_RESET}" >> "$COMBINED_PIPE"
        done &
        BACKEND_TAIL_PID=$!
    fi
    
    # Store PIDs for cleanup
    LOG_PIDS=($LOG_CAT_PID $MONGO_TAIL_PID $FRONTEND_TAIL_PID $BACKEND_TAIL_PID)
}

# Function to verify port is released
check_port_released() {
    local port=$1
    local service=$2
    local max_attempts=5
    local attempt=0
    
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_INFO" "SYSTEM" "Verifying port $port is released..."
    
    while [ $attempt -lt $max_attempts ]; do
        if lsof -i :$port > /dev/null 2>&1; then
            # Port still in use, wait a bit
            print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_WARNING" "SYSTEM" "Port $port still in use, waiting..."
            sleep 1
            ((attempt++))
        else
            print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_SUCCESS" "SYSTEM" "Port $port successfully released"
            return 0
        fi
    done
    
    print_log "$BG_ERROR" "$COLOR_WHITE" "$EMOJI_ERROR" "SYSTEM" "Failed to release port $port for $service"
    
    # Force kill any process using the port
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_WARNING" "SYSTEM" "Force killing processes on port $port..."
    local pid=$(lsof -t -i :$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        kill -9 $pid
        print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_SUCCESS" "SYSTEM" "Forcefully terminated process $pid on port $port"
    fi
    
    return 1
}

# Function to verify process is terminated
verify_process_terminated() {
    local pid=$1
    local service=$2
    local max_attempts=5
    local attempt=0
    
    if [ -z "$pid" ]; then
        return 0
    fi
    
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_INFO" "SYSTEM" "Verifying $service process (PID: $pid) is terminated..."
    
    while [ $attempt -lt $max_attempts ]; do
        if kill -0 $pid 2>/dev/null; then
            # Process still running
            print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_WARNING" "SYSTEM" "$service process (PID: $pid) still running, waiting..."
            sleep 1
            ((attempt++))
        else
            print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_SUCCESS" "SYSTEM" "$service process (PID: $pid) successfully terminated"
            return 0
        fi
    done
    
    print_log "$BG_ERROR" "$COLOR_WHITE" "$EMOJI_ERROR" "SYSTEM" "Failed to terminate $service process (PID: $pid)"
    
    # Force kill the process
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_WARNING" "SYSTEM" "Force killing $service process (PID: $pid)..."
    kill -9 $pid 2>/dev/null
    
    if ! kill -0 $pid 2>/dev/null; then
        print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_SUCCESS" "SYSTEM" "Forcefully terminated $service process (PID: $pid)"
        return 0
    else
        print_log "$BG_ERROR" "$COLOR_WHITE" "$EMOJI_ERROR" "SYSTEM" "Failed to forcefully terminate $service process (PID: $pid)"
        return 1
    fi
}

# Shutdown handler with visual indicators and thorough cleanup
graceful_shutdown() {
    echo ""
    print_separator "$COLOR_RED" "SHUTTING DOWN SERVICES"
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_SYSTEM" "SYSTEM" "Initiating graceful shutdown..."
    
    # Kill log tails
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_INFO" "SYSTEM" "Stopping log streaming..."
    for pid in "${LOG_PIDS[@]}"; do
        if [ ! -z "$pid" ]; then
            kill $pid 2>/dev/null || true
        fi
    done
    
    # Clean up named pipe
    if [ -p "$COMBINED_PIPE" ]; then
        rm -f "$COMBINED_PIPE"
    fi
    
    # Kill frontend service
    if [ ! -z "$FRONTEND_PID" ]; then
        print_log "$BG_FRONTEND" "$COLOR_WHITE" "$EMOJI_FRONTEND" "FRONTEND" "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
        verify_process_terminated "$FRONTEND_PID" "Frontend"
        check_port_released 3000 "Frontend"
    fi
    
    # Kill backend service
    if [ ! -z "$BACKEND_PID" ]; then
        print_log "$BG_BACKEND" "$COLOR_WHITE" "$EMOJI_BACKEND" "BACKEND" "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        verify_process_terminated "$BACKEND_PID" "Backend"
        check_port_released 8000 "Backend"
    fi
    
    # Stop MongoDB
    print_log "$BG_MONGODB" "$COLOR_WHITE" "$EMOJI_MONGODB" "MONGODB" "Stopping MongoDB..."
    cd ui/db && docker-compose down
    cd ../..
    sleep 2
    
    # Check MongoDB port is released
    check_port_released 27017 "MongoDB"
    
    # Check for any remaining MongoDB container
    if docker ps | grep -q kevin-ui-mongodb; then
        print_log "$BG_MONGODB" "$COLOR_WHITE" "$EMOJI_WARNING" "MONGODB" "MongoDB container still running, force stopping..."
        docker stop kevin-ui-mongodb
    fi
    
    # Find and kill any remaining child processes
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_INFO" "SYSTEM" "Cleaning up any remaining processes..."
    pkill -P $$ 2>/dev/null || true
    
    # Check for any processes on our ports
    for port in 3000 8000 27017; do
        if lsof -i :$port > /dev/null 2>&1; then
            print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_WARNING" "SYSTEM" "Detected process still using port $port, force killing..."
            kill -9 $(lsof -t -i :$port) 2>/dev/null || true
        fi
    done
    
    print_separator "$COLOR_GREEN" "SHUTDOWN COMPLETE"
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_SUCCESS" "SYSTEM" "All services stopped and ports released successfully"
    exit 0
}

# Key press monitor function for shortcut keys
monitor_keypress() {
    print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_INFO" "SYSTEM" "Keyboard shortcuts enabled: Press 'q' to quit"
    
    # Set up non-blocking input
    stty -echo
    
    # Monitor for key presses
    while :; do
        # Check for a key press with a short timeout
        read -t 1 -n 1 key
        
        if [ "$key" = "q" ]; then
            # Restore terminal settings
            stty echo
            print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_INFO" "SYSTEM" "Quit shortcut key pressed (q)"
            graceful_shutdown
        fi
    done
}

# Set up graceful shutdown
trap graceful_shutdown INT TERM

# Main execution
print_separator "$COLOR_BLUE" "STARTING KEVIN AI SERVICES"

# Start all services
print_log "$BG_SYSTEM" "$COLOR_WHITE" "$EMOJI_SYSTEM" "SYSTEM" "Initializing services..."
start_mongodb
start_frontend
start_backend

# Print service status with visual indicators
print_separator "$COLOR_BLUE" "SERVICE STATUS"

# Check MongoDB
if docker ps | grep -q kevin-ui-mongodb; then
    echo -e "${BG_MONGODB}${COLOR_WHITE}${COLOR_BOLD} ${EMOJI_SUCCESS} MONGODB:${COLOR_RESET} ${COLOR_GREEN}RUNNING${COLOR_RESET}"
else
    echo -e "${BG_MONGODB}${COLOR_WHITE}${COLOR_BOLD} ${EMOJI_ERROR} MONGODB:${COLOR_RESET} ${COLOR_RED}NOT RUNNING${COLOR_RESET}"
fi

# Check Frontend
if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${BG_FRONTEND}${COLOR_WHITE}${COLOR_BOLD} ${EMOJI_SUCCESS} FRONTEND:${COLOR_RESET} ${COLOR_GREEN}RUNNING (PID: $FRONTEND_PID)${COLOR_RESET}"
else
    echo -e "${BG_FRONTEND}${COLOR_WHITE}${COLOR_BOLD} ${EMOJI_ERROR} FRONTEND:${COLOR_RESET} ${COLOR_RED}NOT RUNNING${COLOR_RESET}"
fi

# Check Backend
if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${BG_BACKEND}${COLOR_WHITE}${COLOR_BOLD} ${EMOJI_SUCCESS} BACKEND:${COLOR_RESET} ${COLOR_GREEN}RUNNING (PID: $BACKEND_PID)${COLOR_RESET}"
elif [ -d "backend" ]; then
    echo -e "${BG_BACKEND}${COLOR_WHITE}${COLOR_BOLD} ${EMOJI_ERROR} BACKEND:${COLOR_RESET} ${COLOR_RED}NOT RUNNING${COLOR_RESET}"
fi

# Print access URLs with better formatting
print_separator "$COLOR_BLUE" "ACCESS INFORMATION"
echo -e "${COLOR_BOLD}Frontend:${COLOR_RESET}  ${COLOR_CYAN}${COLOR_BOLD}http://localhost:3000${COLOR_RESET}"
[ -d "backend" ] && echo -e "${COLOR_BOLD}Backend:${COLOR_RESET}   ${COLOR_YELLOW}${COLOR_BOLD}http://localhost:8000${COLOR_RESET}"
echo -e "${COLOR_BOLD}MongoDB:${COLOR_RESET}   ${COLOR_PURPLE}${COLOR_BOLD}mongodb://localhost:27017${COLOR_RESET}"

print_separator "$COLOR_BLUE" "KEYBOARD SHORTCUTS"
echo -e "${COLOR_BOLD}Press 'q' to quit all services${COLOR_RESET}"
echo -e "${COLOR_BOLD}Press Ctrl+C to quit all services${COLOR_RESET}"

print_separator "$COLOR_BLUE" "LOG OUTPUT"

# Start key press monitor in the background
monitor_keypress &
KEYPRESS_MONITOR_PID=$!

# Start following logs
follow_logs

# Keep script running
wait 