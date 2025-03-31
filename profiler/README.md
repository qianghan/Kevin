# Student Profiler

A full-stack application for building student profiles with AI assistance.

## Overview

The Student Profiler consists of:

1. **Backend**: FastAPI server with:
   - Configuration management
   - DeepSeek R1 API integration
   - Document analysis
   - Profile recommendations
   - WebSocket real-time communication

2. **Frontend**: Next.js UI with:
   - Real-time profile building
   - Service abstractions
   - Document uploads
   - Profile quality scoring

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- npm or yarn

### Setup

1. Clone the repository
2. Run the setup script to create a virtual environment and install dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

3. Activate the virtual environment:

```bash
source profiler/bin/activate
```

4. Update the configuration in `profiler/app/backend/config.yaml` with your API keys and settings.

### Environment Variables

You can override configuration settings using environment variables:

```bash
# Set API key for DeepSeek
export PROFILER_SERVICES__DEEPSEEK__API_KEY=your_api_key_here

# Set API server port
export PROFILER_API__PORT=8000
```

## Usage

The profiler service manager provides an easy way to start, stop and monitor services:

### Starting Services

```bash
# Start all services
python profiler.py start

# Start only the API server
python profiler.py start api

# Start only the UI server
python profiler.py start ui
```

### Stopping Services

```bash
# Stop all services
python profiler.py stop

# Stop only the API server
python profiler.py stop api
```

### Checking Status

```bash
python profiler.py status
```

### Viewing Logs

```bash
# View API server logs
python profiler.py logs api

# Follow UI server logs
python profiler.py logs ui -f

# View last 100 lines of API logs
python profiler.py logs api -n 100
```

### Cleaning Up

```bash
# Clean log files
python profiler.py clean --logs

# Clean PID files
python profiler.py clean --pids

# Clean everything
python profiler.py clean --all
```

## Configuration

The Student Profiler uses a YAML-based configuration system with environment variable overrides.

### Configuration File Location

The system looks for a `config.yaml` file in the following locations (in order):

1. The backend directory
2. A `config` subdirectory in the backend directory
3. `/etc/profiler/config.yaml`

### Environment Variable Overrides

Override any configuration value using environment variables:

- Variables must be prefixed with `PROFILER_`
- Use double underscore (`__`) as a separator for nested keys
- Example: `PROFILER_SERVICES__DEEPSEEK__API_KEY=your_api_key`

## Project Structure

```
profiler/
├── app/
│   ├── backend/           # FastAPI backend
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core functionality
│   │   ├── services/      # Service layer
│   │   └── utils/         # Utility functions
│   └── ui/                # Next.js UI
│       ├── components/    # React components
│       ├── lib/           # UI libraries
│       └── app/           # Next.js app directory
├── logs/                  # Log files
├── profiler.py            # Service manager
└── setup.sh               # Setup script
```

## Development

### Backend Development

Make changes to the FastAPI backend code in `profiler/app/backend/`. The development server will automatically reload when changes are detected.

### Frontend Development

Make changes to the Next.js frontend code in `profiler/app/ui/`. The development server will automatically reload when changes are detected.

## License

MIT 