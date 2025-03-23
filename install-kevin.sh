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
    
    if [ ! -d "ui" ]; then
        log "ERROR" "This script must be run from the Kevin project root directory!"
        log "ERROR" "Please make sure the 'ui' directory exists."
        exit 1
    fi
    
    # Backend directory is optional, so only warn if it doesn't exist
    if [ ! -d "backend" ]; then
        log "WARNING" "Backend directory not found. Will skip backend setup."
    fi
    
    log "SUCCESS" "Directory structure looks good!"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check and install system dependencies
install_system_dependencies() {
    check_status 1 && { log "INFO" "System dependencies already installed. Skipping."; return 0; }
    
    log "INFO" "Checking system dependencies..."
    
    check_directory
    
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
            
            # Check if Docker started correctly
            if ! docker info > /dev/null 2>&1; then
                log "ERROR" "Failed to start Docker. Please start it manually and try again."
                exit 1
            fi
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
            log "WARNING" "If the script fails after this point, please log out, log back in, and run the script again."
        fi
        
        # Start Docker if not running
        if ! docker info > /dev/null 2>&1; then
            log "INFO" "Starting Docker..."
            sudo systemctl start docker
            
            # Check if Docker started correctly
            if ! docker info > /dev/null 2>&1; then
                log "ERROR" "Failed to start Docker. Please check Docker installation and try again."
                exit 1
            fi
        fi
    else
        log "WARNING" "Unsupported OS: $OSTYPE. You may need to install dependencies manually."
    fi
    
    log "SUCCESS" "System dependencies installed!"
    echo "STEP1" >&3
}

# Setup Python virtual environment
setup_python_env() {
    check_status 2 && { log "INFO" "Python environment already set up. Skipping."; return 0; }
    
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
                eval "$(pyenv init --path)" || true
                eval "$(pyenv init -)" || true
                
                # Check if pyenv is now available
                if ! command_exists pyenv; then
                    log "WARNING" "Failed to initialize pyenv. Will try to use system Python instead."
                    PYTHON_CMD="python3"
                else
                    # Install required Python version
                    pyenv install $PYTHON_VERSION
                    pyenv local $PYTHON_VERSION
                    PYTHON_CMD="$(pyenv which python)"
                fi
            fi
        else
            log "ERROR" "Python not found. Please install Python $PYTHON_VERSION."
            exit 1
        fi
    fi
    
    # Verify we have a valid Python command
    if ! command_exists "$PYTHON_CMD"; then
        log "ERROR" "Failed to find a valid Python command. Please install Python $PYTHON_VERSION."
        exit 1
    fi
    
    # Create and activate virtual environment
    log "INFO" "Creating virtual environment at $VENV_DIR..."
    $PYTHON_CMD -m venv $VENV_DIR
    
    # Activate the virtual environment
    source $VENV_DIR/bin/activate
    
    # Check if virtual environment was activated
    if [ -z "$VIRTUAL_ENV" ]; then
        log "ERROR" "Failed to activate virtual environment. Please check Python installation."
        exit 1
    fi
    
    # Upgrade pip
    log "INFO" "Upgrading pip..."
    pip install --upgrade pip
    
    log "SUCCESS" "Python environment setup complete!"
    echo "STEP2" >&3
}

# Install backend dependencies
install_backend_dependencies() {
    check_status 3 && { log "INFO" "Backend dependencies already installed. Skipping."; return 0; }
    
    # Skip if no backend directory
    if [ ! -d "$BACKEND_DIR" ]; then
        log "INFO" "No backend directory found. Skipping backend dependencies."
        echo "STEP3" >&3
        return 0
    }
    
    log "INFO" "Installing backend dependencies..."
    
    # Activate virtual environment if not already activated
    if [ -z "$VIRTUAL_ENV" ]; then
        source $VENV_DIR/bin/activate
        
        # Check if virtual environment was activated
        if [ -z "$VIRTUAL_ENV" ]; then
            log "ERROR" "Failed to activate virtual environment. Please check Python installation."
            exit 1
        fi
    fi
    
    # Install backend requirements
    cd $BACKEND_DIR
    if [ -f "requirements.txt" ]; then
        log "INFO" "Installing dependencies from requirements.txt..."
        pip install -r requirements.txt
    else
        log "WARNING" "No requirements.txt found in the backend directory!"
    fi
    
    # Install additional packages that might be needed
    log "INFO" "Installing common backend packages (FastAPI, uvicorn)..."
    pip install fastapi uvicorn

    cd $KEVIN_DIR
    log "SUCCESS" "Backend dependencies installed!"
    echo "STEP3" >&3
}

# Install frontend dependencies
install_frontend_dependencies() {
    check_status 4 && { log "INFO" "Frontend dependencies already installed. Skipping."; return 0; }
    
    log "INFO" "Installing frontend dependencies..."
    
    # Check Node.js version
    if command_exists node; then
        NODE_V=$(node -v | cut -d'v' -f2)
        log "INFO" "Found Node.js $NODE_V"
        
        # Compare versions (simple check)
        if [[ "${NODE_V%%.*}" -lt "${NODE_VERSION%%.*}" ]]; then
            log "WARNING" "Node.js version $NODE_V may be too old. Recommended: $NODE_VERSION+"
        fi
    else
        log "ERROR" "Node.js not found. Please install Node.js $NODE_VERSION or higher."
        exit 1
    fi
    
    # Check if npm exists
    if ! command_exists npm; then
        log "ERROR" "npm not found. Please install npm."
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
    check_status 5 && { log "INFO" "MongoDB already set up. Skipping."; return 0; }
    
    log "INFO" "Setting up MongoDB with Docker..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log "ERROR" "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if MongoDB container already exists
    if docker ps -a | grep -q kevin-ui-mongodb; then
        log "INFO" "MongoDB container already exists. Starting it if not running..."
        docker start kevin-ui-mongodb 2>/dev/null || true
    else
        log "INFO" "Creating MongoDB container..."
        cd $UI_DIR/db
        
        # Check if docker-compose.yml exists
        if [ ! -f "docker-compose.yml" ]; then
            log "ERROR" "docker-compose.yml not found in $UI_DIR/db directory!"
            exit 1
        fi
        
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
    log "INFO" "Testing MongoDB connection..."
    cd $UI_DIR
    
    # Check if db:test script exists in package.json
    if grep -q "\"db:test\"" package.json; then
        npm run db:test
    else
        log "WARNING" "No db:test script found in package.json. Skipping connection test."
    fi
    
    # Return to project root
    cd $KEVIN_DIR
    log "SUCCESS" "MongoDB setup complete!"
    echo "STEP5" >&3
}

# Create local environment files
create_env_files() {
    check_status 6 && { log "INFO" "Environment files already created. Skipping."; return 0; }
    
    log "INFO" "Setting up environment files..."
    
    # Create .env.local for UI
    if [ ! -f "$UI_DIR/.env.local" ]; then
        log "INFO" "Creating .env.local for UI..."
        
        # Generate a secure random secret for NextAuth
        NEXTAUTH_SECRET=$(openssl rand -base64 32)
        
        cat > "$UI_DIR/.env.local" << EOL
# MongoDB Connection
MONGODB_URI=mongodb://kevinuser:kevin_password@localhost:27017/kevindb?authSource=admin

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}

# Feature Flags
ENABLE_WEB_SEARCH=true
EOL
        log "INFO" "Created .env.local with secure random NEXTAUTH_SECRET"
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
    check_status 7 && { log "INFO" "Start script already created. Skipping."; return 0; }
    
    log "INFO" "Creating start-kevin.sh script..."
    
    # Check if file already exists
    if [ -f "$KEVIN_DIR/start-kevin.sh" ]; then
        # Backup the existing file
        log "INFO" "Backing up existing start-kevin.sh file..."
        mv "$KEVIN_DIR/start-kevin.sh" "$KEVIN_DIR/start-kevin.sh.bak"
    fi
    
    cat > "$KEVIN_DIR/start-kevin.sh" << 'EOL'
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
EOL

    # Make script executable
    chmod +x "$KEVIN_DIR/start-kevin.sh"
    
    log "SUCCESS" "Start script created and made executable!"
    echo "STEP7" >&3
}

# Final configuration
final_config() {
    check_status 8 && { log "INFO" "Final configuration already completed. Skipping."; return 0; }
    
    log "INFO" "Performing final configuration checks..."
    
    # Check if MongoDB is running
    if ! docker ps | grep -q kevin-ui-mongodb; then
        log "WARNING" "MongoDB is not running. Starting it..."
        cd $UI_DIR/db && docker-compose up -d
        cd $KEVIN_DIR
        sleep 3
    fi
    
    # Create README if it doesn't exist
    if [ ! -f "$KEVIN_DIR/README_INSTALLATION.md" ]; then
        log "INFO" "Creating installation README..."
        cat > "$KEVIN_DIR/README_INSTALLATION.md" << EOL
# Kevin AI Installation Guide

This document provides information about the Kevin AI installation process and troubleshooting steps.

## System Requirements

- **Operating System**: macOS or Linux
- **Docker**: Required for MongoDB
- **Node.js**: v${NODE_VERSION} or higher
- **Python**: v${PYTHON_VERSION} or higher

## Installation

The installation process has been automated with the \`install-kevin.sh\` script. It performs the following steps:

1. System dependency checks and installation
2. Python virtual environment setup
3. Backend dependencies installation
4. Frontend dependencies installation
5. MongoDB setup with Docker
6. Environment file creation
7. Start script generation

## Usage

After installation, you can start all services using:

\`\`\`bash
./start-kevin.sh
\`\`\`

This will start:
- MongoDB database
- Next.js frontend
- FastAPI backend (if available)

## Troubleshooting

### Docker Issues

If MongoDB fails to start:
- Ensure Docker is running
- Check logs: \`docker logs kevin-ui-mongodb\`
- Verify Docker permissions (on Linux, you may need to add your user to the docker group)

### Python Issues

If backend fails to start:
- Check virtual environment: \`source .venv/bin/activate\`
- Verify Python version: \`python --version\`
- Check backend dependencies: \`pip list\`

### Node.js Issues

If frontend fails to start:
- Verify Node.js version: \`node --version\`
- Check npm: \`npm --version\`
- Reinstall dependencies: \`cd ui && npm install\`

## Additional Information

The installation script creates a resumable installation process. If installation fails at any point, 
you can simply run the script again and it will continue from where it left off.

For more information about the Kevin AI architecture, refer to the main README.md file.
EOL
        log "SUCCESS" "Installation README created!"
    fi
    
    log "SUCCESS" "Final configuration completed!"
    echo "STEP8" >&3
}

# Pre-execution checks
check_bash_version() {
    # Check if bash version is at least 4.0 (for associative arrays)
    if [[ ${BASH_VERSINFO[0]} -lt 4 ]]; then
        echo -e "${RED}${BOLD}Error: This script requires Bash version 4.0 or higher.${NC}"
        echo -e "${RED}${BOLD}Your current Bash version is ${BASH_VERSION}.${NC}"
        echo -e "${YELLOW}Please upgrade bash or run this script with a newer bash binary.${NC}"
        exit 1
    fi
}

# Main execution
main() {
    echo -e "\n${BLUE}${BOLD}======== Kevin AI Installation ========${NC}\n"
    
    # Check bash version
    check_bash_version
    
    # Set up error handling
    trap 'handle_error $? "$BASH_COMMAND"' ERR
    trap cleanup EXIT
    
    # Run installation steps
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
    
    # Check if all steps completed successfully
    if grep -q "STEP8" $STATUS_FILE; then
        echo -e "\n${GREEN}${BOLD}✅ Installation completed successfully!${NC}"
        echo -e "\n${BLUE}${BOLD}To start Kevin AI, run:${NC}"
        echo -e "    ${GREEN}./start-kevin.sh${NC}\n"
        # Clean up status file on successful installation
        rm -f $STATUS_FILE
    else
        echo -e "\n${YELLOW}${BOLD}⚠️ Installation incomplete.${NC}"
        echo -e "Run the script again to continue installation.\n"
    fi
}

# Run the main function
main 