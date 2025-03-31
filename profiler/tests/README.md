# Student Profiler Test Suite

This directory contains comprehensive tests for the Student Profiler application. The test suite covers API endpoints, backend services, WebSocket functionality, configuration management, and the DeepSeek client implementation.

## Running Tests

### Prerequisites

- Python 3.8 or higher
- Profiler virtual environment created and activated
- Required test dependencies installed

### Commands

Run all tests:

```bash
pytest profiler/tests
```

Run tests with coverage report:

```bash
pytest profiler/tests --cov=profiler/app/backend --cov-report=html
```

Run specific test files:

```bash
# Test API endpoints
pytest profiler/tests/test_api_endpoints.py

# Test WebSocket functionality
pytest profiler/tests/test_websocket.py

# Test services
pytest profiler/tests/test_services.py

# Test configuration system
pytest profiler/tests/test_config.py

# Test DeepSeek client
pytest profiler/tests/test_deepseek_client.py
```

Run specific test function:

```bash
pytest profiler/tests/test_api_endpoints.py::test_health_endpoint
```

## Test Coverage

The test suite covers:

### API Endpoints (`test_api_endpoints.py`)
- Q&A endpoint (`/ask`)
- Document analysis endpoint (`/analyze-document`)
- Recommendations endpoint (`/recommendations`)
- Profile summary endpoint (`/profile-summary`)
- Health check endpoint (`/health`)
- API key authentication

### WebSocket Functionality (`test_websocket.py`)
- Connection establishment
- Authentication
- Message processing
- State management
- Error handling
- Multiple concurrent connections

### Backend Services (`test_services.py`)
- `QAService`: Processing user input, extracting information, generating follow-up questions
- `DocumentService`: Document analysis, information extraction
- `RecommendationService`: Profile recommendations, section-specific recommendations, profile summaries

### Configuration System (`test_config.py`)
- Loading configuration from files
- Environment variable overrides
- Configuration validation
- Helper functions for accessing configuration values

### DeepSeek Client (`test_deepseek_client.py`)
- Client initialization
- Content generation
- Batch processing
- Error handling
- Response structure

## Mocking

The tests use mocks to isolate components and avoid external API calls:

- `mock_qa_service`: Mock QA service with predefined responses
- `mock_document_service`: Mock document service with predefined analysis results
- `mock_recommendation_service`: Mock recommendation service with predefined recommendations
- `mock_deepseek_client`: Mock DeepSeek R1 client that doesn't make actual API calls

## Adding New Tests

When adding new functionality to the application:

1. Create appropriate test cases that validate the new functionality
2. Ensure tests are isolated using mocks where appropriate
3. Make sure tests cover both success and error cases
4. Maintain test coverage for all API endpoints and core services

For further details on pytest, see the [pytest documentation](https://docs.pytest.org/).

## CI/CD Integration

The test suite is designed to be integrated with CI/CD pipelines, with each test module functioning independently to allow for parallel test execution. 