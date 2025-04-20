"""
Tests for document security and permissions functionality.
"""

import pytest
import asyncio
import uuid
import io
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

from app.backend.services.document.security import DocumentSecurity, ScanStatus, ScanResult
from app.backend.services.document.access_control import DocumentAccessControl
from app.backend.services.document.models import Document
from app.backend.utils.errors import SecurityError, ValidationError, AuthorizationError


@pytest.fixture
def mock_virus_scanner():
    """Create a mock virus scanner."""
    scanner = MagicMock()
    
    async def scan_file(file_content):
        # Simulate virus scanning
        content = file_content.read() if hasattr(file_content, 'read') else file_content
        # If content contains the word "virus", report it as infected
        if b"virus" in content:
            return ScanResult(
                status=ScanStatus.INFECTED,
                threats=["Test Virus"],
                details="Found test virus signature"
            )
        return ScanResult(
            status=ScanStatus.CLEAN,
            threats=[],
            details="No threats detected"
        )
    
    scanner.scan_file = AsyncMock(side_effect=scan_file)
    return scanner


@pytest.fixture
def document_security(mock_virus_scanner):
    """Create a document security service with mocked scanner."""
    return DocumentSecurity(
        scanner=mock_virus_scanner,
        max_file_size=10 * 1024 * 1024,  # 10MB
        allowed_mime_types=["application/pdf", "text/plain", "application/msword"],
        blocked_extensions=[".exe", ".bat", ".sh"]
    )


@pytest.fixture
def access_control():
    """Create an access control service."""
    service = DocumentAccessControl()
    # Pre-configure some permissions
    service._permissions = {
        "doc1": {
            "owner": "user1",
            "access": {
                "user1": ["READ", "WRITE", "DELETE", "SHARE"],
                "user2": ["READ"],
                "group1": ["READ", "WRITE"]
            }
        },
        "doc2": {
            "owner": "user2",
            "access": {
                "user2": ["READ", "WRITE", "DELETE", "SHARE"],
                "user3": ["READ", "WRITE"]
            }
        }
    }
    
    return service


class TestDocumentSecurity:
    """Tests for document security functionality."""
    
    @pytest.mark.asyncio
    async def test_virus_scanning_clean_file(self, document_security):
        """Test virus scanning for a clean file."""
        # Create a clean test file
        test_content = b"This is a clean test file"
        test_file = io.BytesIO(test_content)
        
        # Scan the file
        result = await document_security.scan_file(test_file)
        
        # Verify result
        assert result.status == ScanStatus.CLEAN
        assert len(result.threats) == 0
        assert "No threats" in result.details
    
    @pytest.mark.asyncio
    async def test_virus_scanning_infected_file(self, document_security):
        """Test virus scanning for an infected file."""
        # Create an infected test file
        test_content = b"This file contains a virus signature"
        test_file = io.BytesIO(test_content)
        
        # Scan the file
        result = await document_security.scan_file(test_file)
        
        # Verify result
        assert result.status == ScanStatus.INFECTED
        assert len(result.threats) > 0
        assert "Test Virus" in result.threats
    
    @pytest.mark.asyncio
    async def test_file_size_validation(self, document_security):
        """Test file size validation."""
        # Create a document with valid size
        valid_size_doc = Document(
            id="test1",
            title="Valid Size Document",
            owner_id="test-user",
            content_type="text/plain",
            size=1024,  # 1KB
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={}
        )
        
        # Create a document with invalid size
        invalid_size_doc = Document(
            id="test2",
            title="Invalid Size Document",
            owner_id="test-user",
            content_type="text/plain",
            size=20 * 1024 * 1024,  # 20MB (over the 10MB limit)
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={}
        )
        
        # Validate file sizes
        document_security.validate_file_size(valid_size_doc)
        
        with pytest.raises(ValidationError) as excinfo:
            document_security.validate_file_size(invalid_size_doc)
        
        assert "exceeds maximum allowed" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_mime_type_validation(self, document_security):
        """Test MIME type validation."""
        # Create documents with valid and invalid MIME types
        valid_mime_doc = Document(
            id="test1",
            title="Valid MIME Document",
            owner_id="test-user",
            content_type="application/pdf",
            size=1024,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={}
        )
        
        invalid_mime_doc = Document(
            id="test2",
            title="Invalid MIME Document",
            owner_id="test-user",
            content_type="application/x-executable",
            size=1024,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={}
        )
        
        # Validate MIME types
        document_security.validate_mime_type(valid_mime_doc)
        
        with pytest.raises(ValidationError) as excinfo:
            document_security.validate_mime_type(invalid_mime_doc)
        
        assert "MIME type not allowed" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_filename_validation(self, document_security):
        """Test filename validation."""
        # Test valid filenames
        valid_filenames = [
            "document.pdf",
            "report.docx",
            "notes.txt",
            "presentation.pptx"
        ]
        
        # Test invalid filenames
        invalid_filenames = [
            "script.exe",
            "batch.bat",
            "shell.sh",
            "..\\..\\system\\file.txt"  # Path traversal attempt
        ]
        
        # Validate filenames
        for filename in valid_filenames:
            document_security.validate_filename(filename)
        
        for filename in invalid_filenames:
            with pytest.raises(ValidationError):
                document_security.validate_filename(filename)
    
    @pytest.mark.asyncio
    async def test_security_scan_workflow(self, document_security):
        """Test the complete security scan workflow."""
        # Create a test file
        test_content = b"This is a test file for security scanning"
        test_file = io.BytesIO(test_content)
        
        # Create document metadata
        document = Document(
            id="test1",
            title="Test Document",
            owner_id="test-user",
            content_type="text/plain",
            size=len(test_content),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                "filename": "test.txt"
            }
        )
        
        # Perform full security check
        result = await document_security.perform_security_check(document, test_file)
        
        # Verify result
        assert result.passed
        assert len(result.issues) == 0
        
        # Test with an infected file
        infected_content = b"This file contains a virus"
        infected_file = io.BytesIO(infected_content)
        
        document.size = len(infected_content)
        
        result = await document_security.perform_security_check(document, infected_file)
        
        # Verify result
        assert not result.passed
        assert len(result.issues) > 0
        assert any("virus" in issue.lower() for issue in result.issues)


class TestDocumentAccessControl:
    """Tests for document access control functionality."""
    
    @pytest.mark.asyncio
    async def test_user_access_permissions(self, access_control):
        """Test user access permissions for documents."""
        # Check owner access
        can_access = await access_control.can_access_document("user1", "doc1")
        assert can_access is True, "Owner should have access"
        
        # Check user with explicit READ permission
        can_access = await access_control.can_access_document("user2", "doc1")
        assert can_access is True, "User with READ permission should have access"
        
        # Check user without permission
        can_access = await access_control.can_access_document("user3", "doc1")
        assert can_access is False, "User without permission should not have access"
    
    @pytest.mark.asyncio
    async def test_permission_levels(self, access_control):
        """Test different permission levels."""
        # Test READ permission
        can_read = await access_control.check_permission("user2", "doc1", "READ")
        assert can_read is True, "User should have READ permission"
        
        # Test WRITE permission (user2 doesn't have it)
        can_write = await access_control.check_permission("user2", "doc1", "WRITE")
        assert can_write is False, "User should not have WRITE permission"
        
        # Test SHARE permission
        can_share = await access_control.check_permission("user1", "doc1", "SHARE")
        assert can_share is True, "Owner should have SHARE permission"
    
    @pytest.mark.asyncio
    async def test_grant_permission(self, access_control):
        """Test granting permissions to users."""
        # Initially user3 doesn't have access to doc1
        assert await access_control.can_access_document("user3", "doc1") is False
        
        # Grant READ permission
        await access_control.grant_access("doc1", "user3", "READ")
        
        # Now user3 should have access
        assert await access_control.can_access_document("user3", "doc1") is True
        assert await access_control.check_permission("user3", "doc1", "READ") is True
        assert await access_control.check_permission("user3", "doc1", "WRITE") is False
    
    @pytest.mark.asyncio
    async def test_revoke_permission(self, access_control):
        """Test revoking permissions from users."""
        # Initially user2 has READ access to doc1
        assert await access_control.can_access_document("user2", "doc1") is True
        
        # Revoke READ permission
        await access_control.revoke_access("doc1", "user2", "READ")
        
        # Now user2 should not have access
        assert await access_control.can_access_document("user2", "doc1") is False
    
    @pytest.mark.asyncio
    async def test_group_permissions(self, access_control):
        """Test group permissions."""
        # Check group permission
        assert await access_control.check_permission("group1", "doc1", "READ") is True
        assert await access_control.check_permission("group1", "doc1", "WRITE") is True
        
        # Revoke group WRITE permission
        await access_control.revoke_access("doc1", "group1", "WRITE")
        
        # Now group should only have READ permission
        assert await access_control.check_permission("group1", "doc1", "READ") is True
        assert await access_control.check_permission("group1", "doc1", "WRITE") is False
    
    @pytest.mark.asyncio
    async def test_document_sharing(self, access_control):
        """Test document sharing functionality."""
        # User1 can share doc1
        assert await access_control.can_share_document("user1", "doc1") is True
        
        # User2 cannot share doc1
        assert await access_control.can_share_document("user2", "doc1") is False
        
        # Share document with user3
        await access_control.share_document("doc1", "user1", "user3", ["READ", "WRITE"])
        
        # Verify user3 has the correct permissions
        assert await access_control.check_permission("user3", "doc1", "READ") is True
        assert await access_control.check_permission("user3", "doc1", "WRITE") is True
        assert await access_control.check_permission("user3", "doc1", "DELETE") is False
    
    @pytest.mark.asyncio
    async def test_ownership_transfer(self, access_control):
        """Test transferring document ownership."""
        # Initially user1 is the owner of doc1
        assert access_control._permissions["doc1"]["owner"] == "user1"
        
        # Transfer ownership to user2
        await access_control.transfer_ownership("doc1", "user1", "user2")
        
        # Verify new ownership
        assert access_control._permissions["doc1"]["owner"] == "user2"
        
        # Old owner should still have full access
        assert await access_control.check_permission("user1", "doc1", "READ") is True
        assert await access_control.check_permission("user1", "doc1", "WRITE") is True
        
        # New owner should now have full permissions
        assert await access_control.check_permission("user2", "doc1", "READ") is True
        assert await access_control.check_permission("user2", "doc1", "WRITE") is True
        assert await access_control.check_permission("user2", "doc1", "DELETE") is True
        assert await access_control.check_permission("user2", "doc1", "SHARE") is True
    
    @pytest.mark.asyncio
    async def test_unauthorized_ownership_transfer(self, access_control):
        """Test unauthorized ownership transfer."""
        # Try to transfer ownership from non-owner
        with pytest.raises(AuthorizationError) as excinfo:
            await access_control.transfer_ownership("doc1", "user2", "user3")
        
        assert "not the owner" in str(excinfo.value)
        
        # Ownership should not have changed
        assert access_control._permissions["doc1"]["owner"] == "user1"
    
    @pytest.mark.asyncio
    async def test_access_control_with_unknown_document(self, access_control):
        """Test access control with unknown document."""
        # Try to check permissions for an unknown document
        assert await access_control.can_access_document("user1", "unknown_doc") is False
        
        # Try to set permissions for an unknown document
        with pytest.raises(ValueError) as excinfo:
            await access_control.grant_access("unknown_doc", "user1", "READ")
        
        assert "Document not found" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_get_document_permissions(self, access_control):
        """Test retrieving document permissions."""
        # Get all permissions for doc1
        permissions = await access_control.get_document_permissions("doc1")
        
        # Verify permissions structure
        assert "owner" in permissions
        assert permissions["owner"] == "user1"
        assert "access" in permissions
        assert "user1" in permissions["access"]
        assert "user2" in permissions["access"]
        assert "group1" in permissions["access"]
        
        # Verify specific permissions
        assert "READ" in permissions["access"]["user2"]
        assert "WRITE" in permissions["access"]["group1"] 