# Document Management API

## Overview
This document describes the REST API endpoints for document management operations.

## Authentication
All API endpoints require authentication using a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Base URL
```
https://api.profiler.com/v1
```

## Endpoints

### Documents

#### List Documents
```
GET /documents
```
Query Parameters:
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 20)
- `sort` (string): Sort field (default: created_at)
- `order` (string): Sort order (asc/desc)
- `category` (string): Filter by category
- `tag` (string): Filter by tag
- `folder` (string): Filter by folder

Response:
```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "size": "integer",
      "created_at": "string",
      "updated_at": "string",
      "categories": ["string"],
      "tags": ["string"],
      "folder": "string"
    }
  ],
  "pagination": {
    "total": "integer",
    "page": "integer",
    "limit": "integer"
  }
}
```

#### Get Document
```
GET /documents/{id}
```
Response:
```json
{
  "id": "string",
  "name": "string",
  "type": "string",
  "size": "integer",
  "created_at": "string",
  "updated_at": "string",
  "metadata": {
    "author": "string",
    "description": "string",
    "keywords": ["string"]
  },
  "permissions": {
    "read": ["string"],
    "write": ["string"],
    "admin": ["string"]
  }
}
```

#### Upload Document
```
POST /documents
```
Headers:
- `Content-Type: multipart/form-data`

Body:
- `file` (file): Document file
- `name` (string): Document name
- `category` (string): Category ID
- `tags` (string[]): Array of tag IDs
- `folder` (string): Folder ID
- `metadata` (object): Additional metadata

Response:
```json
{
  "id": "string",
  "name": "string",
  "type": "string",
  "size": "integer",
  "created_at": "string"
}
```

#### Update Document
```
PUT /documents/{id}
```
Body:
```json
{
  "name": "string",
  "category": "string",
  "tags": ["string"],
  "folder": "string",
  "metadata": {
    "author": "string",
    "description": "string",
    "keywords": ["string"]
  }
}
```

#### Delete Document
```
DELETE /documents/{id}
```

### Document Versions

#### List Versions
```
GET /documents/{id}/versions
```
Response:
```json
{
  "data": [
    {
      "version": "string",
      "created_at": "string",
      "created_by": "string",
      "size": "integer",
      "changes": "string"
    }
  ]
}
```

#### Get Version
```
GET /documents/{id}/versions/{version}
```
Response:
```json
{
  "version": "string",
  "created_at": "string",
  "created_by": "string",
  "size": "integer",
  "changes": "string",
  "content": "string"
}
```

#### Create Version
```
POST /documents/{id}/versions
```
Body:
- `file` (file): New version file
- `changes` (string): Description of changes

#### Rollback Version
```
POST /documents/{id}/versions/{version}/rollback
```

### Document Sharing

#### Share Document
```
POST /documents/{id}/share
```
Body:
```json
{
  "type": "string", // "link" or "email"
  "recipients": ["string"],
  "permission": "string", // "read", "write", "admin"
  "expires_at": "string"
}
```

#### List Shares
```
GET /documents/{id}/shares
```
Response:
```json
{
  "data": [
    {
      "id": "string",
      "type": "string",
      "recipient": "string",
      "permission": "string",
      "created_at": "string",
      "expires_at": "string"
    }
  ]
}
```

#### Revoke Share
```
DELETE /documents/{id}/shares/{share_id}
```

### Document Search

#### Search Documents
```
GET /documents/search
```
Query Parameters:
- `q` (string): Search query
- `type` (string): Document type
- `date_from` (string): Start date
- `date_to` (string): End date
- `size_from` (integer): Minimum size
- `size_to` (integer): Maximum size

Response:
```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "score": "float",
      "highlights": {
        "content": ["string"],
        "metadata": ["string"]
      }
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {
      "field": "string",
      "reason": "string"
    }
  }
}
```

### 401 Unauthorized
```json
{
  "error": {
    "code": "unauthorized",
    "message": "Authentication required"
  }
}
```

### 403 Forbidden
```json
{
  "error": {
    "code": "forbidden",
    "message": "Insufficient permissions"
  }
}
```

### 404 Not Found
```json
{
  "error": {
    "code": "not_found",
    "message": "Resource not found"
  }
}
```

### 500 Internal Server Error
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected error occurred"
  }
}
``` 