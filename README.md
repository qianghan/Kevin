# Kevin AI

Kevin AI is a comprehensive chat application with advanced features including web search, session management, and streaming responses. It consists of a modern Next.js frontend and an optional FastAPI backend.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Automated Installation](#automated-installation)
  - [Manual Installation](#manual-installation)
  - [Environment Variables](#environment-variables)
  - [Installation Scripts](#installation-scripts)
- [Usage](#usage)
  - [Starting Kevin](#starting-kevin)
  - [Stopping Kevin](#stopping-kevin)
- [Architecture](#architecture)
  - [Frontend](#frontend)
  - [Backend](#backend)
  - [Database](#database)
- [Development](#development)
  - [Directory Structure](#directory-structure)
  - [Frontend Development](#frontend-development)
  - [Backend Development](#backend-development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- Modern React UI built with Next.js
- Real-time streaming chat responses
- Multiple authentication methods
- Session persistence with MongoDB
- Web search integration
- Context summarization
- Responsive design for all devices
- Comprehensive error handling

## Installation

### Prerequisites

Before installing, ensure you have the following installed on your system:

- Git
- Node.js (v18 or higher)
- Python 3.10 or higher (for the backend)
- Docker and Docker Compose (for MongoDB)

### Automated Installation

We provide an automated installation script that handles all setup steps for you:

1. Clone the repository:
```bash
   git clone https://github.com/yourusername/kevin.git
   cd kevin
```

2. Run the installation script:
```bash
   ./install-kevin.sh
   ```

The script will:
- Check and install required system dependencies
- Set up Python virtual environment with the correct version
- Install backend dependencies
- Install frontend dependencies
- Set up MongoDB with Docker
- Create necessary environment files
- Create a convenient startup script
- Initialize basic project structure if needed

The installation script is designed to work immediately after cloning the repository without requiring any additional setup steps.

### Manual Installation

If you prefer to install manually, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/kevin.git
   cd kevin
   ```

2. **Set up the frontend**:
```bash
   cd ui
   npm install
   ```

3. **Set up MongoDB**:
```bash
   cd db
   mkdir -p data
   docker-compose up -d
   ```

4. **Set up the backend** (if applicable):
```bash
   cd ../../backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Create environment files**:
   
   Create a `.env.local` file in the `ui` directory:
   ```
   MONGODB_URI=mongodb://kevinuser:kevin_password@localhost:27017/kevindb?authSource=admin
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=supersecretkeyfornextauth
   ENABLE_WEB_SEARCH=true
   ```
   
   If using the backend, create a `.env` file in the `backend` directory:
   ```
   API_HOST=0.0.0.0
   API_PORT=8000
   MONGODB_URI=mongodb://kevinuser:kevin_password@localhost:27017/kevindb?authSource=admin
   ```

### Environment Variables

**Frontend (UI) Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | mongodb://kevinuser:kevin_password@localhost:27017/kevindb?authSource=admin |
| `NEXTAUTH_URL` | NextAuth base URL | http://localhost:3000 |
| `NEXTAUTH_SECRET` | Secret for NextAuth session encryption | (required) |
| `ENABLE_WEB_SEARCH` | Enable web search functionality | true |

**Backend Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | Host to bind the API server | 0.0.0.0 |
| `API_PORT` | Port for the API server | 8000 |
| `MONGODB_URI` | MongoDB connection string | (same as frontend) |

### Installation Scripts

The Kevin AI project includes two main scripts to automate installation and startup:

#### 1. `install-kevin.sh`

This script handles the complete installation process:

```bash
./install-kevin.sh
```

Key functions:
- **Enhanced project initialization**: Creates required directory structure and basic components
- **System dependency detection**: Identifies and installs required system packages
- **Python environment setup**: Creates a virtual environment with the correct Python version
- **Database setup**: Configures MongoDB with Docker, including automatic creation of Docker configuration
- **Frontend setup**: Installs all Node.js dependencies and creates placeholder components if needed
- **Backend setup**: Installs Python dependencies and creates starter files if needed
- **Environment configuration**: Creates default `.env` files
- **Resumable installation**: Can be restarted if interrupted and will continue from the last completed step

The script is designed to work on both macOS and Linux environments, with detailed logging and visual progress indicators to help troubleshoot any issues during installation.

#### 2. `start-kevin.sh`

This script manages the startup and shutdown of all Kevin services:

```bash
./start-kevin.sh
```

Key functions:
- **Service orchestration**: Starts MongoDB, frontend, and backend in the correct order
- **Enhanced visual interface**: Includes color-coded service status indicators and clear separation between services
- **Keyboard shortcuts**: Press 'q' to gracefully stop all services
- **Health monitoring**: Verifies all services are running correctly with real-time status updates
- **Thorough cleanup**: Ensures all processes are terminated and ports are released during shutdown
- **Process verification**: Checks for port conflicts and orphaned processes
- **Status reporting**: Displays the current state of all services with visual indicators
- **Unified logging**: Combines logs from all services with distinctive formatting

Both scripts include extensive error handling and detailed logging with visual indicators to ensure a smooth installation and startup experience.

## Usage

### Starting Kevin

After installation, you can start all services using the provided script:

```bash
./start-kevin.sh
```

This will start:
- MongoDB database
- Next.js frontend
- FastAPI backend (if available)

The services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000 (if available)
- Backend API Docs: http://localhost:8000/docs (if available)
- MongoDB: mongodb://localhost:27017

### Stopping Kevin

To stop all services, you have two options:

1. Press the `q` key in the terminal where `start-kevin.sh` is running
2. Press `Ctrl+C` in the terminal where `start-kevin.sh` is running

The script will perform a graceful shutdown of all services, with thorough process termination checks and port release verification to ensure complete cleanup.

## Architecture

Kevin AI follows a modular architecture that separates concerns between the frontend, backend, and database.

### Frontend

The frontend is built with Next.js and follows a component-based architecture. It uses:

- React for UI components
- NextAuth.js for authentication
- MongoDB adapter for session persistence
- EventSource for streaming responses

For more details on the frontend architecture, see [UI Architecture](ui/README.md).

### Backend

The backend is built with FastAPI and provides:

- Chat query processing
- Session management
- Streaming response capabilities
- Web search integration

### Database

Kevin uses MongoDB for data persistence, storing:

- User accounts
- Chat sessions
- Messages
- Application state

## Development

### Directory Structure

```
kevin/
├── ui/                 # Frontend application
│   ├── app/            # Next.js app router
│   ├── features/       # Feature modules
│   ├── lib/            # Shared libraries
│   └── db/             # Database setup
├── backend/            # Backend API (optional)
│   ├── app/            # Application modules
│   └── api/            # API endpoints
├── install-kevin.sh    # Installation script
└── start-kevin.sh      # Startup script
```

### Frontend Development

To develop the frontend in isolation:

```bash
cd ui
npm run dev
```

### Backend Development

To develop the backend in isolation:

```bash
cd backend
source ../.venv/bin/activate  # On Windows: ..\.venv\Scripts\activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting

**MongoDB connection issues:**
- Ensure Docker is running
- Check MongoDB logs: `docker logs kevin-ui-mongodb`
- Verify connection string in environment files

**Frontend issues:**
- Check Next.js logs
- Verify Node.js version (v18+ required)
- Make sure all dependencies are installed: `cd ui && npm install`

**Backend issues:**
- Verify Python version (3.10+ required)
- Check virtual environment activation
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check for errors in the backend logs

## License

[MIT License](LICENSE)

---

For more detailed information about the UI architecture, refer to the [UI README](ui/README.md). 