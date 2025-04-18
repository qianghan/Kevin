#!/usr/bin/env python3
"""
Profile Migration Script.

This script migrates profiles from one repository type to another, e.g., from JSON files to PostgreSQL.
"""

import os
import sys
import argparse
import asyncio
from typing import List, Optional

# Add parent directory to path to allow importing from profiler modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from profiler.app.backend.utils.logging import get_logger
from profiler.app.backend.utils.config_manager import ConfigManager
from profiler.app.backend.services.profile import (
    ProfileRepositoryInterface,
    JSONFileProfileRepository,
    DatabaseProfileRepository,
    Profile
)

logger = get_logger("profile_migration")


async def get_source_repository(source_type: str, config: ConfigManager) -> ProfileRepositoryInterface:
    """
    Get the source repository.
    
    Args:
        source_type: The type of the source repository ('json' or 'postgresql')
        config: Configuration manager
        
    Returns:
        The source repository
        
    Raises:
        ValueError: If the source_type is invalid
    """
    if source_type == "json":
        storage_dir = config.get_config().get("profile_service", {}).get("storage_dir", "./data/profiles")
        repo = JSONFileProfileRepository(storage_dir=storage_dir)
    elif source_type in ("postgresql", "database"):
        db_config = config.get_config().get("database", {})
        repo = DatabaseProfileRepository(config=db_config)
    else:
        raise ValueError(f"Invalid source type: {source_type}")
    
    await repo.initialize()
    return repo


async def get_destination_repository(destination_type: str, config: ConfigManager) -> ProfileRepositoryInterface:
    """
    Get the destination repository.
    
    Args:
        destination_type: The type of the destination repository ('json' or 'postgresql')
        config: Configuration manager
        
    Returns:
        The destination repository
        
    Raises:
        ValueError: If the destination_type is invalid
    """
    if destination_type == "json":
        storage_dir = config.get_config().get("profile_service", {}).get("storage_dir", "./data/profiles")
        repo = JSONFileProfileRepository(storage_dir=storage_dir)
    elif destination_type in ("postgresql", "database"):
        db_config = config.get_config().get("database", {})
        repo = DatabaseProfileRepository(config=db_config)
    else:
        raise ValueError(f"Invalid destination type: {destination_type}")
    
    await repo.initialize()
    return repo


async def migrate_profiles(source_repo: ProfileRepositoryInterface, 
                          destination_repo: ProfileRepositoryInterface,
                          user_id: Optional[str] = None) -> int:
    """
    Migrate profiles from source to destination repository.
    
    Args:
        source_repo: Source repository
        destination_repo: Destination repository
        user_id: Optional user ID to filter profiles by
        
    Returns:
        Number of profiles migrated
    """
    # Get profiles from source repository
    profiles = await source_repo.list_profiles(user_id=user_id)
    logger.info(f"Found {len(profiles)} profiles to migrate" + (f" for user {user_id}" if user_id else ""))
    
    # Migrate each profile
    migrated_count = 0
    for profile in profiles:
        try:
            # Save profile to destination repository
            await destination_repo.save_profile(profile)
            logger.info(f"Migrated profile {profile.profile_id} for user {profile.user_id}")
            migrated_count += 1
        except Exception as e:
            logger.error(f"Failed to migrate profile {profile.profile_id}: {str(e)}")
    
    logger.info(f"Migration complete. Migrated {migrated_count}/{len(profiles)} profiles.")
    return migrated_count


async def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description="Migrate profiles between repositories")
    parser.add_argument("--source", choices=["json", "postgresql", "database"], default="json",
                        help="Source repository type (default: json)")
    parser.add_argument("--destination", choices=["json", "postgresql", "database"], default="postgresql",
                        help="Destination repository type (default: postgresql)")
    parser.add_argument("--config", default="./profiler/app/backend/config.yaml",
                        help="Path to configuration file (default: ./profiler/app/backend/config.yaml)")
    parser.add_argument("--user-id", help="Optional user ID to filter profiles by")
    
    args = parser.parse_args()
    
    if args.source == args.destination:
        logger.error("Source and destination repositories must be different")
        sys.exit(1)
    
    try:
        # Load configuration
        config = ConfigManager(args.config)
        
        # Get repositories
        source_repo = await get_source_repository(args.source, config)
        destination_repo = await get_destination_repository(args.destination, config)
        
        # Migrate profiles
        migrated_count = await migrate_profiles(source_repo, destination_repo, args.user_id)
        
        # Shutdown repositories
        await source_repo.shutdown()
        await destination_repo.shutdown()
        
        logger.info(f"Successfully migrated {migrated_count} profiles.")
        
    except Exception as e:
        logger.exception(f"Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 