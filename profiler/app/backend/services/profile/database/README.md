# PostgreSQL Profile Repository

This directory contains the PostgreSQL implementation of the `ProfileRepositoryInterface` for the profile service.

## Features

- Fully asynchronous implementation using SQLAlchemy's async features
- Robust error handling and resource management
- Connection pooling for improved performance
- Automatic schema creation and management
- Transaction support
- Support for complex queries and filters
- Docker container support for easy setup

## Components

- **models.py**: SQLAlchemy ORM models for profile data
- **connection.py**: Database connection management
- **repository.py**: PostgreSQL implementation of the `ProfileRepositoryInterface`

## Configuration

The PostgreSQL repository can be configured through the application's main `config.yaml` file:

```yaml
database:
  type: "postgresql"
  url: "postgresql+asyncpg://username:password@hostname:port/database"
  pool_size: 20
  max_overflow: 10
  echo: false
  connect_timeout: 10
  pool_pre_ping: true
  pool_recycle: 3600

profile_service:
  repository_type: "postgresql"
```

## Environment Variables

For security reasons, you can override the database connection details using environment variables:

- `PROFILER_DATABASE__URL`: Full PostgreSQL connection URL
- `PROFILER_DATABASE__POOL_SIZE`: Connection pool size
- `PROFILER_DATABASE__MAX_OVERFLOW`: Maximum overflow connections
- `PROFILER_DATABASE__CONNECT_TIMEOUT`: Connection timeout in seconds
- `PROFILER_PROFILE_SERVICE__REPOSITORY_TYPE`: Set to "postgresql" to use this repository

## Docker Container

A PostgreSQL container is provided for development and testing. The container is configured in the `docker-compose.yml` file and can be started with the `start_test_env.sh` script:

```bash
# Start the test environment with PostgreSQL container
./start_test_env.sh
```

The Docker container setup includes:

- PostgreSQL 15 database server
- Pre-configured database name, user, and password
- Automatic database initialization
- Data persistence through Docker volumes
- Health checks to ensure database availability
- Custom initialization scripts to set up schemas and roles

### Docker Configuration

You can customize the Docker setup by editing the following files:

1. **docker-compose.yml**: Container configuration, ports, volumes, and environment variables
2. **scripts/init-db/01-init.sql**: Database initialization SQL script that runs when the container starts

### Connecting to the Docker PostgreSQL Database

When using the Docker container, the application automatically connects to the PostgreSQL instance with the following connection details:

- **Host**: localhost
- **Port**: 5432 (or dynamically assigned if 5432 is in use)
- **Database**: profiler
- **Username**: postgres
- **Password**: postgres

You can connect to the database using any PostgreSQL client with these credentials.

## Usage

The PostgreSQL repository is automatically used when the `repository_type` is set to `"postgresql"` or `"database"` in the `profile_service` configuration.

```python
from profiler.app.backend.services.profile import ProfileService, ProfileServiceFactory
from profiler.app.backend.utils.config_manager import ConfigManager

# Create a config manager
config_manager = ConfigManager()

# Create a profile service factory with PostgreSQL repository
factory = ProfileServiceFactory(config_manager)

# Create a profile service
profile_service = ProfileService(factory)

# Initialize the service
await profile_service.initialize()
```

## Migration from JSON File Repository

To migrate profiles from the JSON file repository to PostgreSQL:

1. Configure the PostgreSQL repository as described above
2. Run the migration script: `python -m profiler.scripts.migrate_profiles --source json --destination postgresql`

## Testing

The PostgreSQL repository implementation includes comprehensive test coverage. To run the tests:

```bash
pytest profiler/tests/requirements/prd_1/test_postgresql_repository.py -v
``` 