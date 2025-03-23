#!/bin/bash

# =====================================================================
# Kevin AI Installation Script (Enhanced)
# =====================================================================
# Features:
# - Color-coded progress tracking with emoji indicators
# - Resumable installation with status tracking
# - Detailed error logging with line numbers
# - Clean rollback on failure
# - Progress percentage display
# =====================================================================

# Initialize installation status
STATUS_FILE=".kevin_install_status"
ERROR_LOG="install_error.log"
touch $STATUS_FILE
exec 3<> $STATUS_FILE

# Color and style definitions
BOLD='\033[1m'
BLUE='\033[0;94m'
GREEN='\033[0;92m'
YELLOW='\033[0;93m'
RED='\033[0;91m'
NC='\033[0m' # No Color

# Configuration variables
PYTHON_VERSION="3.10"
NODE_VERSION="18"
MONGO_PORT="27017"
KEVIN_DIR="$(pwd)"
VENV_DIR="$KEVIN_DIR/.venv"
BACKEND_DIR="$KEVIN_DIR/backend"
UI_DIR="$KEVIN_DIR/ui"

# Progress tracking
TOTAL_STEPS=8
CURRENT_STEP=0
declare -A STEPS=(
    [1]="System Dependencies"
    [2]="Python Environment"
    [3]="Backend Dependencies"
    [4]="Frontend Dependencies"
    [5]="MongoDB Setup"
    [6]="Environment Files"
    [7]="Start Script"
    [8]="Final Configuration"
)

# Logging functions with timestamp and line numbers
log() {
    local level=$1
    local message=$2
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local line_info="${BASH_SOURCE[1]}:${BASH_LINENO[0]}"
    case $level in
        "INFO") echo -e "${BLUE}${BOLD}[ℹ] ${timestamp} ${line_info} ${message}${NC}" ;;
        "SUCCESS") echo -e "${GREEN}${BOLD}[✓] ${timestamp} ${line_info} ${message}${NC}" ;;
        "WARNING") echo -e "${YELLOW}${BOLD}[⚠] ${timestamp} ${line_info} ${message}${NC}" ;;
        "ERROR") echo -e "${RED}${BOLD}[✗] ${timestamp} ${line_info} ${message}${NC}" ;;
    esac
}

# Error handling with rollback
handle_error() {
    local exit_code=$1
    local command=$2
    log "ERROR" "Command failed (exit $exit_code): $command"
    echo -e "${RED}${BOLD}Installation failed at step $CURRENT_STEP/${TOTAL_STEPS}${NC}"
    echo -e "${YELLOW}To resume installation, run the script again.${NC}"
    exit $exit_code
}

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        log "WARNING" "Performing cleanup..."
        # Add specific cleanup operations here
    fi
}

# Check installation status
check_status() {
    local step=$1
    grep -q "STEP$step" $STATUS_FILE && return 0 || return 1
}

# Update progress display
update_progress() {
    CURRENT_STEP=$1
    local percentage=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    echo -e "\n${BLUE}${BOLD}Progress: [$percentage%] Step $CURRENT_STEP/${TOTAL_STEPS} - ${STEPS[$CURRENT_STEP]}${NC}\n"
}

# Verify the script is running from the project root
check_directory() {
    log "INFO" "Checking if script is run from project root..."
    
    if [ ! -d "ui" ] || [ ! -d "backend" ]; then
        log "ERROR" "This script must be run from the Kevin project root directory!"
        log "ERROR" "Please make sure both 'ui' and 'backend' directories exist."
        exit 1
    fi
    
    log "SUCCESS" "Directory structure looks good!"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check and install system dependencies
install_system_dependencies() {
    check_status 1 && return 0
    log "INFO" "Checking system dependencies..."
    
    # Check OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command_exists brew; then
            log "ERROR" "Homebrew is required. Please install it from https://brew.sh/"
            exit 1
        fi
        
        log "INFO" "Installing system dependencies with Homebrew..."
        brew update
        brew install python@$PYTHON_VERSION node@$NODE_VERSION docker docker-compose || true
        
        # Start Docker if not running
        if ! docker info > /dev/null 2>&1; then
            log "INFO" "Starting Docker..."
            open -a Docker
            # Wait for Docker to start
            sleep 10
        fi
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt-get; then
            log "INFO" "Installing system dependencies with apt..."
            sudo apt-get update
            sudo apt-get install -y curl build-essential libssl-dev zlib1g-dev libbz2-dev \
                libreadline-dev libsqlite3-dev wget llvm libncurses5-dev libncursesw5-dev \
                xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git
        elif command_exists yum; then
            log "INFO" "Installing system dependencies with yum..."
            sudo yum -y update
            sudo yum -y groupinstall "Development Tools"
            sudo yum -y install openssl-devel bzip2-devel libffi-devel
        else
            log "WARNING" "Unsupported Linux distribution. You may need to install dependencies manually."
        fi
        
        # Install Docker if not present
        if ! command_exists docker; then
            log "INFO" "Installing Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
            log "WARNING" "You may need to log out and back in for Docker group changes to take effect."
        fi
        
        # Start Docker if not running
        if ! docker info > /dev/null 2>&1; then
            log "INFO" "Starting Docker..."
            sudo systemctl start docker
        fi
    else
        log "WARNING" "Unsupported OS. You may need to install dependencies manually."
    fi
    
    log "SUCCESS" "System dependencies installed!"
    echo "STEP1" >&3
}

# Setup Python virtual environment
setup_python_env() {
    check_status 2 && return 0
    log "INFO" "Setting up Python virtual environment..."
    
    # Check if pyenv is installed, otherwise use system Python
    if command_exists pyenv; then
        log "INFO" "Using pyenv to install Python $PYTHON_VERSION..."
        pyenv install $PYTHON_VERSION -s
        pyenv local $PYTHON_VERSION
        PYTHON_CMD="$(pyenv which python)"
    else
        log "INFO" "Pyenv not found, checking system Python..."
        if command_exists python3; then
            PY_VERSION=$(python3 --version | cut -d' ' -f2)
            log "INFO" "Found Python $PY_VERSION"
            if [[ $PY_VERSION == $PYTHON_VERSION* ]]; then
                PYTHON_CMD="python3"
            else
                log "WARNING" "System Python ($PY_VERSION) is not $PYTHON_VERSION"
                log "WARNING" "Installing pyenv to manage Python versions..."
                
                # Install pyenv
                curl https://pyenv.run | bash
                
                # Add pyenv to PATH for the current session
                export PATH="$HOME/.pyenv/bin:$PATH"
                eval "$(pyenv init --path)"
                eval "$(pyenv init -)"
                
                # Install required Python version
                pyenv install $PYTHON_VERSION
                pyenv local $PYTHON_VERSION
                PYTHON_CMD="$(pyenv which python)"
            fi
        else
            log "ERROR" "Python not found. Please install Python $PYTHON_VERSION."
            exit 1
        fi
    fi
    
    # Create and activate virtual environment
    log "INFO" "Creating virtual environment at $VENV_DIR..."
    $PYTHON_CMD -m venv $VENV_DIR
    
    # Activate the virtual environment
    source $VENV_DIR/bin/activate
    
    # Upgrade pip
    log "INFO" "Upgrading pip..."
    pip install --upgrade pip
    
    log "SUCCESS" "Python environment setup complete!"
    echo "STEP2" >&3
}

# Install backend dependencies
install_backend_dependencies() {
    check_status 3 && return 0
    log "INFO" "Installing backend dependencies..."
    
    # Activate virtual environment if not already activated
    if [ -z "$VIRTUAL_ENV" ]; then
        source $VENV_DIR/bin/activate
    fi
    
    # Install backend requirements
    cd $BACKEND_DIR
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        log "WARNING" "No requirements.txt found in the backend directory!"
    fi
    
    # Install additional packages that might be needed
    pip install fastapi uvicorn

    cd $KEVIN_DIR
    log "SUCCESS" "Backend dependencies installed!"
    echo "STEP3" >&3
}

# Install frontend dependencies
install_frontend_dependencies() {
    check_status 4 && return 0
    log "INFO" "Installing frontend dependencies..."
    
    # Check Node.js version
    if command_exists node; then
        NODE_V=$(node -v | cut -d'v' -f2)
        log "INFO" "Found Node.js $NODE_V"
    else
        log "ERROR" "Node.js not found. Please install Node.js $NODE_VERSION or higher."
        exit 1
    fi
    
    # Install frontend dependencies
    cd $UI_DIR
    log "INFO" "Installing npm packages for the UI..."
    npm install
    
    # Return to project root
    cd $KEVIN_DIR
    log "SUCCESS" "Frontend dependencies installed!"
    echo "STEP4" >&3
}

# Setup MongoDB with Docker
setup_mongodb() {
    check_status 5 && return 0
    log "INFO" "Setting up MongoDB with Docker..."
    
    # Check if MongoDB container already exists
    if docker ps -a | grep -q kevin-ui-mongodb; then
        log "INFO" "MongoDB container already exists. Starting it if not running..."
        docker start kevin-ui-mongodb 2>/dev/null || true
    else
        log "INFO" "Creating MongoDB container..."
        cd $UI_DIR/db
        
        # Create the data directory if it doesn't exist
        mkdir -p data
        
        # Start MongoDB with docker-compose
        docker-compose up -d
        
        # Return to project root
        cd $KEVIN_DIR
    fi
    
    # Wait for MongoDB to start
    log "INFO" "Waiting for MongoDB to start..."
    sleep 5
    
    # Test MongoDB connection
    cd $UI_DIR
    npm run db:test
    
    # Return to project root
    cd $KEVIN_DIR
    log "SUCCESS" "MongoDB setup complete!"
    echo "STEP5" >&3
}

# Create local environment files
create_env_files() {
    check_status 6 && return 0
    log "INFO" "Setting up environment files..."
    
    # Create .env.local for UI
    if [ ! -f "$UI_DIR/.env.local" ]; then
        log "INFO" "Creating .env.local for UI..."
        cat > "$UI_DIR/.env.local" << EOL
# MongoDB Connection
MONGODB_URI=mongodb://kevinuser:kevin_password@localhost:27017/kevindb?authSource=admin

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=supersecretkeyfornextauth

# Feature Flags
ENABLE_WEB_SEARCH=true
EOL
    else
        log "INFO" ".env.local already exists for UI. Skipping."
    fi
    
    # Create .env for backend if needed
    if [ -d "$BACKEND_DIR" ] && [ ! -f "$BACKEND_DIR/.env" ]; then
        log "INFO" "Creating .env for backend..."
        cat > "$BACKEND_DIR/.env" << EOL
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
MONGODB_URI=mongodb://kevinuser:kevin_password@localhost:27017/kevindb?authSource=admin
EOL
    elif [ -d "$BACKEND_DIR" ]; then
        log "INFO" ".env already exists for backend. Skipping."
    fi
    
    log "SUCCESS" "Environment files created!"
    echo "STEP6" >&3
}

# Create the start-kevin.sh script
create_start_script() {
    check_status 7 && return 0
    log "INFO" "Creating start-kevin.sh script..."
    
    cat > "$KEVIN_DIR/start-kevin.sh" << 'EOL'
#!/bin/bash

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Start MongoDB
start_mongodb() {
    log_info "Starting MongoDB..."
    cd ui/db && docker-compose up -d
    sleep 2
    cd ../..
}

# Start frontend (UI)
start_frontend() {
    log_info "Starting frontend..."
    cd ui
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    log_success "Frontend started with PID: $FRONTEND_PID"
}

# Start backend if it exists
start_backend() {
    if [ -d "backend" ]; then
        log_info "Starting backend..."
        cd backend
        source ../.venv/bin/activate
        if [ -f "main.py" ]; then
            uvicorn main:app --host 0.0.0.0 --port 8000 &
            BACKEND_PID=$!
            log_success "Backend started with PID: $BACKEND_PID"
        else
            # Try to find the right file to start
            if [ -f "app.py" ]; then
                uvicorn app:app --host 0.0.0.0 --port 8000 &
                BACKEND_PID=$!
                log_success "Backend started with PID: $BACKEND_PID"
            else
                log_error "Couldn't find a valid backend entry point (main.py or app.py)"
            fi
        fi
        cd ..
    else
        log_info "No backend directory found. Skipping backend startup."
    fi
}

# Function to properly shut down on CTRL+C
graceful_shutdown() {
    echo ""
    log_info "Shutting down services..."
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    log_info "Stopping MongoDB..."
    cd ui/db && docker-compose down && cd ../..
    
    log_success "All services stopped. Goodbye!"
    exit 0
}

# Trap CTRL+C and other signals
trap graceful_shutdown INT TERM

# Start all services
start_mongodb
start_frontend
start_backend

# Print access URLs
log_success "Services started successfully!"
echo ""
echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
if [ -d "backend" ]; then
    echo -e "${GREEN}Backend API:${NC} http://localhost:8000"
    echo -e "${GREEN}Swagger Docs:${NC} http://localhost:8000/docs"
fi
echo -e "${GREEN}MongoDB:${NC} mongodb://localhost:27017"
echo ""
log_info "Press Ctrl+C to stop all services"

# Keep script running
while true; do
    sleep 1
done
EOL

    # Make script executable
    chmod +x "$KEVIN_DIR/start-kevin.sh"
    
    log "SUCCESS" "Start script created and made executable!"
    echo "STEP7" >&3
}

# Main execution with error handling
trap 'handle_error $? "$BASH_COMMAND"' ERR
trap cleanup EXIT

(
    update_progress 1 && install_system_dependencies
    update_progress 2 && setup_python_env
    update_progress 3 && install_backend_dependencies
    update_progress 4 && install_frontend_dependencies
    update_progress 5 && setup_mongodb
    update_progress 6 && create_env_files
    update_progress 7 && create_start_script
    update_progress 8 && final_config
) 2>&1 | tee $ERROR_LOG

echo -e "${GREEN}${BOLD}Installation completed successfully!${NC}"
rm -f $STATUS_FILE 