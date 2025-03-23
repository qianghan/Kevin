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
SERVICES=("mongodb" "frontend" "backend")
declare -A PORTS=([mongodb]=27017 [frontend]=3000 [backend]=8000)
declare -A COLORS=([mongodb]="35" [frontend]="36" [backend]="33")

# Initialize logging
mkdir -p $LOG_DIR
for service in "${SERVICES[@]}"; do
    > "$LOG_DIR/$service.log"
done

# Color functions
service_color() {
    echo -e "\033[1;${COLORS[$1]}m"
}

print_log() {
    local service=$1
    local message=$2
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "$(service_color $service)[${service^^}] ${timestamp} ${message}\033[0m"
}

# Service management
start_mongodb() {
    if ! docker ps | grep -q kevin-ui-mongodb; then
        print_log mongodb "Starting MongoDB..."
        docker-compose -f ui/db/docker-compose.yml up > "$LOG_DIR/mongodb.log" 2>&1 &
        MONGO_PID=$!
        sleep 5
    fi
}

start_frontend() {
    print_log frontend "Starting Frontend..."
    cd ui
    npm run dev > "../$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    cd ..
}

start_backend() {
    if [ -d "backend" ]; then
        print_log backend "Starting Backend..."
        cd backend
        source ../.venv/bin/activate
        uvicorn main:app --host 0.0.0.0 --port 8000 > "../$LOG_DIR/backend.log" 2>&1 &
        BACKEND_PID=$!
        cd ..
    fi
}

# Log tailing
tail_logs() {
    tail -n 0 -f $LOG_DIR/*.log | while read -r line; do
        for service in "${SERVICES[@]}"; do
            if [[ "$line" == *"==> $LOG_DIR/$service.log <=="* ]]; then
                current_service=$service
                continue
            fi
            if [[ "$current_service" == "$service" ]]; then
                print_log $service "$line"
                break
            fi
        done
    done &
    TAIL_PID=$!
}

# Health checks
check_services() {
    for service in "${SERVICES[@]}"; do
        if [ "$service" == "mongodb" ]; then
            docker ps | grep -q kevin-ui-mongodb || return 1
        else
            netstat -tuln | grep -q ":${PORTS[$service]} " || return 1
        fi
    done
    return 0
}

# Shutdown handler
graceful_shutdown() {
    echo ""
    print_log system "Initiating shutdown..."
    kill $TAIL_PID $FRONTEND_PID $BACKEND_PID 2>/dev/null
    docker-compose -f ui/db/docker-compose.yml down
    
    # Kill any remaining processes
    pkill -P $$ 2>/dev/null
    print_log system "All services stopped"
    exit 0
}

# Main execution
trap graceful_shutdown INT TERM

start_mongodb
start_frontend
start_backend
tail_logs

# Display status
echo -e "\n\033[1;37mService Status:\033[0m"
for service in "${SERVICES[@]}"; do
    status="\033[0;32mRUNNING\033[0m"
    if [ "$service" == "mongodb" ]; then
        docker ps | grep -q kevin-ui-mongodb || status="\033[0;31mDOWN\033[0m"
    else
        netstat -tuln | grep -q ":${PORTS[$service]} " || status="\033[0;31mDOWN\033[0m"
    fi
    echo -e "$(service_color $service)● ${service^^}\033[0m: $status"
done

echo -e "\n\033[1;37mAccess URLs:\033[0m"
echo -e "Frontend:  \033[4;36mhttp://localhost:3000\033[0m"
[ -d "backend" ] && echo -e "Backend:   \033[4;33mhttp://localhost:8000\033[0m"
echo -e "MongoDB:   \033[4;35mmongodb://localhost:27017\033[0m"
echo -e "\n\033[1;37mPress Ctrl+C to stop all services\033[0m"

# Wait for termination
wait 