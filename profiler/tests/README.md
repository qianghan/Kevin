# Profiler API Tests

This directory contains tests for the Profiler API service.

## Test Types

- **Unit Tests**: Individual components in isolation
  - `test_rate_limiter.py`: Tests for the rate limiting middleware
  - `test_basic.py`: Basic unittest tests for the API health endpoint

- **API Tests**: Complete API endpoints and flows
  - `test_api_endpoints.py`: Comprehensive tests for all API endpoints including document analysis, recommendation, and UI flows
  - `test_auth.py`: Authentication and authorization tests
  - `test_health.py`: Health endpoint tests

## Running Tests

### All Tests

Use the `run_tests.py` script at the root of the project:

```bash
# From the profiler directory
./run_tests.py
```

### Specific Tests

You can run individual test files directly:

```bash
# Unit tests
python tests/test_rate_limiter.py
python tests/test_basic.py

# API tests (requires complete environment setup)
python -m pytest tests/test_api_endpoints.py -v

# Run specific test cases
python -m pytest tests/test_api_endpoints.py::test_analyze_document_endpoint -v
python -m pytest tests/test_api_endpoints.py::test_ui_flow_document_to_recommendations -v
```

## Test Structure

- `conftest.py`: Common fixtures and mocks for pytest
- `test_*.py`: Individual test modules
- `data/`: Test data files

## Mock Services

The test suite leverages robust mocking for external services to ensure consistent and reliable test execution:

### Document Service Mock

The document service mock (`mock_document_service` in `conftest.py`) provides:
- Document analysis with realistic validation
- Document type detection
- Proper structure for extracted information
- Validation for empty content and invalid document types

### Recommendation Service Mock

The recommendation service mock (`mock_recommendation_service` in `conftest.py`) provides:
- Recommendation generation with realistic output structure
- Profile summary generation
- Category-based filtering

### QA Service Mock

The QA service mock (`mock_qa_service` in `conftest.py`) provides:
- Question generation
- Answer evaluation
- Context handling for conversation flow

## Key Test Cases

### Document Analysis Tests

- `test_analyze_document_endpoint`: Tests document analysis with various content types
- `test_analyze_document_with_metadata`: Tests document analysis with additional metadata
- Validation tests for empty content and invalid document types

### Recommendation Tests

- `test_recommendations_endpoint`: Tests recommendation generation 
- `test_recommendations_with_categories`: Tests recommendation filtering by categories
- Validation tests for request structure

### UI Flow Tests

- `test_ui_flow_document_to_recommendations`: Tests complete flow from document upload to recommendations
- `test_ui_flow_qa_interaction`: Tests question and answer interaction flow
- `test_ui_flow_profile_summary`: Tests profile summary generation

## Writing New Tests

When adding new functionality to the API, consider:

1. **Unit Tests**: Test individual components thoroughly
2. **Integration Tests**: Verify that components work together
3. **API Tests**: Test the public API endpoints
4. **Edge Cases**: Include tests for error conditions and edge cases
5. **Mock Updates**: Update mock services if new service behaviors are needed

## Coverage Reporting

To generate a coverage report:

```bash
./run_tests.py --coverage
```

Coverage results will be available in the `htmlcov/` directory. 