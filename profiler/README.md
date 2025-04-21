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
                          │  │           │ │  Service  │ │ Service  │ │
                          │  └───────────┘ └───────────┘ └────┬─────┘ │
                          │                                    │      │
                          └────────────────────────────────────┼──────┘
                                                               │
                                                               ▼
                          ┌──────────────────────────────────────────┐
                          │                                          │
                          │          University Provider             │
                          │          Interface                       │
                          │                                          │
                          └──────────────────┬───────────────────────┘
                                             │
                                             │
                                             ▼
          ┌───────────────────────────────────────────────────────────┐
          │                                                           │
          │                Kevin University Search API                │
          │                (/api/search/documents)                    │
          │                                                           │
          └───────────────────────────────────────────────────────────┘
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
  - **University Provider**: Interface for retrieving university recommendations from external sources

#### External Services
- **Kevin University Search API**: Provides university recommendations based on student profile data

### Flow
1. User interacts with the UI to build a profile
2. UI communicates with the backend via WebSocket
3. Backend processes requests through the workflow executor
4. Services handle specialized tasks (QA, document analysis, recommendations)
5. Recommendation service queries both internal and external data sources
6. External university recommendations are merged with internal recommendations
7. Results are sent back to the UI in real-time

## Recent Changes

### Backend
- Updated API prefix from `/api` to `/api/profiler`
- Improved WebSocket handling with better error recovery
- Fixed workflow execution with proper state management
- Enhanced error handling in WebSocket connections
- Updated configuration validation paths from `services` to `ai_clients`
- Fixed async initialization of document and recommendation services
- **Added Kevin University API integration** for enhanced university recommendations

### Frontend
- Upgraded WebSocket service with automatic reconnection
- Added connection timeout handling (10 seconds)
- Implemented exponential backoff for reconnection attempts
- Enhanced error handling with detailed error messages
- Added message queuing for offline capability
- Updated environment configuration for proper API server connections

## Kevin API Integration

### Integration Architecture

The integration with Kevin's University API follows SOLID principles with a clean separation of concerns:

```
┌─────────────────────────────────────────┐     ┌─────────────────────────────────┐
│            Profiler System              │     │          Kevin System           │
│                                         │     │                                 │
│  ┌─────────────────────────────────┐    │     │    ┌─────────────────────────┐  │
│  │                                 │    │     │    │                         │  │
│  │     Recommendation Service      │    │     │    │       University API    │  │
│  │                                 │    │     │    │                         │  │
│  └──────────────┬──────────────────┘    │     │    └─────────────┬───────────┘  │
│                 │                        │     │                  │              │
│  ┌──────────────▼──────────────────┐    │     │    ┌─────────────▼───────────┐  │
│  │                                 │    │     │    │                         │  │
│  │  University Provider Interface  │    │     │    │  /api/search/documents  │  │
│  │                                 │◄───┼─────┼────►                         │  │
│  └──────────────┬──────────────────┘    │     │    └─────────────────────────┘  │
│                 │                        │     │                                 │
│  ┌──────────────▼──────────────────┐    │     └─────────────────────────────────┘
│  │                                 │    │
│  │   Kevin University Adapter      │    │
│  │                                 │    │
│  └──────────────┬──────────────────┘    │
│                 │                        │
│  ┌──────────────▼──────────────────┐    │
│  │                                 │    │
│  │   Recommendation Merger         │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

### Key Integration Files

- `providers/university_provider.py`: Interface definition
- `providers/kevin_university_adapter.py`: Implementation for Kevin API
- `mappers/university_mapper.py`: Maps API responses to internal format
- `merger.py`: Merges university recommendations with other recommendations
- `factory.py`: Factory for creating appropriate provider instances
- `service.py`: Enhanced service using the university provider

### Key Integration Code

**University Provider Interface**:
```python
class UniversityProvider(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        pass
        
    @abstractmethod
    async def get_universities(self, profile_data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    async def get_university_details(self, university_id: str) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        pass
```

**Factory Method**:
```python
@staticmethod
async def create_provider(config) -> Optional[UniversityProvider]:
    """Create and return a university provider if configured"""
    logger = logging.getLogger(__name__)
    
    # Check if Kevin integration is enabled
    if config.get("external_services.kevin.enabled", False):
        logger.info("Creating Kevin University Adapter")
        provider = KevinUniversityAdapter(config)
        await provider.initialize()
        return provider
        
    logger.info("No university provider configured")
    return None
```

**Service Integration**:
```python
# Initialize university provider if enabled
self.university_provider = await UniversityProviderFactory.create_provider(self.config)

# In get_recommendations method
if self.university_provider and self._is_profile_complete_enough(profile_state):
    try:
        self.logger.info("Getting university recommendations")
        profile_data = self._extract_university_relevant_data(profile_state)
        university_recs = await self.university_provider.get_universities(profile_data)
        self.logger.info(f"Retrieved {len(university_recs)} university recommendations")
        return await self.recommendation_merger.merge_recommendations(standard_recs, university_recs)
    except Exception as e:
        self.logger.error(f"Error getting university recommendations: {e}")
        # Return standard recommendations if university recs fail
        return standard_recs
```

### Configuration

To enable the Kevin University API integration, add the following to your configuration:

```yaml
external_services:
  kevin:
    enabled: true
    base_url: "http://localhost:5000"  # Kevin API URL
    api_key: "your-api-key-here"
    timeout_seconds: 5
    retry_attempts: 3
```

### Error Handling

The Kevin University API integration is designed with robust error handling to ensure the overall recommendation system remains operational even when the external service is unavailable:

1. **API Unavailability Detection**:
   - Connection timeouts (configurable via `timeout_seconds`)
   - HTTP error status codes
   - Malformed response handling

2. **Graceful Degradation**:
   - When `/api/search/documents` is unavailable, the system falls back to internal recommendations only
   - The main recommendation workflow continues without disruption
   - Users receive standard recommendations without knowing the external service failed

3. **Retry Mechanism**:
   - Configurable retry attempts (`retry_attempts` in config)
   - Exponential backoff between retries
   - Circuit breaker pattern to prevent overwhelming the external service

4. **Error Logging and Monitoring**:
   - Detailed error logs with exception information
   - Service health metrics tracking
   - Administrative alerts for persistent failures

5. **Example Error Handling Code**:
   ```python
   # In the University Adapter implementation
   async def get_universities(self, profile_data, limit=5):
       for attempt in range(self.retry_attempts):
           try:
               response = await self.client.post(
                   f"{self.base_url}/api/search/documents",
                   json=profile_data,
                   timeout=self.timeout_seconds
               )
               return self.mapper.map_universities(response.json())
           except (TimeoutError, ConnectionError) as e:
               self.logger.warning(f"Kevin API connection error (attempt {attempt+1}/{self.retry_attempts}): {e}")
               if attempt < self.retry_attempts - 1:
                   await asyncio.sleep(self._calculate_backoff(attempt))
               else:
                   self.logger.error(f"Kevin API unavailable after {self.retry_attempts} attempts")
                   return []
           except Exception as e:
               self.logger.error(f"Unexpected error querying Kevin API: {e}")
               return []
   ```

This error handling strategy ensures that the Kevin University API integration enhances the recommendation system when available but never compromises the core functionality when unavailable.

## Profile Export System

The Profile Export feature allows users to export their profiles in various formats for different purposes.

### Architecture

The Profile Export system follows SOLID principles with a clean interface-based design:

```
┌─────────────────────────────┐     ┌─────────────────────────────┐
│                             │     │                             │
│     Profile Service         │     │      Template System        │
│                             │     │                             │
└──────────────┬──────────────┘     └──────────────┬──────────────┘
               │                                    │
               │                                    │
               ▼                                    ▼
┌─────────────────────────────┐     ┌─────────────────────────────┐
│                             │     │                             │
│  ProfileExportInterface     │     │     Template Repository     │
│                             │     │                             │
└──────────────┬──────────────┘     └──────────────┬──────────────┘
               │                                    │
               │                                    │
               ▼                                    ▼
┌─────────────────────────────┐     ┌─────────────────────────────┐
│                             │     │                             │
│   ProfileExportService      │◄────┤     Template Renderer       │
│                             │     │                             │
└──────────────┬──────────────┘     └──────────────┬──────────────┘
               │                                    │
               │                                    │
               ▼                                    ▼
┌─────────────────────────────┐     ┌─────────────────────────────┐
│                             │     │                             │
│     Export Formatters       │     │      Export Storage         │
│ (PDF, DOCX, HTML, JSON...)  │     │                             │
│                             │     │                             │
└─────────────────────────────┘     └─────────────────────────────┘
```

### Key Features

- **Multiple Export Formats**: PDF, DOCX, HTML, JSON, YAML, CSV, and Markdown
- **Template Customization**: Default and custom templates for different purposes
- **Batch Export**: Export profiles in multiple formats at once
- **Profile Sharing**: Share exported profiles via email or links
- **Preview Generation**: Preview exports before downloading

### API Endpoints

- `POST /api/profiler/profile/export`: Export profile in a specific format
- `POST /api/profiler/profile/export-archive`: Export profile in multiple formats
- `GET /api/profiler/profile/export/templates`: Get available templates
- `GET /api/profiler/profile/export/templates/{id}/preview`: Preview a template
- `POST /api/profiler/profile/export/templates`: Create a custom template

### Implementation Details

The Profile Export service is implemented using:

- `jinja2` for template rendering
- `pdfkit` and `weasyprint` for PDF generation
- `python-docx` for DOCX files
- `markdown` for text formatting
- `zipfile` for archive creation

For complete details, see the [Profile Export User Guide](docs/profile_export_guide.md) and [API Documentation](docs/api/profile_export_api.md).

## Recommendation Engine Architecture

The Recommendation Engine is a core component of the Profiler system, designed to provide personalized, actionable recommendations to users based on their profile data, document content, and Q&A interactions.

### Core Components

1. **IRecommendationService**: The primary interface that defines the contract for recommendation operations.
2. **RecommendationService**: Implementation of the recommendation service that coordinates between data sources and recommendation generation.
3. **RecommendationCategory**: Enum defining different types of recommendations (SKILL, EXPERIENCE, EDUCATION, etc.).
4. **Recommendation**: Data model representing individual recommendations with properties like priority, steps, and progress tracking.

### Integration Points

- **Profile Service**: Sources user profile data to contextualize recommendations
- **Document Service**: Uses document content to generate document-based recommendations
- **Q&A Service**: Triggers recommendations based on user responses to questions
- **Notification Service**: Delivers recommendation notifications to users

### Recommendation Generation Flow

1. Data collection from integrated services
2. Analysis of user context and history
3. Application of personalization algorithms
4. Prioritization of potential recommendations
5. Generation of detailed action steps
6. Delivery to user with notification

### Key Features

- Personalized recommendation paths
- Detailed action steps for each recommendation
- Progress tracking for ongoing recommendations
- Recommendation history and analytics
- Peer comparison insights

For detailed implementation information and test results, see [Understanding the Recommendation Engine](profiler/docs/understand_recommendation_engine.md).

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
  - `external_services`: External API integrations (e.g., Kevin)

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
│   │   ├── services/       # Service implementations
│   │   │   ├── recommendation/ # Recommendation services
│   │   │   │   ├── providers/  # University provider implementations
│   │   │   │   ├── mappers/    # Data mapping classes
│   │   │   │   ├── factory.py  # Provider factory
│   │   │   │   ├── merger.py   # Recommendation merger
│   │   │   │   └── service.py  # Main service implementation
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

### Adding a New University Provider

1. Create a new class that implements the `UniversityProvider` interface
2. Add a factory method to create the provider based on configuration
3. Add necessary mappers for the provider's data format
4. Update the configuration to enable the new provider

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

## Features

- Profile creation and management
- Document upload and analysis
- Interactive Q&A for profile building
- Personalized recommendations
- Profile export in multiple formats
- Data persistence with PostgreSQL or JSON files

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- npm 8+
- Docker and docker-compose (for PostgreSQL container)

### Installation

1. Clone the repository
2. Install Python dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Install UI dependencies:
```bash
cd app/ui
npm install
```

### Running the Application

Use the provided startup script:

```bash
./start_test_env.sh
```

This script will:
1. Start a PostgreSQL Docker container for data persistence
2. Start the API server with WebSocket support
3. Start the UI development server

## Database Configuration

### PostgreSQL (Recommended)

The application uses PostgreSQL for data persistence by default. The database is automatically configured and started as a Docker container when running the application with `start_test_env.sh`.

Configuration is handled through the `config.yaml` file:

```yaml
database:
  type: "postgresql"
  url: "postgresql+asyncpg://postgres:postgres@localhost:5432/profiler"
  pool_size: 20
  max_overflow: 10
```

You can also use the following environment variables to override the database configuration:

- `PROFILER_DATABASE__URL`: Full PostgreSQL connection URL
- `PROFILER_DATABASE__POOL_SIZE`: Connection pool size
- `PROFILER_DATABASE__MAX_OVERFLOW`: Maximum overflow connections
- `PROFILER_PROFILE_SERVICE__REPOSITORY_TYPE`: Set to "postgresql" to use PostgreSQL

### JSON File Storage (Alternative)

For development or testing, you can use JSON file storage instead of PostgreSQL by setting:

```yaml
profile_service:
  repository_type: "json_file"
  storage_dir: "./data/profiles"
```

### Migrating Data

To migrate profiles from JSON files to PostgreSQL:

```bash
python -m profiler.scripts.migrate_profiles --source json --destination postgresql
```

## Development

### Testing

Run the PostgreSQL migration test:

```bash
./scripts/test_migration.sh
```

Run the PostgreSQL connection test:

```bash
python scripts/test_postgres_connection.py
```

Run the unit tests:

```bash
pytest tests/
```

### Docker Integration

The application includes Docker support for the PostgreSQL database. The Docker configuration is defined in `docker-compose.yml`.

To manually start the PostgreSQL container:

```bash
docker-compose up -d postgres
```

## Architecture

The application follows a layered architecture:

- **UI Layer**: React/Next.js frontend
- **API Layer**: FastAPI backend with WebSocket support
- **Service Layer**: Business logic components
- **Repository Layer**: Data access layer with PostgreSQL and JSON implementations
- **Domain Layer**: Core domain models and interfaces

The persistence layer follows the Repository Pattern, providing abstraction over different storage mechanisms.