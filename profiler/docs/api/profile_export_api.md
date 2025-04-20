# Profile Export API

This document describes the API endpoints for exporting user profiles in various formats.

## Base URL

All endpoints are prefixed with `/api/profiler`.

## Authentication

All endpoints require authentication using a Bearer token:

```
Authorization: Bearer <token>
```

## Endpoints

### Export Profile

Exports a profile in the specified format.

```
POST /api/profiler/profile/export
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | The ID of the profile to export |
| format | string | Yes | The export format (pdf, docx, html, json, yaml, csv, markdown) |
| template_id | string | No | The ID of the template to use (defaults to standard template) |
| options | object | No | Format-specific options |

#### Request Body Example

```json
{
  "profile_id": "user123-profile456",
  "format": "pdf",
  "template_id": "resume_professional",
  "options": {
    "page-size": "A4",
    "include_photo": true,
    "color_scheme": "professional"
  }
}
```

#### Response

On success, returns a 200 OK response with the exported file as an attachment.

**Headers:**

```
Content-Type: application/pdf (or appropriate MIME type for the requested format)
Content-Disposition: attachment; filename="profile_export_<timestamp>.<extension>"
```

#### Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Profile or template not found |
| 415 | Unsupported Media Type - Requested format not supported |
| 500 | Internal Server Error - Failed to generate export |

#### Error Response Example

```json
{
  "error": "export_error",
  "message": "Failed to generate PDF: Missing required profile section: education",
  "details": {
    "profile_id": "user123-profile456",
    "format": "pdf",
    "missing_sections": ["education"]
  }
}
```

### Export Profile Archive

Exports a profile in multiple formats as a zip archive.

```
POST /api/profiler/profile/export-archive
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | The ID of the profile to export |
| formats | array | Yes | Array of export formats to include |
| template_id | string | No | The ID of the template to use (defaults to standard template) |
| options | object | No | Format-specific options |

#### Request Body Example

```json
{
  "profile_id": "user123-profile456",
  "formats": ["pdf", "docx", "json"],
  "template_id": "resume_professional",
  "options": {
    "pdf": {
      "page-size": "A4"
    },
    "docx": {
      "include_header": false
    }
  }
}
```

#### Response

On success, returns a 200 OK response with the zip archive as an attachment.

**Headers:**

```
Content-Type: application/zip
Content-Disposition: attachment; filename="profile_export_<timestamp>.zip"
```

#### Error Responses

Same as for the Export Profile endpoint.

### Get Available Templates

Retrieves a list of available export templates.

```
GET /api/profiler/profile/export/templates
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| format | string | No | Filter templates by format |

#### Response

```json
{
  "templates": [
    {
      "id": "resume_professional",
      "name": "Professional Resume",
      "description": "Clean professional resume format",
      "formats": ["pdf", "docx", "html"],
      "preview_url": "/api/profiler/profile/export/templates/resume_professional/preview"
    },
    {
      "id": "academic_cv",
      "name": "Academic CV",
      "description": "Comprehensive academic curriculum vitae",
      "formats": ["pdf", "docx"],
      "preview_url": "/api/profiler/profile/export/templates/academic_cv/preview"
    }
  ]
}
```

### Get Template Preview

Returns a preview image of the template.

```
GET /api/profiler/profile/export/templates/{template_id}/preview
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| template_id | string | The ID of the template |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| format | string | No | The format to preview (defaults to pdf) |

#### Response

Returns a 200 OK response with the preview image.

**Headers:**

```
Content-Type: image/png
```

### Create Custom Template

Creates a new custom template.

```
POST /api/profiler/profile/export/templates
```

#### Request Body

```json
{
  "name": "My Custom Template",
  "description": "Personalized template with custom styling",
  "base_template_id": "resume_professional",
  "format": "pdf",
  "styles": {
    "colors": {
      "primary": "#336699",
      "secondary": "#99ccff",
      "text": "#333333"
    },
    "fonts": {
      "heading": "Roboto",
      "body": "Open Sans"
    },
    "layout": {
      "sections_order": ["personal_info", "summary", "skills", "experience", "education"]
    }
  }
}
```

#### Response

```json
{
  "id": "custom_template_123",
  "name": "My Custom Template",
  "description": "Personalized template with custom styling",
  "formats": ["pdf"],
  "preview_url": "/api/profiler/profile/export/templates/custom_template_123/preview",
  "created_at": "2023-06-15T10:30:00Z"
}
```

## Webhooks

### Export Completed Webhook

If configured, this webhook is triggered when a profile export is completed.

**Endpoint:** Configured in account settings

**Payload:**

```json
{
  "event_type": "profile_export_completed",
  "timestamp": "2023-06-15T10:35:22Z",
  "data": {
    "profile_id": "user123-profile456",
    "export_id": "export789",
    "format": "pdf",
    "download_url": "https://example.com/api/profiler/exports/download/export789",
    "expires_at": "2023-06-22T10:35:22Z"
  }
}
```

## Rate Limiting

Export operations are resource-intensive and subject to rate limiting:

- 10 single-format exports per minute per user
- 2 multi-format archive exports per minute per user
- 100 exports per day per user

When rate limits are exceeded, the API returns a 429 Too Many Requests response with a Retry-After header. 