"""
Test for the switch_section feature in the WebSocket API.

This test specifically targets the _update_state method that we fixed to handle 
switch_section messages properly.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from app.backend.api.websocket import ConnectionManager


@pytest.mark.asyncio
async def test_update_state_switch_section():
    """Test that the _update_state method correctly handles switch_section messages."""
    manager = ConnectionManager()
    
    # Create a mock state
    current_state = {
        "user_id": "test-user",
        "current_section": "academic",
        "sections": {
            "academic": {"status": "in_progress"},
            "extracurricular": {"status": "not_started"},
            "personal": {"status": "not_started"},
            "essays": {"status": "not_started"}
        },
        "current_questions": [],
        "current_answer": None,
        "interaction_count": 0,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    # Test switching to a different section
    message_type = "switch_section"
    message_data = {"section": "personal"}
    raw_data = {
        "type": "switch_section",
        "data": {"section": "personal"}
    }
    
    # Mock the datetime to have a predictable timestamp
    with patch('app.backend.api.websocket.datetime') as mock_datetime:
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_datetime.now.return_value = mock_now
        
        # Call the method
        updated_state = await manager._update_state(
            current_state=current_state,
            message_type=message_type,
            message_data=message_data,
            raw_data=raw_data
        )
    
    # Verify the current_section was updated
    assert updated_state["current_section"] == "personal"
    assert updated_state["interaction_count"] == 1
    
    # Test switching without providing a section (should raise ValueError)
    message_type = "switch_section"
    message_data = {}  # Missing section
    raw_data = {
        "type": "switch_section",
        "data": {}  # Missing section
    }
    
    with pytest.raises(ValueError, match="Invalid section switch data"):
        await manager._update_state(
            current_state=current_state,
            message_type=message_type,
            message_data=message_data,
            raw_data=raw_data
        )


@pytest.mark.asyncio
async def test_update_state_all_section_types():
    """Test that the _update_state method works with all section types."""
    manager = ConnectionManager()
    
    # Create a mock state
    current_state = {
        "user_id": "test-user",
        "current_section": "academic",
        "sections": {
            "academic": {"status": "in_progress"},
            "extracurricular": {"status": "not_started"},
            "personal": {"status": "not_started"},
            "essays": {"status": "not_started"}
        },
        "current_questions": [],
        "current_answer": None,
        "interaction_count": 0,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    # Test each section type
    sections = ["academic", "extracurricular", "personal", "essays"]
    
    for section in sections:
        message_type = "switch_section"
        message_data = {"section": section}
        raw_data = {
            "type": "switch_section",
            "data": {"section": section}
        }
        
        # Call the method
        updated_state = await manager._update_state(
            current_state=current_state,
            message_type=message_type,
            message_data=message_data,
            raw_data=raw_data
        )
        
        # Verify the section was updated correctly
        assert updated_state["current_section"] == section
        
        # Use the updated state for the next iteration
        current_state = updated_state 