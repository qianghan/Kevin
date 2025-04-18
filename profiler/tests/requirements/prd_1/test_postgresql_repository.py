"""
Tests for PostgreSQL profile repository implementation.

This module contains tests for the PostgreSQL implementation of the ProfileRepositoryInterface.
"""

import os
import sys
import pytest
import uuid
from datetime import datetime
from typing import Dict, List, Any, AsyncGenerator

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path to allow importing from profiler modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from profiler.app.backend.services.profile import (
    PostgreSQLProfileRepository, 
    Profile, 
    ProfileConfig, 
    ProfileSectionData,
    Base
)
from profiler.app.backend.utils.errors import ResourceNotFoundError

# Test PostgreSQL connection URL - using SQLite in memory for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Fixture for creating a test database engine."""
    engine = create_async_engine(TEST_DB_URL, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def config() -> Dict[str, Any]:
    """Fixture for PostgreSQL repository configuration."""
    return {
        "url": TEST_DB_URL,
        "echo": True,
        "pool_size": 5,
        "max_overflow": 10
    }


@pytest.fixture
async def repository(config: Dict[str, Any]) -> AsyncGenerator[PostgreSQLProfileRepository, None]:
    """Fixture for creating a test repository."""
    repo = PostgreSQLProfileRepository(config)
    await repo.initialize()
    yield repo
    await repo.shutdown()


@pytest.fixture
def sample_profile() -> Profile:
    """Fixture for creating a sample profile."""
    now = datetime.utcnow().isoformat()
    profile_id = str(uuid.uuid4())
    
    # Create a sample profile
    profile = Profile(
        profile_id=profile_id,
        user_id="test_user",
        current_section="academic",
        sections={
            "academic": ProfileSectionData(
                section_id="academic",
                title="Academic Information",
                data={"school": "Test University", "gpa": 3.8},
                metadata={"order": 1},
                completed=True,
                last_updated=now
            ),
            "extracurricular": ProfileSectionData(
                section_id="extracurricular",
                title="Extracurricular Activities",
                data={"activities": ["Chess Club", "Debate Team"]},
                metadata={"order": 2},
                completed=False,
                last_updated=now
            )
        },
        metadata={"test": True},
        config=ProfileConfig(
            sections=["academic", "extracurricular", "personal"],
            required_sections=["academic"],
            section_dependencies={"personal": ["academic"]},
            validation_rules={}
        ),
        created_at=now,
        last_updated=now,
        status="active"
    )
    
    return profile


@pytest.mark.asyncio
async def test_save_and_get_profile(repository: PostgreSQLProfileRepository, sample_profile: Profile):
    """Test saving and retrieving a profile."""
    # Save the profile
    saved_profile = await repository.save_profile(sample_profile)
    
    # Verify the profile was saved correctly
    assert saved_profile.profile_id == sample_profile.profile_id
    assert saved_profile.user_id == sample_profile.user_id
    
    # Get the profile
    retrieved_profile = await repository.get_profile(sample_profile.profile_id)
    
    # Verify the retrieved profile matches the saved profile
    assert retrieved_profile.profile_id == sample_profile.profile_id
    assert retrieved_profile.user_id == sample_profile.user_id
    assert retrieved_profile.current_section == sample_profile.current_section
    assert retrieved_profile.status == sample_profile.status
    
    # Verify sections
    assert len(retrieved_profile.sections) == 2
    assert "academic" in retrieved_profile.sections
    assert "extracurricular" in retrieved_profile.sections
    
    # Verify section data
    academic = retrieved_profile.sections["academic"]
    assert academic.title == "Academic Information"
    assert academic.data["school"] == "Test University"
    assert academic.data["gpa"] == 3.8
    assert academic.completed is True
    
    extracurricular = retrieved_profile.sections["extracurricular"]
    assert extracurricular.title == "Extracurricular Activities"
    assert "Chess Club" in extracurricular.data["activities"]
    assert "Debate Team" in extracurricular.data["activities"]
    assert extracurricular.completed is False


@pytest.mark.asyncio
async def test_update_profile(repository: PostgreSQLProfileRepository, sample_profile: Profile):
    """Test updating a profile."""
    # Save the profile
    saved_profile = await repository.save_profile(sample_profile)
    
    # Update the profile
    saved_profile.current_section = "personal"
    saved_profile.sections["academic"].data["gpa"] = 4.0
    saved_profile.sections["academic"].data["graduation_year"] = 2025
    
    # Add a new section
    saved_profile.sections["personal"] = ProfileSectionData(
        section_id="personal",
        title="Personal Information",
        data={"hobby": "Reading"},
        metadata={},
        completed=False,
        last_updated=datetime.utcnow().isoformat()
    )
    
    # Save the updated profile
    updated_profile = await repository.save_profile(saved_profile)
    
    # Get the updated profile
    retrieved_profile = await repository.get_profile(sample_profile.profile_id)
    
    # Verify the updates
    assert retrieved_profile.current_section == "personal"
    assert retrieved_profile.sections["academic"].data["gpa"] == 4.0
    assert retrieved_profile.sections["academic"].data["graduation_year"] == 2025
    assert "personal" in retrieved_profile.sections
    assert retrieved_profile.sections["personal"].data["hobby"] == "Reading"


@pytest.mark.asyncio
async def test_delete_profile(repository: PostgreSQLProfileRepository, sample_profile: Profile):
    """Test deleting a profile."""
    # Save the profile
    saved_profile = await repository.save_profile(sample_profile)
    
    # Verify the profile exists
    retrieved_profile = await repository.get_profile(sample_profile.profile_id)
    assert retrieved_profile.profile_id == sample_profile.profile_id
    
    # Delete the profile
    await repository.delete_profile(sample_profile.profile_id)
    
    # Verify the profile was deleted
    with pytest.raises(ResourceNotFoundError):
        await repository.get_profile(sample_profile.profile_id)


@pytest.mark.asyncio
async def test_list_profiles(repository: PostgreSQLProfileRepository, sample_profile: Profile):
    """Test listing profiles."""
    # Save the profile
    await repository.save_profile(sample_profile)
    
    # Create and save another profile
    profile2 = Profile(
        profile_id=str(uuid.uuid4()),
        user_id="test_user2",
        current_section="academic",
        sections={},
        metadata={},
        config=ProfileConfig(
            sections=["academic"],
            required_sections=["academic"],
            section_dependencies={},
            validation_rules={}
        ),
        created_at=datetime.utcnow().isoformat(),
        last_updated=datetime.utcnow().isoformat(),
        status="active"
    )
    await repository.save_profile(profile2)
    
    # List all profiles
    all_profiles = await repository.list_profiles()
    assert len(all_profiles) == 2
    
    # List profiles for test_user
    user_profiles = await repository.list_profiles(user_id="test_user")
    assert len(user_profiles) == 1
    assert user_profiles[0].profile_id == sample_profile.profile_id
    
    # List profiles for test_user2
    user2_profiles = await repository.list_profiles(user_id="test_user2")
    assert len(user2_profiles) == 1
    assert user2_profiles[0].profile_id == profile2.profile_id


@pytest.mark.asyncio
async def test_nonexistent_profile(repository: PostgreSQLProfileRepository):
    """Test handling of nonexistent profiles."""
    with pytest.raises(ResourceNotFoundError):
        await repository.get_profile("nonexistent_id")
    
    with pytest.raises(ResourceNotFoundError):
        await repository.delete_profile("nonexistent_id") 