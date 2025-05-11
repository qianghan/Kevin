#!/bin/bash

# Start the mock services
echo "Starting mock services..."
node dev-server.js &
MOCK_PID=$!

# Wait a moment for services to initialize
sleep 2

# Set environment variables for development
export NODE_ENV=development
export NEXT_PUBLIC_API_URL=http://localhost:4000/api
export NEXT_PUBLIC_UI_URL=http://localhost:3002
export NEXT_PUBLIC_AUTH_BYPASS=true
export NEXT_PUBLIC_MOCK_MODE=true

# Start the frontend application
echo "Starting frontend application..."
cd frontend && npm run dev

# Handle cleanup when script exits
function cleanup {
  echo "Shutting down mock services..."
  kill $MOCK_PID
  echo "All services stopped."
}

# Set trap for cleanup
trap cleanup EXIT

# Wait for processes to finish
wait 