# Student Profiler

An AI-powered application for building comprehensive student profiles, analyzing documents, and generating personalized recommendations for college applications.

## Architecture

The Student Profiler follows a microservices architecture with a clear separation between frontend and backend components:

```
┌───────────────────┐     ┌───────────────────────────────────────────┐
│                   │     │                                           │
│    Next.js UI     │◄────┤              FastAPI API                  │
│                   │     │                                           │
└───────┬───────────┘     └──────────────────┬────────────────────────┘
        │                                    │
        │                                    │
        ▼                                    ▼
┌───────────────────┐     ┌───────────────────────────────────────────┐
│                   │     │                                           │
│  WebSocket Client │◄────┤           Profile Builder                 │
│                   │     │                                           │
└───────────────────┘     └──────────────────┬────────────────────────┘
                                             │
                                             │
                                             ▼
                          ┌───────────────────────────────────────────┐
                          │                                           │
                          │          Workflow Executor                │
                          │                                           │
                          └──────────────────┬────────────────────────┘
                                             │
                                             │
                                             ▼
                          ┌───────────────────────────────────────────┐
                          │  Services                                 │
                          │                                           │
                          │  ┌───────────┐ ┌───────────┐ ┌──────────┐ │
                          │  │           │ │           │ │          │ │
                          │  │    QA     │ │ Document  │ │Recommender│ │
                          │  │           │ │  Service  │ │          │ │
                          │  └───────────┘ └───────────┘ └──────────┘ │
                          │                                           │
                          └───────────────────────────────────────────┘
```

### Key Components

#### Client-Side
- **Next.js UI**: Interactive frontend written in React/Next.js
- **WebSocket Client**: Real-time communication with the server
- **Service Abstractions**: Type-safe interfaces for backend services
- **React Components**: Modular UI components for profile building, document upload, and recommendations

#### Server-Side
- **FastAPI API**: REST and WebSocket endpoints
- **Profile Builder**: Core logic for profile generation
- **Workflow Executor**: Manages state transitions and service coordination
- **Services**:
  - **QA Service**: Handles question generation and answer processing
  - **Document Service**: Processes uploaded documents
  - **Recommendation Service**: Generates personalized recommendations

### Flow
1. User interacts with the UI to build a profile
2. UI communicates with the backend via WebSocket
3. Backend processes requests through the workflow executor
4. Services handle specialized tasks (QA, document analysis, recommendations)
5. Results are sent back to the UI in real-time

## Recent Changes

### Backend
- Updated API prefix from `/api` to `/api/profiler`
- Improved WebSocket handling with better error recovery
- Fixed workflow execution with proper state management
- Enhanced error handling in WebSocket connections
- Updated configuration validation paths from `services` to `ai_clients`
- Fixed async initialization of document and recommendation services

### Frontend
- Upgraded WebSocket service with automatic reconnection
- Added connection timeout handling (10 seconds)
- Implemented exponential backoff for reconnection attempts
- Enhanced error handling with detailed error messages
- Added message queuing for offline capability
- Updated environment configuration for proper API server connections

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn
- Docker (optional, for containerized deployment)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/student-profiler.git
   cd student-profiler
   ```

2. Set up the backend:
   ```bash
   cd profiler
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd app/ui
   npm install
   ```

4. Configure environment variables:
   - Backend: Copy `config.example.yaml` to `config.yaml` and update values
   - Frontend: Copy `.env.example` to `.env.local` and update values:
     ```
     NEXT_PUBLIC_API_URL=http://localhost:8001
     NEXT_PUBLIC_WS_URL=ws://localhost:8001
     NEXT_PUBLIC_API_KEY=your_api_key
     ```

5. Start the services:
   ```bash
   cd profiler
   ./start_test_env.sh
   ```

6. Access the application:
   - UI: http://localhost:3001
   - API docs: http://localhost:8001/api/profiler/docs

### Stopping Services

To stop all running services:
```bash
pkill -f "uvicorn|next"
```

## Configuration

### Backend Configuration
- Main config: `profiler/config.yaml`
- Environment-specific configs in `profiler/config/`
- Key configuration sections:
  - `ai_clients`: Configuration for AI service connections
  - `services`: Settings for internal services
  - `database`: Database connection details
  - `security`: API keys and authentication settings

### Frontend Configuration
- Environment variables in `.env.local`
- Key configuration options:
  - `NEXT_PUBLIC_API_URL`: Backend API URL
  - `NEXT_PUBLIC_WS_URL`: WebSocket URL
  - `NEXT_PUBLIC_API_KEY`: API key for authentication

## Project Structure

```
profiler/
├── app/                    # Application code
│   ├── backend/            # Backend Python code
│   │   ├── api/            # FastAPI endpoints
│   │   │   ├── main.py     # API entry point
│   │   │   ├── routes/     # API route handlers
│   │   │   └── websocket.py # WebSocket handler
│   │   ├── core/           # Core business logic
│   │   │   ├── services/   # Service implementations
│   │   │   └── workflows/  # Workflow definitions
│   │   └── utils/          # Utility functions
│   └── ui/                 # Frontend code
│       ├── app/            # Next.js app directory
│       ├── components/     # React components
│       ├── lib/            # Frontend libraries
│       │   ├── services/   # Service implementations
│       │   └── hooks/      # React hooks
│       └── public/         # Static assets
├── config/                 # Configuration files
├── tests/                  # Test suite
└── scripts/                # Utility scripts
```

## API Documentation

The API documentation is available at:
- OpenAPI UI: http://localhost:8001/api/profiler/docs
- ReDoc UI: http://localhost:8001/api/profiler/redoc

### Key Endpoints

- `GET /api/profiler/health`: Health check endpoint
- `POST /api/profiler/questions`: Generate questions for profile building
- `POST /api/profiler/document/analyze`: Analyze uploaded documents
- `POST /api/profiler/recommendations`: Generate recommendations based on profile
- `WebSocket /api/ws/{user_id}`: Real-time profile building

## WebSocket Protocol

### Connection
```javascript
const ws = new WebSocket(`${WS_URL}/api/ws/${userId}`);
```

### Message Format
```json
{
  "action": "ACTION_NAME",
  "payload": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

### Actions
- `ANSWER_QUESTION`: Submit an answer to a question
- `REQUEST_SECTION`: Request questions for a specific section
- `VALIDATE_SECTION`: Validate a completed section
- `REQUEST_REVIEW`: Request human review of a section

### Response Format
```json
{
  "type": "STATE_UPDATE",
  "state": {
    "sections": {
      "personal": {
        "status": "active",
        "data": {}
      },
      "academic": {
        "status": "pending",
        "data": {}
      }
    },
    "status": "active",
    "currentQuestion": "What are your career goals?",
    "currentSection": "personal"
  }
}
```

## Development

### Adding a New Service

1. Define the service interface in `app/backend/core/services/interfaces.py`
2. Implement the service in `app/backend/core/services/`
3. Register the service in the service factory
4. Add configuration in `config.yaml`

### Extending Workflows

1. Define new workflow nodes in `app/backend/core/workflows/`
2. Update the workflow graph in `create_profile_workflow()`
3. Add any necessary tools or agents
4. Register the workflow in the workflow executor

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.