#!/usr/bin/env python3
"""
Test script for PostgreSQL connection.

This script tests the connection to the PostgreSQL database using the repository implementation.
It can be used to verify that the Docker container setup works correctly.
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime

# Add parent directory to path to allow importing from profiler modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from profiler.app.backend.utils.logging import get_logger
from profiler.app.backend.services.profile import (
    PostgreSQLProfileRepository,
    Profile,
    ProfileConfig,
    ProfileSectionData
)
from profiler.app.backend.utils.errors import ResourceNotFoundError

logger = get_logger("postgres_test")


async def test_connection(connection_url: str) -> bool:
    """
    Test the connection to the PostgreSQL database.
    
    Args:
        connection_url: PostgreSQL connection URL
    
    Returns:
        True if the connection is successful, False otherwise
    """
    logger.info(f"Testing connection to PostgreSQL: {connection_url.split('@')[-1]}")
    
    # Set environment variable for database URL
    os.environ["PROFILER_DATABASE__URL"] = connection_url
    
    # Create repository
    repo = PostgreSQLProfileRepository()
    
    try:
        # Initialize repository (this creates the database structure)
        await repo.initialize()
        logger.info("Database connection and initialization successful")
        
        # Create a test profile
        test_profile = Profile(
            profile_id="test-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            user_id="postgres-test-user",
            current_section="test",
            sections={
                "test": ProfileSectionData(
                    section_id="test",
                    title="Test Section",
                    data={"test": "data"},
                    metadata={},
                    completed=False,
                    last_updated=datetime.utcnow().isoformat()
                )
            },
            metadata={"test": True, "docker": True},
            config=ProfileConfig(
                sections=["test"],
                required_sections=["test"],
                section_dependencies={},
                validation_rules={}
            ),
            created_at=datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat(),
            status="test"
        )
        
        # Save the profile
        logger.info(f"Creating test profile with ID: {test_profile.profile_id}")
        saved_profile = await repo.save_profile(test_profile)
        logger.info(f"Test profile created successfully: {saved_profile.profile_id}")
        
        # Retrieve the profile
        retrieved_profile = await repo.get_profile(test_profile.profile_id)
        logger.info(f"Test profile retrieved successfully: {retrieved_profile.profile_id}")
        
        # List profiles
        profiles = await repo.list_profiles(user_id="postgres-test-user")
        logger.info(f"Listed {len(profiles)} profiles for test user")
        
        # Delete the profile
        await repo.delete_profile(test_profile.profile_id)
        logger.info(f"Test profile deleted successfully: {test_profile.profile_id}")
        
        # Verify deletion
        try:
            await repo.get_profile(test_profile.profile_id)
            logger.error("Profile was not deleted properly")
            return False
        except ResourceNotFoundError:
            logger.info("Profile deletion verified")
        
        # Clean up
        await repo.shutdown()
        logger.info("Database connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Error testing PostgreSQL connection: {str(e)}")
        return False


async def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(description="Test PostgreSQL connection")
    parser.add_argument("--url", default="postgresql+asyncpg://postgres:postgres@localhost:5432/profiler",
                        help="PostgreSQL connection URL")
    
    args = parser.parse_args()
    
    # Test connection
    success = await test_connection(args.url)
    
    if success:
        logger.info("PostgreSQL connection test PASSED ✓")
        sys.exit(0)
    else:
        logger.error("PostgreSQL connection test FAILED ✗")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 