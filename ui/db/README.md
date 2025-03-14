# UI MongoDB Setup

This directory contains a dedicated MongoDB setup specifically for the Kevin UI application.

## Directory Structure

- `config/` - MongoDB configuration files
- `data/` - MongoDB data directory (created when container runs)
- `init/` - Database initialization scripts
- `docker-compose.yml` - Docker Compose configuration for MongoDB
- `test-mongodb.js` - Script to test MongoDB connection

## Getting Started

1. Make sure Docker is running on your machine

2. Start MongoDB from this directory:
   ```bash
   cd ui/db
   docker-compose up -d
   ```

3. Verify MongoDB is running:
   ```bash
   docker ps
   ```
   You should see the `kevin-ui-mongodb` container running.

4. Test the MongoDB connection:
   ```bash
   cd ui/db
   node test-mongodb.js
   ```

## Connection Details

- **Port:** 27018 (different from the default 27017 to avoid conflicts)
- **Connection String:** `mongodb://kevinuser:kevin_password@localhost:27018/kevindb`
- **Database Name:** `kevindb`

## Environment Setup

Update your `.env.local` in the UI directory:

```
MONGODB_URI=mongodb://kevinuser:kevin_password@localhost:27018/kevindb
```

## User Accounts

The initialization script sets up the following example user accounts:

1. **Admin User**
   - Email: admin@example.com
   - Role: admin

2. **Student User**
   - Email: student@example.com
   - Role: student

3. **Parent User**
   - Email: parent@example.com
   - Role: parent

## Manually Connecting to MongoDB

You can connect to MongoDB using the mongo shell:

```bash
# Connect as admin
docker exec -it kevin-ui-mongodb mongosh admin -u admin -p secure_password

# Connect as application user
docker exec -it kevin-ui-mongodb mongosh kevindb -u kevinuser -p kevin_password
```

## Managing the MongoDB Instance

```bash
# Start MongoDB
docker-compose up -d

# Stop MongoDB
docker-compose down

# View logs
docker logs kevin-ui-mongodb

# Reset data
docker-compose down
rm -rf data/*
docker-compose up -d
``` 