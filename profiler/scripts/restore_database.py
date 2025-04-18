#!/usr/bin/env python3
"""
Database restore script for the Profiler application.

This script restores a PostgreSQL database backup created by the backup_database.py script.
It supports both compressed and uncompressed backups.
"""

import os
import sys
import argparse
import subprocess
import logging
import gzip
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('db_restore')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Restore PostgreSQL database for Profiler application.')
    parser.add_argument('backup_file', help='Path to the backup file (.sql or .gz)')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', help='Database password')
    parser.add_argument('--db-name', default='profiler', help='Database name')
    parser.add_argument('--create-db', action='store_true', help='Create database if it does not exist')
    parser.add_argument('--drop-db', action='store_true', help='Drop database if it exists before restoring')
    return parser.parse_args()

def is_compressed(file_path: Path) -> bool:
    """
    Check if a file is gzip compressed.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file is gzip compressed, False otherwise
    """
    return file_path.suffix.lower() == '.gz'

def decompress_file(input_file: Path) -> Path:
    """
    Decompress a gzip file to a temporary file.
    
    Args:
        input_file: Path to the gzip file
        
    Returns:
        Path to the decompressed file
    """
    logger.info(f"Decompressing {input_file}")
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sql')
    temp_file.close()
    output_file = Path(temp_file.name)
    
    with gzip.open(input_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    logger.info(f"Decompressed to {output_file}")
    return output_file

def create_database(
    host: str,
    port: int,
    user: str,
    db_name: str,
    password: Optional[str] = None
) -> bool:
    """
    Create a database if it doesn't exist.
    
    Args:
        host: Database host
        port: Database port
        user: Database user
        db_name: Database name
        password: Database password (optional)
        
    Returns:
        True if the database was created or already exists, False otherwise
    """
    logger.info(f"Creating database {db_name} if it doesn't exist")
    
    # First, check if the database exists
    cmd = ['psql', '-h', host, '-p', str(port), '-U', user, '-lqt']
    
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Check if the database exists in the output
        if any(line.split('|')[0].strip() == db_name for line in result.stdout.splitlines()):
            logger.info(f"Database {db_name} already exists")
            return True
            
        # Database doesn't exist, create it
        create_cmd = ['createdb', '-h', host, '-p', str(port), '-U', user, db_name]
        result = subprocess.run(
            create_cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"Database {db_name} created successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create database: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def drop_database(
    host: str,
    port: int,
    user: str,
    db_name: str,
    password: Optional[str] = None
) -> bool:
    """
    Drop a database if it exists.
    
    Args:
        host: Database host
        port: Database port
        user: Database user
        db_name: Database name
        password: Database password (optional)
        
    Returns:
        True if the database was dropped or didn't exist, False otherwise
    """
    logger.info(f"Dropping database {db_name} if it exists")
    
    cmd = ['dropdb', '-h', host, '-p', str(port), '-U', user, '--if-exists', db_name]
    
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"Database {db_name} dropped (or didn't exist)")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to drop database: {e}")
        logger.error(f"Error output: {e.stderr.decode()}")
        return False

def restore_database(
    backup_file: Path,
    host: str,
    port: int,
    user: str,
    db_name: str,
    password: Optional[str] = None
) -> bool:
    """
    Restore a database from a backup file.
    
    Args:
        backup_file: Path to the SQL backup file
        host: Database host
        port: Database port
        user: Database user
        db_name: Database name
        password: Database password (optional)
        
    Returns:
        True if the restore was successful, False otherwise
    """
    logger.info(f"Restoring database {db_name} from {backup_file}")
    
    cmd = ['psql', '-h', host, '-p', str(port), '-U', user, '-d', db_name, '-f', str(backup_file)]
    
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Database restored successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to restore database: {e}")
        logger.error(f"Error output: {e.stderr.decode()}")
        return False

def main():
    """Main entry point."""
    args = parse_args()
    
    backup_path = Path(args.backup_file)
    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_path}")
        sys.exit(1)
    
    # Check if we need to decompress the backup
    sql_file = backup_path
    if is_compressed(backup_path):
        sql_file = decompress_file(backup_path)
    
    # Handle database creation or dropping
    if args.drop_db:
        if not drop_database(args.host, args.port, args.user, args.db_name, args.password):
            logger.error("Failed to drop database. Exiting.")
            sys.exit(1)
    
    if args.create_db or args.drop_db:
        if not create_database(args.host, args.port, args.user, args.db_name, args.password):
            logger.error("Failed to create database. Exiting.")
            sys.exit(1)
    
    # Restore the database
    success = restore_database(sql_file, args.host, args.port, args.user, args.db_name, args.password)
    
    # Clean up temporary file if needed
    if is_compressed(backup_path) and sql_file != backup_path:
        logger.info(f"Removing temporary file: {sql_file}")
        sql_file.unlink()
    
    if success:
        logger.info(f"Database {args.db_name} restored successfully from {backup_path}")
        sys.exit(0)
    else:
        logger.error(f"Failed to restore database {args.db_name} from {backup_path}")
        sys.exit(1)

if __name__ == '__main__':
    main() 