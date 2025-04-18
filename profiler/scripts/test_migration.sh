#!/bin/bash

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

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker to run this test."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker to run this test."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose to run this test."
    exit 1
fi

# Create test profiles in JSON format
print_message "Creating test profiles in JSON format..."

# Create storage directory
mkdir -p data/profiles

# Create 3 test profiles
for i in {1..3}; do
    cat > "data/profiles/test-profile-$i.json" << EOF
{
    "profile_id": "test-profile-$i",
    "user_id": "migration-test-user",
    "current_section": "test",
    "sections": {
        "test": {
            "section_id": "test",
            "title": "Test Section $i",
            "data": {
                "test": "data-$i",
                "migration_test": true
            },
            "metadata": {
                "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
            },
            "completed": false,
            "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
        }
    },
    "metadata": {
        "test": true,
        "migration": true
    },
    "config": {
        "sections": ["test"],
        "required_sections": ["test"],
        "section_dependencies": {},
        "validation_rules": {}
    },
    "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "status": "test"
}
EOF
done

print_message "Created 3 test profiles in JSON format."

# Start PostgreSQL container for testing
print_message "Starting PostgreSQL container for migration test..."

# Use a different container name and port for testing
sed 's/profiler-postgres/migration-test-postgres/g' docker-compose.yml > test-docker-compose.yml
sed -i '' 's/"5432:5432"/"5433:5432"/g' test-docker-compose.yml

# Start the container
docker-compose -f test-docker-compose.yml up -d postgres

# Wait for the container to be ready
print_message "Waiting for PostgreSQL container to be ready..."
attempts=0
while [ $attempts -lt 30 ]; do
    if docker logs migration-test-postgres 2>&1 | grep -q "database system is ready to accept connections"; then
        print_message "PostgreSQL container is ready"
        sleep 2  # Give it a moment more to fully initialize
        break
    fi
    sleep 1
    attempts=$((attempts + 1))
    
    if [ $attempts -eq 30 ]; then
        print_error "PostgreSQL container took too long to start"
        docker-compose -f test-docker-compose.yml down
        rm test-docker-compose.yml
        exit 1
    fi
done

# Set environment variables for database connection
export PROFILER_DATABASE__URL="postgresql+asyncpg://postgres:postgres@localhost:5433/profiler"
export PROFILER_PROFILE_SERVICE__REPOSITORY_TYPE="postgresql"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the migration script
print_message "Running migration script..."
python -m profiler.scripts.migrate_profiles --source json --destination postgresql --user-id migration-test-user

# Exit code of the migration script
MIGRATION_EXIT_CODE=$?

if [ $MIGRATION_EXIT_CODE -ne 0 ]; then
    print_error "Migration script failed with exit code $MIGRATION_EXIT_CODE"
    docker-compose -f test-docker-compose.yml down
    rm test-docker-compose.yml
    exit 1
fi

# Test PostgreSQL connection
print_message "Verifying migration by checking PostgreSQL database..."
python profiler/scripts/test_postgres_connection.py --url "$PROFILER_DATABASE__URL"

# Exit code of the connection test
CONNECTION_TEST_EXIT_CODE=$?

# Clean up
print_message "Cleaning up..."
docker-compose -f test-docker-compose.yml down
rm test-docker-compose.yml

# Output final result
if [ $CONNECTION_TEST_EXIT_CODE -eq 0 ]; then
    print_message "Migration test passed! ✓"
    print_message "The migrate_profiles script is working correctly."
    exit 0
else
    print_error "Migration test failed! ✗"
    print_error "The migrate_profiles script may have issues."
    exit 1
fi 