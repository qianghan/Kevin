#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Fixing Docker connection issues...${NC}"

# Clear any DOCKER_HOST environment variable that might be interfering
unset DOCKER_HOST

# Make sure Docker Desktop is running
if ! pgrep -f "Docker Desktop" > /dev/null; then
    echo -e "${RED}Docker Desktop is not running.${NC}"
    echo -e "${YELLOW}Please start Docker Desktop from your Applications folder first.${NC}"
    exit 1
fi

# Set to the default context
echo -e "${YELLOW}Setting Docker context to default...${NC}"
docker context use default

# Test Docker connectivity
echo -e "${YELLOW}Testing Docker connectivity...${NC}"
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Cannot connect to Docker daemon.${NC}"
    echo -e "${YELLOW}Try restarting Docker Desktop and then run this script again.${NC}"
    exit 1
fi

echo -e "${GREEN}Docker connection fixed! Now starting the application...${NC}"

# Start MongoDB container directly
echo -e "${YELLOW}Starting MongoDB container...${NC}"
cd "$(dirname "$(dirname "$0")")/ui/db" || { echo -e "${RED}UI/db directory not found${NC}"; exit 1; }

# Remove existing container if it exists but is not running
if docker ps -a | grep -q "kevin-ui-mongodb" && ! docker ps | grep -q "kevin-ui-mongodb"; then
    echo -e "${YELLOW}Removing stale MongoDB container...${NC}"
    docker rm kevin-ui-mongodb
fi

# Start the container
docker-compose up -d
cd - > /dev/null

# Check if MongoDB is running
if docker ps | grep -q "kevin-ui-mongodb"; then
    echo -e "${GREEN}✓ MongoDB container started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start MongoDB container${NC}"
    echo -e "${YELLOW}Please try restarting Docker Desktop completely.${NC}"
    exit 1
fi

# Now run the original start script
cd "$(dirname "$0")" || { echo -e "${RED}Frontend directory not found${NC}"; exit 1; }
./start-chat.sh 