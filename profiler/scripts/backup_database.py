#!/usr/bin/env python3
"""
Database backup script for the Profiler application.

This script creates a backup of the PostgreSQL database used by the Profiler application.
It supports both full database dumps and selective table backups.
"""

import os
import sys
import argparse
import subprocess
import logging
import datetime
import gzip
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
logger = logging.getLogger('db_backup')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Backup PostgreSQL database for Profiler application.')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', help='Database password')
    parser.add_argument('--db-name', default='profiler', help='Database name')
    parser.add_argument('--backup-dir', default='./backups', help='Directory to store backups')
    parser.add_argument('--compress', action='store_true', help='Compress the backup file')
    parser.add_argument('--tables', nargs='+', help='Specific tables to backup (space-separated)')
    parser.add_argument('--schema-only', action='store_true', help='Backup schema only, no data')
    parser.add_argument('--data-only', action='store_true', help='Backup data only, no schema')
    return parser.parse_args()

def create_backup_dir(backup_dir: str) -> Path:
    """
    Create backup directory if it doesn't exist.
    
    Args:
        backup_dir: Path to the backup directory
        
    Returns:
        Path object for the backup directory
    """
    backup_path = Path(backup_dir)
    
    if not backup_path.exists():
        logger.info(f"Creating backup directory: {backup_path}")
        backup_path.mkdir(parents=True)
    
    return backup_path

def generate_backup_filename(db_name: str, compress: bool = False) -> str:
    """
    Generate a filename for the backup file.
    
    Args:
        db_name: Database name
        compress: Whether the backup will be compressed
        
    Returns:
        Backup filename
    """
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    extension = 'gz' if compress else 'sql'
    return f"{db_name}_{timestamp}.{extension}"

def build_pg_dump_command(
    host: str,
    port: int,
    user: str,
    db_name: str,
    output_file: Path,
    password: Optional[str] = None,
    tables: Optional[List[str]] = None,
    schema_only: bool = False,
    data_only: bool = False
) -> List[str]:
    """
    Build the pg_dump command.
    
    Args:
        host: Database host
        port: Database port
        user: Database user
        db_name: Database name
        output_file: Path to the output file
        password: Database password (optional)
        tables: List of tables to backup (optional)
        schema_only: Whether to backup schema only
        data_only: Whether to backup data only
        
    Returns:
        pg_dump command as a list of strings
    """
    cmd = ['pg_dump', '-h', host, '-p', str(port), '-U', user]
    
    # Add options
    if schema_only:
        cmd.append('--schema-only')
    elif data_only:
        cmd.append('--data-only')
    
    # Add specific tables if provided
    if tables:
        for table in tables:
            cmd.extend(['-t', table])
    
    # Add output file and database name
    cmd.extend(['-f', str(output_file), db_name])
    
    return cmd

def run_backup(cmd: List[str], password: Optional[str] = None) -> bool:
    """
    Run the pg_dump command.
    
    Args:
        cmd: pg_dump command as a list of strings
        password: Database password (optional)
        
    Returns:
        True if backup was successful, False otherwise
    """
    logger.info(f"Running backup command: {' '.join(cmd)}")
    
    # Set PGPASSWORD environment variable if password is provided
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
        logger.info("Backup completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e}")
        logger.error(f"Error output: {e.stderr.decode()}")
        return False

def compress_file(input_file: Path) -> Path:
    """
    Compress a file using gzip.
    
    Args:
        input_file: Path to the input file
        
    Returns:
        Path to the compressed file
    """
    output_file = input_file.with_suffix('.gz')
    logger.info(f"Compressing {input_file} to {output_file}")
    
    with open(input_file, 'rb') as f_in:
        with gzip.open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Remove the original file
    input_file.unlink()
    logger.info(f"Removed original file: {input_file}")
    
    return output_file

def main():
    """Main entry point."""
    args = parse_args()
    
    # Create backup directory
    backup_path = create_backup_dir(args.backup_dir)
    
    # Generate backup filename
    filename = generate_backup_filename(args.db_name, args.compress)
    output_file = backup_path / filename
    
    # If compress flag is set, we'll compress after creating the SQL file
    final_output_file = output_file
    if args.compress:
        final_output_file = backup_path / filename.replace('.gz', '.sql')
    
    # Build and run pg_dump command
    cmd = build_pg_dump_command(
        host=args.host,
        port=args.port,
        user=args.user,
        db_name=args.db_name,
        output_file=final_output_file,
        password=args.password,
        tables=args.tables,
        schema_only=args.schema_only,
        data_only=args.data_only
    )
    
    success = run_backup(cmd, args.password)
    
    if success and args.compress:
        compress_file(final_output_file)
        logger.info(f"Final backup file: {output_file}")
    
    if success:
        logger.info(f"Backup completed and saved to: {output_file}")
        sys.exit(0)
    else:
        logger.error("Backup failed.")
        sys.exit(1)

if __name__ == '__main__':
    main() 