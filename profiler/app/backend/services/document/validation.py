"""
Document validation utilities.

This module provides validation functionality for document data.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import ValidationError

logger = get_logger(__name__)


class DocumentValidator:
    """Validator for document data."""
    
    @classmethod
    def validate_metadata(cls, metadata: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate document metadata.
        
        Args:
            metadata: Document metadata to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check metadata size
        metadata_str = json.dumps(metadata)
        if len(metadata_str) > 10240:  # 10KB limit
            errors.append("Metadata exceeds 10KB size limit")
        
        # Validate reserved keys
        reserved_keys = ["system", "processing", "security", "shared_with"]
        for key in reserved_keys:
            if key in metadata and not cls._validate_reserved_key(key, metadata[key]):
                errors.append(f"Invalid format for reserved metadata key: {key}")
        
        # Validate custom keys
        for key, value in metadata.items():
            if key not in reserved_keys:
                if not cls._validate_custom_metadata_key(key):
                    errors.append(f"Invalid metadata key: {key}")
                
                if not cls._validate_custom_metadata_value(value):
                    errors.append(f"Invalid metadata value for key {key}")
        
        return len(errors) == 0, errors if errors else None
    
    @staticmethod
    def _validate_reserved_key(key: str, value: Any) -> bool:
        """
        Validate reserved metadata keys.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            True if valid, False otherwise
        """
        if key == "system":
            # System metadata must be a dictionary
            if not isinstance(value, dict):
                return False
                
            # Check for required system keys
            required_keys = ["version", "last_modified_by"]
            for req_key in required_keys:
                if req_key not in value:
                    return False
            
            return True
            
        elif key == "processing":
            # Processing metadata must be a dictionary
            if not isinstance(value, dict):
                return False
                
            # Check for valid processing keys
            valid_keys = ["status", "progress", "error", "completed_at", "started_at"]
            for k in value.keys():
                if k not in valid_keys:
                    return False
            
            return True
            
        elif key == "security":
            # Security metadata must be a dictionary
            if not isinstance(value, dict):
                return False
                
            # Check for valid security keys
            valid_keys = ["classification", "restricted", "expiry", "access_level"]
            for k in value.keys():
                if k not in valid_keys:
                    return False
            
            return True
            
        elif key == "shared_with":
            # Shared with metadata must be a list
            if not isinstance(value, list):
                return False
                
            # Check each sharing entry
            for entry in value:
                if not isinstance(entry, dict):
                    return False
                    
                # Check for required keys in sharing entry
                required_keys = ["sharing_id", "user_id", "permissions", "shared_at"]
                for req_key in required_keys:
                    if req_key not in entry:
                        return False
            
            return True
            
        return False
    
    @staticmethod
    def _validate_custom_metadata_key(key: str) -> bool:
        """
        Validate a custom metadata key.
        
        Args:
            key: Metadata key
            
        Returns:
            True if valid, False otherwise
        """
        # Keys must be alphanumeric with underscores, no more than 64 chars
        return bool(re.match(r'^[a-zA-Z0-9_]{1,64}$', key))
    
    @staticmethod
    def _validate_custom_metadata_value(value: Any) -> bool:
        """
        Validate a custom metadata value.
        
        Args:
            value: Metadata value
            
        Returns:
            True if valid, False otherwise
        """
        # Check type
        if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
            return False
            
        # For string values, check length
        if isinstance(value, str) and len(value) > 1024:
            return False
            
        # For lists, check length and validate each item
        if isinstance(value, list):
            if len(value) > 100:
                return False
                
            for item in value:
                if isinstance(item, (list, dict)):
                    # No nested complex structures beyond one level
                    return False
                    
                if isinstance(item, str) and len(item) > 1024:
                    return False
        
        # For dictionaries, check length and validate each key/value
        if isinstance(value, dict):
            if len(value) > 50:
                return False
                
            for k, v in value.items():
                if not DocumentValidator._validate_custom_metadata_key(k):
                    return False
                    
                if isinstance(v, (list, dict)):
                    # No nested complex structures beyond one level
                    return False
                    
                if isinstance(v, str) and len(v) > 1024:
                    return False
        
        return True
    
    @classmethod
    def validate_document_file(cls, filename: str, file_size: int, mime_type: str) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate document file properties.
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate filename
        if not cls._validate_filename(filename):
            errors.append("Invalid filename format")
        
        # Validate file size (100MB limit)
        if file_size <= 0 or file_size > 104857600:
            errors.append(f"File size {file_size} is invalid or exceeds 100MB limit")
        
        # Validate MIME type
        if not cls._validate_mime_type(mime_type):
            errors.append(f"Unsupported MIME type: {mime_type}")
        
        return len(errors) == 0, errors if errors else None
    
    @staticmethod
    def _validate_filename(filename: str) -> bool:
        """
        Validate a filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if valid, False otherwise
        """
        # Filename must be 1-255 characters
        if not filename or len(filename) > 255:
            return False
            
        # Filename must not contain invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in filename:
                return False
                
        return True
    
    @staticmethod
    def _validate_mime_type(mime_type: str) -> bool:
        """
        Validate a MIME type.
        
        Args:
            mime_type: MIME type of the file
            
        Returns:
            True if supported, False otherwise
        """
        # List of supported MIME types
        supported_types = [
            # PDF
            'application/pdf',
            
            # Microsoft Office
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            
            # OpenDocument
            'application/vnd.oasis.opendocument.text',
            'application/vnd.oasis.opendocument.spreadsheet',
            'application/vnd.oasis.opendocument.presentation',
            
            # Plain text
            'text/plain',
            
            # Rich text
            'application/rtf',
            'text/rtf',
            
            # Markup languages
            'text/html',
            'text/xml',
            'application/xml',
            'application/json',
            'application/markdown',
            'text/markdown',
            
            # Images
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'image/svg+xml',
            
            # Archives
            'application/zip',
            'application/x-rar-compressed',
            'application/gzip',
            'application/x-7z-compressed'
        ]
        
        return mime_type in supported_types 