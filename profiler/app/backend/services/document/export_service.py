"""
Document Export Service module.

This module provides functionality for exporting documents in various formats 
and sharing them via different methods like email, links, and embedding.
"""

import io
import os
import json
import uuid
import time
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, BinaryIO, Union, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import markdown
import html2text
from fpdf import FPDF
from docx import Document as DocxDocument

from .interfaces import DocumentExportServiceInterface, DocumentRepositoryInterface
from .access_control import DocumentAccessControl
from ..auth import AuthenticationService, AuthenticationServiceInterface
from .exceptions import DocumentAccessError, DocumentNotFoundError, ExportError, ShareError
from ...utils.errors import ServiceError
from .models import Document, DocumentVersion, DocumentShare
from sqlalchemy.orm import Session
from ...utils.pdf_generator import generate_pdf
from ...utils.docx_generator import generate_docx
from ...utils.html_generator import generate_html

logger = logging.getLogger(__name__)

class DocumentExportError(ServiceError):
    """Exception raised when document export fails."""
    pass

class DocumentExportService(DocumentExportServiceInterface):
    """
    Service for exporting and sharing documents.
    
    This service handles:
    - Exporting documents in various formats (PDF, DOCX, HTML, TXT, JSON)
    - Sharing documents via email
    - Generating shareable links
    - Creating embed codes for documents
    """
    
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        access_control: DocumentAccessControl,
        auth_service: AuthenticationServiceInterface,
        config: Dict[str, Any],
        db_session: Session,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        sender_email: Optional[str] = None,
        base_url: str = "http://localhost:3000"
    ):
        """
        Initialize the document export service.
        
        Args:
            document_repository: Repository for document operations
            access_control: Service for document access control
            auth_service: Service for authentication
            config: Configuration settings including:
                - email_settings: SMTP server settings
                - frontend_url: Base URL for the frontend
                - jwt_secret: Secret for JWT generation
            db_session: Database session
            smtp_host: SMTP server host for email sending
            smtp_port: SMTP server port
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            sender_email: Email address for sending shared documents
            base_url: Base URL for generating shareable links
        """
        self._document_repository = document_repository
        self._access_control = access_control
        self._auth_service = auth_service
        self._config = config
        self.db_session = db_session
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.sender_email = sender_email
        self.base_url = base_url.rstrip('/')
        
        # Email configuration
        self._email_settings = config.get('email_settings', {})
        self._smtp_server = self._email_settings.get('smtp_server', 'localhost')
        self._smtp_port = self._email_settings.get('smtp_port', 587)
        self._smtp_user = self._email_settings.get('smtp_user', '')
        self._smtp_password = self._email_settings.get('smtp_password', '')
        self._sender_email = self._email_settings.get('sender_email', 'noreply@profiler.app')
        
        # URLs and secrets
        self._frontend_url = config.get('frontend_url', 'http://localhost:3000')
        self._jwt_secret = config.get('jwt_secret', 'default-secret-change-in-production')
        
        # Available export formats
        self.export_formats = {
            'pdf': self._export_to_pdf,
            'docx': self._export_to_docx,
            'html': self._export_to_html,
            'txt': self._export_to_text,
            'json': self._export_to_json
        }
    
    async def export_document(
        self, 
        document_id: str, 
        user_id: str, 
        format: str = 'pdf',
        version_id: Optional[str] = None
    ) -> Tuple[BinaryIO, str, str]:
        """Export a document in the specified format.
        
        Args:
            document_id: ID of the document to export
            user_id: ID of the user requesting the export
            format: Format to export to (pdf, docx, html, txt, json)
            version_id: Optional specific version to export
            
        Returns:
            Tuple containing:
            - File-like object with the exported document
            - Filename for the exported document
            - MIME type of the exported document
            
        Raises:
            DocumentExportError: If export fails for any reason
        """
        # Check format is supported
        if format not in self.export_formats:
            raise DocumentExportError(f"Unsupported export format: {format}")
        
        # Check access permissions
        if not await self._access_control.can_access_document(user_id, document_id):
            raise DocumentExportError("User does not have permission to export this document")
        
        try:
            # Get document
            if version_id:
                document_version = await self._document_repository.get_document_version(document_id, version_id)
                if not document_version:
                    raise DocumentExportError(f"Document version {version_id} not found")
                document = await self._document_repository.get_document(document_id)
                if not document:
                    raise DocumentExportError(f"Document {document_id} not found")
                content = document_version.content
                metadata = document_version.metadata
            else:
                document = await self._document_repository.get_document(document_id)
                if not document:
                    raise DocumentExportError(f"Document {document_id} not found")
                latest_version = await self._document_repository.get_latest_version(document_id)
                if not latest_version:
                    raise DocumentExportError(f"No versions found for document {document_id}")
                content = latest_version.content
                metadata = latest_version.metadata
            
            # Generate filename
            safe_title = document.title.replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_title}_{timestamp}.{format}"
            
            # Export document using the appropriate format handler
            return await self.export_formats[format](document, content, metadata, filename)
            
        except Exception as e:
            logger.error(f"Error exporting document {document_id}: {str(e)}")
            raise DocumentExportError(f"Failed to export document: {str(e)}")
    
    async def share_document(
        self,
        document_id: str,
        user_id: str,
        recipients: List[str],
        message: Optional[str] = None,
        expiry_days: int = 7,
        format: str = 'pdf',
        method: str = 'email',
        version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Share a document with other users.
        
        Args:
            document_id: ID of the document to share
            user_id: ID of the user sharing the document
            recipients: List of email addresses to share with
            message: Optional message to include with the share
            expiry_days: Number of days until the share expires
            format: Format to share the document in
            method: Sharing method ('email', 'link')
            version_id: Optional version ID if a specific version is to be shared
            
        Returns:
            Dictionary with sharing details
            
        Raises:
            DocumentExportError: If sharing fails
        """
        if not await self._access_control.can_share_document(user_id, document_id):
            raise DocumentExportError("User does not have permission to share this document")
        
        document = await self._document_repository.get_document(document_id)
        if not document:
            raise DocumentExportError(f"Document {document_id} not found")
        
        # Generate a shareable link
        share_token = self._generate_share_token(document_id, expiry_days)
        share_url = f"{self.base_url}/documents/shared/{share_token}"
        
        result = {
            "document_id": document_id,
            "share_url": share_url,
            "expires_at": (datetime.now() + timedelta(days=expiry_days)).isoformat(),
            "method": method
        }
        
        if method == 'email':
            # Only send email if email method is selected
            await self._share_via_email(
                document,
                recipients,
                message,
                share_url,
                expiry_days,
                version_id
            )
            result["recipients"] = recipients
            
        return result
    
    def generate_embed_code(
        self, 
        document_id: str, 
        user_id: str,
        width: str = "100%",
        height: str = "500px",
        show_toolbar: bool = True,
        version_id: Optional[str] = None
    ) -> str:
        """Generate HTML embed code for a document.
        
        Args:
            document_id: ID of the document to embed
            user_id: ID of the user generating the embed code
            width: Width of the embedded viewer (CSS value)
            height: Height of the embedded viewer (CSS value)
            show_toolbar: Whether to show the document toolbar
            version_id: Optional specific version to embed
            
        Returns:
            HTML code for embedding the document
        """
        # Check if user has access to the document
        document = self._document_repository.get_document_by_id(document_id)
        if not document:
            raise DocumentExportError("Document not found")
        
        # Check access permissions
        if not self._auth_service.can_share_document(user_id, document_id):
            raise DocumentExportError("You don't have permission to embed this document")
        
        # Generate a special embed token that doesn't expire
        embed_token = str(uuid.uuid4())
        
        # Create a share record for embedding (no expiry)
        share = DocumentShare(
            id=str(uuid.uuid4()),
            document_id=document_id,
            created_by=user_id,
            share_token=embed_token,
            is_embed=True,
            version_id=version_id
        )
        
        # Save share to database
        self._document_repository.create_document_share(share)
        
        # Generate embed URL
        embed_url = f"{self.base_url}/api/documents/embed/{embed_token}"
        
        # Generate HTML code
        toolbar_param = "true" if show_toolbar else "false"
        embed_html = f"""<iframe 
            src="{embed_url}?toolbar={toolbar_param}" 
            width="{width}" 
            height="{height}" 
            frameborder="0" 
            allowfullscreen
            title="{document.title}"
        ></iframe>"""
        
        return embed_html
    
    # Private methods for exporting
    
    async def _export_to_pdf(
        self, 
        document: Document, 
        content: Union[str, bytes, Dict[str, Any]], 
        metadata: Dict[str, Any],
        filename: str
    ) -> Tuple[BinaryIO, str, str]:
        """Export document to PDF format.
        
        For PDF export, additional processing may be needed based on the content type:
        - If content is HTML, convert to PDF
        - If content is already a PDF, just return as is
        - If content is text, convert to PDF
        - If content is JSON, format and convert to PDF
        """
        # Implementation depends on document content type
        content_type = metadata.get('content_type', 'text/plain')
        
        # Sample implementation - would need libraries like WeasyPrint, reportlab, etc.
        # Simplified here
        pdf_data = io.BytesIO()
        
        if content_type == 'application/pdf':
            # Content is already PDF
            if isinstance(content, bytes):
                pdf_data.write(content)
            else:
                pdf_data.write(str(content).encode('utf-8'))
        elif content_type in ['text/html', 'text/plain', 'application/json']:
            # Here would use a PDF generation library
            # For demo, just creating a simple PDF-like representation
            pdf_data.write(f"PDF EXPORT OF: {document.title}\n\n".encode('utf-8'))
            if isinstance(content, dict):
                pdf_data.write(json.dumps(content, indent=2).encode('utf-8'))
            else:
                if isinstance(content, bytes):
                    pdf_data.write(content)
                else:
                    pdf_data.write(str(content).encode('utf-8'))
        else:
            raise DocumentExportError(f"Cannot export content type {content_type} to PDF")
        
        pdf_data.seek(0)
        return pdf_data, filename, 'application/pdf'
    
    async def _export_to_docx(
        self, 
        document: Document, 
        content: Union[str, bytes, Dict[str, Any]], 
        metadata: Dict[str, Any],
        filename: str
    ) -> Tuple[BinaryIO, str, str]:
        """Export document to DOCX format."""
        # Here would use a library like python-docx
        docx_data = io.BytesIO()
        
        # Simplified implementation
        docx_data.write(f"DOCX EXPORT OF: {document.title}\n\n".encode('utf-8'))
        if isinstance(content, dict):
            docx_data.write(json.dumps(content, indent=2).encode('utf-8'))
        else:
            if isinstance(content, bytes):
                docx_data.write(content)
            else:
                docx_data.write(str(content).encode('utf-8'))
        
        docx_data.seek(0)
        return docx_data, filename, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    
    async def _export_to_html(
        self, 
        document: Document, 
        content: Union[str, bytes, Dict[str, Any]], 
        metadata: Dict[str, Any],
        filename: str
    ) -> Tuple[BinaryIO, str, str]:
        """Export document to HTML format."""
        html_data = io.BytesIO()
        
        content_type = metadata.get('content_type', 'text/plain')
        
        if content_type == 'text/html':
            # Content is already HTML
            if isinstance(content, bytes):
                html_data.write(content)
            else:
                html_data.write(str(content).encode('utf-8'))
        else:
            # Convert to HTML
            html_content = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{document.title}</title>\n</head>\n<body>\n"
            
            if isinstance(content, dict):
                html_content += f"<pre>{json.dumps(content, indent=2)}</pre>"
            else:
                if isinstance(content, bytes):
                    try:
                        text_content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        text_content = "Binary content cannot be displayed in HTML"
                else:
                    text_content = str(content)
                
                # Escape HTML special characters
                text_content = text_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_content += f"<pre>{text_content}</pre>"
            
            html_content += "\n</body>\n</html>"
            html_data.write(html_content.encode('utf-8'))
        
        html_data.seek(0)
        return html_data, filename, 'text/html'
    
    async def _export_to_text(self, document: Any, content: Any) -> BinaryIO:
        """Export document to plain text format."""
        try:
            output = io.BytesIO()
            
            # Create text structure
            text_content = f"{document.title}\n"
            text_content += "=" * len(document.title) + "\n\n"
            text_content += f"Created: {document.created_at}\n"
            text_content += f"Last Modified: {document.updated_at}\n\n"
            text_content += "CONTENT:\n"
            text_content += "-" * 50 + "\n\n"
            
            # Add content based on type
            if document.content_type == 'markdown':
                # Convert markdown to plain text
                h = html2text.HTML2Text()
                h.ignore_links = False
                text_content += h.handle(markdown.markdown(content))
            else:
                # Already plain text
                text_content += content
            
            output.write(text_content.encode('utf-8'))
            output.seek(0)
            return output
        
        except Exception as e:
            logger.error(f"Text export error: {str(e)}", exc_info=True)
            raise ExportError(f"Failed to export to text: {str(e)}")
    
    async def _export_to_json(
        self, 
        document: Document, 
        content: Union[str, bytes, Dict[str, Any]], 
        metadata: Dict[str, Any],
        filename: str
    ) -> Tuple[BinaryIO, str, str]:
        """Export document to JSON format with metadata."""
        json_data = io.BytesIO()
        
        # Create a JSON representation of the document
        document_data = {
            "document": {
                "id": document.id,
                "title": document.title,
                "created_at": document.created_at.isoformat() if hasattr(document.created_at, 'isoformat') else str(document.created_at),
                "updated_at": document.updated_at.isoformat() if hasattr(document.updated_at, 'isoformat') else str(document.updated_at),
                "owner_id": document.owner_id,
                "metadata": metadata
            }
        }
        
        # Add content based on its type
        if isinstance(content, dict):
            document_data["content"] = content
        else:
            if isinstance(content, bytes):
                try:
                    # Try to decode as UTF-8 text
                    document_data["content"] = content.decode('utf-8')
                except UnicodeDecodeError:
                    # If binary, encode as base64
                    import base64
                    document_data["content"] = base64.b64encode(content).decode('ascii')
                    document_data["content_encoding"] = "base64"
            else:
                document_data["content"] = str(content)
        
        json_data.write(json.dumps(document_data, indent=2).encode('utf-8'))
        json_data.seek(0)
        return json_data, filename, 'application/json'
    
    # Private methods for sharing
    
    async def _share_via_email(
        self,
        document: Document,
        recipients: List[str],
        message: Optional[str],
        share_url: str,
        expiry_days: int,
        version_id: Optional[str] = None
    ) -> None:
        """Share a document via email.
        
        Args:
            document: The document to share
            recipients: List of email addresses to share with
            message: Optional message to include with the share
            share_url: URL for accessing the shared document
            expiry_days: Number of days until the share expires
            version_id: Optional version ID if a specific version is to be shared
        
        Raises:
            DocumentExportError: If email sending fails
        """
        if not self.smtp_host or not self.smtp_port:
            raise DocumentExportError("Email configuration is missing")
        
        try:
            # Get user information
            user = self._auth_service.get_user_by_id(document.owner_id)
            sender_name = f"{user.first_name} {user.last_name}" if hasattr(user, 'first_name') else "A Profiler User"
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self._sender_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"{sender_name} shared a document with you: {document.title}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>{sender_name} has shared a document with you</h2>
                <p>Document: <strong>{document.title}</strong></p>
                <p>Click the link below to view the document:</p>
                <p><a href="{share_url}">{share_url}</a></p>
                <p>This link was generated by the Profiler document management system.</p>
                
                {f"<p>Message from sender: {message}</p>" if message else ""}
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send the email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Document {document.id} shared via email with {len(recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send share email: {str(e)}")
            raise DocumentExportError(f"Failed to share document via email: {str(e)}")
    
    def _generate_share_token(self, document_id: str, expiry_days: int = 7) -> str:
        """Generate a JWT token for document sharing.
        
        Args:
            document_id: ID of the document being shared
            expiry_days: Number of days until the token expires
            
        Returns:
            JWT token string
        """
        payload = {
            'document_id': document_id,
            'shared': True,
            'exp': int(time.time()) + (60 * 60 * 24 * expiry_days),  # Expires in X days
            'jti': str(uuid.uuid4())  # Unique token ID
        }
        
        return jwt.encode(payload, self._jwt_secret) 