# Template Rendering Process

This document describes the template rendering process used by the Profile Export service.

## Overview

The template rendering process transforms a user's profile data into a formatted document using a template system. This process ensures consistent styling while allowing for customization.

## Process Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Profile Data   │────►│ Data Preparation│────►│Template Selection│
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Final Output  │◄────│Format Conversion│◄────│Template Rendering│
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Detailed Steps

### 1. Profile Data Retrieval

The process begins with retrieving the user's profile data.

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│  User Request   │────►│ Profile Service │
│                 │     │                 │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │  Profile Data   │
                        │                 │
                        └─────────────────┘
```

- The system retrieves the complete profile from the ProfileService
- All sections are loaded: personal info, education, experience, skills, etc.
- Related metadata is attached (last update time, profile completeness)

### 2. Data Preparation

Before rendering, the profile data goes through preparation steps.

```
┌─────────────────┐
│  Profile Data   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│  Data Filtering │────►│  Data Formatting│
│                 │     │                 │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │ Prepared Data   │
                        │                 │
                        └─────────────────┘
```

- **Data Filtering**:
  - Removes any sections marked as private
  - Applies template-specific section filtering
  - Handles conditional sections based on completeness

- **Data Formatting**:
  - Converts dates to consistent format
  - Formats text fields (capitalizes names, formats phone numbers)
  - Processes Markdown in description fields
  - Creates derived fields (e.g., total years of experience)

### 3. Template Selection

The system selects and loads the appropriate template.

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│ Template Request│────►│Template Registry│
│                 │     │                 │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │Template Loading │
                        │                 │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │Template Instance│
                        │                 │
                        └─────────────────┘
```

- **Template Selection**:
  - Identifies template by ID or uses default for the format
  - Handles fallback if template is not found
  - Validates template compatibility with export format

- **Template Loading**:
  - Loads template definition from file system
  - Parses template configuration
  - Loads associated assets (CSS, JS, fonts)
  - Initializes template engine (Jinja2)

### 4. Template Rendering

The system renders the prepared data using the selected template.

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│ Prepared Data   │────►│  Jinja2 Engine  │
│                 │     │                 │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌─────────────────┐     │
         │                 │     │
         │Template Instance│────►│
         │                 │     │
         └─────────────────┘     ▼
                        ┌─────────────────┐
                        │                 │
                        │   HTML Output   │
                        │                 │
                        └─────────────────┘
```

- **Context Preparation**:
  - Combines profile data with template-specific context
  - Adds utility functions for formatting
  - Injects template configuration values

- **Rendering Process**:
  - Renders main template with Jinja2
  - Processes template inheritance and includes
  - Applies filters and transforms
  - Generates intermediate HTML representation

### 5. Format Conversion

The HTML output is converted to the requested final format.

```
┌─────────────────┐
│                 │
│   HTML Output   │
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│                                                     │
│               Format Converter                      │
│                                                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │         │  │         │  │         │  │         │ │
│  │   PDF   │  │  DOCX   │  │  JSON   │  │ Other   │ │
│  │         │  │         │  │         │  │ Formats │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │
│                                                     │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │                 │
                  │  Final Output   │
                  │                 │
                  └─────────────────┘
```

- **PDF Conversion**:
  - Uses pdfkit or weasyprint to convert HTML to PDF
  - Applies PDF-specific options (page size, margins)
  - Handles pagination and page breaks

- **DOCX Conversion**:
  - Uses python-docx to generate Word documents
  - Maps HTML elements to Word styles
  - Handles document structure and formatting

- **Other Formats**:
  - JSON/YAML: Structured data serialization
  - Markdown: HTML to Markdown conversion
  - CSV: Structured data to tabular format

### 6. Output Delivery

The final step is delivering the formatted document to the user.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Final Output   │────►│ Response Builder│────►│  User Download  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- **Response Preparation**:
  - Sets appropriate content type
  - Adds content disposition header for download
  - Compresses content if needed
  - Adds cache control headers

- **Delivery Methods**:
  - Direct download through HTTP response
  - Temporary storage with shareable link
  - Email attachment
  - Integration with external storage

## Template Structure

Templates are organized in a hierarchical structure:

```
templates/
├── base/
│   ├── base.html                  # Base template with common structure
│   ├── components/                # Reusable components
│   │   ├── header.html
│   │   ├── footer.html
│   │   ├── section.html
│   │   └── ...
│   └── layouts/                   # Layout variations
│       ├── standard.html
│       ├── academic.html
│       └── ...
├── pdf/
│   ├── resume_template.html       # PDF-specific templates
│   ├── portfolio_template.html
│   └── ...
├── docx/                          # DOCX-specific templates
├── html/                          # HTML-specific templates
└── config/                        # Template configuration
    ├── resume_professional.json
    ├── academic_cv.json
    └── ...
```

## Template Configuration

Each template is defined by a JSON configuration file:

```json
{
  "id": "resume_professional",
  "name": "Professional Resume",
  "description": "Clean professional resume format",
  "version": "1.2.0",
  "formats": ["pdf", "docx", "html"],
  "base_template": "base/layouts/standard.html",
  "styles": {
    "colors": {
      "primary": "#336699",
      "secondary": "#99ccff",
      "text": "#333333"
    },
    "fonts": {
      "heading": "Roboto",
      "body": "Open Sans"
    }
  },
  "sections": {
    "order": [
      "personal_info",
      "summary",
      "skills",
      "experience",
      "education",
      "certifications"
    ],
    "optional": ["projects", "languages", "interests", "references"]
  },
  "format_options": {
    "pdf": {
      "page_size": "A4",
      "margin_top": "20mm",
      "margin_right": "20mm",
      "margin_bottom": "20mm",
      "margin_left": "20mm"
    },
    "docx": {
      "include_header": true,
      "include_footer": true
    }
  }
}
```

## Extension Points

The template rendering system offers several extension points:

1. **Custom Template Functions**
   - Register additional Jinja2 functions
   - Add specialized formatters for specific data types

2. **Custom Converters**
   - Implement additional format converters
   - Extend existing converters with new options

3. **Template Hooks**
   - Pre-processing hooks for data preparation
   - Post-processing hooks for output customization

4. **Custom Template Sources**
   - Database-stored templates
   - Remote template repositories

## Performance Considerations

- Templates are cached in memory for improved performance
- Rendering-intensive formats (PDF) use a worker pool
- Large profiles are processed with streaming techniques
- Export results are cached with configurable time-to-live

## Security Measures

- Template validation prevents injection attacks
- User data is sanitized before rendering
- Template access control enforces permissions
- Output files are scanned for malicious content 