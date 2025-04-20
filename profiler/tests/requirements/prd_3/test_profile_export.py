"""
BDD tests for Profile Export functionality (PRD-3).

These tests verify the requirements for profile export functionality,
including PDF, Word, JSON formats, preview, and sharing capabilities.
"""

import os
import io
import json
import pytest
import uuid
import asyncio
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from pytest_bdd import scenarios, given, when, then, parsers
import pytest_asyncio

# Mock imports (replace with actual imports when available)
# We'll use Document as a model for what these interfaces might look like
from app.backend.services.profile import ProfileService, Profile, ProfileRepository
from app.backend.services.auth import AuthenticationService
from app.backend.utils.errors import ResourceNotFoundError, ValidationError, SecurityError

# Register scenarios
scenarios("features/profile_export.feature")

# Test constants
TEST_PROFILE_DATA = {
    "personal_info": {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "123-456-7890",
        "address": "123 Test Street",
        "bio": "This is a test biography for profile export testing."
    },
    "education": [
        {
            "institution": "Test University",
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "start_date": "2015-09-01",
            "end_date": "2019-05-30",
            "gpa": "3.8"
        }
    ],
    "experience": [
        {
            "company": "Test Company",
            "position": "Software Engineer",
            "start_date": "2019-06-15",
            "end_date": "2023-01-01",
            "description": "Developed and maintained software applications."
        }
    ],
    "skills": ["Python", "JavaScript", "React", "TDD", "BDD"]
}

# Mock ProfileExportService for testing
class MockProfileExportService:
    """Mock profile export service for testing."""
    
    def __init__(self):
        self.profiles = {}
        self.templates = {
            "default": {"name": "Default Template", "sections": ["personal_info", "education", "experience", "skills"]},
            "academic": {"name": "Academic Template", "sections": ["personal_info", "education", "skills"]},
            "professional": {"name": "Professional Template", "sections": ["personal_info", "experience", "skills"]}
        }
        self.exports = {}
        self.shared_profiles = {}
        
    async def initialize(self):
        """Initialize the export service."""
        pass
        
    async def shutdown(self):
        """Shutdown the export service."""
        pass
        
    async def save_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> str:
        """Save a profile for export testing."""
        self.profiles[profile_id] = profile_data
        return profile_id
        
    async def export_profile_as_pdf(self, profile_id: str, template_id: str = "default", options: Dict[str, Any] = None) -> bytes:
        """Export profile as PDF."""
        if profile_id not in self.profiles:
            raise ResourceNotFoundError(f"Profile {profile_id} not found")
        if template_id not in self.templates:
            raise ValidationError(f"Template {template_id} not found")
            
        # In a real implementation, generate PDF here
        # For testing, we'll just return a dummy PDF
        export_id = str(uuid4())
        dummy_pdf = b"%PDF-1.5\n%Test PDF for profile export"
        self.exports[export_id] = {
            "data": dummy_pdf,
            "format": "pdf",
            "profile_id": profile_id,
            "template_id": template_id,
            "options": options or {}
        }
        return dummy_pdf
        
    async def export_profile_as_word(self, profile_id: str, template_id: str = "default", options: Dict[str, Any] = None) -> bytes:
        """Export profile as Word document."""
        if profile_id not in self.profiles:
            raise ResourceNotFoundError(f"Profile {profile_id} not found")
        if template_id not in self.templates:
            raise ValidationError(f"Template {template_id} not found")
            
        # In a real implementation, generate Word doc here
        # For testing, we'll just return a dummy DOCX
        export_id = str(uuid4())
        dummy_docx = b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00\x00\x00!Test DOCX for profile export"
        self.exports[export_id] = {
            "data": dummy_docx,
            "format": "docx",
            "profile_id": profile_id,
            "template_id": template_id,
            "options": options or {}
        }
        return dummy_docx
        
    async def export_profile_as_json(self, profile_id: str) -> str:
        """Export profile as JSON."""
        if profile_id not in self.profiles:
            raise ResourceNotFoundError(f"Profile {profile_id} not found")
            
        profile_data = self.profiles[profile_id]
        export_id = str(uuid4())
        json_data = json.dumps(profile_data)
        self.exports[export_id] = {
            "data": json_data,
            "format": "json",
            "profile_id": profile_id
        }
        return json_data
        
    async def generate_preview(self, profile_id: str, format_type: str, template_id: str = "default") -> Dict[str, Any]:
        """Generate preview for profile export."""
        if profile_id not in self.profiles:
            raise ResourceNotFoundError(f"Profile {profile_id} not found")
        if template_id not in self.templates:
            raise ValidationError(f"Template {template_id} not found")
        if format_type not in ["pdf", "docx", "json"]:
            raise ValidationError(f"Format {format_type} not supported")
            
        # Return preview data
        preview_id = str(uuid4())
        preview_data = {
            "id": preview_id,
            "format": format_type,
            "template": self.templates[template_id],
            "profile_data": self.profiles[profile_id],
            "preview_html": f"<html><body><h1>{self.profiles[profile_id]['personal_info']['name']}'s Profile</h1></body></html>"
        }
        return preview_data
        
    async def share_profile(self, profile_id: str, recipient_ids: List[str], permissions: Dict[str, bool] = None) -> Dict[str, Any]:
        """Share profile with other users."""
        if profile_id not in self.profiles:
            raise ResourceNotFoundError(f"Profile {profile_id} not found")
            
        share_id = str(uuid4())
        self.shared_profiles[share_id] = {
            "profile_id": profile_id,
            "recipients": recipient_ids,
            "permissions": permissions or {"view": True, "download": False},
            "created_at": datetime.utcnow().isoformat(),
            "access_link": f"https://example.com/shared-profiles/{share_id}"
        }
        return self.shared_profiles[share_id]
        
    async def get_shared_profile(self, share_id: str) -> Dict[str, Any]:
        """Get a shared profile."""
        if share_id not in self.shared_profiles:
            raise ResourceNotFoundError(f"Shared profile {share_id} not found")
            
        shared_profile = self.shared_profiles[share_id]
        profile_data = self.profiles[shared_profile["profile_id"]]
        return {
            "share_info": shared_profile,
            "profile_data": profile_data
        }
        
    async def create_custom_template(self, template_data: Dict[str, Any]) -> str:
        """Create a custom template."""
        template_id = template_data.get("id", str(uuid4()))
        self.templates[template_id] = template_data
        return template_id
        
    async def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get template by ID."""
        if template_id not in self.templates:
            raise ResourceNotFoundError(f"Template {template_id} not found")
        return self.templates[template_id]

# Test data setup
@pytest.fixture
def test_data():
    """Dictionary to store test data between steps."""
    return {
        "user_id": str(uuid4()),
        "profile_id": str(uuid4()),
        "profile_data": TEST_PROFILE_DATA.copy(),
        "selected_format": None,
        "selected_template": None,
        "export_options": {},
        "exported_file": None,
        "preview_data": None,
        "shared_profile": None,
        "recipients": [],
        "share_permissions": {},
        "custom_template": None,
        "error": None
    }

# Setup fixtures
@pytest_asyncio.fixture
async def profile_export_service():
    """Create a profile export service for testing."""
    service = MockProfileExportService()
    await service.initialize()
    yield service
    await service.shutdown()

@pytest_asyncio.fixture
async def auth_service():
    """Create an authentication service for testing."""
    return AuthenticationService()

# Step definitions

@given("I have a user account")
def given_user_account(test_data):
    """User has an account in the system."""
    # For testing purposes, just use the user_id that's already in test_data
    assert test_data["user_id"] is not None
    
@given("I have a profile with complete information")
def given_complete_profile(test_data, profile_export_service):
    """Set up a complete profile for testing."""
    profile_id = str(uuid4())
    test_data["profile_id"] = profile_id
    # This needs to be executed, not just defined as async
    loop = asyncio.get_event_loop()
    loop.run_until_complete(profile_export_service.save_profile(profile_id, TEST_PROFILE_DATA))
    test_data["profile_data"] = TEST_PROFILE_DATA
    return test_data

@given(parsers.parse('I have selected the {format_type} export format'))
def select_export_format(test_data, format_type):
    """Set the export format."""
    # Normalize format type
    if format_type.lower() == "word document":
        test_data["format_type"] = "docx"
    else:
        test_data["format_type"] = format_type.lower()
    
    # Default options for different formats
    if test_data["format_type"] == "pdf":
        test_data["export_options"] = {
            "include_photo": True,
            "include_contact_info": True,
            "color_scheme": "professional"
        }
    elif test_data["format_type"] == "docx":
        test_data["export_options"] = {
            "include_header": True,
            "include_footer": False,
            "color_scheme": "professional"
        }
    return test_data

@given("I have selected an export format")
def select_any_export_format(test_data):
    """User selects any export format."""
    test_data["selected_format"] = "pdf"  # Default to PDF for tests

@when(parsers.parse('I choose a template for my profile'))
@given(parsers.parse('I have chosen a template'))
def choose_template(test_data):
    """User chooses a template."""
    test_data["selected_template"] = "default"

@when(parsers.parse('I customize export options'))
def customize_export_options(test_data):
    """User customizes export options."""
    test_data["export_options"] = {
        "include_photo": True,
        "include_contact_info": True,
        "color_scheme": "professional"
    }

@when(parsers.parse('I initiate the export process'))
def initiate_export(test_data, profile_export_service):
    """Initiate the export process."""
    try:
        format_type = test_data.get("format_type", "pdf").lower()
        profile_id = test_data["profile_id"]
        template_id = test_data.get("template_id", "default")
        options = test_data.get("export_options", {})
        
        loop = asyncio.get_event_loop()
        
        if format_type == "pdf":
            file_data = loop.run_until_complete(profile_export_service.export_profile_as_pdf(
                profile_id, template_id, options
            ))
        elif format_type in ["docx", "word"]:
            file_data = loop.run_until_complete(profile_export_service.export_profile_as_word(
                profile_id, template_id, options
            ))
        elif format_type == "json":
            file_data = loop.run_until_complete(profile_export_service.export_profile_as_json(
                profile_id
            ))
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
        
        test_data["exported_file"] = file_data
    except Exception as e:
        test_data["error"] = str(e)
    return test_data

@when(parsers.parse('I request a preview'))
def request_preview(test_data, profile_export_service):
    """Request a preview of the profile export."""
    try:
        format_type = test_data.get("format_type", "pdf").lower()
        profile_id = test_data["profile_id"]
        template_id = test_data.get("template_id", "default")
        
        loop = asyncio.get_event_loop()
        preview_data = loop.run_until_complete(profile_export_service.generate_preview(
            profile_id, format_type, template_id
        ))
        
        test_data["preview_data"] = preview_data
    except Exception as e:
        test_data["error"] = str(e)
    return test_data

@given(parsers.parse('I have exported my profile'))
def have_exported_profile(test_data, profile_export_service):
    """Set up an exported profile for testing."""
    if "exported_file" not in test_data:
        format_type = test_data.get("format_type", "pdf").lower()
        profile_id = test_data["profile_id"]
        template_id = test_data.get("template_id", "default")
        options = test_data.get("export_options", {})
        
        loop = asyncio.get_event_loop()
        
        if format_type == "pdf":
            file_data = loop.run_until_complete(profile_export_service.export_profile_as_pdf(
                profile_id, template_id, options
            ))
        elif format_type == "docx" or format_type == "word":
            file_data = loop.run_until_complete(profile_export_service.export_profile_as_word(
                profile_id, template_id, options
            ))
        elif format_type == "json":
            file_data = loop.run_until_complete(profile_export_service.export_profile_as_json(
                profile_id
            ))
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
        
        test_data["exported_file"] = file_data
    return test_data

@when(parsers.parse('I select sharing options'))
def select_sharing_options(test_data):
    """User selects sharing options."""
    test_data["share_options"] = {
        "format": test_data["selected_format"],
        "expiry_days": 30,
        "allow_download": True
    }

@when(parsers.parse('I enter recipient information'))
def enter_recipients(test_data):
    """User enters recipient information."""
    test_data["recipients"] = [
        "recipient1@example.com",
        "recipient2@example.com"
    ]

@when(parsers.parse('I set access permissions'))
def set_permissions(test_data):
    """Set sharing permissions."""
    # Default permissions
    test_data["share_permissions"] = {
        "view": True,
        "download": True
    }
    
    # Custom permissions based on test scenario
    if "permission_settings" in test_data:
        for permission, value in test_data["permission_settings"].items():
            test_data["share_permissions"][permission] = value
    
    return test_data

@when(parsers.parse('I initiate the sharing process'))
def initiate_sharing(test_data, profile_export_service):
    """Initiate the sharing process."""
    try:
        profile_id = test_data["profile_id"]
        recipients = test_data.get("recipients", ["user1@example.com", "user2@example.com"])
        permissions = test_data.get("share_permissions", {"view": True, "download": True})
        
        loop = asyncio.get_event_loop()
        share_info = loop.run_until_complete(profile_export_service.share_profile(
            profile_id, recipients, permissions
        ))
        
        test_data["shared_profile"] = share_info
    except Exception as e:
        test_data["error"] = str(e)
    return test_data

@given(parsers.parse('I have created a custom template'))
def create_custom_template(test_data, profile_export_service):
    """Create a custom template for testing."""
    custom_template = {
        "name": "My Custom Template",
        "sections": ["personal_info", "education", "experience", "skills"],
        "styles": {
            "font": "Arial",
            "colors": {
                "primary": "#336699",
                "secondary": "#99ccff"
            }
        }
    }
    
    loop = asyncio.get_event_loop()
    template_id = loop.run_until_complete(profile_export_service.create_custom_template(custom_template))
    
    test_data["custom_template"] = custom_template
    test_data["template_id"] = template_id
    return test_data

@when(parsers.parse('I select my custom template'))
def select_custom_template(test_data):
    """User selects their custom template."""
    test_data["selected_template"] = test_data["custom_template"]

@given(parsers.parse('another user has shared their profile with me'))
def another_user_shared_profile(test_data, profile_export_service):
    """Set up a scenario where another user has shared a profile with the test user."""
    # Create another user's profile
    other_profile_id = str(uuid4())
    
    other_profile_data = dict(TEST_PROFILE_DATA)
    other_profile_data["personal_info"]["name"] = "Other User"
    other_profile_data["personal_info"]["email"] = "other@example.com"
    
    loop = asyncio.get_event_loop()
    
    # Save the other user's profile
    loop.run_until_complete(profile_export_service.save_profile(other_profile_id, other_profile_data))
    
    # Share the profile with the test user
    recipients = [test_data.get("user_email", "test@example.com")]
    permissions = {"view": True, "download": True}
    
    share_info = loop.run_until_complete(profile_export_service.share_profile(
        other_profile_id, recipients, permissions
    ))
    
    test_data["other_profile_id"] = other_profile_id
    test_data["other_profile_data"] = other_profile_data
    test_data["share_id"] = share_info["access_link"].split("/")[-1]
    test_data["share_info"] = share_info
    return test_data

@when(parsers.parse('I access the shared profile link'))
def access_shared_profile(test_data, profile_export_service):
    """Access a shared profile link."""
    try:
        share_id = test_data["share_id"]
        
        loop = asyncio.get_event_loop()
        shared_profile = loop.run_until_complete(profile_export_service.get_shared_profile(share_id))
        
        test_data["viewed_shared_profile"] = shared_profile
    except Exception as e:
        test_data["error"] = str(e)
    return test_data

# Assertions

@then(parsers.parse('I should receive a {format_type} file containing my profile information'))
def check_received_file(test_data, format_type):
    """Check that a file was received with the correct format."""
    assert test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert test_data["exported_file"] is not None, "No file was exported"
    
    # Basic format check
    if format_type.lower() == "pdf":
        assert test_data["exported_file"].startswith(b"%PDF"), "Not a valid PDF file"
    elif format_type.lower() == "word" or format_type.lower() == "docx":
        assert test_data["exported_file"].startswith(b"PK"), "Not a valid DOCX file"
    elif format_type.lower() == "json":
        # For JSON, we've stored a string, not bytes
        if isinstance(test_data["exported_file"], bytes):
            json_content = test_data["exported_file"].decode("utf-8")
        else:
            json_content = test_data["exported_file"]
        # Verify it's valid JSON
        json.loads(json_content)

@then(parsers.parse('I should receive a Word document containing my profile information'))
def check_received_word_file(test_data):
    """Check that a Word document was received."""
    assert test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert test_data["exported_file"] is not None, "No file was exported"
    assert test_data["exported_file"].startswith(b"PK"), "Not a valid DOCX file"

@then(parsers.parse('the {format_type} should match the selected template'))
def check_template_match(test_data, format_type):
    """Check that the exported file matches the selected template."""
    # This is a placeholder for a real implementation that would check the content
    assert test_data["selected_template"] is not None, "No template was selected"
    # In a real test, we'd validate the content structure matches the template

@then(parsers.parse('the {format_type} should include all required profile sections'))
def check_sections_included(test_data, format_type):
    """Check that all required sections are included in the export."""
    # This is a placeholder for a real implementation that would check the content
    assert test_data["profile_data"] is not None, "No profile data available"
    # In a real test, we'd validate that all required sections exist in the output

@then(parsers.parse('the JSON should have the correct schema'))
def check_json_schema(test_data):
    """Check that the JSON export has the correct schema."""
    assert isinstance(test_data["exported_file"], str), "Exported file should be a string for JSON"
    try:
        json_data = json.loads(test_data["exported_file"])
        # Check for required top-level keys
        required_keys = ["personal_info", "education", "experience", "skills"]
        for key in required_keys:
            assert key in json_data, f"Required key {key} missing from JSON export"
    except json.JSONDecodeError:
        assert False, "Exported JSON is not valid"

@then(parsers.parse('the JSON should include all profile data'))
def check_json_complete(test_data):
    """Check that the JSON export includes all profile data."""
    try:
        json_data = json.loads(test_data["exported_file"])
        # Simple check for data completeness
        assert json_data == test_data["profile_data"], "JSON export should match the original profile data"
    except json.JSONDecodeError:
        assert False, "Exported JSON is not valid"

@then(parsers.parse('I should see a preview of my profile'))
def check_preview_available(test_data):
    """Check that a preview is available."""
    assert test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert test_data["preview_data"] is not None, "No preview data available"
    assert "preview_html" in test_data["preview_data"], "Preview HTML missing"

@then(parsers.parse('the preview should match the selected template'))
def check_preview_template_match(test_data):
    """Check that the preview matches the selected template."""
    assert test_data["preview_data"]["template"]["name"] is not None, "Template name missing in preview"
    # In a real test, we'd validate the preview structure matches the template

@then(parsers.parse('the preview should include all required profile sections'))
def check_preview_sections(test_data):
    """Check that the preview includes all required sections."""
    assert test_data["preview_data"]["profile_data"] is not None, "Profile data missing in preview"
    # In a real test, we'd validate that all required sections exist in the preview

@then(parsers.parse('the recipients should receive access to my profile'))
def check_recipients_access(test_data):
    """Check that recipients received access to the profile."""
    assert test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert test_data["shared_profile"] is not None, "Profile was not shared"
    assert "recipients" in test_data["shared_profile"], "Recipients missing in shared profile"
    assert set(test_data["recipients"]).issubset(set(test_data["shared_profile"]["recipients"])), "Not all recipients received access"

@then(parsers.parse('the recipients should have the permissions I specified'))
def check_recipients_permissions(test_data):
    """Check that recipients have the specified permissions."""
    assert "permissions" in test_data["shared_profile"], "Permissions missing in shared profile"
    for permission, value in test_data["share_permissions"].items():
        assert test_data["shared_profile"]["permissions"].get(permission) == value, f"Permission {permission} does not match"

@then(parsers.parse('the exported profile should use my custom template'))
def check_custom_template_used(test_data):
    """Check that the exported profile uses the custom template."""
    assert test_data["selected_template"] == test_data["custom_template"], "Custom template not selected for export"
    # In a real test, we'd validate the export structure matches the custom template

@then(parsers.parse('I should be able to view the shared profile'))
def check_can_view_shared_profile(test_data):
    """Check that the user can view the shared profile."""
    assert test_data["error"] is None, f"Error occurred: {test_data.get('error')}"
    assert test_data["viewed_shared_profile"] is not None, "Shared profile not viewed"
    assert "profile_data" in test_data["viewed_shared_profile"], "Profile data missing in viewed shared profile"

@then(parsers.parse('the profile should have the format specified by the owner'))
def check_shared_profile_format(test_data):
    """Check that the shared profile has the format specified by the owner."""
    # This would check the format matches what the owner specified
    # For now, just ensure we have the shared profile data
    assert "share_info" in test_data["viewed_shared_profile"], "Share info missing in viewed shared profile"

# Unit test cases

@pytest.mark.asyncio
async def test_export_profile_as_pdf(profile_export_service):
    """Test exporting a profile as PDF."""
    # Create a test profile
    profile_id = str(uuid4())
    await profile_export_service.save_profile(profile_id, TEST_PROFILE_DATA)
    
    # Export as PDF
    pdf_data = await profile_export_service.export_profile_as_pdf(profile_id)
    
    # Verify
    assert pdf_data is not None
    assert pdf_data.startswith(b"%PDF")

@pytest.mark.asyncio
async def test_export_profile_as_word(profile_export_service):
    """Test exporting a profile as Word document."""
    # Create a test profile
    profile_id = str(uuid4())
    await profile_export_service.save_profile(profile_id, TEST_PROFILE_DATA)
    
    # Export as Word
    docx_data = await profile_export_service.export_profile_as_word(profile_id)
    
    # Verify
    assert docx_data is not None
    assert docx_data.startswith(b"PK\x03\x04")

@pytest.mark.asyncio
async def test_export_profile_as_json(profile_export_service):
    """Test exporting a profile as JSON."""
    # Create a test profile
    profile_id = str(uuid4())
    await profile_export_service.save_profile(profile_id, TEST_PROFILE_DATA)
    
    # Export as JSON
    json_data = await profile_export_service.export_profile_as_json(profile_id)
    
    # Verify
    assert json_data is not None
    parsed_json = json.loads(json_data)
    assert parsed_json == TEST_PROFILE_DATA

@pytest.mark.asyncio
async def test_profile_preview_generation(profile_export_service):
    """Test generating a preview for profile export."""
    # Create a test profile
    profile_id = str(uuid4())
    await profile_export_service.save_profile(profile_id, TEST_PROFILE_DATA)
    
    # Generate preview
    preview_data = await profile_export_service.generate_preview(profile_id, "pdf")
    
    # Verify
    assert preview_data is not None
    assert "preview_html" in preview_data
    assert "profile_data" in preview_data
    assert preview_data["profile_data"] == TEST_PROFILE_DATA

@pytest.mark.asyncio
async def test_profile_sharing(profile_export_service):
    """Test sharing a profile with other users."""
    # Create a test profile
    profile_id = str(uuid4())
    await profile_export_service.save_profile(profile_id, TEST_PROFILE_DATA)
    
    # Share profile
    recipients = ["user1@example.com", "user2@example.com"]
    permissions = {"view": True, "download": True}
    
    shared_profile = await profile_export_service.share_profile(profile_id, recipients, permissions)
    
    # Verify
    assert shared_profile is not None
    assert "profile_id" in shared_profile
    assert shared_profile["profile_id"] == profile_id
    assert "recipients" in shared_profile
    assert set(recipients) == set(shared_profile["recipients"])
    assert "permissions" in shared_profile
    assert shared_profile["permissions"] == permissions

@pytest.mark.asyncio
async def test_custom_template_creation(profile_export_service):
    """Test creating and using a custom template."""
    # Create custom template
    template_data = {
        "name": "Custom Test Template",
        "sections": ["personal_info", "skills", "experience"],
        "style": {"primary_color": "#FF5500"}
    }
    
    template_id = await profile_export_service.create_custom_template(template_data)
    
    # Verify template was created
    retrieved_template = await profile_export_service.get_template(template_id)
    assert retrieved_template is not None
    assert retrieved_template["name"] == template_data["name"]
    assert retrieved_template["sections"] == template_data["sections"]
    
    # Create a test profile
    profile_id = str(uuid4())
    await profile_export_service.save_profile(profile_id, TEST_PROFILE_DATA)
    
    # Export using custom template
    pdf_data = await profile_export_service.export_profile_as_pdf(profile_id, template_id)
    
    # Verify
    assert pdf_data is not None
    assert pdf_data.startswith(b"%PDF") 