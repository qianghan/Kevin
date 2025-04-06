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

## Testing

The Profiler API includes a comprehensive test suite to ensure all endpoints function correctly and to prevent regressions.

### Running the Tests

You can run the tests using the provided `run_tests.py` script:

```bash
# Make the script executable (if not already)
chmod +x run_tests.py

# Run all tests
./run_tests.py

# Run tests with coverage report
./run_tests.py --coverage

# Run specific test module
./run_tests.py tests/test_basic.py

# Run tests with different verbosity level (0-3)
./run_tests.py --verbosity 2
```

Alternatively, you can run specific test files directly:

```bash
# Run a specific test file directly
python tests/test_basic.py

# Run endpoint tests with pytest
python -m pytest tests/test_api_endpoints.py -v

# Run specific endpoint tests
python -m pytest tests/test_api_endpoints.py::test_analyze_document_endpoint -v
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test how components work together
- **API Tests**: Test the complete API endpoints

The test suite covers:
- Authentication and authorization
- API endpoint functionality
- Error handling
- Rate limiting
- End-to-end flows
- Document analysis workflows
- Recommendation generation
- Profile summaries
- UI interaction flows

### Mock Services

The test suite includes robust mocking for all services:

- **Document Service**: Mocks document analysis and extraction with proper validation
- **Recommendation Service**: Mocks the recommendation generation process
- **QA Service**: Mocks the question answering functionality

These mocks ensure tests can run without external dependencies while still providing realistic validation.

### Error Handling Testing

The test suite includes specific tests for error handling:
- Validation errors (422 status codes)
- Empty content validation
- Invalid document types
- Authentication errors (401 status codes)
- Rate limiting (429 status codes)

### Creating New Tests

When adding new functionality to the API, be sure to add corresponding tests. Follow these guidelines:

1. Add unit tests for any new utility functions or classes
2. Update integration tests if component interactions change
3. Add API tests for any new endpoints
4. Update existing tests if endpoints' behavior changes
5. Ensure mocks properly simulate real service behavior

## License

MIT 