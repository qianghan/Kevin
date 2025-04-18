#!/bin/bash

# DB Maintenance Script for Profiler
# This script provides convenient commands for backup and restore operations

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the script's directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Path to the backup directory
BACKUP_DIR="$PROJECT_ROOT/backups"

# Make sure the backup directory exists
mkdir -p "$BACKUP_DIR"

# Default database connection parameters
HOST="localhost"
PORT="5432"
USER="postgres"
DB_NAME="profiler"

# Function to show usage information
show_usage() {
    echo "DB Maintenance Script for Profiler"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  backup              Create a database backup"
    echo "  restore FILE        Restore database from a backup file"
    echo "  list                List available backups"
    echo "  prune N             Delete all but the N most recent backups"
    echo "  help                Show this help message"
    echo ""
    echo "Options:"
    echo "  --host HOST         Database host (default: $HOST)"
    echo "  --port PORT         Database port (default: $PORT)"
    echo "  --user USER         Database user (default: $USER)"
    echo "  --password PASS     Database password"
    echo "  --db-name NAME      Database name (default: $DB_NAME)"
    echo "  --backup-dir DIR    Backup directory (default: $BACKUP_DIR)"
    echo "  --no-compress       Don't compress the backup (for backup command)"
    echo "  --tables TABLES     Specific tables to backup (space-separated, for backup command)"
    echo "  --schema-only       Backup schema only, no data (for backup command)"
    echo "  --data-only         Backup data only, no schema (for backup command)"
    echo "  --drop-db           Drop database before restoring (for restore command)"
    echo "  --create-db         Create database if it doesn't exist (for restore command)"
    echo ""
    echo "Examples:"
    echo "  $0 backup                        # Create a full compressed backup"
    echo "  $0 backup --schema-only          # Backup schema only"
    echo "  $0 backup --tables users roles   # Backup only the users and roles tables"
    echo "  $0 restore backups/profiler_20230101_120000.gz  # Restore from a backup file"
    echo "  $0 list                          # List available backups"
    echo "  $0 prune 5                       # Keep only the 5 most recent backups"
}

# Function to create a backup
create_backup() {
    local args=()
    
    # Add connection parameters
    args+=(--host "$HOST" --port "$PORT" --user "$USER" --db-name "$DB_NAME")
    
    # Add backup directory
    args+=(--backup-dir "$BACKUP_DIR")
    
    # Add password if provided
    if [ -n "$PASSWORD" ]; then
        args+=(--password "$PASSWORD")
    fi
    
    # Add compress flag if not disabled
    if [ "$NO_COMPRESS" != "true" ]; then
        args+=(--compress)
    fi
    
    # Add schema-only flag if specified
    if [ "$SCHEMA_ONLY" == "true" ]; then
        args+=(--schema-only)
    fi
    
    # Add data-only flag if specified
    if [ "$DATA_ONLY" == "true" ]; then
        args+=(--data-only)
    fi
    
    # Add tables if specified
    if [ ${#TABLES[@]} -gt 0 ]; then
        args+=(--tables "${TABLES[@]}")
    fi
    
    print_message "Creating database backup..."
    python "$SCRIPT_DIR/backup_database.py" "${args[@]}"
    
    if [ $? -eq 0 ]; then
        print_message "Backup created successfully in $BACKUP_DIR"
    else
        print_error "Backup failed"
        exit 1
    fi
}

# Function to restore a backup
restore_backup() {
    local file="$1"
    local args=()
    
    # Validate backup file
    if [ ! -f "$file" ]; then
        print_error "Backup file not found: $file"
        exit 1
    fi
    
    # Add connection parameters
    args+=(--host "$HOST" --port "$PORT" --user "$USER" --db-name "$DB_NAME")
    
    # Add password if provided
    if [ -n "$PASSWORD" ]; then
        args+=(--password "$PASSWORD")
    fi
    
    # Add drop-db flag if specified
    if [ "$DROP_DB" == "true" ]; then
        args+=(--drop-db)
    fi
    
    # Add create-db flag if specified
    if [ "$CREATE_DB" == "true" ]; then
        args+=(--create-db)
    fi
    
    print_message "Restoring database from $file..."
    python "$SCRIPT_DIR/restore_database.py" "$file" "${args[@]}"
    
    if [ $? -eq 0 ]; then
        print_message "Database restored successfully"
    else
        print_error "Database restore failed"
        exit 1
    fi
}

# Function to list available backups
list_backups() {
    local files=()
    local count=0
    
    # Find backup files in the backup directory
    if [ -d "$BACKUP_DIR" ]; then
        files=($(find "$BACKUP_DIR" -type f \( -name "*.sql" -o -name "*.gz" \) | sort -r))
        count=${#files[@]}
    fi
    
    if [ $count -eq 0 ]; then
        print_message "No backups found in $BACKUP_DIR"
    else
        print_message "Found $count backups in $BACKUP_DIR:"
        
        printf "%-5s %-30s %-15s %-15s\n" "No." "Filename" "Date" "Size"
        printf "%-5s %-30s %-15s %-15s\n" "----" "--------" "----" "----"
        
        for ((i=0; i<count; i++)); do
            local file="${files[$i]}"
            local filename=$(basename "$file")
            local date=$(date -r "$file" "+%Y-%m-%d %H:%M")
            local size=$(du -h "$file" | cut -f1)
            
            printf "%-5s %-30s %-15s %-15s\n" "$((i+1))" "$filename" "$date" "$size"
        done
    fi
}

# Function to prune old backups
prune_backups() {
    local keep=$1
    
    # Validate input
    if ! [[ "$keep" =~ ^[0-9]+$ ]] || [ "$keep" -lt 1 ]; then
        print_error "Invalid number of backups to keep: $keep"
        echo "Please specify a positive integer"
        exit 1
    fi
    
    # Find backup files in the backup directory
    if [ ! -d "$BACKUP_DIR" ]; then
        print_message "No backups directory found at $BACKUP_DIR"
        return
    fi
    
    local files=($(find "$BACKUP_DIR" -type f \( -name "*.sql" -o -name "*.gz" \) | sort -r))
    local count=${#files[@]}
    
    if [ $count -eq 0 ]; then
        print_message "No backups found in $BACKUP_DIR"
        return
    fi
    
    if [ $count -le $keep ]; then
        print_message "Found $count backups, keeping all (requested to keep $keep)"
        return
    fi
    
    local to_delete=$((count - keep))
    print_message "Found $count backups, keeping $keep most recent, deleting $to_delete"
    
    # Delete old backups
    for ((i=keep; i<count; i++)); do
        local file="${files[$i]}"
        print_message "Deleting $(basename "$file")..."
        rm "$file"
    done
    
    print_message "Pruned $to_delete old backups, kept $keep most recent"
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

COMMAND="$1"
shift

# Initialize variables
NO_COMPRESS="false"
SCHEMA_ONLY="false"
DATA_ONLY="false"
DROP_DB="false"
CREATE_DB="false"
PASSWORD=""
TABLES=()

# Parse options
while [ $# -gt 0 ]; do
    case "$1" in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --user)
            USER="$2"
            shift 2
            ;;
        --password)
            PASSWORD="$2"
            shift 2
            ;;
        --db-name)
            DB_NAME="$2"
            shift 2
            ;;
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --no-compress)
            NO_COMPRESS="true"
            shift
            ;;
        --schema-only)
            SCHEMA_ONLY="true"
            shift
            ;;
        --data-only)
            DATA_ONLY="true"
            shift
            ;;
        --drop-db)
            DROP_DB="true"
            shift
            ;;
        --create-db)
            CREATE_DB="true"
            shift
            ;;
        --tables)
            shift
            while [ $# -gt 0 ] && [[ "$1" != --* ]]; do
                TABLES+=("$1")
                shift
            done
            ;;
        *)
            # Save the first non-option argument as the backup file for restore
            if [ "$COMMAND" == "restore" ] && [[ "$1" != --* ]] && [ -z "$BACKUP_FILE" ]; then
                BACKUP_FILE="$1"
                shift
            else
                print_error "Unknown option: $1"
                show_usage
                exit 1
            fi
            ;;
    esac
done

# Execute the requested command
case "$COMMAND" in
    backup)
        create_backup
        ;;
    restore)
        if [ -z "$BACKUP_FILE" ]; then
            print_error "No backup file specified for restore"
            show_usage
            exit 1
        fi
        restore_backup "$BACKUP_FILE"
        ;;
    list)
        list_backups
        ;;
    prune)
        if [ -z "$1" ]; then
            print_error "No number specified for prune command"
            show_usage
            exit 1
        fi
        prune_backups "$1"
        ;;
    help)
        show_usage
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac 