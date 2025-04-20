"""
HTML generation utilities.

This module provides functions for generating HTML documents.
"""

import io
from typing import Dict, Any, Optional, Union
import markdown
from bs4 import BeautifulSoup


def generate_html(
    content: Union[str, bytes, Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    subject: Optional[str] = None,
    keywords: Optional[str] = None
) -> bytes:
    """
    Generate an HTML document from content.
    
    Args:
        content: Content to convert to HTML (text, markdown, or document data)
        metadata: Optional metadata to include in the HTML
        title: Optional document title
        author: Optional document author
        subject: Optional document subject
        keywords: Optional document keywords
        
    Returns:
        HTML document as bytes
    """
    # Start with basic HTML structure
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
            h1 {{ color: #333; }}
            .metadata {{ color: #666; margin-bottom: 20px; }}
            .content {{ margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="metadata">
            {metadata_html}
        </div>
        <div class="content">
            {content_html}
        </div>
    </body>
    </html>
    """
    
    # Process metadata
    metadata_html = ""
    if metadata:
        metadata_html = "<ul>"
        for key, value in metadata.items():
            metadata_html += f"<li><strong>{key}:</strong> {value}</li>"
        metadata_html += "</ul>"
    
    # Process content based on type
    content_html = ""
    if isinstance(content, str):
        # Check if content is markdown
        if content.strip().startswith(('#', '*', '-', '>', '`', '|')):
            content_html = markdown.markdown(content)
        else:
            # Plain text
            content_html = f"<pre>{content}</pre>"
    elif isinstance(content, bytes):
        # Try to decode as text
        try:
            text_content = content.decode('utf-8')
            content_html = f"<pre>{text_content}</pre>"
        except UnicodeDecodeError:
            # If not text, add as binary data note
            content_html = "<p>Binary content cannot be displayed in HTML format</p>"
    elif isinstance(content, dict):
        # Handle structured document data
        if 'title' in content:
            content_html += f"<h2>{content['title']}</h2>"
        
        if 'content' in content:
            if isinstance(content['content'], str):
                content_html += f"<div>{content['content']}</div>"
            elif isinstance(content['content'], list):
                content_html += "<ul>"
                for item in content['content']:
                    content_html += f"<li>{item}</li>"
                content_html += "</ul>"
    
    # Format the HTML
    html_content = html_template.format(
        title=title or "Document",
        metadata_html=metadata_html,
        content_html=content_html
    )
    
    # Use BeautifulSoup to prettify the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    pretty_html = soup.prettify()
    
    return pretty_html.encode('utf-8') 