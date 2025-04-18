#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set DeepSeek API key
export PROFILER_SERVICES__DEEPSEEK__API_KEY="sk-a8c90a7a82884c0e994508e0608728eb"

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a port is in use
check_port() {
    if lsof -i :$1 > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to find an available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    while check_port $port; do
        port=$((port + 1))
    done
    echo $port
}

# Function to check if a process is running
check_process() {
    if pgrep -f "$1" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker to use the PostgreSQL container."
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker to use the PostgreSQL container."
        return 1
    fi
    
    return 0
}

# Function to check if docker-compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install docker-compose to use the PostgreSQL container."
        return 1
    fi
    
    return 0
}

# Function to start the PostgreSQL container
start_postgres() {
    print_message "Starting PostgreSQL container..."
    
    # Check if Docker and docker-compose are available
    if ! check_docker || ! check_docker_compose; then
        print_warning "Skipping PostgreSQL container startup. Using local database settings."
        return 1
    fi
    
    # Check if the postgres container is already running
    if docker ps | grep -q "profiler-postgres"; then
        print_message "PostgreSQL container is already running"
        DB_PORT=5432
        return 0
    fi
    
    # Check if port 5432 is available for PostgreSQL
    if check_port 5432; then
        print_warning "Port 5432 is in use. Finding an available port..."
        DB_PORT=$(find_available_port 5432)
        
        # Update docker-compose.yml with the new port
        local temp_file=$(mktemp)
        sed "s/5432:5432/${DB_PORT}:5432/" docker-compose.yml > "$temp_file"
        mv "$temp_file" docker-compose.yml
        print_message "Using port $DB_PORT for PostgreSQL container"
    else
        DB_PORT=5432
    fi
    
    # Start the PostgreSQL container
    if ! docker-compose up -d postgres; then
        print_error "Failed to start PostgreSQL container"
        print_warning "Continuing with local database settings"
        return 1
    fi
    
    # Wait for the PostgreSQL container to be ready (max 30 seconds)
    print_message "Waiting for PostgreSQL container to be ready..."
    local attempts=0
    while [ $attempts -lt 30 ]; do
        if docker logs profiler-postgres 2>&1 | grep -q "database system is ready to accept connections"; then
            print_message "PostgreSQL container is ready"
            sleep 2  # Give it a moment more to fully initialize
            
            # Update environment variables for database connection
            export PROFILER_DATABASE__URL="postgresql+asyncpg://postgres:postgres@localhost:${DB_PORT}/profiler"
            export PROFILER_PROFILE_SERVICE__REPOSITORY_TYPE="postgresql"
            
            print_message "PostgreSQL container started successfully"
            print_message "Database URL: $PROFILER_DATABASE__URL"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    print_error "PostgreSQL container took too long to start"
    print_warning "Continuing with local database settings"
    return 1
}

# Function to start a service
start_service() {
    local service_name=$1
    local start_command=$2
    local check_pattern=$3
    local log_file=$4

    if check_process "$check_pattern"; then
        print_warning "$service_name is already running"
        return 0
    fi

    print_message "Starting $service_name..."
    mkdir -p "$(dirname "$log_file")"
    eval "$start_command" > "$log_file" 2>&1 &
    local pid=$!

    # Wait for service to start (max 30 seconds)
    local attempts=0
    while [ $attempts -lt 30 ]; do
        if check_process "$check_pattern"; then
            sleep 2  # Give the service a moment to fully initialize
            if [ -f "$log_file" ]; then
                if ! grep -q "error\|exception\|fail" "$log_file"; then
                    print_message "$service_name started successfully (PID: $pid)"
                    return 0
                fi
            fi
        fi
        sleep 1
        attempts=$((attempts + 1))
    done

    print_error "Failed to start $service_name"
    print_error "Check logs: $log_file"
    if [ -f "$log_file" ]; then
        print_error "Last 10 lines of log:"
        tail -n 10 "$log_file" | while read line; do print_error "$line"; done
    fi
    return 1
}

# Function to stop services and containers
stop_services() {
    print_message "Stopping services..."
    
    # Stop API and UI services
    pkill -f "uvicorn.*app.backend.api.main:app" || true
    pkill -f "next.*dev" || true
    
    # Stop PostgreSQL container if it was started by this script
    if [[ "$USE_POSTGRES_CONTAINER" == "true" ]]; then
        print_message "Stopping PostgreSQL container..."
        docker-compose down || true
    fi
    
    print_message "All services stopped"
    exit 0
}

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Check for DeepSeek API key
if [ -z "$PROFILER_SERVICES__DEEPSEEK__API_KEY" ]; then
    print_warning "DeepSeek API key not set in environment variables"
    read -p "Enter your DeepSeek API key: " DEEPSEEK_API_KEY
    export PROFILER_SERVICES__DEEPSEEK__API_KEY="$DEEPSEEK_API_KEY"
    print_message "API key set for this session"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    print_message "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Start PostgreSQL container if enabled
USE_POSTGRES_CONTAINER="true"
if [[ "$USE_POSTGRES_CONTAINER" == "true" ]]; then
    start_postgres
fi

# Check if port 8000 is available for API server
if check_port 8000; then
    print_warning "Port 8000 is in use. Finding an available port..."
    API_PORT=$(find_available_port 8000)
    print_message "Using port $API_PORT for API server"
else
    API_PORT=8000
fi

# Start API server with WebSocket support
start_service "API Server" "uvicorn app.backend.api.main:app --host 0.0.0.0 --port $API_PORT --ws websockets" "uvicorn.*app.backend.api.main:app" "$SCRIPT_DIR/logs/api_server.log"

# Start UI server
if [ -d "app/ui" ]; then
    cd app/ui
    # Install UI dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_message "Installing UI dependencies..."
        npm install
    fi
    
    # Check if .env.local exists, create if not
    if [ ! -f ".env.local" ]; then
        print_message "Creating .env.local file..."
        cat > .env.local << EOL
NEXT_PUBLIC_API_URL=http://localhost:$API_PORT
NEXT_PUBLIC_WS_URL=ws://localhost:$API_PORT
NEXT_PUBLIC_API_KEY=test_key
EOL
    else
        # Update existing .env.local with correct ports
        sed -i '' "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://localhost:$API_PORT|" .env.local
        sed -i '' "s|NEXT_PUBLIC_WS_URL=.*|NEXT_PUBLIC_WS_URL=ws://localhost:$API_PORT|" .env.local
    fi
    
    # Check if port 3000 is available for UI server
    if check_port 3000; then
        print_warning "Port 3000 is in use. Finding an available port..."
        UI_PORT=$(find_available_port 3000)
        print_message "Using port $UI_PORT for UI server"
    else
        UI_PORT=3000
    fi
    
    # Start the UI server with the determined port
    start_service "UI Server" "npm run dev -- -p $UI_PORT" "next.*dev" "$SCRIPT_DIR/logs/ui_server.log"
    cd "$SCRIPT_DIR"
else
    print_error "UI directory not found at app/ui"
    exit 1
fi

# Check if both services are running
if check_process "uvicorn.*app.backend.api.main:app" && check_process "next.*dev"; then
    print_message "Both services are running successfully!"
    print_message "API Server: http://localhost:$API_PORT"
    print_message "UI Server: http://localhost:$UI_PORT"
    print_message "API Documentation: http://localhost:$API_PORT/api/docs"
    
    if [[ "$USE_POSTGRES_CONTAINER" == "true" ]] && [[ -n "$DB_PORT" ]]; then
        print_message "PostgreSQL Database: localhost:$DB_PORT"
    fi
else
    print_error "Failed to start one or both services. Check logs for details."
    stop_services
    exit 1
fi

# Register trap for clean exit
trap stop_services INT

# Keep script running and handle Ctrl+C
while true; do sleep 1; done 