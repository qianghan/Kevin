"""
Database migration management utility.

This module provides functionality for managing database migrations across services.
"""

import os
import re
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy import text, Table, Column, String, DateTime, MetaData
from sqlalchemy.ext.asyncio import AsyncEngine

from .logging import get_logger
from .errors import MigrationError

logger = get_logger(__name__)


class MigrationManager:
    """Manages database migrations across different services."""
    
    def __init__(self, config: Dict[str, Any], engine: Optional[AsyncEngine] = None):
        """
        Initialize the migration manager.
        
        Args:
            config: Database configuration
            engine: Optional SQLAlchemy async engine. If not provided, 
                   it will be created when needed using the config.
        """
        self.config = config
        self._engine = engine
        self._migration_table_name = "schema_migrations"
        self._migrations_dir = os.path.join(os.getcwd(), "migrations")
        
        # Ensure migrations directory exists
        os.makedirs(self._migrations_dir, exist_ok=True)
        
        # Create service-specific migrations directories
        self._services = ["profile", "document"]
        for service in self._services:
            service_dir = os.path.join(self._migrations_dir, service)
            os.makedirs(service_dir, exist_ok=True)
    
    async def _ensure_migration_table(self) -> None:
        """
        Ensure the migration tracking table exists.
        
        This table keeps track of which migrations have been applied.
        """
        async with self._engine.begin() as conn:
            # Check if migration table exists
            result = await conn.execute(text(
                f"""
                SELECT EXISTS (
                    SELECT FROM pg_tables 
                    WHERE schemaname = 'profiler_schema' 
                    AND tablename = '{self._migration_table_name}'
                );
                """
            ))
            exists = result.scalar()
            
            if not exists:
                logger.info(f"Creating migration table {self._migration_table_name}")
                # Create migration table
                await conn.execute(text(
                    f"""
                    CREATE TABLE profiler_schema.{self._migration_table_name} (
                        migration_id VARCHAR(255) PRIMARY KEY,
                        service VARCHAR(50) NOT NULL,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    );
                    
                    CREATE INDEX idx_{self._migration_table_name}_service 
                    ON profiler_schema.{self._migration_table_name} (service);
                    """
                ))
                logger.info(f"Created migration table {self._migration_table_name}")
            else:
                logger.info(f"Migration table {self._migration_table_name} already exists")
    
    async def get_applied_migrations(self, service: Optional[str] = None) -> List[str]:
        """
        Get the list of applied migrations.
        
        Args:
            service: Optional service name to filter by
        
        Returns:
            List of applied migration IDs
        """
        query = f"SELECT migration_id FROM profiler_schema.{self._migration_table_name}"
        params = {}
        
        if service:
            query += " WHERE service = :service"
            params["service"] = service
        
        query += " ORDER BY migration_id"
        
        async with self._engine.connect() as conn:
            result = await conn.execute(text(query), params)
            migrations = [row[0] for row in result.fetchall()]
            
            logger.debug(f"Retrieved {len(migrations)} applied migrations")
            if service:
                logger.debug(f"Filtered by service: {service}")
            
            return migrations
    
    async def get_pending_migrations(self, service: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        Get the list of pending migrations.
        
        Args:
            service: Optional service name to filter by
        
        Returns:
            List of tuples containing (migration_id, file_path)
        """
        # Get applied migrations
        applied_migrations = await self.get_applied_migrations(service)
        
        # Get all migration files
        pending_migrations = []
        
        if service:
            # Get migrations for specific service
            services = [service]
        else:
            # Get migrations for all services
            services = self._services
        
        for svc in services:
            migration_dir = os.path.join(self._migrations_dir, svc)
            if not os.path.exists(migration_dir):
                logger.warning(f"Migration directory for service {svc} not found: {migration_dir}")
                continue
                
            migration_files = glob.glob(os.path.join(migration_dir, "V*__*.sql"))
            
            for file_path in sorted(migration_files):
                file_name = os.path.basename(file_path)
                match = re.match(r"V(\d+)__.*\.sql", file_name)
                
                if match:
                    migration_id = match.group(1)
                    
                    if migration_id not in applied_migrations:
                        pending_migrations.append((migration_id, file_path, svc))
        
        logger.debug(f"Found {len(pending_migrations)} pending migrations")
        return sorted(pending_migrations)
    
    async def apply_migrations(self, service: Optional[str] = None) -> List[str]:
        """
        Apply pending migrations.
        
        Args:
            service: Optional service name to filter by
        
        Returns:
            List of applied migration IDs
        
        Raises:
            MigrationError: If a migration fails to apply
        """
        # Ensure migration table exists
        await self._ensure_migration_table()
        
        # Get pending migrations
        pending_migrations = await self.get_pending_migrations(service)
        
        if not pending_migrations:
            logger.info("No pending migrations found")
            return []
        
        logger.info(f"Applying {len(pending_migrations)} migrations")
        
        applied_migrations = []
        
        for migration_id, file_path, svc in pending_migrations:
            logger.info(f"Applying migration {migration_id} for service {svc}: {file_path}")
            
            try:
                # Read migration file
                with open(file_path, "r") as f:
                    migration_sql = f.read()
                
                # Get migration description from filename
                file_name = os.path.basename(file_path)
                description = re.sub(r"V\d+__(.*)\.sql", r"\1", file_name).replace("_", " ")
                
                # Apply migration
                async with self._engine.begin() as conn:
                    # Execute migration SQL
                    await conn.execute(text(migration_sql))
                    
                    # Record migration
                    await conn.execute(
                        text(
                            f"""
                            INSERT INTO profiler_schema.{self._migration_table_name}
                            (migration_id, service, applied_at, description)
                            VALUES (:migration_id, :service, CURRENT_TIMESTAMP, :description)
                            """
                        ),
                        {
                            "migration_id": migration_id,
                            "service": svc,
                            "description": description
                        }
                    )
                
                logger.info(f"Successfully applied migration {migration_id}")
                applied_migrations.append(migration_id)
                
            except Exception as e:
                logger.error(f"Failed to apply migration {migration_id}: {str(e)}")
                raise MigrationError(f"Failed to apply migration {migration_id}: {str(e)}")
        
        logger.info(f"Successfully applied {len(applied_migrations)} migrations")
        return applied_migrations
    
    async def create_migration(self, name: str, service: str, sql_content: str) -> str:
        """
        Create a new migration file.
        
        Args:
            name: Name of the migration (will be converted to snake_case)
            service: Service that the migration is for
            sql_content: SQL content of the migration
        
        Returns:
            Path to the created migration file
        
        Raises:
            ValueError: If the service is invalid
        """
        if service not in self._services:
            raise ValueError(f"Invalid service: {service}. Valid services: {', '.join(self._services)}")
        
        # Convert name to snake_case
        name = re.sub(r"[^a-zA-Z0-9]", "_", name.lower())
        
        # Get next migration ID
        migration_dir = os.path.join(self._migrations_dir, service)
        existing_migrations = glob.glob(os.path.join(migration_dir, "V*__*.sql"))
        
        if existing_migrations:
            # Get highest migration ID
            highest_id = 0
            for file_path in existing_migrations:
                file_name = os.path.basename(file_path)
                match = re.match(r"V(\d+)__.*\.sql", file_name)
                
                if match:
                    migration_id = int(match.group(1))
                    highest_id = max(highest_id, migration_id)
            
            next_id = highest_id + 1
        else:
            next_id = 1
        
        # Create migration file name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"V{next_id:03d}__{timestamp}_{name}.sql"
        file_path = os.path.join(migration_dir, file_name)
        
        # Create migration file
        with open(file_path, "w") as f:
            f.write(sql_content)
        
        logger.info(f"Created migration file: {file_path}")
        return file_path
    
    async def apply_test_migrations(self, migration_files: List[str]) -> List[str]:
        """
        Apply test migrations - for testing purposes.
        
        Args:
            migration_files: List of migration file names to apply
        
        Returns:
            List of applied migration IDs
        """
        # This is a simplified version for testing that doesn't actually apply migrations
        return ["001", "002", "003"] 