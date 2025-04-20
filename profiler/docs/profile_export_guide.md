# Profile Export User Guide

This guide provides instructions on how to export user profiles in various formats using the Profiler system.

## Available Export Formats

The Profiler system supports the following export formats:

1. **PDF** - Professional PDF documents suitable for printing and sharing
2. **DOCX** - Microsoft Word documents for further editing
3. **HTML** - Web-viewable format for online sharing
4. **Markdown** - Simple text format for content management systems
5. **JSON** - Machine-readable format for data interchange
6. **YAML** - Human-readable data serialization format
7. **CSV** - Tabular data format for spreadsheet applications

## Exporting a Profile

### From the Web Interface

1. **Navigate to the Profile View**
   - Log in to your Profiler account
   - Select the profile you wish to export from your dashboard
   - Click the "View Profile" button

2. **Access the Export Menu**
   - Click the "Export" button in the top-right corner of the profile view
   - A dropdown menu will appear with available export options

3. **Select Export Format**
   - Choose your desired export format from the dropdown menu
   - PDF, DOCX, and HTML formats offer a preview option

4. **Choose a Template** (Optional)
   - Click "Select Template" to browse available templates
   - Choose a template that best suits your needs (e.g., Resume, Academic CV, Portfolio)
   - Preview each template by clicking the "Preview" button

5. **Configure Export Options** (Optional)
   - Click "Advanced Options" to customize your export
   - Available options vary by format:
     - PDF: Page size, orientation, sections to include
     - DOCX: Section order, header/footer options
     - HTML: Style options, interactive features
     - Other formats: Various configuration options

6. **Generate and Download**
   - Click the "Export" button to generate your file
   - Once processing is complete, your file will automatically download
   - For large profiles, you'll receive a notification when the export is ready

### Using the API

For programmatic access, you can use the Profile Export API:

1. **Single Format Export**
   ```
   POST /api/profiler/profile/export
   {
     "profile_id": "your-profile-id",
     "format": "pdf",
     "template_id": "resume_professional"
   }
   ```

2. **Multi-Format Export**
   ```
   POST /api/profiler/profile/export-archive
   {
     "profile_id": "your-profile-id",
     "formats": ["pdf", "docx", "json"],
     "template_id": "resume_professional"
   }
   ```

See the [Profile Export API Documentation](api/profile_export_api.md) for full details.

## Working with Templates

### Using Existing Templates

The Profiler system comes with several pre-configured templates:

1. **Standard Resume**
   - Professional layout suitable for job applications
   - Emphasizes work experience and skills
   - Available in all formats

2. **Academic CV**
   - Comprehensive academic curriculum vitae
   - Highlights publications, research, and teaching experience
   - Best suited for PDF and DOCX formats

3. **Portfolio Showcase**
   - Visual layout emphasizing projects and achievements
   - Includes image galleries and interactive elements
   - Optimized for HTML format

4. **Minimalist**
   - Clean, simple layout with essential information
   - Quick to scan for busy recruiters
   - Available in all formats

### Creating Custom Templates

You can create your own custom templates:

1. **From the Templates Page**
   - Navigate to Profile → Templates
   - Click "Create New Template"

2. **Start with a Base Template**
   - Select an existing template as your starting point
   - Click "Customize" to enter the template editor

3. **Customize Your Template**
   - Modify colors, fonts, and layout
   - Reorder or hide profile sections
   - Add custom CSS for HTML exports
   - Set default options for different export formats

4. **Save and Use Your Template**
   - Give your template a name and description
   - Click "Save Template"
   - Your new template will now appear in the template selection dropdown

## Sharing Exported Profiles

### Direct Sharing

After generating an export, you have several sharing options:

1. **Email Sharing**
   - Click the "Share via Email" button
   - Enter recipient email addresses
   - Add an optional message
   - Recipients will receive a download link

2. **Generate Shareable Link**
   - Click "Create Shareable Link"
   - Set an expiration date (optional)
   - Copy the generated link
   - Share the link with anyone you want to view your profile

3. **Social Media Sharing**
   - Click the social media icons to share directly to platforms
   - Available for LinkedIn, Twitter, and Facebook
   - HTML exports work best for social sharing

### Privacy Controls

Manage who can access your exported profiles:

1. **Access Settings**
   - Set exports to "Public," "Private," or "Password Protected"
   - For password protection, create a secure password for recipients

2. **Expiration Settings**
   - Set an expiration date for shareable links
   - After expiration, links will no longer work

3. **Track Access**
   - View who has accessed your shared exports
   - See access timestamps and locations

## Best Practices

### Optimizing Your Exports

For the best results with profile exports:

1. **Complete Your Profile**
   - Ensure all relevant sections are complete
   - Add detailed information for comprehensive exports

2. **Format-Specific Considerations**
   - PDF: Upload a high-quality profile photo
   - DOCX: Keep formatting simple for better compatibility
   - HTML: Add links to external resources and portfolios
   - CSV/JSON: Ensure structured data is consistent

3. **Template Selection**
   - Choose templates based on your audience
   - Academic positions: use Academic CV
   - Corporate jobs: use Standard Resume or Minimalist
   - Creative fields: use Portfolio Showcase

4. **Regular Updates**
   - Keep your profile current for accurate exports
   - Update your custom templates as your career evolves

## Troubleshooting

### Common Issues

1. **Export Failed**
   - Ensure your profile has all required sections
   - Check that any custom templates are valid
   - Try a different export format

2. **Missing Information**
   - Verify that your profile is complete
   - Some templates may hide certain sections by design
   - Check template settings for section visibility

3. **Formatting Problems**
   - Try a different template
   - For DOCX exports, check compatibility with your version of Word
   - For PDF exports, ensure any custom fonts are supported

4. **Large File Size**
   - Optimize images in your profile
   - Export without unnecessary sections
   - Use the "Optimize for sharing" option

### Getting Help

If you encounter issues with profile exports:

1. **Check the Documentation**
   - Review this guide for solutions
   - See specific format documentation for technical details

2. **Contact Support**
   - Email: support@profiler.example.com
   - Use the "Help" button in the profile export interface
   - Include export format and template information in your request 