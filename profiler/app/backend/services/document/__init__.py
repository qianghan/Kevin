"""
Document service package.

This package provides functionality for document management, including:
- Document storage and retrieval
- Document versioning
- Document metadata extraction
- Document security features (access control, audit logging, watermarking)
- Document sharing and collaboration
- OCR for scanned documents
- Virus/malware scanning for document security
"""

from .repository import DocumentRepositoryInterface, DocumentRepository
from .versioning import DocumentVersioningService as DocumentVersionManager
from .access_control import DocumentAccessControl
from .audit import DocumentAuditLogger, AuditAction, AuditLevel, AuditRecord
from .watermark import DocumentWatermark, WatermarkType, WatermarkPosition, WatermarkOptions
from .ocr import DocumentOCR, OCRException
from .security import DocumentSecurity, ScanStatus, ScanResult
from .models import Document, DocumentVersion
from .service import DocumentService
from .external import ExternalStorageService, ExternalDocument, ExternalStorageType
from .notification import DocumentNotificationManager, NotificationType
from .export_service import DocumentExportService
from .extraction import DocumentMetadataExtractor, DocumentMetadataExtractionService
from .exceptions import (
    DocumentError,
    DocumentAccessError,
    DocumentNotFoundError,
    ExportError,
    ShareError,
    StorageError,
    ValidationError,
    VersionError,
    IndexingError,
    SearchError,
    BackupError,
    RestoreError
)

__all__ = [
    'DocumentRepositoryInterface',
    'DocumentRepository',
    'DocumentVersionManager',
    'DocumentAccessControl',
    'DocumentAuditLogger',
    'AuditAction',
    'AuditLevel',
    'AuditRecord',
    'DocumentWatermark',
    'WatermarkType',
    'WatermarkPosition',
    'WatermarkOptions',
    'DocumentOCR',
    'OCRException',
    'DocumentSecurity',
    'ScanStatus',
    'ScanResult',
    'Document',
    'DocumentVersion',
    'DocumentService',
    'ExternalStorageService',
    'ExternalDocument',
    'ExternalStorageType',
    'DocumentNotificationManager',
    'NotificationType',
    'DocumentExportService',
    'DocumentMetadataExtractor',
    'DocumentMetadataExtractionService',
    'DocumentError',
    'DocumentAccessError',
    'DocumentNotFoundError',
    'ExportError',
    'ShareError',
    'StorageError',
    'ValidationError',
    'VersionError',
    'IndexingError',
    'SearchError',
    'BackupError',
    'RestoreError'
] 