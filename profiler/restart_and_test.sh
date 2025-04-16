#!/bin/bash

echo "[INFO] Stopping all services..."
pkill -f "next"
pkill -f "uvicorn"

echo "[INFO] Installing websockets package for testing..."
pip install websockets

echo "[INFO] Starting services..."
cd /Users/qiang.han/Documents/mycodespace/Kevin/profiler

# Start backend in background
cd app/backend
PYTHONPATH=/Users/qiang.han/Documents/mycodespace/Kevin/profiler uvicorn api.main:app --reload --port 8000 --log-level debug --ws websockets &
BACKEND_PID=$!
echo "[INFO] Backend started with PID: $BACKEND_PID"

# Start frontend in background
cd ../ui
npm run dev &
FRONTEND_PID=$!
echo "[INFO] Frontend started with PID: $FRONTEND_PID"

# Wait for services to start
echo "[INFO] Waiting for services to start..."
sleep 5

# Run the WebSocket test
echo "[INFO] Running WebSocket test..."
cd ../backend
python test_websocket.py

# Keep the script running
echo "[INFO] Services are running. Press Ctrl+C to stop."
wait 