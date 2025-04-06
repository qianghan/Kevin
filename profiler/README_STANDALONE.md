# Profiler Service (Standalone)

This directory contains the Profiler service, refactored to run independently from the Kevin project.

## Setup and Installation

### Option 1: Using the install script

The simplest way to set up and run the service is to use the provided installation script:

```bash
./install_and_run.sh
```

This will:
1. Create a virtual environment if one doesn't exist
2. Install all required dependencies
3. Install the profiler package in development mode
4. Start the service

### Option 2: Manual setup

If you prefer to do the setup manually:

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the service:
   ```bash
   python run.py
   ```

## Running Tests

To run the tests:

```bash
python -m pytest tests/
```

## Project Structure

- `app/` - The main application package
  - `backend/` - Backend services and API
    - `api/` - FastAPI application
    - `core/` - Core functionality and interfaces
    - `services/` - Service implementations
    - `utils/` - Utility functions and helpers
  - `ui/` - User interface components (if applicable)
- `tests/` - Test suite
- `run.py` - Application entry point
- `setup.py` - Package installation configuration

## Configuration

The service uses a configuration file located at `app/backend/config.yaml`. You can also set configuration values using environment variables with the prefix `PROFILER_`. 