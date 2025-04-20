"""
Document service exceptions.

This module defines custom exceptions for document-related operations.
"""

from typing import Dict, Any, Optional
from ...utils.errors import BaseError


class DocumentError(BaseError):
    """Base class for document-related errors."""
    pass


class DocumentAccessError(DocumentError):
    """Raised when there is an error accessing a document."""
    pass


class AccessControlError(DocumentError):
    """Raised when there is an error with document access control."""
    pass


class DocumentNotFoundError(DocumentError):
    """Raised when a requested document is not found."""
    pass


class ExportError(DocumentError):
    """Raised when there is an error exporting a document."""
    pass


class ShareError(DocumentError):
    """Raised when there is an error sharing a document."""
    pass


class StorageError(DocumentError):
    """Raised when there is an error with document storage."""
    pass


class ValidationError(DocumentError):
    """Raised when document validation fails."""
    pass


class VersionError(DocumentError):
    """Raised when there is an error with document versioning."""
    pass


class IndexingError(DocumentError):
    """Raised when there is an error indexing a document."""
    pass


class SearchError(DocumentError):
    """Raised when there is an error searching documents."""
    pass


class BackupError(DocumentError):
    """Raised when there is an error backing up documents."""
    pass


class RestoreError(DocumentError):
    """Raised when there is an error restoring documents from backup."""
    pass 