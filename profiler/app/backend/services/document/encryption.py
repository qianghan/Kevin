"""
Document encryption module.

This module provides functionality for encrypting and decrypting documents
using industry-standard encryption algorithms.
"""

import os
import base64
import logging
from enum import Enum, auto
from typing import Optional, Dict, Any, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms."""
    FERNET = auto()  # AES-128 in CBC mode with PKCS7 padding and HMAC-SHA256
    AES_256 = auto()  # Future implementation

class DocumentEncryption:
    """
    Service for encrypting and decrypting documents.
    
    Provides functionality to securely encrypt document content
    using industry-standard encryption algorithms. The service supports
    password-based encryption and key management.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize the document encryption service.
        
        Args:
            master_key: Optional master key for encryption. If not provided, 
                        one will be generated and stored securely.
        """
        self._master_key = master_key or os.environ.get('DOCUMENT_MASTER_KEY')
        
        if not self._master_key:
            # Generate a secure master key if none is provided
            self._master_key = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
            logger.info("Generated new master encryption key")
        
        self._key_cache: Dict[str, bytes] = {}
    
    def derive_key(self, document_id: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive a document-specific encryption key using the master key.
        
        Args:
            document_id: The unique identifier of the document
            salt: Optional salt for key derivation. If not provided, one will be generated.
            
        Returns:
            bytes: The derived encryption key
        """
        if document_id in self._key_cache:
            return self._key_cache[document_id]
        
        # Use a consistent salt if provided, otherwise generate one
        salt = salt or os.urandom(16)
        
        # Use PBKDF2 to derive a document-specific key from the master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self._master_key.encode()))
        self._key_cache[document_id] = key
        
        return key
    
    def encrypt(self, 
                document_id: str, 
                content: Union[str, bytes],
                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Encrypt document content.
        
        Args:
            document_id: Unique identifier for the document
            content: Document content to encrypt (string or bytes)
            metadata: Optional metadata to include with the encrypted content
            
        Returns:
            Dict containing the encrypted content, salt, and algorithm information
        """
        salt = os.urandom(16)
        key = self.derive_key(document_id, salt)
        
        # Convert content to bytes if it's a string
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        # Encrypt the content using Fernet (AES-128 + HMAC)
        fernet = Fernet(key)
        encrypted_content = fernet.encrypt(content)
        
        result = {
            'encrypted_content': base64.b64encode(encrypted_content).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8'),
            'algorithm': EncryptionAlgorithm.FERNET.name,
            'is_encrypted': True,
        }
        
        # Include metadata if provided
        if metadata:
            result['metadata'] = metadata
            
        logger.info(f"Document {document_id} encrypted successfully")
        return result
    
    def decrypt(self, 
                document_id: str, 
                encrypted_data: Dict[str, Any]) -> Union[str, bytes]:
        """
        Decrypt document content.
        
        Args:
            document_id: Unique identifier for the document
            encrypted_data: Dictionary containing the encrypted content and metadata
            
        Returns:
            The decrypted document content
            
        Raises:
            ValueError: If the encrypted data is invalid or cannot be decrypted
        """
        if not encrypted_data.get('is_encrypted', False):
            raise ValueError("The provided data is not marked as encrypted")
        
        # Extract encryption details
        encrypted_content = base64.b64decode(encrypted_data['encrypted_content'])
        salt = base64.b64decode(encrypted_data['salt'])
        algorithm = encrypted_data.get('algorithm', EncryptionAlgorithm.FERNET.name)
        
        # Validate the algorithm
        if algorithm != EncryptionAlgorithm.FERNET.name:
            raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
        
        # Derive the key using the same salt
        key = self.derive_key(document_id, salt)
        
        # Decrypt the content
        fernet = Fernet(key)
        try:
            decrypted_content = fernet.decrypt(encrypted_content)
            logger.info(f"Document {document_id} decrypted successfully")
            return decrypted_content
        except Exception as e:
            logger.error(f"Failed to decrypt document {document_id}: {str(e)}")
            raise ValueError("Failed to decrypt the document. The key may be invalid.") from e
    
    def rotate_key(self, document_id: str, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-encrypt document with a new key for security purposes.
        
        Args:
            document_id: Unique identifier for the document
            encrypted_data: Dictionary containing the currently encrypted content
            
        Returns:
            Dict containing the re-encrypted content with new keys
        """
        # Decrypt with the old key
        decrypted_content = self.decrypt(document_id, encrypted_data)
        
        # Extract metadata to preserve it
        metadata = encrypted_data.get('metadata')
        
        # Re-encrypt with a new salt (which generates a new key)
        return self.encrypt(document_id, decrypted_content, metadata) 