"""
PDF generation utilities.

This module provides functions for generating PDF documents.
"""

import io
from typing import Dict, Any, Optional, Union
from fpdf import FPDF
from PIL import Image
import markdown
import html2text


def generate_pdf(
    content: Union[str, bytes, Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    subject: Optional[str] = None,
    keywords: Optional[str] = None
) -> bytes:
    """
    Generate a PDF document from content.
    
    Args:
        content: Content to convert to PDF (text, HTML, or document data)
        metadata: Optional metadata to include in the PDF
        title: Optional document title
        author: Optional document author
        subject: Optional document subject
        keywords: Optional document keywords
        
    Returns:
        PDF document as bytes
    """
    # Create PDF object
    pdf = FPDF()
    
    # Set metadata
    if title:
        pdf.set_title(title)
    if author:
        pdf.set_author(author)
    if subject:
        pdf.set_subject(subject)
    if keywords:
        pdf.set_keywords(keywords)
    
    # Add metadata as document info
    if metadata:
        for key, value in metadata.items():
            if isinstance(value, str):
                pdf.set_doc_option(key, value)
    
    # Add content
    pdf.add_page()
    
    # Handle different content types
    if isinstance(content, str):
        # Check if content is HTML
        if content.strip().startswith('<'):
            # Convert HTML to plain text
            h = html2text.HTML2Text()
            h.ignore_links = True
            text = h.handle(content)
            pdf.multi_cell(0, 10, text)
        else:
            # Plain text
            pdf.multi_cell(0, 10, content)
    elif isinstance(content, bytes):
        # Try to handle as image
        try:
            img = Image.open(io.BytesIO(content))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            pdf.image(img_bytes, x=10, y=10)
        except Exception:
            # Not an image, treat as text
            pdf.multi_cell(0, 10, content.decode('utf-8', errors='ignore'))
    elif isinstance(content, dict):
        # Handle structured document data
        if 'title' in content:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, content['title'], ln=True)
            pdf.ln(10)
        
        if 'content' in content:
            pdf.set_font('Arial', '', 12)
            if isinstance(content['content'], str):
                pdf.multi_cell(0, 10, content['content'])
            elif isinstance(content['content'], list):
                for item in content['content']:
                    pdf.multi_cell(0, 10, str(item))
                    pdf.ln(5)
    
    # Get PDF as bytes
    return pdf.output(dest='S').encode('latin1')


def generate_pdf_from_markdown(
    markdown_content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Generate a PDF document from Markdown content.
    
    Args:
        markdown_content: Content in Markdown format
        metadata: Optional metadata to include in the PDF
        
    Returns:
        PDF document as bytes
    """
    # Convert Markdown to HTML
    html = markdown.markdown(markdown_content)
    
    # Convert HTML to PDF
    return generate_pdf(html, metadata=metadata) 