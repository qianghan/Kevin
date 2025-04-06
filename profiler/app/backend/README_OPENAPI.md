# Student Profiler API - OpenAPI Documentation

This directory contains the OpenAPI documentation for the Student Profiler API. The documentation describes all available endpoints, request/response schemas, and authentication requirements.

## Overview

The Student Profiler API provides functionality for:

- Question answering about the profile process
- Document analysis and extraction
- Profile recommendations
- Profile summaries
- Real-time profile building through WebSockets

## Using the OpenAPI Documentation

### Viewing the Documentation

The OpenAPI documentation is available in multiple formats:

1. **Swagger UI** - Available at `/api/docs` in non-production environments
2. **ReDoc** - Available at `/api/redoc` in non-production environments
3. **Raw OpenAPI Schema** - Available in `openapi_doc.yaml`

### Authentication

All API endpoints require authentication using an API key. The API key should be included in the `X-API-Key` header.

Example:
```
X-API-Key: your_api_key_here
```

### Endpoints

The API provides the following main endpoints:

- `/api/ask` - Answer questions about the profile process
- `/api/documents/analyze` - Analyze document content
- `/api/documents/upload` - Upload and analyze a document
- `/api/documents/types` - Get available document types
- `/api/recommendations` - Generate profile recommendations
- `/api/profile-summary` - Generate a comprehensive profile summary
- `/api/health` - Health check endpoint
- `/api/ws/{user_id}` - WebSocket endpoint for real-time interaction

## Validation and Error Handling

The API includes comprehensive validation and robust error handling:

### HTTP Status Codes

- **200 OK** - Successful request
- **401 Unauthorized** - Missing or invalid API key
- **422 Unprocessable Entity** - Validation error (e.g., empty content, invalid document type)
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server-side error

### Validation Errors

Document analysis endpoints validate:
- Document content is not empty
- Document type is valid (one of: "transcript", "essay", "resume", "letter")

Recommendation endpoints validate:
- Profile data structure is valid
- Request is properly formatted with required fields

### Error Response Examples

#### Document Validation Error (422)

```json
{
  "detail": "Document content cannot be empty"
}
```

```json
{
  "detail": "Invalid document type: unknown_type"
}
```

#### Authentication Error (401)

```json
{
  "detail": "Invalid API key"
}
```

#### Rate Limit Error (429)

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

### Examples

#### Analyzing a Document

```
POST /api/documents/analyze
Content-Type: application/json
X-API-Key: your_api_key_here

{
  "content": "Dear Admissions Committee, I am writing to express my interest...",
  "document_type": "cover_letter",
  "user_id": "user123",
  "metadata": {
    "source": "user_upload",
    "filename": "cover_letter.pdf"
  }
}
```

#### Generating Recommendations

```
POST /api/recommendations
Content-Type: application/json
X-API-Key: your_api_key_here

{
  "request": {
    "user_id": "user123",
    "profile_data": {
      "academic": {
        "gpa": 3.8,
        "classes": ["CS101", "MATH202"],
        "achievements": ["Dean's List", "Hackathon Winner"]
      },
      "extracurricular": {
        "activities": ["Chess Club", "Volunteer"]
      }
    }
  }
}
```

Note: The recommendations endpoint expects the profile data to be wrapped in a `request` field as shown above.

## Generating Client Libraries

You can use the OpenAPI document to generate client libraries for various programming languages:

1. Using [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator):

```bash
npx @openapitools/openapi-generator-cli generate -i openapi_doc.yaml -g typescript-fetch -o ./client-typescript
```

2. For Python:

```bash
npx @openapitools/openapi-generator-cli generate -i openapi_doc.yaml -g python -o ./client-python
```

## Updating the Documentation

The OpenAPI document should be updated whenever:

1. New endpoints are added
2. Existing endpoints are modified
3. Request/response schemas change
4. Authentication methods change

## WebSocket Protocol

The WebSocket endpoint at `/api/ws/{user_id}` supports a message-based protocol for real-time interaction during the profile building process.

### Message Types

1. **Client to Server**:
   - `{ "type": "answer", "data": "..." }` - Send an answer to the current question
   - `{ "type": "review_feedback", "data": { "section": "...", "feedback": {...} } }` - Provide feedback on a reviewed section

2. **Server to Client**:
   - `{ "type": "state_update", "data": {...} }` - Update client with latest state
   - `{ "type": "processing", "data": {"message": "..."} }` - Notify client of processing status
   - `{ "type": "ping" }` - Connection check

See the main API documentation for more details on the WebSocket protocol. 