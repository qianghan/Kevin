"""
Document Service Database Module.

This module provides database models and utilities for the document service.
"""

from .models import (
    DocumentModel as Document,
    DocumentChunkModel as DocumentChunk,
    DocumentVersionModel as DocumentVersion,
    DocumentShareModel as DocumentShare
)

__all__ = [
    "Document",
    "DocumentChunk",
    "DocumentVersion",
    "DocumentShare"
] 